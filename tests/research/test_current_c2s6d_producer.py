"""Execute the pinned current-client 6D producer up to its queue boundary."""
import hashlib
from pathlib import Path
import struct
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
IMAGE = ROOT / 'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin'
IMAGE_SHA256 = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
BASE = 0x400000
OWNER = 0x3000000
STACK = 0x3100000


class CurrentC2S6DProducerTests(unittest.TestCase):
    def test_native_control_queues_6d_with_one_zero_payload_byte(self):
        raw = IMAGE.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), IMAGE_SHA256)
        # Dispatch 961A0(input=6D) selects the 96252 branch, which calls
        # 157D0. That function submits opcode and one zero byte to 132E0.
        selector = raw[0x9628c + 0x6d - 0x1f]
        target = struct.unpack_from('<I', raw, 0x96274 + 4 * selector)[0]
        self.assertEqual(target, BASE + 0x96252)
        for at, expected in ((0x9625a, 0x157d0), (0x157e2, 0x132e0)):
            self.assertEqual(raw[at], 0xe8)
            self.assertEqual(at + 5 + struct.unpack_from('<i', raw, at + 1)[0], expected)

        sys.path.insert(0, str(ROOT / 'artifacts/tooling/crypto-oracle-python'))
        import unicorn as uc
        from unicorn import x86_const as x86
        vm = uc.Uc(uc.UC_ARCH_X86, uc.UC_MODE_32)
        vm.mem_map(BASE, (len(raw) + 4095) & ~4095, uc.UC_PROT_READ | uc.UC_PROT_EXEC)
        vm.mem_write(BASE, raw)
        vm.mem_map(OWNER, 0x90000, uc.UC_PROT_READ | uc.UC_PROT_WRITE)
        vm.mem_map(STACK, 4096, uc.UC_PROT_READ | uc.UC_PROT_WRITE)
        vm.mem_write(OWNER + 0x86874, struct.pack('<I', OWNER))
        sp = STACK + 0x800
        vm.mem_write(sp, struct.pack('<III', BASE + 0x9626f, 0x6d, 1))
        vm.reg_write(x86.UC_X86_REG_ESP, sp)
        vm.reg_write(x86.UC_X86_REG_ECX, OWNER)
        visited = []

        def stop_before_queue(machine, address, size, _):
            rva = address - BASE
            self.assertTrue((0x961a0 <= rva < 0x96260) or
                            (0x157d0 <= rva < 0x157ed) or rva == 0x132e0)
            visited.append(rva)
            if rva == 0x132e0:
                machine.emu_stop()

        vm.hook_add(uc.UC_HOOK_CODE, stop_before_queue)
        vm.emu_start(BASE + 0x961a0, 0, count=100, timeout=100000)
        self.assertEqual(vm.reg_read(x86.UC_X86_REG_EIP), BASE + 0x132e0)
        self.assertIn(0x96252, visited)
        self.assertIn(0x157d0, visited)
        ret, opcode, pointer, size = struct.unpack(
            '<IIII', vm.mem_read(vm.reg_read(x86.UC_X86_REG_ESP), 16))
        self.assertEqual(ret, BASE + 0x157e7)
        self.assertEqual((opcode, size, bytes(vm.mem_read(pointer, size))), (0x6d, 1, b'\0'))


if __name__ == '__main__':
    unittest.main()
