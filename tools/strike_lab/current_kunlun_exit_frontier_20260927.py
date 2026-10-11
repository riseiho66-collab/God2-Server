"""Read-only CityI2 geometry/exit frontier. No BFS, client, socket or runtime edit."""
import hashlib
import json
from pathlib import Path
import struct
import pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn import x86_const as x
from .omega_assets import decode_csvz
from .current_monster_binary_producer import parse_mdl
from .current_item_transition import NativeItemTransition
from .recover_items import build_items
from .world_scenes import parse_can

ROOT=Path(__file__).resolve().parents[2]
CLIENT=ROOT.parent/'God2'
IMAGE=ROOT/'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin'
PE_PIN='6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98'
IMAGE_PIN='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
BASE=0x400000
def sha(b):return hashlib.sha256(b).hexdigest()
def require(v,m):
    if not v:raise ValueError(m)
def pin(p):
    b=p.read_bytes();return {'path':str(p.relative_to(ROOT.parent)), 'sha256':sha(b),'bytes':len(b)}
def project(a,b):
    return [a-int(b/2),a+int((b+1)/2)]
def native(image):
    v=Uc(UC_ARCH_X86,UC_MODE_32)
    for a,n in ((BASE,(len(image)+4095)&~4095),(0x3000000,0x10000),(0x3100000,0x90000),(0x3200000,0x5000)):
        v.mem_map(a,n)
    v.mem_write(BASE,image)
    return v
def call(v,at,args=(),this=0x3100000):
    sp=0x3008000;stop=0x401000
    v.reg_write(x.UC_X86_REG_ESP,sp);v.reg_write(x.UC_X86_REG_ECX,this)
    v.mem_write(sp,struct.pack('<'+'I'*(1+len(args)),stop,*args))
    v.emu_start(at,stop,count=10000)
    require(v.reg_read(x.UC_X86_REG_EIP)==stop,'Native complete return')
    require(v.reg_read(x.UC_X86_REG_ESP)==sp+4+4*len(args),'Native stack cleanup')

def main():
    pe_raw=(CLIENT/'God2.exe').read_bytes();image=IMAGE.read_bytes()
    require(sha(pe_raw)==PE_PIN and sha(image)==IMAGE_PIN,'Build pin')
    pe=pefile.PE(data=pe_raw);spans={}
    for at,n in ((0x441f90,0x30),(0x44910d,0x10),(0x496350,0x33),(0x4132e0,0x90),(0x43ee20,0x340)):
        r=at-BASE;raw=image[r:r+n]
        require(pe.get_data(r,n)==raw,'Native span differs from current PE')
        spans[hex(at)]={'bytes':n,'sha256':sha(raw)}
    v=native(image);call(v,0x441f90)
    constructor={'full_return':True,'object_1c':struct.unpack('<i',v.mem_read(0x310001c,4))[0],
                 'object_20':struct.unpack('<i',v.mem_read(0x3100020,4))[0]}
    require(constructor['object_1c']==constructor['object_20']==-1,'Default target fields')
    gates=[]
    for length,target,accepted in ((0,-1,False),(1,-1,True),(0,0,True)):
        v=native(image);v.mem_write(0x310001c,struct.pack('<i',target))
        v.reg_write(x.UC_X86_REG_EAX,length);v.reg_write(x.UC_X86_REG_EDI,0x3100000)
        reached=[]
        def stop(uc,pc,size,data):
            if pc in (0x44911c,0x44911e):reached.append(pc);uc.emu_stop()
        v.hook_add(UC_HOOK_CODE,stop);v.emu_start(0x44910d,0x4491e0,count=20)
        require(len(reached)==1 and (reached[0]==0x44911c)==accepted,'Original eligible gate')
        gates.append({'string_length':length,'target_x':target,'eligible':accepted,'stop_va':hex(reached[0]),
                      'scope':'exact native eligibility slice, not full classifier'})
    sends=[]
    for key,slot,blocked in ((5501,4,False),(5571,9,False),(5504,3,False),(5501,4,True)):
        v=native(image);v.mem_write(0x3186874,struct.pack('<I',0x3200000))
        v.mem_write(0x31866e4,struct.pack('<I',int(blocked)))
        call(v,0x496350,(0xa5000000|key,slot,1))
        n=struct.unpack('<I',v.mem_read(0x32036c4,4))[0];logical=bytes(v.mem_read(0x32036c8,n))
        require(logical==(b'' if blocked else struct.pack('<BHB',0x25,key,slot)+b'\xa5'),'Original25 bytes')
        sends.append({'item_key':key,'slot':slot,'ui_blocked':blocked,'logical_hex':logical.hex(),
                      'complete_native_producer_and_queue_return':True,'authority':'request only; no destination/payment/consumption'})
    dispatch=[]
    for key in (5501,5504,5571):
        n=NativeItemTransition();n.seed_slot(4,key,1)
        logical=n.request(key,by_slot=False)
        require(logical==struct.pack('<BHBB',0x25,key,4,0),'Full55 category dispatch')
        dispatch.append({'item_key':key,'logical_hex':logical.hex(),'full_native_return':True,
                         'visited_va':[hex(BASE+r) for r in n.visits],
                         'fixture':'synthetic positive inventory slot; empty metadata table; not native grant'})
    item_catalog=build_items(CLIENT)
    items=[r for r in item_catalog['records'] if r['client_item_id'] in (5501,5504,5571,5601,5605,5609,16055)]
    path=CLIENT/'Data2/map/island03/cityi2/cityi2.mdlZ';raw=decode_csvz(path.read_bytes())
    mdl=parse_mdl(raw,allow_parent_rom=True)
    can_path=CLIENT/'Data2/map/island03/Island03.can';can_raw=can_path.read_bytes();can=parse_can(can_raw)
    can_rows=[{'area':4,'scene':scene,'scene_index_offset':16+can['file_count']*64+scene*2,
               **can['files'][file]} for scene,file in enumerate(can['scene_file_indices'])]
    previous=json.loads((ROOT/'artifacts/world-atlas/kunlun-parent-window-reachability-20260927.json').read_text(encoding='utf-8'))
    old_conflicts={tuple(r['target']) for r in previous['results']['current_floor']['reachable_conflict_cells']}
    tiles=[]
    for i,t in enumerate(mdl['tiles']):
        fields=t['fields'];rom=mdl['rom_references'][fields[3]]
        tiles.append({'tile':i,'name':bytes.fromhex(t['name_hex']).decode('cp950'),
                      'name_hex':t['name_hex'],'offset':t['offset'],'fields':fields,'rom':rom,'action_key':fields[4]})
    rows=[]
    for n,p in enumerate(mdl['placements']):
        model=mdl['models'][p['fields'][0]]
        ids=[l[0] for l in model['layers'] if l[0]>=0]
        names=[tiles[i]['name'] for i in ids]
        if not (any(any(k in s for k in ('門','台','碑柱塔','傳送')) for s in names) or p['attached_reference']):continue
        points=[]
        for z in range(4):
            a,b=model['extra_8_ints'][z*2:z*2+2]
            if a<0 or b<0:continue
            dx,dy=project(a,b);xy=[p['fields'][3]+dx,p['fields'][4]+dy]
            points.append({'pair':z,'raw':[a,b],'tile':xy,'previous_reachable_conflict_target':tuple(xy) in old_conflicts})
        rows.append({'placement':n,**p,'tiles':[tiles[i] for i in ids],
                     'model_points':model['extra_8_ints'],'projected_points':points,
                     'eligibility_from_loader':bool(p['attached_reference']) or p['fields'][6]>=0,
                     'npc_text_join':None})
    unplaced=[t for t in tiles if '傳送' in t['name'] and not any(p['fields'][0]==t['tile'] for p in mdl['placements'])]
    rom_records=[]
    for name,keys in {'Monolith.ROM':{1018},'Door.ROM':{1001,1002},'BigDoor.ROM':{1003,1004,1007,1008},
                      'MARK2.ROM':{1001},'Mark.ROM':{1001},'TT.ROM':{1024}}.items():
        f=path.parent/(name+'Z');decoded=decode_csvz(f.read_bytes())
        require(decoded[:12]==b'IGSROM02\0\0\0\0','ROM source signature')
        at=12;actions=[];ended=False
        while at<len(decoded):
            require(at+12<=len(decoded),'ROM chunk header')
            tag,size=struct.unpack_from('<8sI',decoded,at);end=at+12+size
            require(end<=len(decoded),'ROM source chunk extent')
            if tag==b'ACT_DATA':
                require(size==48,'ROM action header')
                data=decoded[at+12:end];actions.append({'data':data,'offset':at,
                     'name':data[24:].split(b'\0',1)[0].decode('cp950')})
            if tag==b'FILE_END':require(size==0 and end==len(decoded),'ROM end extent');ended=True
            at=end
        require(ended,'ROM source terminator')
        for a in actions:
            key=struct.unpack_from('<I',a['data'])[0]
            if key in keys:rom_records.append({'source':pin(f),'decoded_sha256':sha(decoded),
                'action_key':key,'name':a['name'],'offset':a['offset'],'header_sha256':sha(a['data']),
                'header_hex':a['data'].hex(),'role':'source graphics action; not world NPC identity'})
    source_rows=[]
    selected={'NPCMission01.csvZ':{934},'NPCNormal01.csvZ':{993},'NPCNormal02.csvZ':{1635,1636},
              'NPCMission09.csvZ':{8779,8791,8792},'NpcMission13.csvZ':{12341,12342,12343,12344}}
    for name,keys in selected.items():
        f=CLIENT/'Data2/Patch/Comm'/name;decoded=decode_csvz(f.read_bytes())
        for line_no,line in enumerate(decoded.splitlines(),1):
            try:key=int(line.split(b',')[0])
            except ValueError:continue
            if key in keys:source_rows.append({'file':name,'source':pin(f),'decoded_sha256':sha(decoded),
                'line':line_no,'text_id':key,'raw_row_sha256':sha(line),'raw_row_hex':line.hex(),
                'text':line.decode('cp950'),'world_npc_id':None,'area_scene_position_join':None})
    contextual_rows=[]
    for name,line_numbers in {'Mission_data.csvZ':{119,122,123,125,459,460,461},
                              'gamedata.csvZ':{115,308,1820,1821,1822,3590,21082,21097}}.items():
        f=CLIENT/'Data2/Patch/Comm'/name;decoded=decode_csvz(f.read_bytes())
        for n,line in enumerate(decoded.splitlines(),1):
            if n in line_numbers:contextual_rows.append({'file':name,'source':pin(f),'decoded_sha256':sha(decoded),
                'line':n,'raw_row_sha256':sha(line),'raw_row_hex':line.hex(),'text':line.decode('cp950'),
                'authority':'text/catalog only; no world placement or arrival coordinate'})
    result={'schema':'god2-current-kunlun-exit-frontier-20260927-v1','scope':'read-only; no BFS/UI/server/runtime mutation',
            'pins':[pin(CLIENT/'God2.exe'),pin(IMAGE),pin(path),pin(can_path)],'decoded_mdl_sha256':sha(raw),
            'area4_can_scenes':can_rows,
            'native_spans':spans,'native_constructor':constructor,'native_classifier_eligibility':gates,
            'native_inventory_request':sends,'native_inventory_category_dispatch':dispatch,'teleport_item_source_rows':items,
            'mdl_counts':{k:len(mdl[k]) for k in ('tiles','models','placements')},
            'tile_name_exact_matches':{term:[t for t in tiles if term in t['name']] for term in ('狗洞','法陣','轉生台','傳送')},
            'tile_inventory':tiles,'unplaced_teleport_tiles':unplaced,'geometry_candidates':rows,
            'source_graphics_actions':rom_records,'text_candidates':source_rows,'contextual_source_rows':contextual_rows,
            'qualified_new_cross_map_routes':0,'new_world_npc_placements':0,
            'next_frontier':'bind doghole934 / immortal-child993 / celestial1635-1636 to qualified world identity and original-server destination; generic37/85/86 exists but supplies no source binding'}
    out=ROOT/'artifacts/research/kunlun-exit-frontier-20260927/evidence.json';out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'output':str(out),'geometry_candidates':len(rows),'text_candidates':len(source_rows),
                      'native_gate_cases':len(gates),'native25_cases':len(sends),'new_routes':0}))

if __name__=='__main__':main()
