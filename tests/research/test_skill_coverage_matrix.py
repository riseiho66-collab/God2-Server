"""Audit the generated full matrix without silently rerunning native matrices."""
import copy
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.strike_lab import skill_coverage_matrix as matrix


class SkillCoverageMatrixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = matrix.read_pinned(matrix.CLIENT / matrix.identity.SOURCE,
                                        matrix.identity.SOURCE_SHA256)
        cls.encoded = matrix.OUTPUT.read_bytes()
        cls.report = json.loads(cls.encoded, object_pairs_hook=matrix.unique_object)

    def test_full_source_denominator_and_every_actor_state_key(self):
        # Independently enumerate source group headers and direct record bytes.
        expected = {}
        for kind in range(4):
            group = 4 + kind * 0x6e04
            count, = struct.unpack_from('<I', self.source, group)
            for ordinal in range(count):
                offset = group + 4 + ordinal * 110
                raw = self.source[offset:offset + 110]
                self.assertEqual(raw[:2], bytes((ordinal + 1, kind)))
                expected[kind, ordinal + 1] = (offset, matrix.digest(raw))
        self.assertEqual(len(expected), 448)
        rows = self.report['definitions']
        self.assertEqual([(r['kind'], r['id']) for r in rows], sorted(expected))
        states = ('empty', 'full', 'sparse_signed')
        expected_keys = {(kind, identity, actor, state)
                         for kind, identity in expected for actor in range(14) for state in states}
        keys = []
        for row in rows:
            self.assertEqual((row['source_offset'], row['record_sha256']),
                             expected[row['kind'], row['id']])
            self.assertEqual(row['source_sha256'], matrix.digest(self.source))
            self.assertEqual((row['cases_run'], row['cases_pass'], row['cases_fail']), (42, 42, 0))
            keys.extend((row['kind'], row['id'], c['actor'], c['state']) for c in row['cases'])
        self.assertEqual(len(keys), len(set(keys)))
        self.assertEqual(set(keys), expected_keys)
        self.assertEqual(len(keys), 18816)
        self.assertGreater(len(keys), 4 * 4480)
        matrix.validate_report(self.report, self.source)
        matrix.require_success(self.report)

    def test_every_stored_native_result_matches_formal_result(self):
        for row in self.report['definitions']:
            for case in row['cases']:
                self.assertEqual(case['native'], case['formal'],
                                 (row['kind'], row['id'], case['actor'], case['state']))
                self.assertIs(case['passed'], True)
        self.assertEqual(self.report['formal_executable']['sha256'],
                         matrix.digest(matrix.EXECUTABLE.read_bytes()))
        image = matrix.read_pinned(matrix.IMAGE, matrix.identity.IMAGE_SHA256)
        self.assertEqual(self.report['native_image']['sha256'], matrix.digest(image))

    def test_canonical_json_and_no_duplicate_object_keys(self):
        self.assertEqual(matrix.serialize(self.report).encode('ascii'), self.encoded)
        with self.assertRaisesRegex(ValueError, 'Duplicate JSON key'):
            json.loads('{"passed":true,"passed":false}', object_pairs_hook=matrix.unique_object)
        self.assertNotIn('timing', self.report)
        self.assertNotIn('generated_at', self.report)

    def test_denominator_corruption_is_rejected(self):
        for operation in ('omit_definition', 'duplicate_definition', 'omit_case',
                          'duplicate_case', 'wrong_actor', 'wrong_state', 'inflate_count'):
            with self.subTest(operation=operation):
                report = copy.deepcopy(self.report)
                rows = report['definitions']
                if operation == 'omit_definition':
                    rows.pop()
                elif operation == 'duplicate_definition':
                    rows[-1] = copy.deepcopy(rows[0])
                elif operation == 'omit_case':
                    rows[0]['cases'].pop()
                elif operation == 'duplicate_case':
                    rows[0]['cases'][-1] = copy.deepcopy(rows[0]['cases'][0])
                elif operation == 'wrong_actor':
                    rows[0]['cases'][0]['actor'] = 14
                elif operation == 'wrong_state':
                    rows[0]['cases'][0]['state'] = 'invented'
                else:
                    report['summary']['cases_pass'] += 1
                with self.assertRaises(ValueError):
                    matrix.validate_report(report, self.source)

    def test_counterfactual_formal_failure_cannot_remain_green(self):
        report = copy.deepcopy(self.report)
        row = report['definitions'][0]
        case = row['cases'][0]
        case['formal'][0] ^= 1
        with self.assertRaisesRegex(ValueError, 'Case comparison mismatch'):
            matrix.validate_report(report, self.source)
        case['passed'] = False
        row['cases_pass'] -= 1
        row['cases_fail'] += 1
        report['summary'] = matrix.summarize(report)
        matrix.validate_report(report, self.source)
        self.assertEqual(report['summary']['cases_fail'], 1)
        self.assertEqual(report['summary']['cases_pass'], 18815)
        with self.assertRaisesRegex(ValueError, 'Target comparison failed'):
            matrix.require_success(report)

    def test_formula_denominators_remain_unverified_and_promotions_fail(self):
        for name in matrix.FORMULAS:
            self.assertEqual(self.report['summary']['formula_counts'][name],
                             {'definitions': 448, 'verified': 0, 'unverified': 448})
            report = copy.deepcopy(self.report)
            evidence = report['definitions'][0]['formula_evidence'][name]
            evidence['server_coefficients'] = {'multiplier': 7}
            with self.assertRaisesRegex(ValueError, 'Formula authority promotion'):
                matrix.validate_report(report, self.source)

    def test_state_meaning_and_batch_protocol_boundaries(self):
        states = {state['id']: state for state in self.report['states']}
        self.assertEqual(states['empty']['masks'], [0, 0])
        self.assertEqual(states['empty']['entity_words'], [None] * 28)
        self.assertEqual(states['full']['masks'], [0x3fff, 0x3fff])
        sparse = states['sparse_signed']
        self.assertEqual(set(sparse['entity_words']), {None, -32768, -1, 0, 32767})
        self.assertTrue(all(0 < mask < 0x3fff for mask in sparse['masks']))
        fields = matrix.targeting.Fields(40, 0, 0, 5, 14)
        values = list(map(int, matrix.batch_line(fields, 13, matrix.STATES['sparse_signed']).split()))
        self.assertEqual(len(values), 38)
        self.assertEqual(values[:6], [40, 0, 0, 5, 14, 13])
        self.assertEqual(values[10:17], [32768, -32768, -1, 0, 32767, 32768, -1])
        for stdout, count in (('', 1), ('0 0 0 0 0 -1 -1 1\n', 2),
                              ('0 0 0 0 0 -1 -1 1\n' * 2, 1),
                              ('0 0\n', 1), ('x 0 0 0 0 0 0 0\n', 1)):
            with self.subTest(stdout=stdout, count=count), self.assertRaises(ValueError):
                matrix.parse_batch(stdout, count)


if __name__ == '__main__':
    unittest.main()
