"""Original SKB row loader storage, not server skill coefficients."""
from pathlib import Path
import re
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.strike_lab.current_item_metadata import NativeItemMetadata, growth


class SkillBookFieldTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.n = NativeItemMetadata()

    def expected_byte(self, fields, column):
        if column >= len(fields):
            return 0
        match = re.match(rb'^[ \t]*([+-]?[0-9]+)', fields[column])
        return int(match[1]) & 255 if match else 0

    def test_all_source_book_rows_and_native_lookup(self):
        rows = self.n.sections['SKB']['records']
        self.assertEqual(len(rows), 381)
        lengths = {29: 0, 30: 0}
        for index, row in enumerate(rows):
            with self.subTest(index=index):
                fields = growth.fields(row)
                lengths[len(fields)] += 1
                result = self.n.item_row('SKB', index)
                self.assertEqual(result['selector'], 6)
                self.assertEqual(result['key'], int(fields[0]))
                self.assertEqual(result['record'][0x12c:0x12f],
                                 bytes(self.expected_byte(fields, c) for c in (27, 28, 29)))
                self.assertEqual(result['record'][0x11c:0x12c], fields[26][:15].ljust(16, b'\0'))
                self.assertEqual(result['columns'][-5:], (26, 26, 27, 28, 29))
        self.assertEqual(lengths, {29: 157, 30: 224})

    def test_each_numeric_tail_changes_only_one_byte(self):
        rows = self.n.sections['SKB']['records']
        original = rows[0]
        baseline = self.n.item_row('SKB', 0)['record']
        try:
            for column in (27, 28, 29):
                for text, value in ((b'0', 0), (b'-1', 255), (b'255', 255),
                                    (b'256', 0), (b'999', 231), (b'15min', 15), (b'none', 0)):
                    fields = growth.fields(original)
                    fields[column] = text
                    rows[0] = growth.record(b','.join(fields) + b'\r\n',
                                           original['source_line'], original['decoded_offset'])
                    expected = bytearray(baseline)
                    expected[0x12c + column - 27] = value
                    with self.subTest(column=column, text=text):
                        self.assertEqual(self.n.item_row('SKB', 0)['record'], bytes(expected))
        finally:
            rows[0] = original

    def test_missing_last_column_does_not_inherit_previous_row(self):
        rows = self.n.sections['SKB']['records']
        short = next(i for i, row in enumerate(rows) if len(growth.fields(row)) == 29)
        self.assertEqual(self.n.item_row('SKB', 0)['record'][0x12e], 3)
        self.assertEqual(self.n.item_row('SKB', short)['record'][0x12e], 0)
        self.assertEqual(self.n.item_row('SKB', 0)['record'][0x12e], 3)


if __name__ == '__main__':
    unittest.main()
