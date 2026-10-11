"""Current-only binary evidence, original readers, and non-promotion boundaries."""
import copy
import io
import json
from pathlib import Path
import struct
import sys
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.strike_lab import current_monster_binary_producer as probe


class CurrentMonsterBinaryProducerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = probe.read_pinned(probe.IMAGE)
        cls.rtbs = [probe.read_pinned(path) for path in probe.RTBS]
        cls.decoded = probe.decode_csvz(probe.read_pinned(probe.MDL), limit=probe.MAX_BYTES)
        cls.mdl = probe.parse_mdl(cls.decoded)

    def test_report_opens_exactly_four_pinned_inputs_read_only(self):
        original = Path.open
        opened = []

        def guarded(path, mode='r', *args, **kwargs):
            self.assertIn(path, probe.PINS)
            self.assertEqual(mode, 'rb')
            opened.append(path)
            return original(path, mode, *args, **kwargs)

        with patch.object(Path, 'open', guarded):
            report = probe.build_report()
        self.assertCountEqual(opened, probe.PINS)
        self.assertEqual(len(opened), 4)
        self.assertFalse(report['runtime_eligible'])
        self.assertFalse(report['all_monster_numeric_data_complete'])
        self.assertEqual(report['verified_wild_monster_records'], 0)
        self.assertEqual(report['verified_boss_records'], 0)
        self.assertEqual(report['monster_field_authority'], dict.fromkeys(probe.FIELDS))
        self.assertIsNone(report['next_family'])
        self.assertNotIn('catalog', report)

    def test_native_spans_calls_and_literal_bindings(self):
        evidence = probe.native_evidence(self.image)
        self.assertEqual(len(evidence['spans']), 23)
        self.assertEqual(len(evidence['calls']), 29)
        self.assertIn({'rva': 0x3ef35, 'target_rva': 0x4c6f0}, evidence['calls'])
        self.assertIn({'rva': 0x309ec, 'target_rva': 0x1df60}, evidence['calls'])
        changed = bytearray(self.image)
        changed[0x2f330] ^= 1
        with self.assertRaisesRegex(ValueError, 'image changed'):
            probe.native_evidence(bytes(changed))

    def test_rtb_complete_native_reader_and_pointer_replacement(self):
        for raw, objects, instructions in zip(self.rtbs, (2, 3), (713, 980)):
            with self.subTest(objects=objects):
                n, layout, execution = probe.native_rtb(self.image, raw)
                self.assertEqual(layout['objects'], objects)
                self.assertEqual(layout['frames_per_object'], 60)
                self.assertEqual(layout['unaccounted_bytes'], 0)
                self.assertEqual(execution['all_source_bytes_read'], len(raw))
                self.assertEqual(execution['instruction_count'], instructions)
                self.assertEqual(execution['serialized_pointers_replaced'], objects)
                self.assertTrue(execution['handle_closed'])
                self.assertIn(0x2d930, n.visits)
                self.assertIn(0x28740, n.visits)
                cursor = 0
                for read in execution['io']:
                    self.assertEqual(read['source_offset'], cursor)
                    cursor += read['size'] * read['count']
                self.assertEqual(cursor, len(raw))
                for rec in layout['records']:
                    self.assertNotEqual(n.get32(0x3a00000 + rec['index'] * 52 + 48),
                                        rec['serialized_pointer_48'])

    def test_source_backed_frame_selection_and_render_scalar(self):
        for raw in self.rtbs:
            n, layout, _ = probe.native_rtb(self.image, raw)
            frames = probe.rtb_frame_consumers(n, raw, layout)
            self.assertEqual(len(frames), layout['objects'] * 4)
            for result in frames:
                self.assertEqual(result['movement_arguments'], [0, 0])
                self.assertEqual(result['renderer_scalar_hex'], '0000803f')
                self.assertEqual(result['frame_hex'], '000000000000803f02000000')
            self.assertEqual(frames[1]['source_offset'], frames[3]['source_offset'])
            self.assertIn(0x1df60, n.visits)
            self.assertIn(0x26fe0, n.visits)
            self.assertNotIn(0x1dbc0, n.visits)

    def test_counterfactual_signed_movement_is_not_lost_in_zero_sources(self):
        n, layout, _ = probe.native_rtb(self.image, self.rtbs[0])
        raw = bytearray(self.rtbs[0])
        first = layout['records'][0]
        changed = struct.pack('<hhfB3x', -32768, 32767, 0.25, 2)
        raw[first['frames_start']:first['frames_start'] + 12] = changed
        n.put(n.get32(0x3a00000 + 48), changed)
        result = probe.rtb_frame_consumers(n, bytes(raw), layout)[0]
        self.assertEqual(result['movement_arguments'], [-32768, 32767])
        self.assertEqual(result['renderer_scalar_hex'], struct.pack('<f', 0.25).hex())
        with self.assertRaisesRegex(ValueError, 'pinned RTB'):
            probe.native_rtb(self.image, bytes(raw))

    def test_rtb_rejects_bad_counts_truncation_and_unaccounted_bytes(self):
        source = self.rtbs[0]
        for candidate in (b'', source[:-1], source + b'\0', b'X' + source[1:]):
            with self.subTest(length=len(candidate)), self.assertRaises(ValueError):
                probe.parse_rtb(candidate)
        for at, count in ((8, 0), (8, -1), (8, 257), (10, 0), (10, 4097)):
            candidate = bytearray(source)
            struct.pack_into('<h', candidate, at, count)
            with self.subTest(at=at, count=count), self.assertRaises(ValueError):
                probe.parse_rtb(bytes(candidate))

    def test_mdl_all_regions_references_and_conditional_attachment_structure(self):
        mdl = self.mdl
        self.assertEqual(probe.sha(self.decoded), probe.MDL_SHA)
        self.assertEqual([len(mdl[key]) for key in ('rom_references', 'tiles', 'models', 'groups', 'placements')],
                         [27, 266, 266, 601, 9875])
        self.assertEqual(mdl['pass_cells'], 10292)
        self.assertEqual(sum(group['count'] for group in mdl['groups']), 9875)
        self.assertEqual(sum(p['attached_reference'] is not None for p in mdl['placements']), 81)
        self.assertEqual(sum(p['fields'][9] != 0 for p in mdl['placements']), 719)
        cursor = 0
        for region in mdl['regions']:
            self.assertEqual(region['start'], cursor)
            end = region['end_exclusive']
            self.assertEqual(probe.sha(self.decoded[cursor:end]), region['sha256'])
            cursor = end
        self.assertEqual(cursor, 389290)
        self.assertEqual(mdl['unaccounted_bytes'], 0)
        for row in mdl['placements']:
            self.assertEqual(probe.sha(self.decoded[row['offset']:row['end_exclusive']]), row['sha256'])

    def test_mdl_native_lookup_geometry_and_extra_stores(self):
        rows = [self.mdl['placements'][0], self.mdl['placements'][-1],
                next(p for p in self.mdl['placements'] if p['attached_reference']),
                next(p for p in self.mdl['placements'] if p['fields'][9] == 5)]
        for row in rows:
            result = probe.native_mdl_placement(self.image, row, 266)
            self.assertEqual(result['constructor_arguments'][:6], row['block'] + row['fields'][1:5])
            self.assertEqual(result['constructor_arguments'][6], 0x3600000 + row['fields'][0] * 512)
            self.assertEqual(result['extra_store_values'],
                             [row['fields'][i] & 0xffffffff for i in (5, 6, 7, 9)])
            self.assertEqual(result['row_instructions'], 69)
            self.assertEqual(result['initializer_instructions'], 11)
            self.assertEqual(result['extra_store_instructions'], 14)
            self.assertTrue(result['model_pointer_is_fixture'])
            self.assertIsNone(result['monster_identity'])
        invalid = copy.deepcopy(rows[0])
        invalid['fields'][0] = 266
        with self.assertRaises(ValueError):
            probe.native_mdl_placement(self.image, invalid, 266)

    def test_mdl_rejects_unsupported_versions_bad_refs_and_trailing_bytes(self):
        source = self.decoded
        first = self.mdl['placements'][0]
        row = source[first['offset']:first['end_exclusive']]
        candidates = (source.replace(b'MDL v1.6', b'MDL v1.7', 1), source[:-1], source + b'garbage\r\n',
                      source.replace(b'ROMFILE 27', b'ROMFILE 129', 1),
                      source.replace(row, b'266 ' + row.split(b' ', 1)[1], 1),
                      source.replace(b'Pass\r\n', b'Nope\r\n', 1))
        for candidate in candidates:
            with self.subTest(prefix=candidate[:24]), self.assertRaises(ValueError):
                probe.parse_mdl(candidate)

    def test_summary_preserves_unknown_authority_and_does_not_expand_scope(self):
        stream = io.StringIO()
        with patch.object(sys, 'argv', ['probe', '--summary']), redirect_stdout(stream):
            probe.main()
        result = json.loads(stream.getvalue())
        self.assertEqual(result['mdl']['structure']['placements_count'], 9875)
        self.assertEqual(result['monster_field_authority'], dict.fromkeys(probe.FIELDS))
        self.assertFalse(result['runtime_eligible'])
        self.assertIsNone(result['next_family'])
        self.assertIn('Resource IDs/model indices are not monster IDs.', ' '.join(result['limits']))
        with self.assertRaisesRegex(ValueError, 'Only the fixed'):
            probe.read_pinned(ROOT / 'not-an-allowed-input')


if __name__ == '__main__':
    unittest.main()
