"""Real isolated TCP/SQLite C2S24 route; synthetic peer, no desktop/client launch."""
from contextlib import ExitStack, closing
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

ROOT = dual.ROOT
SOURCE = ROOT / 'artifacts/playtests/private-chain-endtoend-20260924-01'
SAVE_SOURCE = ROOT / 'artifacts/playtests/private-game-2598-20260923-01/town-diagnostic-accounts.db'
BINARY = Path(os.environ.get('GOD2_INVENTORY_MOVE_TEST_BINARY',
                            ROOT / 'build-town-visibility/Release/god2-server.exe'))
ITEM_SOURCE = '70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731'


def projection(slot, item, count):
    clear = bytes((0x41, 0, 0, slot, 0))
    if not count:
        return clear
    identity = item.to_bytes(2, 'little')
    return (clear + bytes((0x3b, count, slot, 0, 0)) + identity + bytes(18)
            + b'\x41' + identity + bytes((slot, count)))


class InventoryMoveServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not BINARY.is_file() or not SAVE_SOURCE.is_file():
            raise AssertionError('Built server and isolated town save fixture required')
        # Reuse the wire helpers without requiring their unrelated binary path.
        dual.RecoveredDualConnectionServerTests.crypto_key = dual.key(ROOT)
        if len(dual.RecoveredDualConnectionServerTests.crypto_key) != 256:
            raise AssertionError('Invalid native transport key fixture')

    def logical(self, helper, peer):
        header = helper.receive(peer, 2)
        length = int.from_bytes(header, 'little')
        self.assertGreaterEqual(length, 4)
        self.assertLessEqual(length, 0xa03)
        previous = 0
        plain = bytearray(header)
        for index, value in enumerate(helper.receive(peer, length - 2)):
            previous = ((value + 3 - previous) & 255) ^ helper.crypto_key[index & 255]
            plain.append(previous)
        self.assertEqual(plain[-1], sum(value + 0x3c for value in plain[:-1]) & 255)
        return bytes(plain[2:-1])

    def test_moves_swaps_restart_restore_and_resources_unchanged(self):
        self.run_inventory_case()

    def test_unfinished_quest_reserves_destination_zero_without_database_mutation(self):
        for stage in range(3):
            with self.subTest(stage=stage):
                self.run_inventory_case(reserved_stage=stage)

    def test_town_and_world_supply_reject_incompatible_battle_rounds(self):
        self.run_inventory_case(world_supply=True)

    def run_inventory_case(self, reserved_stage=None, world_supply=False):
        helper = dual.RecoveredDualConnectionServerTests()
        with tempfile.TemporaryDirectory(prefix='god2-owned-bag-') as temporary, ExitStack() as lifetime:
            root = Path(temporary)
            database = root / 'town-diagnostic-accounts.db'
            with closing(sqlite3.connect(SAVE_SOURCE.resolve().as_uri() + '?mode=ro', uri=True)) as source:
                with closing(sqlite3.connect(database)) as target:
                    source.backup(target)
                    self.assertEqual(target.execute(
                        'select item_id,count from diagnostic_inventory_slots where character_id=4 and slot=0'
                    ).fetchone(), (5569, 1))
                    # Explicit fixture grants, isolated from the original save.
                    for slot, item, count in ((12, 3101, 3), (16, 3107, 7)):
                        self.assertIsNone(target.execute(
                            'select slot from diagnostic_inventory_slots where character_id=4 and slot=?', (slot,)
                        ).fetchone())
                        target.execute('insert into diagnostic_inventory_slots '
                                       '(character_id,slot,item_id,count,revision,source_sha256,design_id) '
                                       "values(4,?,?,?,1,?,'CUSTOM-0015')", (slot, item, count, ITEM_SOURCE))
                    target.execute('update recovered_positions set area=2,scene=4,x=88,y=75,'
                                   'revision=revision+1 where character_id=4')
                    if reserved_stage is not None:
                        if reserved_stage == 0:
                            target.execute('delete from diagnostic_town_guide_progress where character_id=4')
                        else:
                            target.execute('update diagnostic_town_guide_progress set stage=?,journal_description=? '
                                           'where character_id=4', (reserved_stage, reserved_stage))
                        target.execute('delete from diagnostic_town_guide_reward where character_id=4')
                        target.execute('update diagnostic_inventory_slots set item_id=0,count=0 '
                                       'where character_id=4 and slot=0')
                    target.commit()

            def snapshot():
                with closing(sqlite3.connect(database)) as db:
                    self.assertEqual(db.execute('pragma quick_check').fetchone(), ('ok',))
                    return {
                        'bag': db.execute('select slot,item_id,count,revision,source_sha256,design_id '
                                          'from diagnostic_inventory_slots where character_id=4 order by slot').fetchall(),
                        'other': db.execute('select * from diagnostic_inventory_slots where character_id!=4 '
                                            'order by character_id,slot').fetchall(),
                        'resources': db.execute('select * from character_resources order by character_id').fetchall(),
                        'rewards': db.execute('select * from diagnostic_town_guide_reward order by character_id').fetchall(),
                    }

            config = json.loads((SOURCE / 'server-config.json').read_text(encoding='utf-8'))
            config['server'].update(host='127.0.0.1', port=helper.unused_port(), character_port=0)
            config['database']['path'] = str(database)
            config['logging'].update(file=str(root / 'server.log'), level='debug')
            config['development']['diagnostic_world_supply'] = world_supply
            if world_supply:
                config['development']['diagnostic_world_resources'] = True
                config['development']['diagnostic_battle_rounds'] = 3
            config['development']['diagnostic_town']['player_visibility'] = False
            config_path = root / 'config.json'
            config_path.write_text(json.dumps(config), encoding='utf-8')
            endpoint = ('127.0.0.1', config['server']['port'])

            def launch():
                output = lifetime.enter_context((root / 'stdout.log').open('ab'))
                environment = helper.environment()
                # INFO commit markers must be flushed before bounded process stop.
                environment['GOD2_LOG_FILE_ONLY'] = '1'
                process = subprocess.Popen([str(BINARY), '--config', str(config_path), '--run-for', '45'],
                    cwd=ROOT, stdout=output, stderr=subprocess.STDOUT, env=environment,
                    creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                lifetime.callback(helper.stop, process)
                deadline = time.monotonic() + 8
                while True:
                    self.assertIsNone(process.poll(), 'Isolated inventory server exited')
                    try:
                        with socket.create_connection(endpoint, timeout=.1):
                            return process
                    except OSError:
                        self.assertLess(time.monotonic(), deadline, 'Isolated inventory server did not listen')
                        time.sleep(.025)

            def enter():
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
                self.assertEqual(int.from_bytes(entry[3:5], 'little') & 0x3fff, 4)
                game.sendall(current_world_ready_wire(4, (4, 3)))
                helper.silent(game)
                game.sendall(helper.frame(0x30, b'\0'))
                frames = [self.logical(helper, game)]
                while select.select([game], [], [], .15)[0]:
                    frames.append(self.logical(helper, game))
                saved = snapshot()['bag']
                self.assertEqual([row[0] for row in saved], list(range(30)))
                expected = b''.join(projection(row[0], row[1], row[2]) for row in saved)
                self.assertIn(expected, b''.join(frames), 'Complete saved bag was not restored')
                return game

            original = snapshot()
            if world_supply:
                # Current config gates cannot admit both diagnostic modes:
                # world supply requires three rounds, town battle requires one.
                # Keep this limitation explicit, rather than report a TCP pass
                # for an unreachable map/supply combination.
                result = subprocess.run([str(BINARY), '--config', str(config_path), '--run-for', '1'],
                    cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=helper.environment(),
                    creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0), timeout=8)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(b'Town battle requires isolated one-round durable skill fixture', result.stdout)
                self.assertEqual(snapshot(), original)
                return
            process = launch()
            game = enter()
            provisioned = snapshot()
            for field in ('other', 'resources', 'rewards'):
                self.assertEqual(provisioned[field], original[field], field)

            if reserved_stage is not None:
                # Compare every persisted table, including revisions and quest
                # state, after admission has finished provisioning empty cells.
                def database_dump():
                    with closing(sqlite3.connect(database)) as db:
                        return tuple(db.iterdump())
                before = database_dump()
                game.sendall(helper.frame(0x24, bytes((12, 0))))
                self.assertEqual(self.logical(helper, game), projection(12, 3101, 3) + projection(0, 0, 0))
                helper.silent(game)
                self.assertEqual(database_dump(), before, 'Reserved destination mutated the database')
                self.assertEqual(snapshot(), provisioned)
                game.close()
                helper.stop(process)
                log = (root / 'server.log').read_text(encoding='utf-8', errors='replace')
                self.assertNotIn('OWNED_BAG_MOVE_COMMITTED', log)
                return

            def move(source, destination):
                before = snapshot()
                rows = {row[0]: row for row in before['bag']}
                source_row, destination_row = rows[source], rows[destination]
                game.sendall(helper.frame(0x24, bytes((source, destination))))
                reply = self.logical(helper, game)
                self.assertEqual(reply, projection(source, destination_row[1], destination_row[2])
                                 + projection(destination, source_row[1], source_row[2]))
                after = snapshot()
                expected = dict(rows)
                expected[source] = (source, *destination_row[1:3], source_row[3] + 1, *destination_row[4:])
                expected[destination] = (destination, *source_row[1:3], destination_row[3] + 1, *source_row[4:])
                self.assertEqual(after['bag'], [expected[index] for index in sorted(expected)])
                for field in ('other', 'resources', 'rewards'):
                    self.assertEqual(after[field], original[field], field)

            move(0, 5)
            move(5, 0)
            before_empty = snapshot()
            game.sendall(helper.frame(0x24, b'\x01\x02'))
            self.assertEqual(self.logical(helper, game), projection(1, 0, 0) + projection(2, 0, 0))
            self.assertEqual(snapshot(), before_empty)
            move(12, 16)
            move(0, 29)
            committed = snapshot()
            game.close()
            helper.stop(process)
            # Inspect the completed transaction process before restart.
            log = (root / 'server.log').read_text(encoding='utf-8', errors='replace')
            self.assertEqual(log.count('OWNED_BAG_MOVE_COMMITTED'), 4)
            process = launch()
            game = enter()
            self.assertEqual(snapshot(), committed, 'Restart reinitialized or lost saved inventory')
            # Item use must find the moved map, rather than retain a slot0 assumption.
            game.sendall(helper.frame(0x25, (5569).to_bytes(2, 'little') + b'\x1d\0'))
            self.assertEqual(self.logical(helper, game), bytes.fromhex('3f0100'))
            self.assertEqual(snapshot(), committed, 'Map panel lookup mutated inventory/resources')


if __name__ == '__main__':
    unittest.main()
