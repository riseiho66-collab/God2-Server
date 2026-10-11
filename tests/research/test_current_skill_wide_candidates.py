import struct
import unittest
from tools.strike_lab import current_skill_stat_consumers as probe


class WideCandidatesTests(unittest.TestCase):
    def test_candidate_index(self):
        result = probe.wide_image_inventory()
        self.assertEqual(len(result['candidates']), 263)
        addresses = {row['rva'] for row in result['candidates']}
        self.assertTrue({0x10a666, 0x10a66b, 0x10a66e, 0x126201, 0xa9100} <= addresses)
        self.assertEqual(result['authority'], 'UNQUALIFIED_OVERLAPPING_OPERAND_INDEX')

    def test_translation_slice_preserves_all_other_object_bytes(self):
        for old in (-32768, 0, 32767):
            for new in (-32768, 0, 32767):
                result = probe.translation_candidate(old, new, new, old)
                expected = bytearray(result['before'])
                struct.pack_into('<hh', expected, 0x4c, new, old)
                values = [100 + new-old, 200 + old-new, 300 + new-old, 400 + old-new]
                struct.pack_into('<4I', expected, 0x58, *(v & 0xffffffff for v in values))
                self.assertEqual(result['after'], expected)
                self.assertEqual(result['stop_rva'], 0x10a67d)
                self.assertFalse(result['skill_pointer_bound'])
                self.assertFalse(result['callee_executed'])

    def test_invalid_live_ins(self):
        for value in (-32769, 32768, True):
            with self.assertRaises(ValueError):
                probe.translation_candidate(value, 0, 0, 0)


if __name__ == '__main__':
    unittest.main()
