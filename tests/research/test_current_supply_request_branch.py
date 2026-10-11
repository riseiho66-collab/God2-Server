"""Pinned native caller branches with synthetic definition flags, not live UI."""
import struct
import unittest
from tools.strike_lab.current_item_metadata import NativeItemMetadata
from tools.strike_lab import recover_companion_growth as growth

from tools.strike_lab.current_item_transition import (
    NativeItemTransition, UI, COMPANION, DEFINITIONS, SP, RETURN, LENGTH, QUEUE,
    UC_PROT_READ, UC_PROT_WRITE, UC_X86_REG_ESP, UC_X86_REG_ECX, UC_X86_REG_EBP)


class SupplyRequestBranchTests(unittest.TestCase):
    def produce(self, item=3107, flags=None, slot=0, target=0x1234, canary=0xa5, definition=None,
                world_identity_word=None):
        native = NativeItemTransition()  # Verifies image SHA256 before executing.
        vm = native.vm
        native.seed_slot(slot, item, 2)
        vm.mem_write(UI + 0x8688c, struct.pack('<I', COMPANION))
        vm.mem_write(COMPANION, struct.pack('<H', target))
        if world_identity_word is not None:
            # Staged native world identity writer -> original request reader in
            # one VM. The preceding S2C2A parser/UI bridge is not run here.
            vm.reg_write(UC_X86_REG_ESP, SP)
            vm.reg_write(UC_X86_REG_EBP, COMPANION)
            vm.reg_write(UC_X86_REG_ECX, world_identity_word)
            native._run(0x68629, 0x68636)
            self.assertEqual(bytes(vm.mem_read(COMPANION, 4)),
                             struct.pack('<I', world_identity_word & 0x3fff))
        vm.mem_write(UI + 0x232dea, b'\xff\xff')
        vm.mem_write(UI + 0x232e20, b'\xff\xff')
        if flags is not None or definition is not None:
            # Explicit branch fixture; not recovered real MED02 record bytes.
            record = COMPANION + 0x1000
            if definition is not None:
                vm.mem_write(record, definition)
            else:
                vm.mem_write(record + 0x11a, bytes([flags]))
            vm.mem_protect(DEFINITIONS, 0xe0000, UC_PROT_READ | UC_PROT_WRITE)
            vm.mem_write(DEFINITIONS + 0xb2d40 + item * 4, struct.pack('<I', record))
            vm.mem_protect(DEFINITIONS, 0xe0000, UC_PROT_READ)
        vm.mem_write(SP - 0x100, bytes([canary]) * 0x100)
        vm.mem_write(SP, struct.pack('<II', RETURN, item))
        vm.reg_write(UC_X86_REG_ESP, SP)
        vm.reg_write(UC_X86_REG_ECX, UI)
        native._run(0x963c0, RETURN - 0x400000)
        self.assertEqual(vm.reg_read(UC_X86_REG_ESP), SP + 8)
        length = struct.unpack('<I', vm.mem_read(LENGTH, 4))[0]
        self.assertIn(0x59a60, native.visits)
        record = bytes(vm.mem_read(QUEUE + 3, length - 3))
        return native, record

    def test_potion_target_branch_and_unwritten_tail(self):
        for flags in (None, 0, 1, 2, 8):
            for canary in (0, 0xa5, 0xff):
                with self.subTest(flags=flags, canary=canary):
                    native, record = self.produce(flags=flags, slot=29, canary=canary)
                    self.assertEqual(record, struct.pack('<BHHBB', 0x26, 0x1234, 3107, 29, canary))
                    self.assertNotIn(0x96350, native.visits)

    def test_flag_four_selects_28_and_sets_pending(self):
        for flags in (4, 5, 0xff):
            native, record = self.produce(flags=flags)
            self.assertEqual(record, struct.pack('<BHBB', 0x28, 3107, 0, 1))
            self.assertEqual(bytes(native.vm.mem_read(UI + 0x85608, 4)), struct.pack('<I', 1))
            self.assertNotIn(0x96350, native.visits)

    def test_special_id_ranges_still_select_25(self):
        for item in (5301, 5501):
            native, record = self.produce(item=item, flags=4)
            self.assertEqual(record, struct.pack('<BHBB', 0x25, item, 0, 0))
            self.assertIn(0x96350, native.visits)

    def test_all_real_med02_rows_loaded_then_routed(self):
        loader = NativeItemMetadata()
        rows = loader.sections['MED02']['records']
        self.assertEqual(len(rows), 100)
        for index, row in enumerate(rows):
            result = loader.item_row('MED02', index)
            fields = growth.fields(row)
            flags = [growth.decimal(f) if f else 0 for f in fields[14:26]]
            raw = result['record']
            self.assertEqual(raw[0x11a], sum((f & 1) << i for i, f in enumerate(flags[:8])))
            self.assertEqual(raw[0x11b] & 15, sum((f & 1) << i for i, f in enumerate(flags[8:])))
            self.assertEqual(result['selector'], 4)
            with self.subTest(item=result['key']):
                native, request = self.produce(item=result['key'], definition=raw)
                expected = (struct.pack('<BHBB', 0x28, result['key'], 0, 1) if raw[0x11a] & 4
                            else struct.pack('<BHHBB', 0x26, 0x1234, result['key'], 0, 0xa5))
                self.assertEqual(request, expected)
                self.assertNotIn(0x96350, native.visits)
            if result['key'] == 3107:
                self.assertEqual(result['source_line'], 6360)
                self.assertEqual(raw[0x11a:0x11c], bytes.fromhex('fb01'))
                self.assertEqual(request[0], 0x26)

    def test_native_actor_identity_writer_feeds_request_target(self):
        loader = NativeItemMetadata()
        definition = loader.item_row('MED02', 6)
        self.assertEqual(definition['key'], 3107)
        for identity in (1, 217, 0x1234, 0x3fff):
            for upper in (0, 0x4000, 0xffffc000):
                with self.subTest(identity=identity, upper=upper):
                    _, request = self.produce(definition=definition['record'],
                                              target=0xbeef, world_identity_word=identity | upper)
                    self.assertEqual(request, struct.pack('<BHHBB', 0x26, identity, 3107, 0, 0xa5))

    def test_current_med02_rows_preserve_nonzero_inventory_slots(self):
        loader = NativeItemMetadata()
        for source_index, item, slot in ((0, 3101, 5), (6, 3107, 12)):
            with self.subTest(item=item, slot=slot):
                definition = loader.item_row('MED02', source_index)
                self.assertEqual(definition['key'], item)
                _, request = self.produce(item=item, definition=definition['record'],
                                          slot=slot, target=0x1234)
                self.assertEqual(request, struct.pack('<BHHBB', 0x26, 0x1234,
                                                      item, slot, 0xa5))


if __name__ == '__main__':
    unittest.main()
