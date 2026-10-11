"""Current source -> original row parser -> original resource selector."""
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.strike_lab.current_item_metadata import NativeItemMetadata
from tools.strike_lab import recover_companion_growth as growth


class CurrentItemMetadataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = NativeItemMetadata()

    def test_all_rom_map_boundaries_match_first_source_range(self):
        n = self.native
        intervals = [tuple(map(growth.decimal, growth.fields(row)[:3])) for row in n.map_rows]
        probes = {0, 65535}
        for _, low, high in intervals:
            probes.update((low - 1, low, high, high + 1))
        for word in sorted(probes):
            expected = next((index for index, low, high in intervals if low <= word <= high), 0xffff)
            for upper in (0, 0xa5a50000):
                with self.subTest(word=word, upper=upper):
                    self.assertEqual(n.icon_map(upper | word), expected)

    def test_all_55_source_rows_execute_complete_native_item_parser(self):
        n = self.native
        count = 0
        for section in ('EGG', 'SPP'):
            for index, row in enumerate(n.sections[section]['records']):
                with self.subTest(section=section, index=index):
                    result = n.egg_row(section, index)
                    fields = growth.fields(row)
                    raw = result['record']
                    icon = growth.decimal(fields[3])
                    self.assertEqual(struct.unpack_from('<H', raw, 0x114)[0], icon)
                    self.assertEqual(raw[8:8 + len(fields[4]) + 1], fields[4] + b'\0')
                    self.assertEqual(struct.unpack_from('<II', raw),
                                     tuple(growth.decimal(f) for f in fields[5:7]))
                    self.assertEqual(result['group'], 20 if section == 'EGG' else 21)
                    self.assertEqual(result['action'], 0xffff)
                    flags = [growth.decimal(f) if f else 0 for f in fields[14:26]]
                    self.assertEqual(raw[0x11a], sum((f & 1) << i for i, f in enumerate(flags[:8])))
                    self.assertEqual(raw[0x11b] & 15, sum((f & 1) << i for i, f in enumerate(flags[8:])))
                    self.assertTrue(set(range(3, 26)) <= set(result['columns']))
                    self.assertEqual(n.call(0x59a60, result['key']), 0)
                    count += 1
        self.assertEqual(count, 55)
        self.assertEqual(bytes(n.vm.mem_read(n.BASE, len(n.image))), n.image)

    def test_invalid_arguments_do_not_mutate_table(self):
        n = self.native
        before = bytes(n.vm.mem_read(n.TABLE, 0x100000))
        for section, index in (('BAD', 0), ('EGG', -1), ('SPP', 28), ('EGG', True)):
            with self.assertRaises(ValueError):
                n.egg_row(section, index)
        for value in (-1, 1 << 32, True):
            with self.assertRaises(ValueError):
                n.icon_map(value)
        self.assertEqual(bytes(n.vm.mem_read(n.TABLE, 0x100000)), before)

    def test_retained_mis_record_uses_original_index_and_cannot_be_overwritten(self):
        n = NativeItemMetadata()
        rows = n.sections['MIS']['records']
        index = next(i for i, row in enumerate(rows) if growth.fields(row)[0] == b'4660')
        result = n.item_row('MIS', index, retain=True)
        values = growth.fields(rows[index])
        self.assertEqual((result['key'], result['selector'], result['source_line']), (4660, 24, 7636))
        self.assertEqual(result['record'][8:9 + len(values[4])], values[4] + b'\0')
        self.assertEqual(struct.unpack_from('<3H', result['record'], 0x114), (51123, 37, 0xffff))
        self.assertEqual(n.call(0x59a60, 4660), n.RECORD + 16)
        before = bytes(n.vm.mem_read(n.RECORD, 0x1ac))
        with self.assertRaisesRegex(ValueError, 'cannot be overwritten'):
            n.item_row('EGG', 0)
        self.assertEqual(bytes(n.vm.mem_read(n.RECORD, 0x1ac)), before)

    def test_attached_vm_rejects_changed_original_code_before_mapping(self):
        n = self.native
        address = n.BASE + 0x59420
        before = bytes(n.vm.mem_read(address, 1))
        n.vm.mem_write(address, bytes([before[0] ^ 1]))
        try:
            with self.assertRaisesRegex(ValueError, 'metadata code changed'):
                NativeItemMetadata(vm=n.vm)
        finally:
            n.vm.mem_write(address, before)

    def test_item_arguments_reject_before_mutating_record(self):
        n = self.native
        before = bytes(n.vm.mem_read(n.RECORD, 0x1ac))
        for section, index, retain in (('BAD', 0, False), ('MIS', True, False),
                                      ('MIS', -1, False), ('MIS', 0, 1)):
            with self.assertRaises(ValueError):
                n.item_row(section, index, retain=retain)
        self.assertEqual(bytes(n.vm.mem_read(n.RECORD, 0x1ac)), before)

    def test_runner_rejects_unqualified_code_and_nonstack_writes(self):
        n = self.native
        with self.assertRaisesRegex(AssertionError, 'Unexpected native metadata instruction'):
            n.run(0x59a27, 0x59a2b)
        n.reg('ESI', n.TABLE)
        n.reg('EAX', 1)
        n.reg('EDX', n.RECORD + 16)
        before = bytes(n.vm.mem_read(n.TABLE + 0xb2d44, 4))
        n.allowed = ()
        try:
            with self.assertRaisesRegex(AssertionError, 'Unexpected native row write'):
                n.run(0x59a20, 0x59a27)
        finally:
            n.allowed = None
            # Unicorn hooks can raise after a write has been committed.
            n.vm.mem_write(n.TABLE + 0xb2d44, before)
        self.assertFalse(n.active_code)


if __name__ == '__main__':
    unittest.main()
