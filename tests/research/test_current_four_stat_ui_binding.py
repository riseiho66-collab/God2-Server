"""Source-backed UI binding checks; no gameplay VM or desktop process."""
import io
import struct
import unittest

from PIL import Image

from tools.strike_lab import current_four_stat_ui_binding as ui


class CurrentFourStatUIBindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report, cls.images, cls.roms = ui.audit()
        cls.image = ui.pinned_read(ui.IMAGE_PATH, ui.IMAGE_SHA)

    def test_native_fields_control_ids_and_local_coordinates(self):
        expected = [
            ('role', 0x94, 4, 23, 0x196fb2, [194, 217]),
            ('role', 0x98, 4, 24, 0x196fc8, [194, 242]),
            ('role', 0x9c, 4, 30, 0x19704c, [194, 267]),
            ('role', 0xa0, 4, 31, 0x197062, [194, 292]),
            ('companion', 0x38, 2, 6, 0x191f2c, [73, 165]),
            ('companion', 0x3a, 2, 7, 0x191f42, [73, 185]),
            ('companion', 0x3c, 2, 8, 0x191f58, [73, 205]),
            ('companion', 0x3e, 2, 9, 0x191f6e, [73, 225]),
        ]
        self.assertEqual([(v['family'], v['field_offset'], v['field_width'], v['control'],
                           v['descriptor_rva'], v['local_xy'])
                          for v in self.report['bindings']], expected)
        disasm = '\n'.join(self.report['slices']['companion_panel']['disassembly'])
        self.assertIn('0A7DD5 sub ax, word ptr [esp + 0x14]', disasm)
        self.assertIn('0A7DDA sub cx, word ptr [esp + 0x10]', disasm)
        self.assertEqual(struct.unpack_from('<4i', self.image, 0x191e60), (539, 0, 799, 569))
        # The special-key display branch preserves the same four UI controls.
        for start, end, field, control in (
                (0xa9bfb, 0xa9c22, 0x38, 6), (0xa9c22, 0xa9c49, 0x3a, 7),
                (0xa9c49, 0xa9c70, 0x3c, 8), (0xa9c70, 0xa9c97, 0x3e, 9)):
            binding = ui.number_binding(self.image, start, end, 'edi')
            self.assertEqual((binding['field_offset'], binding['control']), (field, control))

    def test_selected_real_assets_match_independent_pillow_decode(self):
        for name, slot, ordinal, offset, dims in (
                ('role', 34, 26, 0x675da, (252, 427)),
                ('role_muye', 34, 48, 0xca5e5, (252, 427)),
                ('companion', 29, 0, 0xe6e, (261, 570))):
            with self.subTest(panel=name):
                selected = self.report['panels'][name]
                self.assertEqual((selected['image_index'], selected['image_offset'],
                                  selected['palette_index']), (ordinal, offset, 0))
                pcx = self.roms[slot]['images'][ordinal]['data']
                width, height, pixels = ui.pcx_pixels(pcx)
                with Image.open(io.BytesIO(pcx)) as independent:
                    independent.load()
                    self.assertEqual(independent.size, dims)
                    self.assertEqual((width, height), dims)
                    self.assertEqual(pixels, independent.tobytes())
                    self.assertEqual(ui.sha(pixels), selected['pixels_sha256'])
        # This TGA consumes image index 3; excluding it shifts all role images.
        self.assertEqual(self.roms[34]['images'][3]['tag'], b'TGA_RWIF')
        for slot, opened, closed in ((34, 0x26, 0x27), (34, 0x43, 0x44), (29, 0, 1)):
            a, art_a = ui.select_action(self.roms[slot], opened)
            b, art_b = ui.select_action(self.roms[slot], closed)
            self.assertEqual(a['image_index'], b['image_index'])
            self.assertEqual(art_a.tobytes(), art_b.tobytes())
            self.assertEqual(a['palette_sha256'], b['palette_sha256'])

    def test_visually_transcribed_crops_remain_byte_exact(self):
        expected = [
            '1535a0bbc28f39bc8783aa0c20f0af7c5967db87214a9bbb6b136001ba774629',
            '2f9b26e43a5877509a1dcac200dad8007b82441441db16bdd413443e0bd8dfe1',
            '3dcf5f50ff1b2ae7f401f944de08950d85f6ada0ac39197c3ed8bb38290d354f',
            'f52f249601a5257208dedacbca95e3bd859d3d7794f7d74c3f272447ec5a2201',
            '39ca90a7c294be61621943076ae8a5d2ee48a8d23b2731f48b2be727de6a37e8',
            'ab739e5cb772e48b19d87180462c4476e58b59e0fa090847c10638fe5bde501d',
            '83962658d9cc77a158d493769da2ae9205a3af01d595be42302ff20752ec8122',
            'b4cb3b9ab34193ed42c0b6c2d397e3dfd66e4076f1c3fa3eb85579507b16e25e',
        ]
        self.assertEqual([v['label_index_pixels_sha256'] for v in self.report['bindings']], expected)
        for binding in self.report['bindings'][:4]:
            box = binding['label_crop_box']
            self.assertEqual(self.images['role'].crop(box).tobytes(),
                             self.images['role_muye'].crop(box).tobytes())
        # This pins the inspected evidence, not an automated Chinese OCR claim.
        self.assertFalse(set(ui.ROLE_LABELS) & set(ui.COMPANION_LABELS))

    def test_parser_rejects_truncated_chunks_and_invalid_row_spans(self):
        slot = 34
        path, raw_sha, decoded_sha = ui.SOURCES[slot]
        _, plain = ui.decoded_source(ui.CLIENT/path, raw_sha, decoded_sha)
        with self.assertRaisesRegex(ValueError, 'Truncated chunk header'):
            ui.parse_rom(plain[:-1])
        bad = bytearray(plain)
        struct.pack_into('<I', bad, 20, len(plain))
        with self.assertRaisesRegex(ValueError, 'Truncated chunk payload'):
            ui.parse_rom(bad)
        pcx = self.roms[slot]['images'][26]['data']
        with self.assertRaisesRegex(ValueError, 'span table size'):
            ui.pcx_pixels(pcx[:-1])
        bad = bytearray(pcx)
        struct.pack_into('<H', bad, len(bad)-2, 253)
        with self.assertRaisesRegex(ValueError, 'span boundary'):
            ui.pcx_pixels(bad)


if __name__ == '__main__':
    unittest.main()
