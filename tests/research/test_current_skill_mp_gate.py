"""Execute both original MP predicates with source records and counterfactuals."""
from pathlib import Path
import hashlib
import json
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.strike_lab.current_skill_mp_gate import NativeSkillMpGate
from tools.strike_lab.recover_combat_rules import CLIENT, SKILLS, SOURCE_HASHES, read_pinned
from tools.strike_lab.recover_combat_skills import parse_skills
from tools.strike_lab.omega_assets import decode_csvz


class SkillMpGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.n = NativeSkillMpGate()

    def test_live_fixture_identity_cost_and_menu_gate_are_distinct(self):
        raw=self.n.definitions[(0,1)].raw
        self.assertEqual(raw[:2],bytes((1,0)))
        self.assertEqual(struct.unpack_from('<H',raw,0x42)[0],5)
        self.assertEqual(raw[0x67],0)
        for mode in ('indexed','selected'):
            for mp in range(9):
                self.assertFalse(self.n.evaluate(raw,mp,mode=mode))
        # Counterfactual isolates the threshold; never claimed as native ownership.
        enabled=bytearray(raw);enabled[0x67]=1
        for mode in ('indexed','selected'):
            for mp in range(9):
                self.assertEqual(self.n.evaluate(bytes(enabled),mp,mode=mode),mp>=5)

    def test_all_definitions_thresholds_both_native_entries(self):
        self.assertEqual(len(self.n.definitions), 448)
        for identity, definition in self.n.definitions.items():
            raw = definition.raw
            cost = struct.unpack_from('<H', raw, 0x42)[0]
            for mp in sorted({0, max(0, cost - 1), cost, cost + 1, 0xffffffff}):
                for mode in ('indexed', 'selected'):
                    with self.subTest(identity=identity, mp=mp, mode=mode):
                        result = self.n.evaluate(raw, mp, mode=mode)
                        self.assertEqual(result, bool(raw[0x67]) and mp >= cost)

    def test_flag_and_unsigned_word_dword_boundaries(self):
        raw = bytearray(next(iter(self.n.definitions.values())).raw)
        for flag in (0, 1, 2, 127, 128, 255):
            raw[0x67] = flag
            for cost in (0, 1, 32767, 32768, 65535):
                struct.pack_into('<H', raw, 0x42, cost)
                for mp in (0, max(cost - 1, 0), cost, cost + 1, 0x80000000, 0xffffffff):
                    for mode in ('indexed', 'selected'):
                        self.assertEqual(self.n.evaluate(bytes(raw), mp, mode=mode), bool(flag) and mp >= cost)

    def test_selection_pages_and_missing_dependencies(self):
        raw = bytearray(110)
        raw[0x67] = 1
        raw = bytes(raw)
        for index in (0, 24, 25, 49, 50, 74, 75, 99):
            self.assertTrue(self.n.evaluate(raw, 0, index=index))
            self.assertTrue(self.n.evaluate(raw, 0, mode='selected', page=index // 25, selected=index % 25))
        for mode in ('indexed', 'selected'):
            for option in ({'menu_present': False}, {'entry_present': False},
                           {'index': -1, 'selected': -1}, {'index': -2147483648, 'selected': -128}):
                self.assertFalse(self.n.evaluate(raw, 65535, mode=mode, **option))

    def test_invalid_inputs_fail_before_native_execution(self):
        raw = bytes(110)
        for option in ({'mp': -1}, {'mp': 0x100000000}, {'index': 100}, {'page': 4},
                       {'selected': 25}, {'mode': 'unknown'}, {'menu_present': 1}):
            with self.assertRaises(ValueError):
                self.n.evaluate(raw, **({'mp': 0} | option))
        with self.assertRaises(ValueError):
            self.n.evaluate(raw[:-1], 0)

    def test_native_bound_book_descriptions_match_mp_field(self):
        rows = parse_skills(decode_csvz(read_pinned(CLIENT / SKILLS, SOURCE_HASHES[SKILLS])))
        books = {row['item_id']: row for row in rows['definitions']}
        binding = json.loads((ROOT / 'artifacts/research/current-skill-book-binding-20260920.json').read_text())
        self.assertEqual(binding['book_sha256'], SOURCE_HASHES[SKILLS])
        self.assertEqual(len(binding['entries']), 381)
        checked = 0
        for entry in binding['entries']:
            book = books[entry['item_id']]
            self.assertEqual(hashlib.sha256(bytes.fromhex(book['raw_record_hex'])).hexdigest(), entry['source_record_sha256'])
            claim = book['description_claims'].get('mp_cost')
            if claim:
                raw = self.n.definitions[entry['kind'], entry['skill_id']].raw
                self.assertEqual(claim['value'], struct.unpack_from('<H', raw, 0x42)[0])
                checked += 1
        self.assertEqual(checked, 243)


if __name__ == '__main__':
    unittest.main()
