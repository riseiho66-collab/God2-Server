"""Native coordinates and retained C3B60 call, with real loaded map resources."""
import unittest
import test_current_battle_owner_map_sprite as sprite
from tools.strike_lab import current_battle_bootstrap as boot
from unicorn.x86_const import UC_X86_REG_EIP, UC_X86_REG_ESP


class CurrentBattleOwnerMapLabelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture = sprite.CurrentBattleOwnerMapSpriteTests
        fixture.setUpClass()
        check = fixture()
        check.test_original_control_returns_on_retained_stack()
        check.test_writes_are_accounted_and_battle_bank_untouched()
        cls.b, cls.n = b, n = fixture.b, fixture.n
        with cls().assertRaises(ValueError):
            b.continue_owner_map_label()
        cls.before = (n.vm.reg_read(UC_X86_REG_EIP), n.vm.reg_read(UC_X86_REG_ESP),
                      bytes(n.vm.mem_read(boot.SP - 0x2000, 0x2000)))
        cls.writer = b.prepare_character_map_coordinates((40 << 17) | (60 << 2))
        cls.after = (n.vm.reg_read(UC_X86_REG_EIP), n.vm.reg_read(UC_X86_REG_ESP),
                     bytes(n.vm.mem_read(boot.SP - 0x2000, 0x2000)))
        cls.owner_before = bytes(n.vm.mem_read(boot.OWNER, boot.OWNER_SIZE))
        cls.battle_before = bytes(n.vm.mem_read(boot.RENDERER, 0x291000))
        cls.calls = b.continue_owner_map_label()

    def test_coordinate_writer_and_native_label_return(self):
        self.assertEqual(self.before, self.after)
        self.assertEqual((self.n.u32(boot.CHARACTER_ROOT + 8), self.n.u32(boot.CHARACTER_ROOT + 12)), (60, 40))
        for pc in (0xc3b60, 0x1077c0, 0x1e500, 0x26700, 0xc3c14):
            self.assertEqual(self.calls[pc], 1, hex(pc))
        self.assertEqual(self.n.vm.reg_read(UC_X86_REG_EIP), boot.BASE + 0xc3348)
        self.assertEqual(self.n.vm.reg_read(UC_X86_REG_ESP), boot.SP - 0xf0)
        self.assertEqual(self.b.counts[boot.ENTRY], 1)

    def test_sources_and_write_footprint_preserved(self):
        expected = bytearray(self.owner_before)
        for _, at, size, value in self.b.owner_map_label_writes:
            if boot.OWNER <= at < boot.OWNER + boot.OWNER_SIZE:
                expected[at - boot.OWNER:at - boot.OWNER + size] = value.to_bytes(size, 'little')
        self.assertEqual(bytes(self.n.vm.mem_read(boot.OWNER, boot.OWNER_SIZE)), bytes(expected))
        self.assertEqual(bytes(self.n.vm.mem_read(boot.RENDERER, 0x291000)), self.battle_before)
        self.b.owner_map_metadata._verify_records(bound=True)
        with self.assertRaises(ValueError):
            self.b.prepare_character_map_coordinates(0)
        with self.assertRaises(ValueError):
            self.b.continue_owner_map_label()


if __name__ == '__main__':
    unittest.main()
