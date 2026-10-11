"""Current pinned x86 armor tooltip/stats/DA projection, no UI or authority claim.

Reuses only VM scaffolding/methods, never old audit pins or retired captures.
The tested EXE is current c5d8; every executed instruction matches qualified
original image149c. Only external sprintf CRT is adapted; tested consumers run.
"""
import argparse,hashlib,json,random,re,struct
from pathlib import Path
import pefile
import unicorn as uc
from unicorn import x86_const as x
from tools.strike_lab.current_protocol_coverage import qualified_image,NativeLengths
from tools.strike_lab.current_weapon_attributes_native_20260926 import Probe,ACTOR,GOD
from tools.strike_lab.current_dialogue_mode4_native_20260926 import UI,RESOURCE,TABLE,STRINGS,PACKET,RETURN,SP
from tools.strike_lab.current_weapon_appearance_20260926 import Oracle as DaMethods
from tools.strike_lab.current_weapon_appearance_20260926 import BASE,WORLD,STACK,DATA,MANAGER
from tools.strike_lab.omega_assets import decode_csvz
ROOT=Path(__file__).resolve().parents[2]
LIVE=ROOT.parent/'God2/God2.exe'
PIN='c5d8f79baa36879851703ac05d2b5caddf44a907677f7de114f568eeaf14f575'

def require(yes,reason):
    if not yes:raise RuntimeError(reason)
def sha(data):return hashlib.sha256(data).hexdigest()

class ArmorProbe(Probe):
    def __init__(self,pe,original):
        super().__init__(pe)
        self.original=original;self.unpacked=[];self.formatted=[];self.visited=set()
        self.vm.hook_add(uc.UC_HOOK_CODE,self.trace)
    def cstring(self,p):
        if not p:return b'(null)'
        out=bytearray()
        for i in range(2048):
            b=self.vm.mem_read(p+i,1)[0]
            if not b:return bytes(out)
            out.append(b)
        raise RuntimeError('CString budget')
    def trace(self,v,a,n,_):
        if a==RETURN:return
        require(bytes(v.mem_read(a,n))==self.original[a-BASE:a-BASE+n],f'Current/original instruction changed {a:x}')
        self.visited.add((a,n))
        sp=self.reg('ESP')
        if a==0x4b4200:
            values=self.read(sp+12,'I');labels=self.read(sp+16,'I')
            self.unpacked.append({'values':list(struct.unpack('<6H',v.mem_read(values,12))),
                                  'labels':list(struct.unpack('<6H',v.mem_read(labels,12)))})
        if a!=0x547af7:return
        # External cdecl sprintf. No gameplay/UI consumer is replaced.
        destination=self.read(sp+4,'I');fmt=self.cstring(self.read(sp+8,'I'))
        position=0;arg=sp+12;output=bytearray();observed=[]
        for match in re.finditer(rb'%(?:[-+ #0]*[0-9]*(?:\.[0-9]+)?)?([sduXx%])',fmt):
            output+=fmt[position:match.start()];kind=match[1]
            if kind==b'%':value=None;out=b'%'
            else:
                value=self.read(arg,'I');arg+=4
                if kind==b's':out=self.cstring(value)
                elif kind==b'd':out=str(value if value<0x80000000 else value-0x100000000).encode()
                elif kind==b'u':out=str(value).encode()
                else:out=format(value,'X' if kind==b'X' else 'x').encode()
            observed.append({'type':kind.decode(),'raw':value,'text_hex':out.hex()});output+=out;position=match.end()
        output+=fmt[position:];require(len(output)<2048,'Formatter output budget')
        self.formatted.append({'format_hex':fmt.hex(),'arguments':observed})
        v.mem_write(destination,bytes(output)+b'\0');ret=self.read(sp,'I')
        self.setreg('EAX',len(output));self.setreg('ESP',sp+4);self.setreg('EIP',ret)

class DAOracle(DaMethods):
    def __init__(self,image):
        self.image=image;self.v=v=uc.Uc(uc.UC_ARCH_X86,uc.UC_MODE_32)
        v.mem_map(BASE,(len(image)+4095)&~4095,uc.UC_PROT_READ|uc.UC_PROT_EXEC);v.mem_write(BASE,image)
        for a,n in ((STACK,0x10000),(DATA,0x10000),(MANAGER&~4095,0x19000),(WORLD+0xaa36000,0x171000)):v.mem_map(a,n)
        self.ranges=();self.stops=set();self.writes=()
        v.hook_add(uc.UC_HOOK_CODE,self.code);v.hook_add(uc.UC_HOOK_MEM_WRITE,self.write)

def program_fixture(n,program):
    n.write(RESOURCE+0xb2c6c,'h',1100);n.write(RESOURCE+0xb2c68,'I',TABLE+0x2000)
    top=STRINGS+0x1000
    for key,text in program.items():
        if key>1100:continue
        n.write(TABLE+0x2000+(key-1)*4,'I',top);n.vm.mem_write(top,text+b'\0');top+=len(text)+1

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,default=ROOT/'artifacts/research/current-armor-projection-20261002/native.json');args=ap.parse_args()
    original=qualified_image();raw=LIVE.read_bytes();require(sha(raw)==PIN,'Current EXE changed')
    pe=pefile.PE(data=raw);image=pe.get_memory_mapped_image()
    ranges=((0x4b4200,0x4b4770),(0x4e6600,0x4e6b40),(0x547b80,0x547c7e),
            (0x469369,0x4693cc),(0x469523,0x469541),(0x4fc990,0x4fc9d0),
            (0x503d30,0x503d88),(0x503f61,0x503f94),(0x4fc130,0x4fc1b4),
            (0x4ff450,0x4ff480),(0x4ffa20,0x4ffa50),(0x503ff4,0x504018))
    for a,z in ranges:require(image[a-BASE:z-BASE]==original[a-BASE:z-BASE],f'Projection region changed{a:x}')
    message=(LIVE.parent/'Data2/Patch/Comm/message.csvZ').read_bytes()
    require(sha(message)=='5cd34cce66feae96d947cd45e32984765ce625673c0fb19c73cb63d7d9178598','message pin changed')
    program={};inside=False
    for row in decode_csvz(message).splitlines():
        if row.startswith(b'ProgramMsg,'):inside=True;continue
        f=row.split(b',',1)
        if inside and len(f)==2 and f[0].isdigit():program[int(f[0])]=f[1]
    labels={i:program[i].decode('cp950') for i in (521,523,74,73,72,75)}
    rng=random.Random(20261002);unpack=[];visits=set()
    # Full4B4690->4B4200 return, observed actual six packed values and
    # original formatter endpoints with/without metadata variance bytes.
    for i in range(66):
        data=bytearray(bytes(20) if i==0 else bytes([255])*20 if i==1 else rng.randbytes(20))
        data[15]&=0xc7 # qualified ordinary quality0; no arbitrary negative prefix pointer
        for variance in ((0,0),(5,3)):
            n=ArmorProbe(pe,original);n.vm.mem_write(PACKET,bytes(data));n.write(TABLE+0x11c,'BB',*variance)
            # Native ProgramMsg lookup table; all requested strings retain source bytes.
            program_fixture(n,program)
            n.setup(PACKET,TABLE,STRINGS);n.run(0x4b4690,[RETURN])
            require(n.reg('ESP')==SP+16,'Armor full return stack imbalance')
            b=data[19];expected=[data[7]+((b>>4)&3)*256,data[12]+(b>>6)*256]+[data[8+j]+((b>>j)&1)*256 for j in range(4)]
            require(n.unpacked==[{'values':expected,'labels':[521,523,74,73,72,75]}],'Armor values/labels differ')
            endpoints=[f['arguments'][-2:] for f in n.formatted if len(f['arguments'])==3 and f['arguments'][-1]['type']=='d' and f['arguments'][-2]['type']=='d']
            if variance!=(0,0):require([[a['raw'] for a in f] for f in endpoints]==[[(expected[0]-5)&0xffffffff,expected[0]+5],[(expected[1]-3)&0xffffffff,expected[1]+3]],'Native armor tooltip variance differs')
            require(bytes(n.vm.mem_read(PACKET,20))==data,'Armor instance mutated')
            visits.update(n.visited);unpack.append({'instance_hex':data.hex(),'metadata_variance':variance,'values':expected,'full_return':True,'formatter_ranges':endpoints})
    # Bounded original tooltip family dispatch. Executes the load from actual
    # local-frame argument cell, bit extraction and jump-table branch. All 64
    # families are controls; this does not claim whole giant GUI tooltip return.
    class_regions=((0x4b6414,0x4b6447),(0x4bc188,0x4bc1f3),
                   (0x4b8bee,0x4b8e6e),(0x4b4060,0x4b4200))
    for a,z in class_regions:require(image[a-BASE:z-BASE]==original[a-BASE:z-BASE],f'Family region changed{a:x}')
    targets={f:struct.unpack_from('<I',original,0xbc188+original[0xbc1d0+f-1]*4)[0]
             if 1<=f<=35 else 0x4ba850 for f in range(64)}
    require(targets[1]==targets[25]==0x4b88e3 and targets[2]==targets[26]==0x4b8bee,'Native family branch table changed')
    family=[]
    for f in range(64):
        for surrounding in (0,0xa580ffff):
            header=(surrounding&~0x3f0000)|(f<<16)
            n=ArmorProbe(pe,original);n.write(PACKET,'I',header);n.setup()
            n.write(SP+0x11ac,'I',PACKET);n.setreg('EDX',0)
            n.run(0x4b6414,set(targets.values()))
            require(n.reg('EIP')==targets[f],'Native family dispatch mismatch')
            visits.update(n.visited);family.append({'firstDWORD':header,'family':f,'stop':hex(n.reg('EIP'))})
    family_full=[]
    for f in (2,26):
        for bound in (0,0x80000000):
            n=ArmorProbe(pe,original);program_fixture(n,program)
            n.write(PACKET,'I',bound|(f<<16));n.setup()
            n.write(SP+0x11a8,'I',TABLE);n.write(SP+0x11ac,'I',PACKET)
            n.vm.mem_write(SP+0x3bc,b'\0');n.setreg('EBP',UI);n.setreg('EDX',0)
            n.run(0x4b6414,[0x4b8b5e])
            require(n.reg('ESP')==SP,'Family-to-unpack bounded return stack imbalance')
            require(n.unpacked==[{'values':[0]*6,'labels':[521,523,74,73,72,75]}],'Family did not execute armor unpacker')
            visits.update(n.visited);family_full.append({'family':f,'boundbit':bool(bound),
                'from':'0x4b6414','stop':'0x4b8b5e','unpacker':'0x4b4690','stack_balanced':True})
    stats=[]
    for sheet in (-1,0):
        for positive,negative in ((0,0),(15,0),(0,15),(15,15),(5,10)):
            for magnitude in (0,511,0x7fff,0x8000,0xffff):
                n=ArmorProbe(pe,original);n.write(UI+0x232dda,'h',sheet);n.write(ACTOR+0x5c,'4I',123,456,78,901)
                n.write(ACTOR+0x78,'4I',11,22,33,44)
                before=bytes(n.vm.mem_read(ACTOR,4096));gb=bytes(n.vm.mem_read(GOD,4096));expected=bytearray(before)
                vals=[magnitude|0xa55a0000]*4+[101,102,103,104,105,positive,negative,0,0x7fffffff,0x80000000,0xffffffff]
                body=struct.pack('<15I',*vals);n.vm.mem_write(PACKET,body);n.setup(PACKET);n.run(0x4e6600,[RETURN])
                require(n.reg('ESP')==SP+8,'2C return stack imbalance')
                for i,off in enumerate((0x88,0x8a,0x8c,0x8e)):
                    bit=(2,4,1,8)[i];value=(-magnitude if negative&bit and not positive&bit else magnitude)&0xffff
                    struct.pack_into('<H',expected,off,value)
                for source,dest,size in ((16,0xa4,20),(36,0xb8,2),(40,0xba,2),(44,0x98,4),(48,0x94,4),(52,0xa0,4),(56,0x9c,4)):expected[dest:dest+size]=body[source:source+size]
                require(bytes(n.vm.mem_read(ACTOR,4096))==expected,'2C exact actor snapshot differs')
                require(bytes(n.vm.mem_read(GOD,4096))==gb,'2C wrote God memory')
                require(not any(c['va'] in ('0x5060f0','0x505680','0x505110') for c in n.observed),'2C wrote HUD')
                visits.update(n.visited);stats.append({'sheet':sheet,'positive':positive,'negative':negative,'magnitude_low16':magnitude,'logical_hex':'2c'+body.hex(),'signed_modifiers':[n.read(ACTOR+o,'h') for o in (0x88,0x8a,0x8c,0x8e)],'full_return':True,'base_vitals_god_unchanged':True,'native_UI_calls':n.observed})
    d=DAOracle(image);dacases=0
    for local in (1,217,0xffff):
        for identity,remote in ((local,False),(local-1 if local>1 else 2,False),(local-1 if local>1 else 2,True)):
            for selector,accessory in ((0,0),(27,3),(91,119)):d.route(local,identity,remote,selector,accessory);dacases+=1
    for override in (False,True):
        for variant in range(8):d.setters(override,variant);dacases+=1
    for block in (bytes(8),bytes(range(8)),bytes([255])*8):d.persist(block);dacases+=1
    result={'status':'PASS','current_client_sha256':sha(raw),'mapped_image_sha256':sha(original),
            'scope':'current executable machine consumers; external sprintf only adapted; no real UI/network/server authority',
            'cases':len(unpack)+len(stats)+dacases+len(family)+len(family_full),'armor_unpack_full_return_cases':unpack,'labels':labels,'2C_cases':stats,'DA_cases':dacases,
            'family_dispatch_cases':family,'family_to_unpack_cases':family_full,
            'native_lengths':{hex(o):NativeLengths(original).query(o)[0] for o in (0x2c,0xda)},
            'matched_regions':[[hex(a),hex(z)] for a,z in ranges+class_regions],
            'actual_executed_instruction_count':len(visits),
            'contract':{'family':'Native4B6414..4B6440 extracts firstDWORD bits16..21: families2/26 route4B8BEE to actual4B4690; families1/25 route weapon4B88E3. This proves type interpretation, not armor slot source mapping.',
                        'armor20':'4B4690 physicaldefense=byte7+256*((byte19>>4)&3); magicdefense=byte12+256*(byte19>>6); str/con/int/speed=byte8..11+256*((byte19>>0..3)&1)',
                        'tooltip':'metadata11C/11D give displayed +/- ranges around instance center; not a server generation roll/formula',
                        '2C61':'four lowWORD modifiers @1/5/9/13; elementDWORDs@17/21/25/29/33; positive/negative lowWORD@37/41; physicaldefenseDWORD@45,physicalattack@49,magicdefense@53,magicattack@57; self only no identity',
                        '2Climits':'modifiers are signed16 after sign mask with positive precedence; raw highWORD ignored; combat/element rawDWORD preserved, display formatter signed%d; no authoritative calculation or maximumHP/MP update',
                        'DA15':'identityWORD@1 unmasked; transformWORD@3; scalarsBYTE@5/6; packed8components@7; exact self identity or existingremote lookup; missingremote ignored; no direction/orientation field',
                        'DAapply':'remote4FC130 actual all4 handles and variant high3bits updated, direction/canary unchanged; local8byte persistence before501810; full resolver/resource/render chain not executed here'},
            'unproved':['EQU/TEQ item to HeroDoll selector mapping','armor family-to-slot source authority','original final-stat/equipment generation/stacking formulas','which armor pieces change world components','full world renderer and live UI acceptance','mid-session22/24 refresh eligibility']}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf-8')
    print('PASS',result['cases'],'current armor unpack/2C/DA cases',args.output)
if __name__=='__main__':main()
