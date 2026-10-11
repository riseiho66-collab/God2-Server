"""Actual ACTMIS data through original x86 parser and requirement consumer."""
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.strike_lab import current_quest_requirements as q
from tools.strike_lab.omega_assets import decode_csvz


class CurrentQuestRequirementsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image, cls.table = q.evidence()
        cls.report = q.build_report()

    def vm_with_rows(self):
        native = q.NativeRequirements(self.image)
        for row in self.table['records']:
            self.assertIsNotNone(native.load_row(q.source_row(row)))
        return native

    def changed_row(self, serial=1, pairs=None):
        fields = [bytes.fromhex(f) for f in self.table['records'][0]['raw_fields_hex']]
        fields[0] = str(serial).encode('ascii')
        if pairs is not None:
            fields[2:] = [str(value).encode('ascii') for pair in pairs for value in pair]
        return b','.join(fields) + b'\r\n'

    def test_pins_fail_closed_and_extraction_retains_exact_source(self):
        with self.assertRaisesRegex(ValueError, 'Pinned image changed'):
            q.NativeRequirements(bytes([self.image[0] ^ 1]) + self.image[1:])
        with self.assertRaisesRegex(ValueError, 'requalification'):
            q.pinned(b'changed', q.SOURCE_SHA, 'ACTMIS source')
        rebuilt = bytes.fromhex(self.table['preamble_hex']) + b''.join(
            q.source_row(row) for row in self.table['records'])
        self.assertEqual(rebuilt, decode_csvz((q.CLIENT / q.SOURCE).read_bytes()))

    def test_native_section_dispatch_selects_actmis_loader(self):
        native = q.NativeRequirements(self.image)
        native.setreg('ESP', q.SP)
        native.setreg('EDI', q.RESOURCE)
        native.write(q.SP + 0xc, '<I', q.COUNT)
        native.vm.mem_write(q.SP + 0x18, b'ACTMIS\0')
        native.run(0x56434, q.BASE + 0x58780)
        self.assertEqual(native.getreg('ECX'), q.RESOURCE)
        self.assertEqual(native.read(native.getreg('ESP'), '<II'),
                         (q.BASE + 0x5647a, q.COUNT))
        self.assertEqual(self.image[0xbc1d0 + 19], 11)
        self.assertEqual(struct.unpack_from('<I', self.image, 0xbc188 + 11 * 4)[0],
                         q.BASE + 0xb9f8d)

    def test_all_169_source_rows_reach_native_key_and_quantity_reads(self):
        self.assertEqual(len(self.report['records']), 169)
        for row, record in zip(self.table['records'], self.report['records']):
            fields = [bytes.fromhex(f) for f in row['raw_fields_hex']]
            serial = int(fields[0])
            keys = [int(fields[i]) for i in (2, 4, 6, 8)]
            quantities = [int(fields[i]) for i in (3, 5, 7, 9)]
            count = sum(bool(k and n) for k, n in zip(keys, quantities))
            with self.subTest(serial=serial):
                self.assertEqual(record['serial'], serial)
                self.assertEqual(record['label_hex'], fields[1].hex())
                self.assertEqual(record['item_keys_u16'], keys)
                self.assertEqual(record['quantities_u8'], quantities)
                self.assertEqual(record['nonzero_pair_count'], count)
                # Every current row has one populated leading pair.
                self.assertEqual(count, 1)
                result = record['consumer']
                self.assertEqual(result['lookup_keys'], keys[:count])
                self.assertEqual(result['format_calls'], [{
                    'format_rva': 0x19288c, 'quantity': quantities[0],
                    'name_hex': q.LOOKUP_FIXTURE_NAME.hex()}])
                for rva, offset, size in ((0xb9fd2, 0, 4), (0xba000, 16, 1),
                                           (0xba01c, 8, 2), (0xba032, 4, 1)):
                    self.assertIn({'rva': rva, 'row_offset': (serial - 1) * 20 + offset,
                                   'size': size}, result['record_reads'])
                self.assertEqual(bytes.fromhex(result['text_hex']),
                                 fields[1] + b'\nlookup-fixture x ' + fields[3])

    def test_native_serial_is_key_not_source_ordinal(self):
        native = q.NativeRequirements(self.image)
        for serial in (169, 2, 1):
            row = self.table['records'][serial - 1]
            record = native.load_row(q.source_row(row))
            self.assertEqual(record['serial'], serial)
            self.assertEqual(native.read(q.ROWS + (serial - 1) * 20 + 8, '<H')[0],
                             int(bytes.fromhex(row['raw_fields_hex'][2])))
        self.assertEqual(native.read(q.RESOURCE + 0xb2c58, '<h'), (169,))
        # Category comes from bits 16..21, while serial comes from instance +8.
        regular = native.consume(169)
        self.assertEqual(native.consume(169, header=0xffd4ffff), regular)

    def test_native_loader_and_consumer_reject_out_of_range_keys(self):
        native = self.vm_with_rows()
        before = bytes(native.vm.mem_read(q.ROWS, q.COUNT * q.STRIDE))
        for serial in (0, -1, 170, 65535):
            self.assertIsNone(native.load_row(self.changed_row(serial)))
        for serial in (0, 170, 65535):
            self.assertEqual(native.consume(serial), {
                'text_hex': '', 'lookup_keys': [], 'format_calls': [], 'record_reads': []})
        self.assertEqual(bytes(native.vm.mem_read(q.ROWS, q.COUNT * q.STRIDE)), before)
        # Consumer sign-extends the resource high-water count.
        native.write(q.RESOURCE + 0xb2c58, '<H', 0x8000)
        self.assertEqual(native.consume(1)['record_reads'], [])

    def test_zero_slots_are_counted_but_not_compacted(self):
        native = q.NativeRequirements(self.image)
        record = native.load_row(self.changed_row(pairs=[(0, 0), (5156, 5), (5157, 7), (0, 0)]))
        self.assertEqual(record['nonzero_pair_count'], 2)
        result = native.consume(1, lookup_keys=[5156, 5157])
        self.assertEqual(result['lookup_keys'], [0, 5156])
        self.assertEqual([f['quantity'] for f in result['format_calls']], [5])
        self.assertEqual(bytes.fromhex(result['text_hex']),
                         bytes.fromhex(record['label_hex']) + b'\nlookup-fixture x 5')

    def test_parser_narrows_fields_before_counting_nonzero_pairs(self):
        native = q.NativeRequirements(self.image)
        record = native.load_row(self.changed_row(pairs=[
            (65537, 257), (65536, 1), (5156, 256), (-1, -1)]))
        self.assertEqual(record['item_keys_u16'], [1, 0, 5156, 65535])
        self.assertEqual(record['quantities_u8'], [1, 1, 0, 255])
        self.assertEqual(record['nonzero_pair_count'], 2)
        result = native.consume(1, lookup_keys=[1])
        self.assertEqual(result['lookup_keys'], [1, 0])
        self.assertEqual([f['quantity'] for f in result['format_calls']], [1])

    def test_missing_lookup_and_zero_pair_count_keep_prefix_only(self):
        native = q.NativeRequirements(self.image)
        record = native.load_row(q.source_row(self.table['records'][0]))
        result = native.consume(1)
        self.assertEqual(result['lookup_keys'], [5156])
        self.assertEqual(result['format_calls'], [])
        self.assertEqual(result['text_hex'], record['label_hex'])
        record = native.load_row(self.changed_row(pairs=[(0, 0)] * 4))
        result = native.consume(1)
        self.assertEqual(result['lookup_keys'], [])
        self.assertEqual(result['text_hex'], record['label_hex'])

    def test_consumer_does_not_mutate_source_or_input_instance(self):
        native = self.vm_with_rows()
        before = bytes(native.vm.mem_read(q.ROWS, 0x20000))
        native.consume(169, lookup_keys=[15508])
        self.assertEqual(bytes(native.vm.mem_read(q.ROWS, 0x20000)), before)
        self.assertEqual(bytes(native.vm.mem_read(q.INSTANCE, 20)),
                         struct.pack('<I4xH10x', 20 << 16, 169))
        self.assertEqual(bytes(native.vm.mem_read(q.BASE, len(self.image))), self.image)


if __name__ == '__main__':
    unittest.main()
