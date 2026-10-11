"""Pinned client result-branch execution with synthetic memory, not live creation."""
import hashlib
from pathlib import Path
import struct
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'artifacts/tooling/crypto-oracle-python'))
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_PROT_READ, UC_PROT_EXEC
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_EDX, UC_X86_REG_ESP, UC_X86_REG_EIP


class CurrentCharacterCreateResultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image=(ROOT/'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin').read_bytes()
        if hashlib.sha256(cls.image).hexdigest()!='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763':
            raise AssertionError('Current mapped client changed')

    def test_opcode2_table_returns_23_logical_bytes(self):
        self.assertEqual(struct.unpack_from('<I',self.image,0x132c)[0],0x401234)
        self.assertEqual(self.image[0x1234:0x123a],bytes.fromhex('b817000000c3'))

    def test_opcode17_result_word_branch(self):
        for result in (0, 1, 256, 65535):
            with self.subTest(result=result):
                vm=Uc(UC_ARCH_X86,UC_MODE_32)
                vm.mem_map(0x414000,8192,UC_PROT_READ|UC_PROT_EXEC)
                vm.mem_write(0x414000,self.image[0x14000:0x16000])
                vm.mem_map(0x3000000,4096)
                vm.mem_map(0x3100000,4096)
                vm.mem_write(0x3100100,b'\x02'+struct.pack('<H',result)+bytes(20))
                vm.mem_protect(0x3100000,4096,UC_PROT_READ)
                vm.reg_write(UC_X86_REG_EDX,0x3100100)
                vm.reg_write(UC_X86_REG_EBX,0x3200000)
                vm.reg_write(UC_X86_REG_ESP,0x3000800)
                stop=0x415004 if result==0 else 0x414f7f
                vm.emu_start(0x414f12,stop,timeout=100000,count=32)
                self.assertEqual(vm.reg_read(UC_X86_REG_EIP),stop)
                if result==0:
                    self.assertEqual(vm.reg_read(UC_X86_REG_ESP),0x30007fc)
                    self.assertEqual(bytes(vm.mem_read(0x30007fc,4)),bytes(4))

    def test_word_result_controls_success_and_error_paths(self):
        for result in (0,1,256):
            with self.subTest(result=result):
                vm=Uc(UC_ARCH_X86,UC_MODE_32)
                vm.mem_map(0x415000,4096,UC_PROT_READ|UC_PROT_EXEC)
                vm.mem_write(0x415000,self.image[0x15000:0x16000])
                vm.mem_map(0x3000000,4096)
                vm.mem_map(0x3100000,4096)
                plain=b'\x02'+struct.pack('<H',result)+bytes(20)
                vm.mem_write(0x3100100,plain)
                vm.mem_protect(0x3100000,4096,UC_PROT_READ)
                vm.reg_write(UC_X86_REG_EAX,0x3100100)
                vm.reg_write(UC_X86_REG_EBX,0x3200000)
                vm.reg_write(UC_X86_REG_ESP,0x3000800)
                # Stop before queue consumption or error-string lookup, neither
                # of which has a real captured object in this synthetic test.
                stop=0x41516a if result==0 else 0x4150e5
                vm.emu_start(0x415076,stop,timeout=100000,count=32)
                self.assertEqual(vm.reg_read(UC_X86_REG_EIP),stop)
                if result==0:
                    self.assertEqual(vm.reg_read(UC_X86_REG_ESP),0x30007fc)
                    self.assertEqual(bytes(vm.mem_read(0x30007fc,4)),bytes(4))


if __name__=='__main__':unittest.main()
