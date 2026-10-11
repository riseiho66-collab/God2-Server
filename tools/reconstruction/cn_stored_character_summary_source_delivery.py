"""Same-backend full native summary reader/provider and corrected binding; static only."""
import difflib
import hashlib
import json
from .cn_wrapper_route_frontier import ROOT

NAME='cn-common-character-summary-source-provider-01'
ROUND='20261008-cn-stored-character-summary-source'
SOURCES=['src/db/NativeCharacterSummarySnapshotRepository.h',
 'src/db/SqliteNativeCharacterSummarySnapshotRepository.h','src/db/SqliteNativeCharacterSummarySnapshotRepository.cpp',
 'src/cn/auth/SharedStoredCharacterSummarySource.h','src/cn/auth/SharedStoredCharacterSummarySource.cpp',
 'src/db/Database.h','src/db/SqliteDatabase.h','src/db/SqliteDatabase.cpp','src/db/SqliteRecoveredCharacterRepository.h',
 'src/cn/net/SharedCredentialServer.h','src/cn/net/SharedCredentialServer.cpp','src/core/Application.cpp',
 'src/cn/auth/SharedLoginComposition.h','src/cn/auth/SharedLoginComposition.cpp',
 'docs/research/cn-stored-character-summary-source-20261008.md',
 'tools/reconstruction/cn_stored_character_summary_source_delivery.py','tools/reconstruction/dual_client_route_catalog.py']
REMAINING=[
 'Actual native07/native22 producer/data and real visibility/rights Authority remain absent; schema installation/population/CAS/recovery are not performed.',
 'Main still null CN plan; actual configured factory/account40+16/role/world reservation/entry/common presence/per-session TW hooks/save/replay/issuer remain open.',
 '149 outer-login probe interpretation corrected: actualresource member+464 base8AF63C; Current/intervening writes/selector4 string and42CA20 caller remain open.',
 'Conditional receivers14/12 unchanged; next exact4AE2E0 entry through4AE367->4E0F30 requires actual ECX/handle qualification.',
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
    if len(before)!=196:raise RuntimeError('Expected196 before files')
    old={r['path']:(o/r['snapshot']).read_bytes() for r in before}
    books=['docs/PACKET_CONNECTION_GOAL_20261006.md','artifacts/integration/packet-connections-20261006/packet-route-ledger.json']
    reports={f'artifacts/integration/packet-connections-20261006/packet-progress-latest.{e}' for e in ['json','md']}
    protected=[]
    for row in before:
        if sha(old[row['path']])!=row['sha256']:raise RuntimeError('Before receipt differs')
        if row['path'] not in set(SOURCES+books)|reports:
            if (ROOT/row['path']).read_bytes()!=old[row['path']]:raise RuntimeError('Protected source differs: '+row['path'])
            protected.append(row)
    prior=(o/'retained-prior/cn-shared-login-composition-context-source-01/manifest.json').read_bytes()
    if sha(prior)!='d396811f3162285a173c258b6b1166934d7f85d2e6e3857722d820f44849e436' or not json.loads(prior)['sealed']:
        raise RuntimeError('Prior149 seal differs')
    agents=[]
    for name in ['title32-boundary','receiver-frontier','m2-source-hosting','m2-source-review']:
        folder=o/'agents'/name;raw=(folder/'findings.json').read_bytes()
        files=[dict(path=p.relative_to(folder).as_posix(),bytes=p.stat().st_size,sha256=sha(p.read_bytes()))
               for p in sorted(folder.rglob('*')) if p.is_file()]
        agents.append(dict(agent=name,findings_sha256=sha(raw),findings=json.loads(raw),files=files,
                           formal_source_modified_by_agent=False))
    seal=(o/'agents/title32-boundary/seal.json').read_bytes()
    if sha(seal)!='186c8a20626bf4a628a51e9c820e39ca93ff526731df5fcda6a584e1d90ab259':raise RuntimeError('Title agent seal differs')
    for row in json.loads(seal)['files']:
        raw=(o/'agents/title32-boundary'/row['path']).read_bytes()
        if sha(raw)!=row['sha256'] or len(raw)!=row['bytes']:raise RuntimeError('Title source receipt differs')
    dump('parallel-agent-deliveries.json',agents)
    relations=dict(version='cn',source_only=True,
        actual_shared_reader='SqliteNativeCharacterSummarySnapshotRepository',
        shared_schema_proposals=['account_native_character_summaries','account_native_character_summary_rows'],
        scope=['account','target group','target server','pinned client SHA'],
        same_connection_accounts_characters_identity=True,one_SELECT_full_header_bindings_ownership=True,
        explicit_ordered_common_ID_name_mode=True,optional_role_record_revision_origin_all_or_none=True,
        all_native_opaque_inactive_bytes_required=True,no_all_visible_or_common_slot_inference=True,
        missing_snapshot_is_absent_not_empty_success=True,
        actual_provider='SharedStoredCharacterSummarySource ->SharedCommonCharacterSummarySource::create',
        native_record_bytes=75,optional_native_role_record_bytes=25,
        real_Authority_required=True,whole_tuple_reload_around_Authority=True,
        checks=['Prepared','BeforePublish','QueueAccepted','NameSubmission'],
        existing_complete_common_root_and_projection_checks_preserved=True,
        formal_context_reader='database.native_character_summaries()',exact_Context_reader_required=True,
        composition_explicit_source='SharedLoginSources.stored_character_summaries',
        schema_registered_or_installed=False,actual_rows_imported=False,actual_native_provider_configured=False,
        actual_factory_or_Main_CN_plan_selected=False,actual_world_reservation_provider_configured=False,
        source_review_include_defect_fixed_by_root=True,source_review_historical_capture_preserved=True,
        WORLD32_actual_resource_binding=dict(outer_login_base='008AF1D8',member_offset='464',actual_resource_base='008AF63C',
            constructor_lea='0044988A',constructor_call='00449890',member_constructor='00427330',
            world_login_pointer='world+8885C4',world_resource_pointer='world+A69F20',UI_resource_pointer='UI+65364',
            setter_source='actual array cell8',setter_read='004AC8A6',setter_write='004AC8A9',
            load_chain=['00449F50','00428AE0','00428C80'],qualified_scope='proven global-login-created UI form',
            corrected_resource_one_past_PE_addresses=['00984B0A','00984B0B'],corrected_initial_PE_hex='0000',
            prior149_outer_object_probe_interpretation_superseded=True,prior149_seal_preserved=True,
            actual_Current_and_intervening_writes_qualified=False,current_selector4_string_qualified=False),
        receiver_evidence=dict(entry='004AA490',primary_tail_targets=['004D2710','004D2740'],segmented_normal_CFG_sites=149,
            path_specific_same_scene_ECX_witnesses=2,local_frontier_closed=True,receiver_caller_or_phase_qualified=False,
            next_entry='004AE2E0',next_tail='004AE367 ->004E0F30'),
        parallel_agent_receipt='parallel-agent-deliveries.json',complete_route=False,formal_application_hosted=False)
    dump('source/stored-summary-and-resource-binding-relations.json',relations)
    facts=dict(round=ROUND,previous_goal_turn_classification='progress:149 actual Context-to-compose conditional source caller/startup table evidence/seals; outer-resource interpretation explicitly corrected in150',
        completed_parallel_agents=3,completed_agent_deliveries_with_source_review=4,
        cn_stored_character_summary_readers_added=1,cn_stored_character_summary_providers_added=1,
        cn_existing_login_stored_summary_source_bindings_added=1,cn_exact_character_summary_Context_bridges_added=1,
        cn_actual_resource_member_bindings_qualified=1,prior149_resource_base_probe_corrections_added=1,
        receiver_primary_tail_edges_qualified=2,receiver_path_specific_ECX_witnesses_added=2,
        source_review_header_dependency_defects_fixed=1,native_evidence_counts_are_overlapping_not_coverage=True,
        new_packet_values=0,new_native_phase_source_bindings=0,new_source_owner_chains=0,new_tw_source_owner_chains=0,
        new_complete_bidirectional_routes=0,actual_native07_or22_rows_imported=False,actual_character_summary_Authority_configured=False,
        actual_native_provider_configured=False,actual_CN_plan_selected=False,formal_application_hosted=False,
        schema_registered_or_installed=False,actual_world_reservation_provider_configured=False,
        whole_game_route_total=None,whole_game_completed_routes=None,whole_game_completion_percent=None,
        original_native_wire_layout_changed=False,original_native_baseline_changed=False,
        build_run=False,tests_run=False,runtime_run=False,native_execution=False,Cplusplus_source_run=False,
        Windows_API_run=False,database_access=False,deployed=False,protected_contexts=protected,remaining=REMAINING)
    dump('findings.json',facts)
    lp=ROOT/books[1];ledger=json.loads(lp.read_text(encoding='utf-8'))
    if any(s['name']==NAME for s in ledger['dual_client_source_segments']):raise RuntimeError('Preserve ledger segment')
    ledger['dual_client_source_segments'].append(dict(name=NAME,round=ROUND,
        version_scope='pinned-cn-account-native07-stored-source-and-current-shared-authority-only',
        status='Same-backend complete snapshot reader/explicit mapping/native role origin/real Authority read-through ->existing common07 source and actual composition; schema/data/actual Authority/Main configuration still absent; resource base149 correction explicit',
        source_paths=SOURCES,native_c2s_by_phase={},native_s2c_by_phase={},
        source_owner_chains_added=0,tw_source_owner_chains_added=0,formal_application_hosted=False,
        complete_gameplay_routes_added=0,evidence=o.relative_to(ROOT).as_posix(),remaining=REMAINING))
    ledger['dual_client_execution_plan']['latest_work_round']=ROUND
    ledger['dual_client_execution_plan']['next_source_frontier']='Actual native07/22 producer/origin/visibility Authority/schema CAS recovery; factory/account40+16/world reservation/common presence/save/replay/issuer;32 Current writes/string4/42CA20;receiver4AE2E0->4E0F30;full TW/CN/web/numeric64/stack99/denominator. PHASE1.'
    lp.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (ROOT/books[0]).open('a',encoding='utf-8') as f:
        f.write('\n\n## CN actual stored character summary source ('+ROUND+')\n\n'
            'Implemented same SQLite/accounts/characters complete version-keyed summary reader, explicit ordinal/commonID/nameMode/optional native22 revision-origin, '
            'single SELECT ownership/coherence, actual full75/native25 adapter and whole tuple reload around mandatory real Authority. '
            'Connected same Context reader into existing common summary/native login; schema/data/provider/Main activation not performed. '
            'Corrected149 outer-login probe: member+464 resource8AF63C, actual UI65364 binding/load lineage qualified; Current/writes/string4 still open and old seal preserved. '
            'Three agents plus readonly source review retained; root fixed missing CnCharacterSummary include. '
            'Receiver two primary tails/local149-site graph/path-specific ECX qualified, no receiver caller/phase. '
            'New packet/phase/owner/complete route0; full goal/PHASE1 retained; no build/test/native/API/SQL/deploy.\n')
    origins=[]
    for rel in SOURCES+books:
        raw=(ROOT/rel).read_bytes();save('source/current/'+rel,raw);origins.append(dict(path=rel,bytes=len(raw),sha256=sha(raw)))
        if rel in old:
            patch=''.join(difflib.unified_diff(old[rel].decode('utf-8-sig').splitlines(True),raw.decode('utf-8-sig').splitlines(True),fromfile='before/'+rel,tofile='source/'+rel))
            if patch:save('diff/'+rel+'.diff',patch.encode('utf-8'))
    dump('source/source-origins.json',origins)
    print(json.dumps({k:facts[k] for k in ['round','completed_parallel_agents','cn_stored_character_summary_readers_added','cn_stored_character_summary_providers_added','prior149_resource_base_probe_corrections_added','new_complete_bidirectional_routes']}))

if __name__=='__main__':main()
