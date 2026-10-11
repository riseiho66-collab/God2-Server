"""Current daily-panel source-backed display and request boundaries.

No gameplay/quest grant authority, process/UI interaction or game callee stubs.
Source records are relocated; native CSV loading is outside this oracle.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from .current_weapon_fresh_tooltip_20260926 import FreshTooltip, MESSAGES
from .current_equipment_projection_20260926 import (
    NativeItemMetadata, ROOT, PIN, require, pefile, BASE, UI, COMPANION,
    DEFINITIONS, PACKET, SP, LENGTH, QUEUE, x)
from .omega_assets import decode_csvz
from unicorn import UC_HOOK_CODE

DAILY = 0x66000000
SOURCE_SHA = '4a347d56706946d7004b2bd2118500ffc60844628fa461862b2f6d5320a90e54'


def source_row():
    raw = (ROOT.parent/'God2/Data2/Patch/Comm/DayMissionDesc.csvZ').read_bytes()
    require(hashlib.sha256(raw).hexdigest() == SOURCE_SHA, 'Daily source SHA')
    decoded = decode_csvz(raw)
    lines = decoded.splitlines(); start = lines.index(b'DailyMisDescNum,85')
    line = lines[start+1]; cells = line.split(b',')
    require(len(cells) == 19, 'Qualified source row width')
    row = bytearray(316)
    row[:2] = bytes([int(cells[0]), int(cells[1])])
    for offset, column in ((2,3),(4,10),(6,5),(8,6),(10,8),(12,9)):
        struct.pack_into('<H', row, offset, int(cells[column]))
    row[14] = int(cells[7].lower() == b'r'); row[15] = int(cells[18])
    require(len(cells[4]) == 8, 'Native weekday width')
    struct.pack_into('<I', row, 16, sum(1 << i for i in range(7) if cells[4][i+1:i+2] == b'1'))
    for offset, column, width in ((20,2,30),(50,11,20),(70,12,41),(111,13,41),
                                  (152,14,41),(193,15,41),(234,16,41),(275,17,41)):
        require(len(cells[column]) < width, 'Source text width')
        row[offset:offset+len(cells[column])] = cells[column]
    return bytes(row), dict(source_sha256=SOURCE_SHA, decoded_sha256=hashlib.sha256(decoded).hexdigest(),
        line=start+2, raw_hex=line.hex(), row_sha256=hashlib.sha256(line).hexdigest(),
        fields=[c.decode('cp950') for c in cells])


class DailyOracle(FreshTooltip):
    def __init__(self, image, definitions, row):
        self.grid=[];self.grid_frames=[];self.controls=[]
        super().__init__(image, definitions)
        v=self.vm
        v.mem_map(DEFINITIONS+0xe0000,0x20000)
        v.mem_map(DAILY,0x10000);v.mem_write(DAILY,row)
        v.mem_write(DEFINITIONS+0xfc2dc,struct.pack('<HHI',1,0,DAILY))
        v.mem_write(COMPANION+0xdc,struct.pack('<I',UI))
        for off in (0x232dd8,0x232e68,0x232e74):v.mem_write(UI+off,b'\xff\xff')
        v.mem_write(UI+0x232e00,struct.pack('<h',2))
        node=UI+0xe2988+2*0x2a08
        v.mem_write(node,b'\x11\0');v.mem_write(node+4,b'\xff\xff')
        for col in range(5):v.mem_write(node+0xa0+100*col,b'\x21')
        self.call(0x8b6c0,this=COMPANION)

    def observe(self,v,address,size,context):
        super().observe(v,address,size,context)
        sp=v.reg_read(x.UC_X86_REG_ESP)
        if address==0x506ad0:
            widget,control,disabled=struct.unpack('<III',v.mem_read(sp+4,12))
            self.controls.append((widget&65535,control,disabled))
        if address==0x546cf7:
            ret,dest=struct.unpack('<II',v.mem_read(sp,8))
            self.grid_frames.append((ret,dest))
        if self.grid_frames and address==self.grid_frames[-1][0]:
            _,dest=self.grid_frames.pop()
            self.grid.append(self.cstring(dest,512).hex())

    def queue(self):
        n=struct.unpack('<I',self.vm.mem_read(LENGTH,4))[0]
        require(n<100,'Queue bound');return bytes(self.vm.mem_read(QUEUE,n)).hex()

    def reset_queue(self):self.vm.mem_write(LENGTH,bytes(4))

    def bounded(self,start,stop,budget=50000):
        hook=self.vm.hook_add(UC_HOOK_CODE,lambda v,a,s,c:v.emu_stop(),begin=stop,end=stop)
        try:self.vm.emu_start(start,stop,count=budget)
        finally:self.vm.hook_del(hook)
        require(self.vm.reg_read(x.UC_X86_REG_EIP)==stop,'Exact native slice stop/budget')


def verify():
    raw=(ROOT.parent/'God2/God2.exe').read_bytes()
    require(hashlib.sha256(raw).hexdigest()==PIN,'Current PE SHA')
    image=pefile.PE(data=raw).get_memory_mapped_image()
    row,source=source_row();loader=NativeItemMetadata()
    n=DailyOracle(image,{k:loader.item_row('WPN',k-1) for k in (1,2)},row)
    v=n.vm;lists=[]
    v.mem_write(SP,struct.pack('<II',BASE+0x1000,PACKET))
    v.reg_write(x.UC_X86_REG_ESP,SP)
    n.bounded(0x415ce0,BASE+0x1000)
    require(struct.unpack('<II',v.mem_read(PACKET+4*0xd7,8))==(2,9),'Original D7/D8 logical lengths')
    # Actual original table-to-ProgramMsg pointer initialization, bounded before
    # widget creation (we qualify display/requests, not original UI allocation).
    v.reg_write(x.UC_X86_REG_ESI,COMPANION);v.reg_write(x.UC_X86_REG_ESP,SP)
    n.bounded(0x48aeb3,0x48af0a,10000)
    require(v.reg_read(x.UC_X86_REG_EIP)==0x48af0a,'Label initialization slice budget')
    labels={}
    for address,expected in ((0x5b6660,950),(0x5b6680,950),(0x5b66a8,951),(0x5b66ac,952)):
        source_id=struct.unpack_from('<H',image,0x18f2ec+(address-0x5b65f8)//2)[0]
        require(source_id==expected,'Button source-ID join')
        pointer=struct.unpack('<I',v.mem_read(address,4))[0]
        labels[hex(address)]={'program_message':source_id,'text':n.cstring(pointer,512).decode('cp950')}
    for count in (0,1,8,9,39,40):
        payload=bytearray(168)
        for i in range(count):payload[i*4:i*4+4]=row[:2]+bytes([i,0x41])
        payload[160]=count
        # Both auxiliary features explicitly disabled. No reward/buy synthesis.
        wire=bytes([0xfd,172,0,2])+payload
        v.mem_write(PACKET,wire);n.grid.clear();n.formatted.clear()
        n.call(0x858b0,0xfd,PACKET+1,budget=500000)
        require(bytes(v.mem_read(COMPANION+0x20f32,4*count))==payload[:4*count],'List entries')
        require(struct.unpack('<I',v.mem_read(COMPANION+0x20f2c,4))[0]==max(1,(count+7)//8),'List page count')
        require(not n.grid_frames,'Formatter return')
        if count:
            require(any(source['fields'][2].encode('cp950') in bytes.fromhex(s) for s in n.grid),'Actual source name formatting')
        lists.append(dict(count=count,wire_hex=wire.hex(),grid_hex=n.grid.copy(),static_text=n.formatted.copy()))
    contexts=[]
    for packed,key,number,aux_key in ((0,0,0,0),(0xf0,1,65535,65535),(0x11,1,123,2),(0x01,2,65535,0)):
        payload=bytearray(168);payload[161]=packed
        struct.pack_into('<HHH',payload,162,key,number,aux_key)
        v.mem_write(PACKET,bytes(payload));n.call(0x8b710,PACKET,this=COMPANION,budget=500000)
        require(v.mem_read(COMPANION+0x20fd6,1)[0]==(packed&15),'Low nibble')
        require(v.mem_read(COMPANION+0x20fde,1)[0]==(packed>>4),'High nibble')
        require(struct.unpack('<H',v.mem_read(COMPANION+0x20fd4,2))[0]==key,'Purchase key')
        require(struct.unpack('<I',v.mem_read(COMPANION+0x20fd8,4))[0]==number,'WORD zero extension')
        require(struct.unpack('<H',v.mem_read(COMPANION+0x20fdc,2))[0]==aux_key,'Final extra WORD')
        contexts.append(dict(packed=packed,item_key=key,raw_word=number,auxiliary_item=aux_key))
    flag_cases=[]
    for flags in (0,1,2,0x40,0x41,0x42,0x81,0xc1):
        payload=bytearray(168);payload[:4]=row[:2]+bytes([0,flags]);payload[160]=1
        v.mem_write(PACKET,bytes(payload));n.controls.clear()
        n.call(0x8b710,PACKET,this=COMPANION,budget=500000)
        relevant=[t for t in n.controls if t[0]==2 and t[1] in (0x1a,0x22)]
        expected=int(not (flags&63 and flags&0xc0==0x40))
        require(relevant==[(2,0x1a,expected),(2,0x22,expected)],'Native row button enable flags')
        flag_cases.append(dict(flags=flags,disabled=expected))
    # Guarded malformed-input observation: execute only ingestion and stop
    # before UI opening. Count41 copies the context bytes into slot41 storage.
    payload=bytearray(168);payload[160:164]=bytes.fromhex('29f05aa5')
    v.mem_write(PACKET,bytes(payload));v.mem_write(SP,struct.pack('<II',BASE+0x1000,PACKET))
    v.reg_write(x.UC_X86_REG_ESP,SP);v.reg_write(x.UC_X86_REG_ECX,COMPANION)
    n.bounded(0x48b710,0x48b7d0,10000)
    require(v.reg_read(x.UC_X86_REG_EIP)==0x48b7d0,'Overflow observation boundary')
    require(bytes(v.mem_read(COMPANION+0x20fd2,2))==bytes.fromhex('29f0'),'Native copy over capacity40')
    # Literal ordinary shortcut request: no source-defined acceptance state.
    n.reset_queue();n.call(0xa6760,0,12,budget=500000)
    require(n.queue()=='d700','Daily menu request')
    v.mem_write(UI+0xa3cf4,struct.pack('<H',0x16));v.mem_write(UI+0xa3d02,bytes(2))
    n.reset_queue();n.call(0xa6d90,0x27,0x20,budget=500000)
    require(n.queue()=='d700','Native menu control release D7')
    auxiliary=[]
    for control in (0x16,0x2d):
        for flag in (0,1,2,15):
            for key in (0,1,65535):
                v.mem_write(COMPANION+0x20fde,bytes([flag]));v.mem_write(COMPANION+0x20fdc,struct.pack('<H',key))
                n.reset_queue();n.call(0x8b9b0,control,1,this=COMPANION,budget=500000)
                expected='d80200000000000000' if flag==1 and key else ''
                require(n.queue()==expected,'Auxiliary gate/output')
                auxiliary.append(dict(control=control,flag=flag,item_key=key,wire_hex=n.queue()))
    messages={}
    for key in range(949,966):
        pointer=struct.unpack('<I',v.mem_read(MESSAGES+4*(key-1),4))[0]
        messages[str(key)]=n.cstring(pointer,1024).decode('cp950')
    # S2C7A mode5 has its own text-ID namespace; stop at renderer entry with
    # real source string selected. No claim that daily pair IDs join these IDs.
    text_raw=(ROOT.parent/'God2/Data2/Patch/Comm/DailyMission01.csvZ').read_bytes()
    require(hashlib.sha256(text_raw).hexdigest()=='f5b6653b9390b44f4fb6af96bb1247f2d2a5c2d639f5a6fa9e735662f4090d72','Daily dialogue source')
    text_plain=decode_csvz(text_raw)
    require(hashlib.sha256(text_plain).hexdigest()=='0c424ba0abb49e2f240b323cdbd97b1506c086184acff21649c388924b955556','Daily dialogue decoded')
    text_lines=text_plain.splitlines();require(text_lines[1]==b'DailyMissionMessage,300','Daily text count')
    table=DAILY+0x1000;top=DAILY+0x2000;source_texts={}
    for index,line in enumerate(text_lines[2:]):
        key,_,value=line.partition(b',');require(int(key)==index+1,'Daily text identity')
        v.mem_write(table+index*4,struct.pack('<I',top));v.mem_write(top,value+b'\0')
        source_texts[index+1]=value;top+=len(value)+1
    require(top<DAILY+0x10000,'Dialogue source relocation bound')
    v.mem_write(DEFINITIONS+0xfc2d4,struct.pack('<HHI',300,0,table))
    v.mem_write(UI+0x232dee,struct.pack('<H',3));dialogue=[]
    for key in (1,2,3,300):
        body=bytearray(26);struct.pack_into('<HBBHHH',body,0,27,5,0,0,key,0)
        v.mem_write(PACKET,bytes(body));v.mem_write(SP,struct.pack('<II',BASE+0x1000,PACKET))
        v.reg_write(x.UC_X86_REG_ESP,SP);v.reg_write(x.UC_X86_REG_ECX,UI)
        n.bounded(0x4c7f10,0x4c81f0)
        require(v.reg_read(x.UC_X86_REG_EIP)==0x4c81f0,'Daily text pre-render boundary')
        sp=v.reg_read(x.UC_X86_REG_ESP);pointer=struct.unpack('<I',v.mem_read(sp+4,4))[0]
        require(n.cstring(pointer,2048)==source_texts[key],'Mode5 exact text namespace')
        dialogue.append(dict(text_key=key,text_hex=source_texts[key].hex(),stop='4C81F0 before renderer'))
    require({0x858b0,0x8b710,0x8b7f0,0x8c040,0x8b9b0,0x58430,0xa6760,0xa6d90,0x132e0,0x15ce0,0xc7f10}.issubset(n.pcs),'Required native coverage')
    return dict(status='PASS',current_pe_sha256=PIN,source=source,lists=lists,menu_request='d700',
        labels=labels,contexts=contexts,flag_cases=flag_cases,overflow41='confirmed copy beyond40; never render/send',dialogue=dialogue,
        auxiliary=auxiliary,program_messages=messages,counts={'full_list_returns':len(lists)+len(contexts)+len(flag_cases),'auxiliary_requests':len(auxiliary),'dialogue_slices':len(dialogue)},
        scope='Original FD dispatcher/list/formatters return with initialized daily widget and absent renderer. Source-row relocation, synthetic server availability. No actual graphical/client/server/reward acceptance.')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path);a=p.parse_args();result=verify()
    if a.output:
        a.output.parent.mkdir(parents=True,exist_ok=True);temporary=a.output.with_suffix(a.output.suffix+'.pending')
        temporary.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');temporary.replace(a.output)
    print(json.dumps(result if not a.output else {'status':result['status'],'counts':result['counts'],'output':str(a.output)},ensure_ascii=True))
