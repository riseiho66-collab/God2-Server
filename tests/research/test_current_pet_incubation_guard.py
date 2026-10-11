"""Original pmpetegg.cpp guard only, not hatching or an authoritative rule."""
from pathlib import Path
import struct
import unittest

from tools.strike_lab.current_item_transition import (
    NativeItemTransition, BASE, UI, DEFINITIONS, SP, RETURN,
    UC_HOOK_CODE, UC_PROT_READ, UC_PROT_WRITE,
    UC_X86_REG_ECX, UC_X86_REG_ESP, UC_X86_REG_EIP, UC_X86_REG_EAX,
)
from tools.strike_lab.recover_companions import GAME
from tools.strike_lab.recover_pet_incubation import extract


class PetIncubationGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        client = Path(__file__).resolve().parents[3] / 'God2'
        cls.records = extract((client / GAME).read_bytes())['entries']

    def setUp(self):
        self.native = NativeItemTransition()
        self.vm = self.native.vm
        # The guard only tests lookup presence; this is an explicitly staged
        # pointer index, NOT execution of the original gamedata loader.
        source = 0x3900000
        self.vm.mem_map(source, 0x10000, UC_PROT_READ | UC_PROT_WRITE)
        self.vm.mem_protect(DEFINITIONS, 0xe0000, UC_PROT_READ | UC_PROT_WRITE)
        for item in self.records:
            raw = bytes.fromhex(item['source']['raw_record_hex'])
            self.vm.mem_write(source, raw)
            self.vm.mem_write(DEFINITIONS + 0xb2d40 + 4 * item['source_key'],
                              struct.pack('<I', source))
            source += len(raw)
        self.vm.mem_protect(DEFINITIONS, 0xe0000, UC_PROT_READ)
        self.vm.mem_protect(0x3900000, 0x10000, UC_PROT_READ)

    def guard(self, slot, item):
        before = self.native._snapshot()
        self.vm.mem_write(SP, struct.pack('<III', RETURN, slot, item))
        self.vm.reg_write(UC_X86_REG_ESP, SP)
        self.vm.reg_write(UC_X86_REG_ECX, UI)
        hits = []

        def observe(vm, address, size, context):
            if address in (BASE + 0x2c70, RETURN):
                hits.append(address - BASE)
                vm.emu_stop()
        hook = self.vm.hook_add(UC_HOOK_CODE, observe)
        try:
            self.vm.emu_start(BASE + 0xd6c80, RETURN, count=1000)
        finally:
            self.vm.hook_del(hook)
        end = self.vm.reg_read(UC_X86_REG_EIP) - BASE
        self.assertIn(end, (0x2c70, RETURN - BASE))
        self.assertEqual(before, self.native._snapshot())
        if end == 0x2c70:
            sp = self.vm.reg_read(UC_X86_REG_ESP)
            return ('assert', struct.unpack('<I', self.vm.mem_read(sp + 12, 4))[0])
        self.assertEqual(self.vm.reg_read(UC_X86_REG_ESP), SP + 12)
        return ('return', self.vm.reg_read(UC_X86_REG_EAX))

    def test_every_source_identity_passes_presence_guard(self):
        for item in self.records:
            for slot in (0, 29, 45):
                with self.subTest(item=item['source_key'], slot=slot):
                    self.assertEqual(self.guard(slot, item['source_key']), ('return', 1))

    def test_invalid_slots_stop_before_native_assertion_handler(self):
        for slot in (30, 44, 46, 127, 128, 255):
            with self.subTest(slot=slot):
                self.assertEqual(self.guard(slot, 9301), ('assert', 0x57a))

    def test_outside_ranges_and_missing_catalog_entries_are_distinct(self):
        for identity in (0, 9300, 9501, 65535):
            self.assertEqual(self.guard(0, identity), ('assert', 0x586))
        for identity in (9326, 9400, 9500):
            self.assertEqual(self.guard(0, identity), ('assert', 0x58b))

    def test_native_argument_widths_not_wide_server_validation(self):
        self.assertEqual(self.guard(256, 9301 + 65536), ('return', 1))
        self.assertEqual(self.guard(301, 9401 + 65536), ('return', 1))

    def test_original_source_assertion_labels(self):
        strings = self.native.image[0x1951ec:0x195300]
        self.assertIn(b'pmpetegg.cpp', strings)
        self.assertIn(b'(itemno>=0 && itemno<=29) || itemno==EGG_EQUIP', strings)
        self.assertIn(b'(itemid>=9301 && itemid<=9400)||(itemid>=9401 && itemid<=9500)', strings)


if __name__ == '__main__':
    unittest.main()
