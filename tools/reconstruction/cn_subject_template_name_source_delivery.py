"""Pinned WORLD30 GOD name/pointer lineage and publisher handoff; static only."""
import csv
import difflib
import hashlib
import json
import re
import struct
from pathlib import Path
import capstone
import pefile
from .cn_wrapper_route_frontier import ROOT
from .cn_pe_import_directory import FileView
from .cn_preborn_selected_subject_source_delivery import local_cfg

NAME='cn-subject-template-name-source-01';ROUND='20261008-cn-subject-template-name-source'
PIN='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
SOURCES=['src/cn/assets/CnSubjectTemplateNames.h','src/cn/assets/CnSubjectTemplateNames.cpp',
 'src/cn/world/SharedSubjectRosterPublication.h','src/cn/world/SharedSubjectRosterPublication.cpp',
 'docs/research/cn-subject-template-name-source-20261008.md',
 'tools/reconstruction/cn_subject_template_name_source_delivery.py','tools/reconstruction/dual_client_route_catalog.py']
REMAINING=[
 'Actual source revision/Current and any relevant pointer replacements, common subject/recipient/roster/inactive row/fields/skills/rules/save/durable replay/committed issuer/Application remain unconfigured.',
 'Pinned GOD names and tab-label refresh are not monster attributes, skill ownership or row initialization; whole graph/native timing/variants remain open.',
 'Full TW/CN/PC/web/WSS/all gameplay/numeric64/stack99/whole-game denominator and later comprehensive tests/repair/recovery release remain open.']

def sha(raw):return hashlib.sha256(raw).hexdigest()

def main():
    b=ROOT/'artifacts/integration/packet-connections-20261006';o=b/NAME
    if not (o/'before-manifest.json').exists() or (o/'findings.json').exists():raise RuntimeError('Fresh before required')
    def save(rel,raw):
        p=o/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as f:f.write(raw)
    def dump(rel,v):save(rel,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    before=json.loads((o/'before-manifest.json').read_text(encoding='utf-8'))
    if len(before)!=183:raise RuntimeError('Expected183 before files')
    old={r['path']:(o/r['snapshot']).read_bytes() for r in before}
    books=['docs/PACKET_CONNECTION_GOAL_20261006.md','artifacts/integration/packet-connections-20261006/packet-route-ledger.json']
    reports={f'artifacts/integration/packet-connections-20261006/packet-progress-latest.{e}' for e in ['json','md']}
    protected=[]
    for row in before:
        if sha(old[row['path']])!=row['sha256']:raise RuntimeError('Before source differs')
        if row['path'] not in set(SOURCES+books)|reports:
            if (ROOT/row['path']).read_bytes()!=old[row['path']]:raise RuntimeError('Protected source differs: '+row['path'])
            protected.append(row)
    prior=(o/'retained-prior/cn-subject-roster-frame-packing-source-01/manifest.json').read_bytes()
    if sha(prior)!='bb154740e6d6360269b4d1c9ae9739963b2954a6d89ca9521730b2bdebc8ccda' or not json.loads(prior)['sealed']:
        raise RuntimeError('Prior seal differs')
    raw=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe').read_bytes()
    if sha(raw)!=PIN:raise RuntimeError('Pinned PE differs')
    view=FileView(pefile.PE(data=raw,fast_load=True),raw)
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True
    recovery=Path('C:/Users/risei/Desktop/God2-xjz/God2_opt_source_recovery_20260926_055734/decompiled')
    targets=struct.unpack('<9I',view.read(0x42d4f4-0x400000,36));mapping=view.read(0x42d518-0x400000,39)
    save('native/tables/0042D4F4.bin',view.read(0x42d4f4-0x400000,36));save('native/tables/0042D518.bin',mapping)
    scopes=[];decoded={}
    for va in [0x4283a0,0x428860,0x428c80,0x42cfb0,0x42d540,0x4d4b80]:
        paths=list(recovery.glob(f'part_*/{va:08x}_*.c'))
        if len(paths)!=1:raise RuntimeError('Primary source not unique')
        source=paths[0].read_bytes();size=int(re.search(rb'Size: (\d+) bytes',source)[1])
        code=view.read(va-0x400000,size)
        tables={0x42d244:('dword ptr [eax*4 + 0x42d4f4]',targets)} if va==0x42cfb0 else {}
        cfg,ins=local_cfg(md,code,va,tables)
        if cfg['frontier']:raise RuntimeError('Entry-rooted local CFG frontier differs')
        save('native/source/'+paths[0].name,source);save(f'native/{va:08X}.bin',code);dump(f'native/{va:08X}-cfg.json',cfg)
        save(f'native/{va:08X}-cfg.asm',('\n'.join(f'{a:08x} {x.bytes.hex()} {x.mnemonic} {x.op_str}' for a,x in sorted(ins.items()))+'\n').encode())
        scopes.append(dict(va=f'{va:08X}',bytes=size,sites=len(ins),frontier=cfg['frontier']));decoded.update(ins)
    dump('native/source-scopes.json',scopes)
    expected={
        0x4283a3:('mov','ax, word ptr [ebp + 8]'),0x4283a7:('mov','edx, 0x88b8'),
        0x4283af:('jae','0x4283bf'),0x4283b4:('mov','eax, dword ptr [ecx + eax*4 + 0xb304c]'),
        0x428970:('push','0x222e0'),0x428975:('lea','eax, [esi + 0xb304c]'),
        0x428de0:('push','0x18c'),0x428e19:('push','0'),
        0x428e47:('mov','dword ptr [esi + ecx*4 + 0xb304c], eax'),0x428e57:('call','0x42cfb0'),
        0x428e66:('add','ebx, 0x18c'),0x42cff9:('lea','eax, [esi + 8]'),
        0x42cffd:('push','4'),0x42cfff:('call','0x4231b0'),0x42d008:('mov','byte ptr [esi + 0x2d], 0'),
        0x42d5b6:('mov','dword ptr [esi + ecx*4 + 0xb304c], eax'),
        0x4d4b9b:('lea','ecx, [eax + 0xdb]'),0x4d4bc3:('add','ecx, 0x3ec'),
        0x4d4be0:('push','0x7ee88c'),0x4d4bf4:('push','0'),
        0x4d4c07:('movsx','ax, byte ptr [eax + 0xcf]'),0x4d4c13:('call','0x456ab0')}
    qualified=[]
    for site,(op,args) in expected.items():
        x=decoded.get(site)
        if not x or (x.mnemonic,x.op_str)!=(op,args):raise RuntimeError('Qualified operand differs: '+hex(site))
        qualified.append(dict(site=f'{site:08X}',bytes=x.bytes.hex(),mnemonic=op,operand=args))
    dump('native/qualified-operand-sites.json',qualified)
    for va,value in [(0x7efb9c,b' \0'),(0x7ee88c,b'\0')]:
        if view.read(va-0x400000,len(value))!=value:raise RuntimeError('Literal differs')
        save(f'native/literals/{va:08X}.bin',value)
    pointers=struct.unpack('<40I',view.read(0x886338-0x400000,160));tags=[view.string(p-0x400000) for p in pointers]
    save('native/tables/00886338.bin',view.read(0x886338-0x400000,160));dump('native/primary-item-type-tags.json',list(enumerate(tags)))
    if any(tag[:3]=='GOD' for tag in tags):raise RuntimeError('GOD has no primary dedicated enum')
    previous=b/'cn-subject-roster-publication-source-01'
    for rel in ['native/roster-declaration-and-publication-relations.json','native/004D5B20-expanded-cfg.asm',
        'native/qualified-operand-sites.json']:
        save('retained-declaration/'+rel,(previous/rel).read_bytes())
    resource=b/'cn-current-npc-name-source-01/inputs'
    data=(resource/'current-gamedata.csv').read_bytes();encoded=(resource/'current-gamedata.csvZ').read_bytes()
    if sha(data)!='16f7bb0f9cdf2965719408204800b329269c810821b96d3d81b5feca168534a3' or sha(encoded)!='8a72d850a34b14170c4cb0e91da9430559ea7def4e047130c533d666d67b893a':
        raise RuntimeError('Pinned resource pair differs')
    save('inputs/current-gamedata.csv',data);save('inputs/current-gamedata.csvZ',encoded)
    current_encoded=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/Data2/Patch/Comm/gamedata.csvZ').read_bytes()
    if current_encoded!=encoded:raise RuntimeError('Current encoded epoch differs')
    dump('inputs/current-encoded-observation.json',dict(path='C:/Users/risei/Desktop/God2-xjz/XJZ-CN/Data2/Patch/Comm/gamedata.csvZ',bytes=len(current_encoded),sha256=sha(current_encoded),read_only=True))
    lines=data.splitlines(keepends=True);offsets=[];offset=0
    for line in lines:offsets.append(offset);offset+=len(line)
    header=next(i for i,line in enumerate(lines) if line.startswith(b'ItemType,'))
    types=[next(csv.reader([line.decode('cp936')])) for line in lines[header+1:header+51]]
    if types[2][:3]!=['2801','2899','GOD']:raise RuntimeError('Actual ItemType GOD row differs')
    save('material/ItemType-raw-lines.bin',b''.join(lines[header:header+51]))
    rows=[];section=None;left=0
    for i,line in enumerate(lines):
        fields=next(csv.reader([line.decode('cp936')]))
        if len(fields)==2 and fields[0] in [r[2] for r in types] and fields[1].isdigit():
            section=fields[0];left=int(fields[1]);continue
        if left:
            left-=1
            if fields[0].isdigit() and 2801<=int(fields[0])<=2899:
                rows.append(dict(section=section,resource_key=int(fields[0]),source_line=i+1,
                    decoded_offset=offsets[i],fields=fields,raw_hex=line.hex(),record_sha256=sha(line)))
    if len(rows)!=34 or any(r['section']!='GOD' or r['resource_key']!=2801+i or len(r['fields'])!=6 or
        b'"' in bytes.fromhex(r['raw_hex']) or b'\0' in bytes.fromhex(r['raw_hex']) for i,r in enumerate(rows)):
        raise RuntimeError('Actual pointer-key source census differs')
    if data[415519:415527]!=b'GOD,34\r\n' or rows[0]['decoded_offset']!=415527 or rows[-1]['decoded_offset']+len(bytes.fromhex(rows[-1]['raw_hex']))!=416611:
        raise RuntimeError('Actual GOD block offsets differ')
    names=[r['fields'][4].encode('cp936') for r in rows]
    if min(map(len,names))!=4 or max(map(len,names))!=10:raise RuntimeError('Actual name boundaries differ')
    dump('material/ordered-GOD-source-rows.json',rows)
    dump('material/low-identifier-name-projections.json',[
        dict(native_absolute_identifier=i,resource_key=2800+i,source_line=rows[i-1]['source_line'] if i<=34 else None,
             name_with_nul_hex=(names[i-1]+b'\0').hex() if i<=34 else '2000',
             kind='actual GOD column4' if i<=34 else 'missing pinned key; native null fallback',
             actual_current_revision_and_replacement_qualification_required=True)
        for i in range(1,100)])
    relations=dict(version='cn',native_sha256=PIN,direction='S2C',opcode='30',phase='world-connection-1',
        actual_owner='world+89B26C',declaration_consumer='004D5B20',lookup='004283A0',resource_owner='actual this+65364',
        resource_key='abs(signed BYTE identifier)+2800',pointer_table='resource+B304C+WORDkey*4',pointer_capacity=35000,
        table_zero_initializer='00428860',actual_loader='00428C80',generic_name_reader='0042CFB0',
        name_column=4,parsed_name_offset=8,name_terminator_offset='2D',native_item_stride=396,
        independent_pointer_replacement_writer='0042D540',actual_Current_must_invalidate_relevant_replacements=True,
        actual_resource_section='GOD',actual_resource_records=34,actual_resource_keys=[2801,2834],
        low_nonzero_identifier_values=99,missing_pinned_identifier_values=65,missing_key_literal='SPACE+NUL',
        NPC_appearance_table_not_used=True,dedicated_GOD_type_enum_invented=False,
        native_tab_label_refresh='004D4B80',tab_name_source='role+DB +ordinal*3EC',
        tab_refresh_does_not_initialize_subject_fields=True,selected_tab_operand='signed BYTE role+CF',
        supplier='CnSubjectTemplateNames',existing_publisher='SharedSubjectRosterPublication',
        actual_low_nonzero30_requires_current_template_supplier=True,
        optional_lookup_vector_aligned_with_all_plan_records=True,lookup_vector_retained_by_completion=True,
        same_names_observed_before_queue_and_queue_accepted=True,wire_bytes_unchanged=True,
        process_memory_required=False,actual_common_rule_save_replay_issuer_configured=False,
        formal_application_hosted=False,complete_route=False)
    dump('native/template-name-and-tab-label-relations.json',relations)
    facts=dict(round=ROUND,previous_goal_turn_classification='progress:145 frame packing/source accounting and immutable seals',
        native_primary_metadata_bytes=sum(s['bytes'] for s in scopes),native_local_normal_entry_CFGs=len(scopes),
        native_instruction_sites=sum(s['sites'] for s in scopes),native_primary_operands_qualified=len(qualified),
        cn_subject_template_name_suppliers_added=1,cn_existing_roster_template_name_handoffs_added=1,
        cn_actual_GOD_name_records=34,cn_low_ID_missing_pinned_keys=65,
        new_packet_values=0,new_native_phase_source_bindings=0,new_source_owner_chains=0,new_tw_source_owner_chains=0,
        new_complete_bidirectional_routes=0,actual_common_rule_save_replay_issuer_configured=False,formal_application_hosted=False,
        whole_game_route_total=None,whole_game_completed_routes=None,whole_game_completion_percent=None,
        native_snapshot_required=False,original_native_wire_layout_changed=False,original_native_baseline_changed=False,
        build_run=False,tests_run=False,runtime_run=False,native_execution=False,Cplusplus_source_run=False,
        Windows_API_run=False,database_access=False,deployed=False,protected_contexts=protected,remaining=REMAINING)
    dump('findings.json',facts)
    lp=ROOT/books[1];ledger=json.loads(lp.read_text(encoding='utf-8'))
    if any(s['name']==NAME for s in ledger['dual_client_source_segments']):raise RuntimeError('Preserve ledger segment')
    ledger['dual_client_source_segments'].append(dict(name=NAME,round=ROUND,
        version_scope='pinned-cn-WORLD30-GOD-name-source-only',
        status='Actual34 GOD names and current conditional null fallback ->existing ordered roster qualifier; common authority/actual Current/issuer/Application incomplete',
        source_paths=SOURCES,native_c2s_by_phase={},native_s2c_by_phase={},
        source_owner_chains_added=0,tw_source_owner_chains_added=0,formal_application_hosted=False,
        complete_gameplay_routes_added=0,evidence=o.relative_to(ROOT).as_posix(),remaining=REMAINING))
    ledger['dual_client_execution_plan']['latest_work_round']=ROUND
    ledger['dual_client_execution_plan']['next_source_frontier']='Actual common roster/subject/recipient/fields/skill identities/rules/save/durable replay/committed issuer/Application; actual source Current/replacement writers/full timing/variants; all TW/CN/web gameplay/numeric64/stack99/denominator. PHASE1.'
    lp.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (ROOT/books[0]).open('a',encoding='utf-8') as f:
        f.write('\n\n## CN WORLD30 actual GOD names ('+ROUND+')\n\n'
            'Recovered WORDkey direct pointer table/generic column4 name writer and actual34 GOD rows; separated NPC appearance names and conditional missing-key SPACE literal. '
            'Added pinned copied-input CnSubjectTemplateNames/current revision supplier and aligned owning name evidence handoff in existing ordered roster publisher. '
            'Independent0042D540 pointer replacement must invalidate source revision;004D4B80 is tab-label refresh, not attribute initialization. '
            'New opcode/phase/owner/complete route0; actual common authority/Current/rules/save/replay/issuer/Application remain open. Full goal/PHASE1 retained; no build/test/native/API/SQL/deploy.\n')
    origins=[]
    for rel in SOURCES+books:
        value=(ROOT/rel).read_bytes();save('source/current/'+rel,value);origins.append(dict(path=rel,bytes=len(value),sha256=sha(value)))
        if rel in old:
            patch=''.join(difflib.unified_diff(old[rel].decode('utf-8-sig').splitlines(True),value.decode('utf-8-sig').splitlines(True),fromfile='before/'+rel,tofile='source/'+rel))
            if patch:save('diff/'+rel+'.diff',patch.encode('utf-8'))
    dump('source/source-origins.json',origins)
    print(json.dumps({k:facts[k] for k in ['round','native_instruction_sites','cn_actual_GOD_name_records','cn_low_ID_missing_pinned_keys','new_complete_bidirectional_routes']}))

if __name__=='__main__':main()
