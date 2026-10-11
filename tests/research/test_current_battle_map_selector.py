"""Lightweight original world-body map selector writer, not a full world packet."""
import struct
from types import SimpleNamespace
import unittest

import test_current_battle_character_binding as character
from tools.strike_lab import current_battle_bootstrap as boot
from unicorn.x86_const import UC_X86_REG_EIP, UC_X86_REG_ESP


class CurrentBattleMapSelectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        character.CurrentBattleCharacterBindingTests.setUpClass()

    def setUp(self):
        self.fixture = character.CurrentBattleCharacterBindingTests()
        self.fixture.setUp()
        self.vm = self.fixture.vm

    def bootstrap(self):
        b = boot.NativeBattleBootstrap.__new__(boot.NativeBattleBootstrap)
        b.native, b.character = SimpleNamespace(vm=self.vm), self.fixture.n
        b.character_prepared = self.fixture.actor()
        b.character_written = set()
        b.owner_map_clock_completed_prefix = True
        self.vm.reg_write(UC_X86_REG_EIP, boot.BASE + 0xc328b)
        self.vm.reg_write(UC_X86_REG_ESP, boot.SP - 0xf0)
        return b

    def test_original_packed_selector_widths_and_unrelated_bytes(self):
        for area in range(64):
            for scene in (0, 1, 15, 1023):
                for high in (0, 0xffff):
                    packed = (high << 16) | (scene << 6) | area
                    with self.subTest(packed=packed):
                        b = self.bootstrap()
                        before = bytearray(b.character_prepared)
                        scratch = bytes(self.vm.mem_read(b.character.sp + 0x40, 4))
                        stage = b.prepare_character_map_selector(packed)
                        struct.pack_into('<I', before, 0x14, scene)
                        struct.pack_into('<H', before, 0x18, area)
                        self.assertEqual(self.fixture.actor(), bytes(before))
                        self.assertEqual(stage['writes'], [
                            (0x6866b, boot.CHARACTER_ROOT + 0x18, 2, area),
                            (0x68672, boot.CHARACTER_ROOT + 0x14, 4, scene)])
                        self.assertEqual(stage['reads'], [(0x6865c, b.character.sp + 0x40, 4)])
                        self.assertEqual(b.character_written,
                                         set(range(boot.CHARACTER_ROOT + 0x14, boot.CHARACTER_ROOT + 0x1a)))
                        self.assertEqual(bytes(self.vm.mem_read(b.character.sp + 0x40, 4)), scratch)
                        self.assertEqual(self.vm.reg_read(UC_X86_REG_EIP), boot.BASE + 0xc328b)
                        self.assertEqual(self.vm.reg_read(UC_X86_REG_ESP), boot.SP - 0xf0)

    def test_invalid_input_pending_state_and_repetition_are_rejected(self):
        b = self.bootstrap()
        original = self.fixture.actor()
        for invalid in (None, True, -1, 2**32, b'\0' * 4):
            with self.assertRaises(ValueError):
                b.prepare_character_map_selector(invalid)
        self.assertEqual(self.fixture.actor(), original)
        self.vm.reg_write(UC_X86_REG_ESP, boot.SP)
        with self.assertRaises(ValueError):
            b.prepare_character_map_selector(2)
        self.vm.reg_write(UC_X86_REG_ESP, boot.SP - 0xf0)
        b.prepare_character_map_selector(2)
        with self.assertRaises(ValueError):
            b.prepare_character_map_selector(2)

    def test_changed_original_writer_code_fails_before_source_write(self):
        b = self.bootstrap()
        original = self.fixture.actor()
        self.vm.mem_write(boot.BASE + 0x6865c, b'\x90')
        with self.assertRaisesRegex(ValueError, 'executable bytes'):
            b.prepare_character_map_selector(2)
        self.assertEqual(self.fixture.actor(), original)
        self.assertFalse(getattr(b, 'map_selector_prepared', False))


if __name__ == '__main__':
    unittest.main()
