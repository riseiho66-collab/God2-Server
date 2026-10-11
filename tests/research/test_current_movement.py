"""Current 2E builders, 40-slot queue and 5D consumer, without UI or send()."""
import struct
import subprocess
import unittest

import test_current_world_ready_builder as ready
import test_current_route_advertisement as routes
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_EBP, UC_X86_REG_EBX
from unicorn.x86_const import UC_X86_REG_ECX, UC_X86_REG_EIP, UC_X86_REG_ESP

POSITION = ready.NET+0x4800


def movement_wire(x,y,slot,tail=0xff,records=None):
    fixture = ready.CurrentWorldReadyBuilderTests()
    fixture.setUpClass()
    vm = fixture.vm()
    vm.mem_write(ready.STACK,bytes([tail])*0x4000)
    codec = ready.NET+0x104+0x654
    vm.reg_write(UC_X86_REG_ECX,codec)
    vm.mem_write(ready.SP,struct.pack('<I',ready.RETURN))
    vm.reg_write(UC_X86_REG_ESP,ready.SP)
    vm.emu_start(ready.BASE+0x10490,ready.RETURN,count=100000)
    vm.mem_write(codec+8,struct.pack('<I',1))
    vm.mem_write(ready.NET+0x2cb8,b'\x01')
    for cx,cy,index in (records or [(x,y,slot)]):
        # 15790 reserves eight bytes; local byte+5 (SP-3) is not assigned.
        # Seed setup used this stack earlier, so set the tested residue now.
        vm.mem_write(ready.SP-3,bytes([tail]))
        vm.reg_write(UC_X86_REG_ECX,ready.NET)
        vm.reg_write(UC_X86_REG_ESP,ready.SP)
        vm.mem_write(ready.SP,struct.pack('<4I',ready.RETURN,cx,cy,index))
        fixture.run_to(vm,0x15790,0x1000)
    vm.reg_write(UC_X86_REG_ECX,ready.NET)
    vm.reg_write(UC_X86_REG_ESP,ready.SP)
    vm.mem_write(ready.SP,struct.pack('<I',ready.RETURN))
    vm.emu_start(ready.BASE+0x13370,ready.BASE+0x12501,count=500000)
    fixture.assertEqual(vm.reg_read(UC_X86_REG_EIP),ready.BASE+0x12501)
    _,pointer,length,flags = struct.unpack('<4I',vm.mem_read(vm.reg_read(UC_X86_REG_ESP),16))
    fixture.assertEqual(flags,0)
    return bytes(vm.mem_read(pointer,length))


class CurrentMovementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ready.CurrentWorldReadyBuilderTests.setUpClass()
        cls.binary = ready.ROOT/'build/tests/Release/recovered-movement.exe'

    def test_original_builder_preserves_unwritten_tail_in_cpp_decoder(self):
        for tail in (0,1,0x5a,0xa5,0xff):
            for x,y,slot in ((18,12,1),(16,14,39),(0,0,0),(65535,32768,255)):
                wire = movement_wire(x,y,slot,tail)
                values = subprocess.check_output([str(self.binary),'--decode',wire.hex()],text=True).split()
                self.assertEqual(tuple(map(int,values)),(x,y,slot,tail))

    def test_original_queue_and_ack_consumer_wrap_at_forty(self):
        fixture = ready.CurrentWorldReadyBuilderTests()
        vm = fixture.vm()
        vm.mem_map(ready.WORLD,4096)
        vm.mem_write(ready.WORLD_OUTPUT,struct.pack('<I',217))
        queue = ready.WORLD+0x234
        effects = []
        def call(entry,*args):
            vm.mem_write(ready.SP,struct.pack('<'+'I'*(len(args)+1),ready.RETURN,*args))
            vm.reg_write(UC_X86_REG_ESP,ready.SP)
            vm.reg_write(UC_X86_REG_ECX,ready.WORLD)
            fixture.run_to(vm,entry,0x1000)
        def effect(uc,address,size,_):
            if address != ready.BASE+0x6cc00:return
            sp = uc.reg_read(UC_X86_REG_ESP)
            ret,*args = struct.unpack('<5I',uc.mem_read(sp,20))
            effects.append(args)
            uc.reg_write(UC_X86_REG_ESP,sp+20)
            uc.reg_write(UC_X86_REG_EIP,ret)
        vm.hook_add(UC_HOOK_CODE,effect)
        call(0x103640,queue)
        vm.mem_write(POSITION,struct.pack('<ii',17,13))
        call(0x1036b0,queue,POSITION)
        self.assertEqual(bytes(vm.mem_read(queue,3)),b'\x01\x00\x01')
        oracle = routes.CurrentRouteAdvertisementTests()
        oracle.image = fixture.image
        previous = (17,13)
        for step in range(1,83):
            slot = step%40
            self.assertEqual(vm.mem_read(queue+2,1)[0],slot)
            position = (18,12) if step&1 else (17,13)
            vm.mem_write(POSITION,struct.pack('<ii',*position))
            call(0x1036b0,queue,POSITION)
            wire = bytes.fromhex(subprocess.check_output([str(self.binary),'--ack',str(slot)],text=True).strip())
            plain = oracle.decode(oracle.vm(),wire)
            self.assertEqual(plain[2:4],bytes([0x5d,slot]))
            vm.mem_write(POSITION,plain[2:-1])
            vm.reg_write(UC_X86_REG_EBX,POSITION)
            vm.reg_write(UC_X86_REG_EBP,ready.WORLD)
            vm.reg_write(UC_X86_REG_ESP,ready.SP)
            fixture.run_to(vm,0x692fa,0x6b517)
            self.assertEqual(vm.mem_read(ready.WORLD+0x231,1)[0],slot)
            self.assertEqual(bytes(vm.mem_read(queue,3)),bytes([1,slot,(slot+1)%40]))
            self.assertEqual((effects[-1][0]&65535,*effects[-1][1:3]),(217,*previous))
            previous = position

    def test_current_step_precondition_is_adjacent_not_arbitrary_destination(self):
        fixture = ready.CurrentWorldReadyBuilderTests()
        for dx,dy in ((1,-1),(-1,1),(0,0),(1,1),(2,0),(0,-2)):
            vm = fixture.vm()
            failures=[]
            def assertion(uc,address,size,_):
                if address == ready.BASE+0x2c70:
                    failures.append(address);uc.emu_stop()
            vm.hook_add(UC_HOOK_CODE,assertion)
            vm.mem_write(ready.SP,struct.pack('<6I',ready.RETURN,17,13,17+dx,13+dy,1))
            vm.reg_write(UC_X86_REG_ESP,ready.SP)
            vm.reg_write(UC_X86_REG_ECX,ready.WORLD)
            vm.emu_start(ready.BASE+0x102700,ready.BASE+0x10276b,count=1000)
            self.assertEqual(bool(failures),abs(dx)>1 or abs(dy)>1)


if __name__ == '__main__':unittest.main()
