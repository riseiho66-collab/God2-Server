"""Pinned18 reply consumer; synthetic execution, not live-world acceptance."""
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'artifacts/tooling/crypto-oracle-python'))
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_ESI, UC_X86_REG_ESP, UC_X86_REG_EIP
from tools.strike_lab.current_offline_entry_bridge import pinned_image


class PostCreateAckTests(unittest.TestCase):
    def test_reply_length_is_three_not_request_length_two(self):
        im = pinned_image()
        target = struct.unpack_from('<I', im, 0x1324 + 0x18 * 4)[0]
        self.assertEqual(target, 0x4012dc)
        self.assertEqual(im[0x12dc:0x12e2], bytes.fromhex('b803000000c3'))
        self.assertEqual(im[0xbe87:0xbe89], b'\x6a\x01')
        self.assertEqual(im[0xbe98:0xbe9a], b'\x6a\x18')
        self.assertEqual(0xbedb + 5 + struct.unpack_from('<i', im, 0xbedc)[0], 0x15210)

    def test_ack_copies_slot_consumes_once_and_returns_zero(self):
        im = pinned_image()
        for token in (0, 1, 7, 255):
            for tail in (0, 255):
                with self.subTest(token=token, tail=tail):
                    vm = Uc(UC_ARCH_X86, UC_MODE_32)
                    vm.mem_map(0x400000, 0x16000)
                    vm.mem_write(0x400000, im[:0x16000])
                    vm.mem_map(0x3000000, 0x3000)
                    stack, packet, output, sentinel = 0x3000800, 0x3001000, 0x3001100, 0x3002000
                    # Consumer entry slice has saved ESI/EDI above return and args.
                    vm.mem_write(stack, struct.pack('<5I', 0, 0, sentinel, output, output + 16))
                    vm.mem_write(packet, bytes((0x18, token, tail)))
                    vm.mem_write(output, b'\xcc' * 32)
                    vm.reg_write(UC_X86_REG_EAX, packet)
                    vm.reg_write(UC_X86_REG_ESI, 0x3200000)
                    vm.reg_write(UC_X86_REG_ESP, stack)
                    calls = []

                    def consume(uc, address, size, _):
                        if address == 0x413670:
                            sp = uc.reg_read(UC_X86_REG_ESP)
                            ret, queue = struct.unpack('<2I', bytes(uc.mem_read(sp, 8)))
                            calls.append((uc.reg_read(UC_X86_REG_ECX), queue))
                            uc.reg_write(UC_X86_REG_ESP, sp + 8)
                            uc.reg_write(UC_X86_REG_EIP, ret)

                    vm.hook_add(UC_HOOK_CODE, consume)
                    vm.emu_start(0x415264, sentinel, timeout=100000, count=40)
                    self.assertEqual(vm.reg_read(UC_X86_REG_EIP), sentinel)
                    self.assertEqual(vm.reg_read(UC_X86_REG_EAX), 0)
                    self.assertEqual(vm.reg_read(UC_X86_REG_ESP), stack + 20)
                    self.assertEqual(calls, [(0x3200000, 0)])
                    self.assertEqual(bytes(vm.mem_read(output, 32)), bytes((token,)) + b'\xcc' * 31)


if __name__ == '__main__':
    unittest.main()
