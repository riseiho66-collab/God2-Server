"""Small original-coordinate regression, including an already translated stop."""
import hashlib
from types import SimpleNamespace
import unittest

from tools.strike_lab import current_battle_bootstrap as boot
from tools.strike_lab.current_indoor_resources import NativeIndoorResources
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
from unicorn.x86_const import UC_X86_REG_EIP, UC_X86_REG_ESP


class CurrentBattleControlPositionTests(unittest.TestCase):
    def make_probe(self):
        image = boot.character_binding.IMAGE.read_bytes()
        self.assertEqual(hashlib.sha256(image).hexdigest(), boot.character_binding.IMAGE_SHA)
        vm = Uc(UC_ARCH_X86, UC_MODE_32)
        vm.mem_map(boot.BASE, (len(image) + 4095) & ~4095)
        vm.mem_write(boot.BASE, image)
        vm.mem_map(boot.SP - 4096, 8192)
        n = SimpleNamespace(vm=vm)
        n.run = lambda *args, **kwargs: NativeIndoorResources.run(n, *args, **kwargs)
        b = boot.NativeBattleBootstrap.__new__(boot.NativeBattleBootstrap)
        b.native = n
        return b, n

    def test_complete_original_copy(self):
        b, n = self.make_probe()
        b._prepare_control_positions()
        self.assertEqual(n.vm.reg_read(UC_X86_REG_EIP), boot.BASE + 0x11f4ef)
        self.assertEqual(n.vm.reg_read(UC_X86_REG_ESP), boot.SP)
        self.assertEqual(len(b.control_position_writes), 56)
        self.assertEqual(bytes(n.vm.mem_read(boot.CONTROL_POSITIONS, 224)),
                         bytes(n.vm.mem_read(0x571aa8, 224)))

    def test_pretranslated_next_instruction_does_not_write_stack(self):
        b, n = self.make_probe()
        n.vm.reg_write(UC_X86_REG_ESP, boot.SP)
        n.run(0x11f4ef, 0x11f4f4, instruction_limit=5)
        self.assertEqual(n.vm.reg_read(UC_X86_REG_ESP), boot.SP - 4)
        n.vm.mem_write(boot.SP - 16, b'\xa5' * 32)
        b._prepare_control_positions()
        self.assertEqual(bytes(n.vm.mem_read(boot.SP - 16, 32)), b'\xa5' * 32)
        self.assertEqual(n.vm.reg_read(UC_X86_REG_EIP), boot.BASE + 0x11f4ef)
        self.assertEqual(n.vm.reg_read(UC_X86_REG_ESP), boot.SP)


if __name__ == '__main__':
    unittest.main()
