"""New current armor appearance gap trace; offline, no UI/process/network.

Full461270 return uses a declared exhausted512 ROM pool and source cacheFFFF,
so original code returns missing handles without any fabricated graphics.
Source-backed lookup keys are observed. This does not generate equipment looks.
"""
import argparse,hashlib,json,struct
from dataclasses import asdict
from pathlib import Path
import pefile
import unicorn as uc
from unicorn import x86_const as x
from .current_protocol_coverage import qualified_image
from .current_appearance_resources import AppearanceResources,BASE,BANK,TABLE,RECORDS,STACK,SP,STOP,INPUT
from .current_armor_20261002 import qualify_source,CAPTURE,ArmorMetadata
from . import current_item_metadata as metadata
from . import recover_companion_growth as growth
from .current_equipment_projection_20260926 import Oracle as InventoryMethods
from .current_item_transition import UI as ITEM_UI,SLOTS,WORLD as ITEM_WORLD
ROOT=Path(__file__).resolve().parents[2]
LIVE=ROOT.parent/'God2/God2.exe'
PIN='c5d8f79baa36879851703ac05d2b5caddf44a907677f7de114f568eeaf14f575'
MANAGER=0x5000000
BLOCK=INPUT+0x4000
OUTPUT=INPUT+0x5000
ROLE=0x7000000

def require(ok,reason):
    if not ok:raise RuntimeError(reason)
def sha(value):return hashlib.sha256(value).hexdigest()

class Appearance(AppearanceResources):
    def __init__(self,mapped):
        super().__init__();self.mapped=mapped;self.visited=set();self.face_args=[];self.primary_args=[]
        self.vm.mem_map(MANAGER,0x170000)
        self.vm.mem_write(MANAGER+0x682e0,bytes(self.vm.mem_read(BANK,0x60000)))
        self.put32(MANAGER+0x16ce18,0)
        self.vm.mem_write(MANAGER+0x121fc,struct.pack('<H',512))
        self.vm.hook_add(uc.UC_HOOK_CODE,self.trace)
        self.input_reads=[];self.vm.hook_add(uc.UC_HOOK_MEM_READ,self.readblock)
    def trace(self,v,a,n,_):
        # CString formatting/destruction are bounded external CRT adapters.
        require(BASE<=a<BASE+len(self.mapped),'Non-native address')
        require(bytes(v.mem_read(a,n))==self.mapped[a-BASE:a-BASE+n],f'Current instruction mismatch{a:x}')
        self.visited.add(a)
        if a in (0x463c90,0x463de0):
            sp=v.reg_read(x.UC_X86_REG_ESP)
            args=struct.unpack('<'+'I'*(6 if a==0x463c90 else 7),v.mem_read(sp+4,24 if a==0x463c90 else 28))
            (self.face_args if a==0x463c90 else self.primary_args).append(list(args))
        require(a not in (0x429820,0x45a0a0,0x459a60),'Unexpected ROM or item lookup in component resolver')
    def readblock(self,v,access,a,n,value,_):
        if a<BLOCK+64 and a+n>BLOCK:self.input_reads.append([a-BLOCK,n])
    def world(self,block):
        self.events.clear();self.face_args.clear();self.primary_args.clear();self.input_reads.clear()
        self.vm.mem_write(BLOCK,block+b'\xa5'*56);self.vm.mem_write(OUTPUT,b'\x5a'*20)
        before=bytes(self.vm.mem_read(RECORDS,len(self.rows)*44))
        self.call(0x61270,0,0,BLOCK,OUTPUT,this=MANAGER)
        require(bytes(self.vm.mem_read(OUTPUT,20))==b'\xff'*12+b'\x5a'*8,'Exhausted pool resolver output/canary')
        require(bytes(self.vm.mem_read(BLOCK,64))==block+b'\xa5'*56,'Component input mutated')
        require(bytes(self.vm.mem_read(RECORDS,len(self.rows)*44))==before,'Native source cache mutated')
        require(self.u32(MANAGER+0x121fc)&65535==512,'Resource pool cursor changed')
        require(len(self.primary_args)==4,'Resolver did not visit four components')
        require(all(0<=a and a+n<=8 for a,n in self.input_reads),'Resolver read outside8byte appearance')
        selected=[]
        for args in self.primary_args:
            binary,component,category,ordinal,action=(a&255 for a in args[2:])
            ptr=self.lookup(binary,component,category,ordinal,action)
            selected.append(None if not ptr else {'key':self.record(ptr)[32:42].split(b'\0')[0].decode(),
                'filename':self.record(ptr)[:30].split(b'\0')[0].decode(),
                'description':self.rows[(ptr-RECORDS)//44][6].encode('latin1').decode('cp950') if len(self.rows[(ptr-RECORDS)//44])==7 else ''})
        return {'component_hex':block.hex(),'primary_arguments':self.primary_args.copy(),
                'derived_face_arguments_raw':self.face_args.copy(),
                'derived_face_arguments_low8':[[a&255 for a in args] for args in self.face_args],
                'selected_records':selected,
                'full_native_return':True,'handles':'FFFF (original exhausted-pool path)','input_reads':self.input_reads.copy()}

class Items(InventoryMethods):
    def install_icons(self):pass
    def __init__(self,image,mapped,definitions):
        self.mapped=mapped;self.current_pcs=set();super().__init__(image,definitions)
    def observe(self,v,a,n,context):
        super().observe(v,a,n,context)
        if BASE<=a<BASE+0x170000:
            require(bytes(v.mem_read(a,n))==self.mapped[a-BASE:a-BASE+n],f'Current inventory instruction mismatch{a:x}')
            self.current_pcs.add(a)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output-dir',type=Path,default=ROOT/'artifacts/research/current-armor-appearance-20261002');args=parser.parse_args()
    raw=LIVE.read_bytes();require(sha(raw)==PIN,'Current EXE identity changed');mapped=pefile.PE(data=raw).get_memory_mapped_image();original=qualified_image()
    decoded,sections,declarations,source=qualify_source()
    groups=json.loads((ROOT/'artifacts/research/native-armor-20261002/records.json').read_text(encoding='utf-8'))
    rows={r[1]:dict(record=bytes.fromhex(r[8]),raw=bytes.fromhex(r[6])) for r in groups[1]}
    n=Appearance(mapped);cases=[]
    for binary in (0,1):
        # Actual588F90 order bfhw: body0 and head2, not numerical equip slots.
        for component,categories in ((0,(0,1,2)),(2,(0,1,2,3,4))):
            for category in categories:
                for ordinal in (0,1,9,31):
                    for variant in (0,6):
                        block=bytearray([binary,0,binary,0,binary,0,0x80|binary,0])
                        block[component*2]=binary|(category<<4)
                        block[component*2+1]=ordinal|(variant<<5)
                        result=n.world(bytes(block));result.update({'changed_track':component,'category':category,'ordinal':ordinal,'variant':variant})
                        cases.append(result)
    # Differential source parser only: no guessed item-id/component relation.
    old_client=metadata.CLIENT;metadata.CLIENT=CAPTURE
    try:p=ArmorMetadata()
    finally:metadata.CLIENT=old_client
    parser_pcs=set()
    def match(v,a,size,_):
        if not p.active_code or a==p.stop_address:return
        require(bytes(v.mem_read(a,size))==mapped[a-BASE:a-BASE+size],f'Current parser instruction mismatch{a:x}');parser_pcs.add(a)
    p.vm.hook_add(uc.UC_HOOK_CODE,match)
    differentials=[]
    for family in ('EQU','TEQ'):
        original_row=p.sections[family]['records'][0];baseline=p.item_row(family,0)['record']
        for col,value in ((1,b'7'),(2,b'New_Visual_Tag'),(3,b'12001'),(7,b'MALE CLASS TEST'),(28,b'999')):
            tokens=growth.fields(original_row);tokens[col]=value
            p.sections[family]['records'][0]=growth.record(b','.join(tokens)+b'\n',original_row['source_line'],0)
            try:nextrow=p.item_row(family,0)
            finally:p.sections[family]['records'][0]=original_row
            expected=bytearray(baseline)
            if col==3:struct.pack_into('<H',expected,0x114,int(value))
            elif col==7:expected[0x2e:0x54]=bytes(0x26);expected[0x2e:0x2e+len(value)]=value
            elif col==28:struct.pack_into('<H',expected,0x11e,int(value))
            require(nextrow['record']==expected,f'Unexpected retained source change column{col}')
            differentials.append({'family':family,'column':col,'test_value':value.decode(),'changed_offsets':[hex(i) for i,(a,b) in enumerate(zip(baseline,expected)) if a!=b],
                'native_read':col in nextrow['columns'],'full396_expected':True})
    picked={key:rows[key] for key in (1001,1201,1501,1601,20001,20201,20501,20601)}
    icon_cases=[]
    for key,value in picked.items():
        icon=struct.unpack_from('<H',value['record'],0x114)[0];index=p.icon_map(icon)
        fields=growth.fields(p.map_rows[index]);require(int(fields[1])<=icon<=int(fields[2]),'Icon native range mismatch')
        path=fields[3].decode('ascii');require(path.lower().startswith('data2\\itmimg\\equ'),'Armor icon did not select inventory EQU ROM')
        icon_cases.append({'item_id':key,'definition114_icon':icon,'native59FC0_rommap_index':index,
            'rommap_bounds':[int(fields[1]),int(fields[2])],'inventory_rom_path':path})
    require(mapped[0x81700:0x817d0]==original[0x81700:0x817d0],'Inventory icon binder changed')
    item=Items(original,mapped,picked);v=item.vm;v.mem_map(ROLE,0x5000)
    worldpage=(ITEM_WORLD+0x1539adc0)&~4095;v.mem_map(worldpage,4096)
    v.mem_write(ITEM_UI+0x86888,struct.pack('<I',ROLE));touch=[]
    def watch(vm,access,a,size,value,_):
        if a<ROLE+0x5000 and a+size>ROLE or a<worldpage+4096 and a+size>worldpage:touch.append([a,size])
    v.hook_add(uc.UC_HOOK_MEM_READ|uc.UC_HOOK_MEM_WRITE,watch)
    transport=[]
    for key in picked:
        family=2 if key<20000 else 26
        for slot in (30,31,32,33):
            data=struct.pack('<HH',key,family)+bytes(16)
            v.mem_write(ROLE,b'\xa5'*0x5000);v.mem_write(worldpage,b'\x5a'*4096);touch.clear()
            item.put(slot,data);wire=item.ui_request(slot)
            packet=b'\x3b'+struct.pack('<BHB',1,slot,0)+data
            from .current_item_transition import PACKET
            v.mem_write(PACKET,packet[1:]);item.call(0x98dd0,PACKET)
            v.mem_write(PACKET,struct.pack('<HBB',0,slot,0));item.call(0x991e0,PACKET)
            require(not touch,'Equipment request/inventory consumer read or wrote actor/world appearance')
            require(bytes(v.mem_read(ROLE,0x5000))==b'\xa5'*0x5000 and bytes(v.mem_read(worldpage,4096))==b'\x5a'*4096,'Appearance canary changed')
            transport.append({'item_id':key,'slot':slot,'request_hex':wire,'full3B41_return':True,'actor_or_saved_appearance_reads_writes':0})
    result={'status':'PASS','current_client_sha256':sha(raw),'source':source,'scope':'native full resolver with exhausted pool, actual source lookup and parser/transport; not ROM pixels, role admission or item-to-appearance generation',
        'native_component_letters':bytes(n.vm.mem_read(0x588f90,4)).decode(),'resolver_cases':cases,'source_field_differentials':differentials,'inventory_transport_cases':transport,'icon_map_cases':icon_cases,
        'executed_addresses':{'resolver':[hex(a) for a in sorted(n.visited)],'parser':[hex(a) for a in sorted(parser_pcs)],'inventory':[hex(a) for a in sorted(item.current_pcs)]},
        'findings':{'track_order':'Original588F90 bfhw:0 body,1 face/hair,2 head,3 weapon. Equip slot30/31 is not DA track30/31.',
            'F':'Face/hair from original HeroDoll descriptions, not footwear; source has no independent glove/shoe component in these four tracks',
            'face_derived':'461366..461399 or4612DF..461312 calls463C90→452420 with head(block4/5) lookup + face base ordinal(block3&31); record42<=1 gives direct face ordinal, >1 adds base ordinal. Face is not derived from armor body.',
            'input':'461270 reads only caller eight component bytes; not item key/20byte instance/396byte metadata',
            'source':'source3 retained at definition114 is inventory icon selector; source1 physical part/source2 tag ignored by parser; source7 is text, source28 encoded level retained; no native H/B composition generated by these parser fields',
            'icon_binder':'Matched481700 reads definition116 RomMaps index, adds41 graphics bank, calls41AE70 with definition114 icon action, stores118; these are ItmImg EQU icons, not RoleDoll H/B tracks. Binder address chain is static matched evidence, not a rendered binder acceptance.',
            'transport':'49A330->49B5E0->496550 emits28;3B/41 apply inventory. Disabled sprite/cache-hit branch does not update actor or saved appearance; not whole UI proof',
            'predicates':'Ordinary guard49B5E0 does not test class/level/sex. Source7 restriction and11E level display are not server admission rules',
            'authority_gap':'No demonstrated itemkey→H/B component producer; head/body IDs cannot be turned into packets by matching names/icons or numeric IDs. Final formulas and live equip remain unproved'}}
    args.output_dir.mkdir(parents=True,exist_ok=True);(args.output_dir/'native.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf-8')
    print('PASS',len(cases),'full resolver cases,',len(differentials),'parser differences,',len(transport),'equipment transport cases',args.output_dir)
if __name__=='__main__':main()
