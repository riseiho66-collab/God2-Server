"""Disposable own-server TCP acceptance of native20/23 and owned durability.

This is a socket peer, not actual-client UI acceptance. Source fixture is opened
read-only and copied; every mutation and process belongs to TemporaryDirectory.
"""
from contextlib import ExitStack, closing, contextmanager
import hashlib
import json
import os
from pathlib import Path
import select
import socket
import sqlite3
import subprocess
import tempfile
import time
from types import SimpleNamespace
import unittest

import test_recovered_dual_connection_server as dual
import test_inventory_move_server as inventory
from test_current_world_ready_builder import current_world_ready_wire

ROOT = dual.ROOT
SOURCE = ROOT / 'artifacts/playtests/private-owned-companions-20260926-01'
BINARY = Path(os.environ.get('GOD2_ROLE_TEXT_TEST_BINARY',
                            ROOT / 'build-town-visibility/Release/god2-server-native-results.exe'))
SOURCE_SHA = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
STABLE_TABLES = ('accounts', 'recovered_characters', 'character_resources',
                'character_role_snapshots', 'character_pet2_slots', 'character_deities',
                'character_deity_selection', 'diagnostic_inventory_slots',
                'battle_reservations', 'battle_settlements')


def text16(value):
    if len(value) > 15 or b'\0' in value:
        raise ValueError('Test secondary text bound')
    return value + bytes(16 - len(value))


def request(value, tail=0xa5):
    if len(value) > 15 or b'\0' in value:
        raise ValueError('Test secondary text bound')
    return b'\x20' + value + b'\0' + bytes([tail]) * (15 - len(value))


class OwnedRoleTextServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not BINARY.is_file() or not (SOURCE / 'town-diagnostic-accounts.db').is_file():
            raise AssertionError('Built candidate and isolated companion fixture required')
        dual.RecoveredDualConnectionServerTests.crypto_key = dual.key(ROOT)
        print('Role text candidate:', BINARY, 'SHA256', hashlib.sha256(BINARY.read_bytes()).hexdigest(), flush=True)

    @contextmanager
    def server(self):
        helper = dual.RecoveredDualConnectionServerTests()
        decoder = inventory.InventoryMoveServerTests()
        source_file = SOURCE / 'town-diagnostic-accounts.db'
        original_hash = hashlib.sha256(source_file.read_bytes()).hexdigest()
        try:
            with tempfile.TemporaryDirectory(prefix='god2-role-text-tcp-') as tmp, ExitStack() as lifetime:
                here = Path(tmp)
                database = here / 'town-diagnostic-accounts.db'
                with closing(sqlite3.connect(source_file.resolve().as_uri() + '?mode=ro', uri=True)) as source:
                    with closing(sqlite3.connect(database)) as target:
                        source.backup(target)
                with closing(sqlite3.connect(database)) as prepared:
                    # Current deity category source rejects historical fixture100.
                    # This synthetic clone keeps its existing qualified101 only.
                    prepared.execute('delete from character_deity_selection where character_id=4')
                    prepared.execute('delete from character_deities where character_id=4 and row_key=100')
                    prepared.execute('insert into character_deity_selection values(4,101,1)')
                    prepared.execute('delete from recovered_positions where character_id=4')
                    prepared.commit()
                config = json.loads((SOURCE / 'server-config.json').read_text('utf-8'))
                config['world'] = {'new_character_birthplace': {'area': 4, 'scene': 3, 'kind': 0,
                    'x': 126, 'y': 126, 'navigation': str(ROOT / 'artifacts/world-atlas/kunlun-4-3.json'),
                    'coordinate_authority': 'CUSTOM-0040'}, 'clock': {'enabled': False}}
                config['database']['path'] = str(database)
                config['server'].update(host='127.0.0.1', port=helper.unused_port(), character_port=0)
                config['logging'].update(file=str(here / 'server.log'), level='debug')
                config['protocol']['packet_dump'] = False
                config['development']['diagnostic_town'].update(player_visibility=False,
                    native_npc_placements_only=True, quest_progress=False, spawn_guides=False,
                    map_probe=False, door_routes=False)
                cfg = here / 'config.json'
                cfg.write_text(json.dumps(config), encoding='utf-8')
                endpoint = ('127.0.0.1', config['server']['port'])

                def launch():
                    output = lifetime.enter_context((here / 'stdout.log').open('ab'))
                    environment = helper.environment()
                    environment['GOD2_LOG_FILE_ONLY'] = '1'
                    process = subprocess.Popen([str(BINARY), '--config', str(cfg), '--run-for', '80'],
                        cwd=ROOT, env=environment, stdout=output, stderr=subprocess.STDOUT,
                        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                    lifetime.callback(helper.stop, process)
                    deadline = time.monotonic() + 10
                    while True:
                        self.assertIsNone(process.poll(), (here / 'stdout.log').read_text('utf-8', errors='replace'))
                        try:
                            with socket.create_connection(endpoint, timeout=.1):
                                return process
                        except OSError:
                            self.assertLess(time.monotonic(), deadline, 'Private role text candidate did not listen')
                            time.sleep(.025)

                def rows():
                    with closing(sqlite3.connect(database)) as db:
                        self.assertEqual(db.execute('pragma quick_check').fetchone(), ('ok',))
                        return db.execute('select character_id,legacy_text,utf8_text,codepage,revision,origin,source_sha256,design_id '
                                          'from character_role_text order by character_id').fetchall()

                def stable():
                    with closing(sqlite3.connect(database)) as db:
                        return {table: db.execute('select * from ' + table + ' order by 1,2').fetchall()
                                for table in STABLE_TABLES}

                process = launch()
                self.assertEqual(rows(), [], 'Native text fixture must begin without text rows')
                with closing(sqlite3.connect(database)) as db:
                    db.execute('insert into character_role_text values(?,?,?,?,?,?,?,?)',
                               (5, text16(b'other-owner'), 'other-owner', 950, 7, 'CUSTOM_DESIGNED', SOURCE_SHA, 'CUSTOM-0056'))
                    db.commit()
                state = SimpleNamespace(helper=helper, decoder=decoder, database=database, endpoint=endpoint,
                    launch=launch, process=process, rows=rows, stable=stable,
                    log=lambda: (here / 'server.log').read_text('utf-8', errors='replace'))
                yield state
                self.assertIsNone(state.process.poll(), state.log()[-4000:])
        finally:
            self.assertEqual(hashlib.sha256(source_file.read_bytes()).hexdigest(), original_hash,
                             'Read-only source fixture changed')

    def drain(self, state, game, first=False):
        result = [state.decoder.logical(state.helper, game)] if first else []
        while select.select([game], [], [], .12)[0]:
            result.append(state.decoder.logical(state.helper, game))
        return result

    @contextmanager
    def enter(self, state, codepage=950, expected=None, project=True):
        helper = state.helper
        with ExitStack() as connections:
            login = connections.enter_context(helper.connect(state.endpoint))
            helper.handshake(login)
            credentials = (b'codexslow', b'labtest2345')
            login.sendall(helper.frame(*dual.credential(4, *credentials)))
            helper.read_frame(login, 0x1d, 176);helper.read_frame(login, 4, 8)
            address = helper.read_frame(login, 5, 12)
            helper.read_frame(login, 6, 8);helper.read_frame(login, 0x0a, 20)
            self.assertEqual(helper.list_characters(login)[3], 1)
            game = connections.enter_context(helper.connect(('127.0.0.1', int.from_bytes(address[9:11], 'little'))))
            helper.handshake(game, game=True)
            game.sendall(helper.frame(*dual.credential(0, *credentials)))
            helper.read_frame(game, 0x1f, 128)
            game.sendall(helper.frame(0x1a, dual.selection_payload(0)))
            helper.read_frame(game, 2, 26)
            entry = helper.read_frame(game, 0x2a, 40)
            identity = int.from_bytes(entry[3:5], 'little') & 0x3fff
            self.assertEqual(identity, 4)
            helper.silent(game)
            game.sendall(current_world_ready_wire(identity, (4, 2) if codepage == 936 else (4, 3)))
            helper.silent(game)
            if project:
                game.sendall(helper.frame(0x30, b'\0'))
                frames = self.drain(state, game, first=True)
                self.assertEqual([frame for frame in frames if frame[:1] == b'\x23'],
                                 [] if expected is None else [b'\x23' + text16(expected)])
                self.assertNotIn(b'\x23' + text16(b'other-owner'), frames)
                helper.silent(game)
            yield game

    def send_text(self, state, game, value, tail=0xa5, ticks=False, fragmented=False):
        raw = request(value, tail)
        if ticks:
            raw = b'\x30\0' + raw + b'\x30\0'
        wire = state.helper.frame(raw[0], raw[1:])
        before = state.rows()
        if fragmented:
            game.sendall(wire[:-1]);state.helper.silent(game)
            self.assertEqual(state.rows(), before, 'Incomplete encrypted frame wrote text')
            game.sendall(wire[-1:])
        else:
            game.sendall(wire)
        self.assertEqual(state.decoder.logical(state.helper, game), b'\x23' + text16(value))
        state.helper.silent(game)

    def test_native_edit_clear_stale_tail_and_restart_both_languages(self):
        with self.server() as state:
            before = state.stable()
            other = state.rows()[0]
            value = '角色文字'
            with self.enter(state) as game:
                self.send_text(state, game, value.encode('cp950'), fragmented=True)
                saved = state.rows()[0]
                self.assertEqual(saved[:5], (4, text16(value.encode('cp950')), value, 950, 1))
                self.assertEqual(saved[5:], ('CUSTOM_DESIGNED', SOURCE_SHA, 'CUSTOM-0056'))
                self.send_text(state, game, value.encode('cp950'), tail=0xff, ticks=True)
                self.assertEqual(state.rows()[0], saved, 'Stack tail changed canonical text/revision')
                self.send_text(state, game, b'')
                self.assertEqual(state.rows()[0][:5], (4, bytes(16), '', 950, 2))
                self.send_text(state, game, value.encode('cp950'))
                saved = state.rows()[0]
            state.helper.stop(state.process)
            state.process = state.launch()
            with self.enter(state, 936, value.encode('cp936')) as game:
                self.assertEqual(state.rows()[0], saved, 'Cross-language restore rewrote saved text')
                self.send_text(state, game, value.encode('cp936'))
                saved = state.rows()[0]
                self.assertEqual(saved[:5], (4, text16(value.encode('cp936')), value, 936, 4))
            with self.enter(state, 950, value.encode('cp950')):
                self.assertEqual(state.rows()[0], saved)
            self.assertEqual(state.rows()[1], other, 'Another owner text changed')
            self.assertEqual(state.stable(), before, 'Text edit changed primary identity/other saved state')
            self.assertIn('OWNED_ROLE_TEXT_SAVED', state.log())
            self.assertGreaterEqual(state.log().count('OWNED_ROLE_TEXT_RESTORED'), 2)

    def test_preprojection_mixed_duplicate_and_invalid_encoding_never_write(self):
        with self.server() as state:
            before = state.stable()
            rows = state.rows()
            with self.enter(state, project=False) as game:
                game.sendall(state.helper.frame(0x20, request(b'early')[1:]))
                state.helper.silent(game);self.assertEqual(state.rows(), rows)
                game.sendall(state.helper.frame(0x30, b'\0'))
                self.drain(state, game, first=True)
                for raw in (request(b'first') + request(b'second'),
                            request(b'mixed') + b'\x2e\x7e\0\x7e\0\x01\xa5',
                            request(b'\x81')):
                    game.sendall(state.helper.frame(raw[0], raw[1:]))
                    state.helper.silent(game);self.assertEqual(state.rows(), rows)
                self.send_text(state, game, b'allowed', ticks=True)
                self.assertEqual(state.rows()[0][:5], (4, text16(b'allowed'), 'allowed', 950, 1))
                self.assertEqual(state.rows()[1], rows[0])
            self.assertEqual(state.stable(), before)

    def test_unrepresentable_cross_language_relogin_preserves_saved_unicode(self):
        with self.server() as state:
            value = '专'
            with self.enter(state, 936) as game:
                self.send_text(state, game, value.encode('cp936'))
            saved = state.rows()
            with self.enter(state, 950, expected=None) as game:
                self.assertEqual(state.rows(), saved)
                game.sendall(state.helper.frame(0x30, b'\0'))
                self.assertFalse(any(frame[:1] == b'\x23' for frame in self.drain(state, game)))
            self.assertIn('OWNED_ROLE_TEXT_DISPLAY_UNAVAILABLE', state.log())
            with self.enter(state, 936, value.encode('cp936')):
                self.assertEqual(state.rows(), saved)


if __name__ == '__main__':
    unittest.main()
