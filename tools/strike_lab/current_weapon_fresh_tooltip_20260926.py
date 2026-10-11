"""Fresh native WPN tooltip formatting, with original CP950 display resources.

Synthetic20byte instances, no gameplay grant/formula claim. No game callee stubs.
Native widget exists, but its renderer handle is explicitly absent: formatted
text/widget state evidence is not final graphical or live-client acceptance.
"""
import hashlib
import json
import struct

from .current_equipment_projection_20260926 import (
    Oracle, NativeItemMetadata, ROOT, BASE, UI, SLOTS, DEFINITIONS, LENGTH, QUEUE,
    RETURN, PIN, require, pefile, uc, x, decode_csvz)

MESSAGES=0x4500000
MESSAGE_SHA='5cd34cce66feae96d947cd45e32984765ce625673c0fb19c73cb63d7d9178598'
DECODED_SHA='370bd6ed9b4892f57190fc7a8dab14061b3e844b0aa9d0171611a9cbab61b5f8'
# These are explicit CUSTOM_TEST_NOT_NATIVE inputs, not native-generated gear.
INSTANCES={1:bytes.fromhex('0100010000000018000000000600000000000000'),
           2:bytes.fromhex('020001000000001e000000000a00000000000000')}


class FreshTooltip(Oracle):
    def __init__(self,image,definitions):
        self.formatted=[];self.weapon_frames=[];self.weapon_output=[];self.fresh_visits=set()
        super().__init__(image,definitions)
        v=self.vm
        raw=(ROOT.parent/'God2/Data2/Patch/Comm/message.csvZ').read_bytes()
        require(hashlib.sha256(raw).hexdigest()==MESSAGE_SHA,'Message source identity')
        plain=decode_csvz(raw)
        require(hashlib.sha256(plain).hexdigest()==DECODED_SHA,'Message decoded identity')
        lines=plain.splitlines();start=lines.index(b'ProgramMsg,1080')
        v.mem_map(MESSAGES,0x40000);pointer=MESSAGES+0x10000
        for index,line in enumerate(lines[start+1:start+1081]):
            key,_,text=line.partition(b',')
            require(int(key)==index+1 and b'\0' not in text,'ProgramMsg row shape')
            v.mem_write(MESSAGES+index*4,struct.pack('<I',pointer))
            v.mem_write(pointer,text+b'\0');pointer+=len(text)+1
        require(pointer<=MESSAGES+0x40000,'Message buffer bound')
        v.mem_protect(DEFINITIONS,0xe0000,3)
        v.mem_write(DEFINITIONS+0xb2c68,struct.pack('<I',MESSAGES))
        v.mem_write(DEFINITIONS+0xb2c6c,struct.pack('<h',1080))
        v.mem_protect(DEFINITIONS,0xe0000,1);v.mem_protect(MESSAGES,0x40000,1)
        # Tooltip widget1 is real native state; text formatting occurs even
        # with renderer handleFFFF (no DirectDraw/font device object).
        v.mem_write(UI+0x232e56,struct.pack('<h',1))
        self.tooltip_node=UI+0xe2988+0x2a08
        v.mem_write(self.tooltip_node,struct.pack('<H',0x11))
        v.mem_write(self.tooltip_node+4,b'\xff\xff')
        v.mem_write(self.tooltip_node+0x28,struct.pack('<i',-1))
        v.mem_write(UI+0x855f0,b'\xff\xff')

    def cstring(self,pointer,bound):
        value=bytes(self.vm.mem_read(pointer,bound));end=value.find(b'\0')
        require(end>=0,'Unterminated native formatting result')
        return value[:end]

    def observe(self,v,address,size,context):
        super().observe(v,address,size,context)
        self.fresh_visits.add(address-BASE)
        sp=v.reg_read(x.UC_X86_REG_ESP)
        if address==BASE+0xb4200:
            ret=struct.unpack('<I',v.mem_read(sp,4))[0]
            destination=struct.unpack('<I',v.mem_read(sp+20,4))[0]
            self.weapon_frames.append((ret,destination))
        if self.weapon_frames and address==self.weapon_frames[-1][0]:
            _,destination=self.weapon_frames.pop()
            self.weapon_output.append(self.cstring(destination,1024))
        # Exact instruction after original vsprintf returns, before args pop.
        if address==BASE+0x107822:
            destination=struct.unpack('<I',v.mem_read(sp,4))[0]
            self.formatted.append(dict(control=v.reg_read(x.UC_X86_REG_EBX)&65535,
                raw_hex=self.cstring(destination,512).hex()))

    def fresh(self,key,slot,event=0):
        data=INSTANCES[key];self.put(slot,data)
        v=self.vm;before=bytes(v.mem_read(SLOTS,1200))
        # Explicit cache miss, never seed matching cached tooltip metadata.
        v.mem_write(BASE+0x1b7830,b'\xff\xff')
        v.mem_write(BASE+0x1b7838,b'\xa5'*20)
        v.mem_write(self.tooltip_node,struct.pack('<H',0x11))
        v.mem_write(LENGTH,bytes(4));v.mem_write(QUEUE,b'\xa5'*16)
        self.formatted=[];self.weapon_output=[];self.fresh_visits=set()
        self.call(0x9a330,slot,event,budget=500000)
        require(not self.weapon_frames,'Weapon formatter failed to return')
        require({0x9a330,0x9b820,0xb5be0,0xb4dd0,0xb4060,0xb45b0,0xb4200,
                 0x147af7,0x146cf7,0x1077c0,0xb4ed0}.issubset(self.fresh_visits),'Fresh native branch missing')
        require(len(self.weapon_output)==1 and len(self.weapon_output[0])>0,'No complete fresh WPN output')
        require(bytes(v.mem_read(BASE+0x1b7838,20))==data,'Fresh cache20bytes mismatch')
        require(struct.unpack('<H',v.mem_read(BASE+0x1b7830,2))[0]==key,'Fresh cache key mismatch')
        require(struct.unpack('<H',v.mem_read(BASE+0x1926b0,2))[0]==0x12,'Tooltip display type')
        require(struct.unpack('<H',v.mem_read(self.tooltip_node,2))[0]&0x20,'Tooltip widget did not open')
        require(bytes(v.mem_read(SLOTS,1200))==before,'Hover/click changed inventory before response')
        length=struct.unpack('<I',v.mem_read(LENGTH,4))[0]
        expected=struct.pack('<BHBB',0x28,key,slot,1) if event==4 else b''
        require(length==len(expected) and bytes(v.mem_read(QUEUE,len(expected)))==expected,'Unexpected request from tooltip')
        texts=[bytes.fromhex(row['raw_hex']) for row in self.formatted]
        require(any(('菜刀' if key==1 else '砍刀').encode('cp950') in value for value in texts),'Original WPN name not formatted')
        require('物攻'.encode('cp950') in self.weapon_output[0] and '魔攻'.encode('cp950') in self.weapon_output[0],
                'Original ProgramMsg stat labels not formatted')
        expected_text=('/c6品質:+0\n能力總和\n物攻:+19 ~ +29\n魔攻:+3 ~ +9/c9' if key==1 else
                       '/c6品質:+0\n能力總和\n物攻:+25 ~ +35\n魔攻:+7 ~ +13/c9').encode('cp950')
        require(self.weapon_output[0]==expected_text,'Native WPN formatting content changed')
        require(any(('等級限定(1級)' if key==1 else '等級限定(10級)').encode('cp950')==value for value in texts),
                'Native WPN source level text changed')
        return dict(key=key,slot=slot,event=event,instance_hex=data.hex(),fresh_cache_miss=True,
            native_return=True,widget_open=True,formatter_hex=self.weapon_output[0].hex(),
            formatter_cp950=self.weapon_output[0].decode('cp950'),formatted_controls=self.formatted,
            request_hex=expected.hex(),graphical_blit_tested=False)


def verify():
    raw=(ROOT.parent/'God2/God2.exe').read_bytes()
    require(hashlib.sha256(raw).hexdigest()==PIN,'Current PE identity mismatch')
    image=pefile.PE(data=raw).get_memory_mapped_image()
    loader=NativeItemMetadata()
    require(all(image[a:b]==loader.image[a:b] for a,b in loader.CODE),'Native metadata code mismatch')
    definitions={key:loader.item_row('WPN',key-1) for key in INSTANCES}
    n=FreshTooltip(image,definitions)
    cases=[n.fresh(key,slot,event) for key in INSTANCES for slot in (0,1,34) for event in (0,4)]
    return dict(status='PASS',current_pe_sha256=PIN,message_sha256=MESSAGE_SHA,message_decoded_sha256=DECODED_SHA,
        cases=cases,count=len(cases),instance_origin='CUSTOM_TEST_NOT_NATIVE',native_game_stubs=0,
        scope='Fresh hover and double-click complete native return, real ProgramMsg formatting, opened tooltip widget with absent renderer. No live graphical acceptance, formula, instance generation or grant.')


if __name__=='__main__':print(json.dumps(verify(),ensure_ascii=False,indent=2))
