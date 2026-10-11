"""Current PE complete equipment consumers and cached-tooltip UI producer.

Synthetic owned instances; no game process/DB/network. No game callee stubs.
Only imported WinMM timeGetTime is adapted. Sound uses the original constructor's
absent-device state. Actual WPN ROM chunks feed enabled native sprite controls;
the ROM file loader and final display-device blit are outside this oracle.
"""
from pathlib import Path
import hashlib
import json
import struct
import sys

from .current_item_metadata import NativeItemMetadata
from .current_item_transition import (
    NativeItemTransition, BASE, UI, SLOTS, STACK, SP, RETURN, PACKET,
    COMPANION, DEFINITIONS, LENGTH, QUEUE, UC_PROT_READ, UC_PROT_WRITE)
from .current_equipment_20260926 import PIN, require
from .omega_assets import decode_csvz
from .current_four_stat_ui_binding import parse_rom
import pefile
import unicorn as uc
from unicorn import x86_const as x

ROOT=Path(__file__).resolve().parents[2]
SOUND, API=0x3900000,0x3920000
RENDER, SPRITES, BANKS, ASSETS=0x3a00000,0x3b00000,0x3c00000,0x3d00000


def instance(key, item_class, salt):
    """Arbitrary test input, not an original player instance or grant rule."""
    return struct.pack('<HH',key,item_class)+bytes((salt+i*7)&255 for i in range(16))


def sound_sources():
    root=ROOT.parent/'God2/Data2/Snd'
    raw=(root/'commsnd.csvZ').read_bytes();plain=decode_csvz(raw)
    require(hashlib.sha256(raw).hexdigest()=='e5704115a5ec39cd97f9712dd5bfb1163e502671faaae65d7f45d9e541a11f0d','Sound source pin')
    require(hashlib.sha256(plain).hexdigest()=='b34f206476b0b307fdbc153b1322c680698fc3bf41f29102a4aa1c1a8cc6dc5f','Sound decoded pin')
    lines=plain.splitlines();result=[]
    for key,name,pin in ((669,'ItemEquip.wav','f52f5b7d06c7f83f2c7be8bab885af78c0e90b502119968d1f8d345a838e91ea'),
                         (670,'ItemPlace.wav','b0c8e1b4aabb7f30710e754b2fb245194bfd0e561f3a640127b26aa12377d766')):
        require(lines[key+2]==f'{key},{name}'.encode(),'Sound source row')
        data=(root/name).read_bytes()
        require(hashlib.sha256(data).hexdigest()==pin and data[:4]==b'RIFF' and data[8:12]==b'WAVE','Sound WAV pin/header')
        result.append(dict(key=key,source_line=key+3,name=name,sha256=pin,bytes=len(data)))
    return result


class Oracle(NativeItemTransition):
    def __init__(self, image, definitions):
        super().__init__()
        old=(len(self.image)+4095)&~4095
        if len(image)>old:self.vm.mem_map(BASE+old,((len(image)+4095)&~4095)-old)
        self.image=image
        v=self.vm
        v.mem_write(BASE,image)
        # Writable original data only; code bytes are never changed.
        v.mem_protect(BASE+0x170000,0x60000,UC_PROT_READ|UC_PROT_WRITE)
        v.mem_map(0,4096) # explicit x86 TEB/SEH head, FS base=0
        v.mem_map(SOUND,0x16000)
        v.mem_map(API,4096)
        v.mem_write(UI+0xcff5c,struct.pack('<I',SOUND))
        v.mem_write(BASE+0x1707bc,struct.pack('<I',API))
        v.mem_protect(DEFINITIONS,0xe0000,UC_PROT_READ|UC_PROT_WRITE)
        for ordinal,(key,d) in enumerate(definitions.items()):
            at=COMPANION+0x1000+ordinal*0x1000
            v.mem_write(at,d['record'])
            v.mem_write(DEFINITIONS+0xb2d40+4*key,struct.pack('<I',at))
        v.mem_protect(DEFINITIONS,0xe0000,UC_PROT_READ)
        for offset in (0x232dc8,0x232dd6,0x232dfe,0x232dea,0x232e20,0x232e66):
            v.mem_write(UI+offset,b'\xff\xff')
        v.mem_write(UI+0x85abd,b'\xff');v.mem_write(UI+8,b'\xff')
        v.mem_write(UI+0x85608,bytes(4))
        self.pcs=set();self.sound_calls=[];self.os_calls=0
        v.hook_add(uc.UC_HOOK_CODE,self.observe)
        self.call(0x4d9f0,this=SOUND)
        require(bytes(v.mem_read(SOUND,4))==bytes(4) and bytes(v.mem_read(SOUND+0x7f19,1))==b'\x01',
                'Native sound constructor absent-device state')
        self.install_icons()

    def install_icons(self):
        """Relocate original ROM chunks into the native read-only resource layout.

        Tests the original binder, action lookup and sprite refresh, not the
        ROM file loader, decompressor or display-device blitter.
        """
        raw=(ROOT.parent/'God2/Data2/ItmImg/WPN01.romZ').read_bytes()
        require(hashlib.sha256(raw).hexdigest()=='caa72d4dccafacd44a27346f3a8db2e15319960bf003966b835416ed6c189499','WPN ROM pin')
        plain=decode_csvz(raw)
        require(hashlib.sha256(plain).hexdigest()=='eef95acad680643cdf07f570f124a273f7dfe112061596ef074736732ff9395f','WPN decoded pin')
        rom=parse_rom(plain,name_encoding='cp950');require(len(rom['actions'])==180,'WPN action count')
        v=self.vm
        for address,size in ((RENDER,0x1000),(SPRITES,0x10000),(BANKS,0x60000),(ASSETS,0x800000)):
            v.mem_map(address,size)
        self.asset_top=ASSETS
        def store(data):
            at=self.asset_top;self.asset_top+=(len(data)+15)&~15
            require(self.asset_top<=ASSETS+0x800000,'Asset fixture budget');v.mem_write(at,data);return at
        bank=BANKS+0x41*0x1514
        for i,palette in enumerate(rom['palettes']):v.mem_write(bank+8+4*i,struct.pack('<I',store(palette['data'])))
        images={}
        self.icon_headers=[];self.icon_images=[]
        v.mem_write(bank+0x108c,struct.pack('<I',2))
        for ordinal,action in enumerate(rom['actions'][:2]):
            require(action['meta'][0]==ordinal+1 and len(action['steps'])==1,'WPN action identity')
            header=bytearray(0x640);header[:48]=action['data']
            struct.pack_into('<I',header,0x30,store(action['steps'][0]['data']))
            for pool_id,pool in enumerate(action['pools']):
                struct.pack_into('<I',header,0x630+4*pool_id,store(pool['data']))
                image_id=struct.unpack_from('<H',pool['data'],6)[0]
                if image_id not in images:images[image_id]=store(rom['images'][image_id]['data'])
                v.mem_write(bank+0x8c+4*image_id,struct.pack('<I',images[image_id]))
            ptr=store(bytes(header));self.icon_headers.append(ptr)
            self.icon_images.append(images[struct.unpack_from('<H',action['pools'][0]['data'],6)[0]])
            v.mem_write(bank+0x1090+4*ordinal,struct.pack('<I',ptr))
        v.mem_write(RENDER+4,struct.pack('<II',SPRITES,0))
        v.mem_write(RENDER+0xc,struct.pack('<I',BANKS))
        v.mem_write(UI+0xcff60,struct.pack('<I',RENDER))
        v.mem_write(UI+0xe2178,struct.pack('<I',RENDER))
        v.mem_write(UI+0x232dc8,bytes(2))
        node=UI+0xe2988;v.mem_write(node,struct.pack('<H',0x21));v.mem_write(node+4,bytes(2))
        v.mem_write(RENDER+0x10+0xe,b'\xff\xff')
        for slot in range(50):
            v.mem_write(node+0xa0+slot*100,b'\x01')
            v.mem_write(RENDER+0x10+0xac+slot*2,struct.pack('<H',slot))
            v.mem_write(SPRITES+0x1258+slot*200,b'\x03')
        # Native481700 applies+0x41 and searches actual ACT_DATA key IDs.
        v.mem_protect(DEFINITIONS,0xe0000,UC_PROT_READ|UC_PROT_WRITE)
        self.call(0x81700,budget=500000)
        v.mem_protect(DEFINITIONS,0xe0000,UC_PROT_READ)
        for ordinal in range(2):
            d=COMPANION+0x1000+ordinal*0x1000
            require(struct.unpack('<HH',v.mem_read(d+0x116,4))==(0x41,ordinal),'Native WPN icon binding')
        v.mem_protect(BANKS,0x60000,UC_PROT_READ);v.mem_protect(ASSETS,0x800000,UC_PROT_READ)

    def observe(self,v,address,size,_):
        if address==API:
            sp=v.reg_read(x.UC_X86_REG_ESP)
            ret=struct.unpack('<I',v.mem_read(sp,4))[0]
            v.reg_write(x.UC_X86_REG_EAX,123456)
            v.reg_write(x.UC_X86_REG_ESP,sp+4);v.reg_write(x.UC_X86_REG_EIP,ret)
            self.os_calls+=1
            return
        if address==RETURN:return
        require(BASE<=address<BASE+0x170000,f'Unexpected non-native execution {address:x}')
        self.pcs.add(address-BASE)
        if address==BASE+0x4e140:
            sp=v.reg_read(x.UC_X86_REG_ESP)
            self.sound_calls.append(struct.unpack('<I',v.mem_read(sp+4,4))[0])

    def call(self,entry,*args,this=UI,budget=100000):
        v=self.vm
        v.mem_write(SP,struct.pack('<'+'I'*(len(args)+1),RETURN,*args))
        v.reg_write(x.UC_X86_REG_ESP,SP);v.reg_write(x.UC_X86_REG_ECX,this)
        v.reg_write(x.UC_X86_REG_EFLAGS,2)
        if budget==100000:self._run(entry,RETURN-BASE)
        else:
            self.writes.clear();v.emu_start(BASE+entry,RETURN,count=budget)
            require(v.reg_read(x.UC_X86_REG_EIP)==RETURN,'Native instruction budget exhausted')
        require(v.reg_read(x.UC_X86_REG_ESP)==SP+4*(len(args)+1),'Unbalanced native return')

    def pending(self):return struct.unpack('<I',self.vm.mem_read(UI+0x85608,4))[0]

    def set_pending(self,value):self.vm.mem_write(UI+0x85608,struct.pack('<I',value))

    def put(self,slot,value,count=1):
        require(len(value)==20,'instance width')
        self.vm.mem_write(SLOTS+24*slot,bytes([count])+bytes(3)+value)

    def record(self,slot):return bytes(self.vm.mem_read(SLOTS+24*slot,24))

    def consume(self,record):
        require(len(record)>=4 and record[0] in (0x3b,0x41,0x3c),'oracle opcode/width')
        entry,size,slot={0x3b:(0x98dd0,25,record[2]),0x41:(0x991e0,5,record[3]),
                         0x3c:(0x98fd0,5,record[3])}[record[0]]
        require(len(record)==size and 0<=slot<37,'oracle record scope')
        before=bytes(self.vm.mem_read(SLOTS,1200))
        self.vm.mem_write(PACKET,record[1:]);self.call(entry,PACKET)
        after=bytes(self.vm.mem_read(SLOTS,1200))
        require(before[:slot*24]==after[:slot*24] and before[(slot+1)*24:]==after[(slot+1)*24:],
                'Consumer modified another slot')
        for address,length in self.writes:
            require(any(lo<=address and address+length<=hi for lo,hi in (
                (STACK,STACK+0x4000),(SLOTS+24*slot,SLOTS+24*(slot+1)),
                (UI+0x85608,UI+0x8560c),(SOUND+0x7f0c,SOUND+0x7f10),(0,4),
                (RENDER+0x10+0x180+slot*2,RENDER+0x10+0x182+slot*2),
                (SPRITES+0x1258+slot*200,SPRITES+0x1320+slot*200))),
                f'Consumer unexpected write {address:x}+{length}')
        occupied=self.record(slot)[0]!=0
        require(bytes(self.vm.mem_read(SPRITES+0x1258+slot*200,1))==bytes([2 if occupied else 3]),'Sprite show/hide state')
        if occupied:
            key=struct.unpack_from('<H',self.record(slot),4)[0]
            require(struct.unpack('<I',self.vm.mem_read(SPRITES+0x12e4+slot*200,4))[0]==self.icon_images[key-1],'Sprite points to wrong original WPN image')

    def ui_request(self,slot):
        """Complete49A330 with the exact previously hovered tooltip cache.

        This legitimate cache-hit branch does not exercise fresh tooltip text
        formatting/resource drawing. Cache coordinates derive from current PE.
        """
        data=self.record(slot)[4:]
        before=bytes(self.vm.mem_read(SLOTS,1200))
        key=struct.unpack_from('<H',data)[0]
        # y is table+4, not the intervening padding word.
        px=struct.unpack_from('<h',self.image,0x1901c0+16*slot)[0]
        py=struct.unpack_from('<h',self.image,0x1901c4+16*slot)[0]
        self.vm.mem_write(BASE+0x1b6810,bytes(8))
        self.vm.mem_write(BASE+0x1926b2,struct.pack('<hh',px,py))
        self.vm.mem_write(BASE+0x1b7830,struct.pack('<H',key))
        self.vm.mem_write(BASE+0x1b7838,data)
        self.vm.mem_write(LENGTH,struct.pack('<I',3))
        self.vm.mem_write(QUEUE,b'PRE'+b'\xa5'*16)
        self.call(0x9a330,slot,4)
        require(struct.unpack('<I',self.vm.mem_read(LENGTH,4))[0]==8,'UI did not append5bytes')
        expected=struct.pack('<BHBB',0x28,key,slot,1)
        require(bytes(self.vm.mem_read(QUEUE,19))==b'PRE'+expected+b'\xa5'*11,'UI queue/canary')
        require(self.pending()==1,'Producer pending')
        require(bytes(self.vm.mem_read(BASE+0x1b7838,20))==data,'Tooltip cache instance changed')
        require(bytes(self.vm.mem_read(SLOTS,1200))==before,'UI request mutated inventory before response')
        return expected.hex()


def clear(slot,opcode=0x41):return struct.pack('<BHBB',opcode,0,slot,0 if opcode==0x41 else 1)
def full(slot,value):return bytes([0x3b,1,slot,0xa5,0x5a])+value
def absolute(slot,key):return struct.pack('<BHBB',0x41,key,slot,1)


def verify():
    raw=(ROOT.parent/'God2/God2.exe').read_bytes()
    require(hashlib.sha256(raw).hexdigest()==PIN,'Current PE identity mismatch')
    image=pefile.PE(data=raw).get_memory_mapped_image()
    loader=NativeItemMetadata()
    require(all(image[a:b]==loader.image[a:b] for a,b in loader.CODE),'Source parser code mismatch')
    definitions={key:loader.item_row('WPN',key-1) for key in (1,2)}
    require(all(d['record'][0x11a]&4 and not d['record'][0x11b]&1 for d in definitions.values()),'Weapon flags')
    n=Oracle(image,definitions)
    checks=0;requests=[];transitions=[]
    for opcode in (0x41,0x3c):
        for bag in (0,12,29):
            for item_class in (1,0x8041,0xffff):
                a=instance(1,item_class,7);b=instance(2,item_class,19)
                n.put(bag,a);n.put(34,bytes(20),0)
                # Equip: remove bag, add actual complete equipment instance.
                requests.append(n.ui_request(bag));n.consume(clear(bag,opcode));n.consume(full(34,a));n.consume(absolute(34,1))
                require(n.record(34)==b'\x01\0\0\0'+a and n.record(bag)[0]==0,'Equip state')
                require(n.pending()==0,'Equip pending clear after native audio return')
                # Swap two different nonzero instances, preserving each20bytes.
                n.put(bag,b);requests.append(n.ui_request(bag))
                n.consume(clear(bag,opcode));n.consume(clear(34,opcode));n.consume(full(bag,a));n.consume(absolute(bag,1))
                n.consume(full(34,b));n.consume(absolute(34,2))
                require(n.record(bag)==b'\x01\0\0\0'+a and n.record(34)==b'\x01\0\0\0'+b,'Swap state')
                require(n.pending()==0,'Swap pending')
                # Unequip to a genuinely empty different bag; no fake occupied34.
                target=(bag+1)%30;n.put(target,bytes(20),0)
                requests.append(n.ui_request(34));n.consume(clear(34,opcode));n.consume(full(target,b));n.consume(absolute(target,2))
                require(n.record(target)==b'\x01\0\0\0'+b,'Unequip full instance')
                require(n.record(34)==b'\0\0\0\0\0\0'+b[2:],'Empty slot keeps native stale tail')
                require(n.pending()==1,'Unequip pending must remain1')
                # Native UI permits subsequent equip despite retained pending.
                requests.append(n.ui_request(target));n.consume(clear(target,opcode));n.consume(full(34,b));n.consume(absolute(34,2))
                require(n.pending()==0 and n.record(34)[4:]==b,'Subsequent equip')
                checks+=4
                transitions.append(dict(clear_opcode=opcode,bag=bag,synthetic_class=item_class,
                                        a=a.hex(),b=b.hex(),unequip_pending=1))
    # Native equipment3C is a clear regardless of its key/count fields.
    clears=0
    for key in (0,1,2,65535):
        for count in (0,1,127,255):
            m=instance(2,1,23);n.put(34,m);n.set_pending(1)
            n.consume(struct.pack('<BHBB',0x3c,key,34,count))
            require(n.record(34)==bytes(6)+m[2:] and n.pending()==1,'Equipment3C ignores key/count')
            clears+=1
    # HighWORD0 also routes28. Nonzero class is not a producer prerequisite.
    n.put(12,instance(1,0,0));requests.append(n.ui_request(12))
    require({0x98dd0,0x98fd0,0x991e0,0x9b850,0x9b720,0x59a60,0x4d9f0,0x4e140,0x4db90,
             0x4e320,0x9a330,0x9b820,0xb5be0,0x96550,0x132e0,0x81700,0x1ae70,
             0x1068c0,0x1ea00,0x1e710,0x27160,0x271e0}.issubset(n.pcs),'Missing native callee')
    return dict(status='PASS',current_pe_sha256=PIN,transitions=checks,ui_requests=len(requests),equipment_clear_cases=clears,
                requests=requests,cases=transitions,sound_calls=n.sound_calls,os_time_calls=n.os_calls,
                definition_rows={str(k):dict(source_line=d['source_line'],flags=d['record'][0x11a:0x11c].hex(),
                    record_sha256=hashlib.sha256(d['record']).hexdigest()) for k,d in definitions.items()},
                native_callee_stubs=0,os_adapters=['WinMM.timeGetTime'],sound_sources=sound_sources(),
                original_icon_bindings={'1':[0x41,0],'2':[0x41,1]},
                scope='Synthetic instance preservation; actual ROM chunks, native binder/action/sprite refresh; native sound constructor absent-device state; cached tooltip UI branch. No file-loader/blit/audio/server acceptance.')


if __name__=='__main__':
    print(json.dumps(verify(),indent=2))
