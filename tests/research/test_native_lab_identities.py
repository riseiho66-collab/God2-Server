"""Generated native-call pages with stubbed callees; not login acceptance."""
import struct
import unittest

from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_ECX
from tools.strike_lab.current_login_command import submit_page,creation_page,lab_identity


class NativeLabIdentityTests(unittest.TestCase):
    def execute(self,page):
        address,stack,login=0x30000000,0x31000000,0x10000000
        code,trap=page(address,login)
        vm=Uc(UC_ARCH_X86,UC_MODE_32)
        vm.mem_map(address,4096);vm.mem_write(address,code)
        vm.mem_map(stack,4096);vm.reg_write(UC_X86_REG_ESP,stack+2048)
        vm.mem_map(0x400000,0x200000)
        vm.mem_write(0x50ec90,b'\xc2\x04\x00')
        for target in (0x4068e0,0x40a870):vm.mem_write(target,b'\xc2\x08\x00')
        calls=[]
        def hook(uc,pc,size,context):
            if pc not in (0x50ec90,0x4068e0,0x40a870):return
            sp=uc.reg_read(UC_X86_REG_ESP)
            receiver=uc.reg_read(UC_X86_REG_ECX)
            if pc==0x50ec90:
                pointer=struct.unpack('<I',uc.mem_read(sp+4,4))[0]
                value=bytes(uc.mem_read(pointer,32)).split(b'\0',1)[0]
            else:value=struct.unpack('<II',uc.mem_read(sp+4,8))
            calls.append((pc,receiver,value))
        vm.hook_add(UC_HOOK_CODE,hook)
        vm.emu_start(address,address+trap,count=100)
        self.assertEqual(vm.reg_read(UC_X86_REG_ESP),stack+2048)
        self.assertEqual(code[trap:trap+3],b'\xcc\x0f\x0b')
        return calls

    def test_distinct_fixed_accounts_and_names_reach_setters(self):
        identities=[]
        for peer in (0,1):
            account,name=lab_identity(peer);identities.append((account,name))
            calls=self.execute(lambda address,login:submit_page(address,login,peer))
            self.assertEqual(calls,[(0x50ec90,0x10178db4,account),
                                   (0x50ec90,0x10179940,b'labtest2345'),
                                   (0x4068e0,0x10000000,(5,1))])
            calls=self.execute(lambda address,login:creation_page(address,login,True,peer))
            self.assertEqual(calls,[(0x50ec90,0x100152a8,name),(0x40a870,0x10000000,(17,1))])
        self.assertNotEqual(identities[0][0],identities[1][0])
        self.assertNotEqual(identities[0][1],identities[1][1])
        self.assertEqual(identities[0],(b'codexlab',b'CodexTrial'))

    def test_reject_arbitrary_identity_selectors(self):
        for peer in (-1,2,True,False,1.0,'1',None):
            with self.subTest(peer=peer):
                with self.assertRaises(ValueError):submit_page(0x30000000,0x10000000,peer)
                with self.assertRaises(ValueError):creation_page(0x30000000,0x10000000,True,peer)


if __name__=='__main__':unittest.main()
