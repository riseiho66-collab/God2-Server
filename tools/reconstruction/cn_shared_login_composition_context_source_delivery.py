"""Retain reviewed native login factory integration and parallel evidence; static only."""
import difflib
import hashlib
import json
from pathlib import Path
from .cn_wrapper_route_frontier import ROOT

NAME='cn-shared-login-composition-context-source-01'
ROUND='20261008-cn-shared-login-composition-context-source'
SOURCES=['src/cn/auth/SharedLoginComposition.h','src/cn/auth/SharedLoginComposition.cpp',
 'docs/research/cn-shared-login-composition-context-source-20261008.md',
 'tools/reconstruction/cn_shared_login_composition_context_source_delivery.py','tools/reconstruction/dual_client_route_catalog.py']
REMAINING=[
 'Formal main still chooses null CN plan; actual configured source factory and full stored Prepare/Authority/native40+16/world providers remain absent.',
 'Actual role22/world reservation/entry/common presence/per-session TW hooks/save/durable replay/committed issuer remain open.',
 'WORLD32 constructor startup lineage is qualified; actualresource binding/intervening writes/selector4 current string and42CA20 caller remain open.',
 'Conditional receivers14/12 unchanged; next exact004AA490 entry tails to004D2740/004D2710 require actual ECX qualification.',
 'Full TW/CN/PC/web/WSS/numeric64/stack99/whole-game denominator and later comprehensive tests/repair/recovery release remain open.']

def sha(raw):return hashlib.sha256(raw).hexdigest()

def main():
    b=ROOT/'artifacts/integration/packet-connections-20261006';o=b/NAME
    if not (o/'before-manifest.json').exists() or (o/'findings.json').exists():raise RuntimeError('Fresh before required')
    def save(rel,raw):
        p=o/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as f:f.write(raw)
    def dump(rel,value):save(rel,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    before=json.loads((o/'before-manifest.json').read_text(encoding='utf-8'))
    if len(before)!=193:raise RuntimeError('Expected193 before files')
    old={r['path']:(o/r['snapshot']).read_bytes() for r in before}
    books=['docs/PACKET_CONNECTION_GOAL_20261006.md','artifacts/integration/packet-connections-20261006/packet-route-ledger.json']
    reports={f'artifacts/integration/packet-connections-20261006/packet-progress-latest.{e}' for e in ['json','md']}
    protected=[]
    for row in before:
        if sha(old[row['path']])!=row['sha256']:raise RuntimeError('Before receipt differs')
        if row['path'] not in set(SOURCES+books)|reports:
            if (ROOT/row['path']).read_bytes()!=old[row['path']]:raise RuntimeError('Protected source differs: '+row['path'])
            protected.append(row)
    prior=(o/'retained-prior/cn-selected-subject-title32-source-01/manifest.json').read_bytes()
    if sha(prior)!='630cff6f535046fd323e5a783108aa28f15f34d148f15f9493f93bf30551d6da' or not json.loads(prior)['sealed']:
        raise RuntimeError('Prior148 seal differs')
    agents=[]
    for name in ['title32-boundary','receiver-frontier','m2-source-hosting']:
        folder=o/'agents'/name;raw=(folder/'findings.json').read_bytes()
        files=[dict(path=p.relative_to(folder).as_posix(),bytes=p.stat().st_size,sha256=sha(p.read_bytes()))
               for p in sorted(folder.rglob('*')) if p.is_file()]
        agents.append(dict(agent=name,findings_sha256=sha(raw),findings=json.loads(raw),files=files,
                           formal_source_modified_by_agent=False))
    seal=(o/'agents/title32-boundary/seal.json').read_bytes()
    if sha(seal)!='7faf7f979d6b3fe12fea552c223166658d2cac121db21c4488956e7c8051b065':raise RuntimeError('Title agent seal differs')
    for row in json.loads(seal)['files']:
        value=(o/'agents/title32-boundary'/row['path']).read_bytes()
        if sha(value)!=row['sha256'] or len(value)!=row['bytes']:raise RuntimeError('Title source receipt differs')
    proposal=(o/'agents/m2-source-hosting/login-composition-factory.proposed.patch').read_bytes()
    dump('parallel-agent-deliveries.json',agents)
    relations=dict(version='cn',source_only=True,
        actual_formal_host='src/cn/net/SharedCredentialServer.cpp:plan.controllers(actual Context)',
        typed_adapter='make_native_login_controller_factory',actual_adapter_call='compose_native_login(context,owned sources)',
        source_factory_requires_actual_Context=True,no_context_or_endpoint_reference_retained_by_adapter=True,
        actual_sources_required=['seed or explicit operational seed policy','one actual account source',
            'world native offer/preparation','selected pinned client groups','actual stored Prepare/Authority when selected',
            'actual role metadata and authority for common summaries when selected'],
        stored_reader_exact_Context_identity=True,same_account_backend_and_existing_current_checks_preserved=True,
        actual_bound_listener_registry_retained_by_composition=True,
        root_applied_reviewed_proposal=True,proposal_sha256=sha(proposal),agent_proposal_remains_historical=True,
        actual_Main_CN_plan_selected=False,actual_source_factory_configured=False,
        actual_native40_16_provider_configured=False,actual_world_reservation_provider_configured=False,
        WORLD32_startup_constructor=dict(table_cell='007EBF50',table_root='00402D40',
            initializer='__initterm',constructor_call_site='00402D45',constructor='00449880',global_ECX='008AF1D8',
            initial_PE_D54CE_CF_hex='0000',actual_resource_binding_qualified=False,intervening_writes_qualified=False,
            current_selector4_string_qualified=False,independent42CA20_caller_qualified=False),
        receiver_local_frontier=dict(entry='00475D40',truncated_instruction='00475F5B RET4',
            exact_metadata_tail_byte_added=1,completed_entry_sites=181,local_frontier_closed=True,
            same_owner_helper='004748D0',helper_entry_sites=36,actual_receiver_caller_qualified=False,
            next_entry='004AA490',qualified_tail_targets=['004D2740','004D2710']),
        parallel_agent_receipt='parallel-agent-deliveries.json',complete_route=False,formal_application_hosted=False)
    dump('source/login-controller-factory-relations.json',relations)
    facts=dict(round=ROUND,previous_goal_turn_classification='progress:148 WORLD32 known resource/ordered source and reviewed same-account snapshot Context bridge/seals',
        completed_parallel_agent_deliveries=3,cn_login_controller_composition_factories_added=1,
        cn_composition_stored_reader_identity_bindings_added=1,
        receiver_metadata_tail_bytes_added=1,receiver_local_frontiers_closed=1,
        title32_startup_constructor_table_roots_added=1,title32_current_selector4_string_qualified=False,
        native_evidence_counts_are_overlapping_not_coverage=True,
        new_packet_values=0,new_native_phase_source_bindings=0,new_source_owner_chains=0,new_tw_source_owner_chains=0,
        new_complete_bidirectional_routes=0,actual_source_factory_configured=False,actual_CN_plan_selected=False,
        formal_application_hosted=False,actual_native40_16_provider_configured=False,actual_world_reservation_provider_configured=False,
        whole_game_route_total=None,whole_game_completed_routes=None,whole_game_completion_percent=None,
        original_native_wire_layout_changed=False,original_native_baseline_changed=False,
        build_run=False,tests_run=False,runtime_run=False,native_execution=False,Cplusplus_source_run=False,
        Windows_API_run=False,database_access=False,deployed=False,protected_contexts=protected,remaining=REMAINING)
    dump('findings.json',facts)
    lp=ROOT/books[1];ledger=json.loads(lp.read_text(encoding='utf-8'))
    if any(s['name']==NAME for s in ledger['dual_client_source_segments']):raise RuntimeError('Preserve ledger segment')
    ledger['dual_client_source_segments'].append(dict(name=NAME,round=ROUND,
        version_scope='pinned-cn-M2-native-login-controller-context-source-only',
        status='Typed actual Context to native composition caller and stored exact reader binding; no configured Main plan/native profile/world provider; parallel startup/decode frontiers retained',
        source_paths=SOURCES,native_c2s_by_phase={},native_s2c_by_phase={},
        source_owner_chains_added=0,tw_source_owner_chains_added=0,formal_application_hosted=False,
        complete_gameplay_routes_added=0,evidence=o.relative_to(ROOT).as_posix(),remaining=REMAINING))
    ledger['dual_client_execution_plan']['latest_work_round']=ROUND
    ledger['dual_client_execution_plan']['next_source_frontier']='Actual Context source factory/native profile Prepare Authority/role/world reservation/common presence;32 actualresource binding/intervening writes/42CA20 caller; receiver004AA490 tail ECX; full TW/CN/web/numeric64/stack99/denominator. PHASE1.'
    lp.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (ROOT/books[0]).open('a',encoding='utf-8') as f:
        f.write('\n\n## CN native login controller Context adapter ('+ROUND+')\n\n'
            'Reviewed/applied typed real Context source factory ->existing plan.controllers ->compose_native_login caller. '
            'Stored profile explicitly binds exact Context snapshot reader; all real Prepare/Authority/native profile/world/client groups/seed source requirements preserved. '
            'Main still null CN plan and actual suppliers absent: no activation/full-route claim. '
            'Three agents retained startup table-rooted402D40 ctor lineage and initial PE bytes (actualresource/writes/string4 still open), '
            'receiver475D40 entry metadata-truncated RET4 closed with exactly one PE byte, and reviewed composition source patch. '
            'New packet/phase/owner/complete route0; full goal/PHASE1 retained; no build/test/native/API/SQL/deploy.\n')
    origins=[]
    for rel in SOURCES+books:
        value=(ROOT/rel).read_bytes();save('source/current/'+rel,value);origins.append(dict(path=rel,bytes=len(value),sha256=sha(value)))
        if rel in old:
            patch=''.join(difflib.unified_diff(old[rel].decode('utf-8-sig').splitlines(True),value.decode('utf-8-sig').splitlines(True),fromfile='before/'+rel,tofile='source/'+rel))
            if patch:save('diff/'+rel+'.diff',patch.encode('utf-8'))
    dump('source/source-origins.json',origins)
    print(json.dumps({k:facts[k] for k in ['round','completed_parallel_agent_deliveries','cn_login_controller_composition_factories_added','new_native_phase_source_bindings','new_complete_bidirectional_routes']}))

if __name__=='__main__':main()
