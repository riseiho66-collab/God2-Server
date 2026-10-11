"""Actual C3080 call on the retained battle stack and original world assets."""
import struct
import unittest

import test_current_battle_owner_bridge as bridge
from tools.strike_lab import current_battle_bootstrap as boot
from unicorn.x86_const import UC_X86_REG_EIP, UC_X86_REG_ESP


class CurrentBattleOwnerMapPanelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture = bridge.CurrentBattleOwnerBridgeTests
        fixture.setUpClass()
        check = fixture()
        check.test_original_descriptor_stores_and_panel_constructor()
        check.test_real_pending_call_reaches_mode_one_resource_boundary()
        check.test_visibility_is_written_by_original_surface_setter()
        cls.b, cls.n = fixture.b, fixture.n
        cls.owner_before = bytes(cls.n.vm.mem_read(boot.OWNER, boot.OWNER_SIZE))
        cls.battle_renderer_before = bytes(cls.n.vm.mem_read(boot.RENDERER, 0x291000))
        cls.calls = cls.b.continue_owner_map_panel()

    def test_real_map_window_and_text_calls_reach_clock_boundary(self):
        for pc, count in ((0xc3080, 1), (0x104ea0, 1), (0x104f50, 1),
                          (0x107710, 3), (0x146cf7, 3), (0xc3119, 1)):
            self.assertEqual(self.calls[pc], count, hex(pc))
        self.assertEqual(self.n.vm.reg_read(UC_X86_REG_EIP), boot.BASE + 0xc3640)
        self.assertEqual(self.n.vm.reg_read(UC_X86_REG_ESP), boot.SP - 0xf4)
        self.assertEqual(self.n.u32(boot.SP - 0xf4), boot.BASE + 0xc311e)
        self.assertEqual(self.b.counts[boot.ENTRY], 1)

    def test_world_window_uses_original_rect_and_independent_resource_bank(self):
        n = self.n
        window = int.from_bytes(n.vm.mem_read(boot.OWNER + 0x232da6, 2), 'little')
        self.assertEqual(window, 0)
        record = boot.OWNER_PANELS + 0x818 + window * 0x2a08
        self.assertEqual(bytes(n.vm.mem_read(record + 0x18, 16)), bytes(n.vm.mem_read(0x592fe0, 16)))
        handle = int.from_bytes(n.vm.mem_read(record + 4, 2), 'little')
        self.assertLess(handle, 0x1000)
        sprite = boot.OWNER_RENDERER + 0x10 + handle * 0x290
        self.assertEqual(n.u32(boot.OWNER_RENDERER + 0xc), boot.OWNER_BANK)
        self.assertEqual(bytes(n.vm.mem_read(boot.RENDERER, 0x291000)), self.battle_renderer_before)
        self.assertNotEqual(bytes(n.vm.mem_read(sprite, 1)), b'\0')
        for index, (asset, _, _) in boot.OWNER_UI_ASSETS.items():
            self.assertEqual(n.u32(n.owner_ui_records + index * 0x108), index)
            self.assertIn(asset, n.opens)

    def test_native_owner_writes_and_guarded_character_remain_exact(self):
        expected = bytearray(self.owner_before)
        for _, address, size, value in self.b.owner_map_panel_writes:
            if boot.OWNER <= address < boot.OWNER + boot.OWNER_SIZE:
                offset = address - boot.OWNER
                expected[offset:offset + size] = value.to_bytes(size, 'little')
        self.assertEqual(bytes(self.n.vm.mem_read(boot.OWNER, boot.OWNER_SIZE)), expected)
        self.assertEqual(bytes(self.n.vm.mem_read(boot.CHARACTER_ROOT, len(self.b.character_prepared))),
                         self.b.character_prepared)
        for at in (boot.OWNER - 16, boot.OWNER + boot.OWNER_SIZE):
            self.assertEqual(bytes(self.n.vm.mem_read(at, 16)), b'\xa5' * 16)
        with self.assertRaisesRegex(AssertionError, 'Unqualified character'):
            self.b._character_read(self.n.vm, 0, boot.CHARACTER_ROOT + 0x453c, 4, 0, None)
        with self.assertRaises(ValueError):
            self.b.continue_owner_map_panel()


if __name__ == '__main__':
    unittest.main()
