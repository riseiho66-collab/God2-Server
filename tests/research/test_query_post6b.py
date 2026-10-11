import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/strike_lab'))
from query_post6b import TRACE, captured_context, run_query


class Post6BQueryTests(unittest.TestCase):
    def setUp(self):
        self.events = [json.loads(line) for line in
                       (ROOT / TRACE).read_bytes().splitlines() if line.strip()]

    def test_exact_frozen_pair(self):
        event = captured_context(self.events)
        self.assertEqual(event['pc'], 0x412506)
        self.assertEqual(event['a1'], 0x4133b3)

    def test_mismatch_and_duplicate_rejected(self):
        for field, value in [('pc', 0x412507), ('matched', False),
                             ('tid', 999), ('eax', 5), ('sp', 0), ('a1', 0)]:
            with self.subTest(field=field):
                events = copy.deepcopy(self.events)
                next(e for e in events if e.get('sequence') == 147)[field] = value
                with self.assertRaises(ValueError):
                    captured_context(events)
        duplicate = next(e for e in self.events if e.get('sequence') == 147)
        with self.assertRaises(ValueError):
            captured_context(self.events + [duplicate])

    def test_three_partial_queries_agree_but_never_certify_direction(self):
        results = [run_query() for _ in range(3)]
        for result in results:
            self.assertEqual(result['verdict'], 'NEED_MORE_EVIDENCE')
            self.assertEqual(result['next_direction'], 'UNKNOWN')
            self.assertFalse(result['codegen_allowed'])
            self.assertFalse(result['new_edge_accepted'])
            self.assertIsNone(result['state_after_hash'])
            self.assertEqual(result['completed_rvas'], [0x12506, 0x12507, 0x12509, 0x1250a])
            self.assertEqual(result['faulting_rva'], 0x133b3)
            self.assertEqual(result['first_missing_dependency']['offset'], 0x40d4)
            self.assertEqual(result['first_missing_dependency']['size'], 4)
            self.assertEqual(result['first_missing_dependency'], results[0]['first_missing_dependency'])


if __name__ == '__main__':
    unittest.main()
