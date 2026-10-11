"""Pinned world-ready tail and builders, with no assets, UI, or transport.

Execute original code from 654F7 through the flush boundary at 65538, including
the receive-buffer reset, 961A0's two selected cases, both builders, and queue
copying. This does not execute the intervening world/resource initializers or
the 2A parser, and does not claim original-client world entry.
"""
import hashlib
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "artifacts/tooling/crypto-oracle-python"))
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn import UC_PROT_READ, UC_PROT_WRITE, UC_PROT_EXEC
from unicorn.x86_const import (
    UC_X86_REG_EAX, UC_X86_REG_EBP, UC_X86_REG_ECX,
    UC_X86_REG_EIP, UC_X86_REG_ESP,
)

BASE = 0x400000
STACK, NET, WORLD = 0x3000000, 0x3100000, 0x4000000
SP, RETURN = STACK + 0x2000, BASE + 0x1000
IMAGE_SHA = "149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763"
G_SLOT = WORLD + 0xA7E05E0
WORLD_OUTPUT = WORLD + 0x1539683C
UI = WORLD + 0xA7F2F6C
UI_G_SLOT = UI + 0x86874
CONFIG = 0x59DFD8
LOG_POINTER = 0x5B4DA8


class CurrentWorldReadyBuilderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = (ROOT / "artifacts/capture_work/host-20260918-1430/output/"
                     "native-master-01-stable.bin").read_bytes()
        if hashlib.sha256(cls.image).hexdigest() != IMAGE_SHA:
            raise AssertionError("Current mapped client image identity changed")

    def vm(self, config=(4, 2)):
        vm = Uc(UC_ARCH_X86, UC_MODE_32)
        vm.mem_map(BASE, (len(self.image) + 4095) & ~4095,
                   UC_PROT_READ | UC_PROT_EXEC)
        vm.mem_write(BASE, self.image)
        for address in (CONFIG, LOG_POINTER):
            vm.mem_protect(address & ~4095, 4096, UC_PROT_READ | UC_PROT_WRITE)
        vm.mem_write(CONFIG, struct.pack("<HH", *config))
        vm.mem_write(LOG_POINTER, bytes(4))
        for address, size in ((STACK, 0x4000), (NET, 0x5000)):
            vm.mem_map(address, size)
        for page in {address & ~4095 for address in (G_SLOT, WORLD_OUTPUT, UI_G_SLOT)}:
            vm.mem_map(page, 4096)
        vm.mem_write(STACK, b"\xa5" * 0x4000)
        vm.mem_write(G_SLOT, struct.pack("<I", NET))
        vm.mem_write(UI_G_SLOT, struct.pack("<I", NET))
        vm.reg_write(UC_X86_REG_ESP, SP)
        vm.reg_write(UC_X86_REG_EBP, WORLD)
        vm.reg_write(UC_X86_REG_ECX, NET)
        return vm

    def run_to(self, vm, entry, stop):
        vm.emu_start(BASE + entry, BASE + stop, timeout=100000, count=4096)
        self.assertEqual(vm.reg_read(UC_X86_REG_EIP), BASE + stop)

    def queued(self, vm):
        size = struct.unpack("<I", vm.mem_read(NET + 0x36C4, 4))[0]
        self.assertLessEqual(size, 0xA00)
        return bytes(vm.mem_read(NET + 0x36C8, size))

    def test_original_1c_builder_masks_low16_and_uses_exact_config_pair(self):
        for value in (0, 1, 0x3FFF, 0x4000, 0xFFFF, 0x1234ABCD, 0xFFFFFFFF):
            for config in ((4, 2), (4, 1), (3, 2), (0, 0), (0xFFFF, 2)):
                with self.subTest(value=value, config=config):
                    vm = self.vm(config)
                    vm.mem_write(SP, struct.pack("<II", RETURN, value))
                    self.run_to(vm, 0x157F0, 0x1000)
                    flag = int(config == (4, 2))
                    self.assertEqual(self.queued(vm), b"\x1c" + struct.pack(
                        "<I", (value & 0xFFFF) | (flag << 16)))
                    self.assertEqual(vm.reg_read(UC_X86_REG_ESP), SP + 8)
                    self.assertEqual(vm.reg_read(UC_X86_REG_EAX), 0)

    def test_original_tail_orders_1f_23_1c_without_receive_wait(self):
        for local_id in (0, 1, 0x3FFF):
            for config in ((4, 2), (4, 3)):
                with self.subTest(local_id=local_id, config=config):
                    vm = self.vm(config)
                    vm.mem_write(WORLD_OUTPUT, struct.pack("<I", local_id))
                    calls = []

                    def trace(machine, address, size, _):
                        rva = address - BASE
                        if rva in (0x13670, 0x157D0, 0x157F0, 0x132E0):
                            calls.append(rva)
                        if rva in (0x13420, 0x13650, 0x13370):
                            raise AssertionError(f"Unexpected receive/flush at {rva:X}")

                    vm.hook_add(UC_HOOK_CODE, trace)
                    self.run_to(vm, 0x654F7, 0x65538)
                    expected = (b"\x1f\x00\x23\x00\x1c" + struct.pack(
                        "<I", local_id | (int(config == (4, 2)) << 16)))
                    self.assertEqual(self.queued(vm), expected)
                    self.assertEqual(calls, [0x13670, 0x157D0, 0x132E0,
                                             0x157D0, 0x132E0, 0x157F0, 0x132E0])
                    self.assertEqual(vm.reg_read(UC_X86_REG_ECX), NET)
                    self.assertEqual(vm.reg_read(UC_X86_REG_ESP), SP)

    def test_original_flush_encodes_nine_logical_bytes_in_one_frame(self):
        for local_id in (1,0x1234,0x3fff):
            wire=current_world_ready_wire(local_id)
            self.assertEqual(wire[:2],b'\x0c\x00')
            self.assertEqual(len(wire),12)

    def test_reset_requires_no_packet_and_only_clears_current_length(self):
        for count in (0, 1, 37, 0xA00):
            with self.subTest(count=count):
                vm = self.vm()
                vm.mem_write(NET + 0x2CC0, struct.pack("<I", count))
                vm.mem_write(NET + 0x2CC4, b"\x23\xa5\x5a\x00")
                # Mark separate outbound and embedded transport memory.
                vm.mem_write(NET + 0x104, b"KEEP")
                vm.mem_write(NET + 0x36C4, struct.pack("<I", 17))
                vm.mem_write(SP, struct.pack("<II", RETURN, 1))
                self.run_to(vm, 0x13670, 0x1000)
                self.assertEqual(bytes(vm.mem_read(NET + 0x2CC0, 4)), bytes(4))
                self.assertEqual(bytes(vm.mem_read(NET + 0x2CC4, 4)), b"\x23\xa5\x5a\x00")
                self.assertEqual(bytes(vm.mem_read(NET + 0x104, 4)), b"KEEP")
                self.assertEqual(bytes(vm.mem_read(NET + 0x36C4, 4)), struct.pack("<I", 17))

    def test_s2c_size_table_is_not_the_c2s_builder_size(self):
        for opcode, target, logical_size in (
            (0x2A, 0x12A0, 37), (0x1F, 0x1306, 125),
            (0x23, 0x124C, 17), (0x1C, 0x12A6, 45),
        ):
            with self.subTest(opcode=opcode):
                self.assertEqual(struct.unpack_from("<I", self.image, 0x1324 + opcode * 4)[0],
                                 BASE + target)
                vm = self.vm()
                vm.mem_write(SP, struct.pack("<I", RETURN))
                self.run_to(vm, target, 0x1000)
                self.assertEqual(vm.reg_read(UC_X86_REG_EAX), logical_size)


def current_world_ready_wire(local_id,config=(4,2)):
    """Execute original builders + zero-seed encoder; stop before send()."""
    fixture=CurrentWorldReadyBuilderTests()
    fixture.setUpClass()
    vm=fixture.vm(config)
    codec=NET+0x104+0x654
    vm.reg_write(UC_X86_REG_ECX,codec)
    vm.mem_write(SP,struct.pack('<I',RETURN))
    vm.emu_start(BASE+0x10490,RETURN,timeout=1000000,count=100000)
    fixture.assertEqual(vm.reg_read(UC_X86_REG_EIP),RETURN)
    vm.mem_write(codec+8,struct.pack('<I',1))
    vm.mem_write(NET+0x2cb8,b'\x01')
    vm.mem_write(WORLD_OUTPUT,struct.pack('<I',local_id))
    vm.reg_write(UC_X86_REG_ESP,SP)
    fixture.run_to(vm,0x654f7,0x12501)
    sp=vm.reg_read(UC_X86_REG_ESP)
    _,pointer,length,flags=struct.unpack('<4I',vm.mem_read(sp,16))
    fixture.assertEqual(flags,0)
    fixture.assertEqual(length,12)
    return bytes(vm.mem_read(pointer,length))


if __name__ == "__main__":
    unittest.main()
