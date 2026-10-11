"""Shared recovered envelope versus original queue and encoder, no sockets/UI."""
import struct
import subprocess
import unittest

import test_current_world_ready_builder as ready
from unicorn.x86_const import UC_X86_REG_ECX, UC_X86_REG_EIP, UC_X86_REG_ESP


def original_wire(logical):
    fixture = ready.CurrentWorldReadyBuilderTests()
    fixture.setUpClass()
    vm = fixture.vm()
    codec = ready.NET + 0x758
    vm.reg_write(UC_X86_REG_ECX, codec)
    vm.reg_write(UC_X86_REG_ESP, ready.SP)
    vm.mem_write(ready.SP, struct.pack('<I', ready.RETURN))
    vm.emu_start(ready.BASE + 0x10490, ready.RETURN, count=100000)
    fixture.assertEqual(vm.reg_read(UC_X86_REG_EIP), ready.RETURN)
    vm.mem_write(codec + 8, struct.pack('<I', 1))
    vm.mem_write(ready.NET + 0x2cb8, b'\x01')
    source = ready.STACK
    vm.mem_write(source, logical[1:] or b'\x00')
    vm.mem_write(ready.SP, struct.pack('<4I', ready.RETURN, logical[0], source, len(logical)-1))
    vm.reg_write(UC_X86_REG_ESP, ready.SP)
    vm.reg_write(UC_X86_REG_ECX, ready.NET)
    fixture.run_to(vm, 0x132e0, 0x1000)
    vm.mem_write(ready.SP, struct.pack('<I', ready.RETURN))
    vm.reg_write(UC_X86_REG_ESP, ready.SP)
    vm.reg_write(UC_X86_REG_ECX, ready.NET)
    vm.emu_start(ready.BASE + 0x13370, ready.BASE + 0x12501, count=500000)
    fixture.assertEqual(vm.reg_read(UC_X86_REG_EIP), ready.BASE + 0x12501)
    _, pointer, length, flags = struct.unpack('<4I', vm.mem_read(vm.reg_read(UC_X86_REG_ESP), 16))
    fixture.assertEqual(flags, 0)
    return bytes(vm.mem_read(pointer, length))


class CurrentWorldFrameTests(unittest.TestCase):
    binary = ready.ROOT / 'build/tests/Release/recovered-world-frame.exe'

    def test_permanent_six_byte_plaintext_oracle(self):
        import test_current_route_advertisement as routes
        wire = original_wire(bytes.fromhex('a60000'))
        self.assertEqual(wire.hex(), '0600a3a3fdd5')
        oracle = routes.CurrentRouteAdvertisementTests()
        ready.CurrentWorldReadyBuilderTests.setUpClass()
        oracle.image = ready.CurrentWorldReadyBuilderTests.image
        self.assertEqual(oracle.decode(oracle.vm(), wire), bytes.fromhex('0600a60000d8'))
        logical = subprocess.check_output([str(self.binary), '--decode', wire.hex()],
                                          text=True, timeout=5).strip()
        self.assertEqual(logical, 'a60000')

    def test_exact_original_queue_encoder_across_key_wrap_and_length_boundary(self):
        for length in (1, 2, 3, 7, 9, 17, 21, 141, 253, 254, 255, 256, 257, 511, 512, 1024, 2559, 2560):
            with self.subTest(length=length):
                logical = bytes((i*73 + length) & 255 for i in range(length))
                expected = original_wire(logical)
                actual = bytes.fromhex(subprocess.check_output(
                    [str(self.binary), '--encode', logical.hex()], text=True, timeout=5).strip())
                self.assertEqual(actual, expected)
                decoded = bytes.fromhex(subprocess.check_output(
                    [str(self.binary), '--decode', expected.hex()], text=True, timeout=5).strip())
                self.assertEqual(decoded, logical)


if __name__ == '__main__':
    unittest.main()
