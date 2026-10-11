"""Saved real-client occupancy evidence; not visible UI or item-use acceptance."""
import json
from pathlib import Path
import sqlite3
import unittest

ROOT = Path(__file__).resolve().parents[2] / 'artifacts/runs'


class SupplyProjectionEvidenceTests(unittest.TestCase):
    def test_native_healing_preserves_mp_and_stops_at_cap(self):
        run = ROOT / 'native-healing-use-20260921-01'
        report = json.loads((run / 'run.json').read_text())
        self.assertEqual(report['result'], 'NATIVE_HEALING_USE_SEQUENCE_OBSERVED')
        self.assertEqual(len(report['supply_calls']), 3)
        self.assertTrue(all(call['returned'] for call in report['supply_calls']))
        for sample, expected in zip(report['supply_results'], ((2,104),(1,120),(1,120)), strict=True):
            slot = bytes.fromhex(sample['slot_hex'])
            values = bytes.fromhex(sample['resource_hex'])
            self.assertEqual((slot[0],int.from_bytes(values[:4],'little')), expected)
            self.assertEqual(int.from_bytes(slot[4:6],'little'), 3101)
            self.assertEqual(int.from_bytes(values[8:12],'little'), 56)
        for index in (492,509,526):
            packet = json.loads((run / f'packet-decode-{index:04d}.json').read_text())
            self.assertTrue(packet['checksum_valid'])
            self.assertEqual(bytes.fromhex(packet['plain_frame_hex'])[2:8], bytes.fromhex('2601001d0c00'))
        db = sqlite3.connect((run / 'diagnostic-accounts.db').resolve().as_uri() + '?mode=ro', uri=True)
        try:
            self.assertEqual(db.execute('SELECT hp,mp,revision FROM character_resources').fetchall(), [(120,56,23)])
            self.assertEqual(db.execute('SELECT item_id,count,revision FROM diagnostic_inventory_slots').fetchall(), [(3101,1,7)])
        finally:
            db.close()

    def test_saved_supply_resources_feed_next_fresh_connection_battle(self):
        run = ROOT / 'native-after-supply-battle-20260921-01'
        report = json.loads((run / 'run.json').read_text())
        self.assertEqual(report['result'], 'NATIVE_SOCKET_BATTLE_RETURNED_TO_WORLD_LOOP')
        self.assertEqual(report['world_resource_before_battle']['hp_maxhp_mp_maxmp_hex'],
                         '1c000000780000005000000050000000')
        self.assertEqual(report['world_resource_after_battle']['hp_maxhp_mp_maxmp_hex'],
                         '04000000780000003800000050000000')
        self.assertTrue(report['world_resource_after_battle']['same_source'])
        self.assertEqual(len(report['socket_skill_commands']), 3)
        self.assertEqual(len(report['animation_batch_completions']), 5)
        db = sqlite3.connect((run / 'diagnostic-accounts.db').resolve().as_uri() + '?mode=ro', uri=True)
        try:
            self.assertEqual(db.execute('SELECT hp,mp,revision FROM character_resources').fetchall(), [(4,56,20)])
            self.assertEqual(db.execute('SELECT item_id,count,revision FROM diagnostic_inventory_slots').fetchall(), [(0,0,4)])
            self.assertEqual(db.execute('SELECT count(*) FROM battle_settlements').fetchone()[0], 4)
        finally:
            db.close()

    def test_live_battle_then_supply(self):
        run = ROOT / 'native-post-battle-supply-20260921-01'
        report = json.loads((run / 'run.json').read_text())
        self.assertEqual(report['result'], 'NATIVE_POST_BATTLE_SUPPLY_OBSERVED')
        self.assertEqual(len(report['socket_skill_commands']), 3)
        self.assertEqual(len(report['animation_batch_completions']), 5)
        after = report['world_resource_after_battle']
        self.assertTrue(after['same_source'])
        self.assertEqual(after['hp_maxhp_mp_maxmp_hex'], '1c000000780000003800000050000000')
        self.assertEqual(len(report['supply_results']), 2)
        for sample in report['supply_results']:
            self.assertGreater(sample['sequence'], after['sequence'])
            self.assertEqual(bytes.fromhex(sample['slot_hex']), bytes(24))
            self.assertEqual(sample['resource_hex'], '1c000000780000005000000050000000')
        packet = json.loads((run / 'packet-decode-0735.json').read_text())
        self.assertTrue(packet['checksum_valid'])
        self.assertEqual(bytes.fromhex(packet['plain_frame_hex'])[2:8], bytes.fromhex('260100230c00'))
        db = sqlite3.connect((run / 'diagnostic-accounts.db').resolve().as_uri() + '?mode=ro', uri=True)
        try:
            self.assertEqual(db.execute('SELECT hp,mp,revision FROM character_resources').fetchall(), [(28,80,17)])
            self.assertEqual(db.execute('SELECT item_id,count,revision FROM diagnostic_inventory_slots').fetchall(), [(0,0,4)])
            self.assertEqual(db.execute('SELECT count(*) FROM battle_settlements').fetchone()[0], 3)
        finally:
            db.close()

    def test_empty_tombstone_relogin_does_not_regrant(self):
        source = ROOT / 'native-supply-exhaustion-20260921-01'
        run = ROOT / 'native-supply-empty-relogin-20260921-01'
        report = json.loads((run / 'run.json').read_text())
        self.assertEqual(report['result'], 'NATIVE_SAVED_POSITION_RESTORED')
        self.assertEqual(bytes.fromhex(report['supply_slot_projection']['bytes_hex']), bytes(24))
        self.assertEqual(report['world_resource_update_return']['values_hex'],
                         '34000000780000003400000050000000')
        self.assertNotIn('supply_calls', report)
        a, b = [sqlite3.connect((p / 'diagnostic-accounts.db').resolve().as_uri() + '?mode=ro', uri=True)
                for p in (source,run)]
        try:
            for (table,) in a.execute('SELECT name FROM sqlite_master WHERE type=?', ('table',)):
                identifier = '"' + table.replace('"', '""') + '"'
                self.assertEqual(a.execute('SELECT * FROM ' + identifier).fetchall(),
                                 b.execute('SELECT * FROM ' + identifier).fetchall(), table)
        finally:
            a.close()
            b.close()

    def test_last_unit_clears_slot_and_empty_slot_does_not_send(self):
        run = ROOT / 'native-supply-exhaustion-20260921-01'
        report = json.loads((run / 'run.json').read_text())
        self.assertEqual(report['result'], 'NATIVE_SUPPLY_EXHAUSTION_OBSERVED')
        self.assertEqual(len(report['supply_calls']), 2)
        self.assertTrue(all(call['returned'] for call in report['supply_calls']))
        self.assertEqual(len(report['supply_results']), 2)
        for sample in report['supply_results']:
            self.assertEqual(bytes.fromhex(sample['slot_hex']), bytes(24))
            self.assertEqual(sample['resource_hex'], '34000000780000003400000050000000')
        packets = [json.loads(path.read_text()) for path in run.glob('packet-decode-*.json')]
        uses = [packet for packet in packets if packet.get('opcode') == 0x26]
        self.assertEqual(len(uses), 1)
        self.assertTrue(uses[0]['checksum_valid'])
        self.assertEqual(bytes.fromhex(uses[0]['plain_frame_hex'])[2:8], bytes.fromhex('260100230c00'))
        db = sqlite3.connect((run / 'diagnostic-accounts.db').resolve().as_uri() + '?mode=ro', uri=True)
        try:
            self.assertEqual(db.execute('SELECT item_id,count,revision FROM diagnostic_inventory_slots').fetchall(), [(0,0,2)])
            self.assertEqual(db.execute('SELECT hp,mp,revision FROM character_resources').fetchall(), [(52,52,12)])
        finally:
            db.close()

    def test_fresh_relogin_preserves_used_inventory_and_resources(self):
        source = ROOT / 'native-supply-use-20260921-01'
        run = ROOT / 'native-supply-relogin-20260921-01'
        report = json.loads((run / 'run.json').read_text())
        self.assertEqual(report['result'], 'NATIVE_SAVED_POSITION_RESTORED')
        self.assertEqual(report['world_resource_update_return']['values_hex'],
                         '34000000780000005000000050000000')
        slot = bytes.fromhex(report['supply_slot_projection']['bytes_hex'])
        self.assertEqual((slot[0], int.from_bytes(slot[4:6], 'little')), (1,3107))
        self.assertNotIn('supply_calls', report)
        a, b = [sqlite3.connect((p / 'diagnostic-accounts.db').resolve().as_uri() + '?mode=ro', uri=True)
                for p in (source,run)]
        try:
            tables = [r[0] for r in a.execute('SELECT name FROM sqlite_master WHERE type=?', ('table',))]
            for table in tables:
                identifier = '"' + table.replace('"', '""') + '"'
                self.assertEqual(a.execute('SELECT * FROM ' + identifier).fetchall(),
                                 b.execute('SELECT * FROM ' + identifier).fetchall(), table)
        finally:
            a.close()
            b.close()

    def test_native_use_sequence_and_saved_transaction(self):
        run = ROOT / 'native-supply-use-20260921-01'
        report = json.loads((run / 'run.json').read_text())
        self.assertEqual(report['result'], 'NATIVE_SUPPLY_USE_SEQUENCE_OBSERVED')
        self.assertEqual(len(report['supply_calls']), 3)
        self.assertTrue(all(c['returned'] for c in report['supply_calls']))
        for sample, expected in zip(report['supply_results'], ((2, 52), (1, 80), (1, 80)), strict=True):
            slot = bytes.fromhex(sample['slot_hex'])
            resources = bytes.fromhex(sample['resource_hex'])
            self.assertEqual((slot[0], int.from_bytes(resources[8:12], 'little')), expected)
            self.assertEqual(int.from_bytes(slot[4:6], 'little'), 3107)
            self.assertEqual(int.from_bytes(resources[:4], 'little'), 52)
        tails = []
        for index in (490, 507, 524):
            packet = json.loads((run / f'packet-decode-{index:04d}.json').read_text())
            self.assertTrue(packet['checksum_valid'])
            raw = bytes.fromhex(packet['plain_frame_hex'])
            self.assertEqual(raw[2:8], bytes.fromhex('260100230c00'))
            tails.append(raw[8])
        self.assertEqual(len(set(tails)), 3)  # Native residual byte is not count.
        db = sqlite3.connect((run / 'diagnostic-accounts.db').resolve().as_uri() + '?mode=ro', uri=True)
        try:
            self.assertEqual(db.execute('SELECT hp,mp,revision FROM character_resources').fetchall(), [(52,80,13)])
            self.assertEqual(db.execute('SELECT item_id,count,revision FROM diagnostic_inventory_slots').fetchall(), [(3107,1,3)])
        finally:
            db.close()

    def test_native_slot_and_resources(self):
        run = ROOT / 'native-supply-projection-20260921-02'
        report = json.loads((run / 'run.json').read_text())
        self.assertEqual(report['result'], 'NATIVE_SAVED_POSITION_RESTORED')
        raw = bytes.fromhex(report['supply_slot_projection']['bytes_hex'])
        self.assertEqual(raw[0], 3)
        self.assertEqual(int.from_bytes(raw[4:6], 'little'), 3107)
        self.assertEqual(report['world_resource_update_return']['values_hex'],
                         '34000000780000000200000050000000')
        config = json.loads((run / 'diagnostic-server-config.json').read_text())
        self.assertTrue(config['development']['diagnostic_world_supply'])

    def test_all_saved_tables_unchanged(self):
        paths = [ROOT / name / 'diagnostic-accounts.db' for name in
                 ('native-supply-fixture-20260921-01', 'native-supply-projection-20260921-02')]
        a, b = [sqlite3.connect(p.resolve().as_uri() + '?mode=ro', uri=True) for p in paths]
        try:
            tables = [r[0] for r in a.execute('SELECT name FROM sqlite_master WHERE type=?', ('table',))]
            self.assertIn('diagnostic_inventory_slots', tables)
            for table in tables:
                identifier = '"' + table.replace('"', '""') + '"'
                self.assertEqual(a.execute('SELECT * FROM ' + identifier).fetchall(),
                                 b.execute('SELECT * FROM ' + identifier).fetchall(), table)
        finally:
            a.close()
            b.close()


if __name__ == '__main__':
    unittest.main()
