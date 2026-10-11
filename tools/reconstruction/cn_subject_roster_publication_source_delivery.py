"""Preserve WORLD30 native roster branches and ordered output source; no runtime."""
import difflib
import hashlib
import json
from pathlib import Path
import capstone
import pefile
from .cn_wrapper_route_frontier import ROOT
from .cn_pe_import_directory import FileView
from .cn_preborn_selected_subject_source_delivery import local_cfg

NAME='cn-subject-roster-publication-source-01';ROUND='20261008-cn-subject-roster-publication-source'
PIN='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
SOURCES=['src/cn/protocol/CnSubjectDeclaration30.h','src/cn/world/SharedSubjectRosterPublication.h',
 'src/cn/world/SharedSubjectRosterPublication.cpp','src/cn/world/SharedWorldGameplay.h','src/cn/world/SharedWorldGameplay.cpp',
 'docs/research/cn-subject-roster-publication-source-20261008.md',
 'tools/reconstruction/cn_subject_roster_publication_source_delivery.py','tools/reconstruction/dual_client_route_catalog.py']
REMAINING=[
 'Actual common subject/recipient/native roster/name/staged inactive row/all field semantics/rules/save/durable replay/committed issuer/Application remain unconfigured.',
 'Declaration helpers/initialization/template lookup and all upstream/state/variants remain open; no TW CUSTOM policy or guessed native IDs/names/rules imported.',
 'CN skill import/provider/preborn initial issuer/native84 caller/phase and full TW/CN/PC/web/WSS/gameplay/numeric64/stack99/denominator/later comprehensive tests/repair/recovery release remain open.']

def sha(raw):return hashlib.sha256(raw).hexdigest()

def main():
    b=ROOT/'artifacts/integration/packet-connections-20261006';o=b/NAME
    if not (o/'before-manifest.json').exists() or (o/'findings.json').exists():raise RuntimeError('Fresh before required')
    def save(rel,raw):
        p=o/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as f:f.write(raw)
    def dump(rel,v):save(rel,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    before=json.loads((o/'before-manifest.json').read_text(encoding='utf-8'))
    if len(before)!=174:raise RuntimeError('Expected174 before files')
    old={r['path']:(o/r['snapshot']).read_bytes() for r in before}
    books=['docs/PACKET_CONNECTION_GOAL_20261006.md','artifacts/integration/packet-connections-20261006/packet-route-ledger.json']
    reports={f'artifacts/integration/packet-connections-20261006/packet-progress-latest.{e}' for e in ['json','md']}
    protected=[]
    for row in before:
        if sha(old[row['path']])!=row['sha256']:raise RuntimeError('Before source differs')
        if row['path'] not in set(SOURCES+books)|reports:
            if (ROOT/row['path']).read_bytes()!=old[row['path']]:raise RuntimeError('Protected source differs: '+row['path'])
            protected.append(row)
    prior=(o/'retained-prior/cn-program-message-catalog-source-01/manifest.json').read_bytes()
    if sha(prior)!='d95298bd5d311f117afd43f07d8532cc2b8c74f27024ca036ec5fb15acf9a4b8' or not json.loads(prior)['sealed']:
        raise RuntimeError('Prior seal differs')
    raw=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe').read_bytes()
    if sha(raw)!=PIN:raise RuntimeError('Pinned PE differs')
    view=FileView(pefile.PE(data=raw,fast_load=True),raw)
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True
    recovery=Path('C:/Users/risei/Desktop/God2-xjz/God2_opt_source_recovery_20260926_055734/decompiled/part_0012')
    for rel in ['004d5b20_FUN_004d5b20.c','004d5b83_caseD_4.c']:save('native/source/'+rel,(recovery/rel).read_bytes())
    table=view.read(0x4d5c98-0x400000,8);targets=[int.from_bytes(table[i:i+4],'little') for i in [0,4]]
    indices=view.read(0x4d5ca0-0x400000,31)
    if targets!=[0x4d5b83,0x4d5b87] or set(indices)!={0,1} or [i+4 for i,n in enumerate(indices) if n==0]!=[4,8,10,31,32,33,34]:
        raise RuntimeError('Primary declaration switch differs')
    save('native/tables/004D5C98.bin',table);save('native/tables/004D5CA0.bin',indices)
    code=view.read(0x4d5b20-0x400000,0x178)
    old_cfg,old_ins=local_cfg(md,code[:99],0x4d5b20,{})
    save('native/004D5B20-primary99.bin',code[:99]);dump('native/004D5B20-primary99-cfg.json',old_cfg)
    cfg,ins=local_cfg(md,code,0x4d5b20,{0x4d5b7c:('dword ptr [eax*4 + 0x4d5c98]',targets)})
    if cfg['frontier'] or len(ins)!=114 or cfg['ret_sites']!=['004d5c43','004d5c53']:raise RuntimeError('Expanded entry CFG differs')
    save('native/004D5B20-expanded.bin',code);dump('native/004D5B20-expanded-cfg.json',cfg)
    save('native/004D5B20-expanded-cfg.asm',('\n'.join(f'{a:08x} {x.bytes.hex()} {x.mnemonic} {x.op_str}' for a,x in sorted(ins.items()))+'\n').encode())
    expected={
        0x4d5b2b:('movsx','eax, byte ptr [ebx]'),0x4d5b31:('xor','ecx, edx'),0x4d5b33:('sub','ecx, edx'),
        0x4d5b49:('cmp','al, 0x10'),0x4d5b4b:('jae','0x4d5c3e'),
        0x4d5b66:('mov','word ptr [edx], ax'),0x4d5b89:('mov','byte ptr [esi + 0x133], al'),
        0x4d5b96:('jl','0x4d5c56'),0x4d5bb1:('cmp','byte ptr [ebx + 0x11], 1'),
        0x4d5be0:('movsx','ecx, word ptr [edx]'),0x4d5be5:('je','0x4d5c46'),
        0x4d5bfe:('inc','byte ptr [eax + 0xd4]'),0x4d5c07:('jge','0x4d5c29'),
        0x4d5c0f:('mov','dword ptr [eax + 0xd0], edx'),0x4d5c23:('mov','byte ptr [ecx + 0xcf], al'),
        0x4d5c48:('mov','byte ptr [edx + 0x1f0], 0'),0x4d5c5c:('add','eax, 0xaf0'),
        0x4d5c62:('call','0x4283a0'),0x4d5c6e:('mov','ecx, 0x7efb9c')}
    qualified=[]
    for site,(op,args) in expected.items():
        x=ins.get(site)
        if not x or (x.mnemonic,x.op_str)!=(op,args):raise RuntimeError('Native operand differs: '+hex(site))
        qualified.append(dict(site=f'{site:08X}',bytes=x.bytes.hex(),mnemonic=op,operand=args))
    dump('native/qualified-operand-sites.json',qualified)
    for va,expected_value in [(0x492a98,0x491324),(0x567d64,0x567c11)]:
        cell=view.read(va-0x400000,4)
        if int.from_bytes(cell,'little')!=expected_value:raise RuntimeError('Primary WORLD30 table differs')
        save(f'native/tables/{va:08X}.bin',cell)
    branch=view.read(0x491324-0x400000,20);branch_cfg,branch_ins=local_cfg(md,branch,0x491324,{})
    if (branch_ins[0x49132e].mnemonic,branch_ins[0x49132e].op_str)!=('call','0x4d5b20') or branch_ins[0x491328].op_str!='ecx, [ebx + 0x89b26c]':
        raise RuntimeError('Qualified WORLD30 owner call differs')
    save('native/WORLD30-primary-case.bin',branch);dump('native/WORLD30-primary-case-cfg.json',branch_cfg)
    length=view.read(0x567c11-0x400000,7)
    if length!=bytes.fromhex('b8130000005dc3'):raise RuntimeError('Native length19 differs')
    save('native/WORLD30-length19.bin',length)
    if view.read(0x7efb9c-0x400000,2)!=b' \0':raise RuntimeError('Native fallback space differs')
    save('native/literals/007EFB9C.bin',b' \0')
    for name,rel in [('cn-subject-status31-source-01','source/status31-publication-relations.json'),
        ('cn-world-subject-skill-publication-source-01','source/publication-relations.json')]:
        p=b/name/rel
        save('retained-source-relations/'+name+'.json',p.read_bytes())
    relations=dict(version='cn',native_sha256=PIN,opcode='30',direction='S2C',phase='world-connection-1',logical_size=19,
        primary_world_cell='00492A98',primary_world_target='00491324',primary_consumer='004D5B20',actual_owner='world+89B26C',
        primary_length_cell='00567D64',primary_length_return='00567C11',primary_metadata99_incomplete=True,
        expanded_entry_cfg_bytes=len(code),expanded_entry_cfg_instruction_sites=len(ins),primary_compressed_switch_cases=31,
        native_absolute_signed_byte_identifier=True,native_minus128_identifier=128,native_capacity=16,
        capacity_gate_precedes_duplicate_reset=True,staged_inactive_slot_written_before_duplicate_search=True,
        high_ID_control17_equals1_first_matching_skill_count_reset_only=True,negative_append_selects_new_row=True,
        low_ID_template_lookup_plus_AF0=True,missing_actual_template_lookup_literal='space',
        inline_name_overread_not_emulated=True,common_identity_or_rules_supplied=False,
        shared_view='CnSubjectDeclaration30',publisher='SharedSubjectRosterPublication',actual_record_order_forms=['30','31','34','35'],
        same_actual_committed_event_one_held_aggregate=True,post_commit_before_queue_and_queue_accepted_owner_required=True,
        definitions_aligned_with_records_from_actual_shared_CN_catalog=True,plan_and_definitions_retained_by_completion=True,
        actual1C_same_ready_lease_binding_emits_nothing=True,separate_status_skill_publishers_mutually_exclusive=True,
        process_memory_or_native_pointer_required=False,actual_common_rule_save_replay_issuer_configured=False,
        formal_application_hosted=False,complete_route=False,same_opcode_C2S30_pairing=None)
    dump('native/roster-declaration-and-publication-relations.json',relations)
    facts=dict(round=ROUND,previous_goal_turn_classification='progress:143 pinned ProgramMsg supplier/metric source correction and seals',
        native_primary_metadata99_bytes=99,native_expanded_entry_cfg_bytes=len(code),native_expanded_entry_cfg_instruction_sites=len(ins),
        native_primary_operands_qualified=len(qualified),cn_subject_declaration30_shared_views_added=1,
        cn_subject_roster_ordered_publication_source_owners_added=1,cn_existing_gameplay_roster_bindings_added=1,
        cn_existing_subject_publication_exclusivity_gates_added=1,
        new_packet_values=0,new_native_phase_source_bindings=1,new_source_owner_chains=1,new_tw_source_owner_chains=0,
        new_complete_bidirectional_routes=0,actual_common_rule_save_replay_issuer_configured=False,formal_application_hosted=False,
        whole_game_route_total=None,whole_game_completed_routes=None,whole_game_completion_percent=None,
        native_snapshot_required=False,original_native_wire_layout_changed=False,original_native_baseline_changed=False,
        build_run=False,tests_run=False,runtime_run=False,native_execution=False,Cplusplus_source_run=False,
        Windows_API_run=False,database_access=False,deployed=False,protected_contexts=protected,remaining=REMAINING)
    dump('findings.json',facts)
    lp=ROOT/books[1];ledger=json.loads(lp.read_text(encoding='utf-8'))
    if any(s['name']==NAME for s in ledger['dual_client_source_segments']):raise RuntimeError('Preserve ledger segment')
    ledger['dual_client_source_segments'].append(dict(name=NAME,round=ROUND,
        version_scope='pinned-cn-world30-declaration-and-ordered30-31-34-35-post-commit-source-only',
        status='Exact declaration append/reset/select source and one ordered held publisher; actual common mapping/name/row/rules/save/replay/issuer/Application incomplete',
        source_paths=SOURCES,native_c2s_by_phase={},native_s2c_by_phase={'world-connection-1':['30']},
        source_owner_chains_added=1,tw_source_owner_chains_added=0,formal_application_hosted=False,
        complete_gameplay_routes_added=0,evidence=o.relative_to(ROOT).as_posix(),remaining=REMAINING))
    ledger['dual_client_execution_plan']['latest_work_round']=ROUND
    ledger['dual_client_execution_plan']['next_source_frontier']='Actual common roster/name/inactive row/subject/recipient/field/skill semantics and committed issuer/rules/save/replay/Application; native declaration helper initialization/template/current and all variants; preborn84 caller/phase, full TW/CN/web gameplay/numeric64/stack99/denominator. PHASE1 no runtime import.'
    lp.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (ROOT/books[0]).open('a',encoding='utf-8') as f:
        f.write('\n\n## CN WORLD30 roster and ordered publication ('+ROUND+')\n\n'
            'Recovered WORLD30 length19/actual owner/primary compressed switch extended114-site entry CFG; preserved incomplete99B metadata. Exact signed-BYTE absolute ID/capacity16/staged inactive row/first high-ID control1 skill-count reset/negative append selection and name source operands retained. '
            'New typed declaration and ordered30/31/34/35 actual committed event held publisher; same1C ready lease, separate status/skill publishers mutually exclusive, real post-commit identity/roster/name/fields/rules/save/durable replay/issuer required. '
            'One partial CN owner/one S2C WORLD30 association; new opcode/full route0. Common providers/Application/all variants/full goal remain open; no native-memory prerequisite. PHASE1 no build/test/native/API/server/SQL/deploy.\n')
    origins=[]
    for rel in SOURCES+books:
        value=(ROOT/rel).read_bytes();save('source/current/'+rel,value);origins.append(dict(path=rel,bytes=len(value),sha256=sha(value)))
        if rel in old:
            patch=''.join(difflib.unified_diff(old[rel].decode('utf-8-sig').splitlines(True),value.decode('utf-8-sig').splitlines(True),fromfile='before/'+rel,tofile='source/'+rel))
            if patch:save('diff/'+rel+'.diff',patch.encode('utf-8'))
    dump('source/source-origins.json',origins)
    print(json.dumps({k:facts[k] for k in ['round','native_expanded_entry_cfg_instruction_sites','cn_subject_roster_ordered_publication_source_owners_added','new_native_phase_source_bindings','new_complete_bidirectional_routes']}))

if __name__=='__main__':main()
