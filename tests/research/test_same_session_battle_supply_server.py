"""Isolated own-server TCP check of battle -> item -> second battle in one session.

Uses original-client captured C2S35 shapes, but is a socket peer, not current-
client visual or native-call acceptance. Every save is a temporary test DB.
"""

from contextlib import closing
from pathlib import Path
import sqlite3
import sys
import unittest

import test_recovered_movement_server as movement
from test_current_movement import movement_wire
from tools.strike_lab import import_native_med02_recovery


SOURCE_SHA = '70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731'
CONTROL_FIRST = bytes.fromhex('000b0000000000000000000000000000')
CONTROL_SECOND = bytes.fromhex('000b0000010000000000000000000000')
SKILL = bytes.fromhex('00030037000001000000000001000000')
RECEIPT_ENEMY = bytes.fromhex('000b0000000001000000000000000000')
RECEIPT_FRIENDLY = bytes.fromhex('000b0000010000000000000000000000')


class SameSessionBattleSupplyServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        movement.RecoveredMovementServerTests.setUpClass()

    @staticmethod
    def logical(h, game):
        header = h.receive(game, 2)
        size = int.from_bytes(header, 'little')
        if not 4 <= size <= 0xa03:
            raise AssertionError(f'invalid frame size {size}')
        plain = bytearray(header)
        previous = 0
        for index, value in enumerate(h.receive(game, size - 2)):
            previous = ((value + 3 - previous) & 255) ^ h.crypto_key[index & 255]
            plain.append(previous)
        if plain[-1] != sum(value + 0x3c for value in plain[:-1]) & 255:
            raise AssertionError('invalid frame checksum')
        return bytes(plain[2:-1])

    def test_saved_hp_potion_client_record_reaches_authoritative_world_route(self):
        m = movement.RecoveredMovementServerTests()
        w, h = m.harness()
        original = h.configuration

        def configuration(*args, **kwargs):
            config = original(*args, **kwargs)
            config['database']['path'] = str(args[0] / 'diagnostic-accounts.db')
            config['development']['diagnostic_world_resources'] = True
            config['development']['diagnostic_world_supply'] = True
            return config

        h.configuration = configuration
        with h.server() as server:
            endpoint, identity = w.create(h, server)
            with closing(sqlite3.connect(server.database)) as db:
                db.execute('INSERT INTO character_resources VALUES(?,?,?,?,?,?,?)',
                           (identity, 20, 120, 2, 80, 1, 'CUSTOM-0012'))
                db.execute('INSERT INTO diagnostic_inventory_slots VALUES(?,?,?,?,?,?,?)',
                           (identity, 0, 3101, 3, 1, SOURCE_SHA, 'CUSTOM-0015'))
                db.commit()
            with h.connect(endpoint) as game:
                m.ready(w, h, game, identity, (17, 13))
                game.sendall(h.frame(0x30, b'\0'))
                self.assertEqual(self.logical(h, game)[0], 0x24)
                self.assertEqual(self.logical(h, game)[0], 0x41)
                request = h.frame(0x26, identity.to_bytes(2, 'little') +
                                  (3101).to_bytes(2, 'little') + b'\0\xa5')
                game.sendall(request)
                supplied = self.logical(h, game)
                self.assertEqual((len(supplied), supplied[:6]),
                                 (22, bytes.fromhex('411d0c000224')))
                self.assertEqual((int.from_bytes(supplied[6:10], 'little'),
                                  int.from_bytes(supplied[10:14], 'little')), (120, 2))
                with closing(sqlite3.connect(server.database)) as db:
                    self.assertEqual(db.execute('SELECT hp,max_hp,mp,max_mp,revision '
                                                'FROM character_resources').fetchone(),
                                     (120, 120, 2, 80, 2))
                    self.assertEqual(db.execute('SELECT item_id,count,revision '
                                                'FROM diagnostic_inventory_slots').fetchone(),
                                     (3101, 2, 2))
                # At full HP the same valid item request has no effect or reply.
                game.sendall(request)
                h.silent(game)
                game.sendall(movement_wire(18, 12, 1))
                m.ack(h, game, 1)
                with closing(sqlite3.connect(server.database)) as db:
                    self.assertEqual(db.execute('SELECT hp,mp FROM character_resources').fetchone(),
                                     (120, 2))
                    self.assertEqual(db.execute('SELECT item_id,count FROM diagnostic_inventory_slots').fetchone(),
                                     (3101, 2))
                    self.assertEqual(db.execute('PRAGMA quick_check').fetchone(), ('ok',))

    def test_imported_med02_combined_potion_reaches_c2s26_and_saved_state(self):
        m = movement.RecoveredMovementServerTests()
        w, h = m.harness()
        original = h.configuration

        def configuration(*args, **kwargs):
            config = original(*args, **kwargs)
            config['database']['path'] = str(args[0] / 'diagnostic-accounts.db')
            config['development']['diagnostic_world_resources'] = True
            config['development']['diagnostic_world_supply'] = True
            return config

        h.configuration = configuration
        with h.server() as server:
            with closing(sqlite3.connect(server.database)) as db:
                imported = import_native_med02_recovery.import_catalog(
                    db, import_native_med02_recovery.ROOT.parent / 'God2')
                self.assertEqual(imported['inserted'], 71)
            endpoint, identity = w.create(h, server)
            with closing(sqlite3.connect(server.database)) as db:
                db.execute('INSERT INTO character_resources VALUES(?,?,?,?,?,?,?)',
                           (identity, 20, 120, 2, 80, 1, 'CUSTOM-0012'))
                db.execute('INSERT INTO diagnostic_inventory_slots VALUES(?,?,?,?,?,?,?)',
                           (identity, 0, 3113, 3, 1, SOURCE_SHA, 'CUSTOM-0015'))
                db.commit()
            with h.connect(endpoint) as game:
                m.ready(w, h, game, identity, (17, 13))
                game.sendall(h.frame(0x30, b'\0'))
                self.assertEqual(self.logical(h, game)[0], 0x24)
                self.assertEqual(self.logical(h, game)[0], 0x41)
                game.sendall(h.frame(0x26, identity.to_bytes(2, 'little') +
                                     (3113).to_bytes(2, 'little') + b'\0\xa5'))
                supplied = self.logical(h, game)
                self.assertEqual((len(supplied), supplied[:6]),
                                 (22, bytes.fromhex('41290c000224')))
                self.assertEqual((int.from_bytes(supplied[6:10], 'little'),
                                  int.from_bytes(supplied[10:14], 'little')), (120, 80))
                game.sendall(movement_wire(18, 12, 1))
                m.ack(h, game, 1)
            with closing(sqlite3.connect(server.database)) as db:
                self.assertEqual(db.execute('SELECT hp,max_hp,mp,max_mp,revision '
                                            'FROM character_resources').fetchone(),
                                 (120, 120, 80, 80, 2))
                self.assertEqual(db.execute('SELECT item_id,count,revision '
                                            'FROM diagnostic_inventory_slots').fetchone(),
                                 (3113, 2, 2))
                self.assertEqual(db.execute('PRAGMA quick_check').fetchone(), ('ok',))

    def test_distinct_saved_supply_slots_project_and_debit_independently(self):
        m = movement.RecoveredMovementServerTests()
        w, h = m.harness()
        original = h.configuration

        def configuration(*args, **kwargs):
            config = original(*args, **kwargs)
            config['database']['path'] = str(args[0] / 'diagnostic-accounts.db')
            config['development']['diagnostic_world_resources'] = True
            config['development']['diagnostic_world_supply'] = True
            return config

        h.configuration = configuration
        with h.server() as server:
            with closing(sqlite3.connect(server.database)) as db:
                import_native_med02_recovery.import_catalog(
                    db, import_native_med02_recovery.ROOT.parent / 'God2')
            endpoint, identity = w.create(h, server)
            with closing(sqlite3.connect(server.database)) as db:
                db.execute('INSERT INTO character_resources VALUES(?,?,?,?,?,?,?)',
                           (identity, 20, 120, 2, 80, 1, 'CUSTOM-0012'))
                db.executemany('INSERT INTO diagnostic_inventory_slots VALUES(?,?,?,?,?,?,?)',
                               [(identity, 5, 3101, 2, 1, SOURCE_SHA, 'CUSTOM-0015'),
                                (identity, 12, 3107, 3, 1, SOURCE_SHA, 'CUSTOM-0015'),
                                (identity, 30, 3101, 1, 1, SOURCE_SHA, 'CUSTOM-0015')])
                db.commit()
            with h.connect(endpoint) as game:
                m.ready(w, h, game, identity, (17, 13))
                game.sendall(h.frame(0x30, b'\0'))
                self.assertEqual(self.logical(h, game)[0], 0x24)
                self.assertEqual(self.logical(h, game),
                                 bytes.fromhex('411d0c050241230c0c03'))
                for item, slot, hp, mp in ((3101, 5, 120, 2), (3107, 12, 120, 52)):
                    game.sendall(h.frame(0x26, identity.to_bytes(2, 'little') +
                                         item.to_bytes(2, 'little') + bytes((slot, 0xa5))))
                    reply = self.logical(h, game)
                    self.assertEqual((len(reply), reply[0], reply[3], reply[5]),
                                     (22, 0x41, slot, 0x24))
                    self.assertEqual((int.from_bytes(reply[6:10], 'little'),
                                      int.from_bytes(reply[10:14], 'little')), (hp, mp))
                game.sendall(movement_wire(18, 12, 1))
                m.ack(h, game, 1)
            with closing(sqlite3.connect(server.database)) as db:
                self.assertEqual(db.execute('SELECT hp,mp,revision FROM character_resources').fetchone(),
                                 (120, 52, 3))
                self.assertEqual(db.execute('SELECT slot,item_id,count,revision FROM '
                                            'diagnostic_inventory_slots ORDER BY slot').fetchall(),
                                 [(5, 3101, 1, 2), (12, 3107, 2, 2), (30, 3101, 1, 1)])
                self.assertEqual(db.execute('PRAGMA quick_check').fetchone(), ('ok',))

    def test_battle_supply_then_second_battle_uses_saved_resources(self):
        m = movement.RecoveredMovementServerTests()
        w, h = m.harness()
        original = h.configuration

        def configuration(*args, **kwargs):
            config = original(*args, **kwargs)
            config['database']['path'] = str(args[0] / 'diagnostic-accounts.db')
            for flag in ('diagnostic_battle_transition', 'diagnostic_battle_participants',
                         'diagnostic_battle_player_appearance', 'diagnostic_battle_animations',
                         'diagnostic_battle_skill_seed', 'diagnostic_battle_skill_settlement',
                         'diagnostic_battle_terminal', 'diagnostic_battle_resources',
                         'diagnostic_battle_after_movement', 'diagnostic_world_resources',
                         'diagnostic_world_supply'):
                config['development'][flag] = True
            config['development']['diagnostic_battle_rounds'] = 3
            config['development']['diagnostic_encounter_limit'] = 2
            return config

        h.configuration = configuration
        with h.server() as server:
            endpoint, identity = w.create(h, server)
            with closing(sqlite3.connect(server.database)) as db:
                db.execute('INSERT INTO character_resources VALUES(?,?,?,?,?,?,?)',
                           (identity, 52, 120, 80, 80, 1, 'CUSTOM-0012'))
                db.execute('INSERT INTO diagnostic_inventory_slots VALUES(?,?,?,?,?,?,?)',
                           (identity, 0, 3107, 1, 1, SOURCE_SHA, 'CUSTOM-0015'))
                db.commit()
            with h.connect(endpoint) as game:
                m.ready(w, h, game, identity, (17, 13))
                game.sendall(h.frame(0x30, b'\0'))
                self.assertEqual(self.logical(h, game)[0], 0x24)
                self.assertEqual(self.logical(h, game)[0], 0x41)
                game.sendall(movement_wire(18, 12, 1))
                m.ack(h, game, 1)
                game.sendall(h.frame(0x30, b'\0'))
                entry = self.logical(h, game)
                self.assertEqual((entry[:2], entry[23]), (b'\x30\xff', 0x82))
                game.sendall(h.frame(0x36, bytes(8)))
                participants = self.logical(h, game)
                self.assertEqual(participants[:3], bytes.fromhex('870180'))
                first_bulk = participants.index(0x88, 5)
                self.assertEqual((int.from_bytes(participants[first_bulk+5:first_bulk+9], 'little'),
                                  int.from_bytes(participants[first_bulk+9:first_bulk+13], 'little')), (52, 80))
                game.sendall(h.frame(0x35, CONTROL_FIRST))
                h.silent(game)
                for round_index in range(3):
                    game.sendall(h.frame(0x35, SKILL))
                    effect = self.logical(h, game)
                    self.assertEqual((effect[0], effect[17]), (0x86, 0x83))
                    if round_index < 2:
                        self.assertEqual(self.logical(h, game)[0], 0x83)
                    receipt = RECEIPT_ENEMY if round_index == 0 else RECEIPT_FRIENDLY
                    game.sendall(h.frame(0x35, receipt))
                    received = self.logical(h, game)
                    if round_index < 2:
                        self.assertEqual(received[0], 0x88)
                    else:
                        self.assertEqual(received[0], 0x89)
                game.sendall(h.frame(0x1c, b'\x01\0\0\0'))
                h.silent(game)
                game.sendall(h.frame(0x26, identity.to_bytes(2, 'little') +
                                     (3107).to_bytes(2, 'little') + b'\0\xa5'))
                supplied = self.logical(h, game)
                self.assertEqual((len(supplied), supplied[:6]),
                                 (22, bytes.fromhex('410000000024')))
                self.assertEqual((int.from_bytes(supplied[6:10], 'little'),
                                  int.from_bytes(supplied[10:14], 'little')), (28, 80))
                with closing(sqlite3.connect(server.database)) as db:
                    hp, mp = db.execute('SELECT hp,mp FROM character_resources').fetchone()
                    self.assertEqual((hp, mp), (28, 80))
                    self.assertEqual(db.execute('SELECT item_id,count FROM diagnostic_inventory_slots').fetchone(),
                                     (0, 0))
                    self.assertEqual(db.execute('SELECT count(*) FROM battle_settlements').fetchone(), (1,))
                game.sendall(movement_wire(17, 13, 1))
                m.ack(h, game, 1)
                game.sendall(h.frame(0x30, b'\0'))
                self.assertEqual(self.logical(h, game)[0], 0x82)
                game.sendall(h.frame(0x36, bytes(8)))
                second = self.logical(h, game)
                self.assertEqual(second[:3], bytes.fromhex('870180'))
                second_bulk = second.index(0x88, 5)
                self.assertEqual((int.from_bytes(second[second_bulk+5:second_bulk+9], 'little'),
                                  int.from_bytes(second[second_bulk+9:second_bulk+13], 'little')), (28, 80))
                game.sendall(h.frame(0x35, CONTROL_SECOND))
                h.silent(game)
                for round_index in range(3):
                    game.sendall(h.frame(0x35, SKILL))
                    effect = self.logical(h, game)
                    self.assertEqual((effect[0], effect[17]), (0x86, 0x83))
                    if round_index < 2:
                        self.assertEqual(self.logical(h, game)[0], 0x83)
                    game.sendall(h.frame(0x35, RECEIPT_ENEMY if round_index == 0
                                         else RECEIPT_FRIENDLY))
                    self.assertEqual(self.logical(h, game)[0], 0x88 if round_index < 2 else 0x89)
                game.sendall(h.frame(0x1c, b'\x01\0\0\0'))
                h.silent(game)
                game.sendall(movement_wire(18, 12, 1))
                m.ack(h, game, 1)
                game.sendall(h.frame(0x30, b'\0'))
                h.silent(game)
                with closing(sqlite3.connect(server.database)) as db:
                    self.assertEqual(db.execute('SELECT count(*) FROM battle_reservations').fetchone(), (2,))
                    self.assertEqual(db.execute('SELECT count(*) FROM battle_settlements').fetchone(), (2,))
                    self.assertEqual(db.execute('SELECT hp,mp FROM character_resources').fetchone(), (4, 56))
                    self.assertEqual(db.execute('SELECT item_id,count FROM diagnostic_inventory_slots').fetchone(), (0, 0))
                    self.assertEqual(db.execute('SELECT total FROM character_experience').fetchone(), (0,))
                    self.assertEqual(db.execute('PRAGMA quick_check').fetchone(), ('ok',))


if __name__ == '__main__':
    if len(sys.argv) > 1:
        import test_recovered_dual_connection_server as dual
        dual.BINARY = Path(sys.argv.pop(1)).resolve()
    unittest.main()
