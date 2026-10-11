"""Executable login/reconnect checks on own loopback; no live-client acceptance.

Run: python -B -m unittest discover -s tests/research
     -p test_recovered_login_blackbox.py -v
Uses the dual harness's build/Release/god2-server.exe; never builds C++.
"""

from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
import sqlite3
import threading
import unittest

import test_recovered_dual_connection_server as dual


class RecoveredLoginBlackboxTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        dual.RecoveredDualConnectionServerTests.setUpClass()

    def setUp(self):
        # Composition keeps discovery from rerunning the existing dual suite.
        self.h = dual.RecoveredDualConnectionServerTests()

    def route(self, server):
        with self.h.connect(server.endpoint) as client:
            return self.h.login(client)

    def healthy(self, server, endpoint):
        with self.h.connect(server.endpoint) as login:
            self.assertEqual(self.h.login(login), endpoint)
            self.h.list_characters(login)
            with self.h.connect(endpoint) as game:
                self.h.game_ready(game)

    def test_incomplete_seed_and_credentials_do_not_survive_reconnect(self):
        h = self.h
        with h.server() as server:
            endpoint = self.route(server)
            before = h.snapshot(server.database)
            seed = (dual.PREFIX / 'C2S_0001.bin').read_bytes()
            for game, address in ((False, server.endpoint), (True, endpoint)):
                for split in (1, 2, 18):
                    with self.subTest(game=game, stage='seed', split=split):
                        with h.connect(address) as client:
                            h.receive(client, 19)
                            client.sendall(seed[:split])
                            h.silent(client)
                        h.unchanged(server.database, before)
                wire = h.frame(*dual.credential(0 if game else 4,
                                                name=dual.OWNER if game else dual.UNKNOWN))
                for split in (1, 2, 25, 175):
                    with self.subTest(game=game, stage='credentials', split=split):
                        with h.connect(address) as client:
                            h.handshake(client, game=game)
                            client.sendall(wire[:split])
                            h.silent(client)
                        h.unchanged(server.database, before)
                self.healthy(server, endpoint)
            h.unchanged(server.database, before)

    def test_malformed_credentials_and_pre_auth_selection_are_isolated(self):
        h = self.h
        with h.server() as server:
            endpoint = self.route(server)
            before = h.snapshot(server.database)
            for game, address in ((False, server.endpoint), (True, endpoint)):
                opcode, valid = dual.credential(0 if game else 4)
                cases = [('selection_before_auth', dual.SELECT.read_bytes()),
                         ('wrong_opcode', h.frame(4 if game else 0, valid)),
                         ('short_header', b'\xaf\x00'),
                         ('long_header', b'\xb1\x00')]
                # Offsets are relative to the payload after the opcode.
                for label, offset, value in (
                        ('name_terminator', 23, 1),
                        ('password_terminator', 155, 1),
                        ('builder_constant', 166, 0),
                        ('config_word_out_of_range', 165, 4)):
                    invalid = bytearray(valid)
                    invalid[offset] = value
                    cases.append((label, h.frame(opcode, invalid)))
                if not game:
                    invalid = bytearray(valid)
                    invalid[167] = 1
                    cases.append(('unsupported_response_flag', h.frame(opcode, invalid)))
                with h.connect(endpoint) as survivor:
                    h.game_ready(survivor)
                    for label, wire in cases:
                        with self.subTest(game=game, case=label), h.connect(address) as client:
                            h.handshake(client, game=game)
                            client.sendall(wire)
                            h.closed(client)
                            h.unchanged(server.database, before)
                            h.silent(survivor)
                self.healthy(server, endpoint)

    def test_authenticated_sockets_reject_credential_replay_and_account_switch(self):
        h = self.h
        with h.server() as server:
            endpoint = self.route(server)
            with h.connect(server.endpoint) as other:
                self.assertEqual(h.login(other, name=dual.OTHER), endpoint)
            before = h.snapshot(server.database)
            for stage in ('login_terminal', 'login_list', 'game_ready'):
                for name in (dual.OWNER, dual.OTHER):
                    with self.subTest(stage=stage, same_account=name == dual.OWNER):
                        game = stage == 'game_ready'
                        with h.connect(endpoint if game else server.endpoint) as client:
                            if game:
                                h.game_ready(client)
                            else:
                                h.login(client)
                                if stage == 'login_list':
                                    h.list_characters(client)
                            client.sendall(h.frame(*dual.credential(0 if game else 4, name=name)))
                            h.closed(client)
                        h.unchanged(server.database, before)
            self.healthy(server, endpoint)

    def test_simultaneous_first_login_commits_one_identity(self):
        h = self.h
        with h.server() as server:
            count = 4
            barrier = threading.Barrier(count)

            def connect_and_login():
                with h.connect(server.endpoint) as client:
                    barrier.wait(timeout=dual.IO_TIMEOUT)
                    endpoint = h.login(client)
                    self.assertEqual(h.list_characters(client)[3], 0)
                    return endpoint

            with ThreadPoolExecutor(max_workers=count) as pool:
                futures = [pool.submit(connect_and_login) for _ in range(count)]
                endpoints = [future.result(timeout=15) for future in futures]
            self.assertEqual(len(set(endpoints)), 1)
            before = h.snapshot(server.database)
            self.assertEqual(len(before[0]), 1)
            self.assertEqual(before[0][0][1], 'god2-bytes:' + dual.OWNER.hex())
            self.assertEqual(before[1], [])
            self.healthy(server, endpoints[0])
            h.unchanged(server.database, before)

    def test_reconnect_preserves_two_accounts_with_the_same_slot_number(self):
        h = self.h
        with h.server() as server:
            for account, hero in zip((dual.OWNER, dual.OTHER), dual.HEROES):
                with h.connect(server.endpoint) as login:
                    endpoint = h.login(login, name=account)
                    self.assertEqual(h.list_characters(login)[3], 0)
                # G authenticates independently after L has gone away.
                with h.connect(endpoint) as game:
                    h.game_ready(game, name=account)
                    h.create(game, hero)
            before = h.snapshot(server.database)
            self.assertEqual(len(before[0]), 2)
            self.assertEqual([row[2] for row in before[1]], [0, 0])
            with h.connect(endpoint) as survivor:
                h.game_ready(survivor, name=dual.OTHER)
                for account, hero in zip((dual.OWNER, dual.OTHER), dual.HEROES):
                    for reconnect in range(2):
                        with self.subTest(account_index=account == dual.OTHER, reconnect=reconnect):
                            with h.connect(server.endpoint) as login:
                                self.assertEqual(h.login(login, name=account), endpoint)
                                listing = h.list_characters(login)
                                self.assertEqual(listing[3], 1)
                                self.assertTrue(listing[5:20].split(b'\0')[0] == hero,
                                                'Character list crossed account boundary')
                            with h.connect(endpoint) as game:
                                h.game_ready(game, name=account)
                                h.select_existing(game, 0)
                            h.silent(survivor)
                h.select_existing(survivor, 0)
            h.unchanged(server.database, before)

    def test_commit_failure_recovers_without_process_restart(self):
        h = self.h
        with h.server() as server:
            with closing(sqlite3.connect(server.database)) as db:
                db.execute("CREATE TRIGGER deny_login BEFORE INSERT ON accounts "
                           "BEGIN SELECT RAISE(ABORT, 'synthetic login failure'); END")
                db.commit()
            with h.connect(server.endpoint) as client:
                h.handshake(client)
                client.sendall(h.frame(*dual.credential()))
                h.closed(client)
            self.assertEqual(h.snapshot(server.database), ([], []))
            self.assertEqual(h.marker_count(server.root, 'RECOVERED_ACCOUNT_BOUND'), 0)
            with closing(sqlite3.connect(server.database)) as db:
                db.execute('DROP TRIGGER deny_login')
                db.commit()
            endpoint = self.route(server)
            self.healthy(server, endpoint)
            self.assertEqual(len(h.snapshot(server.database)[0]), 1)

    def test_invalid_stored_hash_rejects_both_listeners_without_replacement(self):
        h = self.h
        with h.server() as server:
            endpoint = self.route(server)
            saved = h.snapshot(server.database)
            for invalid in ('plaintext-not-a-hash',
                            'god2$pbkdf2-sha256$v1$600000$' + 'z' * 32 + '$' + '0' * 64):
                with closing(sqlite3.connect(server.database)) as db:
                    db.execute('UPDATE accounts SET password_hash=?', (invalid,))
                    db.commit()
                before = h.snapshot(server.database)
                for game, address in ((False, server.endpoint), (True, endpoint)):
                    with self.subTest(game=game, malformed_hex=invalid.startswith('god2$')):
                        with h.connect(address) as client:
                            h.handshake(client, game=game)
                            client.sendall(h.frame(*dual.credential(0 if game else 4)))
                            h.closed(client)
                        h.unchanged(server.database, before)
            with closing(sqlite3.connect(server.database)) as db:
                db.execute('UPDATE accounts SET password_hash=?', (saved[0][0][2],))
                db.commit()
            self.healthy(server, endpoint)
            h.unchanged(server.database, saved)


if __name__ == '__main__':
    unittest.main()
