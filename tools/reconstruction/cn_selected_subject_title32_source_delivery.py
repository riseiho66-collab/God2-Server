"""WORLD32 resource/ordered source and reviewed shared context; static only."""
import difflib
import hashlib
import json
from pathlib import Path
import capstone
import pefile
from .cn_wrapper_route_frontier import ROOT
from .cn_pe_import_directory import FileView
from .cn_preborn_selected_subject_source_delivery import local_cfg

NAME='cn-selected-subject-title32-source-01'
ROUND='20261008-cn-selected-subject-title32-source'
PIN='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
SOURCES=['src/cn/assets/CnSubjectTemplateNames.h','src/cn/assets/CnSubjectTemplateNames.cpp',
 'src/cn/protocol/CnSelectedSubjectTitle32.h',
 'src/cn/world/SharedSubjectRosterPublication.h','src/cn/world/SharedSubjectRosterPublication.cpp',
 'src/cn/net/SharedCredentialServer.h','src/cn/net/SharedCredentialServer.cpp','src/core/Application.cpp',
 'docs/research/cn-selected-subject-title32-source-20261008.md',
 'tools/reconstruction/cn_selected_subject_title32_source_delivery.py','tools/reconstruction/dual_client_route_catalog.py']
REMAINING=[
 'WORLD32 accepted selector4 source/terminator, independent42CA20 caller and actual Current invalidation-before-write remain open.',
 'Actual current selection/common roster/semantics/rules/save/durable replay/committed issuer/Application remain unconfigured.',
 'CN main still null plan; actual compose_native_login caller, stored Prepare/Authority, role22/world reservation/entry/common presence/per-session TW hooks remain open.',
 'Conditional receivers14/12 unchanged:47DE70 and4812B0 open; next entry475D40 through475F5B decode frontier.',
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
    if len(before)!=190:raise RuntimeError('Expected190 before files')
    old={r['path']:(o/r['snapshot']).read_bytes() for r in before}
    books=['docs/PACKET_CONNECTION_GOAL_20261006.md','artifacts/integration/packet-connections-20261006/packet-route-ledger.json']
    reports={f'artifacts/integration/packet-connections-20261006/packet-progress-latest.{e}' for e in ['json','md']}
    protected=[]
    for r in before:
        if sha(old[r['path']])!=r['sha256']:raise RuntimeError('Before receipt differs')
        if r['path'] not in set(SOURCES+books)|reports:
            if (ROOT/r['path']).read_bytes()!=old[r['path']]:raise RuntimeError('Protected source differs: '+r['path'])
            protected.append(r)
    prior=(o/'retained-prior/cn-selected-subject-update-source-01/manifest.json').read_bytes()
    if sha(prior)!='a1743d4950464aaaa6caa8a2f2c11d94f67342cd208e3ea98c5600458efc9ef5' or not json.loads(prior)['sealed']:
        raise RuntimeError('Prior seal differs')
    agents=[]
    for name in ['title32-boundary','receiver-frontier','m2-source-hosting']:
        folder=o/'agents'/name;raw=(folder/'findings.json').read_bytes()
        files=[dict(path=p.relative_to(folder).as_posix(),bytes=p.stat().st_size,sha256=sha(p.read_bytes()))
               for p in sorted(folder.rglob('*')) if p.is_file()]
        agents.append(dict(agent=name,findings_sha256=sha(raw),findings=json.loads(raw),files=files,
                           formal_source_modified_by_agent=False))
    seal=(o/'agents/title32-boundary/seal.json').read_bytes()
    if sha(seal)!='5f5101eb0c72c6e8213e45e7d25279c6c57149a8aa4d9fd47a4ee454570957f1':raise RuntimeError('Title agent seal differs')
    for r in json.loads(seal)['files']:
        raw=(o/'agents/title32-boundary'/r['path']).read_bytes()
        if sha(raw)!=r['sha256'] or len(raw)!=r['bytes']:raise RuntimeError('Title receipt differs')
    patch=(o/'agents/m2-source-hosting/readonly-account-snapshot-context.proposed.patch').read_bytes()
    if sha(patch)!='0a32953c21e5e2892297de76451afdd48736cce672b691b49627eac47c0095e8':raise RuntimeError('Reviewed proposal differs')
    dump('parallel-agent-deliveries.json',agents)
    raw=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe').read_bytes()
    if sha(raw)!=PIN:raise RuntimeError('Pinned PE differs')
    view=FileView(pefile.PE(data=raw,fast_load=True),raw)
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True
    for va,target in [(0x492aa0,0x491360),(0x567d6c,0x567b85)]:
        value=view.read(va-0x400000,4)
        if int.from_bytes(value,'little')!=target:raise RuntimeError('Primary table differs')
        save(f'native/tables/{va:08X}.bin',value)
    code=view.read(0x491360-0x400000,20);cfg,ins=local_cfg(md,code,0x491360,{})
    if (ins[0x491364].mnemonic,ins[0x491364].op_str)!=('lea','ecx, [ebx + 0x89b26c]') or (ins[0x49136a].mnemonic,ins[0x49136a].op_str)!=('call','0x4d5a10'):
        raise RuntimeError('Qualified owner differs')
    save('native/WORLD32-primary-case.bin',code);dump('native/WORLD32-primary-case-cfg.json',cfg)
    value=view.read(0x567b85-0x400000,7)
    if value!=b'\xb8\x02\0\0\0\x5d\xc3':raise RuntimeError('Native logical length differs')
    save('native/WORLD32-length.bin',value)
    records=json.loads((o/'agents/title32-boundary/inputs/GodLevel-source-records.json').read_text(encoding='utf-8'))
    relations=dict(version='cn',native_sha256=PIN,direction='S2C',phase='world-connection-1',opcode='32',
        logical_bytes=2,primary_cell='00492AA0',primary_target='00491360',consumer='004D5A10',
        length_cell='00567D6C',length_target='00567B85',actual_owner='world+89B26C',
        actual_role='UI+430A8',actual_selected_row_pointer='role+D0',native_null_selection_noop=True,
        packet_subject_ID_present=False,actual_current_selection_and_prior30_order_required=True,
        native_signed_header='BYTE resource+D5354',header_count=4,native_string_base='D5356',native_stride=94,
        selected_row_text_offset='13',native_UI_control=3,native_UI_format='%s',
        GodLevel_actual_records=records,selector_actions={'0..3':'copy actual column0 plus NUL','4':'accepted by native comparison; UNKNOWN string','5..255':'retain actual row text and refresh UI'},
        selector4_empty_string_invented=False,all_native_variants_connected=False,
        reset_clear_exclusive_end='D54CE',bytes_D54CE_CF_qualified=False,independent42CA20_caller_qualified=False,
        invalidate_Current_before_reset_load_write_required=True,early_EOF_return1_proves_complete=False,
        shared_source='existing CnSubjectTemplateNames',new_typed_form='CnSelectedSubjectTitle32',
        existing_publisher='SharedSubjectRosterPublication',same_held_original_order=True,owned_per_record_level_lookup_at_both_checks=True,
        native_snapshot_operational_requirement=False,
        reviewed_M2_context_bridge=dict(root_applied=True,proposal_sha256=sha(patch),agent_historical_proposal_applied=False,
            actual_same_SQLite_account_snapshot_reader_exposed=True,backend_owns_accounts_guard=True,
            constructor_or_identity_check_SQL=False,schema_or_import_added=False,
            actual_CN_plan_selected=False,actual_compose_native_login_caller=False,stored_Prepare_Authority_configured=False),
        parallel_agent_receipt='parallel-agent-deliveries.json',actual_common_rule_save_replay_issuer_configured=False,
        formal_application_hosted=False,complete_route=False)
    dump('native/title32-resource-and-shared-context-relations.json',relations)
    facts=dict(round=ROUND,previous_goal_turn_classification='progress:147 actual33/39 selected-row forms and existing ordered handoff/seals',
        completed_parallel_agent_deliveries=3,cn_selected_subject_title32_forms_added=1,cn_actual_GodLevel_records=4,
        cn_existing_ordered_roster_title_forms_added=1,cn_shared_account_snapshot_context_bridges_added=1,
        title_agent_local_primary_functions=11,title_agent_primary_metadata_bytes=9602,title_agent_exact_sites=52,
        receiver_agent_entry_sites=231,receiver_agent_new_local_sites=118,agent_evidence_counts_are_overlapping_not_coverage=True,
        new_packet_values=0,new_native_phase_source_bindings=1,new_source_owner_chains=0,new_tw_source_owner_chains=0,
        new_complete_bidirectional_routes=0,actual_common_rule_save_replay_issuer_configured=False,formal_application_hosted=False,
        actual_CN_plan_selected=False,reviewed_M2_patch_applied_by_root=True,
        whole_game_route_total=None,whole_game_completed_routes=None,whole_game_completion_percent=None,
        native_snapshot_required=False,original_native_wire_layout_changed=False,original_native_baseline_changed=False,
        build_run=False,tests_run=False,runtime_run=False,native_execution=False,Cplusplus_source_run=False,
        Windows_API_run=False,database_access=False,deployed=False,protected_contexts=protected,remaining=REMAINING)
    dump('findings.json',facts)
    lp=ROOT/books[1];ledger=json.loads(lp.read_text(encoding='utf-8'))
    if any(s['name']==NAME for s in ledger['dual_client_source_segments']):raise RuntimeError('Preserve existing ledger segment')
    ledger['dual_client_source_segments'].append(dict(name=NAME,round=ROUND,
        version_scope='pinned-cn-WORLD32-known-resource-and-shared-account-context-source-only',
        status='Exact2B title/current4 resource rows/retained-text branch and held publisher; reviewed same-account snapshot context bridge; selector4 and actual gameplay/login providers remain open',
        source_paths=SOURCES,native_c2s_by_phase={},native_s2c_by_phase={'world-connection-1':['32']},
        source_owner_chains_added=0,tw_source_owner_chains_added=0,formal_application_hosted=False,
        complete_gameplay_routes_added=0,evidence=o.relative_to(ROOT).as_posix(),remaining=REMAINING))
    ledger['dual_client_execution_plan']['latest_work_round']=ROUND
    ledger['dual_client_execution_plan']['next_source_frontier']='Actual CN login composition/providers/world reservation/common presence; current selected roster/rules/save/replay/issuer/Application;32 selector4/42CA20 caller/Current; receiver475D40; all TW/CN/web/numeric64/stack99/denominator. PHASE1.'
    lp.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (ROOT/books[0]).open('a',encoding='utf-8') as f:
        f.write('\n\n## CN WORLD32 and reviewed shared account context ('+ROUND+')\n\n'
            'Three explicitly requested agents completed disjoint title-boundary/receiver-frontier/M2 composition deliveries. '
            'Added exact2B WORLD32, four current GodLevel CP936 names, actual-row projection and same held ordered publisher. '
            'Selectors0..3 copy actual source;5..255 retain actual text; accepted4 remains UNKNOWN and is not emitted as a guessed empty string. '
            'Current invalidates before reset/load/write;42CA20 return1/early EOF is not table completeness. '
            'Applied reviewed three-file mechanical same-SQLite account snapshot reader context/owns_accounts bridge; main nullCNplan/actual providers unchanged. '
            'Receiver14/12 unchanged; qualified local231-site graph excludes one candidate only. '
            'Added one S2C WORLD binding; new opcode/owner/complete route0, whole-game denominator/percentage unknown. '
            'Full goal/PHASE1 retained; no build/test/native/API/SQL/deploy.\n')
    origins=[]
    for rel in SOURCES+books:
        value=(ROOT/rel).read_bytes();save('source/current/'+rel,value);origins.append(dict(path=rel,bytes=len(value),sha256=sha(value)))
        if rel in old:
            patch=''.join(difflib.unified_diff(old[rel].decode('utf-8-sig').splitlines(True),value.decode('utf-8-sig').splitlines(True),fromfile='before/'+rel,tofile='source/'+rel))
            if patch:save('diff/'+rel+'.diff',patch.encode('utf-8'))
    dump('source/source-origins.json',origins)
    print(json.dumps({k:facts[k] for k in ['round','completed_parallel_agent_deliveries','cn_selected_subject_title32_forms_added','cn_shared_account_snapshot_context_bridges_added','new_native_phase_source_bindings','new_complete_bidirectional_routes']}))

if __name__=='__main__':main()
