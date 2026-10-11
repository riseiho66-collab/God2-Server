"""Pinned native producer probes and complete field-domain coverage, offline."""
import hashlib
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.strike_lab import current_monster_rewards_capture as subject


class MonsterRewardsCaptureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = subject.load_image()
        cls.oracle = subject.CaptureResultOracle(cls.image)
        cls.report = subject.build_evidence()

    def test_source_pins_and_native_spans_fail_closed(self):
        self.assertEqual(hashlib.sha256(self.image).hexdigest(), subject.IMAGE_SHA256)
        for name, (lo, hi) in subject.SPANS.items():
            span = self.report['native_proof']['spans'][name]
            self.assertEqual(span['file_offset'], lo)
            self.assertEqual(bytes.fromhex(span['raw_hex']), self.image[lo:hi])
            self.assertEqual(span['sha256'], hashlib.sha256(self.image[lo:hi]).hexdigest())
        changed = bytearray(self.image)
        changed[0x128de1] ^= 1
        with self.assertRaises(ValueError):
            subject.native_evidence(changed)
        with self.assertRaises(ValueError):
            subject.CaptureResultOracle(changed)

    def test_original_relay_byte_width_and_high_byte_counterfactual(self):
        for low in range(256):
            for high in (0, 255):
                with self.subTest(low=low, high=high):
                    result = self.oracle.relay(low | (high << 8))
                    self.assertEqual(result['stop_rva'], 0x128e60)
                    self.assertEqual(result['result_byte'], low)
                    expected = bytearray(b'\xa5' * 0x80)
                    expected[0x53] = low
                    self.assertEqual(bytes.fromhex(result['context_hex']), expected)
                    self.assertEqual(result['writes'], [
                        (0x128de7, self.oracle.CONTEXT + 0x53, 1, low)])
                    actor_reads = [r for r in result['reads']
                                   if self.oracle.ACTOR <= r[1] < self.oracle.ACTOR + 0x300]
                    self.assertEqual(actor_reads, [(0x128de1, self.oracle.ACTOR + 0x286, 1)])

    def test_action_and_null_pointer_gate_only_the_result_relay(self):
        for action in range(256):
            result = self.oracle.relay(0xff05, action=action)
            if action != 0x96:
                self.assertEqual(result['stop_rva'], 0x128dec)
                self.assertEqual(result['writes'], [])
                self.assertEqual(result['result_byte'], 0xa5)
                self.assertFalse(any(r[1] == self.oracle.ACTOR + 0x286 for r in result['reads']))
        result = self.oracle.relay(5, output_present=False)
        self.assertEqual(result['stop_rva'], 0x128e60)
        self.assertEqual(result['writes'], [])
        self.assertFalse(any(r[1] == self.oracle.ACTOR + 0x286 for r in result['reads']))

    def test_all_original_selector_branches_stop_before_ui(self):
        for selector in range(256):
            result = self.oracle.select_message(selector)
            expected = subject.MESSAGE_IDS[selector - 1] if 1 <= selector <= 9 else None
            self.assertEqual(result['message_id'], expected)
            self.assertEqual(result['stop_rva'], 0x1141bc if expected else 0x1141c4)
            self.assertNotIn(0x1141bf, result['visits'])
        # The same result slot also selects transformation-card copy labels.
        self.assertEqual(self.oracle.select_message(6)['message_id'], 1390)

    def test_message_text_provenance_and_qualified_meaning(self):
        messages = {row['selector']: row for row in self.report['result_messages']}
        expected = {
            1: (884, 38591, '\u6230\u5bf5\u6355\u6349\u6210\u529f'),
            3: (882, 38555, '\u6230\u5bf5\u6355\u6349\u5931\u6557'),
            4: (883, 38575, '\u7121\u6cd5\u6355\u6349'),
            5: (1151, 51478, '\u6b64\u602a\u7269\u7b49\u7d1a\u9ad8\u65bc\u73a9\u5bb6\uff0c\u7121\u6cd5\u6355\u6349'),
        }
        for selector, (identity, offset, text) in expected.items():
            row = messages[selector]
            self.assertEqual((row['id'], row['decoded_offset'], row['text_cp950']), (identity, offset, text))
            self.assertEqual(row['sha256'], hashlib.sha256(bytes.fromhex(row['raw_hex'])).hexdigest())
        self.assertIsNone(self.report['native_proof']['server_capturability'])
        self.assertIsNone(self.report['native_proof']['client_capture_target_selection_gate'])
        self.assertIsNone(self.report['native_proof']['identity_join'])

    def test_every_source_occurrence_has_explicit_unresolved_fields(self):
        report = self.report
        coverage = report['coverage']
        self.assertEqual((coverage['source_occurrences'], coverage['source_groups'],
                          coverage['lookup_visible_records'], coverage['lookup_visible_groups'],
                          coverage['superseded_occurrences']), (7815, 97, 7791, 96, 24))
        records = report['records']
        self.assertEqual([r['identity']['source_record_index'] for r in records], list(range(7815)))
        keys = {tuple(r['identity'][key] for key in report['identity_join_key']) for r in records}
        self.assertEqual(len(keys), 7815)
        for row in records:
            identity = row['identity']
            self.assertEqual(identity['record_sha256'],
                             hashlib.sha256(bytes.fromhex(identity['raw_record_hex'])).hexdigest())
            self.assertIn(len(identity['fields_hex']), (6, 10))
            self.assertEqual(identity['source_sha256'], subject.SOURCE_SHA)
            self.assertEqual(set(row['fields']), set(subject.FIELDS))
            self.assertIsNone(row['category'])
            for field in row['fields'].values():
                self.assertEqual(field['status'], 'unresolved_no_identity_bound_original_producer')
                for key in ('value', 'value_source_sha256', 'value_source_offset', 'producer_rva', 'identity_join'):
                    self.assertIsNone(field[key])
        superseded = [r['identity'] for r in records if not r['identity']['lookup_visible']]
        self.assertEqual(len(superseded), 24)
        self.assertEqual({r['area'] for r in superseded}, {7})
        for field in subject.FIELDS:
            self.assertEqual(coverage['fields'][field], {
                'verified_records': 0, 'unresolved_source_occurrences': 7815,
                'unresolved_lookup_records': 7791})
        self.assertIsNone(coverage['true_wild_monster_denominator'])
        self.assertFalse(coverage['all_monster_systems_enumerated'])
        self.assertEqual(set(coverage['categories']), set(subject.CATEGORIES))
        self.assertTrue(all(v['denominator'] is None for v in coverage['categories'].values()))
        self.assertFalse(report['runtime_eligible'])

    def test_synthetic_input_bounds(self):
        for value in (-1, 65536, True, 1.5):
            with self.assertRaises(ValueError):
                self.oracle.relay(value)
        for value in (-1, 256, True):
            with self.assertRaises(ValueError):
                self.oracle.relay(0, action=value)
            with self.assertRaises(ValueError):
                self.oracle.select_message(value)
        with self.assertRaises(ValueError):
            self.oracle.relay(0, output_present=1)


if __name__ == '__main__':
    unittest.main()
