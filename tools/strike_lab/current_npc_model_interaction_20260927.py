"""Current NPCAD action render and independent NPC interaction handle oracle.

Only source/PE reads and research receipt writes. No client, renderer device,
network or database is opened. Native game callees execute without replacement;
Win32 SetRect/timeGetTime adapters and relocated ROM fixtures are explicit.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import capstone
import pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn import x86_const as x
from .omega_assets import decode_csvz
from .current_four_stat_ui_binding import parse_rom
from .current_monster_binary_producer import parse_mdl

ROOT=Path(__file__).resolve().parents[2]
CLIENT=ROOT.parent/'God2'
PE_PIN='6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98'
IMAGE_PIN='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
BASE=0x400000
STACK,STOP,API=0x2000000,0x2100000,0x2200000
RENDER,SPRITES,BANK,ASSETS=0x3000000,0x3400000,0x3600000,0x3700000
DATA,POOL,INPUT,UI,QUEUE=0x4000000,0x4100000,0x4200000,0x4300000,0x4600000
MANAGER=0x10000000
SP=STACK+0x8000
ENTRIES=(0x44a800,0x44a380,0x4421f0,0x441ec0,0x449df0,0x44a0f0,0x41afe0,0x41ae20,0x41b290,
         0x41b9c0,0x41c360,0x41e070,0x425b60,0x425dc0,0x4270e0,
         0x508780,0x50aa20,0x418cd0,0x50a910,0x50b220,0x50b390,0x4cad10,0x4cd780,
         0x4cd010,0x4ccf80,0x4ccd80,0x4ccfe0,0x496750,0x4c84a0,0x4132e0)


def require(value,message):
    if not value:raise ValueError(message)


def sha(data):return hashlib.sha256(data).hexdigest()


class Native:
    def __init__(self,image,saved,rom):
        self.rom=rom;self.image=image;self.saved=saved;self.v=v=Uc(UC_ARCH_X86,UC_MODE_32)
        for at,size in ((0,4096),(BASE,(len(image)+4095)&~4095),(STACK,0x10000),(STOP,4096),
                        (API,4096),(RENDER,0x300000),(SPRITES,0x100000),(BANK,0x2000),
                        (ASSETS,0x100000),(DATA,0x10000),(POOL,0x20000),(INPUT,0x13000),
                        (UI,0x240000),(QUEUE,0x5000),(MANAGER,0x30000),(MANAGER+0xa7e0000,4096)):
            v.mem_map(at,size)
        v.mem_write(BASE,image)
        self.put(0x5706e4,API);self.put(0x5707bc,API+16)
        self.put(RENDER+4,SPRITES);self.put(RENDER+0xc,BANK)
        self.top=ASSETS;self.headers=[];self.palette=self.store(rom['palettes'][0]['data'])
        self.put(BANK+4,1,self.palette)
        self.images=[];self.image_dimensions=[]
        for i,im in enumerate(rom['images']):
            require(im['tag']==b'PCX_RWIF' and im['data'][:4]==bytes.fromhex('0a050108'),'Source PCX format')
            x0,y0,x1,y1=struct.unpack_from('<4H',im['data'],4)
            width,height=x1-x0+1,y1-y0+1
            # Header-only fixture for native initializer reads; no image decode
            # or device drawing is claimed. Source dimensions and palette only.
            header=bytearray(128);struct.pack_into('<HH',header,0,width,height)
            struct.pack_into('<I',header,8,self.palette)
            ptr=self.store(header);self.images.append(ptr);self.image_dimensions.append([width,height])
            self.put(BANK+0x8c+4*i,ptr)
        self.put(BANK+0x108c,len(rom['actions']))
        for i,a in enumerate(rom['actions']):
            h=bytearray(0x640);h[:48]=a['data']
            for n,step in enumerate(a['steps']):struct.pack_into('<I',h,0x30+4*n,self.store(step['data']))
            for n,pool in enumerate(a['pools']):struct.pack_into('<I',h,0x630+4*n,self.store(pool['data']))
            ptr=self.store(h);self.headers.append(ptr);self.put(BANK+0x1090+4*i,ptr)
        # Original static RECT already initialized: no CRT atexit fixture.
        self.put(0x5b5660,1)
        self.put(UI+0x86874,QUEUE)
        self.put(MANAGER+8,INPUT);self.put(POOL+0x60,MANAGER)
        for i in range(256):self.put(POOL+0x70+472*i,0xffffffff)
        self.pcs={};self.trace=[];self.steps=0;self.apis=[]
        v.hook_add(UC_HOOK_CODE,self.code)

    def put(self,at,*values):self.v.mem_write(at,struct.pack('<'+'I'*len(values),*(n&0xffffffff for n in values)))
    def word(self,at):return struct.unpack('<I',self.v.mem_read(at,4))[0]
    def half(self,at):return struct.unpack('<H',self.v.mem_read(at,2))[0]
    def store(self,data):
        at=self.top;self.top+=(len(data)+15)&~15
        require(self.top<=ASSETS+0x100000,'Relocation budget');self.v.mem_write(at,bytes(data));return at
    def code(self,v,at,size,_):
        self.steps+=1
        if at in (API,API+16):
            sp=v.reg_read(x.UC_X86_REG_ESP);ret=self.word(sp)
            if at==API:
                args=[self.word(sp+4+4*i) for i in range(5)]
                self.put(args[0],*args[1:]);cleanup=20;result=1;self.apis.append('SetRect')
            else:cleanup=0;result=2001;self.apis.append('timeGetTime')
            v.reg_write(x.UC_X86_REG_EAX,result);v.reg_write(x.UC_X86_REG_ESP,sp+4+cleanup)
            v.reg_write(x.UC_X86_REG_EIP,ret);return
        require(BASE<=at<0x570000 and at!=0x402c70,'Unexpected execution/assert '+hex(at))
        rva=at-BASE
        require(self.image[rva:rva+size]==self.saved[rva:rva+size], 'Executed pinned code mismatch '+hex(at))
        require(bytes(v.mem_read(at,size))==self.image[rva:rva+size],'Code modified '+hex(at))
        self.pcs[at]=size
        if at in ENTRIES:self.trace.append(hex(at))
    def call(self,va,obj,args=(),cleanup=None):
        self.put(SP,STOP,*args);self.steps=0;self.trace=[];self.apis=[]
        self.v.reg_write(x.UC_X86_REG_ESP,SP);self.v.reg_write(x.UC_X86_REG_ECX,obj)
        self.v.reg_write(x.UC_X86_REG_EFLAGS,2)
        self.v.emu_start(va,STOP,count=300000)
        require(self.v.reg_read(x.UC_X86_REG_EIP)==STOP,'Native return/budget '+hex(va))
        require(self.v.reg_read(x.UC_X86_REG_ESP)==SP+4+(4*len(args) if cleanup is None else cleanup),'Native stack '+hex(va))
        return self.v.reg_read(x.UC_X86_REG_EAX)

    def render(self,tile,model,placement,palette):
        fields=tile['fields'];key=fields[4]
        self.put(DATA+0x2c,DATA+0x200,0,0,palette,0xffffffff)
        self.put(DATA+0x208,DATA+0x400)
        self.put(DATA+0x260,model['frame_offsets'][1])
        self.put(DATA+0x414,7)
        self.put(DATA+0x434,0,key)
        action=self.rom['actions'][key-1001];step=action['steps'][0]['data']
        terminal=next(i for i in range(0,len(step),10) if step[i]==0)
        image_id=struct.unpack_from('<H',action['pools'][step[terminal+3]]['data'],6)[0]
        self.put(DATA+0x478,self.images[image_id])
        self.call(0x44a800,DATA+0x400,[fields[1],fields[2]])
        require(self.word(DATA+0x404)==1,'Native tile-frame count from source dimensions')
        before=bytes(self.v.mem_read(POOL,0x20000))
        self.call(0x4421f0,DATA,[placement['fields'][1],placement['fields'][2],RENDER,0])
        handle=self.word(DATA+0x3c);require(handle<4096,'Native model render handle')
        node=RENDER+0x10+handle*0x290;sprite=self.half(node+0xe)
        require(self.word(node+0x38)==self.headers[key-1001],'Original ACT_DATA binding')
        require(self.half(node+0x2c)==0 and self.word(node+0x44)==self.palette,'Field9 is bounded palette')
        require(self.word(SPRITES+0x12ec+sprite*200)==self.palette,'Sprite palette binding')
        require(self.word(MANAGER+0xa7e001c)==0,'Rendering unexpectedly registers interaction object')
        require(bytes(self.v.mem_read(POOL,0x20000))==before,'Rendering modifies NPC pool')
        require(self.word(QUEUE+0x36c4)==0,'Rendering emits C2S')
        return {'placement_model':placement['fields'][0],'action_key':key,'field9_fixture':palette,
                'source_field9':placement['fields'][9],'tile_frame_count':self.word(DATA+0x404),
                'source_image_dimensions':self.image_dimensions[image_id],'render_handle':handle,'sprite':sprite,
                'bound_action_ordinal':key-1001,'palette_index':self.half(node+0x2c),
                'interaction_objects':0,'npc_pool_unchanged':True,'queue_bytes':0,
                'native_return':True,'trace':self.trace,'os_adapters':self.apis,'steps':self.steps}

    def hit(self,category,identity=None,match=True):
        # Three registered interaction objects with only ordinal2 active. The
        # object is a synthetic positive control, not a source board/NPC join.
        idx=2;obj=MANAGER+0x1c+idx*0xa7e0
        self.put(MANAGER+0xa7e001c,3);self.put(obj,2)
        self.put(obj+8,0xffffffff);self.v.mem_write(obj+0xc,b'\xff\xff')
        self.put(obj+0x10,7);self.v.mem_write(obj+0x2a,b'\xff\xff')
        self.call(0x508780,MANAGER,[idx,category])
        require(self.word(obj+0xa7d0)==category,'Native interaction category setter')
        self.put(INPUT+7*24,1);self.put(INPUT+7*24+20,1);self.put(INPUT+0x1202c,1)
        ret=self.call(0x50aa20,MANAGER,[0,0,DATA+0x800])
        hit_trace=self.trace[:]
        expected=idx if category<7 else 65535
        require(ret==(1 if category<7 else 0),'Native hit return')
        for c in range(7):
            require(self.half(MANAGER+0xa7e005a+12*c)==(expected if c==category else 65535),'Hit registry category/ordinal')
        slot=11
        if identity is not None:
            self.put(POOL+0x70+472*slot,identity)
            self.v.mem_write(POOL+0x7c+472*slot,struct.pack('<H',idx if match else 1001))
        result=self.call(0x4cad10,POOL,[DATA+0x800,0,0 if category!=5 else 1,DATA+0x804])
        success=identity is not None and match and category in (4,5)
        require(result==(0x37 if success else 0xffffffff),'NPC pool matching contract')
        require(self.word(DATA+0x800)==(slot if success else 0),'NPC selected pool slot')
        require(self.word(DATA+0x804)==(slot if success else 0xffffffff),'NPC hover pool slot')
        npc_trace=self.trace[:];queue=''
        if success and category==4:
            got=self.call(0x4ccfe0,POOL,[slot]);require(got==identity,'Actor identity lookup')
            self.call(0x496750,UI,[got]);size=self.word(QUEUE+0x36c4)
            queue=bytes(self.v.mem_read(QUEUE+0x36c8,size)).hex()
            require(queue==struct.pack('<BI',0x37,identity).hex(),'C2S37 identity preservation')
        else:require(self.word(QUEUE+0x36c4)==0,'No producer for unbound/category5 path')
        return {'fixture':'synthetic registered interaction ordinal2; completed primitives, not world caller/mouse',
                'category':category,'actor_identity':identity,'matching_handle':match,'hit_return':ret,
                'npc_result':result,'selected_slot':self.word(DATA+0x800),
                'logical_hex':queue,'producer_invoked':success and category==4,'hit_trace':hit_trace,'npc_trace':npc_trace,'native_return':True}


    def world_slice(self,dx,dy):
        # Native caller block, not a replacement reconstruction. The full
        # world event pump is intentionally outside this bounded execution.
        world=0x50000000;pool=world+0x1539aed8;ui=world+0xa7f2f6c
        for start,size in ((world,4096),(world+0xa7e0000,4096),
                           (world+0xa7f2000,0x240000),(world+0x1539a000,0x22000)):
            self.v.mem_map(start,size)
        self.v.mem_write(pool,bytes(self.v.mem_read(POOL,0x20000)))
        self.put(pool+0x80+11*472,100,200)
        self.put(world+0x224,100+dx,200+dy)
        self.put(world+0xa7e05c8,INPUT);self.put(ui+0x86874,QUEUE)
        self.put(QUEUE+0x36c4,0);self.v.mem_write(QUEUE+0x36c8,bytes(16))
        self.put(SP+0xa4,0)
        self.v.reg_write(x.UC_X86_REG_ESP,SP);self.v.reg_write(x.UC_X86_REG_ESI,world)
        self.trace=[];self.steps=0;self.apis=[]
        self.v.emu_start(0x466d3f,0x466e20,count=300000)
        require(self.v.reg_read(x.UC_X86_REG_EIP)==0x466e20,'World caller slice end')
        require(self.v.reg_read(x.UC_X86_REG_ESP)==SP,'World caller slice balanced stack')
        count=self.word(QUEUE+0x36c4);wire=bytes(self.v.mem_read(QUEUE+0x36c8,count)).hex()
        expected='3778563412' if abs(dx)<=3 and abs(dy)<=3 else ''
        require(wire==expected,'Original world distance gate/identity producer')
        return {'scope':'466D3F..466E20 bounded original caller, not whole event pump',
                'synthetic_actor':0x12345678,'delta':[dx,dy],'logical_hex':wire,
                'trace':self.trace,'steps':self.steps,'native_slice_end':True}


def run():
    raw=(CLIENT/'God2.exe').read_bytes();require(sha(raw)==PE_PIN,'Current PE pin')
    image=pefile.PE(data=raw).get_memory_mapped_image()
    saved=(ROOT/'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin').read_bytes()
    require(sha(saved)==IMAGE_PIN,'Mapped image pin')
    romraw=(CLIENT/'Data2/map/island01/cityi1/npcad.ROMZ').read_bytes();plain=decode_csvz(romraw)
    require(sha(romraw)=='5cd0a3d02f870e5b9b073f6bebf109632650e587cb8f1290a6db464e894687e5','ROM pin')
    require(sha(plain)=='2de80c9ad04f3f46d5af5b38272d31036960b9c8273fae1fbde654ef5ee62a32','Decoded ROM pin')
    rom=parse_rom(plain,name_encoding='cp950')
    require([len(rom[k]) for k in ('palettes','images','actions')]==[1,10,6],'Source ROM counts')
    mdlraw=(CLIENT/'Data2/map/island01/cityi1/cityI1.mdlZ').read_bytes();mdlplain=decode_csvz(mdlraw)
    require(sha(mdlraw)=='bb2b72c2cb368ad9e91046783e1c9638ef02318f589cf462f0c45bbfdce04618','MDL pin')
    require(sha(mdlplain)=='59fd88e12c232c89ae8cb73fed4058090e708f963fc9525ededfe157fccfebef','Decoded MDL pin')
    mdl=parse_mdl(mdlplain,allow_parent_rom=True)
    selected=[(i,p) for i,p in enumerate(mdl['placements']) if p['fields'][0] in range(161,167)]
    require([i for i,p in selected]==[134,135,138],'Three original placements')
    renders=[];lookups=[];hits=[];worlds=[];pcs={}
    for idx,p in selected:
        model=mdl['models'][p['fields'][0]];tile=mdl['tiles'][model['layers'][0][0]]
        for palette in (0,-1,1,255):
            n=Native(image,saved,rom);r=n.render(tile,model,p,palette);pcs.update(n.pcs)
            r.update(placement_index=idx,source_fields=p['fields'],source_line=mdlplain[:p['offset']].count(b'\n')+1,
                     raw_record_hex=mdlplain[p['offset']:p['end_exclusive']].hex());renders.append(r)
    n=Native(image,saved,rom)
    for key in (0,1,5,6,256,257,1001,1002,1003,1004,1005,1006,1007,65535):
        got=n.call(0x41ae20,0,[BANK,key])
        expected=key if key<6 else key-1001 if 1001<=key<=1006 else 0xffffffff
        require(got==expected,'Native action namespace');lookups.append({'key':key,'ordinal':got})
    pcs.update(n.pcs)
    for cat,identity,match in ((4,None,True),(5,None,True),(4,0x12345678,True),
                               (5,0x12345678,True),(4,1001,False),(4,1001,True),(7,1001,True)):
        n=Native(image,saved,rom);hits.append(n.hit(cat,identity,match));pcs.update(n.pcs)
    for dx,dy in ((0,0),(3,3),(4,0),(0,-4)):
        n=Native(image,saved,rom);n.hit(4,0x12345678,True)
        worlds.append(n.world_slice(dx,dy));pcs.update(n.pcs)
    static_spans=((0x4c524,0x4c541),(0x66d3f,0x66e20),(0x66f72,0x66ffa),
                  (0xcafe0,0xcb10a),(0xcc380,0xcc837),(0x108780,0x10879f))
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
    static=[]
    for start,end in static_spans:
        require(image[start:end]==saved[start:end],'Static evidence code mismatch')
        static.append({'start_rva':hex(start),'end_rva':hex(end),'sha256':sha(image[start:end]),
                       'disassembly':['%08X %s %s'%(i.address,i.mnemonic,i.op_str)
                                      for i in md.disasm(image[start:end],BASE+start)]})
    encoded=b''.join(struct.pack('<II',at,size)+image[at-BASE:at-BASE+size] for at,size in sorted(pcs.items()))
    return {'status':'PASS','current_pe_sha256':PE_PIN,'mapped_sha256':IMAGE_PIN,
            'counts':{'complete_model_render_cases':len(renders),'action_lookup_cases':len(lookups),
                      'complete_hit_and_npc_gate_cases':len(hits),'bounded_world_caller_cases':len(worlds),'qualified_interactive_source_boards':0},
            'rom':{'path':'Data2/map/island01/cityi1/npcad.ROMZ','sha256':sha(romraw),'decoded_sha256':sha(plain),
                   'palettes':1,'images':10,'actions':[{'meta':a['meta'],'name':a['name'],'raw_header_hex':a['data'].hex(),
                                                      'offset':a['offset'],'sha256':sha(a['data'])} for a in rom['actions']]},
            'mdl':{'sha256':sha(mdlraw),'decoded_sha256':sha(mdlplain)},
            'static_spans':static,'render_cases':renders,'action_lookups':lookups,'hit_cases':hits,'world_caller_cases':worlds,
            'executed_instructions':len(pcs),'executed_instruction_address_size_bytes_sha256':sha(encoded),
            'executed_instruction_ranges':[[hex(at),size] for at,size in sorted(pcs.items())],
            'limitations':['Original action/palette relocation and header-only image fixtures from source PCX dimensions; not native ROM file loader, pixel decoder, or device blitter.',
                           'Hit positive controls explicitly synthetic; no source world NPC identity.',
                           'Completed render/hit/NPC/producer primitives; whole world input dispatcher and physical mouse not executed.',
                           'No source-backed interactive spawn configuration recovered.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    require(a.output.resolve().is_relative_to((ROOT/'artifacts/research/npc-model-interaction-20260927').resolve()),'Output scope')
    result=run();a.output.parent.mkdir(parents=True,exist_ok=True)
    pending=a.output.with_suffix('.pending');pending.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');pending.replace(a.output)
    print(json.dumps(result['counts']))


