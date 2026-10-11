"""Isolated native 27 TCP route checks; independent of actual UI acceptance.

The historical synthetic fixture is opened read-only and backed up to a private
temporary DB. Revert stones are explicit test grants in that clone only.
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
import unittest

import test_recovered_dual_connection_server as dual
from test_current_world_ready_builder import current_world_ready_wire
import test_inventory_move_server as inventory

ROOT = dual.ROOT
SOURCE = ROOT / 'artifacts/playtests/private-owned-companions-20260926-01'
BINARY = Path(os.environ.get('GOD2_PET2_REVERT_TEST_BINARY',
                            ROOT / 'build-town-visibility/Release/god2-server-native-results.exe'))
ITEM_SOURCE = '70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731'
TABLES = ('character_pet2_slots', 'character_deities', 'character_deity_selection',
          'character_resources', 'character_role_snapshots', 'diagnostic_inventory_slots',
          'battle_reservations', 'battle_settlements', 'recovered_positions', 'character_role_text')


class NativeDiscardServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not BINARY.is_file() or not (SOURCE / 'town-diagnostic-accounts.db').is_file():
            raise AssertionError('Candidate and isolated companion fixture required')
        dual.RecoveredDualConnectionServerTests.crypto_key = dual.key(ROOT)
        print('27 candidate:', BINARY, 'SHA256', hashlib.sha256(BINARY.read_bytes()).hexdigest(), flush=True)

    @contextmanager
    def server(self):
        helper = dual.RecoveredDualConnectionServerTests()
        decoder = inventory.InventoryMoveServerTests()
        source_file = SOURCE / 'town-diagnostic-accounts.db'
        original_hash = hashlib.sha256(source_file.read_bytes()).hexdigest()
        try:
            with tempfile.TemporaryDirectory(prefix='god2-discard-tcp-') as tmp, ExitStack() as lifetime:
                here = Path(tmp)
                database = here / 'town-diagnostic-accounts.db'
                with closing(sqlite3.connect(source_file.resolve().as_uri() + '?mode=ro', uri=True)) as source:
                    with closing(sqlite3.connect(database)) as target:
                        source.backup(target)
                with closing(sqlite3.connect(database)) as prepared:
                    from tools.strike_lab.discard_fixture_27_20261002 import copy_catalog
                    copy_catalog(prepared)
                    # Historical synthetic key100 has no current portrait. Only
                    # this throwaway clone is adjusted to the qualified key101.
                    prepared.execute('delete from character_deity_selection where character_id=4')
                    prepared.execute('delete from character_deities where character_id=4 and row_key=100')
                    prepared.execute('insert into character_deity_selection values(4,101,1)')
                    prepared.execute('delete from recovered_positions where character_id=4')
                    for slot, key, count, sha in ((7, 0x400f, 3, ITEM_SOURCE), (8, 0x4010, 2, ITEM_SOURCE),
                                                  (9, 3107, 7, ITEM_SOURCE), (11, 0x400f, 1, 'a' * 64)):
                        prepared.execute('insert or replace into diagnostic_inventory_slots '
                            '(character_id,slot,item_id,count,revision,source_sha256,design_id) '
                            "values(4,?,?,?,1,?,'CUSTOM-0015')", (slot, key, count, sha))
                    prepared.commit()
                config = json.loads((SOURCE / 'server-config.json').read_text('utf-8'))
                config['world'] = {'new_character_birthplace': {'area': 4, 'scene': 3, 'kind': 0,
                    'x': 126, 'y': 126, 'navigation': str(ROOT / 'artifacts/world-atlas/kunlun-4-3.json'),
                    'coordinate_authority': 'CUSTOM-0040'}}
                config['database']['path'] = str(database)
                config['world']['owned_supply']={'enabled':True}
                config['server'].update(host='127.0.0.1', port=helper.unused_port(), character_port=0)
                config['logging'].update(file=str(here / 'server.log'), level='debug')
                config['development']['diagnostic_town'].update(player_visibility=False,
                    native_npc_placements_only=True, quest_progress=False, spawn_guides=False,
                    map_probe=False, door_routes=False)
                cfg = here / 'config.json'
                cfg.write_text(json.dumps(config), encoding='utf-8')
                endpoint = ('127.0.0.1', config['server']['port'])
                output = lifetime.enter_context((here / 'stdout.log').open('ab'))
                environment = helper.environment()
                environment['GOD2_LOG_FILE_ONLY'] = '1'
                process = subprocess.Popen([str(BINARY), '--config', str(cfg), '--run-for', '40'],
                    cwd=ROOT, env=environment, stdout=output, stderr=subprocess.STDOUT,
                    creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                lifetime.callback(helper.stop, process)
                deadline = time.monotonic() + 10
                while True:
                    self.assertIsNone(process.poll(), (here / 'stdout.log').read_text('utf-8', errors='replace'))
                    try:
                        with socket.create_connection(endpoint, timeout=.1):
                            break
                    except OSError:
                        self.assertLess(time.monotonic(), deadline, 'Private D6 candidate did not listen')
                        time.sleep(.025)

                def saved():
                    with closing(sqlite3.connect(database)) as db:
                        self.assertEqual(db.execute('pragma quick_check').fetchone(), ('ok',))
                        return {table: db.execute('select * from ' + table + ' order by 1,2').fetchall()
                                for table in TABLES}

                login = lifetime.enter_context(helper.connect(endpoint))
                helper.handshake(login)
                account, password = b'codexslow', b'labtest2345'
                login.sendall(helper.frame(*dual.credential(4, account, password)))
                helper.read_frame(login, 0x1d, 176)
                helper.read_frame(login, 4, 8)
                address = helper.read_frame(login, 5, 12)
                helper.read_frame(login, 6, 8)
                helper.read_frame(login, 0x0a, 20)
                self.assertEqual(helper.list_characters(login)[3], 1)
                game = lifetime.enter_context(helper.connect(('127.0.0.1', int.from_bytes(address[9:11], 'little'))))
                helper.handshake(game, game=True)
                game.sendall(helper.frame(*dual.credential(0, account, password)))
                helper.read_frame(game, 0x1f, 128)
                game.sendall(helper.frame(0x1a, dual.selection_payload(0)))
                helper.read_frame(game, 2, 26)
                entry = helper.read_frame(game, 0x2a, 40)
                identity = int.from_bytes(entry[3:5], 'little') & 0x3fff
                game.sendall(current_world_ready_wire(identity, (4, 3)))
                helper.silent(game)

                def project():
                    game.sendall(helper.frame(0x30, b'\0'))
                    frames = [decoder.logical(helper, game)]
                    while select.select([game], [], [], .15)[0]:
                        frames.append(decoder.logical(helper, game))
                    self.assertTrue(any(b'\xfb' in frame for frame in frames), 'Owned pet projection missing')
                    helper.silent(game)

                def log():
                    return (here / 'server.log').read_text('utf-8', errors='replace')

                def deny(logical, expected_reason, fragmented=False):
                    before = saved()
                    count = log().count('OWNED_PET2_REVERT_DENIED')
                    wire = helper.frame(logical[0], logical[1:])
                    helper.send(game, wire, fragmented=fragmented)
                    helper.silent(game)
                    deadline = time.monotonic() + 3
                    while log().count('OWNED_PET2_REVERT_DENIED') == count:
                        self.assertIsNone(process.poll(), 'Private candidate exited')
                        self.assertLess(time.monotonic(), deadline, 'D6 denial marker missing: ' + log())
                        time.sleep(.02)
                    latest = [line for line in log().splitlines() if 'OWNED_PET2_REVERT_DENIED' in line][-1]
                    self.assertIn('reason=' + expected_reason, latest)
                    self.assertIn('no_state_change no_success_reply', latest)
                    self.assertEqual(saved(), before, 'D6 request changed an owned or other character row')
                    # A second framed request must also be processed; silence
                    # asserts an open socket, not merely a successful send().
                    game.sendall(helper.frame(0x6d, b'\0'))
                    helper.silent(game)

                yield helper, decoder, game, saved, project, deny, log
        finally:
            self.assertEqual(hashlib.sha256(source_file.read_bytes()).hexdigest(), original_hash,
                             'Read-only fixture source changed')

    def test_partial_complete_invalid_and_mixed_batches(self):
        with self.server() as (helper,decoder,game,saved,project,deny,log):
            project()
            original=saved()
            for raw in (b'\x27\x24\x0c\x09\x01',b'\x27\x23\x0c\x09\0',b'\x27\x23\x0c\x09\x08'):
                game.sendall(helper.frame(raw[0],raw[1:]))
                expected=b'\x41\0\0\x09\0\x3b\x07\x09\0\0\x23\x0c'+bytes(18)+b'\x41\x23\x0c\x09\x07'
                self.assertEqual(decoder.logical(helper,game),expected)
                helper.silent(game);self.assertEqual(saved(),original)
            for raw in (b'\x27\x23\x0c\x09\x02'*2,b'\x27\x23\x0c\x09\x02\x21\x01'):
                game.sendall(helper.frame(raw[0],raw[1:]));helper.silent(game);self.assertEqual(saved(),original)
            for quantity,remaining in ((2,5),(5,0)):
                raw=b'\x30\0\x27\x23\x0c\x09'+bytes([quantity])+b'\x30\0'
                helper.send(game,helper.frame(raw[0],raw[1:]),fragmented=True)
                expected=b'\x41'+(b'\x23\x0c' if remaining else b'\0\0')+bytes([9,remaining])
                self.assertEqual(decoder.logical(helper,game),expected);helper.silent(game)
                now=saved();rows=now['diagnostic_inventory_slots']
                row=next(r for r in rows if r[0]==4 and r[1]==9)
                self.assertEqual(row[2:4],(3107 if remaining else 0,remaining))
                for table in original:
                    if table!='diagnostic_inventory_slots':self.assertEqual(now[table],original[table])
                self.assertEqual([r for r in rows if r[:2]!=(4,9)], [r for r in original['diagnostic_inventory_slots'] if r[:2]!=(4,9)])
            self.assertEqual(log().count('OWNED_BAG_DISCARD_COMMITTED'),2)

    def test_unprojected_and_truncated_never_mutate(self):
        with self.server() as (helper,decoder,game,saved,project,deny,log):
            original=saved();game.sendall(helper.frame(0x27,b'\x23\x0c\x09\x02'));helper.silent(game)
            self.assertEqual(saved(),original)
            project();original=saved();game.sendall(helper.frame(0x27,b'\x23\x0c\x09'));helper.closed(game)
            self.assertEqual(saved(),original)

if __name__=='__main__':unittest.main()
