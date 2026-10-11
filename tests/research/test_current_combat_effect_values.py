"""Four pinned source records plus explicit synthetic dataflow counterfactuals."""
import struct
import unittest

from tools.strike_lab import current_combat_effect_values as effects


SAMPLES = (2, 302, 936, 1201)


class CurrentCombatEffectValuesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image, cls.rows = effects.sources()

    def setUp(self):
        self.native = effects.NativeEffectValues(self.image)

    def test_pinned_header_dispatch_and_actual_allocation_arguments(self):
        self.assertEqual(len(self.rows), 1202)
        self.assertEqual(self.native.header(), {
            'native_count': 1202, 'allocation_arguments': [1203, 8],
            'loader_reached': True, 'stop_rva': '0x5bedf'})
        self.assertIn(0x56ec6, self.native.trace)
        self.assertIn(0x5beb0, self.native.trace)
        self.assertNotIn(0x147e23, self.native.trace)

    def test_four_source_rows_native_widths_and_consumer_pointer_provenance(self):
        for index in SAMPLES:
            with self.subTest(index=index):
                raw = self.rows[index]['raw']
                fields = raw.rstrip(b'\r\n').split(b',')
                loaded = self.native.load_row(raw)
                for col, field in enumerate(fields):
                    self.assertEqual(self.native.cstring(
                        effects.RESOURCE + 0x78 + col * effects.FIELD_STRIDE), field)
                pointer = effects.LABELS + index * 512
                self.assertEqual(loaded['index'], index)
                self.assertEqual(bytes.fromhex(loaded['native_record_hex']),
                                 struct.pack('<H2sI', index, b'\xa5\xa5', pointer))
                self.assertEqual(loaded['record_writes'], [
                    {'rva': '0x5bf49', 'offset': 0, 'bytes': 2},
                    {'rva': '0x5bf8d', 'offset': 4, 'bytes': 4}])
                self.assertEqual(loaded['allocation_bytes'], len(fields[4]) + 1)
                self.assertEqual(loaded['columns_requested'], [0, 0, 4, 4])
                self.assertEqual(loaded['token_columns_read'], [0, 4])
                self.assertEqual(self.native.get(effects.RESOURCE + 0xd2ab8, '<H'),
                                 (index + 1,))
                for neighbor in (index - 1, index + 1):
                    self.assertEqual(bytes(self.native.vm.mem_read(
                        effects.ROWS + neighbor * 8, 8)), b'\xa5' * 8)
                consumer = self.native.consume(index)
                self.assertEqual(consumer['description_pointer'], pointer)
                self.assertEqual(bytes.fromhex(consumer['description_hex']), fields[4])
                self.assertEqual(bytes.fromhex(consumer['text_hex']),
                                 effects.FIXTURE_LABEL + b': ' + fields[4])
                self.assertEqual(consumer['format_rva'], '0x190178')
                self.assertEqual(bytes.fromhex(consumer['format_hex']), b'%s: %s')
                self.assertTrue(consumer['native_lookup_executed'])
                self.assertTrue(consumer['native_formatter_executed'])
                self.assertEqual(consumer['next_stop_rva'], '0xbb97c')
                self.assertIn(0xbb8f7, self.native.trace)
                self.assertIn(0xbb935, self.native.trace)

    def test_code_category_basic_value_counterfactuals_preserve_record_and_text(self):
        # Mutants are synthetic, not additional original-source coverage.
        raw = self.rows[302]['raw']
        baseline = self.native.load_row(raw), self.native.consume(302)
        mutations = ((1, b'99'), (2, b'GOD_6421'), (2, b'NOT_AN_EFFECT'),
                     (3, b'-32768'), (3, b'2147483648'), (3, b'not-a-number'))
        for column, value in mutations:
            with self.subTest(column=column, value=value):
                fields = raw.rstrip(b'\r\n').split(b',')
                fields[column] = value
                actual = self.native.load_row(b','.join(fields) + b'\r\n')
                self.assertEqual(actual, baseline[0])
                self.assertEqual(self.native.consume(302), baseline[1])

    def test_description_counterfactual_changes_native_output_not_coefficient(self):
        fields = self.rows[302]['raw'].rstrip(b'\r\n').split(b',')
        self.native.load_row(self.rows[302]['raw'])
        baseline = self.native.consume(302)
        fields[4] = b'counterfactual literal hit 99%'
        loaded = self.native.load_row(b','.join(fields) + b'\r\n')
        actual = self.native.consume(302)
        self.assertEqual(loaded['allocation_bytes'], len(fields[4]) + 1)
        self.assertEqual(actual['text_hex'], (effects.FIXTURE_LABEL + b': ' + fields[4]).hex())
        self.assertNotEqual(actual['text_hex'], baseline['text_hex'])
        # Negative control: an oracle that ignores the description must fail.
        with self.assertRaises(AssertionError):
            self.assertEqual(actual['text_hex'], baseline['text_hex'])

    def test_exact_bytes_guard_and_bounded_tokenizer_inputs(self):
        class DerivedBytes(bytes):
            pass
        invalid = (None, '1,2,3,4,text\n', bytearray(b'1\n'), memoryview(b'1\n'),
                   DerivedBytes(b'1\n'), b'', b'1', b'a\0\n', b'a' * 380 + b'\n',
                   b'a' * 4095 + b'\n', b'0,1,2,3,4,5\n')
        for raw in invalid:
            with self.subTest(kind=type(raw).__name__, length=getattr(raw, '__len__', lambda: 0)()):
                with self.assertRaises(ValueError):
                    self.native.tokenize(raw)
        self.assertEqual(self.native.trace, [])
        self.assertEqual(self.native.tokenize(b'a' * 379 + b'\n'), 1)
        self.assertEqual(self.native.cstring(effects.RESOURCE + 0x78), b'a' * 379)
        self.assertEqual(self.native.tokenize(b'0,1,2,3,4\n'), 5)

    def test_native_index_bounds_reject_before_record_stores(self):
        for index in (-1, 1202, 65538):
            with self.subTest(index=index):
                raw = str(index).encode() + b',1,GOD_6421,50,fixture\n'
                with self.assertRaises(ValueError):
                    self.native.load_row(raw)
                self.assertEqual(bytes(self.native.vm.mem_read(effects.ROWS, 1203 * 8)),
                                 b'\xa5' * (1203 * 8))
                self.assertEqual(self.native.get(effects.RESOURCE + 0xd2ab8, '<H'), (0,))


if __name__ == '__main__':
    unittest.main()
