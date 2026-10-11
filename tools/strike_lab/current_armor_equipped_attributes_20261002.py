"""Bounded armor20 versus self2C/base22 native consumers and status formatting.

No UI, processes, sockets, DB or client writes. Original instructions execute;
only the external CRT sprintf adapter from ArmorProbe is reused. Arbitrary
instances and stat snapshots are differential inputs, not recovered formulas.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import pefile
import unicorn as uc
from tools.strike_lab.current_protocol_coverage import qualified_image,NativeLengths
from tools.strike_lab.current_armor_projection_20261002 import ArmorProbe,program_fixture
from tools.strike_lab.current_armor_appearance_20261002 import Items
from tools.strike_lab.current_weapon_attributes_native_20260926 import ACTOR,GOD
from tools.strike_lab.current_dialogue_mode4_native_20260926 import UI,TABLE,STRINGS,PACKET,RETURN,SP
from tools.strike_lab.current_item_transition import UI as ITEM_UI,PACKET as ITEM_PACKET,SLOTS
from tools.strike_lab.omega_assets import decode_csvz

ROOT=Path(__file__).resolve().parents[2]
LIVE=ROOT.parent/'God2/God2.exe'
PIN='c5d8f79baa36879851703ac05d2b5caddf44a907677f7de114f568eeaf14f575'
BASE=0x400000
ROLE=0x7000000
OUTPUT=ROOT/'artifacts/research/current-armor-equipped-attributes-20261002'
CONTRACT=ROOT/'artifacts/research/native-armor-transfer-20261002/candidate-01/contract.json'

def require(value,reason):
    if not value:raise RuntimeError(reason)
def sha(raw):return hashlib.sha256(raw).hexdigest()

def instance(key,values):
    pdef,mdef,con,strength,intelligence,speed=values
    data=bytearray(struct.pack('<HH',key,2)+bytes(16))
    data[7]=pdef&255;data[12]=mdef&255
    data[8:12]=bytes(x&255 for x in (con,strength,intelligence,speed))
    data[19]=((pdef>>8)<<4)|((mdef>>8)<<6)|sum((v>>8)<<i for i,v in enumerate((con,strength,intelligence,speed)))
    return bytes(data)

class StatProbe(ArmorProbe):
    def __init__(self,pe,original):
        super().__init__(pe,original)
        self.phase='setup';self.role_accesses=[];self.inventory_accesses=[];self.status_formats=[]
        self.vm.hook_add(uc.UC_HOOK_MEM_READ|uc.UC_HOOK_MEM_WRITE,self.role_access)
        self.vm.hook_add(uc.UC_HOOK_CODE,self.status)
    def role_access(self,v,access,a,n,value,_):
        if ACTOR+0x58<=a<ACTOR+0xbc:
            self.role_accesses.append({'phase':self.phase,'pc':hex(self.reg('EIP')),'write':access==uc.UC_MEM_WRITE,'offset':hex(a-ACTOR),'size':n})
        if UI+0x8560c<=a<UI+0x8560c+50*24:
            self.inventory_accesses.append({'phase':self.phase,'pc':hex(self.reg('EIP')),'offset':a-(UI+0x8560c),'size':n})
    def status(self,v,a,n,_):
        if a!=0x5077c0:return
        sp=self.reg('ESP');control=self.read(sp+12,'I')&65535
        fmt=self.cstring(self.read(sp+16,'I'))
        self.status_formats.append({'phase':self.phase,'control':control,'format_hex':fmt.hex(),
                                    'value_raw':self.read(sp+20,'I')})
    def call(self,address,*args,phase):
        self.phase=phase;self.setup(*args);self.run(address,[RETURN])
        require(self.reg('ESP')==SP+4+4*len(args),'Native stat stack differs '+hex(address))

def role_snapshot(n):
    return {'base':list(struct.unpack('<4I',n.vm.mem_read(ACTOR+0x78,16))),
            'modifier':list(struct.unpack('<4h',n.vm.mem_read(ACTOR+0x88,8))),
            'attack_defense':list(struct.unpack('<4I',n.vm.mem_read(ACTOR+0x94,16))),
            'elements':list(struct.unpack('<5I',n.vm.mem_read(ACTOR+0xa4,20))),
            'vitals':list(struct.unpack('<4I',n.vm.mem_read(ACTOR+0x5c,16)))}

def target_xrefs(image,targets):
    # Bounded direct-call references to two already identified functions only.
    out=[];at=image.find(b'\xe8',0x1000,0x147000)
    while at>=0:
        target=BASE+at+5+struct.unpack_from('<i',image,at+1)[0]
        if target in targets:out.append({'caller':hex(BASE+at),'callee':hex(target)})
        at=image.find(b'\xe8',at+1,0x147000)
    return out

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output-dir',type=Path,default=OUTPUT);args=parser.parse_args()
    original=qualified_image();raw=LIVE.read_bytes();require(sha(raw)==PIN,'Current EXE differs')
    pe=pefile.PE(data=raw);mapped=pe.get_memory_mapped_image()
    guards=json.loads(CONTRACT.read_text('utf-8'))['source_sha256']
    require(all(sha((ROOT/name).read_bytes())==digest for name,digest in guards.items()),'Frozen runtime20 differs before research')
    spans=((0x4e6600,0x4e6b40),(0x4e6b40,0x4e6bf0),(0x4e6db0,0x4e717a),
           (0x4e8509,0x4e8521),(0x498dd0,0x498fc0),(0x4991e0,0x4992f8),
           (0x49a330,0x49b664),(0x496550,0x496610),(0x4b4690,0x4b4770))
    for a,z in spans:require(mapped[a-BASE:z-BASE]==original[a-BASE:z-BASE],'Current/native span differs '+hex(a))
    message=(LIVE.parent/'Data2/Patch/Comm/message.csvZ').read_bytes()
    require(sha(message)=='5cd34cce66feae96d947cd45e32984765ce625673c0fb19c73cb63d7d9178598','Message source differs')
    program={};inside=False
    for row in decode_csvz(message).splitlines():
        if row.startswith(b'ProgramMsg,'):inside=True;continue
        fields=row.split(b',',1)
        if inside and len(fields)==2 and fields[0].isdigit():program[int(fields[0])]=fields[1]
    records=json.loads((ROOT/'artifacts/research/native-armor-20261002/records.json').read_text('utf-8'))
    keys=(1201,1001,1501,1601)
    definitions={row[1]:{'record':bytes.fromhex(row[8]),'raw':bytes.fromhex(row[6])} for row in records[1] if row[1] in keys}
    require(set(definitions)==set(keys),'Four-part source definitions absent')
    # Deliberately distinctive center operands, not native item-generation data.
    centers=((11,21,31,41,51,61),(12,22,32,42,52,62),(13,23,33,43,53,63),(14,24,34,44,54,64))
    instances=[instance(key,values) for key,values in zip(keys,centers)]
    tooltip=[];visits=set()
    for key,data,values in zip(keys,instances,centers):
        n=StatProbe(pe,original);program_fixture(n,program);n.vm.mem_write(PACKET,data)
        role_before=bytes(n.vm.mem_read(ACTOR,4096));n.call(0x4b4690,PACKET,TABLE,STRINGS,phase='tooltip')
        require(n.unpacked==[{'values':list(values),'labels':[521,523,74,73,72,75]}],'Actual tooltip center mismatch')
        require(bytes(n.vm.mem_read(ACTOR,4096))==role_before and not n.role_accesses,'Tooltip accessed role attributes')
        tooltip.append({'key':key,'instance20':data.hex(),'native_operands':list(values),'labels':[program[i].decode('cp950') for i in (521,523,74,73,72,75)],'role_accesses':0})
        visits.update(n.visited)
    inventory=Items(original,mapped,definitions);inventory.vm.mem_map(ROLE,0x5000)
    inventory.vm.mem_write(ITEM_UI+0x86888,struct.pack('<I',ROLE));actor_access=[]
    inventory.vm.hook_add(uc.UC_HOOK_MEM_READ|uc.UC_HOOK_MEM_WRITE,
        lambda v,access,a,n,val,_:actor_access.append([hex(v.reg_read(uc.x86_const.UC_X86_REG_EIP)),a-ROLE,n,access]) if ROLE<=a<ROLE+0x5000 else None)
    transitions=[]
    for slot,data in zip(range(30,34),instances):
        actor_access.clear();inventory.vm.mem_write(ROLE,b'\xa5'*0x5000)
        inventory.put(slot,data);request=inventory.ui_request(slot)
        inventory.vm.mem_write(ITEM_PACKET,struct.pack('<BHB',1,slot,0)+data);inventory.call(0x98dd0,ITEM_PACKET)
        inventory.vm.mem_write(ITEM_PACKET,struct.pack('<HBB',int.from_bytes(data[:2],'little'),slot,1));inventory.call(0x991e0,ITEM_PACKET)
        require(not actor_access and bytes(inventory.vm.mem_read(ROLE,0x5000))==b'\xa5'*0x5000,'Inventory equip path accessed actor')
        transitions.append({'slot':slot,'key':int.from_bytes(data[:2],'little'),'actual28':request,'3B41_full_return':True,'actor_accesses':0})
    cases=[]
    body=struct.pack('<15I',13,17,19,23,101,102,103,104,105,0,0,2001,2002,2003,2004)
    for sheet in (-1,0):
        for mask in range(16):
            n=StatProbe(pe,original);n.write(UI+0x232dda,'h',sheet);n.write(UI+0x232e50,'h',-1)
            n.write(ACTOR+0x58,'H',0);n.write(ACTOR+0x5c,'4I',123,456,78,901);n.write(ACTOR+0x78,'4I',111,222,333,444)
            for part,data in enumerate(instances):
                n.vm.mem_write(UI+0x8560c+(30+part)*24,(struct.pack('<I',1)+data) if mask&(1<<part) else bytes(24))
            before=role_snapshot(n);n.vm.mem_write(PACKET,body);n.call(0x4e6600,PACKET,phase='consumer2C')
            after2c=role_snapshot(n);n.call(0x4e6db0,ACTOR,phase='base_sheet')
            require(role_snapshot(n)==after2c and after2c['base']==before['base'] and
                    after2c['modifier']==[13,17,19,23] and after2c['attack_defense']==[2002,2001,2004,2003],
                    'Native stat snapshot unexpectedly recomputed from equipment')
            require(not n.inventory_accesses,'Native stat consumer/formatter read equipped instances')
            formats=[x for x in n.status_formats if x['phase']=='base_sheet' and 14<=x['control']<=21]
            if sheet>=0:
                require({x['control']:x['value_raw'] for x in formats}==dict(zip(range(14,22),[111,222,333,444,13,17,19,23])),
                        'Base and modifier display were added together')
            else:require(not formats,'Closed role sheet emitted base/modifier formatting')
            cases.append({'sheet':sheet,'equipped_mask':mask,'before':before,'after2C':after2c,
                          'after_base_refresh':role_snapshot(n),'actual_separate_base_modifier_format_args':formats,
                          'inventory_reads':0,'role_accesses':n.role_accesses})
            visits.update(n.visited)
    integer=[]
    for magnitude,positive,negative in ((13,0,15),(13,15,15),(0x7fff,0,0),(0x8000,0,0),(0xffff,0,0)):
        n=StatProbe(pe,original);n.write(UI+0x232dda,'h',0);n.write(UI+0x232e50,'h',-1)
        n.write(ACTOR+0x78,'4I',111,222,333,444);n.write(ACTOR+0x58,'H',0)
        vals=[0xa55a0000|magnitude]*4+[0]*5+[positive,negative,0x7fffffff,0x80000000,0xffffffff,0x80000001]
        n.vm.mem_write(PACKET,struct.pack('<15I',*vals));n.call(0x4e6600,PACKET,phase='integer2C')
        once=role_snapshot(n);n.call(0x4e6710,ACTOR,phase='raw_repeat_refresh');twice=role_snapshot(n)
        expected=(-magnitude if negative and not positive else magnitude)&65535
        require(once['modifier']==[expected if expected<32768 else expected-65536]*4,'2C lowWORD/sign rule differs')
        require(twice['modifier']==([-x if x!=-32768 else -32768 for x in once['modifier']] if negative and not positive else once['modifier']),
                'Native direct repeated refresh sign behavior differs')
        require(once['base']==twice['base']==[111,222,333,444] and
                once['attack_defense']==twice['attack_defense']==[0x80000000,0x7fffffff,0x80000001,0xffffffff],
                'Raw DWORD snapshot unexpectedly recalculated')
        integer.append({'magnitude_low16':magnitude,'positive':positive,'negative':negative,'logical2C':(b'\x2c'+struct.pack('<15I',*vals)).hex(),
                        'once':once,'direct_repeat':twice,'format_calls':n.status_formats})
        visits.update(n.visited)
    xrefs=target_xrefs(original,{0x4e6710,0x4b4690})
    require(xrefs==[{'caller':'0x4b8e64','callee':'0x4b4690'},{'caller':'0x4e66f8','callee':'0x4e6710'},{'caller':'0x4e8514','callee':'0x4e6710'}],
            'Known targeted callers changed')
    require(all(sha((ROOT/name).read_bytes())==digest for name,digest in guards.items()),'Frozen runtime20 differs after research')
    result={'status':'PASS','current_client_sha256':sha(raw),'original_mapped_sha256':sha(original),
            'tool_sha256':sha(Path(__file__).read_bytes()),'scope':'offline native consumer/formatter differential; no server stat authority, UI/network or rendered acceptance',
            'cases':len(tooltip)+len(transitions)+len(cases)+len(integer),'tooltip_cases':tooltip,'equipment_actor_access_cases':transitions,
            'equipment_independent_stat_cases':cases,'integer_and_repeat_cases':integer,'targeted_direct_call_xrefs':xrefs,
            'native_lengths':{'2C':NativeLengths(original).query(0x2c)[0],'22':NativeLengths(original).query(0x22)[0]},
            'matched_spans':[[hex(a),hex(z)] for a,z in spans],'executed_instruction_count':len(visits),
            'runtime20_preserved':True,
            'contract':{'armor_tooltip_center':'byte7+bits19[4:5]*256 physical defense; byte12+bits19[6:7]*256 magic defense; bytes8..11+bits19[0:3]*256 con/str/int/speed; integer ranges defense0..1023 and modifiers0..511',
                'self2C':'logical61: four DWORD cells@1/5/9/13 consumed lowWORD only, con/str/int/speed; elementDWORDs@17..33; positive/negative lowWORD masks@37/41 bits con2,str4,int1,speed8; defense/attack DWORDs@45/49/53/57 physicaldefense/physicalattack/magicdefense/magicattack',
                'base_vs_modifier':'base22→actor78/7C/80/84;2C→signed16 actor88/8A/8C/8E. Full4E6DB0 sends controls14..17 base and18..21 modifier separately, without summing or reading gear',
                'negative_mask':'4E6710 negates existing WORD when negative-bit-only. Positive wins over negative. Directly repeating this function toggles negative-sign magnitudes; fresh2C replaces raw values before normalization. Another native caller4E8514 exists; full caller lifetime not tested',
                'combat_values':'2C copies final combat DWORDs verbatim; values can exceed signed INT32 but original status %d displays them signed. This is display transport, not a server combat formula',
                'four_part_result':'all16 equipment occupancy masks leave identical2C output; original3B/41 equip-slot30..33 and cached original28 request do not access actor stats in qualified inactive-sprite branch'},
            'open':['original equipped sum/quality/enhancement/buff/set stacking producer','original base→final physical/magic formula','server authoritative generation of20byte instance centers','source itemkey→appearance selector','full4E8514 caller and negative-mask lifecycle'],
            'custom_fallback_inputs_not_approval':{'available':'owned metadata20 key/family strict admission, slot30..33 ownership and four tooltip centers, existing authoritative base state; self2C codec only after separate live refresh acceptance',
                'limits':'do not call tooltip +/- source variance a rolled bonus; do not silently include bag items; overflow/signed16/signmasks and signed%d combat display need explicit policy; no recovered set/enhancement/buff/finalcombat formula; native empty/unknown instance must not create bonus',
                'possible_documented_design':'explicit custom sum of center fields over occupied30..33 only, with lossless wide accumulator and chosen output caps, fresh2C absolute snapshots; this is a proposed CUSTOM design, not native formula or production balance approval'}}
    args.output_dir.mkdir(parents=True,exist_ok=False)
    (args.output_dir/'native.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf-8')
    print('PASS',result['cases'],'bounded native armor/stat cases',args.output_dir)

if __name__=='__main__':main()
