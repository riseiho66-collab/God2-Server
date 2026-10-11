"""Original 2.40.83 common-chat receiver through bubble and panel calls.

Only the language probe, strcmp-like special-command probes and UI callees
are stubbed. This verifies native receiver routing, not on-screen rendering.
"""
import hashlib
from pathlib import Path
import struct
import unittest

from unicorn import Uc,UcError,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE,UC_HOOK_MEM_INVALID
from unicorn.x86_const import UC_X86_REG_EAX,UC_X86_REG_EBP,UC_X86_REG_EBX,UC_X86_REG_ECX,UC_X86_REG_EIP,UC_X86_REG_ESP


ROOT=Path(__file__).resolve().parents[2]
IMAGE=ROOT/'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin'
SHA='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
BASE=0x400000
STACK=0x3000000
PACKET=0x3100000
WORLD=0x10000000


class CurrentChatReceiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image=IMAGE.read_bytes()
        if hashlib.sha256(cls.image).hexdigest()!=SHA:
            raise AssertionError('Original mapped client identity changed')

    def route(self,text,simplified,sender=0x1234):
        encoded=text.encode('cp936' if simplified else 'cp950')
        logical=bytearray(len(encoded)+14)
        logical[0]=0x5c
        logical[1:3]=len(logical).to_bytes(2,'little')
        logical[5:9]=sender.to_bytes(4,'little')
        logical[9]=0x80 if simplified else 0
        logical[13:13+len(encoded)]=encoded
        vm=Uc(UC_ARCH_X86,UC_MODE_32)
        vm.mem_map(BASE,(len(self.image)+4095)&~4095)
        vm.mem_write(BASE,self.image)
        vm.mem_map(STACK,0x4000)
        vm.mem_map(PACKET,0x1000)
        vm.mem_write(PACKET,bytes(logical))
        local_id=WORLD+0x1539683c
        vm.mem_map(local_id&~4095,4096)
        vm.mem_write(local_id,(0x789a).to_bytes(4,'little'))
        vm.reg_write(UC_X86_REG_ESP,STACK+0x2000)
        vm.reg_write(UC_X86_REG_EBP,WORLD)
        vm.reg_write(UC_X86_REG_EBX,PACKET)
        bubbles=[]
        panels=[]
        def hook(uc,address,size,user):
            if address not in (BASE+0x131c10,BASE+0x147f90,BASE+0xfb690,
                               BASE+0x75e00):
                return
            esp=uc.reg_read(UC_X86_REG_ESP)
            return_to=struct.unpack('<I',uc.mem_read(esp,4))[0]
            if address==BASE+0x131c10:
                uc.reg_write(UC_X86_REG_EAX,int(simplified))
                uc.reg_write(UC_X86_REG_ESP,esp+4)
            elif address==BASE+0x147f90:
                uc.reg_write(UC_X86_REG_EAX,0)
                uc.reg_write(UC_X86_REG_ESP,esp+4)
            elif address==BASE+0xfb690:
                sender,pointer=struct.unpack('<II',uc.mem_read(esp+4,8))
                displayed=bytes(uc.mem_read(pointer,len(encoded)+1))
                bubbles.append((sender,displayed,uc.reg_read(UC_X86_REG_ECX)))
                uc.reg_write(UC_X86_REG_ESP,esp+12)  # Native callee ret 8.
                uc.reg_write(UC_X86_REG_EIP,return_to)
                return
            else:
                category,pointer=struct.unpack('<II',uc.mem_read(esp+4,8))
                panels.append((category,bytes(uc.mem_read(pointer,len(encoded)+1)),
                               uc.reg_read(UC_X86_REG_ECX)))
                uc.emu_stop()
                return
            uc.reg_write(UC_X86_REG_EIP,return_to)
        vm.hook_add(UC_HOOK_CODE,hook)
        faults=[]
        def invalid(uc,access,address,size,value,user):
            faults.append((address,uc.reg_read(UC_X86_REG_EIP)))
            return False
        vm.hook_add(UC_HOOK_MEM_INVALID,invalid)
        try:vm.emu_start(BASE+0x6ae96,BASE+0x6b517,timeout=1000000,count=10000)
        except UcError as error:raise AssertionError(f'Native receiver faults {faults}') from error
        self.assertEqual(vm.reg_read(UC_X86_REG_EIP),BASE+0x75e00)
        self.assertEqual(bubbles,[(sender,encoded+b'\0',WORLD+0x15383410)])
        self.assertEqual(panels,[(0,encoded+b'\0',WORLD+0xa7f2f6c)])

    def test_traditional_and_simplified_common_chat_reach_native_ui(self):
        self.route('漢字遊戲',False)
        self.route('汉字游戏',True)
        self.route('歡迎來到仙界傳。',False,0x7fffffff)
        self.route('欢迎来到仙界传。',True,0x7fffffff)

    def test_welcome_sender_misses_original_actor_bubble_lookup(self):
        vm=Uc(UC_ARCH_X86,UC_MODE_32)
        vm.mem_map(BASE,(len(self.image)+4095)&~4095)
        vm.mem_write(BASE,self.image)
        vm.mem_map(STACK,0x10000)
        vm.mem_map(PACKET,0x1000)
        actors=0x3600000
        vm.mem_map(actors,0x14000)
        vm.mem_write(PACKET,b'welcome\0')
        sp=STACK+0x8000
        vm.mem_write(sp,struct.pack('<III',0x7fff0000,0x7fffffff,PACKET))
        vm.reg_write(UC_X86_REG_ESP,sp)
        vm.reg_write(UC_X86_REG_ECX,actors)
        vm.emu_start(BASE+0xfb690,0x7fff0000,timeout=1000000,count=10000)
        self.assertEqual(vm.reg_read(UC_X86_REG_EIP),0x7fff0000)
        self.assertEqual(vm.reg_read(UC_X86_REG_ESP),sp+12)

    def test_common_channel_panel_filter_in_original_client(self):
        # 475E00 dispatches type0 through original 4C7610. A user option at
        # panel config+449C bit4 controls whether 47DE00 receives the line.
        for enabled in (False,True):
            with self.subTest(enabled=enabled):
                vm=Uc(UC_ARCH_X86,UC_MODE_32)
                vm.mem_map(BASE,(len(self.image)+4095)&~4095)
                vm.mem_write(BASE,self.image)
                vm.mem_map(STACK,0x4000)
                vm.mem_map(PACKET,0x1000)
                ui=WORLD+0xa7f2f6c
                vm.mem_map(ui&~4095,0x89000)
                options=0x3300000
                vm.mem_map(options,0x5000)
                vm.mem_write(ui+0x86888,struct.pack('<I',options))
                vm.mem_write(options+0x449c,bytes((0x10 if enabled else 0,)))
                content=b'common channel test\0'
                vm.mem_write(PACKET,content)
                sp=STACK+0x3000
                vm.mem_write(sp,struct.pack('<III',0x7fff0000,0,PACKET))
                vm.reg_write(UC_X86_REG_ESP,sp)
                vm.reg_write(UC_X86_REG_ECX,ui)
                calls=[]
                def hook(uc,address,size,user):
                    if address==BASE+0x7dd60:
                        inner=uc.reg_read(UC_X86_REG_ESP)
                        return_to=struct.unpack('<I',uc.mem_read(inner,4))[0]
                        uc.reg_write(UC_X86_REG_ESP,inner+12)  # Native callee ret 8.
                        uc.reg_write(UC_X86_REG_EIP,return_to)
                    elif address==BASE+0x7de00:
                        inner=uc.reg_read(UC_X86_REG_ESP)
                        category,color,pointer=struct.unpack('<III',uc.mem_read(inner+4,12))
                        calls.append((category,color,bytes(uc.mem_read(pointer,len(content)))))
                        uc.emu_stop()
                vm.hook_add(UC_HOOK_CODE,hook)
                vm.emu_start(BASE+0x75e00,0x7fff0000,timeout=1000000,count=10000)
                self.assertEqual(calls,[(0,0xffffff,content)] if enabled else [])


if __name__=='__main__':unittest.main()
