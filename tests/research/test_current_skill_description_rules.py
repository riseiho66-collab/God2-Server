"""Keep original text claims distinct from recovered runtime formulas."""
from pathlib import Path
import hashlib
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.strike_lab.current_skill_description_rules import build_ledger


class DescriptionRuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ledger = build_ledger()
        cls.rows = {(r['item_id'], r['source_column']): r for r in cls.ledger['entries']}

    def claims(self, item, column=10):
        return self.rows[item, column]['claims']

    def test_complete_scan_and_provenance(self):
        self.assertEqual(self.ledger['book_records_scanned'], 381)
        self.assertEqual(len(self.rows), 61)
        self.assertEqual(len(self.rows), len(self.ledger['entries']))
        for row in self.rows.values():
            raw = bytes.fromhex(row['raw_record_hex'])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), row['source_record_sha256'])
            fields = raw.decode('cp950').split(',')
            self.assertEqual(fields[row['source_column']], row['source_text'])
            self.assertEqual(fields[7:13], row['description_context'])

    def test_conditional_damage_factors_not_generalized(self):
        for item in (6568, 6569, 6570, 6572, 6573, 6574, 6665, 6666, 6667, 6668, 6669):
            effect = self.claims(item)[0]
            self.assertEqual(effect['factor'], 2)
            self.assertIn('critical', effect['condition'])
            self.assertIsNone(effect['probability'])
        self.assertIsNone(self.claims(6575)[0]['factor'])
        for item in range(6890, 6894):
            self.assertEqual(self.claims(item, 11)[0]['effect'], 'double_damage_special_ability_excluded')
            self.assertIsNone(self.claims(item, 11)[0]['factor'])

    def test_guarantees_preserve_prerequisites(self):
        counter = self.claims(6571)[1]
        self.assertEqual(counter['probability'], 1)
        self.assertIn('axe 5; attacked and hit; counterattack', counter['condition'])
        status = self.claims(6884)[0]
        self.assertEqual(status['probability'], 1)
        self.assertIn('proc AND target not immune', status['condition'])

    def test_ambiguity_and_duration(self):
        for effect in (self.claims(6873)[0], self.claims(6573)[1]):
            self.assertIsNone(effect['factor'])
            self.assertTrue(effect['ambiguity'])
        for item in (6604, 6612, 6620, 6628, 6636):
            self.assertEqual(self.claims(item, 12)[0]['rounds'], 5)
        self.assertEqual(self.claims(6871)[0]['factor'], 5)
        self.assertIn('ordinary scene', self.claims(6871)[0]['condition'])

    def test_never_promote_descriptions(self):
        self.assertFalse(self.ledger['runtime_verified'])
        self.assertFalse(self.ledger['production_enabled'])
        for row in self.rows.values():
            self.assertEqual(row['authority'], 'description_only')
            self.assertIsNone(row['runtime_skill_identity'])
            self.assertFalse(row['executable'])


if __name__ == '__main__':
    unittest.main()
