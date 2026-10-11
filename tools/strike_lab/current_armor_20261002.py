"""Current TW armor definitions, original x86 loader; no server authority claim.

Reads captured native source and proves current EQU/TEQ rows remain identical.
Writes only new research evidence. No process, network, UI, client or DB writes.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import struct

import pefile
from . import current_item_metadata as metadata
from . import recover_companion_growth as growth
from .current_protocol_coverage import qualified_image, IMAGE_SHA256
from .omega_assets import decode_csvz

ROOT = Path(__file__).resolve().parents[2]
SOURCE = 'Data2/Patch/Comm/gamedata.csvZ'
CAPTURE = ROOT / 'artifacts/capture_work/host-20260918-1430/client'
CURRENT = ROOT.parent / 'God2'
SOURCE_SHA = '70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731'
DECODED_SHA = '75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815'
COUNTS = {'EQU': 692, 'TEQ': 662}
AUTHORITY = 'NATIVE_PARSED_DEFINITION_ONLY'
CATEGORY_SLOT = {0:31, 1:31, 2:30, 3:30, 4:30, 5:32, 6:33, 7:30}
EXPECTED_LABELS = ['鎧甲', '袍', '頭巾', '頭冠', '頭盔', '手套', '鞋', '頭飾']
DESC_SLOT = {'鎧':31, '袍':31, '頭盔':30, '頭帶':30, '頭巾':30,
             '頭冠':30, '頭飾':30, '手套':32, '鞋子':33,
             '傳奇手套':32, '傳奇鞋子':33, '頭部飾品':30, '手部飾品':32}

def sha(data):
    return hashlib.sha256(data).hexdigest()

def require(ok, why):
    if not ok:
        raise AssertionError(why)

def fingerprint(groups):
    d = hashlib.sha256()
    for group in groups:
        for row in group:
            for value in row:
                data = value if isinstance(value,bytes) else str(value).encode('ascii')
                d.update(struct.pack('<I',len(data))); d.update(data)
    return d.hexdigest()

def qualify_source():
    original = (CAPTURE / SOURCE).read_bytes()
    current = (CURRENT / SOURCE).read_bytes()
    require(sha(original)==SOURCE_SHA, 'Captured original source changed')
    decoded = decode_csvz(original)
    require(sha(decoded)==DECODED_SHA, 'Captured decoded source changed')
    current_decoded = decode_csvz(current)
    sections = growth.parse_sections(decoded, tuple(COUNTS))
    current_sections = growth.parse_sections(current_decoded, tuple(COUNTS))
    originals = decoded.split(b'\n'); currents = current_decoded.split(b'\n')
    declarations = {}
    for family,count in COUNTS.items():
        a,b = sections[family]['records'],current_sections[family]['records']
        require(len(a)==len(b)==count, 'Armor row count changed')
        require([r['raw_record_hex'] for r in a]==[r['raw_record_hex'] for r in b],
                'Current armor raw rows differ from captured original')
        aa = next((i,line) for i,line in enumerate(originals)
                  if len(line.split(b','))>3 and line.split(b',')[2]==family.encode())
        bb = next((i,line) for i,line in enumerate(currents)
                  if len(line.split(b','))>3 and line.split(b',')[2]==family.encode())
        require(aa[1]==bb[1], 'Current ItemType declaration changed')
        labels = [t.decode('cp950') for t in aa[1].rstrip(b'\r').split(b',')[4:]]
        require(labels[:8]==EXPECTED_LABELS,'Ordinary armor declared labels changed')
        declarations[family] = dict(source_line=aa[0]+1,current_source_line=bb[0]+1,
            raw_hex=aa[1].hex(),labels=labels,current_exact_equality=True)
    return decoded,sections,declarations,dict(captured_path=str(CAPTURE/SOURCE),
        captured_sha256=SOURCE_SHA,decoded_sha256=DECODED_SHA,
        current_path=str(CURRENT/SOURCE),current_sha256=sha(current),
        current_decoded_sha256=sha(current_decoded),unchanged_raw_rows=1354,
        declaration_exact_equality=True)

class ArmorMetadata(metadata.NativeItemMetadata):
    # Added original guard only; metadata native code remains inherited verbatim.
    CODE = metadata.NativeItemMetadata.CODE + ((0x9b5e0,0x9b662),)

def field_differentials(native):
    vectors=[]
    for family in COUNTS:
        original=native.sections[family]['records'][0]
        baseline=native.item_row(family,0)['record']
        for column,value,offset in ((1,b'99',None),(2,b'Probe_Tag',None),
                (30,b'17',None),(31,b'18',None),(26,b'19',0x11c),
                (27,b'20',0x11d),(28,b'777',0x11e),(29,b'9',0x120)):
            tokens=growth.fields(original);tokens[column]=value
            native.sections[family]['records'][0]=growth.record(b','.join(tokens)+b'\n',
                                                               original['source_line'],0)
            try:observed=native.item_row(family,0)
            finally:native.sections[family]['records'][0]=original
            expected=bytearray(baseline)
            if offset is not None:
                width=2 if column==28 else 1
                expected[offset:offset+width]=int(value).to_bytes(width,'little')
            require(observed['record']==bytes(expected),'Armor source field differential changed unexpected bytes')
            require((column in observed['columns'])==(offset is not None),'Armor source access/retention mismatch')
            vectors.append(dict(family=family,synthetic_source_column=column,
                synthetic_value=value.decode(),changed_offsets=[hex(i) for i,(a,b)
                    in enumerate(zip(baseline,observed['record'])) if a!=b],
                complete_396_byte_expected_equality=True))
    return vectors

def request_vectors(image,mapped,rows):
    from .current_equipment_projection_20260926 import Oracle,UI,BASE
    import unicorn as uc
    # Inactive sprite UI is a precise fixture. Cached tooltip does not need
    # resource binders. Do not install weapon icons for armor or assert sprite
    # acceptance from a wrong resource bank.
    class Request(Oracle):
        def install_icons(self):
            pass
        def observe(self,v,address,size,context):
            if BASE<=address<BASE+0x170000:
                rva=address-BASE
                require(mapped[rva:rva+size]==image[rva:rva+size],f'Executed armor request code differs {address:x}')
            super().observe(v,address,size,context)
    pick={}
    for row in rows:
        family,key=row[0],row[1]
        if key in (1001,1201,1501,1601,20001,20201,20501,20601):
            pick[key]=dict(record=row[8])
    require(len(pick)==8,'Armor request source examples missing')
    n=Request(image,pick);role=0x66000000;n.vm.mem_map(role,0x5000)
    n.vm.mem_write(UI+0x86888,struct.pack('<I',role));reads=[]
    def watch(vm,access,address,size,value,context):
        if address<role+0x5000 and address+size>role or address<UI+0x8688c and address+size>UI+0x86888:
            reads.append((address,size))
    n.vm.hook_add(uc.UC_HOOK_MEM_READ,watch)
    vectors=[]
    for key in pick:
        family=2 if key<20000 else 26
        for poison in (0,0x55,0xff):
            n.vm.mem_write(role,bytes([poison])*0x5000)
            for slot in (0,30,31,32,33):
                data=struct.pack('<HH',key,family)+bytes(16)
                n.put(slot,data);reads.clear()
                wire=n.ui_request(slot)
                require(not reads,'Ordinary armor native request read role profile')
                require(bytes(n.vm.mem_read(role,0x5000))==bytes([poison])*0x5000,'Ordinary armor native request mutated role')
                vectors.append(dict(key=key,slot=slot,fixture_family_word=family,
                    role_poison=poison,request_hex=wire,role_reads=0))
    return dict(scope='Original complete cached-tooltip28 request to real return, disabled sprite UI, synthetic20byte instance, absent sound device, WinMM clock adapter; not role eligibility or live UI acceptance',
        cases=len(vectors),vectors=vectors,executed_instruction_rvas=sorted(n.pcs))

def prove_level_display(out):
    """Additional bounded display proof, never a server equip-level formula."""
    from .current_weapon_attributes_native_20260926 import Probe,PACKET,TABLE,UI
    import unicorn as uc
    _,_,_,source=qualify_source()
    original_image=qualified_image()
    pe=pefile.PE(data=(CURRENT/'God2.exe').read_bytes())
    mapped=pe.get_memory_mapped_image()
    oracle=json.loads((out/'oracle.json').read_text(encoding='utf-8'))
    serialized=json.loads((out/'records.json').read_text(encoding='utf-8'))
    for row in serialized[1]:
        row[6]=bytes.fromhex(row[6]);row[8]=bytes.fromhex(row[8])
    require(fingerprint(serialized)==oracle['catalog_fingerprint']==
            '29d1de3729c843571c3a7bc117beb12289bd7110932ec45fc5d846b627282efe',
            'Armor display input catalog drift')
    levels={struct.unpack_from('<H',row[8],0x11e)[0] for row in serialized[1]}
    require(mapped[0x1926d4:0x1926dc]==original_image[0x1926d4:0x1926dc] and
            struct.unpack_from('<4h',mapped,0x1926d4)==(0,1,3,5),'Armor display table changed')
    n=Probe(pe);pcs=set()
    def qualify(vm,address,size,context):
        if address==0x547af7:return
        rva=address-0x400000
        require(0<=rva<len(original_image) and mapped[rva:rva+size]==original_image[rva:rva+size],
                f'Armor display executed code mismatch {address:x}')
        pcs.add(rva)
    n.vm.hook_add(uc.UC_HOOK_CODE,qualify)
    vectors=[]
    for base in sorted(levels|{0,999,1000,1001,32767,32768,65535}):
        for grade,adjustment in enumerate((0,1,3,5)):
            n.write(PACKET+12,'I',grade<<30);n.write(TABLE+0x11e,'H',base)
            n.setup();n.write(n.reg('ESP')+0x11a8,'I',TABLE)
            n.setreg('EDX',PACKET);n.setreg('EBP',UI)
            n.run(0x4b6020,[0x547af7])
            sp=n.reg('ESP');fmt=n.read(sp+8,'I')
            value=(base-adjustment)&65535
            expected=max(1,value if value<32768 else value-65536)
            if base<1000:
                require(fmt==0x592adc and n.read(sp+20,'I')==expected,'Armor plain display level mismatch')
                numbers=[expected]
            else:
                require(fmt==0x592acc,'Armor rebirth format selection mismatch')
                numbers=[n.read(sp+20,'I'),n.read(sp+28,'I')]
                require(numbers==[expected//1000,expected%1000],'Armor rebirth display numbers mismatch')
            vectors.append(dict(source_encoded_level=base,in_source=base in levels,
                synthetic_instance_grade=grade,display_numbers=numbers,
                display_encoded=expected,format_pointer=hex(fmt)))
    # Explicit language evidence remains text evidence. It cannot silently turn
    # into a claim that original server admission predicates were recovered.
    texts=[]
    for row in serialized[1]:
        fields=row[6].split(b',');text=fields[7].decode('cp950')
        require(row[8][0x2e:].split(b'\0',1)[0]==fields[7],'Native restriction string mismatch')
        if text:
            texts.append(dict(item_id=row[1],source_line=row[3],source_column=7,
                parsed_offset='0x2e',text=text,
                explicit_class_names=[s for s in ('劍客','仙道','藥師','謀士') if s in text],
                explicit_gender_names=[s for s in ('男性','女性') if s in text],
                authority='SOURCE_DESCRIPTION_ONLY_NOT_NATIVE_SERVER_PREDICATE'))
    result=dict(scope='Original4B6020 formatting operands before547AF7; synthetic instance grade bits; not an equipment admission or server formula',
        source=source,catalog_fingerprint=oracle['catalog_fingerprint'],
        cases=len(vectors),source_encoded_level_count=len(levels),
        instance_grade_offset=12,instance_grade_bit_range=[30,31],
        adjustment_table_va='0x5926d4',adjustments=[0,1,3,5],
        signed_word_floor=1,rebirth_format_selects_original_source_word_ge_1000=True,
        vectors=vectors,executed_instruction_rvas=sorted(pcs),
        source7_nonempty_count=len(texts),source7_restrictions=texts)
    (out/'level-and-restrictions.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf-8')
    print(json.dumps(dict(display_cases=len(vectors),source_levels=len(levels),
        source7_nonempty=len(texts),output=str(out/'level-and-restrictions.json'))))
    return result

def prove(out):
    decoded,sections,declarations,source_proof = qualify_source()
    image = qualified_image()
    executable = (CURRENT/'God2.exe').read_bytes()
    mapped = pefile.PE(data=executable).get_memory_mapped_image()
    regions = list(ArmorMetadata.CODE)+[(0x9a330,0x9a5ce),(0x98030,0x9838e),
                                      (0x1905f0,0x190618),(0xb6020,0xb6380),
                                      (0x1897ec,0x18987c)]
    matched = []
    for low,high in regions:
        require(mapped[low:high]==image[low:high],f'Current native code/data changed {low:x}')
        matched.append(dict(start_rva=hex(low),end_rva_exclusive=hex(high),
                            sha256=sha(image[low:high])))
    native_tags=[]
    for ordinal in range(36):
        at=struct.unpack_from('<I',image,0x1897ec+ordinal*4)[0]-0x400000
        end=image.index(0,at)+1
        require(mapped[at:end]==image[at:end],'Current metadata family tag changed')
        native_tags.append(image[at:end-1].decode('cp950'))
    require(next(i for i,t in enumerate(native_tags) if t[:3]=='EQU')==2 and
            next(i for i,t in enumerate(native_tags) if t[:3]=='TEQ')==26,
            'Native armor family selector binding changed')
    # Redirect only this isolated loader process to a pinned original native
    # capture. The old tool and its source/hash pins are never edited.
    previous_client = metadata.CLIENT
    metadata.CLIENT = CAPTURE
    try:
        native = ArmorMetadata()
    finally:
        metadata.CLIENT = previous_client
    require(native.decoded==decoded,'Loader source drift')
    sources=[]; rows=[]; qualifications=[]; columns=set(); levels=Counter()
    flags=Counter(); description_guards=[]; icon_slots=defaultdict(set)
    native_guard_cases=0
    for family in sorted(COUNTS):
        original=sections[family]['records']; count=COUNTS[family]
        sources.append((family,SOURCE,SOURCE_SHA,DECODED_SHA,IMAGE_SHA256,
                        '0x59420','0x59a60',count,'CP950',AUTHORITY))
        for ordinal,source in enumerate(original):
            parsed=native.item_row(family,ordinal)
            data=parsed['record']; fields=growth.fields(source)
            raw=bytes.fromhex(source['raw_record_hex']).rstrip(b'\r\n')
            key=parsed['key']; category=int(fields[1]); icon=int(fields[3])
            require(len(data)==396 and len(fields)==32,'Armor definition width changed')
            require(parsed['source_line']==source['source_line'] and
                    decoded[source['decoded_offset']:source['decoded_offset']+len(raw)]==raw,
                    'Armor source provenance mismatch')
            raw.decode('cp950',errors='strict')
            require(struct.unpack_from('<H',data,0x114)[0]==icon,'Native icon field differs')
            require(struct.unpack_from('<H',data,0x11e)[0]==int(fields[28]),'Native encoded level differs')
            require(data[0x11c]==int(fields[26]) and data[0x11d]==int(fields[27]) and
                    data[0x120]==int(fields[29]),'Native restriction fields differ')
            columns.update(parsed['columns']); levels[int(fields[28])]+=1; flags[data[0x11a]]+=1
            rows.append((family,key,ordinal,source['source_line'],source['decoded_offset'],
                         sha(raw),raw,sha(data),data,AUTHORITY))
            description=fields[8].decode('cp950')
            slot=CATEGORY_SLOT.get(category)
            tokens=description.split('-')
            named_slots={DESC_SLOT[t] for t in tokens if t in DESC_SLOT}
            if description in DESC_SLOT:named_slots.add(DESC_SLOT[description])
            if slot is not None:
                require(not named_slots or named_slots=={slot},'Source ordinary category/description conflict')
                icon_slots[icon].add(slot)
            require(data[0x2e:].split(b'\0',1)[0]==fields[7], 'Native armor source7 restriction text storage differs')
            qualification=dict(family=family,item_id=key,source_record_index=ordinal,
                source_line=source['source_line'],decoded_offset=source['decoded_offset'],
                category=category,category_label=declarations[family]['labels'][category],
                name=fields[4].decode('cp950'),description=description,icon_id=icon,
                restriction_text=fields[7].decode('cp950'),native_definition_restriction_offset='0x2e',
                loader_family_selector=parsed['selector'],
                equip_flag=bool(data[0x11a]&4),flags_11a=data[0x11a],
                encoded_level=struct.unpack_from('<H',data,0x11e)[0],
                restriction_bytes_11c_11d_120=[data[0x11c],data[0x11d],data[0x120]],
                slot=slot,slot_evidence='ItemType explicit label' if slot else None,
                explicit_description_slots=sorted(named_slots))
            qualifications.append(qualification)
            for i in range(7,13):
                text=fields[i].decode('cp950')
                if any(t in text for t in ('男','女','劍客','劍士','仙道','藥師','謀士','職業','限定','限','轉')):
                    description_guards.append(dict(item_id=key,source_line=source['source_line'],
                        source_column=i,text=text,authority='SOURCE_DESCRIPTION_ONLY'))
            # Ordinary EQU/TEQ never enter deity 7000<id<8000 branch. Execute
            # the original guard to its true RET with poisoned unrelated role
            # bytes, never assert a server class/level/gender admission rule.
            for poison in (0,1,2,255):
                native.vm.mem_write(native.OWNER+0x866ba,bytes([poison]))
                accepted=native.call(0x9b5e0,key,this=native.OWNER)
                require(accepted&255==1,'Unexpected ordinary armor client guard rejection')
                native_guard_cases+=1
    require(len(rows)==1354 and len({r[1] for r in rows})==1354,'Armor ID collision')
    require(1 not in columns and 2 not in columns,'Native loader began reading source category/tag')
    require(all(len(v)==1 for v in icon_slots.values()),'Ordinary icon shared across physical slots')
    differential_vectors=field_differentials(native)
    requests=request_vectors(image,mapped,rows)
    # Special source groups are not mapped by numeric/category arithmetic.
    # Preserve explicit physical subtype text separately. Exact icon reuse is
    # corroboration, not a native admission predicate. Ambiguous rows excluded.
    for q in qualifications:
        if q['slot'] is not None:continue
        slots=set(q['explicit_description_slots'])
        icon_match=icon_slots.get(q['icon_id'],set())
        q['ordinary_same_icon_slots']=sorted(icon_match)
        if len(slots)==1 and (not icon_match or slots==icon_match):
            q['slot']=next(iter(slots));q['slot_evidence']='explicit original physical subtype description'
        else:
            q['unknown_reason']='Special category lacks an unambiguous original physical subtype; same icon alone is not admission authority'
    groups=(tuple(sources),tuple(sorted(rows,key=lambda r:(r[0],r[1]))))
    serialized=[[list(row) for row in group] for group in groups]
    for row in serialized[1]:
        row[6]=row[6].hex();row[8]=row[8].hex()
    out.mkdir(parents=True,exist_ok=True)
    (out/'records.json').write_text(json.dumps(serialized,separators=(',',':'))+'\n','utf-8')
    qualified=[q for q in qualifications if q['slot'] is not None and q['equip_flag']]
    unknown=[q for q in qualifications if q['slot'] is None or not q['equip_flag']]
    result=dict(schema='current-armor-20261002',scope='Native source/definition plus original client entry guard; emulator is not server authority, player instance or live UI acceptance',
        source=source_proof,current_client_sha256=sha(executable),native_image_sha256=IMAGE_SHA256,
        matched_regions=matched,catalog_fingerprint=fingerprint(groups),rows=1354,
        native_loader_cases=1354,native_guard_cases=native_guard_cases,
        field_differential_cases=len(differential_vectors),field_differentials=differential_vectors,
        full_native_requests=requests,
        original_loader_rva='0x59420',original_lookup_rva='0x59a60',
        parsed_definition_bytes=396,owned_instance_bytes=20,source_columns_read=sorted(columns),
        declarations=declarations,qualifications=qualifications,
        native_family_tags=native_tags,family_selectors={'EQU':2,'TEQ':26},
        original_slot_label_message_ids={str(s):struct.unpack_from('<H',image,0x1905f0+(s-30)*2)[0] for s in (30,31,32,33)},
        qualification_scope='Explicit source physical-slot label and native equip flag; not original server role admission',
        qualified_equip_ids_by_slot={str(s):[q['item_id'] for q in qualified if q['slot']==s] for s in (30,31,32,33)},
        qualified_count=len(qualified),unknown_count=len(unknown),unknown=unknown,
        encoded_level_counts=dict(sorted(levels.items())),flags_11a_counts=dict(sorted(flags.items())),
        original_guard=dict(entry='0x49B5E0',ordinary_return='AL=1',
            bounds='7000 < id < 8000 only; armor IDs outside this guard range',
            native_ui_path='49A330 flags4 -> definition11A bit4 ->49B5E0 ->496550 -> C2S28',
            class_level_gender_guard='Not read on qualified ordinary client path; original server eligibility not recovered'),
        restrictions=dict(fields='source26/27/28/29 -> definition11C/11D/11E(WORD)/120',
            zeros='All armor source26/27/29 zero; no class or sex inferred from these zeros',
            min_level='Encoded source28 retained exactly; >=1000 describes rebirth/level display. Instance+12 high two bits affect tooltip adjustments0/1/3/5, not recovered server admission',
            description_guards=description_guards),
        slot_scope='30 head,31 armor,32 gloves,33 shoes from original ProgramMsg table. Explicit ItemType/source physical labels only, no %8, no invented special-category slot',
        not_proven=['original server class/level/gender predicates','source description stats as exact instance combat values','grant/drop provenance','live UI equip/unequip and persistence'])
    (out/'oracle.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf-8')
    print(json.dumps(dict(rows=1354,fingerprint=result['catalog_fingerprint'],
        native_guard_cases=native_guard_cases,qualified=len(qualified),unknown=len(unknown),
        slot_counts={s:len(v) for s,v in result['qualified_equip_ids_by_slot'].items()},out=str(out))))
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output-dir',type=Path,default=ROOT/'artifacts/research/native-armor-20261002')
    p.add_argument('--level-display-only',action='store_true')
    a=p.parse_args()
    if a.level_display_only:prove_level_display(a.output_dir)
    else:prove(a.output_dir);prove_level_display(a.output_dir)

if __name__=='__main__':main()
