"""Pinned x86 builders with synthetic arguments; stop before queue/network calls."""
import hashlib
import struct
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'artifacts/tooling/crypto-oracle-python'))
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_PROT_READ,UC_PROT_EXEC
from unicorn.x86_const import UC_X86_REG_ECX,UC_X86_REG_ESP,UC_X86_REG_EIP


def builder(opcode,value):
    data=(ROOT/'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin').read_bytes()
    if hashlib.sha256(data).hexdigest()!='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763':
        raise AssertionError('Current image changed')
    vm=Uc(UC_ARCH_X86,UC_MODE_32)
    vm.mem_map(0x400000,(len(data)+4095)&~4095,UC_PROT_READ|UC_PROT_EXEC)
    vm.mem_write(0x400000,data)
    stack,source,obj=0x3000000,0x3100000,0x3200000
    for address,size in ((stack,4096),(source,4096),(obj,0x16000)):
        vm.mem_map(address,size);vm.mem_write(address,b'\xa5'*size)
    sp=stack+0x800
    if opcode==0x18:
        vm.mem_write(sp,struct.pack('<II',0,value))
        vm.mem_write(obj+0x15e88,struct.pack('<I',0x3300000))
        entry,stop,length=0x40be80,0x40be9a,1
    elif opcode==0x1a:
        vm.mem_write(source+0x100,b'LocalBufferA\0'+b'X'*3)
        vm.mem_write(source+0x200,b'LocalBufferB\0'+b'Y'*3)
        vm.mem_write(sp,struct.pack('<IIII',0,source+0x100,source+0x200,value))
        entry,stop,length=0x414c50,0x414ca6,37
    else:raise ValueError('Unsupported builder')
    vm.reg_write(UC_X86_REG_ESP,sp);vm.reg_write(UC_X86_REG_ECX,obj)
    # Includes the original CRT bounded-copy implementation for the 1A builder.
    vm.emu_start(entry,stop,timeout=100000,count=4096)
    if vm.reg_read(UC_X86_REG_EIP)!=stop:raise AssertionError('Builder did not reach queue boundary')
    actual,pointer,size=struct.unpack('<III',vm.mem_read(vm.reg_read(UC_X86_REG_ESP),12))
    if actual!=opcode or size!=length:raise AssertionError('Queue shape changed')
    if not stack<=pointer<=stack+4096-size:raise AssertionError('Unexpected builder output location')
    return bytes(vm.mem_read(pointer,size))


class CurrentPostCreateBuilderTests(unittest.TestCase):
    def test_context_builder_keeps_low_byte(self):
        for value in (0,1,255,256):
            with self.subTest(value=value):self.assertEqual(builder(0x18,value),bytes([value&255]))

    def test_selection_builder_bounds_and_unwritten_tail(self):
        for token in range(8):
            with self.subTest(token=token):
                payload=builder(0x1a,token)
                self.assertEqual(payload[:16],b'LocalBufferA\0'+bytes(3))
                self.assertEqual(payload[16:32],b'LocalBufferB\0'+bytes(3))
                self.assertEqual(payload[32:34],bytes([token if token<4 else 0,4]))
                self.assertEqual(payload[34:],b'\xa5'*3)


if __name__=='__main__':unittest.main()
