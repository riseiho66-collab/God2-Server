"""Real TCP CUSTOM-0046 acceptance on a disposable clone only.

The 20-byte WPN operands are explicitly synthetic; this does not certify native
instance generation, formulas, appearance, rendering, or client UI acceptance.
Run with GOD2_OWNED_SERVER_CANDIDATE to select an already built candidate.
"""
from contextlib import ExitStack, closing
import json
import hashlib
import os
from pathlib import Path
import select
import socket
import sqlite3
import struct
import subprocess
import sys
import tempfile
import time
import unittest

import test_recovered_dual_connection_server as dual
import test_inventory_move_server as inventory
from test_current_world_ready_builder import current_world_ready_wire

ROOT = dual.ROOT
sys.path.insert(0, str(ROOT))
from tools.strike_lab.run_private_owned_companions import seed_weapon_transfers, WEAPON_SOURCE_SHA, CURRENT_CLIENT_SHA
from tools.strike_lab import import_native_weapons

SOURCE = ROOT / 'artifacts/playtests/private-owned-companions-20260926-01'
BINARY = Path(os.environ.get('GOD2_OWNED_SERVER_CANDIDATE',
    ROOT / 'build-town-visibility/Release/god2-server.exe'))


def clear(slot):
    return bytes((0x41, 0, 0, slot, 0))


def occupied(slot, raw):
    return bytes((0x3b, 1, slot, 0, 0)) + raw + b'\x41' + raw[:2] + bytes((slot, 1)) if any(raw[:2]) else b''


def selection(slot, key):
    return b'\x28' + struct.pack('<HBB', key, slot, 1)


class OwnedWeaponTransfersServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not BINARY.is_file() or not (SOURCE / 'town-diagnostic-accounts.db').is_file():
            raise AssertionError('Built weapon candidate and isolated source fixture required')
        dual.RecoveredDualConnectionServerTests.crypto_key = dual.key(ROOT)
        print('OWNED_WEAPON_TEST_BINARY',str(BINARY),hashlib.sha256(BINARY.read_bytes()).hexdigest(),flush=True)

    def test_owned_transfers_rejections_restart_and_scalar_reuse(self):
        helper = dual.RecoveredDualConnectionServerTests()
        decoder = inventory.InventoryMoveServerTests()
        with tempfile.TemporaryDirectory(prefix='god2-weapon-tcp-') as temporary, ExitStack() as lifetime:
            here = Path(temporary)
            database = here / 'town-diagnostic-accounts.db'
            with closing(sqlite3.connect((SOURCE / database.name).resolve().as_uri() + '?mode=ro', uri=True)) as source:
                with closing(sqlite3.connect(database)) as target:
                    source.backup(target)
                    target.execute('update recovered_positions set area=2,scene=4,x=88,y=75,revision=revision+1 where character_id=4')
                    target.commit()
            config = json.loads((SOURCE / 'server-config.json').read_text('utf-8'))
            config['database']['path'] = str(database)
            config['server'].update(host='127.0.0.1', port=helper.unused_port(), character_port=0)
            config['logging'].update(file=str(here / 'server.log'), level='debug')
            config['protocol']['packet_dump'] = False
            config['development'].update(diagnostic_world_resources=False, diagnostic_world_supply=False)
            config['development']['diagnostic_town'].update(player_visibility=False,
                native_npc_placements_only=True, quest_progress=False, map_probe=False)
            config.setdefault('world', {})['owned_weapon_transfers'] = {'enabled': True}
            config['world']['clock'] = {'enabled': False}
            cfg = here / 'config.json'
            cfg.write_text(json.dumps(config), encoding='utf-8')
            endpoint = ('127.0.0.1', config['server']['port'])
            env = helper.environment()
            env['GOD2_LOG_FILE_ONLY'] = '1'
            flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
            migration = subprocess.run([str(BINARY), '--config', str(cfg), '--migrate-only'],
                cwd=ROOT, env=env, creationflags=flags, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, timeout=20)
            self.assertEqual(migration.returncode, 0, migration.stdout.decode('utf-8', errors='replace')[-2000:])
            records = import_native_weapons.cached_records(ROOT / 'artifacts/research/native-weapons-20260926/records.json')
            with closing(sqlite3.connect(database)) as db:
                import_native_weapons.import_catalog(db, records=records)
                # Different owner's explicit instance must never authorize this actor.
                db.execute("insert into diagnostic_inventory_slots values(5,0,2,1,1,?,'CUSTOM-0015') "
                    'on conflict(character_id,slot) do update set item_id=2,count=1,revision=1,source_sha256=excluded.source_sha256', (WEAPON_SOURCE_SHA,))
                db.execute("insert into character_weapon_slot_metadata values(5,0,?,1,'CUSTOM_TEST_NOT_NATIVE',"
                    "'isolated-other-owner',?,?,'CUSTOM-0046')",
                    (bytes.fromhex('020001000000001e000000000a00000000000000'), WEAPON_SOURCE_SHA, CURRENT_CLIENT_SHA))
                db.commit()

            def snapshot():
                with closing(sqlite3.connect(database)) as db:
                    self.assertEqual(db.execute('pragma quick_check').fetchone(), ('ok',))
                    tables = ('diagnostic_inventory_slots', 'character_weapon_slot_metadata',
                        'character_resources', 'character_role_snapshots', 'character_deities',
                        'character_deity_selection', 'character_pet2_slots', 'character_role_auxiliary_snapshots')
                    return {table: db.execute('select * from ' + table + ' order by 1,2').fetchall() for table in tables}

            initial = snapshot()
            stable_tables = tuple(t for t in initial if t not in ('diagnostic_inventory_slots', 'character_weapon_slot_metadata'))

            def unchanged_authorities():
                current = snapshot()
                for table in stable_tables:
                    self.assertEqual(current[table], initial[table], table)
                for table in ('diagnostic_inventory_slots', 'character_weapon_slot_metadata'):
                    self.assertEqual([r for r in current[table] if r[0] != 4],
                                     [r for r in initial[table] if r[0] != 4], table + ' other owner')

            def slots():
                with closing(sqlite3.connect(database)) as db:
                    scalars = db.execute('select slot,item_id,count,revision from diagnostic_inventory_slots where character_id=4 order by slot').fetchall()
                    meta = {r[0]: r[1:] for r in db.execute('select slot,logical20,revision,origin,provenance,source_sha256,client_sha256,design_id from character_weapon_slot_metadata where character_id=4')}
                return {slot: {'item': item, 'count': count, 'revision': revision,
                    'raw': meta[slot][0] if slot in meta else bytes(20),
                    'meta': meta.get(slot)} for slot, item, count, revision in scalars}

            def launch():
                output = lifetime.enter_context((here / 'stdout.log').open('ab'))
                process = subprocess.Popen([str(BINARY), '--config', str(cfg), '--run-for', '50'],
                    cwd=ROOT, env=env, stdout=output, stderr=subprocess.STDOUT, creationflags=flags)
                lifetime.callback(helper.stop, process)
                deadline = time.monotonic() + 8
                while True:
                    self.assertIsNone(process.poll(), (here / 'stdout.log').read_text('utf-8', errors='replace')[-3000:])
                    try:
                        with socket.create_connection(endpoint, timeout=.1):
                            return process
                    except OSError:
                        self.assertLess(time.monotonic(), deadline, 'Isolated server did not listen')
                        time.sleep(.025)

            def drain(game, required=False):
                frames = [decoder.logical(helper, game)] if required else []
                while select.select([game], [], [], .15)[0]:
                    frames.append(decoder.logical(helper, game))
                return frames

            def send(game, logical):
                game.sendall(helper.frame(logical[0], logical[1:]))

            def rejected(game, logical):
                before = snapshot()
                with closing(sqlite3.connect(database)) as db:
                    position = db.execute('select * from recovered_positions order by character_id').fetchall()
                send(game, logical)
                if select.select([game], [], [], .15)[0]:
                    self.fail('Unexpected response/EOF for ' + logical.hex() + ': ' +
                        game.recv(256).hex() + '\n' + (here / 'server.log').read_text('utf-8', errors='replace')[-1800:])
                helper.silent(game)  # EOF also fails, so rejection keeps TCP alive.
                self.assertEqual(snapshot(), before, 'Rejected operation changed saved rows')
                with closing(sqlite3.connect(database)) as db:
                    self.assertEqual(db.execute('select * from recovered_positions order by character_id').fetchall(),
                                     position, 'Rejected mixed frame applied its movement')

            def enter(connections, expected_weapon_slots=None):
                login = connections.enter_context(helper.connect(endpoint)); helper.handshake(login)
                credentials = (b'codexslow', b'labtest2345')
                login.sendall(helper.frame(*dual.credential(4, *credentials)))
                helper.read_frame(login, 0x1d, 176); helper.read_frame(login, 4, 8)
                address = helper.read_frame(login, 5, 12)
                helper.read_frame(login, 6, 8); helper.read_frame(login, 0x0a, 20)
                self.assertEqual(helper.list_characters(login)[3], 1)
                game = connections.enter_context(helper.connect(('127.0.0.1', int.from_bytes(address[9:11], 'little'))))
                helper.handshake(game, game=True)
                game.sendall(helper.frame(*dual.credential(0, *credentials))); helper.read_frame(game, 0x1f, 128)
                game.sendall(helper.frame(0x1a, dual.selection_payload(0))); helper.read_frame(game, 2, 26)
                entry = helper.read_frame(game, 0x2a, 40)
                self.assertEqual(int.from_bytes(entry[3:5], 'little') & 0x3fff, 4)
                game.sendall(current_world_ready_wire(4, (4, 3))); helper.silent(game)
                if expected_weapon_slots is not None:
                    rejected(game, selection(0, 1))  # World tail admitted; no owned projection yet.
                game.sendall(helper.frame(0x30, b'\0'))
                frames = drain(game, required=True)
                self.assertFalse(any(frame[:1] in (b'\xda', b'\x2c') for frame in frames),
                                 'Unowned final-stat or appearance frame fabricated')
                if expected_weapon_slots is not None:
                    expected = b''.join(clear(s) + occupied(s, row['raw']) for s, row in expected_weapon_slots.items()
                        if row['item'] in (0, 1, 2))
                    self.assertIn(expected, frames, 'Exact persisted weapon instance projection missing')
                # Genuine post-admission movement roundtrip, not merely an initial snapshot.
                game.sendall(helper.frame(0x2e, struct.pack('<HHBB', 88, 75, 1, 0xa5)))
                self.assertEqual(decoder.logical(helper, game), b'\x5d\x01')
                helper.silent(game)
                unchanged_authorities()
                return game

            process = launch()
            with ExitStack() as connections:
                game = enter(connections)
                # With scalar bag policy disabled, an unrelated saved map move
                # is denied silently; enabling weapon support must not turn it
                # into a connection-closing legacy callback.
                for raw in (selection(0, 2), selection(34, 2), b'\x24\x00\x05'):
                    rejected(game, raw)
            helper.stop(process)
            self.assertEqual(snapshot(), initial, 'Missing owned weapon rows were automatically granted')

            with closing(sqlite3.connect(database)) as db:
                seed_weapon_transfers(db); db.commit()
            process = launch()
            with ExitStack() as connections:
                game = enter(connections, slots())
                for raw in (selection(0, 2), selection(0, 1) + selection(0, 1),
                            selection(0, 1) + b'\x24\x00\x05',
                            selection(0, 1) + b'\x2e' + struct.pack('<HHBB', 88, 75, 2, 0xa5)):
                    rejected(game, raw)
                game.sendall(helper.frame(0x2e, struct.pack('<HHBB', 88, 75, 2, 0xa5)))
                self.assertEqual(decoder.logical(helper, game), b'\x5d\x02',
                                 'Rejected mixed frame advanced the movement sequence')
                helper.silent(game)

                def transfer(source, destination, logical):
                    before = slots()
                    send(game, logical)
                    raw_reply = decoder.logical(helper, game)
                    after = slots()
                    expected_raw = {}
                    for slot, donor in ((source, destination), (destination, source)):
                        previous, incoming = before[slot], before[donor]
                        raw = incoming['raw'] if incoming['count'] else b'\0\0' + previous['raw'][2:]
                        expected_raw[slot] = raw
                        self.assertEqual(after[slot]['raw'], raw)
                        self.assertEqual(after[slot]['revision'], previous['revision'] + 1)
                        self.assertEqual((after[slot]['item'], after[slot]['count']), (incoming['item'], incoming['count']))
                        meta = after[slot]['meta']
                        self.assertEqual(meta[1], after[slot]['revision'])
                        self.assertEqual(meta[4:], (WEAPON_SOURCE_SHA, CURRENT_CLIENT_SHA, 'CUSTOM-0046'))
                        self.assertEqual(meta[2:4], incoming['meta'][2:4] if incoming['count'] else
                            ('EMPTY_SLOT_POLICY', 'CUSTOM-0046/clear-previous-instance'))
                    expected = clear(source) + clear(destination) + occupied(source, expected_raw[source]) + occupied(destination, expected_raw[destination])
                    self.assertEqual(raw_reply, expected, 'Unexpected records/stat/appearance or truncated instance reply')
                    self.assertEqual({s: r for s, r in after.items() if s not in (source, destination)},
                                     {s: r for s, r in before.items() if s not in (source, destination)})
                    helper.silent(game)
                    unchanged_authorities()

                transfer(0, 34, selection(0, 1))
                transfer(1, 34, selection(1, 2))
                transfer(34, 0, selection(34, 2))
                transfer(0, 34, selection(0, 2))
                transfer(1, 12, b'\x24\x01\x0c')
                transfer(12, 2, b'\x24\x0c\x02')  # source > destination, retained full20.
            helper.stop(process)
            persisted = snapshot()
            process = launch()
            with ExitStack() as connections:
                game = enter(connections, slots())
                self.assertEqual(snapshot(), persisted, 'Restart altered instances/revisions/provenance')
                rejected(game, selection(34, 1))
            helper.stop(process)

            # A later scalar map placement must retire only the empty overlay.
            # Fill the rest of the bag explicitly in this disposable fixture to
            # test unequip denial when no owned empty cell remains.
            with closing(sqlite3.connect(database)) as db:
                self.assertIsNotNone(db.execute('select 1 from character_weapon_slot_metadata where character_id=4 and slot=0 and origin=\'EMPTY_SLOT_POLICY\'').fetchone())
                db.execute('update diagnostic_inventory_slots set item_id=5569,count=1,revision=revision+1 where character_id=4 and slot<30 and count=0')
                self.assertIsNone(db.execute('select 1 from character_weapon_slot_metadata where character_id=4 and slot=0').fetchone())
                db.commit()
            full = snapshot()
            process = launch()
            with ExitStack() as connections:
                game = enter(connections, slots())
                rejected(game, selection(34, 2))
                self.assertEqual(snapshot(), full, 'Full bag rejection or scalar reuse changed data')
            helper.stop(process)
            unchanged_authorities()
            log = (here / 'server.log').read_text('utf-8', errors='replace')
            self.assertEqual(log.count('OWNED_WEAPON_TRANSFER_COMMITTED'), 6)


if __name__ == '__main__':
    unittest.main()
