"""Native computational/source-binding regressions, not gameplay coverage."""
import copy
import hashlib
import struct
import unittest

from tools.strike_lab import current_critical_formula as critical


class CurrentCriticalCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = critical.build_report()

    def test_exact_image_and_independent_slice_hashes(self):
        image = critical.pinned_image()
        self.assertEqual(len(image), 3174400)
        expected = {
            'rng_core': '31bb6fafafa05866bf29918dc8d4b783401df229ab92b953d457695156c25e80',
            'action_producer': '91bc188cd6021a76623d4dead824aeb93b6e1823e0f6e60a1058b22facf84b18',
            'action_tables': '1cfd5c2310908b04f323a0793bef30572f3977514664b86bd841f7a41beda546',
            'effect_consumer': '40e4d3311054224c88d2fae33140ba841c0be37c32b3749b7807ad7449efddee',
        }
        for name, sha in expected.items():
            lo, hi = critical.SLICES[name]
            self.assertEqual(hashlib.sha256(image[lo:hi]).hexdigest(), sha)
            self.assertEqual(self.report['slices'][name]['sha256'], sha)

    def test_original_type_table_is_not_a_guessed_critical_bit(self):
        image = critical.pinned_image()
        expected = [0x12cb2d] * 6 + [0x12cb54, 0x12cb6b, 0x12cb6b, 0x12cb3a]
        expected += [0x12cb54] * 10 + [0x12cb47]
        actual = [struct.unpack_from('<I', image, 0x12cc98 + 4 * image[0x12ccac + i])[0]
                  - critical.BASE for i in range(21)]
        self.assertEqual(actual, expected)
        self.assertEqual(struct.unpack_from('<I', image, 0x12cc3c + 12 * 4)[0]
                         - critical.BASE, 0x12ca2d)

    def test_rng_native_recurrence_mask_remainder_and_write_order(self):
        rows = self.report['rng_cases']
        self.assertEqual(len(rows), 98)
        self.assertEqual(len({(r['seed'], r['poison']) for r in rows}), len(rows))
        outputs = set()
        for row in rows:
            with self.subTest(seed=row['seed'], poison=row['poison']):
                critical.verify_rng(row)
                outputs.add(critical.rng_reference(row['seed'])[1])
                self.assertEqual([w[0] for w in row['writes']],
                                 [0x147d93, 0x12b3cd, 0x12b3d4])
                self.assertEqual({(a - critical.ACTOR, size) for _, a, size in row['reads']
                                  if critical.ACTOR <= a < critical.ACTOR + 0x1000},
                                 {(0x1a, 2), (0x277, 1), (0x1e9, 1)})
        self.assertTrue({0, 1, 49, 50, 98, 99, 100, 101, 199, 200, 32767} <= outputs)
        # Known native state chain: re-use the prior original write as input.
        probe, seed = critical.Probe(), 1
        for expected in (41, 18467, 6334, 26500, 19169):
            row = probe.rng_to_action(seed)
            self.assertEqual(row['numeric_argument'], expected % 100)
            seed = row['next_seed']

    def test_received_amount_producer_is_byte_exact_not_doubled(self):
        rows = self.report['received_cases']
        self.assertEqual(len(rows), 176)
        for row in rows:
            with self.subTest(kind=row['kind'], value=row['value'], type=row['type_byte']):
                kind, value = row['kind'], row['value']
                self.assertEqual(row['stored_words'], [value, 0 if kind == 1 else 0x8123])
                amount_pc, type_pc, type_offset = ((0x12c615, 0x12c612, 10) if kind == 1
                                                  else (0x12c956, 0x12c94f, 12))
                self.assertIn((amount_pc, critical.PAYLOAD + 8, 2), row['reads'])
                self.assertIn((type_pc, critical.PAYLOAD + type_offset, 1), row['reads'])
                self.assertIn((0x12b3cd, critical.ACTOR + 0x286, 2, value), row['writes'])
                self.assertIn((0x12a95f, critical.ACTOR + 0x1e9, 1, kind), row['writes'])
                if 'numeric_argument' in row:
                    self.assertEqual(row['numeric_argument'], critical.signed16(value))
                else:
                    self.assertEqual(row['stop_rva'], {6: 0x12b453, 7: 0x12b43a,
                                                      8: 0x12b421}[row['type_byte']])
                # This is a limited read-footprint assertion, not universal
                # independence from all stats or a meaning assigned to +DB8.
                self.assertFalse(any(a < critical.ACTOR + 0xdbc and a + size > critical.ACTOR + 0xdb8
                                     for _, a, size in row['reads']))

    def test_result_arithmetic_signed_overflow_index_and_source(self):
        rows = self.report['arithmetic_cases']
        self.assertEqual(len(rows), 84)
        self.assertEqual({(r['type_byte'], r['counter']) for r in rows},
                         {(t, index) for t in range(21) for index in range(4)})
        for row in rows:
            critical.verify_accumulation(row)
            writes = row['writes']
            self.assertEqual(writes[1], (0x12cae3, critical.ACTOR + 0x2c4,
                                         2, row['counter'] + 1))
            self.assertEqual(writes[2], (0x12caee, critical.ACTOR + 0x4d0 + 2 * row['counter'], 2, 2))
            op = critical.TYPE_OPERATIONS.get(row['type_byte'])
            if op in ('add_a', 'add_b', 'replace_a'):
                self.assertEqual(writes[-1][1], critical.ACTOR + 0xb60 + 8 * row['counter']
                                 + (4 if op == 'add_b' else 0))
            else:
                self.assertEqual(len(writes), 4)
        # Diagnostic selectors are stopped BEFORE the call, not called success.
        self.assertEqual(self.report['counts']['arithmetic_stops'], {'12CB54': 44, '12CB6B': 40})

    def test_counterfactual_initial_state_changes_the_sum_not_a_multiplier(self):
        probe = critical.Probe()
        for selector in (0, 1, 5, 9, 20):
            for initial in (0, 1, 0x7fffffff, 0xffffffff):
                row = probe.action(13, 0xffff, selector, a=initial, b=initial)
                critical.verify_accumulation(row)
                expected = 0xffffffff if selector == 20 else (initial - 1) & 0xffffffff
                self.assertEqual(row['output'][1 if selector == 9 else 0], expected)

    def test_wrong_computational_claims_and_missing_provenance_are_detected(self):
        row = copy.deepcopy(self.report['rng_cases'][0])
        for key, replacement in (('next_seed', 0), ('numeric_argument', row['numeric_argument'] * 2),
                                 ('numeric_argument', critical.rng_reference(row['seed'])[1] // 100)):
            bad = copy.deepcopy(row)
            bad[key] = replacement
            with self.assertRaises(AssertionError):
                critical.verify_rng(bad)
        bad = copy.deepcopy(row)
        bad['reads'] = []
        with self.assertRaises(AssertionError):
            critical.verify_rng(bad)
        overflow = self.report['arithmetic_cases'][0]
        for output in ([0xffffffff, overflow['b']], [1, overflow['b']]):
            bad = copy.deepcopy(overflow)
            bad['output'] = output
            with self.assertRaises(AssertionError):
                critical.verify_accumulation(bad)
        negative = self.report['arithmetic_cases'][1]
        bad = copy.deepcopy(negative)
        bad['output'][0] = 65535  # Incorrect unsigned extension of received FFFF.
        with self.assertRaises(AssertionError):
            critical.verify_accumulation(bad)
        bad = copy.deepcopy(negative)
        bad['reads'] = []
        with self.assertRaises(AssertionError):
            critical.verify_accumulation(bad)

    def test_report_repeated_native_execution_is_byte_deterministic(self):
        self.assertEqual(critical.serialize(self.report), critical.serialize(critical.build_report()))
        self.assertEqual(self.report['counts']['total'], 358)
        self.assertLess(max(r['instruction_count'] for key in ('rng_cases', 'arithmetic_cases', 'received_cases')
                            for r in self.report[key]), 500)


if __name__ == '__main__':
    unittest.main()
