"""Saved own-server native defeat evidence; not UI or native rule acceptance."""
import json
from pathlib import Path
import sqlite3
import unittest

ROOT = Path(__file__).resolve().parents[2] / 'artifacts/runs'
RUN = ROOT / 'native-defeat-20260921-01'


class DefeatEvidenceTests(unittest.TestCase):
    def test_revival_expansion_word_does_not_track_hp_death(self):
        report = json.loads((ROOT / 'native-defeat-20260921-02/run.json').read_text())
        self.assertEqual(report['result'], 'NATIVE_SOCKET_DEFEAT_RETURNED_TO_WORLD_LOOP')
        before, enemy, after = report['socket_defeat_vitals']
        self.assertEqual(before['entity_pointer'], after['entity_pointer'])
        self.assertEqual(before['entity_word_1a_hex'], '7d00')
        self.assertEqual(after['entity_word_1a_hex'], '7d00')
        self.assertEqual(enemy['entity_word_1a_hex'], '8d00')
        self.assertEqual(int.from_bytes(bytes.fromhex(before['actor_vitals_hex'])[:4], 'little'), 4)
        self.assertEqual(int.from_bytes(bytes.fromhex(after['actor_vitals_hex'])[:4], 'little'), 0)
        self.assertEqual(len(report['animation_batch_completions']), 2)
        self.assertTrue(all(not x['timeout_fallback'] for x in report['animation_batch_completions']))

    def test_native_death_receipt_and_world_return(self):
        report = json.loads((RUN / 'run.json').read_text())
        self.assertEqual(report['result'], 'NATIVE_SOCKET_DEFEAT_RETURNED_TO_WORLD_LOOP')
        self.assertIsNone(report.get('error'))
        self.assertEqual(len(report['socket_skill_commands']), 1)
        self.assertEqual(len(report['animation_batch_completions']), 2)
        self.assertTrue(all(not x['timeout_fallback'] for x in report['animation_batch_completions']))
        records = report['socket_defeat_vitals']
        self.assertEqual([bytes.fromhex(x['logical_hex'])[:3] for x in records],
                         [bytes.fromhex(x) for x in ('860100', '86000e', '860000')])
        self.assertEqual(records[-1]['actor_vitals_hex'], '00000000300000007800000050000000')
        self.assertEqual(report['socket_outcome_entry']['logical_hex'], '89' + '00' * 56)
        after = report['world_resource_after_battle']
        self.assertTrue(after['same_source'])
        self.assertEqual(after['hp_maxhp_mp_maxmp_hex'], '00000000780000003000000050000000')
        packet = json.loads((RUN / 'packet-decode-0566.json').read_text())
        self.assertTrue(packet['checksum_valid'])
        self.assertTrue(packet['client_plaintext_match'])
        self.assertEqual(packet['plain_frame_hex'], '140035000b0000000001000000000000000000c9')

    def test_fresh_connection_preserves_death_and_all_saved_tables(self):
        run = ROOT / 'native-defeat-relogin-20260921-01'
        report = json.loads((run / 'run.json').read_text())
        self.assertEqual(report['result'], 'NATIVE_SAVED_POSITION_RESTORED')
        self.assertIsNone(report.get('error'))
        self.assertEqual(report['world_resource_update_return']['values_hex'],
                         '00000000780000003000000050000000')
        before = sqlite3.connect((RUN / 'diagnostic-accounts.db').resolve().as_uri() + '?mode=ro', uri=True)
        after = sqlite3.connect((run / 'diagnostic-accounts.db').resolve().as_uri() + '?mode=ro', uri=True)
        try:
            tables = before.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
            self.assertEqual(tables, after.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall())
            for (table,) in tables:
                quoted = '"' + table.replace('"', '""') + '"'
                self.assertEqual(before.execute(f'SELECT * FROM {quoted} ORDER BY rowid').fetchall(),
                                 after.execute(f'SELECT * FROM {quoted} ORDER BY rowid').fetchall(), table)
        finally:
            before.close()
            after.close()

    def test_defeat_is_persisted_without_award_or_inventory_mutation(self):
        db = sqlite3.connect((RUN / 'diagnostic-accounts.db').resolve().as_uri() + '?mode=ro', uri=True)
        source = sqlite3.connect((ROOT / 'native-after-supply-battle-20260921-01/diagnostic-accounts.db').resolve().as_uri() + '?mode=ro', uri=True)
        try:
            self.assertEqual(db.execute('SELECT hp,mp,revision FROM character_resources').fetchall(), [(0,48,21)])
            self.assertEqual(source.execute('SELECT hp,mp,revision FROM character_resources').fetchall(), [(4,56,20)])
            rows = db.execute('SELECT * FROM battle_settlements ORDER BY 1').fetchall()
            old = source.execute('SELECT * FROM battle_settlements ORDER BY 1').fetchall()
            self.assertEqual(rows[:-1], old)
            outcome = json.loads(rows[-1][1])
            self.assertFalse(outcome['won'])
            self.assertEqual(outcome['experience'], 0)
            self.assertEqual(outcome['after'][:4], [0,120,48,80])
            for table in ('character_experience', 'diagnostic_inventory_slots', 'recovered_positions'):
                self.assertEqual(db.execute(f'SELECT * FROM {table} ORDER BY 1').fetchall(),
                                 source.execute(f'SELECT * FROM {table} ORDER BY 1').fetchall())
        finally:
            db.close()
            source.close()


if __name__ == '__main__':
    unittest.main()
