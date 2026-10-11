import copy
from pathlib import Path
import unittest

from tools.strike_lab.omega_assets import decode_csvz
from tools.strike_lab.recover_companions import GAME, digest, serialize
from tools.strike_lab.recover_pet_incubation import extract

CLIENT = Path(__file__).resolve().parents[3] / 'God2'


class PetIncubationEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = (CLIENT / GAME).read_bytes()
        cls.result = extract(cls.raw)
        cls.entries = {r['source_key']: r for r in cls.result['entries']}

    def test_all_records_exactly_match_original_offsets(self):
        decoded = decode_csvz(self.raw)
        self.assertEqual(len(self.entries), 55)
        for item in self.entries.values():
            source = item['source']
            raw = bytes.fromhex(source['raw_record_hex'])
            offset = source['decoded_offset']
            self.assertEqual(decoded[offset:offset + len(raw)], raw)
            self.assertEqual(digest(raw), source['sha256'])

    def test_tooltip_durations_are_not_timer_rules(self):
        timed = {k: c['hours'] for k, r in self.entries.items()
                 for c in r['claims'] if c['kind'] == 'care_duration_tooltip'}
        self.assertEqual(timed, {9324: 1, 9325: 20})
        self.assertIsNone(self.entries[9325]['unknown']['server_timer_rule'])

    def test_caps_and_immediate_evolution_remain_distinct(self):
        def caps(key):
            return [c['value'] for c in self.entries[key]['claims'] if 'value' in c]
        self.assertEqual(caps(9403), [70, 80, 80])
        self.assertEqual(caps(9408), [90, 100, 100])
        self.assertEqual(caps(9421), [1, 1, 1])
        self.assertEqual(caps(9427), [])
        self.assertEqual(caps(9433), [100, 100, 100])
        immediate = {k for k, r in self.entries.items() for c in r['claims']
                     if c['kind'] == 'immediate_evolution_tooltip'}
        self.assertEqual(immediate, {9420, 9427, 9428, 9433})

    def test_unknowns_and_no_arithmetic_hatch_mapping(self):
        for row in self.entries.values():
            self.assertFalse(row['runtime_eligible'])
            self.assertTrue(all(v is None for v in row['unknown'].values()))
            self.assertNotIn('hatch_result', row)
        self.assertIn(9426, self.entries)
        self.assertNotIn(9326, self.entries)

    def test_unqualified_or_malformed_bytes_fail_closed(self):
        for raw in (b'', self.raw[:-1], b'\0' + self.raw[1:], self.raw + b'\0'):
            with self.subTest(size=len(raw)), self.assertRaises(ValueError):
                extract(raw)

    def test_deterministic_and_independent_results(self):
        original = serialize(self.result)
        second = extract(self.raw)
        self.assertEqual(original, serialize(second))
        changed = copy.deepcopy(second)
        changed['entries'][0]['unknown']['growth_formula'] = 'invented'
        self.assertEqual(original, serialize(self.result))
        self.assertNotEqual(original, serialize(changed))


if __name__ == '__main__':
    unittest.main()
