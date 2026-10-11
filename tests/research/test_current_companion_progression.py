"""Original QualityStar consumer arithmetic, precise boundaries and provenance."""
from pathlib import Path
import struct
import unittest
from unittest.mock import patch

from tools.strike_lab import current_companion_progression as progression


ROOT = Path(__file__).resolve().parents[2]
CLIENT = ROOT.parent / 'God2'
IMAGE = ROOT / 'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin'
growth = progression.growth


class CurrentCompanionProgressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = progression.build_evidence(CLIENT, IMAGE)
        cls.image, cls.decoded = progression.qualified_inputs(CLIENT, IMAGE)

    def test_all_source_indices_two_branches_and_unrelated_bits(self):
        self.assertEqual(self.result['case_count'], 1024)
        values = [[growth.decimal(x) for x in growth.fields(row)]
                  for row in self.result['source']['records']]
        cases = []
        for mode in (1, 0x100):
            for noise in (0, 0xff00ffff):
                for qi in range(16):
                    for si in range(16):
                        cases.append({
                            'packed': (qi << 20) | (si << 16) | noise, 'mode': mode,
                            'quality': [qi, values[0][qi]], 'star': [si, values[1][si]],
                            'table_reads': [
                                [0xb7e38 if mode == 1 else 0xb7efd, 0x3400000 + qi * 2, 2],
                                [0xb7f98, 0x3400100 + si * 2, 2]]})
        self.assertEqual(growth.digest(growth.serialize(cases)), self.result['cases_sha256'])

    def test_gate_is_integer_sum_equals_one_not_truthy_or(self):
        cases = self.result['synthetic_gate_cases']
        self.assertEqual(len(cases), 9)
        self.assertEqual([(x['first'], x['second']) for x in cases if x['admitted']],
                         [(0, 1), (1, 0)])
        for case in cases:
            self.assertEqual(case['sum'], case['first'] + case['second'])
        native = progression.NativeProgression(self.image, self.decoded)
        self.assertEqual(native.gate(255, 255)['sum'], 510)

    def test_pinned_source_records_and_code_provenance(self):
        source = self.result['source']
        self.assertEqual(source['decoded_sha256'], growth.digest(self.decoded))
        self.assertEqual([r['source_line'] for r in source['records']], [5, 7])
        for row in source['records']:
            raw = bytes.fromhex(row['raw_record_hex'])
            start = row['decoded_offset']
            self.assertEqual(self.decoded[start:start + len(raw)], raw)
            self.assertEqual(growth.digest(raw), row['sha256'])
        for kind in ('executed_ranges', 'static_only_ranges'):
            for span in self.result[kind].values():
                self.assertEqual(span['sha256'], growth.digest(
                    self.image[span['start_rva']:span['stop_rva_exclusive']]))
        for call in self.result['calls']:
            self.assertEqual(progression.relative_call(self.image, call['call_rva'], call['target_rva']), call)
        for name, sha in self.result['dependencies'].items():
            self.assertEqual(sha, growth.digest((ROOT / 'tools/strike_lab' / name).read_bytes()))

    def test_source_zero_is_observed_without_stat_or_exp_claim(self):
        example = self.result['diagonal_examples'][0]
        self.assertEqual((example['quality'], example['star']), ([0, 0], [0, 0]))
        self.assertFalse(self.result['runtime_eligible'])
        self.assertFalse(self.result['growth_formula_verified'])
        self.assertFalse(self.result['experience_thresholds_verified'])
        self.assertIsNone(self.result['deity_xp_lead'])
        self.assertEqual(self.result['classification'], 'native_display_argument_selection_only')
        self.assertEqual(self.result['next_producer']['status'],
                         'static_caller_argument_boundary_not_value_writer')
        self.assertEqual(self.result['formats']['0x1929f4'], '%s:%d (%s+%d)')

    def test_changed_authority_fails_before_native_execution(self):
        with self.assertRaisesRegex(ValueError, 'native image'):
            progression.NativeProgression(b'changed', self.decoded)
        with self.assertRaisesRegex(ValueError, 'decoded QualityStar'):
            progression.NativeProgression(self.image, self.decoded + b'\n')
        with patch.object(growth, 'read_source', return_value=b'changed'):
            with self.assertRaisesRegex(ValueError, 'native image'):
                progression.qualified_inputs(CLIENT, IMAGE)
        actual = growth.read_source

        def changed_source(root, path):
            return b'changed' if path == growth.source_path(progression.SOURCE) else actual(root, path)

        with patch.object(growth, 'read_source', side_effect=changed_source):
            with self.assertRaisesRegex(ValueError, 'current QualityStar'):
                progression.qualified_inputs(CLIENT, IMAGE)

    def test_no_formatter_or_game_callee_success_stub(self):
        native = progression.NativeProgression(self.image, self.decoded)
        native.prepare()
        with self.assertRaisesRegex(AssertionError, 'Unexpected consumer instruction'):
            native.segment(0xb7e4d, (0xb7e52,))
        # Null table input must fault at the actual read, never fabricate values.
        native.vm.mem_write(native.TABLE + 0xfc2cc, struct.pack('<I', 0))
        with self.assertRaises(native.uc.UcError):
            native.arguments(0, 1)

    def test_inputs_are_read_only_to_native_code(self):
        native = progression.NativeProgression(self.image, self.decoded)
        for address in (native.TABLE, native.OUTPUT, native.INPUT, native.OWNER):
            regions = [(a, b, p) for a, b, p in native.vm.mem_regions() if a <= address <= b]
            self.assertEqual(len(regions), 1)
            self.assertEqual(regions[0][2], native.uc.UC_PROT_READ)
        for packed, mode in ((-1, 1), (1 << 32, 1), (0, 0), (0, 0x101)):
            with self.assertRaises(ValueError):
                native.arguments(packed, mode)


if __name__ == '__main__':
    unittest.main()
