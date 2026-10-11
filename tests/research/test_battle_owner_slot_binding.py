"""Original 3B store and battle reader in one VM; no gameplay authority."""
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.strike_lab import current_companion_instance as native
from tools.strike_lab.recover_combat_rules import IMAGE


class BattleOwnerSlotBindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = native.qualified_image(IMAGE)

    def test_original_packet_store_to_battle_reader_both_dispatches(self):
        n = native.NativeInstance(self.image)
        vm = n.vm
        battle = 0x20000000
        window_page = battle + 0xab3b000
        sentinel = native.BASE + 0x1000
        vm.mem_map(battle, 0x1000)
        vm.mem_map(window_page, 0x1000)
        self.assertEqual(n.STORE + 44 * 24, n.OWNER + 0x85a30)
        for dispatch in ('primary', 'secondary'):
            for word in (0, 1, 0x7fff, 0x8000, 0xffff):
                for same in (False, True):
                    with self.subTest(dispatch=dispatch, word=word, same=same):
                        record = struct.pack('<H', word) + bytes(range(2, 20))
                        stored = n.packet_store(44, record, dispatch=dispatch)
                        self.assertTrue(stored['copied'])
                        before = bytes(vm.mem_read(n.STORE - 16, 1232))
                        vm.mem_write(battle, b'\xa5' * 4096)
                        vm.mem_write(window_page, b'\xa5' * 4096)
                        n.put32(battle + 0x20, n.OWNER)
                        vm.mem_write(battle + 0xab3b1d2, struct.pack('<h', 1))
                        vm.mem_write(battle + 0xab3b8bc,
                                     struct.pack('<H', word if same else word ^ 1))
                        battle_before = bytes(vm.mem_read(battle, 4096))
                        window_before = bytes(vm.mem_read(window_page, 4096))
                        n.prepare()
                        n.put32(n.SP, sentinel)
                        n.reg('ECX', battle)
                        pcs, reads = [], []

                        def code(machine, address, size, context):
                            if address == sentinel or address == native.BASE + 0x11023c:
                                machine.emu_stop()
                                return
                            pc = address - native.BASE
                            self.assertTrue(0x110210 <= pc < 0x11023c or
                                            0x1102fa <= pc <= 0x1102ff, hex(pc))
                            pcs.append(pc)

                        def read(machine, access, address, size, value, context):
                            if not n.STACK <= address < n.STACK + 0x10000:
                                reads.append((n.reg('EIP') - native.BASE, address, size))

                        def write(machine, access, address, size, value, context):
                            self.assertTrue(n.SP - 32 <= address < address + size <= n.SP,
                                            (hex(address), size))

                        hooks = [vm.hook_add(native.uc.UC_HOOK_CODE, code),
                                 vm.hook_add(native.uc.UC_HOOK_MEM_READ, read),
                                 vm.hook_add(native.uc.UC_HOOK_MEM_WRITE, write)]
                        try:
                            vm.emu_start(native.BASE + 0x110210, 0, count=40,
                                         timeout=1000000)
                        finally:
                            for hook in hooks:
                                vm.hook_del(hook)
                        self.assertEqual(n.reg('EIP'), sentinel if same else
                                         native.BASE + 0x11023c)
                        self.assertEqual(reads, [
                            (0x110217, battle + 0xab3b1d2, 2),
                            (0x110225, battle + 0x20, 4),
                            (0x110228, n.STORE + 44 * 24, 2),
                            (0x11022f, battle + 0xab3b8bc, 2)])
                        if same:
                            self.assertEqual(n.reg('ESP'), n.SP + 4)
                            self.assertIn(0x1102ff, pcs)
                        else:
                            self.assertEqual(n.reg('EDI') & 0xffff, word)
                            self.assertNotIn(0x1102fa, pcs)
                        self.assertEqual(bytes(vm.mem_read(n.STORE - 16, 1232)), before)
                        self.assertEqual(bytes(vm.mem_read(battle, 4096)), battle_before)
                        self.assertEqual(bytes(vm.mem_read(window_page, 4096)), window_before)
        self.assertEqual(bytes(vm.mem_read(native.BASE, len(self.image))), self.image)


if __name__ == '__main__':
    unittest.main()
