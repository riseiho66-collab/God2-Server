"""Retained native selector initialization through its actual caller return."""
import struct
import unittest

import test_current_battle_selector_windows as windows
from tools.strike_lab import current_battle_bootstrap as boot
from unicorn.x86_const import UC_X86_REG_EIP, UC_X86_REG_ESP


class CurrentBattleSelectorPopulationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture = windows.CurrentBattleSelectorWindowTests
        fixture.setUpClass()
        check = fixture()
        check.test_original_constructor_owns_page_zero_and_three_list_headers()
        check.test_both_windows_return_and_original_pagination_reset_runs()
        check.test_native_bindings_and_nonzero_learned_skill_survive()
        cls.b, cls.n = fixture.b, fixture.n
        cls.prior_counts = dict(cls.b.counts)
        cls.calls = cls.b.continue_selector_population()

    def test_original_population_and_third_window_return_on_retained_stack(self):
        self.assertEqual(self.calls, {pc: 1 for pc in (
            0x11bf40, 0x11c045, 0x11c050, 0x11c1c9, 0x11bd70, 0x11bdc4,
            0x11b290, 0x11b568, 0x11c4f0, 0x11c515, 0x11bd65, 0x11bf94, 0x11bf99)})
        self.assertEqual(self.n.vm.reg_read(UC_X86_REG_EIP), boot.BASE + 0x1116a9)
        self.assertEqual(self.n.vm.reg_read(UC_X86_REG_ESP), boot.SP - 0x1c)
        self.assertEqual(self.b.counts[boot.ENTRY], 1)
        self.assertEqual(self.b.counts[0x11bb80], 1)
        self.assertTrue(self.b.selector_population_completed)
        for pc, extra in ((0x104ea0, 1), (0x106550, 5), (0x1057d0, 2),
                          (0x106c70, 1), (0x10c350, 1), (0x10c540, 5),
                          (0x10caa0, 20), (0x10d1d0, 1), (0x10d540, 1), (0x10d310, 1)):
            self.assertEqual(self.b.counts[pc] - self.prior_counts.get(pc, 0), extra, hex(pc))

    def test_third_window_and_original_three_bank_reset(self):
        n = self.n
        self.assertEqual(n.u32(boot.SELECTOR + 0x2e34), boot.BATTLE + 0xab3b1d8)
        self.assertEqual(n.u32(boot.SELECTOR + 0x32c8), boot.MOUSE)
        self.assertEqual(n.u32(boot.SELECTOR + 0x32cc), boot.RENDERER)
        self.assertEqual(bytes(n.vm.mem_read(boot.SELECTOR + 0x2d10, 2)), b'\x00\x01')
        expected = bytearray(0x54)
        struct.pack_into('<I', expected, 0x4c, 1)
        for offset in (0x2d14, 0x2d68, 0x2dbc):
            self.assertEqual(bytes(n.vm.mem_read(boot.SELECTOR + offset, 0x54)), expected)
        self.assertEqual(bytes(n.vm.mem_read(boot.SELECTOR + 0x3514, 2)), b'\xff\xff')

    def test_nonzero_ownership_is_retained_separately_from_empty_menu_cache(self):
        n, b = self.n, self.b
        self.assertEqual(n.vm.mem_read(boot.CHARACTER_ROOT + 0x168 + 0x1f0, 1)[0], 1)
        self.assertEqual(bytes(n.vm.mem_read(boot.CHARACTER_ROOT, len(b.character_prepared))), b.character_prepared)
        self.assertEqual(bytes(n.vm.mem_read(b.skill_catalog['destination'], len(b.skill_catalog['body']))),
                         b.skill_catalog['body'])
        self.assertEqual(n.u32(boot.SELECTOR + 0x10), 0)
        self.assertEqual(n.u32(boot.SELECTOR + 0x2d4), boot.CHARACTER_ROOT + 0x168)
        for address, before in b.selector_neighbors.items():
            self.assertEqual(bytes(n.vm.mem_read(address, len(before))), before)

    def test_native_name_copy_uses_original_writer_bytes(self):
        self.assertEqual(len(self.b.selector_label_copies), 1)
        copy = self.b.selector_label_copies[0]
        self.assertEqual(copy['source'], boot.CHARACTER_ROOT + 0x16b)
        self.assertEqual(copy['expected'], b'Probe100')
        self.assertEqual(copy['actual'], b'Probe100\0')

    def test_repeat_continuation_is_rejected(self):
        with self.assertRaises(ValueError):
            self.b.continue_selector_population()


if __name__ == '__main__':
    unittest.main()
