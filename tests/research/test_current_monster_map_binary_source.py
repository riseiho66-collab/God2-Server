"""Current MBD source/reader qualification; no client, server, or database writes."""
import hashlib
import io
import json
from pathlib import Path
import struct
import sys
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.strike_lab import current_monster_map_binary_source as source


class CurrentMonsterMapBinarySourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.opened = []
        original = Path.open

        def current_only(path, mode='r', *args, **kwargs):
            if path not in source.PINS or mode != 'rb':
                raise AssertionError(f'Unexpected source access: {path} ({mode})')
            cls.opened.append(path)
            return original(path, mode, *args, **kwargs)

        with mock.patch.object(Path, 'open', current_only):
            cls.report = source.build_report()
        cls.raw = source.read_pinned(source.PLAIN)
        cls.image = source.read_pinned(source.IMAGE)

    def test_fixed_read_surface_and_exact_plain_compressed_equivalence(self):
        self.assertEqual(self.opened, [source.PLAIN, source.PACKED, source.IMAGE])
        self.assertTrue(self.report['plain_equals_decoded'])
        self.assertEqual(self.report['decoded_sha256'], source.PLAIN_SHA)
        self.assertEqual([s['bytes'] for s in self.report['sources']], [3035748, 735668])
        with mock.patch.object(Path, 'open', side_effect=AssertionError('Must reject before open')):
            with self.assertRaisesRegex(ValueError, 'Only the fixed current'):
                source.read_pinned(source.CLIENT / 'Data2/map/unselected.mbd')

    def test_all_bytes_accounted_as_header_index_and_packed_blocks(self):
        layout = source.parse_mbd(self.raw)
        self.assertEqual((layout['width'], layout['height']), (35, 37))
        self.assertEqual((layout['present_blocks'], layout['absent_blocks']), (859, 436))
        self.assertEqual(layout['index_end'], 0x144c)
        present = [offset for offset in layout['offsets'] if offset]
        self.assertEqual(present, list(range(0x144c, len(self.raw), 21 * 21 * 8)))
        self.assertEqual(len(self.raw), 16 + 1295 * 4 + 859 * 21 * 21 * 8)
        self.assertEqual(self.report['structure']['unaccounted_bytes'], 0)
        self.assertEqual(self.report['structure']['index_sha256'],
                         'da6107876d89fafbdcb2042afadef40f29879f4c74914fdeef4d7a469cc36d20')

    def test_original_block_index_seek_size_and_return(self):
        absent, *present = self.report['block_execution']
        self.assertEqual((absent['index'], absent['return_value'], absent['io']), (0, 0, []))
        self.assertIsNone(absent['payload_sha256'])
        expected = (
            (34, 0x144c, '0462367625a2eedf9ad6eba746275657c085d38340969a4718c0d3cefa6e2e89'),
            (87, 0x2fdc, '44dfdbfdafa5c7da6886d446a7e2a2e34e991ff0bae29b8b90b5197b7a9b3171'),
            (1294, 0x2e449c, '3a4d30f1ae6909a1ef1fa3f3073fc6894493096e6f7e1a887c39124f3da8b63e'))
        for run, (index, offset, digest) in zip(present, expected):
            with self.subTest(index=index):
                self.assertEqual((run['index'], run['source_offset'], run['return_value']), (index, offset, 1))
                self.assertEqual(run['payload_sha256'], digest)
                self.assertEqual(source.sha(self.raw[offset:offset + 3528]), digest)
                self.assertEqual(run['io'], [
                    {'rva': 0x1477a3, 'operation': 'fseek', 'offset': offset, 'origin': 0},
                    {'rva': 0x14785c, 'operation': 'fread', 'size': 3528, 'count': 1}])
                self.assertLess(run['instruction_count'], 200)

    def test_static_reader_and_tile_consumer_operands(self):
        native = self.report['native']
        self.assertEqual(native['sha256'], source.IMAGE_SHA)
        for span in native['spans'].values():
            self.assertEqual(hashlib.sha256(self.image[span['start_rva']:span['end_rva_exclusive']]).hexdigest(),
                             span['sha256'])
        calls = {call['rva']: call['target_rva'] for call in native['calls']}
        self.assertEqual(calls[0x3cf9a], 0x408e0)
        self.assertEqual(calls[0x3b7b1], 0x40790)
        self.assertEqual(calls[0x3b7ce], 0x3b1b0)
        # Assert the field width/addressing, not just the existence of a diagnostic.
        from capstone import Cs, CS_ARCH_X86, CS_MODE_32
        decoder = Cs(CS_ARCH_X86, CS_MODE_32)
        expected = {
            0x3b712: ('mov', 'eax, 0x15'),
            0x3b719: ('push', '0x1b9'),
            0x3b7c7: ('movsx', 'ebp, word ptr [ecx + eax*8]'),
            0x3b1e5: ('mov', 'eax, dword ptr [esi + edi*4 + 0x110]'),
            0x407e2: ('mov', 'eax, dword ptr [ecx + eax*4]'),
            0x40809: ('shl', 'edx, 3'),
        }
        for rva, wanted in expected.items():
            instruction = next(decoder.disasm(self.image[rva:rva + 15], source.BASE + rva))
            self.assertEqual((instruction.mnemonic, instruction.op_str), wanted)

    def test_rejects_malformed_structure_without_inferring_values(self):
        cases = [self.raw[:15], self.raw + b'\0', self.raw[:-1],
                 b'MBD v1.1' + self.raw[8:], self.raw[:0x144b]]
        for offset, value in ((8, 0), (12, 0xffffffff), (16 + 34 * 4, 16),
                              (16 + 69 * 4, 0x144c), (16 + 87 * 4, 0x2fdd)):
            changed = bytearray(self.raw)
            struct.pack_into('<I', changed, offset, value)
            cases.append(bytes(changed))
        for number, raw in enumerate(cases):
            with self.subTest(case=number), self.assertRaises(ValueError):
                source.parse_mbd(raw)

    def test_rejects_pin_changes_before_native_execution(self):
        with mock.patch.object(source, 'NativeRun', side_effect=AssertionError('Must not execute')):
            with self.assertRaisesRegex(ValueError, 'pinned current MBD'):
                source.native_block(self.image, self.raw[:-1] + bytes([self.raw[-1] ^ 1]), 87)
            for index in (-1, 1295, True):
                with self.assertRaisesRegex(ValueError, 'Block index'):
                    source.native_block(self.image, self.raw, index)
        changed = bytearray(self.image)
        changed[0x40790] ^= 1
        with self.assertRaisesRegex(ValueError, 'Pinned image'):
            source.native_evidence(bytes(changed))
        with mock.patch.object(Path, 'open', return_value=io.BytesIO(b'changed')):
            with self.assertRaisesRegex(ValueError, 'Pinned source hash'):
                source.read_pinned(source.PLAIN)

    def test_word_2_has_a_real_local_consumer_but_no_stat_meaning(self):
        from capstone import Cs, CS_ARCH_X86, CS_MODE_32
        decoder = Cs(CS_ARCH_X86, CS_MODE_32)
        expected = {
            0x3b7be: ('mov', 'ecx, dword ptr [esp + 0x34]'),
            0x3b804: ('mov', 'edx, dword ptr [esp + 0x34]'),
            0x3b808: ('imul', 'ecx, edi'),
            0x3b80b: ('add', 'ecx, esi'),
            0x3b80d: ('lea', 'ecx, [edx + ecx*8]'),
            0x3b810: ('movsx', 'edx, word ptr [ecx + 2]'),
            0x3b814: ('cmp', 'edx, dword ptr [esp + 0x10]'),
            0x3b818: ('jle', '0x43b83b'),
            0x3b82c: ('movsx', 'edx, word ptr [ecx + 2]'),
            0x3b830: ('cmp', 'edx, dword ptr [esp + 0x10]'),
            0x3b834: ('jle', '0x43b83b'),
            0x3b836: ('dec', 'edx'),
            0x3b837: ('mov', 'word ptr [ecx + 2], dx'),
        }
        for rva, wanted in expected.items():
            with self.subTest(rva=hex(rva)):
                instruction = next(decoder.disasm(self.image[rva:rva + 15], source.BASE + rva))
                self.assertEqual((instruction.mnemonic, instruction.op_str), wanted)
        use = self.report['native']['cell_word_2_use']
        self.assertEqual((use['cell_offset'], use['width'], use['signed_read']), (2, 2, True))
        self.assertEqual(use['read_rvas'], [0x3b810, 0x3b82c])
        self.assertEqual(use['write_rva'], 0x3b837)
        self.assertIsNone(use['meaning'])

    def test_empty_hook_is_pinned_disqualified_and_retained_in_summary(self):
        from capstone import Cs, CS_ARCH_X86, CS_MODE_32
        raw = self.image[0x38790:0x387a0]
        self.assertEqual(raw, b'\xc3' + b'\x90' * 15)
        instructions = list(Cs(CS_ARCH_X86, CS_MODE_32).disasm(raw, source.BASE + 0x38790))
        self.assertEqual([(i.mnemonic, i.op_str) for i in instructions], [('ret', '')] + [('nop', '')] * 15)
        rejected, = self.report['disqualified_source_recovery_targets']
        self.assertEqual((rejected['call_rva'], rejected['callee_rva']), (0x37f4c, 0x38790))
        self.assertEqual(rejected['bytes_hex'], raw.hex())
        self.assertEqual(rejected['sha256'], '499f1f307c1cb989f968a6b7fcaec591e1828877223d0b0e7e8e8b76cde8c9ca')
        self.assertEqual((rejected['start_rva'], rejected['end_rva_exclusive']), (0x38790, 0x387a0))
        with mock.patch.object(source, 'build_report', return_value=self.report), \
                mock.patch.object(sys, 'argv', ['sidecar', '--summary']), \
                mock.patch('sys.stdout', new_callable=io.StringIO) as output:
            source.main()
        summary = json.loads(output.getvalue())
        self.assertEqual(summary['disqualified_source_recovery_targets'], [rejected])
        self.assertIsNone(summary['next_unexamined']['callee_rva'])

    def test_monster_authority_stays_unknown_and_next_consumer_unresolved(self):
        self.assertEqual(self.report['verified_wild_monster_records'], 0)
        self.assertEqual(self.report['verified_boss_records'], 0)
        self.assertEqual(len(self.report['monster_field_authority']), 21)
        self.assertTrue(all(v is None for v in self.report['monster_field_authority'].values()))
        self.assertFalse(self.report['runtime_eligible'])
        self.assertIsNone(self.report['cell_authority']['bytes_2_through_7'])
        frontier = self.report['next_unexamined']
        self.assertIsNone(frontier['call_rva'])
        self.assertIsNone(frontier['callee_rva'])
        self.assertEqual(frontier['source_block'], {'index': 87, 'start': 0x2fdc, 'end_exclusive': 0x3da4})
        self.assertIsNone(frontier['wild_stat_binding'])
        self.assertEqual(self.report['samples'][1]['first_cell_hex'], '21000b0032000080')


if __name__ == '__main__':
    unittest.main()
