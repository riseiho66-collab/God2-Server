"""Current weapon display arithmetic and bounded actual28 admission audit.

Not an equipment legality or server damage formula. Synthetic role/instance
operands are labelled; source restrictions remain source text, not predicates.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct
from .current_equipment_20260926 import EquipmentOracle, PIN, require, ROOT
from .current_weapon_appearance_20260926 import Oracle as Slice, DATA, SP, WORLD
from .current_weapon_attributes_native_20260926 import Probe, UI as TOOLTIP_UI, PACKET, TABLE, pefile
from .current_equipment_projection_20260926 import Oracle as RequestOracle, NativeItemMetadata, UI, COMPANION
from .omega_assets import decode_csvz
from unicorn import UC_HOOK_MEM_READ
from unicorn import x86_const as x

SOURCE_SHA='70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731'
DECODED_SHA='75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815'


def verify():
    raw=(ROOT.parent/'God2/God2.exe').read_bytes()
    require(hashlib.sha256(raw).hexdigest()==PIN,'Current PE mismatch')
    pe=pefile.PE(data=raw);image=pe.get_memory_mapped_image()
    source=(ROOT.parent/'God2/Data2/Patch/Comm/gamedata.csvZ').read_bytes()
    require(hashlib.sha256(source).hexdigest()==SOURCE_SHA,'Source mismatch')
    decoded=decode_csvz(source)
    require(hashlib.sha256(decoded).hexdigest()==DECODED_SHA,'Decoded source mismatch')
    lines=decoded.splitlines();families={};text_restrictions=[];levels=set()
    for family,count in (('WPN',630),('TWP',629)):
        start=lines.index(f'{family},{count}'.encode());rows=lines[start+1:start+1+count]
        require(len(rows)==count,'Source count')
        counts=Counter()
        for offset,row in enumerate(rows):
            cells=row.split(b',');level=int(cells[28]);counts[level]+=1;levels.add(level)
            note=cells[7].decode('cp950')
            if any(word in note for word in ('男性','女性','職業','限定')):
                text_restrictions.append(dict(family=family,key=int(cells[0]),line=start+offset+2,
                    text=note,raw_hex=cells[7].hex(),row_sha256=hashlib.sha256(row).hexdigest()))
        families[family]={'rows':count,'encoded_level_counts':dict(sorted(counts.items()))}
    # New full formatting-argument check. The >=1000 branch compares ORIGINAL
    # source WORD, while quotient/remainder use adjusted signed-WORD floor1.
    n=Probe(pe);level_vectors=[]
    for base in sorted(levels|{0,999,1000,1001,32767,32768,65535}):
        for grade,adjustment in enumerate((0,1,3,5)):
            n.write(PACKET+12,'I',grade<<30);n.write(TABLE+0x11e,'H',base)
            n.setup();n.write(n.reg('ESP')+0x11a8,'I',TABLE)
            n.setreg('EDX',PACKET);n.setreg('EBP',TOOLTIP_UI)
            n.run(0x4b6020,[0x547af7])
            sp=n.reg('ESP');fmt=n.read(sp+8,'I')
            value=(base-adjustment)&65535
            signed=value if value<32768 else value-65536
            expected=max(1,signed)
            if base<1000:
                require(fmt==0x592adc and n.read(sp+20,'I')==expected,'Plain level format operands')
                numbers=[expected]
            else:
                require(fmt==0x592acc,'Rebirth level format selection')
                numbers=[n.read(sp+20,'I'),n.read(sp+28,'I')]
                require(numbers==[expected//1000,expected%1000],'Rebirth quotient/remainder')
            level_vectors.append(dict(base_encoded=base,grade_bits=grade,display_encoded=expected,
                format='level' if base<1000 else 'turn_level',numbers=numbers,
                source_value=base in levels))
    # Native signed32 endpoints with no floor/clamp; these are tooltip widths.
    n=Slice();range_vectors=[]
    for center in (0,1,24,1023):
        for width in (1,3,5,255):
            n.v.mem_write(DATA,struct.pack('<H',center))
            for register,value in ((x.UC_X86_REG_ESP,SP),(x.UC_X86_REG_EDI,DATA),(x.UC_X86_REG_ECX,width)):
                n.v.reg_write(register,value)
            n.writes=();n.run(0x4b445c,(0x4b446e,),((0x4b445c,0x4b446e),))
            values=list(struct.unpack('<ii',n.v.mem_read(SP-8,8)))
            require(values==[center-width,center+width],'Native range arithmetic')
            range_vectors.append(dict(center=center,width=width,display_endpoints=values))
    # Actual source rows, including male/female-only TWP descriptions. Cache-hit
    # tooltip is deliberate: isolate equip admission from display formatting.
    loader=NativeItemMetadata()
    require(all(image[a:b]==loader.image[a:b] for a,b in loader.CODE),'Metadata parser code mismatch')
    definitions={1:loader.item_row('WPN',0),2:loader.item_row('WPN',1),
                 19071:loader.item_row('TWP',70),19072:loader.item_row('TWP',71)}
    require(all(d['record'][0x11a]&4 for d in definitions.values()),'Source equip flag')
    for key,expected in ((1,1),(2,10),(19071,10),(19072,10)):
        require(struct.unpack_from('<H',definitions[key]['record'],0x11e)[0]==expected,'Parsed definition level')
    for key,text in ((19071,'限男性角色裝備'),(19072,'限女性角色裝備')):
        require(definitions[key]['record'][0x2e:].split(b'\0',1)[0]==text.encode('cp950'),
                'Native source restriction text storage')
    n=RequestOracle(image,definitions);role=0x66000000;n.vm.mem_map(role,0x5000)
    n.vm.mem_write(UI+0x86888,struct.pack('<I',role));reads=[]
    def watch(v,access,address,size,value,context):
        if address<role+0x5000 and address+size>role or address<UI+0x8688c and address+size>UI+0x86888:
            reads.append((address,size))
    n.vm.hook_add(UC_HOOK_MEM_READ,watch)
    request_vectors=[]
    for key in definitions:
        family=1 if key<19000 else 25
        data=struct.pack('<HH',key,family)+bytes(16)
        for poison in (0,0x55,0xff):
            n.vm.mem_write(role,bytes([poison])*0x5000)
            for deity_bits in range(4):
                n.vm.mem_write(UI+0x866ba,bytes([deity_bits]))
                for slot in (0,34):
                    n.put(slot,data);reads.clear()
                    wire=n.ui_request(slot)
                    require(not reads,'Unexpected ordinary equip role reads')
                    require(bytes(n.vm.mem_read(role,0x5000))==bytes([poison])*0x5000,'Equip mutated role')
                    request_vectors.append(dict(key=key,slot=slot,role_poison=poison,
                        deity_bits=deity_bits,request_hex=wire,role_reads=0))
    return dict(status='PASS',client_sha256=PIN,source_sha256=SOURCE_SHA,decoded_sha256=DECODED_SHA,
        families=families,source_description_restrictions=text_restrictions,
        level_format_vectors=level_vectors,range_vectors=range_vectors,request_vectors=request_vectors,
        counts={'level_formats':len(level_vectors),'range_endpoints':len(range_vectors),
                'full_native_requests':len(request_vectors),'source_description_restrictions':len(text_restrictions)},
        scope='Current native tooltip arithmetic/format-call operands and complete cached-tooltip28 request returns. '
              'No role reads on tested ordinary WPN/TWP equip route. Does not authorize ignoring server restrictions, '
              'generate legal instances, calculate combat/final stats, or certify rendering.')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path);args=parser.parse_args()
    result=verify()
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        pending=args.output.with_suffix(args.output.suffix+'.pending')
        pending.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');pending.replace(args.output)
    print(json.dumps({'status':result['status'],'counts':result['counts'],'output':str(args.output) if args.output else None}))
