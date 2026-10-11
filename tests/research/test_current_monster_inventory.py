"""Full source coverage and no guessed monster classification or values."""
import hashlib
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.strike_lab import current_monster_inventory as inventory


class CurrentMonsterInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = inventory.pinned_catalog()
        cls.report = inventory.build_inventory()
        raw = (ROOT.parent / 'God2' / inventory.SOURCE).read_bytes()
        cls.plain = inventory.decode_csvz(raw, limit=4 * 1024 * 1024)
        cls.lines = cls.plain.splitlines(keepends=True)

    def test_all_source_occurrences_preserved(self):
        rows = self.report['records']
        self.assertEqual(len(rows), 7815)
        self.assertEqual([r['source_record_index'] for r in rows], list(range(7815)))
        self.assertEqual(len({r['source_line'] for r in rows}), 7815)
        self.assertEqual(len({r['source_offset'] for r in rows}), 7815)
        for row in rows:
            raw = bytes.fromhex(row['raw_record_hex'])
            at = row['source_offset']
            self.assertEqual(self.plain[at:at + len(raw)], raw)
            self.assertEqual(hashlib.sha256(raw).hexdigest(), row['record_sha256'])
            self.assertEqual(self.lines[row['source_line'] - 1], raw)

    def test_visible_identity_keys_and_native_allocation_offsets(self):
        visible = [r for r in self.report['records'] if r['lookup_visible']]
        self.assertEqual(len(visible), 7791)
        keys = {(r['area'], r['scene'], r['ordinal']) for r in visible}
        self.assertEqual(len(keys), len(visible))
        self.assertEqual(len(self.catalog['groups']), 96)
        for row in visible:
            group = (row['area'], row['scene'])
            self.assertEqual(row['source_record_index'],
                             self.catalog['group_offsets'][group] + row['ordinal'] - 1)
            fields = self.catalog['groups'][group][row['ordinal'] - 1]
            self.assertEqual(row['fields_hex'], [f.encode('latin1').hex() for f in fields])

    def test_overwritten_area_records_retained_but_not_runtime_visible(self):
        removed = [r for r in self.report['records'] if not r['lookup_visible']]
        self.assertEqual(len(removed), 24)
        self.assertEqual({r['area'] for r in removed}, {7})
        self.assertEqual(len(self.catalog['loaded_groups']), 97)
        self.assertEqual(sum(len(g[3]) for g in self.catalog['loaded_groups']), 7815)

    def test_names_never_merge_variants(self):
        rows = [r for r in self.report['records'] if r['lookup_visible']]
        self.assertLess(len({r['name_bytes_hex'] for r in rows}), len(rows))
        self.assertEqual(len({(r['area'], r['scene'], r['ordinal']) for r in rows}), len(rows))

    def test_every_requested_field_remains_unknown_not_zero(self):
        self.assertEqual(len(inventory.FIELDS), 21)
        for row in self.report['records']:
            self.assertEqual(set(row['native_values']), set(inventory.FIELDS))
            self.assertTrue(all(value is None for value in row['native_values'].values()))
            self.assertIsNone(row['monster_classification'])
        for value in self.report['field_coverage'].values():
            self.assertEqual(value, {'verified_lookup_records': 0, 'unresolved_lookup_records': 7791,
                                     'verified_percent_of_lookup_records': 0.0})
        self.assertFalse(self.report['runtime_eligible'])

    def test_unknown_skills_and_loot_are_not_empty_lists_or_zero_rates(self):
        for name in ('skill_assignments', 'drop_items', 'drop_rates'):
            self.assertIn(name, self.report['field_coverage'])
            self.assertTrue(all(r['native_values'][name] is None for r in self.report['records']))
        self.assertIn('denominator', self.report['drop_rate_policy'])
        self.assertIn('repertoire', self.report['assignment_policy'])

    def test_boss_scope_does_not_claim_exhaustive_species_denominator(self):
        self.assertIn('boss', self.report['requested_scope'])
        self.assertIsNone(self.report['summary']['unique_wild_monsters'])
        self.assertFalse(self.report['summary']['all_monster_systems_enumerated'])

    def test_identity_hash_mismatch_fails_closed(self):
        with patch.object(inventory, 'SOURCE_SHA', '0' * 64):
            with self.assertRaises(ValueError):
                inventory.pinned_catalog()
        with patch.object(inventory, 'PLAIN_SHA', '0' * 64):
            with self.assertRaises(ValueError):
                inventory.pinned_catalog()

    def test_bad_envelopes_rejected_before_native_execution(self):
        for data in (self.plain.replace(b'EnyName,7931', b'EnyName,1', 1),
                     self.plain.replace(b'EnyNameTotal,7815', b'EnyNameTotal,7814', 1),
                     self.plain.replace(b'EnyNameIsland_Area,1,2', b'EnyNameIsland_Area,17,2', 1),
                     self.plain.replace(b'EnyNameAreaId_Idx,0,21', b'EnyNameAreaId_Idx,0,7816', 1),
                     self.plain[:self.plain.index(b'SpecialEnyInfo,')]):
            self.assertNotEqual(data, self.plain)
            with self.assertRaises(ValueError):
                inventory.parse_enemy_catalog(data)


if __name__ == '__main__':
    unittest.main()
