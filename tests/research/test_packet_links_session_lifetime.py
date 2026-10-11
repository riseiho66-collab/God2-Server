"""Real isolated TCP review of post-release owner/session lifetimes.

Uses the immutable qualified release copy and disposable companion fixture.
No production connection, production DB access, or native-client automation.
"""
from contextlib import ExitStack, closing
import os
from pathlib import Path
import re
import sqlite3
import time
import unittest

import test_owned_role_text_server as role
from test_current_world_ready_builder import current_world_ready_wire
import test_recovered_dual_connection_server as dual


class PacketLinksSessionLifetimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.binary = Path(os.environ.get('GOD2_PACKET_SESSION_REVIEW_BINARY',
            role.ROOT / 'artifacts/releases/packet-links-20260930-01/god2-server.candidate.exe'))
        cls.previous_binary = role.BINARY
        cls.addClassCleanup(setattr, role, 'BINARY', cls.previous_binary)
        role.BINARY = cls.binary
        role.OwnedRoleTextServerTests.setUpClass()

    def setUp(self):
        self.fixture = role.OwnedRoleTextServerTests()

    def login(self, state, lifetime, username=b'codexslow'):
        helper = state.helper
        login = lifetime.enter_context(helper.connect(state.endpoint))
        helper.handshake(login)
        credentials = (username, b'labtest2345')
        login.sendall(helper.frame(*dual.credential(4, *credentials)))
        helper.read_frame(login, 0x1d, 176)
        helper.read_frame(login, 4, 8)
        address = helper.read_frame(login, 5, 12)
        helper.read_frame(login, 6, 8)
        helper.read_frame(login, 0x0a, 20)
        helper.list_characters(login)
        game = lifetime.enter_context(helper.connect(('127.0.0.1', int.from_bytes(address[9:11], 'little'))))
        helper.handshake(game, game=True)
        game.sendall(helper.frame(*dual.credential(0, *credentials)))
        helper.read_frame(game, 0x1f, 128)
        return login, game

    def select(self, state, game, expected_character, token=0, project=True, expected_text=None, snapshot=True, ready=True):
        helper = state.helper
        game.sendall(helper.frame(0x1a, dual.selection_payload(token)))
        try:
            helper.read_frame(game, 2, 26)
        except AssertionError as error:
            raise AssertionError(str(error) + '\n' + state.log()[-6000:]) from error
        entry = helper.read_frame(game, 0x2a, 40)
        identity = int.from_bytes(entry[3:5], 'little') & 0x3fff
        self.assertEqual(identity, expected_character)
        if not ready:
            helper.silent(game)
            return
        game.sendall(current_world_ready_wire(identity, (4, 3)))
        helper.silent(game)
        if project:
            game.sendall(helper.frame(0x30, b'\0'))
            frames = self.fixture.drain(state, game, first=snapshot)
            self.assertEqual([r for r in frames if r[:1] == b'\x23'],
                             [] if expected_text is None else [b'\x23' + role.text16(expected_text)])
        helper.silent(game)

    def edit(self, state, game, text, character=4):
        game.sendall(state.helper.frame(0x20, role.request(text)[1:]))
        self.assertEqual(state.decoder.logical(state.helper, game), b'\x23' + role.text16(text))
        rows = {r[0]: r for r in state.rows()}
        self.assertEqual(rows[character][1:4], (role.text16(text), text.decode('ascii'), 950))
        state.helper.silent(game)

    def wait_marker(self, state, marker, minimum=1):
        deadline = time.monotonic() + 3
        while state.log().count(marker) < minimum:
            self.assertIsNone(state.process.poll(), 'Private server exited')
            self.assertLess(time.monotonic(), deadline, 'Private server did not produce marker ' + marker)
            time.sleep(.01)

    def game_id(self, state, character):
        matches = re.findall(r'session_id=(\d+) EXISTING_CHARACTER_BOUND character_id=' + str(character) + r'\b', state.log())
        self.assertTrue(matches)
        return matches[-1]

    def test_duplicate_character_lease_rejects_peer_preserves_original_and_releases_on_disconnect(self):
        with self.fixture.server() as state, ExitStack() as lifetime:
            login, game = self.login(state, lifetime)
            self.select(state, game, 4)
            self.edit(state, game, b'first-lease')
            first_id = self.game_id(state, 4)
            before = state.rows(), state.stable()
            duplicate_login, duplicate = self.login(state, lifetime)
            duplicate.sendall(state.helper.frame(0x1a, dual.selection_payload(0)))
            state.helper.closed(duplicate)
            self.assertEqual((state.rows(), state.stable()), before)
            # Disconnecting either failed peer socket must not erase the first
            # world's readiness or its movement/owned-projection lease.
            duplicate_login.close()
            self.edit(state, game, b'still-original')
            game.sendall(state.helper.frame(0xd6, bytes((7, 42, 1))))
            state.helper.silent(game)
            self.wait_marker(state, 'OWNED_PET2_REVERT_DENIED')
            self.assertIn('reason=missing_item', state.log())
            self.edit(state, game, b'after-d6')
            game.close()
            login.close()
            self.wait_marker(state, 'session_id=' + first_id + ' DISCONNECT_GAME_EXIT')
            _, reconnected = self.login(state, lifetime)
            self.select(state, reconnected, 4, expected_text=b'after-d6')
            self.edit(state, reconnected, b'new-lease')
            self.assertNotEqual(self.game_id(state, 4), first_id)

    def test_abandoned_prepared_lease_rejects_duplicate_then_releases_before_world_ready(self):
        with self.fixture.server() as state, ExitStack() as lifetime:
            login, game = self.login(state, lifetime)
            self.select(state, game, 4, ready=False)
            first_id = self.game_id(state, 4)
            before = state.rows(), state.stable()
            _, duplicate = self.login(state, lifetime)
            duplicate.sendall(state.helper.frame(0x1a, dual.selection_payload(0)))
            state.helper.closed(duplicate)
            self.assertEqual((state.rows(), state.stable()), before)
            game.close()
            login.close()
            self.wait_marker(state, 'session_id=' + first_id + ' DISCONNECT_GAME_EXIT')
            _, reconnected = self.login(state, lifetime)
            self.select(state, reconnected, 4)
            self.edit(state, reconnected, b'after-abandon')

    def test_login_socket_close_cannot_clear_projected_game_session_or_reserve_ownership(self):
        with self.fixture.server() as state, ExitStack() as lifetime:
            login, game = self.login(state, lifetime)
            self.select(state, game, 4)
            login.close()
            self.edit(state, game, b'game-survives')
            with closing(sqlite3.connect(state.database)) as db:
                before = db.execute('SELECT * FROM character_pet2_slots ORDER BY character_id,slot').fetchall()
            game.sendall(state.helper.frame(0x24, bytes((42, 43))))
            response = state.decoder.logical(state.helper, game)
            self.assertTrue(response.startswith(b'\x41\0\0\x2a\0\x41\0\0\x2b\0'))
            with closing(sqlite3.connect(state.database)) as db:
                after = db.execute('SELECT * FROM character_pet2_slots ORDER BY character_id,slot').fetchall()
            self.assertNotEqual(after, before)
            self.assertEqual([r for r in before if r[0] != 4 or r[1] == 44],
                             [r for r in after if r[0] != 4 or r[1] == 44])
            self.edit(state, game, b'after-reserve')

    def test_two_accounts_keep_text_owner_and_disconnect_cleanup_independent(self):
        with self.fixture.server() as state, ExitStack() as lifetime:
            # Clone-only credentials use the already known synthetic password;
            # no stored hash/credentials are printed or production rows touched.
            with closing(sqlite3.connect(state.database)) as db:
                identity = 'god2-bytes:' + b'leasepeer'.hex()
                db.execute('INSERT INTO accounts(username,password_hash) SELECT ?,a.password_hash '
                           'FROM accounts a JOIN recovered_characters c ON c.account_id=a.id WHERE c.id=4', (identity,))
                peer = db.execute('SELECT id FROM accounts WHERE username=?', (identity,)).fetchone()[0]
                profile = bytearray(db.execute('SELECT profile FROM recovered_characters WHERE id=4').fetchone()[0])
                name = b'LeasePeerHero'
                profile[:15] = name + bytes(15 - len(name))
                peer_character = db.execute('INSERT INTO recovered_characters(account_id,slot,profile,name_bytes) VALUES(?,0,?,?)',
                                            (peer, bytes(profile), name)).lastrowid
                db.commit()
            owner_login, owner_game = self.login(state, lifetime)
            self.select(state, owner_game, 4)
            peer_login, peer_game = self.login(state, lifetime, b'leasepeer')
            self.select(state, peer_game, peer_character, snapshot=False)
            # Enqueue both world mutations before draining either response.
            # Each socket and saved row must retain its own owner's bytes.
            owner_game.sendall(state.helper.frame(0x20, role.request(b'owner-text')[1:]))
            peer_game.sendall(state.helper.frame(0x20, role.request(b'peer-text')[1:]))
            self.assertEqual(state.decoder.logical(state.helper, owner_game), b'\x23' + role.text16(b'owner-text'))
            self.assertEqual(state.decoder.logical(state.helper, peer_game), b'\x23' + role.text16(b'peer-text'))
            owner_row = next(row for row in state.rows() if row[0] == 4)
            self.edit(state, peer_game, b'peer-updated', peer_character)
            self.assertEqual(next(row for row in state.rows() if row[0] == 4), owner_row)
            before = state.stable()
            peer_game.sendall(state.helper.frame(0x24, bytes((42, 43))))
            state.helper.silent(peer_game)  # Peer has no pet capacity; cannot use owner's pets.
            self.assertEqual(state.stable(), before)
            peer_game.close()
            peer_login.close()
            self.edit(state, owner_game, b'owner-still-on', 4)
            self.assertEqual(next(row for row in state.rows() if row[0] == peer_character)[1], role.text16(b'peer-updated'))
            self.assertEqual(next(row for row in state.rows() if row[0] == 5)[1], role.text16(b'other-owner'))


if __name__ == '__main__':
    unittest.main()
