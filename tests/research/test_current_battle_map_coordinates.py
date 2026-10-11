"""Native coordinate writer boundary probes, not captured world positions."""
import struct
import unittest
import test_current_battle_map_selector as selector
from tools.strike_lab import current_battle_bootstrap as boot
from unicorn.x86_const import UC_X86_REG_EIP, UC_X86_REG_ESP


class CurrentBattleMapCoordinateTests(unittest.TestCase):
    setUp = selector.CurrentBattleMapSelectorTests.setUp

    @classmethod
    def setUpClass(cls):
        selector.CurrentBattleMapSelectorTests.setUpClass()

    def bootstrap(self):
        b = selector.CurrentBattleMapSelectorTests.bootstrap(self)
        b.owner_map_sprite_completed_prefix = True
        self.vm.reg_write(UC_X86_REG_EIP, boot.BASE + 0xc3331)
        return b

    def test_coordinates_widths_and_retained_context(self):
        for x in (0, 1, 127, 16384, 32767):
            for y in (0, 1, 127, 16384, 32767):
                for flags in range(4):
                    b = self.bootstrap()
                    expected = bytearray(b.character_prepared)
                    scratch = bytes(self.vm.mem_read(b.character.sp + 0x44, 4))
                    stage = b.prepare_character_map_coordinates((y << 17) | (x << 2) | flags)
                    struct.pack_into('<II', expected, 8, x, y)
                    self.assertEqual(self.fixture.actor(), bytes(expected))
                    self.assertEqual(stage['writes'], [(0x68645, boot.CHARACTER_ROOT + 8, 4, x),
                                                       (0x68650, boot.CHARACTER_ROOT + 12, 4, y)])
                    self.assertEqual(b.character_written, set(range(boot.CHARACTER_ROOT + 8, boot.CHARACTER_ROOT + 16)))
                    self.assertEqual(bytes(self.vm.mem_read(b.character.sp + 0x44, 4)), scratch)
                    self.assertEqual(self.vm.reg_read(UC_X86_REG_EIP), boot.BASE + 0xc3331)
                    self.assertEqual(self.vm.reg_read(UC_X86_REG_ESP), boot.SP - 0xf0)

    def test_coordinate_preconditions_and_code_pin(self):
        b = self.bootstrap()
        for value in (None, True, -1, 2**32, b'1234'):
            with self.assertRaises(ValueError):
                b.prepare_character_map_coordinates(value)
        self.vm.reg_write(UC_X86_REG_ESP, boot.SP)
        with self.assertRaises(ValueError):
            b.prepare_character_map_coordinates(0)
        self.vm.reg_write(UC_X86_REG_ESP, boot.SP - 0xf0)
        original = self.fixture.actor()
        self.vm.mem_write(boot.BASE + 0x68636, b'\x90')
        with self.assertRaisesRegex(ValueError, 'executable bytes'):
            b.prepare_character_map_coordinates(0)
        self.assertEqual(self.fixture.actor(), original)

if __name__ == '__main__':
    unittest.main()
