"""Pinned x86 selection slices in synthetic memory; no client/network/UI run."""
import hashlib
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'artifacts/tooling/crypto-oracle-python'))
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn import UC_PROT_READ, UC_PROT_EXEC
from unicorn.x86_const import (
    UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_ECX, UC_X86_REG_EBP,
    UC_X86_REG_ESI, UC_X86_REG_ESP, UC_X86_REG_EIP,
)

BASE, STACK, BODY, MAIN, NET_A, NET_B = (
    0x400000, 0x3000000, 0x3100000, 0x3200000, 0x3400000, 0x3410000,
)
SP = STACK + 0x2000


class CurrentExistingCharacterSelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = (ROOT / 'artifacts/capture_work/host-20260918-1430/output/'
                     'native-master-01-stable.bin').read_bytes()
        if hashlib.sha256(cls.image).hexdigest() != (
                '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'):
            raise AssertionError('Current mapped client changed')

    def vm(self):
        vm = Uc(UC_ARCH_X86, UC_MODE_32)
        vm.mem_map(BASE, (len(self.image) + 4095) & ~4095,
                   UC_PROT_READ | UC_PROT_EXEC)
        vm.mem_write(BASE, self.image)
        for address, size in ((STACK, 0x4000), (BODY, 0x2000),
                              (MAIN, 0x180000), (NET_A, 0x5000), (NET_B, 0x5000)):
            vm.mem_map(address, size)
        vm.mem_write(STACK, b'\xa5' * 0x4000)
        vm.reg_write(UC_X86_REG_ESP, SP)
        return vm

    def run_to(self, vm, entry, stop):
        vm.emu_start(BASE + entry, BASE + stop, timeout=1000000, count=10000)
        self.assertEqual(vm.reg_read(UC_X86_REG_EIP), BASE + stop)

    def test_dispatch_and_reply_lengths(self):
        for state, target in ((7, 0x5935), (0x14, 0x5626), (0x1a, 0x5a05)):
            self.assertEqual(struct.unpack_from('<I', self.image, 0x5bf8 + 4 * state)[0],
                             BASE + target)
        for opcode, length in ((1, 2), (2, 23), (7, 75), (0x18, 3), (0x1f, 125)):
            target = struct.unpack_from('<I', self.image, 0x1324 + 4 * opcode)[0] - BASE
            self.assertEqual(self.image[target:target + 6], b'\xb8' + struct.pack('<I', length) + b'\xc3')

    def test_connected_existing_selection_sends_only_1a_and_reaches_state8(self):
        # Execute state 14, real BD50, BA00, builder and result waiter. Only
        # queue/flush/timer services are synthetic, stopping before state setter.
        for unsolicited18 in (False, True):
            with self.subTest(unsolicited18=unsolicited18):
                vm = self.vm()
                vm.mem_write(MAIN + 0x15e84, struct.pack('<II', NET_A, NET_B))
                vm.mem_write(NET_A + 0x2cb8, b'\x01')
                vm.mem_write(NET_B + 0x2cb8, b'\x01')
                vm.mem_write(MAIN + 0x178ce0, struct.pack('<Ih', BODY + 0x800, 1))
                vm.mem_write(BODY + 0x800, b'\x02\x00' + bytes(72))
                vm.mem_write(BODY + 0x800 + 2 + 36 + 19, b'\xa3')
                vm.mem_write(MAIN + 0x178cf6, b'AccountA\x00')
                vm.mem_write(MAIN + 0x178d0e, b'BufferB\x00')
                vm.mem_write(BODY + 0x100, b'\x18\x01\xff')
                vm.mem_write(BODY + 0x200, b'\x02' + bytes(22))
                queue = [BODY + 0x100, BODY + 0x200] if unsolicited18 else [BODY + 0x200]
                sent, consumed = [], []

                def service(uc, address, size, context):
                    rva = address - BASE
                    if rva not in (0x132e0, 0x13370, 0x15b80, 0x13420, 0x13650, 0x13670):
                        return
                    sp = uc.reg_read(UC_X86_REG_ESP)
                    ret = struct.unpack('<I', uc.mem_read(sp, 4))[0]
                    result, pop = 0, 0
                    if rva == 0x132e0:
                        opcode, pointer, length = struct.unpack('<III', uc.mem_read(sp + 4, 12))
                        sent.append((opcode, bytes(uc.mem_read(pointer, length))))
                        pop = 12
                    elif rva in (0x13420, 0x13650, 0x13670):
                        self.assertTrue(queue, 'Waiter exhausted synthetic queue')
                        pop = 4
                        if rva == 0x13650:
                            result = queue[0]
                        elif rva == 0x13670:
                            consumed.append(queue.pop(0))
                    uc.reg_write(UC_X86_REG_EAX, result)
                    uc.reg_write(UC_X86_REG_ESP, sp + 4 + pop)
                    uc.reg_write(UC_X86_REG_EIP, ret)

                vm.hook_add(UC_HOOK_CODE, service)
                vm.reg_write(UC_X86_REG_EBP, MAIN)
                self.run_to(vm, 0x5626, 0xafb0)
                self.assertEqual(len(sent), 1)
                opcode, payload = sent[0]
                self.assertEqual((opcode, len(payload)), (0x1a, 37))
                self.assertEqual(payload[:16], b'AccountA' + bytes(8))
                self.assertEqual(payload[16:32], b'BufferB' + bytes(9))
                self.assertEqual(payload[32:34], b'\x03\x04')
                # The three unwritten tail bytes are not assigned wire defaults.
                sp = vm.reg_read(UC_X86_REG_ESP)
                self.assertEqual(struct.unpack('<I', vm.mem_read(sp + 4, 4))[0], 8)
                self.assertEqual(len(consumed), 2 if unsolicited18 else 1)
                self.assertFalse(queue)

    def test_selection_result_is_word_not_byte(self):
        for result in (0, 1, 256):
            with self.subTest(result=result):
                vm = self.vm()
                vm.mem_write(BODY, b'\x02' + struct.pack('<H', result) + bytes(20))
                vm.reg_write(UC_X86_REG_EAX, BODY)
                vm.reg_write(UC_X86_REG_EBX, NET_B)
                self.run_to(vm, 0x14d76, 0x14e9d if result == 0 else 0x14e18)

    def test_greeting_requires_opcode01_and_value_f6(self):
        for opcode, value, stop in ((1, 0xf6, 0x132d2), (1, 0xf5, 0x1327b),
                                    (0xf6, 0xf6, 0x1321e)):
            with self.subTest(opcode=opcode, value=value):
                vm = self.vm()
                vm.mem_write(BODY, bytes((opcode, value)))
                vm.mem_write(SP + 0x14, struct.pack('<I', 0xf6))
                vm.reg_write(UC_X86_REG_EAX, BODY)
                vm.reg_write(UC_X86_REG_EBX, NET_B)
                self.run_to(vm, 0x13215, stop)

    def test_preselection_1f_copies_exactly_124_bytes(self):
        vm = self.vm()
        vm.mem_write(BODY, b'\x1f' + bytes(range(124)))
        vm.mem_write(BODY + 0x800, b'\xa5' * 126)
        vm.mem_write(SP + 0x14, struct.pack('<I', BODY + 0x801))
        vm.reg_write(UC_X86_REG_EAX, BODY)
        vm.reg_write(UC_X86_REG_EBX, NET_B)
        self.run_to(vm, 0x14ab9, 0x14b2c)
        self.assertEqual(bytes(vm.mem_read(BODY + 0x800, 126)),
                         b'\xa5' + bytes(range(124)) + b'\xa5')

    def test_separate_18_reply_reads_first_of_two_payload_bytes(self):
        for token, ignored in ((0, 0xff), (1, 0), (0xfe, 0xa5)):
            with self.subTest(token=token, ignored=ignored):
                vm = self.vm()
                vm.mem_write(BODY, bytes((0x18, token, ignored)))
                vm.mem_write(BODY + 0x800, b'\xa5' * 3)
                vm.mem_write(SP + 0x0c, struct.pack('<I', BODY + 0x801))
                vm.reg_write(UC_X86_REG_EAX, BODY)
                vm.reg_write(UC_X86_REG_ESI, NET_B)
                self.run_to(vm, 0x15264, 0x152cb)
                self.assertEqual(bytes(vm.mem_read(BODY + 0x800, 3)),
                                 bytes((0xa5, token, 0xa5)))
        vm = self.vm()
        vm.mem_write(BODY, b'\x02' + bytes(22))
        vm.reg_write(UC_X86_REG_EAX, BODY)
        vm.reg_write(UC_X86_REG_ESI, NET_B)
        self.run_to(vm, 0x15264, 0x1526d)

    def test_state7_result_path_removes_record(self):
        for selected in (0, 1):
            with self.subTest(selected=selected):
                vm = self.vm()
                first, second = b'A' * 36, b'B' * 36
                vm.mem_write(BODY, b'\x02\x80' + first + second)
                vm.mem_write(MAIN + 0x178ce0, struct.pack('<Ih', BODY, selected))
                vm.mem_write(SP + 0x14, struct.pack('<I', MAIN + 0x178ce4))
                vm.reg_write(UC_X86_REG_EAX, 0)
                vm.reg_write(UC_X86_REG_EBP, MAIN)
                vm.reg_write(UC_X86_REG_ESI, MAIN + 0x178ce4)
                self.run_to(vm, 0xc24d, 0xc2bc)
                self.assertEqual(bytes(vm.mem_read(BODY, 2)), b'\x01\x80')
                self.assertEqual(bytes(vm.mem_read(BODY + 2, 36)), second if selected == 0 else first)
                self.assertEqual(bytes(vm.mem_read(MAIN + 0x178ce4, 2)), b'\x00\x00')


if __name__ == '__main__':
    unittest.main()
