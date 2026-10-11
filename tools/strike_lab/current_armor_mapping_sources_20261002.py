"""Read-only current armor appearance source audit; new artifacts only.

No item/icon/name arithmetic is admitted as a native appearance authority.
Executed HeroDoll lookups use original instructions matched to current c5d8.
"""
import argparse,csv,hashlib,io,json,re,struct
from collections import Counter
from pathlib import Path
import capstone,pefile
from unicorn import UC_HOOK_CODE
from .current_armor_20261002 import qualify_source,CAPTURE,CURRENT
from .current_appearance_resources import AppearanceResources,BASE
from .omega_assets import decode_csvz
from .recover_companion_growth import fields

ROOT=Path(__file__).resolve().parents[2]
PIN='c5d8f79baa36879851703ac05d2b5caddf44a907677f7de114f568eeaf14f575'
def sha(value):return hashlib.sha256(value).hexdigest()
def require(ok,reason):
    if not ok:raise RuntimeError(reason)
def text(value):return value.decode('cp950')

def static_native(pe,mapped):
    dis=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);dis.skipdata=True
    code=[]
    for section in pe.sections:
        # The unpacked original .text retains dump flags C0000040. Relying
        # only on IMAGE_SCN_MEM_EXECUTE would silently omit native code.
        if section.Name.rstrip(b'\0')==b'.text' or section.Characteristics&0x20000000:
            code.extend(dis.disasm(mapped[section.VirtualAddress:section.VirtualAddress+section.Misc_VirtualSize],BASE+section.VirtualAddress))
    calls={hex(target):[] for target in (0x459a60,0x452460,0x451f20,0x452420)}
    strings={}
    for name in (b'HeroDoll.csv',b'HeroDoll_Fight.csv',b'ChangeDollCard',b'ChangeDollEffect',b'Equ01001',b'Teq01001'):
        offsets=[m.start() for m in re.finditer(re.escape(name),mapped)]
        addresses={BASE+n for n in offsets};refs=[]
        for i,ins in enumerate(code):
            tokens=set(int(n,16) for n in re.findall(r'0x[0-9a-f]+',ins.op_str))
            if addresses&tokens:
                refs.append({'va':hex(ins.address),'instruction':ins.mnemonic+' '+ins.op_str,
                    'next_instructions':[{'va':hex(x.address),'bytes':x.bytes.hex(),'instruction':x.mnemonic+' '+x.op_str} for x in code[i:i+16]]})
        strings[name.decode()]={'string_vas':[hex(n) for n in sorted(addresses)],'static_instruction_refs':refs}
    for i,ins in enumerate(code):
        if ins.mnemonic=='call' and ins.op_str in calls:
            calls[ins.op_str].append({'caller':hex(ins.address),'context':[{'va':hex(x.address),'bytes':x.bytes.hex(),'instruction':x.mnemonic+' '+x.op_str} for x in code[max(0,i-7):i+4]]})
    return {'scope':'Linear static .text plus executable-section disassembly; unpacked .text dump flags do not mark EXECUTE. Direct calls only, not complete indirect call graph or execution',
            'named_source_refs':strings,'direct_callers':calls}

def native_current_profile(pe,mapped):
    from .current_dialogue_mode4_native_20260926 import Native,UI,PACKET
    from .current_player_sex_contract_20260927 import PINS,profile_sex
    from .current_weapon_selector_authority_20260926 import chunks
    raw=(CURRENT/'data3/flow/FlowGui.ROMZ').read_bytes();require(sha(raw)==PINS['data3/flow/FlowGui.ROMZ'],'Current role-label ROM changed')
    acts=[value for kind,value in chunks(decode_csvz(raw)) if kind==b'ACT_DATA']
    names=['Flow_TipSword','Flow_TipWizard','Flow_TipRuse','Flow_TipDoctor']
    for i,name in enumerate(names):require(acts[56+i][24:48].split(b'\0')[0].decode()==name,'Current class control action identity changed')
    for i,name in ((95,'Flow_CarBoyH'),(96,'Flow_CarBoyL'),(97,'Flow_CarGirlH'),(98,'Flow_CarGirlL')):
        require(acts[i][24:48].split(b'\0')[0].decode()==name,'Current native sex ROM action identity changed')
    for offset in (0x183088,0x183608):
        require(struct.unpack_from('<2h',mapped,offset+4*8)==(95,96) and struct.unpack_from('<2h',mapped,offset+5*8)==(97,98),'Current sex control binding changed')
    cases=[];pcs=set()
    for entry,refresh,sender,builder,opcode in ((0x4097a0,0x409680,0x40c0b0,0x414cf0,0x17),(0x40c680,0x40c580,0x40c160,0x414cc0,0x1b)):
        for category in range(4):
            for sex in range(2):
                n=Native(pe,[b'']);profile=bytearray(40);profile[0]=65
                def check(vm,address,size,_):
                    if address in n.stops:return
                    require(bytes(vm.mem_read(address,size))==mapped[address-BASE:address-BASE+size],'Current profile native instruction changed');pcs.add(address)
                n.vm.hook_add(UC_HOOK_CODE,check);n.vm.mem_write(UI+0x15280,bytes(profile));n.setup(15+sex,1);n.run(entry,[refresh])
                profile[33]=sex;profile[29]=sex
                require(bytes(n.vm.mem_read(UI+0x15280,40))==bytes(profile),'Current sex event profile mismatch')
                n.setup(11+category,1);n.run(entry,[refresh]);profile[29]=2*category+sex
                require(bytes(n.vm.mem_read(UI+0x15280,40))==bytes(profile),'Current class event profile mismatch')
                n.setup(PACKET,PACKET+4);n.run(sender,[builder]);pointer=n.read(n.reg('ESP')+4,'I');wire=bytes(n.vm.mem_read(pointer,40))
                profile[29]+=1;profile[31]+=1;profile[38]=(profile[38]&0xf0)|sex
                require(wire==bytes(profile) and profile_sex(wire)==sex,'Current prequeue profile sender mismatch')
                cases.append({'opcode':hex(opcode),'sex_control':15+sex,'class_control':11+category,'profile_hex':wire.hex(),'wire29':wire[29],'profile33':wire[33],'profile38_low_nibble':wire[38]&15,'class_id':[1,2,4,3][category],'native_class_action':names[category]})
    return {'count':len(cases),'current_client_sha256':PIN,'flow_rom_sha256':sha(raw),'cases':cases,'executed_current_matched_vas':[hex(n) for n in sorted(pcs)],
        'scope':'Current c5d8 original sex/class UI events and full40 prequeue sender, stopped before drawing/packet building; no server equipment admission inferred'}

def source_tables():
    report={}
    for name,expected in (('HeroDoll.csvZ',918),('HeroDoll_Fight.csvZ',3578)):
        path=CURRENT/'Data2/Patch'/name;raw=path.read_bytes();capture=(CAPTURE/'Data2/Patch'/name).read_bytes()
        require(raw==capture,'Current/captured HeroDoll source mismatch '+name)
        decoded=decode_csvz(raw,limit=2*1024*1024);rows=list(csv.reader(io.StringIO(decoded.decode('latin1'))))
        start,count=int(rows[0][2]),int(rows[0][4]);selected_lines=[(i+1,row) for i,row in enumerate(rows) if i>=start-1 and row]
        selected=[row for _,row in selected_lines];blank_lines=[i+1 for i,row in enumerate(rows) if i>=start-1 and not row]
        require(start==26 and count==expected and len(selected)==count,'HeroDoll source denominator changed')
        require(all(len(row) in (6,7) for row in selected),'HeroDoll unexpected column width')
        keys=[row[0]+row[1] for row in selected]
        require(len(set(keys))==count,'Duplicate HeroDoll source key')
        report[name]={'path':str(path),'sha256':sha(raw),'decoded_sha256':sha(decoded),'source_header':[r.encode('latin1').decode('cp950') for r in decoded.decode('latin1').splitlines()[:25]],
          'first_data_line':start,'count':count,'blank_data_lines':blank_lines,'columns':['role namespace','action/component/category/ordinal key suffix','file identifier','resource path','palette or attack action','derived hairstyle','optional description'],
          'key_role_namespaces':dict(Counter(row[0] for row in selected)),
          'keys_and_source_records':[{'line':selected_lines[i][0],'key':keys[i],'fields':[v.encode('latin1').decode('cp950') for v in row]} for i,row in enumerate(selected)],
          'no_equ_teq_item_id_column':True,
          'authority':'resource-key -> filename/palette/hairstyle table; fields are not EQU/TEQ item IDs'}
    return report

def executed_world_lookup(mapped):
    oracle=AppearanceResources();pcs=set()
    # Loader executes in the inherited constructor; prove its entire retained
    # code slice unchanged before using those native-produced rows.
    for lo,hi in ((0x51ae0,0x51cd2),(0x5201c,0x521a2)):
        require(bytes(oracle.vm.mem_read(BASE+lo,hi-lo))==mapped[lo:hi],'Current native HeroDoll loader slice differs')
    def check(vm,address,size,_):
        require(BASE<=address<BASE+len(mapped),'Lookup escaped native image')
        require(bytes(vm.mem_read(address,size))==mapped[address-BASE:address-BASE+size],f'Current lookup instruction mismatch {address:x}')
        pcs.add(address)
    oracle.vm.hook_add(UC_HOOK_CODE,check)
    rows=[]
    for index,row in enumerate(oracle.rows):
        role,suffix=row[:2]
        require(re.fullmatch(r'r[123]',role) and re.fullmatch(r'[bfhw][0-9][0-9]{2}',suffix),'Unexpected world key format')
        args=(int(role[1])-1,'bfhw'.index(suffix[0]),int(suffix[1]),int(suffix[2:]),0)
        pointer=oracle.lookup(*args)
        # Native52260 transforms categories. A filename's apparent category is
        # not necessarily a directly addressable byte tuple (e.g. H5/action0).
        native=None if not pointer else oracle.record(pointer)
        if pointer==oracle.by_key[role+suffix]:
            require(native[32:42].split(b'\0')[0].decode()==role+suffix,'Native record key differs')
            require(native[:30].split(b'\0')[0].decode()==row[3].lower(),'Native filename not exact ASCII-lowercased source path')
        rows.append({'line':index+26,'source_key':role+suffix,'lookup_bytes':list(args),'direct_source_match':pointer==oracle.by_key[role+suffix],
            'native_key':None if native is None else native[32:42].split(b'\0')[0].decode(),
            'native_filename':None if native is None else native[:30].split(b'\0')[0].decode(),'record42':None if native is None else native[42]})
    return {'count':len(rows),'original_lookup_va':'0x452460','key_transformation_va':'0x452260','loader_slice':['0x45201c','0x4521a2'],
            'rows':rows,'executed_current_matched_vas':[hex(n) for n in sorted(pcs)],
            'direct_source_match_count':sum(r['direct_source_match'] for r in rows),
            'scope':'918 source-derived candidate tuples, action0; native category transform may select different rows/missing keys. No resource handles/rendering, no EQU/TEQ key input, Fight not executed'}

def armor_fields(sections):
    records=[];restrictions=Counter();tags=[]
    for family,section in sections.items():
        for row in section['records']:
            f=fields(row);require(len(f)==32,'Armor source32 fields changed')
            restriction=text(f[7]);restrictions[restriction]+=1;tags.append(f[2])
            records.append({'family':family,'item_id':int(f[0]),'source_line':row['source_line'],
                'physical_subtype_column1':text(f[1]),'opaque_tag_column2':text(f[2]),'inventory_icon_column3':int(f[3]),
                'source7_restriction_text':restriction,'source7_raw_hex':f[7].hex(),
                'source7_definition_offset':'0x2e','source26_27_28_29':[text(n) for n in f[26:30]]})
    explicit=[]
    for row in records:
        value=row['source7_restriction_text'];sex=[];classes=[]
        for code,label in ((0,'男性'),(1,'女性')):
            if label in value:sex.append({'source_token':label,'native_profile33':code})
        for code,label in ((1,'劍士'),(2,'仙道'),(3,'藥師'),(4,'謀士')):
            if label in value:classes.append({'source_token':label,'catalog_class_id':code})
        if sex or classes:explicit.append(dict(row,recognized_sex=sex,recognized_classes=classes,
            scope='literal source token alignment only; not recovered parser/admission predicate'))
    return {'count':len(records),'records':records,'source7_distribution':[{'text':k,'count':v} for k,v in sorted(restrictions.items())],
            'recognized_literal_restrictions':explicit,
            'profile_alignment':{'source_evidence':['artifacts/research/current-player-sex-contract-20260927/native.json','artifacts/research/character-growth-native-20260927/binding.json'],
              'male':0,'female':1,'native_profile_sex_offset':33,'wire29_domain':[1,8],'wire29_parity':'(wire29-1)&1 == profile33','profile38_low_nibble':'must equal profile33',
              'wire29_class_pairs':[{'wire29':[1,2],'class_id':1,'native_action':'Flow_TipSword'},{'wire29':[3,4],'class_id':2,'native_action':'Flow_TipWizard'},{'wire29':[5,6],'class_id':4,'native_action':'Flow_TipRuse'},{'wire29':[7,8],'class_id':3,'native_action':'Flow_TipDoctor'}],
              'authority':'Previously executed create-event/sender fields, not original-server equipment acceptance or HeroDoll appearance binary inference'}},tags

def extra_mapping_scan(tags):
    results=[];tagset=set(tags)
    for path in sorted((CURRENT/'Data2/Patch').rglob('*.csvZ')):
        if path.name.lower().endswith('-gb.csvz'):continue
        raw=path.read_bytes()
        try:decoded=decode_csvz(raw,limit=32*1024*1024)
        except Exception as error:
            results.append({'path':str(path),'sha256':sha(raw),'decoded':False,'error':type(error).__name__});continue
        hits=[];taghits=[]
        for number,line in enumerate(decoded.splitlines(),1):
            # Exact ASCII resource key namespace and exact source opaque tag,
            # never numeric substring or Chinese name equality as a mapping.
            keys=re.findall(rb'(?<![A-Za-z0-9])r[123](?:[15][1-6])?[bh][0-9]{3}(?![A-Za-z0-9])',line,re.I)
            fields_in_line=set(line.replace(b'"',b'').split(b','))
            tokens=line.replace(b'"',b'').split(b',')
            if len(tokens)>1 and re.fullmatch(rb'r[123]',tokens[0]) and re.fullmatch(rb'(?:[15][1-6])?[bh][0-9]{3}',tokens[1]):keys.append(tokens[0]+tokens[1])
            matches=fields_in_line&tagset
            if keys and len(hits)<30:hits.append({'line':number,'keys':[k.decode() for k in keys],'raw_hex':line.hex()})
            if matches and len(taghits)<30:taghits.append({'line':number,'exact_tags':[k.decode() for k in sorted(matches)],'raw_hex':line.hex()})
        results.append({'path':str(path),'sha256':sha(raw),'decoded':True,'decoded_sha256':sha(decoded),'length':len(decoded),
                        'head_body_namespace_hits_first30':hits,'exact_equ_teq_tag_hits_first30':taghits,
                        'focused_headers_first30':decoded.decode('cp950').splitlines()[:30] if path.name.lower() in ('changedollcard.csvz','changedolleffect.csvz','drvdoll.csvz') else []})
    return {'scope':'Current non-gb CSVZ under Data2/Patch, bounded32MiB/file, exact resource-key/opaque-tag tokens; negative scan is not proof no encrypted/binary/server mapping exists',
            'files':results}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output-dir',type=Path,default=ROOT/'artifacts/research/current-armor-mapping-sources-20261002-run02');args=parser.parse_args()
    require(not args.output_dir.exists(),'New output directory required')
    raw=(CURRENT/'God2.exe').read_bytes();require(sha(raw)==PIN,'Current c5d8 client changed');pe=pefile.PE(data=raw);mapped=pe.get_memory_mapped_image()
    _,sections,_,source=qualify_source();armor,tags=armor_fields(sections)
    tables=source_tables();native=static_native(pe,mapped);lookup=executed_world_lookup(mapped);extra=extra_mapping_scan(tags);profile=native_current_profile(pe,mapped)
    result={'status':'PASS_BOUNDED_RESEARCH','client_sha256':sha(raw),'source':source,'resource_tables':tables,'armor_source_fields':armor,
        'native_static':native,'native_world_lookup':lookup,'extra_source_scan':extra,'current_native_profile_alignment':profile,
        'appearance_mapping_accepted':False,'reason':'No demonstrated EQU/TEQ itemID -> HeroDoll B/H category+ordinal producer. Source tags/icons/names and literal restrictions are not substituted for that authority.',
        'mutations':'Only newly created research directory; no runtime/client/DB/process/UI/network actions'}
    args.output_dir.mkdir(parents=True);(args.output_dir/'native.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print('PASS bounded current source audit:',len(tables),'resource tables;',lookup['count'],'executed world lookups;',armor['count'],'armor rows;',len(extra['files']),'extra source files',args.output_dir)
if __name__=='__main__':main()
