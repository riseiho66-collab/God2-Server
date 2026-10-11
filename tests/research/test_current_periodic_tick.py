"""Execute current 11750 and its original queue/codec, without socket or UI."""
import struct
import unittest

import test_current_world_ready_builder as ready
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_ECX, UC_X86_REG_EDI, UC_X86_REG_EIP, UC_X86_REG_ESI, UC_X86_REG_ESP

TIMER = ready.NET + 0x4800


def periodic_wire(movements=()):
    fixture = ready.CurrentWorldReadyBuilderTests()
    fixture.setUpClass()
    vm = fixture.vm()
    codec = ready.NET + 0x104 + 0x654
    vm.reg_write(UC_X86_REG_ECX, codec)
    vm.mem_write(ready.SP, struct.pack('<I', ready.RETURN))
    vm.reg_write(UC_X86_REG_ESP, ready.SP)
    vm.emu_start(ready.BASE + 0x10490, ready.RETURN, count=100000)
    fixture.assertEqual(vm.reg_read(UC_X86_REG_EIP), ready.RETURN)
    vm.mem_write(codec + 8, struct.pack('<I', 1))
    vm.mem_write(ready.NET + 0x2cb8, b'\x01')
    for x, y, slot in movements:
        vm.mem_write(ready.SP - 3, b'\xa5')
        vm.reg_write(UC_X86_REG_ECX, ready.NET)
        vm.reg_write(UC_X86_REG_ESP, ready.SP)
        vm.mem_write(ready.SP, struct.pack('<4I', ready.RETURN, x, y, slot))
        fixture.run_to(vm, 0x15790, 0x1000)
    vm.mem_write(TIMER + 0x14, struct.pack('<I', ready.NET))
    vm.mem_write(ready.SP, struct.pack('<II', ready.RETURN, TIMER))
    vm.reg_write(UC_X86_REG_ESP, ready.SP)
    vm.emu_start(ready.BASE + 0x11750, ready.BASE + 0x12501, count=500000)
    fixture.assertEqual(vm.reg_read(UC_X86_REG_EIP), ready.BASE + 0x12501)
    _, pointer, length, flags = struct.unpack('<4I', vm.mem_read(vm.reg_read(UC_X86_REG_ESP), 16))
    fixture.assertEqual(flags, 0)
    return bytes(vm.mem_read(pointer, length))


class CurrentPeriodicTickTests(unittest.TestCase):
    def test_original_empty_queue_flush_has_exact_five_byte_wire(self):
        self.assertEqual(periodic_wire(), bytes.fromhex('05002d2d22'))

    def test_original_flush_appends_tick_to_pending_movement(self):
        import test_current_route_advertisement as routes
        oracle = routes.CurrentRouteAdvertisementTests()
        ready.CurrentWorldReadyBuilderTests.setUpClass()
        oracle.image = ready.CurrentWorldReadyBuilderTests.image
        for records in ([(18, 12, 1)], [(18, 12, 1), (17, 13, 2)]):
            wire = periodic_wire(records)
            plain = oracle.decode(oracle.vm(), wire)
            expected = b''.join(b'\x2e' + struct.pack('<HHBB', x, y, slot, 0xa5)
                                for x, y, slot in records) + b'\x30\x00'
            self.assertEqual(plain[2:-1], expected)

    def test_null_network_returns_without_queueing(self):
        fixture = ready.CurrentWorldReadyBuilderTests()
        fixture.setUpClass()
        vm = fixture.vm()
        vm.mem_write(TIMER + 0x14, bytes(4))
        vm.mem_write(ready.SP, struct.pack('<II', ready.RETURN, TIMER))
        vm.reg_write(UC_X86_REG_ESP, ready.SP)
        fixture.run_to(vm, 0x11750, 0x1000)
        self.assertEqual(fixture.queued(vm), b'')

    def test_original_default_interval_and_due_branch(self):
        fixture = ready.CurrentWorldReadyBuilderTests()
        fixture.setUpClass()
        for anchor, now, sent, due in ((100, 5099, 0, False), (100, 5100, 0, True),
                                     (100, 10099, 1, False), (100, 10100, 1, True),
                                     (0xfffffff0, 4983, 0, False),
                                     (0xfffffff0, 4984, 0, True)):
            with self.subTest(anchor=anchor, now=now, sent=sent):
                vm = fixture.vm()
                vm.mem_write(ready.SP, struct.pack('<I', ready.RETURN))
                vm.reg_write(UC_X86_REG_ESP, ready.SP)
                vm.reg_write(UC_X86_REG_ECX, TIMER)
                fixture.run_to(vm, 0x115d0, 0x1000)
                self.assertEqual(struct.unpack('<I', vm.mem_read(TIMER, 4))[0], 5000)
                vm.mem_write(TIMER + 0x2c, struct.pack('<II', anchor, sent))
                vm.reg_write(UC_X86_REG_ESI, TIMER)
                vm.reg_write(UC_X86_REG_EDI, now)
                vm.reg_write(UC_X86_REG_ESP, ready.SP)
                def stop_at_decision(machine, address, size, _):
                    if address in (ready.BASE + 0x11852, ready.BASE + 0x1187f):
                        machine.emu_stop()
                vm.hook_add(UC_HOOK_CODE, stop_at_decision)
                vm.emu_start(ready.BASE + 0x11837, ready.RETURN, count=200)
                self.assertEqual(vm.reg_read(UC_X86_REG_EIP),
                                 ready.BASE + (0x11852 if due else 0x1187f))


if __name__ == '__main__':
    unittest.main()
