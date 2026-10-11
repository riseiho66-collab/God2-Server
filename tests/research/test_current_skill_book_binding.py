"""Native book identity lookup must agree with original tags, not names."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.strike_lab.current_skill_book_binding import NativeSkillBookBinding
from tools.strike_lab.current_skill_description_rules import build_ledger


class SkillBookBindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.n = NativeSkillBookBinding()
        cls.catalog = cls.n.catalog()

    def expected(self, kind, skill_id):
        prefix = ('SpcA', 'SpcD', 'SpcC', 'SpcB')[kind] + f'{skill_id:02d}'
        width = 7 if skill_id >= 100 else 6
        base = (6500, 6600, 6700, 6800)[kind]
        return next((key for key in range(base + 1, base + 400)
                     if key in self.n.records and
                     self.n.records[key][1][0x11c:0x11c + width] == prefix.encode()), None)

    def test_all_populated_runtime_definitions(self):
        self.assertEqual(self.catalog['definition_count'], 448)
        matched = {(r['kind'], r['skill_id']): r for r in self.catalog['entries']}
        missing = {(r['kind'], r['skill_id']) for r in self.catalog['unmatched']}
        self.assertFalse(matched.keys() & missing)
        self.assertEqual(matched.keys() | missing, self.n.definitions.keys())
        for kind, skill_id in self.n.definitions:
            with self.subTest(kind=kind, skill_id=skill_id):
                expected = self.expected(kind, skill_id)
                self.assertEqual(matched.get((kind, skill_id), {}).get('item_id'), expected)

    def test_boundary_ids_and_absence_do_not_retain_previous_result(self):
        for kind in range(4):
            for skill_id in (0, 1, 99, 100, 127, 255):
                with self.subTest(kind=kind, skill_id=skill_id):
                    result = self.n.lookup(kind, skill_id)
                    self.assertEqual(result['item_id'] if result else None, self.expected(kind, skill_id))
                    for before, after in zip(self.n.branch_trace[::2], self.n.branch_trace[1::2]):
                        self.assertEqual(before[1], skill_id)
                        self.assertEqual(after[1], skill_id)
                        self.assertEqual(after[2] & 1, int(skill_id < 100))
                    self.assertTrue(all(c[1] == (7 if skill_id >= 100 else 6)
                                        for c in self.n.comparisons))
        with self.assertRaises(ValueError):
            self.n.lookup(4, 1)
        with self.assertRaises(ValueError):
            self.n.lookup(0, 256)

    def test_source_join_does_not_promote_formula(self):
        ledger = build_ledger()
        for entry in ledger['entries']:
            for binding in self.catalog['entries']:
                if binding['item_id'] != entry['item_id']:
                    continue
                self.assertEqual(binding['source_record_sha256'], entry['source_record_sha256'])
                self.assertEqual(binding['source_line'], entry['source_line'])
                self.assertTrue(binding['native_lookup_verified'])
                self.assertFalse(binding['damage_formula_verified'])
                self.assertFalse(entry['executable'])


if __name__ == '__main__':
    unittest.main()
