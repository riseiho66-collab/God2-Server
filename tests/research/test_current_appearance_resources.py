"""Actual CSVZ/native record and lookup regression; no live client involved."""
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.strike_lab.current_appearance_resources import (
    AppearanceResources, BASE, SP, TABLE, RECORDS, INPUT, INDEX, BANK,
    UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_EBP, UC_X86_REG_ECX,
    UC_X86_REG_EDI, UC_X86_REG_ESI, UC_X86_REG_ESP,
)


class AppearanceResourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.oracle = AppearanceResources()

    def test_all_918_original_loader_records_match_source_fields(self):
        a = self.oracle
        self.assertEqual(len(a.rows), 918)
        for ordinal, row in enumerate(a.rows):
            ptr = RECORDS+ordinal*44
            record = a.record(ptr)
            self.assertEqual(record[:30].split(b'\0')[0], row[3].lower().encode('ascii'))
            self.assertEqual(record[30:32], b'\xff\xff')
            self.assertEqual(record[32:42].split(b'\0')[0], (row[0]+row[1]).lower().encode('ascii'))
            self.assertEqual(record[42], int(row[5]))
            # Original native hash/comparison lookup, including collision chains.
            a.vm.mem_write(INPUT, (row[0]+row[1]).lower().encode('ascii')+b'\0')
            self.assertEqual(a.call(0x15a662, INPUT, INPUT+0x1000, this=INDEX), 1)
            self.assertEqual(a.u32(INPUT+0x1000), ptr)

    def test_real_binary_head_records_both_supply_two(self):
        a = self.oracle
        first = a.lookup(0, 2, 0, 0, 0)
        second = a.lookup(1, 2, 0, 0, 0)
        self.assertNotEqual(first, second)
        for ptr, key in ((first, b'r1h000'), (second, b'r2h000')):
            record = a.record(ptr)
            self.assertEqual(record[:30].split(b'\0')[0], b'r01w800.romz')
            self.assertEqual(record[32:42].split(b'\0')[0], key)
            self.assertEqual(record[42], 2)
        for binary in (0, 1):
            for extra in range(32):
                self.assertEqual(a.call(0x52420, binary, 2, 0, 0, 0, extra) & 255, 2+extra)

    def test_original_preview_and_world_component_one_resolve_same_real_record(self):
        a, v = self.oracle, self.oracle.vm
        for binary in (0, 1):
            for first in range(7):
                for second in range(7):
                    block = bytes((binary, first << 5, binary, second << 5,
                                   binary, 0, 0x80 | binary, 0))
                    # Preview component 2 has not yet received its binary nibble.
                    preview = bytearray(block)
                    preview[4] = 0
                    v.mem_write(SP+0x10, bytes(preview))
                    v.reg_write(UC_X86_REG_ESP, SP-4)
                    a.put32(SP-4, 0)  # Native 9A7F's action argument.
                    v.reg_write(UC_X86_REG_EDI, TABLE-0xd8c)
                    v.reg_write(UC_X86_REG_ESI, SP+0x12)
                    a.events.clear()
                    a.run(0x9a90, 0x9b00)
                    preview_record = v.reg_read(UC_X86_REG_EAX)
                    preview_keys = list(a.events)
                    self.assertEqual(v.reg_read(UC_X86_REG_ESP), SP)
                    self.assertEqual(preview_keys, [(0, 2, 0, 0, 0), (binary, 1, 0, 2, 0)])

                    # Execute both real 63780 calls against the native-loaded
                    # Drv table. EBP is the world consumer's selector input.
                    v.mem_write(INPUT+0x4000, block)
                    v.reg_write(UC_X86_REG_ESP, SP)
                    v.reg_write(UC_X86_REG_EBP, 0)
                    v.reg_write(UC_X86_REG_EBX, 1)
                    v.reg_write(UC_X86_REG_EDI, INPUT+0x4000)
                    v.reg_write(UC_X86_REG_ESI, BANK)
                    a.events.clear()
                    a.run(0x61366, 0x61399)
                    derived = v.reg_read(UC_X86_REG_EAX) & 255
                    self.assertEqual(derived, 2)
                    self.assertEqual(a.events, [(binary, 2, 0, 0, 0)])
                    self.assertEqual(v.reg_read(UC_X86_REG_ESP), SP)

                    a.run(0x61399, 0x613f1)
                    # 63DE0 args: bank, counter pointer, then five lookup bytes.
                    key = tuple(n & 255 for n in struct.unpack('<5I', v.mem_read(SP-20, 20)))
                    self.assertEqual(key, preview_keys[1])
                    world_record = a.lookup(*key)
                    self.assertEqual(world_record, preview_record)
                    self.assertEqual(a.record(world_record)[30:32], b'\xff\xff')

    def test_native_driver_rows_and_action_lookup_match_current_source(self):
        a = self.oracle
        self.assertEqual(a.driver_count, 92)
        for ordinal, row in enumerate(a.driver_rows):
            record = bytes(a.vm.mem_read(BANK+0x121f8+ordinal*32, 32))
            self.assertEqual(record[:16].split(b'\0')[0], row[1].encode('ascii'))
            self.assertEqual(struct.unpack_from('<H', record, 16)[0], 65535)
            for field, offset in ((2, 18), (3, 30), (4, 22),
                                  (5, 24), (6, 26), (7, 28)):
                self.assertEqual(struct.unpack_from('<H', record, offset)[0], int(row[field]))
            self.assertEqual(a.driver_action(ordinal), int(row[2]))
        self.assertEqual(a.driver_action(0), 0)
        self.assertEqual({a.driver_action(i) for i in range(1, 92)}, {2})
        before = bytes(a.vm.mem_read(BANK+0x121f6, 2+92*32+2))
        for selector in (92, 93, 255, 32767):
            self.assertEqual(a.driver_action(selector), 0)
        for selector in (-1, 32768, 65535, 65536):
            with self.assertRaises(ValueError):
                a.driver_action(selector)
        self.assertEqual(bytes(a.vm.mem_read(BANK+0x121f6, len(before))), before)

    def test_missing_lookup_is_null_and_does_not_fabricate_cached_resource(self):
        a = self.oracle
        before = bytes(a.vm.mem_read(RECORDS, 918*44))
        self.assertEqual(a.lookup(15, 2, 0, 31, 0), 0)
        self.assertEqual(a.call(0x52420, 15, 2, 0, 31, 0, 0) & 255, 0)
        self.assertEqual(a.call(0x526c0, 1, 1, 0, 2, 0) & 65535, 65535)
        self.assertEqual(bytes(a.vm.mem_read(RECORDS, 918*44)), before)
        for key in ((0, 4, 0, 0, 0), (0, 2, 0, 0, 3), (-1, 2, 0, 0, 0)):
            with self.assertRaises(ValueError):
                a.lookup(*key)


if __name__ == '__main__':
    unittest.main()
