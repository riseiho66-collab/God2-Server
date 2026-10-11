"""Actual selector construction and continued same-stack window initialization."""
import struct
import unittest

import test_current_battle_bootstrap as baseline
from tools.strike_lab import current_battle_bootstrap as boot
from unicorn.x86_const import UC_X86_REG_EIP, UC_X86_REG_ESP


class CurrentBattleSelectorWindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture = baseline.CurrentBattleBootstrapTests
        fixture.setUpClass()
        cls.b, cls.n = fixture.boot, fixture.n
        # Check the retained old boundary before continuing that exact stack.
        check = fixture()
        check.test_one_normal_entry_through_all_real_calls_and_next_boundary()
        check.test_native_character_writer_feeds_continuous_selector_source_reads()
        check.test_native_loaded_catalog_and_learned_pointer_retained_in_same_vm()
        cls.before = bytes(cls.n.vm.mem_read(boot.SELECTOR, 0x351c))
        cls.prior_counts = dict(cls.b.counts)
        cls.calls = cls.b.continue_selector_windows()

    def test_original_constructor_owns_page_zero_and_three_list_headers(self):
        data = self.b.selector_constructed
        self.assertEqual(struct.unpack_from('<I', data, 0)[0], 0x5715e4)
        self.assertEqual(data[4:0x2d10], bytes(0x2d0c))
        for offset in (0x2e38, 0x3080, 0x32c8):
            self.assertEqual(struct.unpack_from('<I', data, offset)[0], 0)
            self.assertEqual(data[offset + 0x210:offset + 0x224], bytes(0x14))
            self.assertEqual(struct.unpack_from('<I', data, offset + 0x23c)[0], 0xffff)

    def test_both_windows_return_and_original_pagination_reset_runs(self):
        self.assertEqual(self.calls, {rva: 1 for rva in (
            0x11a9d0, 0x11ac91, 0x11adb0, 0x11b09e, 0x11bc84, 0x11c4b0, 0x11c4ea)})
        self.assertEqual(self.n.vm.reg_read(UC_X86_REG_EIP), boot.BASE + 0x11bc95)
        self.assertEqual(self.n.vm.reg_read(UC_X86_REG_ESP), boot.SP - 0x54)
        self.assertEqual(self.n.u32(boot.SELECTOR + 8), 0)
        self.assertEqual(self.n.u32(boot.SELECTOR + 12), 1)
        self.assertEqual(self.b.counts[0x1112c0], 1)
        self.assertTrue(self.b.selector_windows_completed)
        for pc, extra in ((0x104ea0, 2), (0x106550, 21), (0x1057d0, 4),
                          (0x106c70, 2), (0x10c350, 2), (0x10c540, 21),
                          (0x10caa0, 21), (0x10d1d0, 2), (0x10d540, 2), (0x10d310, 2)):
            self.assertEqual(self.b.counts[pc] - self.prior_counts.get(pc, 0), extra, hex(pc))

    def test_native_bindings_and_nonzero_learned_skill_survive(self):
        n, b = self.n, self.b
        for offset, value in ((0x2e10, boot.RENDERER), (0x2e20, boot.MOUSE),
                              (0x2e24, boot.PANELS), (0x2e28, boot.OWNER),
                              (0x2e2c, boot.BATTLE + 0xab3b1d4),
                              (0x2e30, boot.BATTLE + 0xab3b1d6)):
            self.assertEqual(n.u32(boot.SELECTOR + offset), value, hex(offset))
        self.assertEqual(bytes(n.vm.mem_read(boot.CHARACTER_ROOT, len(b.character_prepared))), b.character_prepared)
        self.assertEqual(bytes(n.vm.mem_read(b.skill_catalog['destination'], len(b.skill_catalog['body']))),
                         b.skill_catalog['body'])
        self.assertEqual(n.vm.mem_read(boot.CHARACTER_ROOT + 0x168 + 0x1f0, 1)[0], 1)
        for offset in (0x2e38, 0x3080):
            self.assertEqual(n.u32(boot.SELECTOR + offset), boot.MOUSE)
            self.assertEqual(n.u32(boot.SELECTOR + offset + 4), boot.RENDERER)
        for address, before in b.selector_neighbors.items():
            self.assertEqual(bytes(n.vm.mem_read(address, 16)), before)

    def test_reentry_is_rejected(self):
        with self.assertRaises(ValueError):
            self.b.continue_selector_windows()


if __name__ == '__main__':
    unittest.main()
