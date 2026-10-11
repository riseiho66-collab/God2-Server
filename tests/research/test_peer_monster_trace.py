import unittest

from tools.strike_lab.peer_monster_trace import compare_entries


def native(fields, *, visible=True, line=10):
    return dict(area=2, scene=0, ordinal=1, lookup_visible=visible, source_line=line,
                fields_hex=[f.hex() for f in fields])


class TraceTests(unittest.TestCase):
    def setUp(self):
        self.fields = ['1', 'test', '1', '0', '15', '6']
        self.peer = dict(area=2, map=0, entryIndex=1, name='test',
                         rawFields=self.fields, sourceLine=10)

    def test_exact_match_not_changed_line(self):
        row = native([v.encode() for v in self.fields], line=99)
        counts, issues, _ = compare_entries([self.peer], [row])
        self.assertEqual(counts['exact_fields'], 1)
        self.assertEqual(counts['same_source_line'], 0)
        self.assertFalse(issues)

    def test_duplicate_does_not_double_count(self):
        a = native([v.encode() for v in self.fields], visible=False)
        b = native([v.encode() for v in self.fields])
        counts, _, _ = compare_entries([self.peer], [a, b])
        self.assertEqual(counts['exact_fields'], 1)
        self.assertEqual(counts['exact_fields_visible'], 1)

    def test_undecodable_is_not_silently_replaced(self):
        fields = [v.encode() for v in self.fields]
        fields[1] = b'\xff'
        counts, issues, _ = compare_entries([self.peer], [native(fields)])
        self.assertEqual(counts['native_rows_with_undecodable_fields'], 1)
        self.assertEqual(issues[0]['reason'], 'native_decode_unresolved')
        self.assertNotIn('exact_fields', counts)

    def test_missing_and_changed_fields(self):
        counts, issues, _ = compare_entries([self.peer], [])
        self.assertEqual(issues[0]['reason'], 'missing_key')
        fields = [v.encode() for v in self.fields]
        fields[-1] = b'7'
        counts, issues, _ = compare_entries([self.peer], [native(fields)])
        self.assertEqual(issues[0]['reason'], 'different_fields')


if __name__ == '__main__':
    unittest.main()
