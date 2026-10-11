from pathlib import Path
import struct
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/strike_lab'))
from omega_assets import decode_csvz,validate_table


class OmegaAssetTests(unittest.TestCase):
    def test_literal_decode(self):
        data=b'\x05\x16'+struct.pack('<I',3)+b'Z\x07abc'
        self.assertEqual(decode_csvz(data),b'abc')

    def test_overlapping_back_reference(self):
        data=b'\x05\x16'+struct.pack('<I',7)+b'Z\x01a\xee\xf3'
        self.assertEqual(decode_csvz(data),b'a'*7)

    def test_initial_spaces(self):
        data=b'\x05\x16'+struct.pack('<I',3)+b'Z\x00\x00\x00'
        self.assertEqual(decode_csvz(data),b'   ')

    def test_bad_lengths_and_uninitialized_tail_fail(self):
        for data in (b'bad',b'\x05\x16'+struct.pack('<I',4)+b'Z\x07abc',
                     b'\x05\x16'+struct.pack('<I',3)+b'Z\x00\xff\xf0',
                     b'\x05\x16'+struct.pack('<I',3)+b'Z\x00\xee'):
            with self.assertRaises(ValueError): decode_csvz(data)

    def test_optional_string_columns_are_valid(self):
        value=validate_table(b'Any,v1,2,date\r\nSystemMessage,2\r\n1,0,one\r\n2,0,two,,\r\n')
        self.assertTrue(value['valid']);self.assertEqual(value['sections'][0]['max_observed_id'],2)
        self.assertEqual(value['sections'][0]['raw_decoded_offset'],15)
        self.assertEqual(value['sections'][0]['text_mode_offset'],14)

    def test_exact_tag_and_count_bounds(self):
        for value in (b'X,1,2\nSystemmessage,1\n1,0,a\n',b'X,1,2\nSystemMessage,1\n2,0,a\n',
                      b'X,1,2\nSystemMessage,32768\n1,0,a\n',b'X,1,2\nSystemMessage,2\n1,0,a\n'):
            self.assertFalse(validate_table(value)['valid'])


if __name__=='__main__': unittest.main()
