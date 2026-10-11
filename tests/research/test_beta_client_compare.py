import struct
import unittest

from tools.strike_lab.beta_client_compare import enemy_rows, skill_rows


class BetaCompareTests(unittest.TestCase):
    def test_both_skill_widths(self):
        for width in (108, 110):
            data = bytearray(4 + 4 * (4 + 256 * width))
            data[:4] = b'1.03'
            struct.pack_into('<I', data, 4, 1)
            data[8:10] = b'\x01\x00'
            self.assertEqual(len(skill_rows(data, width)[0, 1][1]), width)

    def test_bad_envelope(self):
        with self.assertRaises(ValueError):
            skill_rows(b'1.03', 108)

    def test_bad_identity(self):
        data = bytearray(4 + 4 * (4 + 256 * 108))
        data[:4] = b'1.03'
        struct.pack_into('<I', data, 4, 1)
        with self.assertRaises(ValueError):
            skill_rows(data, 108)

    def test_enemy_count(self):
        raw = b'EnyName,3\nEnyNameTotal,1\nEnyNameIsland_Area,1,1\n1,test,1,0,15,3\n'
        self.assertEqual(len(enemy_rows(raw)), 1)
        with self.assertRaises(ValueError):
            enemy_rows(raw.replace(b'Total,1', b'Total,2'))
