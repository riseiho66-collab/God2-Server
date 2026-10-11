"""Pinned WORLD33/39 selected-row sources and existing publisher; static only."""
import difflib
import hashlib
import json
import re
from pathlib import Path
import capstone
import pefile
from .cn_wrapper_route_frontier import ROOT
from .cn_pe_import_directory import FileView
from .cn_preborn_selected_subject_source_delivery import local_cfg

NAME='cn-selected-subject-update-source-01';ROUND='20261008-cn-selected-subject-update-source'
PIN='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
SOURCES=['src/cn/protocol/CnSelectedSubjectUpdate.h',
 'src/cn/world/CnPrebornSubjectState.h','src/cn/world/CnPrebornSubjectState.cpp',
 'src/cn/world/SharedSubjectRosterPublication.h','src/cn/world/SharedSubjectRosterPublication.cpp',
 'docs/research/cn-selected-subject-update-source-20261008.md',
 'tools/reconstruction/cn_selected_subject_update_source_delivery.py','tools/reconstruction/dual_client_route_catalog.py']
REMAINING=[
 'Actual recipient/current selection/per-record evolving native order/common identity/field semantics/rules/save/durable replay/committed issuer/Application remain unconfigured.',
 'WORLD32 resource selector/string bounds, full native helper/dispatcher timing/variants, native null vs missing source, and all gameplay remain open.',
 'Full TW/CN/PC/web/WSS/numeric64/stack99/whole-game denominator and later comprehensive tests/repair/recovery release remain open.']

def sha(raw):return hashlib.sha256(raw).hexdigest()

def main():
    b=ROOT/'artifacts/integration/packet-connections-20261006';o=b/NAME
    if not (o/'before-manifest.json').exists() or (o/'findings.json').exists():raise RuntimeError('Fresh before required')
    def save(rel,raw):
        p=o/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as f:f.write(raw)
    def dump(rel,v):save(rel,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    before=json.loads((o/'before-manifest.json').read_text(encoding='utf-8'))
    if len(before)!=187:raise RuntimeError('Expected187 before files')
    old={r['path']:(o/r['snapshot']).read_bytes() for r in before}
    books=['docs/PACKET_CONNECTION_GOAL_20261006.md','artifacts/integration/packet-connections-20261006/packet-route-ledger.json']
    reports={f'artifacts/integration/packet-connections-20261006/packet-progress-latest.{e}' for e in ['json','md']}
    protected=[]
    for row in before:
        if sha(old[row['path']])!=row['sha256']:raise RuntimeError('Before source differs')
        if row['path'] not in set(SOURCES+books)|reports:
            if (ROOT/row['path']).read_bytes()!=old[row['path']]:raise RuntimeError('Protected source differs: '+row['path'])
            protected.append(row)
    prior=(o/'retained-prior/cn-subject-template-name-source-01/manifest.json').read_bytes()
    if sha(prior)!='ad72d6f477bb8ae8b49494fd50bd74b367a4a0ce148fc51452f8bf9a0f50586c' or not json.loads(prior)['sealed']:
        raise RuntimeError('Prior seal differs')
    raw=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe').read_bytes()
    if sha(raw)!=PIN:raise RuntimeError('Pinned PE differs')
    view=FileView(pefile.PE(data=raw,fast_load=True),raw)
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True
    recovery=Path('C:/Users/risei/Desktop/God2-xjz/God2_opt_source_recovery_20260926_055734/decompiled')
    scopes=[];decoded={}
    for va in [0x4d5880,0x4d5a90,0x4d3e30,0x4d5a10]:
        paths=list(recovery.glob(f'part_*/{va:08x}_*.c'))
        if len(paths)!=1:raise RuntimeError('Primary source not unique')
        source=paths[0].read_bytes();size=int(re.search(rb'Size: (\d+) bytes',source)[1])
        code=view.read(va-0x400000,size);cfg,ins=local_cfg(md,code,va,{})
        expected_frontier=[dict(site='004d3e30',reason='outside_metadata_code')] if va==0x4d5880 else []
        if cfg['frontier']!=expected_frontier:raise RuntimeError('Entry-rooted local CFG frontier differs')
        save('native/source/'+paths[0].name,source);save(f'native/{va:08X}.bin',code);dump(f'native/{va:08X}-cfg.json',cfg)
        save(f'native/{va:08X}-cfg.asm',('\n'.join(f'{a:08x} {x.bytes.hex()} {x.mnemonic} {x.op_str}' for a,x in sorted(ins.items()))+'\n').encode())
        scopes.append(dict(va=f'{va:08X}',bytes=size,sites=len(ins),frontier=cfg['frontier']));decoded.update(ins)
    dump('native/source-scopes.json',scopes)
    branches=[]
    for op,cell,target,consumer,length_cell,length_target,length in [
        ('33',0x492aa4,0x491374,0x4d5880,0x567d70,0x567b85,2),
        ('39',0x492abc,0x4913b0,0x4d5a90,0x567d88,0x567b9a,17),
        ('32',0x492aa0,0x491360,0x4d5a10,0x567d6c,0x567b85,2)]:
        for va,value in [(cell,target),(length_cell,length_target)]:
            actual=view.read(va-0x400000,4)
            if int.from_bytes(actual,'little')!=value:raise RuntimeError('Primary table target differs')
            save(f'native/tables/{va:08X}.bin',actual)
        code=view.read(target-0x400000,20);cfg,ins=local_cfg(md,code,target,{})
        if (ins[target+4].mnemonic,ins[target+4].op_str)!=('lea','ecx, [ebx + 0x89b26c]') or (ins[target+10].mnemonic,ins[target+10].op_str)!=('call',hex(consumer)):
            raise RuntimeError('Actual WORLD owner call differs')
        save(f'native/WORLD{op}-primary-case.bin',code);dump(f'native/WORLD{op}-primary-case-cfg.json',cfg)
        length_bytes=view.read(length_target-0x400000,7)
        if length_bytes!=b'\xb8'+length.to_bytes(4,'little')+b'\x5d\xc3':raise RuntimeError('Primary native length differs')
        save(f'native/WORLD{op}-length.bin',length_bytes)
        branches.append(dict(opcode=op,primary_cell=f'{cell:08X}',primary_target=f'{target:08X}',consumer=f'{consumer:08X}',
            length_cell=f'{length_cell:08X}',length_target=f'{length_target:08X}',logical_bytes=length,source_connected=op!='32',frontier=cfg['frontier']))
    expected={
        0x4d5883:('mov','eax, dword ptr [ecx + 0x430a8]'),0x4d5889:('mov','edx, dword ptr [eax + 0xd0]'),
        0x4d5891:('je','0x4d58a4'),0x4d5898:('mov','byte ptr [edx + 0x40], al'),0x4d589f:('jmp','0x4d3e30'),
        0x4d3e40:('js','0x4d3ef1'),0x4d3e4f:('test','bl, 8'),0x4d3e56:('lea','eax, [eax*8 - 1]'),
        0x4d3e6e:('test','bl, 4'),0x4d3e76:('mov','eax, 8'),0x4d3e96:('test','bl, 2'),
        0x4d3e9e:('mov','eax, 9'),0x4d3ecb:('test','bl, 1'),0x4d3ed0:('push','0xa'),
        0x4d5aa1:('mov','ebx, dword ptr [eax + 0xd0]'),0x4d5aa9:('je','0x4d5b0d'),
        0x4d5ab5:('mov','esi, dword ptr [edx]'),0x4d5ab7:('mov','dword ptr [ebx + 0x2c], esi'),
        0x4d5aba:('mov','ecx, dword ptr [edx + 8]'),0x4d5abe:('mov','dword ptr [ebx + 0x30], ecx'),
        0x4d5ac1:('movzx','eax, word ptr [edx + 4]'),0x4d5ac9:('mov','word ptr [ebx + 0x34], ax'),
        0x4d5acd:('movzx','eax, word ptr [edx + 0xc]'),0x4d5ad6:('mov','word ptr [ebx + 0x36], ax'),
        0x4d5aea:('movzx','eax, word ptr [ebx + 0x36]'),0x4d5aef:('movzx','eax, word ptr [ebx + 0x34]'),
        0x4d5a33:('movsx','eax, byte ptr [ecx + 0xd5354]'),0x4d5a3e:('imul','eax, edx, 0x5e')}
    qualified=[]
    for site,(op,args) in expected.items():
        x=decoded.get(site)
        if not x or (x.mnemonic,x.op_str)!=(op,args):raise RuntimeError('Qualified operand differs: '+hex(site))
        qualified.append(dict(site=f'{site:08X}',bytes=x.bytes.hex(),mnemonic=op,operand=args))
    dump('native/qualified-operand-sites.json',qualified)
    if view.read(0x7ef9b8-0x400000,6)!=b'%d/%d\0':raise RuntimeError('Native pair format differs')
    save('native/literals/007EF9B8.bin',b'%d/%d\0')
    relations=dict(version='cn',native_sha256=PIN,direction='S2C',phase='world-connection-1',branches=branches,
        actual_owner='world+89B26C',actual_role='UI+430A8',actual_selected_row_pointer='role+D0',
        native_no_selected_row_noop=True,packet_subject_ID_present=False,current_selection_and_prior30_order_required=True,
        WORLD33=dict(logical_bytes=2,row_write='BYTE+40',tail='004D3E30',helper_handle='signed WORD UI+1C84C8>=0',
            helper_group='1D',helper_controls=['1A','1B','1C','1D'],helper_bits=[8,4,2,1],helper_set_resources=[7,8,9,10],helper_unset_resource=-1,
            high_four_bits_retained=True,status_names_qualified=False),
        WORLD39=dict(logical_bytes=17,payload_dword_offsets=[0,8],row_dword_offsets=['2C','30'],
            payload_zero_extended_word_offsets=[4,12],row_word_offsets=['34','36'],
            unconsumed_payload_offsets=[6,7,14,15],literal='%d/%d',native_ui_controls=[4,5],
            DWORD_signed_decimal_presentation_preserved=True,WORD_zero_extension_preserved=True,numeric64_extension_complete=False),
        WORLD32=dict(source_connected=False,remaining='Actual resource+D5354 signed maximum and D5356+selector*5E string/bounds/current source'),
        source_view='CnSelectedSubjectUpdate',actual_full_row_projection_preserves_other_bytes=True,
        optional_snapshot_full_selected_row_and_Current_handoff=True,native_snapshot_operational_requirement=False,
        existing_publisher='SharedSubjectRosterPublication',new_ordered_forms=['33','39'],held_original_order_and_wire_retained=True,
        minimum_actual_record_bytes=2,existing_native_transport_operational_limits_unchanged=True,
        actual_common_rule_save_replay_issuer_configured=False,formal_application_hosted=False,complete_route=False)
    dump('native/selected-row-update-relations.json',relations)
    facts=dict(round=ROUND,previous_goal_turn_classification='progress:146 actual GOD names/current source and existing roster handoff/seals',
        native_primary_metadata_bytes=sum(s['bytes'] for s in scopes),native_local_normal_entry_CFGs=sum(not s['frontier'] for s in scopes),
        native_instruction_sites=sum(s['sites'] for s in scopes),native_primary_operands_qualified=len(qualified),
        cn_selected_subject_typed_forms_added=2,cn_selected_subject_full_row_source_handoffs_added=1,
        cn_existing_ordered_roster_selected_forms_added=2,
        new_packet_values=0,new_native_phase_source_bindings=2,new_source_owner_chains=0,new_tw_source_owner_chains=0,
        new_complete_bidirectional_routes=0,actual_common_rule_save_replay_issuer_configured=False,formal_application_hosted=False,
        whole_game_route_total=None,whole_game_completed_routes=None,whole_game_completion_percent=None,
        native_snapshot_required=False,original_native_wire_layout_changed=False,original_native_baseline_changed=False,
        build_run=False,tests_run=False,runtime_run=False,native_execution=False,Cplusplus_source_run=False,
        Windows_API_run=False,database_access=False,deployed=False,protected_contexts=protected,remaining=REMAINING)
    dump('findings.json',facts)
    lp=ROOT/books[1];ledger=json.loads(lp.read_text(encoding='utf-8'))
    if any(s['name']==NAME for s in ledger['dual_client_source_segments']):raise RuntimeError('Preserve ledger segment')
    ledger['dual_client_source_segments'].append(dict(name=NAME,round=ROUND,
        version_scope='pinned-cn-WORLD33-39-current-selected-row-source-only',
        status='Exact2/17B forms, readonly actual full selected row projection and existing held ordered publisher; actual common selection/fields/rules/save/replay/issuer/Application incomplete',
        source_paths=SOURCES,native_c2s_by_phase={},native_s2c_by_phase={'world-connection-1':['33','39']},
        source_owner_chains_added=0,tw_source_owner_chains_added=0,formal_application_hosted=False,
        complete_gameplay_routes_added=0,evidence=o.relative_to(ROOT).as_posix(),remaining=REMAINING))
    ledger['dual_client_execution_plan']['latest_work_round']=ROUND
    ledger['dual_client_execution_plan']['next_source_frontier']='Actual current selection/common roster/field semantics/rules/save/durable replay/committed issuer/Application; WORLD32 resource+D5354/D5356 selected string source/bounds; all TW/CN/web gameplay/numeric64/stack99/denominator. PHASE1.'
    lp.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (ROOT/books[0]).open('a',encoding='utf-8') as f:
        f.write('\n\n## CN WORLD33/39 actual selected-row updates ('+ROUND+')\n\n'
            'Recovered actual world owner/case/length2/17 and current role+D0 selected-row null gates. '
            'Preserved BYTE40/tail icon bits and DWORD2C/30, MOVZX WORD34/36, four unread payload bytes and signed DWORD %d presentation. '
            'Added exact typed forms/full-row readonly projection, optional current native snapshot full row handoff and existing held publisher ordered33/39 forms. '
            'Added two S2C WORLD bindings; new opcode/owner/complete route0. Actual common selection/fields/rules/save/replay/issuer/Application and WORLD32 resource source remain open. '
            'Full goal/PHASE1 retained; no build/test/native/API/SQL/deploy, no numeric64 completion claim.\n')
    origins=[]
    for rel in SOURCES+books:
        value=(ROOT/rel).read_bytes();save('source/current/'+rel,value);origins.append(dict(path=rel,bytes=len(value),sha256=sha(value)))
        if rel in old:
            patch=''.join(difflib.unified_diff(old[rel].decode('utf-8-sig').splitlines(True),value.decode('utf-8-sig').splitlines(True),fromfile='before/'+rel,tofile='source/'+rel))
            if patch:save('diff/'+rel+'.diff',patch.encode('utf-8'))
    dump('source/source-origins.json',origins)
    print(json.dumps({k:facts[k] for k in ['round','native_instruction_sites','cn_selected_subject_typed_forms_added','new_native_phase_source_bindings','new_complete_bidirectional_routes']}))

if __name__=='__main__':main()
