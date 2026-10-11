"""Own-server L/G TCP contracts, not live-client or UI acceptance.

Requires a freshly built build/Release/god2-server.exe and the main change's
config/recovered-dual-connection.json. This module never builds the server.
Run: python -B -m unittest discover -s tests/research
     -p test_recovered_dual_connection_server.py -v

Each wire matrix shares one process. Only the persistence case restarts its
server; invalid configurations have a bounded, separate startup check.
"""

from contextlib import closing, contextmanager
import json
from pathlib import Path
import os
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / 'config/recovered-dual-connection.json'
BINARY = ROOT / 'build/Release/god2-server.exe'
PREFIX = ROOT / 'artifacts/golden/server-list/server-list-one-01'
SELECT = ROOT / 'artifacts/golden/server-select/C2S_0001.bin'
sys.path.insert(0, str(ROOT / 'tools/strike_lab'))
from c2s0002 import key


OWNER = b'DualOwner'
OTHER = b'DualOther'
UNKNOWN = b'DualUnknown'
PASSWORD = b'DualSyntheticSecret131'
WRONG_PASSWORD = b'DualWrongSecret'
HEROES = (b'DualFirstHero', b'DualSecondHero')
IO_TIMEOUT = 3


def credential(opcode=4, name=OWNER, password=PASSWORD):
    # Same 173 logical bytes as the existing recovered account tests.
    if len(name) > 23 or len(password) > 131:
        raise ValueError('Test credential bounds')
    payload = bytearray(172)
    payload[:len(name)] = name
    payload[24:24 + len(password)] = password
    payload[166] = 0xc8
    return opcode, bytes(payload)


def profile(name):
    if not 1 <= len(name) <= 14 or b'\0' in name:
        raise ValueError('Test character name bounds')
    payload = bytearray(44)
    payload[:len(name)] = name
    payload[29] = 2
    payload[31:34] = b'\x01\x03\x01'
    payload[36] = 0x41
    payload[38:40] = (1 + (9 << 4) + (8 << 10)).to_bytes(2, 'little')
    payload[40:44] = b'\x04\xaa\xbb\xcc'
    return bytes(payload)


def selection_payload(token):
    # Pinned 14C50 builder shape; its last three bytes are opaque stack data.
    return (b'LocalBufferA\0' + bytes(3) + b'LocalBufferB\0' + bytes(3)
            + bytes((token, 4)) + b'\xa5' * 3)


class RecoveredDualConnectionServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not BINARY.is_file():
            raise AssertionError('Fresh server binary required; this test does not build it')
        if not CONFIG.is_file():
            raise AssertionError('Main change must provide config/recovered-dual-connection.json')
        cls.crypto_key = key(ROOT)
        if len(cls.crypto_key) != 256 or (-sum(cls.crypto_key)) & 255:
            raise AssertionError('Recovered zero-seed key fixture changed')

    def frame(self, opcode, payload=b''):
        plain = bytearray((len(payload) + 4).to_bytes(2, 'little'))
        plain.extend(bytes((opcode,)) + payload)
        plain.append(sum(value + 0x3c for value in plain) & 255)
        self.assertLessEqual(len(plain) - 2, len(self.crypto_key))
        wire = bytearray(plain[:2])
        previous = 0
        for k, value in zip(self.crypto_key, plain[2:]):
            wire.append(((k ^ value) + previous - 3) & 255)
            previous = value
        return bytes(wire)

    def receive(self, client, size):
        data = bytearray()
        deadline = time.monotonic() + IO_TIMEOUT
        previous_timeout = client.gettimeout()
        try:
            while len(data) < size:
                remaining = deadline - time.monotonic()
                self.assertGreater(remaining, 0, 'Response deadline exceeded')
                client.settimeout(remaining)
                chunk = client.recv(size - len(data))
                self.assertTrue(chunk, 'Unexpected EOF before complete response')
                data.extend(chunk)
        finally:
            client.settimeout(previous_timeout)
        return bytes(data)

    def read_frame(self, client, opcode, length):
        header = self.receive(client, 2)
        self.assertEqual(int.from_bytes(header, 'little'), length)
        encrypted = self.receive(client, length - 2)
        plain = bytearray(header)
        previous = 0
        for index, value in enumerate(encrypted):
            previous = ((value + 3 - previous) & 255) ^ self.crypto_key[index & 255]
            plain.append(previous)
        self.assertEqual(plain[-1], sum(value + 0x3c for value in plain[:-1]) & 255)
        self.assertEqual(plain[2], opcode)
        return bytes(plain)

    def silent(self, client):
        previous_timeout = client.gettimeout()
        try:
            client.settimeout(.1)
            with self.assertRaises(socket.timeout, msg='Expected an open, silent connection'):
                client.recv(1)
        finally:
            client.settimeout(previous_timeout)

    def closed(self, client):
        client.settimeout(IO_TIMEOUT)
        try:
            self.assertEqual(client.recv(1), b'', 'Rejected request sent response bytes')
        except ConnectionResetError:
            pass

    def send(self, client, wire, fragmented=False, pending=None):
        if not fragmented:
            client.sendall(wire)
            return
        start = 0
        for end in (1, 2, len(wire) - 1):
            client.sendall(wire[start:end])
            self.silent(client)
            if pending is not None:
                pending()
            start = end
        client.sendall(wire[start:])

    @staticmethod
    def unused_port():
        with socket.socket() as reserve:
            reserve.bind(('127.0.0.1', 0))
            return reserve.getsockname()[1]

    def configuration(self, root, database=None, registration=True,
                      dual=True, character_port=0):
        config = json.loads(CONFIG.read_text(encoding='utf-8'))
        port = self.unused_port()
        while port == character_port:
            port = self.unused_port()
        config['server'].update(host='127.0.0.1', port=port,
                                character_port=character_port, max_sessions=32)
        config['protocol'].update(mode='god2_legacy_character_list_candidate',
                                  allow_unverified_legacy=True, packet_dump=True)
        config['development'].update(mock_login=False, recovered_account_auth=True,
                                     local_account_registration=registration,
                                     recovered_character_creation=True,
                                     recovered_dual_connection=dual)
        config['database']['path'] = str(database or root / 'test.db')
        config['logging'].update(file=str(root / 'server.log'), level='debug')
        config['lua'].update(script_root=str(ROOT / 'scripts'),
                             bootstrap=str(ROOT / 'scripts/bootstrap.lua'), hot_reload=False)
        return config

    @staticmethod
    def environment():
        env = dict(os.environ)
        env.pop('GOD2_POST6B_STRIKE_HOLD', None)
        env.pop('GOD2_UI_GATE_CONTROL', None)
        return env

    @staticmethod
    def stop(process):
        if process.poll() is None:
            process.terminate()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=3)

    def launch(self, root, config, log, run_for=45):
        path = root / 'config.json'
        path.write_text(json.dumps(config), encoding='utf-8')
        return subprocess.Popen(
            [str(BINARY), '--config', str(path), '--run-for', str(run_for)],
            cwd=ROOT, env=self.environment(), stdout=log, stderr=subprocess.STDOUT,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))

    @contextmanager
    def server(self, **options):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = self.configuration(root, **options)
            endpoint = (config['server']['host'], config['server']['port'])
            with (root / 'stdout.log').open('wb') as log:
                process = self.launch(root, config, log)
                try:
                    deadline = time.monotonic() + 5
                    while True:
                        self.assertIsNone(process.poll(), 'Server exited before L was ready')
                        try:
                            probe = socket.create_connection(endpoint, timeout=.2)
                            probe.close()
                            break
                        except OSError:
                            if time.monotonic() >= deadline:
                                self.fail('L listener startup deadline exceeded')
                            time.sleep(.025)
                    yield SimpleNamespace(root=root, endpoint=endpoint, process=process,
                                          database=Path(config['database']['path']))
                    self.assertIsNone(process.poll(), 'Server exited during TCP scenario')
                finally:
                    self.stop(process)
                    self.assert_private_logs(root)

    def connect(self, endpoint):
        return socket.create_connection(endpoint, timeout=IO_TIMEOUT)

    def logs(self, root):
        return '\n'.join(path.read_text(encoding='utf-8', errors='replace')
                         for path in (root / 'stdout.log', root / 'server.log')
                         if path.exists())

    def assert_private_logs(self, root):
        text = self.logs(root).lower()
        for secret in (OWNER, OTHER, UNKNOWN, PASSWORD, WRONG_PASSWORD, *HEROES):
            # Check raw strings and common byte-dump forms without printing them.
            for value in (secret.decode('ascii'), secret.hex(), secret.hex(' ')):
                self.assertFalse(value.lower() in text, 'Synthetic private data leaked to server logs')

    def marker_count(self, root, marker):
        return (root / 'stdout.log').read_text(encoding='utf-8', errors='replace').count(marker)

    def await_marker(self, root, marker, count):
        deadline = time.monotonic() + IO_TIMEOUT
        while self.marker_count(root, marker) < count and time.monotonic() < deadline:
            time.sleep(.025)
        self.assertEqual(self.marker_count(root, marker), count, marker)

    def snapshot(self, database):
        with closing(sqlite3.connect(database, timeout=IO_TIMEOUT)) as db:
            return (
                db.execute('SELECT id,username,password_hash FROM accounts ORDER BY id').fetchall(),
                db.execute('SELECT id,account_id,slot,name_bytes,profile '
                           'FROM recovered_characters ORDER BY id').fetchall(),
            )

    def unchanged(self, database, expected):
        self.assertTrue(self.snapshot(database) == expected, 'Rejected/incomplete request changed persistent data')

    def handshake(self, client, game=False, fragmented=False):
        self.assertEqual(self.receive(client, 19), (PREFIX / 'S2C_0001.bin').read_bytes())
        self.send(client, (PREFIX / 'C2S_0001.bin').read_bytes(), fragmented)
        greeting = self.read_frame(client, 1, 5)
        self.assertEqual(greeting[3], 0xf6 if game else 0x53)

    def login(self, client, name=OWNER, fragmented=False, dual=True):
        self.handshake(client, fragmented=fragmented)
        opcode, payload = credential(name=name)
        self.send(client, self.frame(opcode, payload), fragmented)
        reply = self.read_frame(client, 0x1d, 176)
        self.assertTrue(reply[3:-1] == payload, 'L credential acknowledgement mismatch')
        listing = self.read_frame(client, 4, 8)
        self.assertEqual(listing[3:-1], b'\x00\x00\x01\x00')
        endpoint = None
        if dual:
            address = self.read_frame(client, 5, 12)
            # P = plain[2]: subgroup P+1, opaque P+2, IPv4 P+3..6,
            # and little-endian bound G port P+7..8.
            self.assertEqual(address[3:5], b'\x00\x00')
            host = socket.inet_ntoa(address[5:9])
            port = int.from_bytes(address[9:11], 'little')
            self.assertEqual(host, client.getpeername()[0])
            self.assertGreater(port, 0)
            self.assertNotEqual(port, client.getpeername()[1])
            endpoint = (host, port)
            route = self.read_frame(client, 6, 8)
            self.assertEqual(route[3], 1)
        terminal = self.read_frame(client, 0x0a, 20)
        self.assertEqual(terminal[3:-1], bytes(16))
        self.silent(client)
        return endpoint

    def list_characters(self, client, fragmented=False, dual=True):
        self.send(client, SELECT.read_bytes(), fragmented)
        listing = self.read_frame(client, 7, 78)
        self.assertLessEqual(listing[3], 2)
        if dual:
            for index in range(listing[3]):
                self.assertEqual(listing[5 + 36 * index + 32], 1,
                                 'Populated record route must match opcode 06')
        self.silent(client)
        return listing

    def game_ready(self, client, name=OWNER, fragmented=False, pending=None):
        self.handshake(client, game=True, fragmented=fragmented)
        self.send(client, self.frame(*credential(0, name=name)), fragmented, pending)
        bootstrap = self.read_frame(client, 0x1f, 128)
        self.assertEqual(bootstrap[3:-1], bytes(124))
        self.silent(client)

    def result(self, client):
        result = self.read_frame(client, 2, 26)
        self.assertEqual(result[3:-1], bytes(22))
        self.silent(client)

    def create(self, client, name, fragmented=False, pending=None):
        wire = self.frame(0x1b, profile(name))
        self.assertEqual(len(wire), 48)
        self.send(client, wire, fragmented, pending)
        self.result(client)

    def select_existing(self, client, token, fragmented=False):
        wire = self.frame(0x1a, selection_payload(token))
        self.assertEqual(len(wire), 41)
        self.send(client, wire, fragmented)
        self.result(client)

    def select_created(self, client, token, fragmented=False):
        context = self.frame(0x18, b'\x01')
        selection = self.frame(0x1a, selection_payload(token))
        self.assertEqual((len(context), len(selection)), (5, 41))
        if fragmented:
            self.send(client, context, True)
            self.silent(client)
            self.send(client, selection, True)
        else:
            client.sendall(context + selection)
        self.result(client)

    def seed_character(self, server):
        with self.connect(server.endpoint) as login:
            endpoint = self.login(login)
            self.assertEqual(self.list_characters(login)[3], 0)
            with self.connect(endpoint) as game:
                self.game_ready(game)
                self.create(game, HEROES[0])
                self.select_created(game, 0)
        self.await_marker(server.root, 'POST_CREATE_CHARACTER_BOUND', 1)
        return endpoint

    def test_persistent_create_restart_saved_slot_and_independent_connections(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / 'persistent.db'
            with self.server(database=database) as server:
                first_pid = server.process.pid
                for slot, name in enumerate(HEROES):
                    with self.subTest(slot=slot), self.connect(server.endpoint) as login:
                        endpoint = self.login(login, fragmented=(slot == 0))
                        self.assertEqual(self.list_characters(login, fragmented=True)[3], slot)
                        before = self.snapshot(database)
                        with self.connect(endpoint) as game:
                            self.assertEqual(game.getpeername(), endpoint)
                            self.game_ready(game, fragmented=(slot == 0),
                                            pending=lambda: self.unchanged(database, before))
                            self.create(game, name, fragmented=True,
                                        pending=lambda: self.unchanged(database, before))
                            self.silent(login)  # L remains open while G commits a character.
                            saved = self.snapshot(database)
                            self.assertEqual(len(saved[1]), slot + 1)
                            self.assertEqual(saved[1][-1][2:], (slot, name, profile(name)[:40]))
                            login.shutdown(socket.SHUT_RDWR)
                            login.close()
                            self.select_created(game, slot, fragmented=(slot == 0))
                            self.unchanged(database, saved)
                    self.await_marker(server.root, 'POST_CREATE_CHARACTER_BOUND', slot + 1)
                self.assertEqual(self.marker_count(server.root, 'EXISTING_CHARACTER_BOUND'), 0)
                self.assertEqual(len(saved[0]), 1)
                self.assertEqual(saved[0][0][1], 'god2-bytes:' + OWNER.hex())
                self.assertTrue(PASSWORD.decode('ascii') not in saved[0][0][2],
                                'Database contains plaintext password')

            # Reuse the real committed DB in a fresh process; no direct fixture inserts.
            with self.server(database=database, registration=False) as server:
                self.assertNotEqual(server.process.pid, first_pid)
                with self.connect(server.endpoint) as login:
                    endpoint = self.login(login)
                    listing = self.list_characters(login)
                    self.assertEqual(listing[3], 2)
                    for index, name in enumerate(HEROES):
                        record = listing[5 + 36 * index:5 + 36 * (index + 1)]
                        self.assertEqual(record[:15].split(b'\0')[0], name)
                        self.assertEqual(record[19] & 7, saved[1][index][2])
                    token = listing[5 + 36 + 19] & 7
                    self.assertEqual(token, 1)
                    with self.connect(endpoint) as game:
                        self.game_ready(game)
                        self.silent(login)
                        login.shutdown(socket.SHUT_RDWR)
                        login.close()
                        self.select_existing(game, token, fragmented=True)
                self.unchanged(database, saved)
                self.await_marker(server.root, 'EXISTING_CHARACTER_BOUND', 1)
                self.assertEqual(self.marker_count(server.root, 'POST_CREATE_CHARACTER_BOUND'), 0)

    def test_g_credentials_verify_password_and_never_autoregister(self):
        with self.server() as server:
            endpoint = self.seed_character(server)
            with self.connect(server.endpoint) as login:
                self.assertEqual(self.login(login), endpoint)
                self.list_characters(login)
                before = self.snapshot(server.database)
                correct = self.frame(*credential(0))
                cases = (
                    ('unknown_account', self.frame(*credential(0, name=UNKNOWN))),
                    ('stored_password', self.frame(*credential(0, password=WRONG_PASSWORD))),
                    ('empty_account', self.frame(*credential(0, name=b''))),
                    ('empty_password', self.frame(*credential(0, password=b''))),
                    ('checksum', correct[:-1] + bytes((correct[-1] ^ 1,))),
                    ('login_opcode_on_g', self.frame(*credential(4))),
                )
                for label, wire in cases:
                    with self.subTest(case=label), self.connect(endpoint) as game:
                        self.handshake(game, game=True)
                        self.send(game, wire, fragmented=True)
                        self.closed(game)
                        self.unchanged(server.database, before)
                        self.silent(login)
                self.assertEqual(self.marker_count(server.root, 'EXISTING_CHARACTER_BOUND'), 0)
                with self.connect(endpoint) as game:
                    self.game_ready(game)
                    self.select_existing(game, 0)
                self.await_marker(server.root, 'EXISTING_CHARACTER_BOUND', 1)
                self.unchanged(server.database, before)

    def test_g_rejects_missing_slot_other_account_checksum_and_wrong_opcode(self):
        with self.server() as server:
            endpoint = self.seed_character(server)
            with self.connect(server.endpoint) as other_login:
                self.assertEqual(self.login(other_login, name=OTHER), endpoint)
                self.assertEqual(self.list_characters(other_login)[3], 0)
                before = self.snapshot(server.database)
                valid = self.frame(0x1a, selection_payload(0))
                cases = (
                    ('missing_slot_token', OWNER, self.frame(0x1a, selection_payload(1))),
                    ('other_account_slot', OTHER, valid),
                    ('checksum', OWNER, valid[:-1] + bytes((valid[-1] ^ 1,))),
                    ('wrong_opcode', OWNER, self.frame(0x19, selection_payload(0))),
                    ('missing_token_byte', OWNER, self.frame(0x1a, selection_payload(0)[:32]
                                                             + selection_payload(0)[33:])),
                )
                for label, name, wire in cases:
                    with self.subTest(case=label), self.connect(endpoint) as game:
                        self.game_ready(game, name=name)
                        game.sendall(wire)
                        self.closed(game)
                        self.unchanged(server.database, before)
                self.assertEqual(self.marker_count(server.root, 'EXISTING_CHARACTER_BOUND'), 0)
                self.assertEqual(self.marker_count(server.root, 'POST_CREATE_CHARACTER_BOUND'), 1)

    def test_l_rejects_create_and_existing_selection_before_and_after_a6(self):
        with self.server() as server:
            self.seed_character(server)
            before = self.snapshot(server.database)
            for selected in (False, True):
                for opcode, payload in ((0x1b, profile(HEROES[1])),
                                        (0x1a, selection_payload(0))):
                    with self.subTest(selected=selected, opcode=opcode), self.connect(server.endpoint) as login:
                        self.login(login)
                        if selected:
                            self.list_characters(login)
                        login.sendall(self.frame(opcode, payload))
                        self.closed(login)
                        self.unchanged(server.database, before)
            self.assertEqual(self.marker_count(server.root, 'EXISTING_CHARACTER_BOUND'), 0)
            self.assertEqual(self.marker_count(server.root, 'POST_CREATE_CHARACTER_BOUND'), 1)

    def test_explicit_character_port_matches_05_and_accepts_g(self):
        port = self.unused_port()
        with self.server(character_port=port) as server:
            with self.connect(server.endpoint) as login:
                endpoint = self.login(login)
                self.assertEqual(endpoint, ('127.0.0.1', port))
                self.list_characters(login)
                with self.connect(endpoint) as game:
                    self.game_ready(game)
                    self.assertEqual(game.getpeername(), endpoint)

    def test_false_flag_preserves_legacy_single_connection_flow(self):
        with self.server(dual=False) as server:
            with self.connect(server.endpoint) as login:
                self.assertIsNone(self.login(login, dual=False))
                self.assertEqual(self.list_characters(login, dual=False)[3], 0)
                self.create(login, HEROES[0])
                self.select_created(login, 0)
            self.await_marker(server.root, 'POST_CREATE_CHARACTER_BOUND', 1)
            self.assertEqual(len(self.snapshot(server.database)[1]), 1)

    def test_invalid_port_and_missing_prerequisites_fail_startup(self):
        cases = [
            ('negative_port', 'server', 'character_port', -1),
            ('overflow_port', 'server', 'character_port', 65536),
            ('fractional_port', 'server', 'character_port', 1.5),
            ('string_port', 'server', 'character_port', '2593'),
            ('boolean_port', 'server', 'character_port', True),
            ('missing_port', 'server', 'character_port', None),
            ('missing_candidate_mode', 'protocol', 'mode', 'god2_post_server_select'),
            ('missing_legacy_opt_in', 'protocol', 'allow_unverified_legacy', False),
            ('missing_account_auth', 'development', 'recovered_account_auth', False),
            ('missing_character_creation', 'development', 'recovered_character_creation', False),
        ]
        for label, section, field, value in cases:
            with self.subTest(case=label), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                config = self.configuration(root, registration=False)
                if value is None:
                    del config[section][field]
                else:
                    config[section][field] = value
                with (root / 'stdout.log').open('wb') as log:
                    process = self.launch(root, config, log, run_for=10)
                    try:
                        try:
                            code = process.wait(timeout=3)
                        except subprocess.TimeoutExpired:
                            self.fail('Invalid dual-connection configuration did not fail startup')
                        self.assertNotEqual(code, 0, 'Invalid configuration exited successfully')
                    finally:
                        self.stop(process)
                text = self.logs(root)
                self.assertNotIn(' listening on ', text)
                if section == 'server':
                    self.assertIn('character_port', text)
                    if value is not None:
                        self.assertIn('Invalid server limit:', text)
                else:
                    self.assertIn('requires', text)


if __name__ == '__main__':
    unittest.main()
