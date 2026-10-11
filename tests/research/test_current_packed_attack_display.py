"""Pinned packed record display extraction, not original monster abilities."""
import struct
import unittest

from tests.research import test_current_battle_identity_cache as native


class PackedAttackDisplayTests(unittest.TestCase):
    setUp = native.BattleIdentityCacheTests.setUp
    put = native.BattleIdentityCacheTests.put
    run_native = native.BattleIdentityCacheTests.run_native

    def test_original_equipment_metadata_spread_source(self):
        from tools.strike_lab.current_item_metadata import NativeItemMetadata
        loader = NativeItemMetadata()
        for tag, selector, expected in (('WPN', 1, (5, 3)), ('EQU', 2, (0, 0)),
                                         ('TWP', 25, (6, 4)), ('TEQ', 26, (0, 0))):
            with self.subTest(section=tag):
                parsed = loader.item_row(tag, 0)
                fields = loader.sections[tag]['records'][0]['fields_hex']
                source = tuple(int(bytes.fromhex(fields[i])) for i in (26, 27))
                self.assertEqual(source, expected)
                self.assertEqual(parsed['selector'], selector)
                self.assertEqual(tuple(parsed['record'][0x11c:0x11e]), source)

    def test_original_formatter_spread_arithmetic(self):
        table = 0x24000000
        self.vm.mem_map(table, 0xb3000)
        self.vm.mem_map(native.OWNER + 0xcf000, 0x2000)
        self.put(native.OWNER + 0xcff70, table)
        # Zero message count takes the real missing-label path. No CRT executes.
        self.vm.mem_write(table + 0xb2c6c, b'\0\0')
        metadata, values, labels = native.INPUT + 0x100, native.INPUT + 0x300, native.INPUT + 0x400
        for index in (0, 1):
            for spread in (0, 3, 5, 255):
                for value in (0, 1, 1023):
                    with self.subTest(index=index, spread=spread, value=value):
                        self.vm.mem_write(metadata + 0x11c + index, bytes([spread]))
                        self.vm.mem_write(values + 2*index, struct.pack('<H', value))
                        self.vm.mem_write(labels + 2*index, struct.pack('<H', 520 + 2*index))
                        self.put(native.SP + 0x10, native.OWNER)
                        self.put(native.SP + 0x12c, metadata)
                        self.put(native.SP + 0x134, labels)
                        stop = 0xb4479 if spread else 0xb452a
                        self.run_native(0xb4409, [(0xb4409, 0xb452f)],
                            stop=native.BASE + stop, registers={'EBX': index, 'EDI': values})
                        sp = self.vm.reg_read(native.reg.UC_X86_REG_ESP)
                        if spread:
                            _, fmt, name, lo, hi = struct.unpack('<5I', self.vm.mem_read(sp, 20))
                            self.assertEqual((fmt, name, lo, hi),
                                             (native.BASE + 0x1926f4, 0, (value-spread) & 0xffffffff, value+spread))
                        else:
                            _, fmt, name, number = struct.unpack('<4I', self.vm.mem_read(sp, 16))
                            self.assertEqual((fmt, name, number), (native.BASE + 0x1926ec, 0, value))

    def test_original_record_type_dispatch(self):
        for category, destination in ((1, 0xb88e3), (25, 0xb88e3),
                                      (2, 0xb8bee), (26, 0xb8bee)):
            with self.subTest(category=category):
                self.run_native(0xb6424, [(0xb6424, 0xb6447)],
                    stop=native.BASE + destination,
                    registers={'EAX': (category << 16) | 0xc000abcd})

    def test_original_packed_values_and_message_labels(self):
        for entry, end, labels in ((0xb45b0, 0xb467c, (520, 522)),
                                   (0xb4690, 0xb475c, (521, 523))):
            for hi_a in range(4):
                for hi_b in range(4):
                    for low in (0, 255):
                        with self.subTest(entry=entry, hi_a=hi_a, hi_b=hi_b, low=low):
                            record = bytearray(20)
                            record[7], record[12] = low, 255-low
                            record[8:12] = bytes((13, 29, 71, 111))
                            struct.pack_into('<I', record, 16,
                                             (hi_a << 28) | (hi_b << 30) | 0x0f000000)
                            self.vm.mem_write(native.INPUT, bytes(record))
                            # Stop on entering B4200: formatting and its CRT calls
                            # are outside this qualification, not stubbed.
                            self.run_native(entry, [(entry, end)],
                                args=(native.INPUT, 0x12345678, native.OUTPUT),
                                stop=native.BASE + 0xb4200)
                            sp = self.vm.reg_read(native.reg.UC_X86_REG_ESP)
                            ret, source, arg2, values, names, output = struct.unpack(
                                '<6I', self.vm.mem_read(sp, 24))
                            self.assertEqual(ret, native.BASE + end)
                            self.assertEqual((source, arg2, output),
                                             (native.INPUT, 0x12345678, native.OUTPUT))
                            self.assertEqual(struct.unpack('<6H', self.vm.mem_read(names, 12)),
                                             (*labels, 74, 73, 72, 75))
                            self.assertEqual(struct.unpack('<6H', self.vm.mem_read(values, 12)),
                                             (low + 256*hi_a, 255-low + 256*hi_b,
                                              269, 285, 327, 367))
                            self.assertEqual(bytes(self.vm.mem_read(native.INPUT, 20)), bytes(record))


if __name__ == '__main__':
    unittest.main()
