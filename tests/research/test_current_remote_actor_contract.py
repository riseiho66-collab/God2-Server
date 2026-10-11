"""Original instruction slices: remote actor IDs/coordinates, not live visibility."""
import hashlib
import struct
import unittest

from tools.strike_lab.current_protocol_coverage import IMAGE, IMAGE_SHA256
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_PROT_READ, UC_PROT_EXEC, UC_HOOK_CODE
from unicorn.x86_const import (UC_X86_REG_ESP, UC_X86_REG_EBP, UC_X86_REG_EBX,
                              UC_X86_REG_ECX, UC_X86_REG_EDX, UC_X86_REG_EAX, UC_X86_REG_EIP,
                              UC_X86_REG_ESI, UC_X86_REG_EDI)

BASE=0x400000
STACK=0x30000000
BODY=STACK+0x1000
WORLD=0x10000000
POOL=0x20000000


class RemoteActorContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=IMAGE.read_bytes()
        if hashlib.sha256(cls.raw).hexdigest()!=IMAGE_SHA256:
            raise ValueError('Current native image identity mismatch')

    def setUp(self):
        self.vm=Uc(UC_ARCH_X86,UC_MODE_32)
        self.vm.mem_map(BASE,(len(self.raw)+4095)&~4095)
        self.vm.mem_write(BASE,self.raw)
        self.vm.mem_protect(BASE,(len(self.raw)+4095)&~4095,UC_PROT_READ|UC_PROT_EXEC)
        self.vm.mem_map(STACK,0x4000)
        self.vm.mem_map(POOL,0x14000)

    def test_dispatch_and_native_length_leaves(self):
        for opcode,size,target in ((0x6f,81,0x695c8),(0x5e,13,0x69a60),(0x73,5,0x69a28)):
            self.assertEqual(struct.unpack_from('<I',self.raw,0x6b5d4+4*opcode)[0],BASE+target)
            leaf=struct.unpack_from('<I',self.raw,0x1324+4*opcode)[0]
            self.vm.mem_write(STACK+0x800,struct.pack('<I',STACK+0x3000))
            self.vm.reg_write(UC_X86_REG_ESP,STACK+0x800)
            self.vm.emu_start(leaf,STACK+0x3000,count=20)
            self.assertEqual(self.vm.reg_read(UC_X86_REG_EAX),size)

    def projection(self,opcode,identity,packed):
        body=bytearray(81 if opcode==0x6f else 13)
        body[0]=opcode
        struct.pack_into('<I',body,1,identity)
        struct.pack_into('<I',body,13 if opcode==0x6f else 9,packed)
        self.vm.mem_write(BODY,bytes(body))
        self.vm.reg_write(UC_X86_REG_ESP,STACK+0x800)
        self.vm.reg_write(UC_X86_REG_EBP,WORLD)
        self.vm.reg_write(UC_X86_REG_EBX,BODY)
        self.vm.reg_write(UC_X86_REG_EDX,0)
        start,stop=(0x695c8,0x695f1) if opcode==0x6f else (0x69a60,0x69a82)
        self.vm.emu_start(BASE+start,BASE+stop,count=40)
        sp=self.vm.reg_read(UC_X86_REG_ESP)
        self.assertEqual(sp,STACK+0x800-12)
        self.assertEqual(self.vm.reg_read(UC_X86_REG_ECX),WORLD+0xa7f2f6c)
        entity,x,y=struct.unpack('<III',self.vm.mem_read(sp,12))
        return entity&0xffff,x,y

    def test_original_coordinate_projection_and_id_widths(self):
        for identity in (0,1,4095,4096,16383,65535,0xffffffff):
            for x,y in ((0,0),(86,71),(2047,2047),(2048,32767),(32767,1)):
                self.assertEqual(self.projection(0x6f,identity,(x<<2)|(y<<17)|3),
                                 (identity&0xfff,x,y))
                self.assertEqual(self.projection(0x5e,identity,(x&2047)|((y&2047)<<11)|0xffc00000),
                                 (identity&0xffff,x&2047,y&2047))

    def test_original_remote_pool_lookup_capacity(self):
        self.vm.mem_write(POOL,b'\xff'*0x14000)
        for slot,identity in ((0,7),(63,4095),(127,1234)):
            self.vm.mem_write(POOL+0x18+slot*0x268,struct.pack('<I',identity))
        for identity,expected in ((7,0),(4095,63),(1234,127),(8,65535),(65543,65535)):
            self.vm.mem_write(STACK+0x800,struct.pack('<II',STACK+0x3000,identity))
            self.vm.reg_write(UC_X86_REG_ESP,STACK+0x800)
            self.vm.reg_write(UC_X86_REG_ECX,POOL)
            self.vm.emu_start(BASE+0xfc960,STACK+0x3000,count=3000)
            self.assertEqual(self.vm.reg_read(UC_X86_REG_EAX)&0xffff,expected)
            self.assertEqual(self.vm.reg_read(UC_X86_REG_ESP),STACK+0x808)

    def test_remote_status_bit_selects_original_component_action(self):
        actor=POOL+0x18
        def selection(status,source,slot=2):
            self.vm.mem_write(actor+0x60,struct.pack('<H',status))
            self.vm.mem_write(BODY,bytes([source]))
            self.vm.mem_write(STACK+0x818,struct.pack('<I',BODY))
            self.vm.reg_write(UC_X86_REG_ESP,STACK+0x800)
            self.vm.reg_write(UC_X86_REG_ESI,actor)
            self.vm.reg_write(UC_X86_REG_EBX,slot)
            self.vm.reg_write(UC_X86_REG_EAX,0)
            self.vm.emu_start(BASE+0xfb5a2,BASE+0xfb5bd,count=20)
            self.assertEqual(self.vm.reg_read(UC_X86_REG_ECX),actor+0x224)
            self.assertEqual(self.vm.reg_read(UC_X86_REG_ESP),STACK+0x7f8)
            selected_slot,action=struct.unpack('<II',self.vm.mem_read(STACK+0x7f8,8))
            self.assertEqual(selected_slot,slot)
            return action&255
        # Exhaustive status words: only bit12 changes this action-selection slice.
        for status in range(65536):
            self.assertEqual(selection(status,0xa0),7 if status&0x1000 else 5)
        for source in range(256):
            for slot in range(4):
                self.assertEqual(selection(0,source,slot),source>>5)
                self.assertEqual(selection(0x1000,source,slot),7)

    def test_status_high_byte_selects_named_native_effect_actions(self):
        from tools.strike_lab.current_world_startup_assets import pinned_assets
        from tools.strike_lab.current_four_stat_ui_binding import parse_rom
        sources=pinned_assets()
        rom=parse_rom(sources[3][1],name_encoding='cp950')
        names=['\u5c01','\u7720','\u6bd2','\u4e82','\u77f3']
        display=POOL+0x4000;actor=POOL+0x18
        for index,name in enumerate(names):
            self.setUp()
            status=1<<(index+8)
            self.vm.mem_write(POOL+8,struct.pack('<I',display))
            self.vm.mem_write(actor+0x48,b'\0\0')
            self.vm.mem_write(display+0x46,b'\xff\xff\0\0')
            self.vm.mem_write(STACK+0x800,struct.pack('<III',STACK+0x3000,actor,status))
            self.vm.reg_write(UC_X86_REG_ESP,STACK+0x800)
            self.vm.reg_write(UC_X86_REG_ECX,POOL)
            # Original remote status -> display status setup, stopping at icon setup.
            try:
                self.vm.emu_start(BASE+0xfd770,BASE+0x10adc0,count=300)
            except Exception as error:
                self.fail(f'status {status:x} PC {self.vm.reg_read(UC_X86_REG_EIP):x}: {error}')
            sp=self.vm.reg_read(UC_X86_REG_ESP)
            selected=struct.unpack('<III',self.vm.mem_read(sp,12))
            self.assertEqual(selected[1:],(display+0x1c,index))
            # Continue original setup only as far as its resource-selection call.
            self.vm.mem_write(display+0x18,struct.pack('<I',23))
            self.vm.mem_write(display+0x1c+0x2a,b'\0\0')
            self.vm.emu_start(BASE+0x10adc0,BASE+0x10adff,count=50)
            sp=self.vm.reg_read(UC_X86_REG_ESP)
            _,resource,action,mode=struct.unpack('<4I',self.vm.mem_read(sp,16))
            self.assertEqual((resource,action,mode),(23,index,0))
            self.assertEqual(rom['actions'][action]['name'],name)
            # The original resolver treats selectors0..4 as ordinals, not source IDs.
            self.vm.mem_write(BODY+0x108c,struct.pack('<I',len(rom['actions'])))
            self.vm.mem_write(STACK+0x800,struct.pack('<III',STACK+0x3000,BODY,index))
            self.vm.reg_write(UC_X86_REG_ESP,STACK+0x800)
            self.vm.emu_start(BASE+0x1ae20,STACK+0x3000,count=30)
            self.assertEqual(self.vm.reg_read(UC_X86_REG_EAX),index)

    def test_remote_title_low_byte_priority_differs_on_insert_and_update(self):
        actor=POOL+0x18
        display=POOL+0x4000
        self.vm.mem_write(POOL+8,struct.pack('<I',display))
        self.vm.mem_write(actor+0x48,struct.pack('<H',7))
        targets={BASE+x for x in (0x10a430,0x10a510,0x10a580,0x10a5f0)}
        observed=[]
        def stop_at_title(vm,address,size,user):
            if address in targets:
                observed.append(address-BASE)
                vm.emu_stop()
        hook=self.vm.hook_add(UC_HOOK_CODE,stop_at_title)
        try:
            for insert in (False,True):
                for flags in range(256):
                    observed.clear()
                    self.vm.mem_write(actor+0x60,struct.pack('<H',flags))
                    self.vm.reg_write(UC_X86_REG_ESP,STACK+0x800)
                    self.vm.reg_write(UC_X86_REG_EBP,actor)
                    self.vm.reg_write(UC_X86_REG_ESI,POOL if insert else actor)
                    self.vm.reg_write(UC_X86_REG_EDI,POOL)
                    self.vm.emu_start(BASE+(0xfc4b9 if insert else 0xfb5eb),
                                      STACK+0x3000,count=40)
                    priority=(2,1) if insert else (1,2)
                    expected=0x10a510 if flags&128 else next(
                        ({1:0x10a430,2:0x10a580}[bit] for bit in priority if flags&bit),
                        0x10a5f0)
                    self.assertEqual(observed,[expected],(insert,flags))
                    self.assertEqual(self.vm.reg_read(UC_X86_REG_ECX),display)
                    sp=self.vm.reg_read(UC_X86_REG_ESP)
                    self.assertEqual(struct.unpack('<H',self.vm.mem_read(sp+4,2))[0],7)
        finally:
            self.vm.hook_del(hook)

    def test_native_remote_title_uses_dtitle_not_state_effect_resource(self):
        from tools.strike_lab.current_world_startup_assets import pinned_assets
        from tools.strike_lab.current_four_stat_ui_binding import parse_rom
        actions=parse_rom(pinned_assets()[2][1],name_encoding='cp950')['actions']
        for entry,action,name in ((0x10a430,1,'Fight'),(0x10a510,2,'Help'),
                                  (0x10a580,3,'Watch')):
            self.setUp()
            self.vm.mem_write(POOL+4,struct.pack('<I',BODY))
            self.vm.mem_write(POOL+0x10,struct.pack('<I',23))
            self.vm.mem_write(POOL+0x18,struct.pack('<I',99))
            self.vm.mem_write(POOL+0x24,struct.pack('<i',0))
            self.vm.mem_write(POOL+0xa4,struct.pack('<i',2))
            self.vm.mem_write(STACK+0x800,struct.pack('<II',STACK+0x3000,0))
            self.vm.reg_write(UC_X86_REG_ESP,STACK+0x800)
            self.vm.reg_write(UC_X86_REG_ECX,POOL)
            self.vm.emu_start(BASE+entry,BASE+0x1bf30,count=60)
            sp=self.vm.reg_read(UC_X86_REG_ESP)
            _,graphic,resource,selected,mode=struct.unpack('<5I',self.vm.mem_read(sp,20))
            self.assertEqual((graphic,resource,selected,mode),(BODY+0x10+2*0x290,23,action,0))
            self.assertEqual(actions[selected]['name'],name)

    def test_original_insert_scalar_and_string_stores(self):
        actor=POOL+0x18
        resources=BODY+0x200
        for identity in (1,4095,4096,16383):
            for size in (0,1,14,15):
                body=bytearray(80)
                struct.pack_into('<I',body,0,identity|(5<<21)|(2<<29))
                struct.pack_into('<I',body,4,27<<8)
                struct.pack_into('<I',body,12,(86<<2)|(71<<17))
                strings=[bytes([65+i])*size for i in range(3)]
                for offset,value in zip((28,44,60),strings):
                    body[offset:offset+len(value)]=value
                body[78:80]=bytes([7,9])
                self.vm.mem_write(BODY,bytes(body))
                self.vm.mem_write(resources,struct.pack('<6H',10,11,12,13,14,15))
                self.vm.mem_write(actor,b'\xa5'*0x268)
                self.vm.mem_write(STACK+0x824,struct.pack('<I',resources))
                self.vm.reg_write(UC_X86_REG_ESP,STACK+0x800)
                self.vm.reg_write(UC_X86_REG_EBP,actor)
                self.vm.reg_write(UC_X86_REG_EBX,BODY)
                self.vm.emu_start(BASE+0xfc2c3,BASE+0xfc3be,count=1000)
                stored=bytes(self.vm.mem_read(actor,0x268))
                self.assertEqual(struct.unpack_from('<I',stored)[0],identity&4095)
                for offset,value in zip((4,20,36),strings):
                    self.assertEqual(stored[offset:offset+16],value+b'\0'+b'\xa5'*(15-size))
                self.assertEqual(struct.unpack_from('<4H',stored,0x34),(27,14,0,1))
                self.assertEqual(struct.unpack_from('<II',stored,0x64),(86,71))
                self.assertEqual(stored[0x7a],5)
                self.assertEqual(stored[0x260],(identity>>12)&3)
                self.assertEqual(stored[0x264:0x266],bytes([7,9]))
                self.assertEqual(bytes(self.vm.mem_read(BODY,80)),bytes(body))

    def test_three_text_fields_preserve_encoded_bytes(self):
        actor=POOL+0x18
        for values in ((b'',b'',b''),
                       (b'PlayerA',b'GroupB',b'TitleC'),
                       (bytes.fromhex('a4a4a4e5'),bytes.fromhex('b4fab8d5'),b'Test'),
                       (bytes(range(0x81,0x90)),b'B'*15,b'C'*15)):
            body=bytearray(80)
            struct.pack_into('<I',body,0,7)
            for offset,value in zip((28,44,60),values):
                body[offset:offset+len(value)]=value
            self.vm.mem_write(BODY,bytes(body))
            self.vm.mem_write(actor,b'\xa5'*0x268)
            self.vm.reg_write(UC_X86_REG_ESP,STACK+0x800)
            self.vm.reg_write(UC_X86_REG_EBP,actor)
            self.vm.reg_write(UC_X86_REG_EBX,BODY)
            self.vm.emu_start(BASE+0xfc2c3,BASE+0xfc33f,count=1000)
            stored=bytes(self.vm.mem_read(actor,0x268))
            for offset,value in zip((4,20,36),values):
                self.assertEqual(stored[offset:offset+16],value+b'\0'+b'\xa5'*(15-len(value)))
            self.assertEqual(stored[52:],b'\xa5'*(0x268-52))
            self.assertEqual(bytes(self.vm.mem_read(BODY,80)),bytes(body))

    def test_remote_text_reaches_three_display_buffers(self):
        actor=POOL+0x18
        display=0x21000000
        self.vm.mem_map(display,0x20000)
        self.vm.mem_map(WORLD+0x1539a000,0x2000)
        # Original setters use handle * ((21*64-1)*32) plus the field offset.
        stride=0xa7e0
        for values in ((b'',b'',b''),(b'PlayerA',b'GroupB',b'TitleC'),
                       (b'A'*14,b'B'*15,bytes.fromhex('a4a4a4e5'))):
            body=bytearray(80)
            struct.pack_into('<I',body,0,7)
            for offset,value in zip((28,44,60),values):
                body[offset:offset+len(value)]=value
            self.vm.mem_write(BODY,bytes(body))
            self.vm.mem_write(actor,b'\0'*0x268)
            self.vm.reg_write(UC_X86_REG_ESP,STACK+0x800)
            self.vm.reg_write(UC_X86_REG_EBP,actor)
            self.vm.reg_write(UC_X86_REG_EBX,BODY)
            self.vm.emu_start(BASE+0xfc2c3,BASE+0xfc33f,count=1000)
            self.vm.mem_write(POOL+8,struct.pack('<I',display))
            self.vm.mem_write(actor+0x48,struct.pack('<H',1))
            self.vm.mem_write(display+stride,b'\xa5'*0x100)
            self.vm.mem_write(display+stride+0x28,struct.pack('<I',1))
            self.vm.mem_write(STACK+0x820,struct.pack('<III',actor+4,actor+20,actor+36))
            self.vm.reg_write(UC_X86_REG_ESP,STACK+0x800)
            self.vm.reg_write(UC_X86_REG_ESI,actor)
            self.vm.reg_write(UC_X86_REG_EDI,POOL)
            self.vm.reg_write(UC_X86_REG_EAX,1)
            self.vm.emu_start(BASE+0xfd427,BASE+0xfd45d,count=3000)
            self.assertEqual(self.vm.reg_read(UC_X86_REG_ESP),STACK+0x800)
            for offset,value in zip((0x70,0x81,0x92),values):
                expected=b' '*max(0,(14-len(value))//2)+value+b'\0'
                actual=bytes(self.vm.mem_read(display+stride+offset,17))
                self.assertEqual(actual,expected+b'\xa5'*(17-len(expected)))
            self.assertEqual(bytes(self.vm.mem_read(BODY,80)),bytes(body))
            remote_labels=bytes(self.vm.mem_read(display+stride+0x70,51))
            # Original local actor name at+B7 reaches the same first setter.
            local_actor=BODY+0x200
            self.vm.mem_write(local_actor,b'\0'*0x100)
            for offset,value in zip((0xb7,0xc7,0x96),values):
                self.vm.mem_write(local_actor+offset,value+b'\0')
            self.vm.mem_write(display+stride+0x70,b'\xa5'*51)
            self.vm.mem_write(WORLD+0x1539ad80,struct.pack('<I',1))
            self.vm.reg_write(UC_X86_REG_ESP,STACK+0x800)
            self.vm.reg_write(UC_X86_REG_ESI,WORLD)
            self.vm.reg_write(UC_X86_REG_EDI,local_actor)
            self.vm.reg_write(UC_X86_REG_EBP,display)
            self.vm.emu_start(BASE+0x1003e0,BASE+0x100422,count=3000)
            self.assertEqual(self.vm.reg_read(UC_X86_REG_ESP),STACK+0x800)
            self.assertEqual(bytes(self.vm.mem_read(display+stride+0x70,51)),remote_labels)

    def test_unterminated_final_string_reads_outside_record(self):
        # Prove the native slice has no field bound, rather than assuming one.
        body=bytearray(80)
        body[60:80]=b'X'*20
        self.vm.mem_write(BODY,bytes(body)+b'Y\0')
        self.vm.mem_write(POOL+0x18,b'\xa5'*0x268)
        self.vm.reg_write(UC_X86_REG_ESP,STACK+0x800)
        self.vm.reg_write(UC_X86_REG_EBP,POOL+0x18)
        self.vm.reg_write(UC_X86_REG_EBX,BODY)
        self.vm.emu_start(BASE+0xfc2c3,BASE+0xfc33f,count=1000)
        self.assertEqual(bytes(self.vm.mem_read(POOL+0x18+36,22)),b'X'*20+b'Y\0')

    def call_native(self,rva,*args):
        self.vm.mem_write(STACK+0x800,struct.pack('<'+'I'*(len(args)+1),STACK+0x3000,*args))
        self.vm.reg_write(UC_X86_REG_ESP,STACK+0x800)
        self.vm.reg_write(UC_X86_REG_ECX,POOL)
        self.vm.emu_start(BASE+rva,STACK+0x3000,count=100000)
        self.assertEqual(self.vm.reg_read(UC_X86_REG_EIP),STACK+0x3000)
        self.assertEqual(self.vm.reg_read(UC_X86_REG_ESP),STACK+0x804+4*len(args))

    def test_original_pool_initializer_matches_live_baseline(self):
        self.vm.mem_write(POOL,b'\xa5'*0x14000)
        self.call_native(0xfabb0,0x11110000,0x22220000,0x33330000,0x1234,0x44440000)
        self.assertEqual(struct.unpack('<III',self.vm.mem_read(POOL,12)),
                         (0x11110000,0x22220000,0x33330000))
        records=bytes(self.vm.mem_read(POOL+0x18,128*0x268))
        self.assertEqual(hashlib.sha256(records).hexdigest(),
                         '0b0ff8a35500703b6280e49875c477203a8309c85c92f8e4bfa8d17ca8cbce3e')
        for index in range(128):
            record=records[index*0x268:(index+1)*0x268]
            self.assertEqual(struct.unpack_from('<I',record)[0],0xffffffff)
            self.assertEqual(record[0xa9:0xab],b'\0\0')
            for offset in (0x3c,0x3e,0x40,0x44,0x46,0x48):
                self.assertEqual(struct.unpack_from('<h',record,offset)[0],-1)
        self.assertEqual(struct.unpack('<III',self.vm.mem_read(POOL+0x13418,12)),(1,1,1))
        self.assertEqual(struct.unpack('<H',self.vm.mem_read(POOL+0x13424,2))[0],0x1234)
        self.assertEqual(struct.unpack('<I',self.vm.mem_read(POOL+0x13428,4))[0],0x44440000)

    def test_complete_update_and_remove_without_render_handles(self):
        self.vm.mem_write(POOL,b'\xff'*0x14000)
        self.vm.mem_write(POOL+0x13418,struct.pack('<II',1,1))
        actor=POOL+0x18+63*0x268
        self.vm.mem_write(actor,struct.pack('<I',1234))
        self.vm.mem_write(actor+0x60,b'\0\0')
        self.vm.mem_write(actor+0x64,struct.pack('<II',86,71))
        self.vm.mem_write(actor+0xa8,b'\0'*324)
        before=bytes(self.vm.mem_read(POOL,0x14000))
        body=struct.pack('<III',1234,0,87|(72<<11))
        self.vm.mem_write(BODY,body)
        self.call_native(0xfb520,BODY+0x200,BODY)
        updated=bytes(self.vm.mem_read(POOL,0x14000))
        offset=actor-POOL
        self.assertEqual(updated[:offset],before[:offset])
        self.assertEqual(updated[offset+0x268:],before[offset+0x268:])
        self.assertEqual(struct.unpack_from('<II',updated,offset+0x6c),(86,71))
        self.assertEqual(updated[offset+0xa9:offset+0xab],b'\0\1')
        self.assertEqual(struct.unpack_from('<II',updated,offset+0xac),(87,72))
        for index in range(1,39):
            self.vm.mem_write(BODY,struct.pack('<III',1234,0,(87+index)|(72<<11)))
            self.call_native(0xfb520,BODY+0x200,BODY)
        ring=bytes(self.vm.mem_read(actor+0xa8,324))
        self.assertEqual(ring[1:3],b'\0\x27')
        for index in range(39):
            self.assertEqual(struct.unpack_from('<II',ring,4+8*index),(87+index,72))
        self.vm.mem_write(BODY,struct.pack('<III',1234,0,999|(999<<11)))
        self.call_native(0xfb520,BODY+0x200,BODY)
        self.assertEqual(bytes(self.vm.mem_read(actor+0xa8,324)),ring)
        # Cleanup is mode-sensitive: mode0 does not free the identity slot.
        self.vm.mem_write(POOL+0x13418,struct.pack('<I',0))
        self.call_native(0xfb4f0,BODY)
        self.assertEqual(struct.unpack('<I',self.vm.mem_read(actor,4))[0],1234)
        self.vm.mem_write(POOL+0x13418,struct.pack('<I',1))
        before=bytes(self.vm.mem_read(POOL,0x14000))
        self.call_native(0xfb4f0,BODY)
        removed=bytes(self.vm.mem_read(POOL,0x14000))
        self.assertEqual(struct.unpack_from('<I',removed,offset)[0],0xffffffff)
        self.assertEqual(removed[:offset],before[:offset])
        self.assertEqual(removed[offset+0x268:],before[offset+0x268:])
        self.call_native(0xfb4f0,BODY)
        self.assertEqual(bytes(self.vm.mem_read(POOL,0x14000)),removed)
        self.call_native(0xfb520,BODY+0x200,BODY)
        self.assertEqual(bytes(self.vm.mem_read(POOL,0x14000)),removed)


if __name__=='__main__':
    unittest.main()
