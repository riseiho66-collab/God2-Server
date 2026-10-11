"""Current-only native item-result proof and complete identity null coverage."""
import io
import json
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.strike_lab import current_monster_drop_rules as drops


class CurrentMonsterDropRulesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = drops.build_report()
        cls.cases = {case['case']: case for case in cls.report['counterfactuals']}
        cls.native = drops.NativeLootResult()
        cls.catalog = drops.inventory.pinned_catalog()

    def consume(self, entries, *, selector=0, previous=(0xa501, 0xa502, 0xa503, 0xa504)):
        return self.native.consume(drops.synthetic_record(entries, selector=selector),
                                   previous_slots=previous, spectator=False)

    def test_complete_occurrences_preserve_exact_source_keys_and_offsets(self):
        rows = self.report['records']
        self.assertEqual(len(rows), 7815)
        self.assertEqual(len({tuple(r['identity'][k] for k in drops.IDENTITY) for r in rows}), 7815)
        plain = self.native.metadata.decoded
        for actual, original in zip(rows, self.catalog['records'], strict=True):
            self.assertEqual(actual['identity'], {k: original[k] for k in drops.IDENTITY})
            self.assertEqual(actual['lookup_visible'], original['lookup_visible'])
            src = actual['source']
            self.assertEqual(src['sha256'], drops.inventory.SOURCE_SHA)
            self.assertEqual(src['decoded_sha256'], drops.inventory.PLAIN_SHA)
            self.assertEqual(src['line'], original['source_line'])
            self.assertEqual(src['decoded_offset'], original['source_offset'])
            raw = bytes.fromhex(src['raw_record_hex'])
            self.assertEqual(plain[src['decoded_offset']:src['decoded_offset'] + len(raw)], raw)
            self.assertEqual(drops.sha(raw), src['row_sha256_including_line_ending'])
        self.assertEqual(sum(r['lookup_visible'] for r in rows), 7791)
        self.assertEqual(sum(not r['lookup_visible'] for r in rows), 24)
        self.assertEqual(self.report['coverage']['visible_groups'], 96)
        self.assertEqual(self.report['coverage']['source_groups'], 97)

    def test_no_item_definition_or_probe_promoted_to_monster_drop(self):
        self.assertFalse(self.report['runtime_eligible'])
        self.assertIsNone(self.report['coverage']['all_boss_denominator'])
        self.assertIsNone(self.report['coverage']['unique_species_denominator'])
        self.assertFalse(self.report['coverage']['all_monster_systems_enumerated'])
        self.assertEqual(set(self.report['requested_scope']),
                         {'normal', 'boss', 'elite', 'event', 'quest', 'summoned'})
        for row in self.report['records']:
            self.assertIsNone(row['monster_classification'])
            self.assertIsNone(row['variant_identity'])
            self.assertEqual(row['native_values'], dict.fromkeys(drops.FIELDS))
        for coverage in self.report['field_coverage'].values():
            self.assertEqual(coverage, {'verified_source_occurrences': 0,
                                       'unresolved_source_occurrences': 7815,
                                       'unresolved_visible_occurrences': 7791})
        self.assertTrue(all(v is None for v in self.report['remaining_frontier'].values()))
        for case in self.cases.values():
            self.assertEqual(case['input_authority'], 'synthetic_counterfactual_not_original_loot')
        parsed = json.loads(json.dumps(self.report))
        self.assertIsNone(parsed['records'][-1]['native_values']['drop_rates'])

    def test_source_item_original_producer_and_index_are_executed(self):
        item = self.report['current_source_item_probe']
        source = item['source']
        self.assertEqual(source['file_sha256'], drops.inventory.SOURCE_SHA)
        row = source['record']
        raw = bytes.fromhex(row['raw_record_hex'])
        self.assertEqual(row['source_line'], 7636)
        self.assertEqual(row['decoded_offset'], 545749)
        self.assertEqual(drops.sha(raw), row['sha256'])
        self.assertEqual(self.native.metadata.decoded[545749:545749 + len(raw)], raw)
        self.assertEqual(item['key'], 4660)
        self.assertEqual((item['native_icon_group'], item['native_icon_action']), (37, 65535))
        for rva in (0x59420, 0x59a20, 0x59a60, 0x9b720):
            self.assertIn(rva, item['producer_executed_rvas'])
        record = bytes.fromhex(item['native_record_hex'])
        self.assertEqual(record[8:].split(b'\0', 1)[0], bytes.fromhex(row['fields_hex'][4]))

    def test_four_slots_run_native_lookup_and_store_then_native_name_consumer(self):
        case = self.cases['four_positive']
        self.assertEqual(case['slot_keys'], [drops.KEY] * 4)
        self.assertEqual(case['stop_rva'], 0x118c6f)
        self.assertEqual([w[0] for w in case['slot_writes']], [0x85443] * 4)
        self.assertEqual([w[2:] for w in case['slot_writes']], [[2, drops.KEY]] * 4)
        self.assertEqual([w[1] - self.native.metadata.OWNER for w in case['slot_writes']],
                         [0x23d618, 0x23d61a, 0x23d61c, 0x23d61e])
        for index, args in enumerate(case['icon_call_raw_arguments']):
            self.assertEqual(args[0] & 65535, 65535)
            self.assertEqual(args[1:], [37, index, 0xffffffff])
        for rva in (0x118c21, 0x853d0, 0x9b720, 0x59a60, 0x1068c0, 0x85443):
            self.assertIn(rva, case['executed_rvas'])
        source_name = self.native.item['record'][8:].split(b'\0', 1)[0]
        self.assertEqual(bytes.fromhex(case['name_consumer']['text_hex']), b','.join([source_name] * 4))
        self.assertIn(0x59a60, case['name_consumer']['executed_rvas'])
        self.assertNotIn(0x5a0a0, case['name_consumer']['executed_rvas'])

    def test_loss_marker_is_word_and_any_positive_slot_can_select_loss_header(self):
        for index in range(4):
            for marker in (0, 1, 65534, 65535):
                with self.subTest(index=index, marker=marker):
                    entries = [(drops.KEY, 0, 0)] * 4
                    entries[index] = (drops.KEY, marker, 0)
                    result = self.consume(entries)
                    self.assertEqual(result['slot_keys'], [drops.KEY] * 4)
                    self.assertEqual(result['selected_program_message'], 298 if marker == 65535 else None)
                    self.assertEqual(result['stop_rva'], 0x118c5a if marker == 65535 else 0x118c6f)
        row = self.report['loss_message']
        self.assertEqual(row['source_line'], 2324)
        self.assertEqual(row['decoded_offset'], 0x169a0)
        self.assertEqual(bytes.fromhex(row['text_hex']).decode('cp950'),
                         '\u60a8\u6389\u843d\u4ee5\u4e0b\u88dd\u5099:')
        self.assertEqual(drops.sha(bytes.fromhex(row['raw_record_hex'])), row['row_sha256'])
        self.assertEqual(self.cases['spectator_loss_marker']['selected_program_message'], 293)

    def test_nonpositive_signed_entries_preserve_previous_slots_and_skip_marker(self):
        result = self.cases['signed_gate']
        self.assertEqual(result['slot_keys'], [0xa501, 0xa502, 0xa503, drops.KEY])
        self.assertEqual([x[1:] for x in result['packet_reads']],
                         [[49, 4], [17, 4], [25, 4], [33, 4], [41, 4], [45, 2]])
        self.assertIsNone(result['selected_program_message'])
        for value in (0, 0x80000000, 0x80001234, 0xffffffff):
            with self.subTest(value=value):
                result = self.consume([(value, 65535, 65535)] * 4)
                self.assertEqual(result['slot_keys'], [0xa501, 0xa502, 0xa503, 0xa504])
                self.assertEqual(result['slot_writes'], [])
                self.assertEqual(result['icon_call_raw_arguments'], [])
                self.assertEqual(len(result['packet_reads']), 5)
                self.assertIsNone(result['selected_program_message'])

    def test_positive_dword_is_low_word_item_key_not_quantity_or_monster_key(self):
        baseline = self.cases['four_positive']
        for label in ('high_word_alias', 'unused_tail'):
            result = self.cases[label]
            self.assertEqual(result['slot_keys'], baseline['slot_keys'])
            self.assertEqual(result['icon_call_raw_arguments'], baseline['icon_call_raw_arguments'])
            self.assertEqual(result['packet_reads'], baseline['packet_reads'])
            self.assertEqual(result['stop_rva'], baseline['stop_rva'])
        self.assertEqual([x[1:] for x in baseline['packet_reads']],
                         [[49, 4], [17, 4], [21, 2], [25, 4], [29, 2],
                          [33, 4], [37, 2], [41, 4], [45, 2]])
        result = self.consume([(0x7fff1234, 0, 65535)] * 4)
        self.assertEqual(result['slot_keys'], [drops.KEY] * 4)
        self.assertNotIn(0x5a0a0, result['executed_rvas'])

    def test_lookup_missing_and_out_of_bounds_use_native_fallback_but_still_store_key(self):
        for case, key in (('fixture_uninstalled_key', 1), ('lookup_upper_bound', 0x7f58)):
            result = self.cases[case]
            self.assertEqual(result['slot_keys'], [key] * 4)
            self.assertIn(0x9b753, result['executed_rvas'])
            for index, args in enumerate(result['icon_call_raw_arguments']):
                self.assertEqual(args[1:], [65, index, 0xffffffff])
        result = self.consume([(0x7fffffff, 0, 0)] * 4)
        self.assertEqual(result['slot_keys'], [65535] * 4)

    def test_selector_counterfactuals_never_run_item_loop(self):
        targets = {1: 0x118cf2, 2: 0x118cfc, 3: 0x118cd9, 4: 0x118d48, 0xffffffff: 0x118d48}
        for value, stop in targets.items():
            case = self.cases['selector_' + str(value)]
            self.assertEqual(case['stop_rva'], stop)
            self.assertEqual(case['slot_keys'], case['previous_slots'])
            self.assertEqual(case['packet_reads'], [[0x118bf8, 49, 4]])
            self.assertEqual(case['slot_writes'], [])
            self.assertNotIn(0x853d0, case['executed_rvas'])

    def test_active_control_stops_before_unqualified_renderer_without_faking_return(self):
        case = self.cases['active_control_boundary']
        self.assertEqual(case['stop_rva'], 0x106927)
        self.assertEqual(case['slot_keys'], case['previous_slots'])
        self.assertEqual(case['slot_writes'], [])
        self.assertEqual(len(case['icon_call_raw_arguments']), 1)
        self.assertEqual(case['icon_call_raw_arguments'][0][0] & 65535, 0)
        self.assertNotIn(0x1ea00, case['executed_rvas'])

    def test_receive_queue_and_size_static_bindings_match_pinned_image(self):
        image = self.native.metadata.image
        self.assertEqual(image[0x119a04 + 0x89], 24)
        self.assertEqual(struct.unpack_from('<I', image, 0x119908 + 24 * 4)[0], drops.BASE + 0x1195cc)
        self.assertEqual(image[0x11465c + 0x89 - 0x1c], 8)
        self.assertEqual(struct.unpack_from('<I', image, 0x114634 + 8 * 4)[0], drops.BASE + 0x114582)
        self.assertEqual(image[0x11459a], 0xe8)
        self.assertEqual(0x11459f + struct.unpack_from('<i', image, 0x11459b)[0], 0x118bf0)
        self.assertEqual(struct.unpack_from('<I', image, 0x1548)[0], drops.BASE + 0x1240)
        self.assertEqual(image[0x1240:0x1246], b'\xb8\x39\x00\x00\x00\xc3')

    def test_instruction_and_message_provenance_have_exact_original_bytes(self):
        image = self.native.metadata.image
        self.assertEqual(drops.sha(image), drops.IMAGE_SHA)
        for name, span in self.report['native_spans'].items():
            lo, hi = drops.SPANS[name]
            self.assertEqual((span['offset'], span['end_exclusive']), (lo, hi))
            self.assertEqual(bytes.fromhex(span['raw_hex']), image[lo:hi])
            self.assertEqual(span['sha256'], drops.sha(image[lo:hi]))
        raw = drops.pinned(drops.CLIENT / drops.MESSAGE, drops.MESSAGE_SHA)
        plain = drops.decode_csvz(raw)
        row = self.report['loss_message']
        selected = bytes.fromhex(row['raw_record_hex'])
        self.assertEqual(plain[row['decoded_offset']:row['decoded_offset'] + len(selected)], selected)

    def test_reject_wrong_length_opcode_and_unknown_context(self):
        record = drops.synthetic_record([(drops.KEY, 0, 0)] * 4)
        for bad in (b'', record[:-1], record + b'\0', b'\x88' + record[1:], bytearray(record)):
            with self.assertRaises(ValueError):
                self.native.consume(bad, previous_slots=(1, 2, 3, 4), spectator=False)
        for slots in (None, (1, 2, 3), (1, 2, 3, -1), (True, 2, 3, 4)):
            with self.assertRaises(ValueError):
                self.native.consume(record, previous_slots=slots, spectator=False)

    def test_source_pins_fail_closed_without_writing_files(self):
        for payload, expected, limit in ((b'changed', drops.IMAGE_SHA, 100),
                                         (b'xx', drops.sha(b'xx'), 1)):
            with patch.object(Path, 'open', return_value=io.BytesIO(payload)):
                with self.assertRaises(ValueError):
                    drops.pinned('unused', expected, limit)


if __name__ == '__main__':
    unittest.main()
