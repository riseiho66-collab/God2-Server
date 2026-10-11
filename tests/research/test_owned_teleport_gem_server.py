"""Owned native gem TCP routes against a disposable schema40 database.

Synthetic socket peer and explicit synthetic instance fixtures; not actual-client
acceptance or an item acquisition path. The source save is opened read-only.
"""
from contextlib import ExitStack, closing, contextmanager
import hashlib
import json
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import tempfile
import time
from types import SimpleNamespace
import unittest

import test_owned_role_text_server as role

ROOT = role.ROOT
SOURCE = role.SOURCE
BINARY = Path(os.environ.get('GOD2_TELEPORT_GEM_TEST_BINARY',
                            ROOT / 'build-town-visibility/Release/god2-server-native-results.exe'))
ITEM_SOURCE = '70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731'
MENU = bytes.fromhex('6db73e180181000a0005000000') + bytes(16)
TRANSFER = bytes.fromhex('6102010000') + ((56 << 2) | (75 << 17)).to_bytes(4, 'little')


def metadata(charges):
    return bytes((0xb7, 0x3e, 8, charges << 1)) + bytes(range(0x81, 0x91))


def projection(slot, charges):
    clear = bytes((0x41, 0, 0, slot, 0))
    return clear if not charges else (clear + bytes((0x3b, 1, slot, 0, 0)) + metadata(charges)
                                     + bytes((0x41, 0xb7, 0x3e, slot, 1)))


def use(slot=12, target=None):
    return ((b'\x25' if target is None else b'\x26' + target.to_bytes(2, 'little'))
            + b'\xb7\x3e' + bytes((slot, 0xa5)))


SELECT = b'\x99\xb7\x3e\x05\xa5'
CANCEL = b'\x86\x04\0\xa5\x5a'


class OwnedTeleportGemServerTests(unittest.TestCase):
    drain = role.OwnedRoleTextServerTests.drain
    enter = role.OwnedRoleTextServerTests.enter

    @classmethod
    def setUpClass(cls):
        if not BINARY.is_file() or not (SOURCE / 'town-diagnostic-accounts.db').is_file():
            raise AssertionError('Built candidate and isolated companion fixture required')
        role.dual.RecoveredDualConnectionServerTests.crypto_key = role.dual.key(ROOT)
        print('Gem candidate:', BINARY, 'SHA256', hashlib.sha256(BINARY.read_bytes()).hexdigest(), flush=True)

    @contextmanager
    def server(self, charges=2, restore_mode=None):
        helper = role.dual.RecoveredDualConnectionServerTests()
        decoder = role.inventory.InventoryMoveServerTests()
        source_file = SOURCE / 'town-diagnostic-accounts.db'
        original_hash = hashlib.sha256(source_file.read_bytes()).hexdigest()
        try:
            with tempfile.TemporaryDirectory(prefix='god2-gem-tcp-') as tmp, ExitStack() as lifetime:
                here = Path(tmp)
                database = here / 'town-diagnostic-accounts.db'
                with closing(sqlite3.connect(source_file.resolve().as_uri() + '?mode=ro', uri=True)) as source:
                    with closing(sqlite3.connect(database)) as target:
                        source.backup(target)
                config = json.loads((SOURCE / 'server-config.json').read_text('utf-8'))
                config['world'] = {'owned_teleport_gem': {'enabled': True}, 'clock': {'enabled': False}}
                config['database']['path'] = str(database)
                config['server'].update(host='127.0.0.1', port=helper.unused_port(), character_port=0)
                config['logging'].update(file=str(here / 'server.log'), level='debug')
                config['protocol']['packet_dump'] = False
                config['development']['diagnostic_town'].update(player_visibility=False,
                    native_npc_placements_only=True, quest_progress=False, spawn_guides=True,
                    map_probe=False, door_routes=True, source_consensus=True, island_routes=True,
                    island_navigation=str(ROOT / 'artifacts/world-atlas/island01-entry-2-0.json'))
                if restore_mode is not None:
                    self.assertIn(restore_mode, ('town', 'resource'))
                    # Keep the legacy non-owned-supply branch enabled. This exact
                    # combination previously reached scalar projection after full20.
                    config['world']['owned_supply'] = {'enabled': False}
                    config['development']['diagnostic_town']['quest_progress'] = True
                if restore_mode == 'resource':
                    # Existing config guards require the one-round diagnostic
                    # battle/door bundle for world resources in this DB basename.
                    # World-supply cannot combine with that bundle: it requires
                    # three rounds. Preserve both guards; no battle is requested.
                    config['development']['diagnostic_town'].update(
                        map_probe=True, battle_after_quest=True, door_after_battle=True)
                    for flag in ('diagnostic_battle_transition','diagnostic_battle_participants',
                                 'diagnostic_battle_player_appearance','diagnostic_battle_animations',
                                 'diagnostic_battle_skill_seed','diagnostic_battle_skill_settlement',
                                 'diagnostic_battle_terminal','diagnostic_battle_resources',
                                 'diagnostic_world_resources'):
                        config['development'][flag] = True
                    config['development']['diagnostic_battle_rounds'] = 1
                    config['development']['diagnostic_world_supply'] = False
                cfg = here / 'config.json'
                cfg.write_text(json.dumps(config), encoding='utf-8')
                migrated = subprocess.run([str(BINARY), '--config', str(cfg), '--migrate-only'],
                    cwd=ROOT, env=helper.environment(), capture_output=True, timeout=30,
                    creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                self.assertEqual(migrated.returncode, 0, migrated.stdout.decode('utf-8', errors='replace')
                                 + migrated.stderr.decode('utf-8', errors='replace'))
                with closing(sqlite3.connect(database)) as db:
                    db.execute('pragma foreign_keys=on')
                    db.execute('delete from character_deity_selection where character_id=4')
                    db.execute('delete from character_deities where character_id=4 and row_key=100')
                    db.execute('insert into character_deity_selection values(4,101,1)')
                    db.execute('insert or replace into recovered_positions values(4,2,0,477,210,20)')
                    # Explicit synthetic fixtures in this temporary clone only. No default
                    # charges are inferred from scalar inventory, and no source file is written.
                    for character, slot, item, count in ((4,12,16055,1),(4,13,0,0),
                                                        (4,15,3101,2),(4,16,16055,1),
                                                        (5,14,16055,1)):
                        db.execute('insert or replace into diagnostic_inventory_slots values(?,?,?,?,?,?,?)',
                                   (character,slot,item,count,9,ITEM_SOURCE,'CUSTOM-0015'))
                    for character, slot in ((4,12),(5,14)):
                        db.execute('insert into character_teleport_gem_metadata values(?,?,?,?,?,?,?,?)',
                            (character,slot,metadata(charges),9,'CUSTOM_TEST_NOT_NATIVE',
                             'TCP isolated synthetic full20; no production grant',ITEM_SOURCE,'CUSTOM-0057'))
                    db.commit()
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
                            self.assertLess(time.monotonic(), deadline, 'Private gem candidate did not listen')
                            time.sleep(.025)

                def snapshot():
                    with closing(sqlite3.connect(database)) as db:
                        self.assertEqual(db.execute('pragma quick_check').fetchone(), ('ok',))
                        return {table: db.execute('select * from ' + table + ' order by 1,2').fetchall()
                                for table in ('diagnostic_inventory_slots','character_teleport_gem_metadata',
                                              'recovered_positions','character_resources','character_role_text')}

                state = SimpleNamespace(helper=helper, decoder=decoder, database=database, endpoint=endpoint,
                    launch=launch, process=launch(), snapshot=snapshot,
                    log=lambda: (here / 'server.log').read_text('utf-8', errors='replace'))
                try:
                    yield state
                    self.assertIsNone(state.process.poll(), state.log()[-4000:])
                except BaseException:
                    print('Gem candidate failure log:\n' + state.log()[-12000:].encode(
                        'ascii', errors='backslashreplace').decode('ascii'), flush=True)
                    raise
        finally:
            self.assertEqual(hashlib.sha256(source_file.read_bytes()).hexdigest(), original_hash,
                             'Read-only source fixture changed')

    def send(self, state, game, raw):
        game.sendall(state.helper.frame(raw[0], raw[1:]))

    def reject(self, state, game, raw):
        before = state.snapshot()
        self.send(state, game, raw)
        state.helper.silent(game)
        self.assertEqual(state.snapshot(), before, 'Rejected/cancelled request mutated saved state')

    def open(self, state, game, raw=None):
        before = state.snapshot()
        self.send(state, game, use() if raw is None else raw)
        self.assertEqual(state.decoder.logical(state.helper, game), MENU)
        state.helper.silent(game)
        self.assertEqual(state.snapshot(), before, 'Opening menu consumed a charge')

    def assert_saved(self, state, charges, revision=10, position=(2,4,56,75,21), slot=12):
        with closing(sqlite3.connect(state.database)) as db:
            self.assertEqual(db.execute('select item_id,count,revision from diagnostic_inventory_slots '
                                       'where character_id=4 and slot=?', (slot,)).fetchone(),
                             (16055,1,revision) if charges else (0,0,revision))
            row = db.execute('select metadata20,revision from character_teleport_gem_metadata '
                             'where character_id=4 and slot=?', (slot,)).fetchone()
            self.assertEqual(row, (metadata(charges),revision) if charges else None)
            self.assertEqual(db.execute('select area,scene,x,y,revision from recovered_positions '
                                       'where character_id=4').fetchone(), position)

    def test_native25_26_menu_cancel_foreign_stale_and_mixed_are_nonmutating(self):
        with self.server() as state:
            initial = state.snapshot()
            with self.enter(state, project=False) as game:
                self.reject(state, game, use())  # Before first owned inventory projection.
                self.send(state, game, b'\x30\0')
                frames = self.drain(state, game, first=True)
                self.assertIn(projection(12,2), frames)
                for raw in (b'\x6d\0', use(target=5), use(14), use(16), SELECT,
                            use()+use(), use()+b'\x24\x0c\x0d'):
                    self.reject(state, game, raw)
                self.open(state, game, b'\x30\0'+use()+b'\x1f\0')
                self.reject(state, game, CANCEL)
                self.reject(state, game, SELECT)
                self.open(state, game, use(target=4))
                self.reject(state, game, SELECT+SELECT)
                self.reject(state, game, SELECT+role.request(b'mixed'))
                self.reject(state, game, role.request(b'mixed')+SELECT)
                self.reject(state, game, SELECT+b'\x2e\xdd\x01\xd2\0\x01\xa5')
                # Atomic external fixture revision change makes this offer stale.
                with closing(sqlite3.connect(state.database)) as db:
                    db.execute('update diagnostic_inventory_slots set revision=revision+1 where character_id=4 and slot=12')
                    db.execute('update character_teleport_gem_metadata set revision=revision+1 where character_id=4 and slot=12')
                    db.commit()
                self.reject(state, game, SELECT)
                self.open(state, game)
                self.reject(state, game, CANCEL)
                self.assert_saved(state, 2, revision=10, position=(2,0,477,210,20))
            final = state.snapshot()
            self.assertEqual(initial['character_resources'], final['character_resources'])
            self.assertEqual(initial['character_role_text'], final['character_role_text'])
            self.assertEqual([x for x in initial['character_teleport_gem_metadata'] if x[0]==5],
                             [x for x in final['character_teleport_gem_metadata'] if x[0]==5])

    def test_whole_move_preserves_metadata_cancels_offer_and_rejects_unknown(self):
        with self.server() as state, self.enter(state) as game:
            self.open(state, game)
            self.reject(state, game, b'\x24\x0c\x0f')  # Ordinary destination.
            self.reject(state, game, b'\x24\x0c\x0d'+role.request(b'mixed'))
            self.send(state, game, b'\x24\x0c\x0d')
            self.assertEqual(state.decoder.logical(state.helper, game), projection(12,0)+projection(13,2))
            self.assert_saved(state, 2, slot=13, position=(2,0,477,210,20))
            self.reject(state, game, SELECT)
            self.reject(state, game, use())
            self.open(state, game, use(13))
            self.reject(state, game, CANCEL)

    def test_atomic_charge_position_commit_failure_retry_duplicate_and_restart(self):
        with self.server() as state:
            foreign = [row for row in state.snapshot()['character_teleport_gem_metadata'] if row[0]==5]
            with self.enter(state) as game:
                self.open(state, game, use(target=4))
                with closing(sqlite3.connect(state.database)) as db:
                    db.execute("create trigger fixture_abort_position before update on recovered_positions "
                               "begin select raise(abort,'fixture position failure');end")
                    db.commit()
                self.reject(state, game, SELECT)
                self.assert_saved(state, 2, revision=9, position=(2,0,477,210,20))
                with closing(sqlite3.connect(state.database)) as db:
                    db.execute('drop trigger fixture_abort_position');db.commit()
                self.send(state, game, SELECT)
                self.assertEqual(state.decoder.logical(state.helper, game), projection(12,1)+TRANSFER)
                self.assert_saved(state, 1)
                self.reject(state, game, SELECT)
                self.reject(state, game, use())  # Destination transfer still pending.
                self.send(state, game, b'\x1c\x04\0\0\0')
                state.helper.silent(game)
                self.send(state, game, b'\x30\0')
                self.drain(state, game)
                self.reject(state, game, use())  # Town source is not an allowed edge.
            state.helper.stop(state.process)
            state.process = state.launch()
            with self.enter(state, project=False) as game:
                self.send(state, game, b'\x30\0')
                frames = self.drain(state, game, first=True)
                self.assertIn(projection(12,1), frames)
                self.assert_saved(state, 1)
                self.reject(state, game, SELECT)
            self.assertEqual(foreign, [row for row in state.snapshot()['character_teleport_gem_metadata'] if row[0]==5])
            self.assertEqual(state.log().count('OWNED_TELEPORT_GEM_COMMITTED'), 1)

    def test_last_charge_exhaustion_is_persistent_and_never_regranted(self):
        with self.server(charges=1) as state:
            with self.enter(state) as game:
                self.open(state, game)
                self.send(state, game, SELECT)
                self.assertEqual(state.decoder.logical(state.helper, game), projection(12,0)+TRANSFER)
                self.assert_saved(state, 0)
                self.reject(state, game, SELECT)
            state.helper.stop(state.process)
            state.process = state.launch()
            with self.enter(state, project=False) as game:
                self.send(state, game, b'\x30\0')
                frames = self.drain(state, game, first=True)
                self.assertFalse(any(projection(12,1) in frame for frame in frames))
                self.assert_saved(state, 0)
                self.reject(state, game, use())
                self.reject(state, game, SELECT)

    def legacy_restore(self, mode):
        with self.server(restore_mode=mode) as state:
            before = state.snapshot()
            with self.enter(state, project=False) as game:
                self.send(state, game, b'\x30\0')
                frames = self.drain(state, game, first=True)
                self.assertIn(projection(12,2), frames, 'Full20 instance was not initially projected')
                # The town restore follows full20; the resource restore runs on
                # the next tick after that town handler has completed.
                self.send(state, game, b'\x30\0')
                frames += self.drain(state, game)
                state.helper.silent(game)
                self.assertEqual(frames.count(projection(12,2)), 1)
                for frame in frames:
                    if frame != projection(12,2):
                        self.assertNotIn(projection(12,0), frame,
                                         'Later scalar restore cleared the full20 gem')
                        self.assertNotIn(b'\x41\xb7\x3e\x0c\x01', frame,
                                         'Later scalar restore reprojected the gem')
                self.open(state, game)
                self.reject(state, game, CANCEL)
                self.assert_saved(state, 2, revision=9, position=(2,0,477,210,20))
                self.assertEqual(state.snapshot(), before)
                if mode == 'resource':
                    self.assertIn('DIAGNOSTIC_WORLD_RESOURCES_ALREADY_RESTORED', state.log())
                self.assertNotIn('Unqualified owned bag projection', state.log())
                self.assertNotIn('Diagnostic supply contains an unqualified saved slot', state.log())

    def test_legacy_town_restore_preserves_full_instance_and_connection(self):
        self.legacy_restore('town')

    def test_legacy_resource_restore_preserves_full_instance_and_connection(self):
        self.legacy_restore('resource')


if __name__ == '__main__':
    unittest.main()
