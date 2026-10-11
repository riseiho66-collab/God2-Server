"""Continuous owner-row selection and original skill-book lookup, not learning."""

import json
from pathlib import Path
import unittest

from tools.strike_lab.current_skill_book_owner_chain import NativeSkillBookOwnerChain


ROOT = Path(__file__).resolve().parents[2]


class SkillBookOwnerChainTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = NativeSkillBookOwnerChain()
        cls.artifact = json.loads((ROOT / 'artifacts/research/current-skill-book-binding-20260920.json').read_text())

    def test_original_owner_row_to_source_loaded_book(self):
        cases = ((0, 1, 0, 6501, 'SpcA01', 0),
                 (0, 96, 1, 6568, 'SpcA96', 1),
                 (1, 1, 4, 6601, 'SpcD01', 0))
        entries = {(entry['kind'], entry['skill_id']): entry for entry in self.artifact['entries']}
        for kind, skill_id, page, item_id, code, tail in cases:
            with self.subTest(kind=kind, skill_id=skill_id, page=page):
                result = self.native.owner_book(kind, skill_id, page=page)
                self.assertEqual((result['item_id'], result['code'], result['tail_12c']),
                                 (item_id, code, tail))
                self.assertEqual(result['source_line'], entries[kind, skill_id]['source_line'])
                self.assertEqual(result['slot'], page * 10)
                self.assertEqual(result['lookup_keys'][-1], item_id)

    def test_unmatched_current_definition_does_not_invent_book(self):
        self.assertIn({'kind': 0, 'skill_id': 68}, self.artifact['unmatched'])
        result = self.native.owner_book(0, 68)
        self.assertIsNone(result['item_id'])
        self.assertEqual(result['item_ptr'], 0)

    def test_invalid_staged_identity_and_page(self):
        for kind, skill_id, page in ((-1, 1, 0), (4, 1, 0), (0, 0, 0),
                                     (0, 256, 0), (0, 1, -1), (0, 1, 5),
                                     (True, 1, 0), (0, 1.0, 0)):
            with self.subTest(kind=kind, skill_id=skill_id, page=page):
                with self.assertRaises(ValueError):
                    self.native.owner_book(kind, skill_id, page=page)


if __name__ == '__main__':
    unittest.main()
