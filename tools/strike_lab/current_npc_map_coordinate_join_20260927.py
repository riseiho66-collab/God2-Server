"""Bounded current-PE map-coordinate / MDL identity audit; no live access.

Native lookup/UI-anchor/setter execution uses source-projected test records.
This does not claim full map loading, NPC creation, or original spawn authority.
"""
import argparse
import hashlib
import json
import re
import struct
from pathlib import Path
import pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn import x86_const as x
from .omega_assets import decode_csvz
from .world_atlas import parse_catalog
from .current_monster_binary_producer import parse_mdl, SPANS
from .town_navigation import MDL_SHA, MDL_DECODED_SHA

ROOT=Path(__file__).resolve().parents[2]
CLIENT=ROOT.parent/'God2'
DECOMPILED=ROOT.parent.parent/'God2-解殼EXE原始碼重建/decompiled/functions'
PE_SHA='6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98'
SOURCE_SHA='70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731'
DECODED_SHA='75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815'
BASE=0x400000
UI,TABLE,ROWS,META,STACK,STOP=0x3000000,0x3400000,0x3600000,0x3610000,0x2000000,0x1000000


def require(value,message):
    if not value:raise ValueError(message)


def sha(data):return hashlib.sha256(data).hexdigest()


class Native:
    def __init__(self,image,rows):
        self.vm=v=Uc(UC_ARCH_X86,UC_MODE_32)
        for at,size in ((BASE,(len(image)+4095)&~4095),(UI,0x300000),(TABLE,0x100000),
                        (ROWS,0x20000),(STACK,0x10000),(STOP,0x1000)):
            v.mem_map(at,size)
        v.mem_write(BASE,image);v.mem_write(UI+0xcff70,struct.pack('<I',TABLE))
        v.mem_write(TABLE+0xd2aba,struct.pack('<h',len(rows)))
        v.mem_write(TABLE+0xd2abc,struct.pack('<I',ROWS))
        self.addresses={}
        for i,r in enumerate(rows):
            at=ROWS+i*0x1a4;self.addresses[r['area'],r['scene']]=at
            v.mem_write(at+0xf0,struct.pack('<H',r['packed_selector']))
            v.mem_write(at+0xf4,struct.pack('<I',r['kind']|(r['catalog_x']<<2)|(r['catalog_y']<<17)))
            v.mem_write(at+0xf8,struct.pack('<hhh',r['layer_width'],r['layer_height'],r['layers_per_row']))
        self.pcs=set();self.writes=[]
        v.hook_add(UC_HOOK_CODE,self.code)
        v.hook_add(UC_HOOK_MEM_WRITE,lambda v,a,at,s,val,c:self.writes.append((at,s,val)))

    def code(self,v,at,size,_):
        allowed=((0x459d80,0x459df8),(0x4c3ea0,0x4c3f56),(0x441fc0,0x441fe6),(0x44c6f0,0x44c735))
        require(any(a<=at<b for a,b in allowed),'Unexpected native boundary '+hex(at))
        self.pcs.add(at)

    def call(self,at,*args,this=UI):
        v=self.vm;sp=STACK+0x8000
        v.mem_write(sp,struct.pack('<'+'I'*(len(args)+1),STOP,*(a&0xffffffff for a in args)))
        v.reg_write(x.UC_X86_REG_ESP,sp);v.reg_write(x.UC_X86_REG_ECX,this)
        self.writes=[];v.emu_start(at,STOP,count=100000)
        require(v.reg_read(x.UC_X86_REG_EIP)==STOP,'Native return/budget')
        require(v.reg_read(x.UC_X86_REG_ESP)==sp+4+4*len(args),'Native stack return')
        return v.reg_read(x.UC_X86_REG_EAX)


def run():
    raw=(CLIENT/'God2.exe').read_bytes();require(sha(raw)==PE_SHA,'Current PE changed')
    image=pefile.PE(data=raw).get_memory_mapped_image()
    raw_source=(CLIENT/'Data2/Patch/Comm/gamedata.csvZ').read_bytes()
    require(sha(raw_source)==SOURCE_SHA,'Gamedata changed');plain=decode_csvz(raw_source)
    require(sha(plain)==DECODED_SHA,'Decoded gamedata changed')
    rows=parse_catalog(plain);require(len(rows)==144,'Catalog count')
    mdl_path=CLIENT/'Data2/map/island01/CityI1/cityI1.mdlZ'
    mdl_raw=mdl_path.read_bytes();require(sha(mdl_raw)==MDL_SHA,'CityI1 MDL changed')
    mdl_plain=decode_csvz(mdl_raw);require(sha(mdl_plain)==MDL_DECODED_SHA,'CityI1 decoded MDL changed')
    mdl=parse_mdl(mdl_plain,allow_parent_rom=True)
    kunlun_raw=(CLIENT/'Data2/map/island03/cityi2/cityi2.mdlZ').read_bytes()
    require(sha(kunlun_raw)=='cb36dbf46adc611620e1bd7c9b0093955c846f33a849ebf88f6ce57f426813cc','CityI2 MDL pin')
    kunlun_plain=decode_csvz(kunlun_raw)
    require(sha(kunlun_plain)=='bed2f89dcdb30ed6d7b30c5625423f8bd007ca30eea32ec5406a7ebb7932dd5f','CityI2 decoded pin')
    require(kunlun_plain.splitlines()[5011].split()==[b'0',b'2'],'CityI2 zero-width Pass row')
    # Qualified subsequently by current_mdl_zero_pass_20260927: retain exact
    # blank rows instead of preserving the superseded parser-failure assertion.
    kunlun=parse_mdl(kunlun_plain,allow_parent_rom=True)
    require(kunlun['unaccounted_bytes']==0 and any(g['width']==0 and g['height']==2
        for m in kunlun['models'] for g in m['grids']),'Qualified CityI2 zero grid lost')
    codes={}
    for key in ('mdl_dispatch','model_catalog_reader','tile_reader','model_reader','model_lookup','placement_reader','placement_setter'):
        a,b,pin=SPANS[key];require(sha(image[a:b])==pin,'Native MDL span changed: '+key)
        codes[key]={'rva_start':hex(a),'rva_end_exclusive':hex(b),'sha256':pin}
    for name,a,b in (('map_anchor',0xc3ea0,0xc3f56),('map_lookup',0x59d80,0x59df8),
                     ('map_marker',0xc3e30,0xc3e97),('map_projection',0xc2510,0xc257e),
                     ('world_map_marker_caller',0x65e00,0x65ed0)):
        codes[name]={'rva_start':hex(a),'rva_end_exclusive':hex(b),'sha256':sha(image[a:b])}
    n=Native(image,rows);v=n.vm;lookups=[]
    for r in rows:
        actual=n.call(0x459d80,r['area'],r['scene'],this=TABLE)
        require(actual==n.addresses[r['area'],r['scene']],'Native map lookup mismatch')
        lookups.append({'area':r['area'],'scene':r['scene'],'source_line':r['source_line'],'record_pointer':hex(actual)})
    require(n.call(0x459d80,63,1023,this=TABLE)==0,'Missing map must stay null')
    anchors=[]
    for area,scene in ((2,4),(4,3)):
        base=n.addresses[area,0];current=n.addresses[area,scene]
        area_row=next(r for r in rows if (r['area'],r['scene'])==(area,0))
        scene_row=next(r for r in rows if (r['area'],r['scene'])==(area,scene))
        for mode in ('no_metadata','same_metadata_key','different_metadata_key','missing_scene','scene_metadata_null'):
            v.mem_write(base+0x1a0,struct.pack('<I',0 if mode=='no_metadata' else META))
            v.mem_write(current+0x1a0,struct.pack('<I',0 if mode in ('no_metadata','scene_metadata_null') else META+0x100))
            v.mem_write(META+0x24,struct.pack('<h',5));v.mem_write(META+0x124,struct.pack('<h',6 if mode=='different_metadata_key' else 5))
            n.call(0x4c3ea0,area,1023 if mode=='missing_scene' else scene)
            expected=(scene_row['layer_width'],scene_row['layer_height']) if mode=='different_metadata_key' else (area_row['catalog_x'],area_row['catalog_y'])
            actual=struct.unpack('<ii',v.mem_read(UI+0x8aa30,8));require(actual==expected,'Map UI anchor mismatch')
            nonstack=[(a,s,value) for a,s,value in n.writes if not STACK<=a<STACK+0x10000]
            require([(a,s) for a,s,_ in nonstack]==[(UI+0x8aa30,4),(UI+0x8aa34,4)],'Unexpected nonstack map write')
            anchors.append({'area':area,'scene':scene,'mode':mode,'ui_anchor':list(actual),
                            'writes':[{'ui_offset':hex(a-UI),'bytes':s,'value':value} for a,s,value in nonstack]})
    roms=[i for i,s in enumerate(mdl['rom_references']) if s.lower()=='npcad.rom'];require(roms==[15],'NPCAD ROM index')
    tiles={i:t for i,t in enumerate(mdl['tiles']) if t['fields'][3]==15}
    models={i:m for i,m in enumerate(mdl['models']) if any(layer[0] in tiles for layer in m['layers'])}
    require(set(tiles)==set(range(161,167)) and set(models)==set(tiles),'NPCAD model join')
    placements=[]
    for index,p in enumerate(mdl['placements']):
        if p['fields'][0] not in models:continue
        f=p['fields'];at=META+0x1000;v.mem_write(at,bytes([0xa5])*0x50)
        n.call(0x441fc0,f[1],f[2],f[3],f[4],0x12345678,this=at)
        require(struct.unpack('<4I',v.mem_read(at+0xc,16))==tuple(f[1:5]),'Native model coordinate setter')
        require(struct.unpack('<I',v.mem_read(at+0x2c,4))[0]==0x12345678,'Native model pointer setter')
        nonstack=[(a,s) for a,s,_ in n.writes if not STACK<=a<STACK+0x10000]
        require(nonstack==[(at+off,4) for off in (0xc,0x10,0x14,0x18,0x2c)],'Unexpected model setter write')
        entry=dict(p,index=index,source_line=mdl_plain[:p['offset']].count(b'\n')+1,
                   raw_record_hex=mdl_plain[p['offset']:p['end_exclusive']].hex(),
                   qualification='STATIC_MODEL_GEOMETRY_NOT_WORLD_NPC',native_setter_return=True)
        placements.append(entry)
    require(len(placements)==3,'NPCAD placement count')
    # Read only textual call sites to retain concrete next reader/caller edges.
    targets=('004c3ea0','00465e00','004c3e30','004c2660','004c25f0',
             '004e9b50','004e9bc0','004e9eb0','0044c6f0','0043ee20','004cc380')
    callers={t:[] for t in targets}
    for path in DECOMPILED.glob('*.c'):
        source=path.read_text(encoding='utf-8')
        for target in targets:
            for line,text in enumerate(source.splitlines(),1):
                if re.search(r'\bFUN_'+target+r'\(',text) and 'Entry:' not in text and not text.startswith(('void FUN_','undefined4 FUN_','int FUN_')):
                    callers[target].append({'file':path.name,'line':line,'text':text.strip()})
    return {'status':'PASS','current_pe_sha256':PE_SHA,'source_sha256':SOURCE_SHA,'decoded_sha256':DECODED_SHA,
            'code_spans':codes,'counts':{'native_map_lookups':145,'full_anchor_returns':len(anchors),
                'npcad_tiles':len(tiles),'npcad_models':len(models),'native_model_setter_returns':len(placements),
                'qualified_world_npc_placements':0},
            'map_lookups':lookups,'ui_anchor_cases':anchors,
            'source_map_rows':[r for r in rows if (r['area'],r['scene']) in ((2,0),(2,4),(4,0),(4,3))],
            'mdl':{'path':str(mdl_path.relative_to(CLIENT)),'sha256':MDL_SHA,'decoded_sha256':MDL_DECODED_SHA,
                'rom_index':15,'rom_reference':'npcad.ROM','tiles':[{**t,'index':i,'name':bytes.fromhex(t['name_hex']).decode('cp950')} for i,t in tiles.items()],
                'models':[{**m,'index':i} for i,m in models.items()],'placements':placements},
            'cityi2_parser_boundary':{'source_sha256':sha(kunlun_raw),'decoded_sha256':sha(kunlun_plain),
                'source_line':5012,'raw_hex':kunlun_plain.splitlines()[5011].hex(),
                'reason':'Former zero-width parser boundary now qualified by current_mdl_zero_pass_20260927; complete source consumption preserves explicit blank rows. This does not supply NPC identity.'},
            'decompiler_callers_static_only':callers,
            'scope':'Full native map lookup/anchor and geometry setter; source-projected records and synthetic metadata operands, no game callee stubs. Full MDL/renderer/72 allocation not executed. Model geometry is not NPC identity/direction/interaction authority.'}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    require(args.output.resolve().is_relative_to((ROOT/'artifacts/research/npc-map-coordinate-join-20260927').resolve()),'Output outside designated evidence directory')
    result=run();args.output.parent.mkdir(parents=True,exist_ok=True)
    temporary=args.output.with_suffix('.pending');temporary.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');temporary.replace(args.output)
    print(json.dumps({'status':result['status'],'counts':result['counts']}))
