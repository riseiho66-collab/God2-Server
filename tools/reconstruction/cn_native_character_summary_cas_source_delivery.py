"""Retain complete issuer tuple atomic writer and bounded lifetime evidence, static only."""
import difflib
import hashlib
import json
from .cn_wrapper_route_frontier import ROOT

NAME='cn-native-character-summary-cas-source-01'
ROUND='20261008-cn-native-character-summary-cas-source'
SOURCES=['src/db/SqliteNativeCharacterSummarySnapshotRepository.h',
 'src/db/SqliteNativeCharacterSummarySnapshotRepository.cpp',
 'src/db/SqliteDatabase.h','src/db/SqliteDatabase.cpp',
 'src/cn/auth/CnNativeCharacterSummaryCommit.h','src/cn/auth/CnNativeCharacterSummaryCommit.cpp',
 'src/cn/assets/CnSubjectTemplateNames.h',
 'docs/research/cn-native-character-summary-cas-source-20261008.md',
 'tools/reconstruction/cn_native_character_summary_cas_source_delivery.py',
 'tools/reconstruction/dual_client_route_catalog.py']
REMAINING=[
 'Actual native07/22 issuer/data/visibility/rights/revision and actual commit caller remain unconfigured; schema registration/installation/population/recovery not performed.',
 'Owned character removal cascades mappings but leaves header/count; exact issuer replacement/invalidation within actual mutation transaction remains open.',
 'Snapshot CAS does not revoke retained issued world offers; actual issuer/admission revision and invalidation remain open.',
 'Main CN plan/source factory/account40+16/world reservation/presence/per-session TW/save/replay/hosting still open.',
 'Resource lifetime lineage is bounded; Current bytes/firstNUL/string4/intervening writes and42CA20 caller remain unknown.',
 'Receiver upstream9 helper preservation and actual network owner/phase remain open; next4C4060->4C409C->4C4880 input/ECX.',
 'Complete TW/CN/PC/web/WSS/numeric64/stack99/full-game denominator and later comprehensive testing/repair/recovery release remain open.']

def sha(raw):return hashlib.sha256(raw).hexdigest()

def main():
    base=ROOT/'artifacts/integration/packet-connections-20261006';out=base/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():raise RuntimeError('Fresh before required')
    def save(rel,raw):
        path=out/rel;path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('xb') as stream:stream.write(raw)
    def dump(rel,value):save(rel,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    before=json.loads((out/'before-manifest.json').read_text(encoding='utf-8'))
    if len(before)!=203:raise RuntimeError('Expected203 before files')
    old={row['path']:(out/row['snapshot']).read_bytes() for row in before}
    books=['docs/PACKET_CONNECTION_GOAL_20261006.md','artifacts/integration/packet-connections-20261006/packet-route-ledger.json']
    reports={f'artifacts/integration/packet-connections-20261006/packet-progress-latest.{ext}' for ext in ['json','md']}
    protected=[]
    for row in before:
        if sha(old[row['path']])!=row['sha256']:raise RuntimeError('Before receipt differs')
        if row['path'] not in set(SOURCES+books)|reports:
            if (ROOT/row['path']).read_bytes()!=old[row['path']]:raise RuntimeError('Protected source differs: '+row['path'])
            protected.append(row)
    prior=(out/'retained-prior/cn-common-character-summary-source-provider-01/manifest.json').read_bytes()
    if sha(prior)!='31ba81573d7c875c0ff029227c67bc8f53324e9fc7007b69420c02c30fef47de' or not json.loads(prior)['sealed']:
        raise RuntimeError('Prior150 seal differs')
    agents=[]
    for name in ['m2-source-hosting','receiver-frontier','title32-boundary','m2-source-review','receiver-handoff','title32-handoff']:
        folder=out/'agents'/name;raw=(folder/'findings.json').read_bytes()
        files=[dict(path=path.relative_to(folder).as_posix(),bytes=path.stat().st_size,sha256=sha(path.read_bytes()))
               for path in sorted(folder.rglob('*')) if path.is_file()]
        agents.append(dict(agent=name,findings_sha256=sha(raw),findings=json.loads(raw),files=files,
                           formal_source_modified_by_agent=False))
    seal=(out/'agents/title32-boundary/seal.json').read_bytes()
    if sha(seal)!='2173092be8894763bd5cfe348066f31a85bd86db461d4dc6ab90460588c16a12':raise RuntimeError('Title151 seal differs')
    for row in json.loads(seal)['files']:
        raw=(out/'agents/title32-boundary'/row['path']).read_bytes()
        if sha(raw)!=row['sha256'] or len(raw)!=row['bytes']:raise RuntimeError('Title source receipt differs')
    dump('parallel-agent-deliveries.json',agents)
    relations=dict(version='cn',source_only=True,
        actual_atomic_writer='SqliteNativeCharacterSummarySnapshotRepository::replace_from_issuer',
        actual_same_database_getter='SqliteDatabase::native_character_summary_writer',
        actual_typed_plan='CnNativeCharacterSummaryCommit::Plan::from_actual_issuer',
        actual_commit_entry='CnNativeCharacterSummaryCommit::commit_actual_source ->same_database_writer.replace_from_issuer',
        scope=['account','group','server','pinned client SHA'],
        full_expected_next_tuple_CAS=True,explicit_issuer_revision_origin_required=True,no_revision_generated=True,
        same_SQLite_accounts_mutable_characters_identity=True,owner_thread_and_reentry_guard=True,
        own_BEGIN_IMMEDIATE_required=True,outer_transaction_rejected=True,foreign_keys_required=True,
        issuer_checks=['Prepared','BeforeWrite','BeforeCommit'],whole_tuple_and_complete_common_roots_before_after_callbacks=True,
        trusted_issuer_no_SQL_no_yield_no_eventpump_required=True,earlier_source_preparation_revisions_checked_by_actual_issuer=True,
        BeforeCommit_observes_staged_next=True,header_ordered_mapping_and_optional_role_atomic=True,
        exact_SQL_change_cardinalities=True,missing_roles_all_four_SQL_NULL=True,
        owned_complete_readback_before_COMMIT=True,no_callback_or_reload_after_COMMIT=True,
        CN_Plan_native_record_bytes=75,CN_Plan_optional_native_role_record_bytes=25,
        explicit_ordered_common_IDs_name_modes_native_slots=True,no_COMMON_slot_or_CUSTOM_level_inference=True,
        actual_issuer_or_commit_caller_selected=False,actual_native_data_installed=False,schema_registered_or_installed=False,
        actual_source_factory_or_Main_CN_plan_selected=False,actual_world_reservation_provider_configured=False,
        removal_header_refresh_or_invalidation_connected=False,issued_world_offer_revision_invalidation_connected=False,
        WORLD32_resource_lifetime=dict(destructor_chain=['007E9D50','00449940','member+464','00427350','00430340/00423020'],
            invalidate_Current_before_destruction=True,native_process_memory_required_for_own_server_catalog=False,
            current_selector4_string_qualified=False,all_intervening_writes_excluded=False,bounded_target_search0_not_global_unreachable=True),
        receiver_evidence=dict(entry='004AE2E0',tail_site='004AE367',primary_tail='004E0F30',segmented_normal_CFG_sites=51,
            last_helper_negative_handle_ECX_suffix_relations=1,actual_S='ESI at004AE35D',helper='0052A420',handle='S+1C8524',
            original_entry_ECX_across_upstream9_helpers_qualified=False,actual_network_owner_or_phase_qualified=False,
            next_entry='004C4060',next_call='004C409C ->004C4880'),
        parallel_agent_receipt='parallel-agent-deliveries.json',complete_route=False,formal_application_hosted=False)
    dump('source/native-summary-cas-and-lifetime-relations.json',relations)
    facts=dict(round=ROUND,previous_goal_turn_classification='progress:150 same-backend full stored summary reader/provider and corrected resource member binding; no deployment',
        completed_parallel_agents=3,completed_agent_deliveries_with_source_review_and_handoffs=6,
        cn_native_character_summary_atomic_writers_added=1,cn_native_character_summary_typed_commit_plans_added=1,
        cn_same_database_summary_commit_entries_added=1,cn_resource_destruction_Current_lineages_added=1,
        receiver_primary_tail_edges_qualified=1,receiver_last_helper_ECX_suffix_relations_added=1,
        receiver_segmented_normal_CFG_sites=51,source_review_definite_new_implementation_defects_found=0,
        native_evidence_counts_are_overlapping_not_coverage=True,
        new_packet_values=0,new_native_phase_source_bindings=0,new_source_owner_chains=0,new_tw_source_owner_chains=0,
        new_complete_bidirectional_routes=0,actual_native07_or22_rows_imported=False,
        actual_issuer_or_commit_caller_selected=False,actual_character_summary_Authority_configured=False,
        actual_native_provider_configured=False,actual_CN_plan_selected=False,formal_application_hosted=False,
        schema_registered_or_installed=False,removal_header_invalidation_connected=False,issued_world_offer_invalidation_connected=False,
        whole_game_route_total=None,whole_game_completed_routes=None,whole_game_completion_percent=None,
        original_native_wire_layout_changed=False,original_native_baseline_changed=False,levels_changed=False,
        build_run=False,tests_run=False,runtime_run=False,native_execution=False,Cplusplus_source_run=False,
        Windows_API_run=False,database_access=False,deployed=False,protected_contexts=protected,remaining=REMAINING)
    dump('findings.json',facts)
    ledger_path=ROOT/books[1];ledger=json.loads(ledger_path.read_text(encoding='utf-8'))
    if any(segment['name']==NAME for segment in ledger['dual_client_source_segments']):raise RuntimeError('Preserve existing segment')
    ledger['cn_native_character_summary_cas_source']=dict(facts,evidence=out.relative_to(ROOT).as_posix())
    ledger['dual_client_source_segments'].append(dict(name=NAME,round=ROUND,
        version_scope='pinned-cn-native07-22-real-issuer-atomic-storage-and-bounded-resource-lifetime-source-only',
        status='Same-backend owned transaction/fulltuple CAS/native-shaped actual issuer commit source; actual schema/data/issuer/caller/removal/worldoffer/hosting remain open',
        source_paths=SOURCES,native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,
        tw_source_owner_chains_added=0,formal_application_hosted=False,complete_gameplay_routes_added=0,
        evidence=out.relative_to(ROOT).as_posix(),remaining=REMAINING))
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next_source_frontier']='Actual issuer/native07+22/source visibility/revision and commit caller; removal fullheader invalidation and worldoffer revision; real factory/account40+16/world/presence/save/replay;Current string4/42CA20;receiver4C4060->4C4880;full TW/CN/web/numeric64/stack99/denominator. PHASE1 only.'
    ledger_path.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (ROOT/books[0]).open('a',encoding='utf-8') as stream:
        stream.write('\n\n## CN actual issuer summary atomic CAS source ('+ROUND+')\n\n'
            'Added same SQLite/account/mutable-character writer with full expected/next tuple CAS, own transaction, owner/reentry/FK checks, '
            'complete common roots and tuple reload around mandatory actual issuer Prepared/BeforeWrite/BeforeCommit; '
            'all header/mapping/optional-role writes atomic, four NULL roles, exact cardinalities and owned pre-COMMIT readback. '
            'Added strict pinned CN75/optional25 move-only Plan and actual same-database commit entry; actual issuer/caller/schema/data/Main remain absent. '
            'Character deletion stale header and issued worldoffer revision invalidation explicitly remain open. '
            'Native destruction member+464 lineage/Current invalidation and receiver one tail/negative-handle ECX suffix retained; upstream9 helper preservation unknown. '
            'Three owner-requested agents plus readonly review/handoffs retained; new packet/phase/owner/fullroute0, whole-game percent null. '
            'No build/test/native/C++/API/DB/deploy; full TW/CN/web/numeric64/stack99 goal stays active. See research/cn-native-character-summary-cas-source-20261008.md.\n')
    origins=[]
    for rel in SOURCES+books:
        raw=(ROOT/rel).read_bytes();save('source/current/'+rel,raw)
        origins.append(dict(path=rel,bytes=len(raw),sha256=sha(raw)))
        if rel in old:
            patch=''.join(difflib.unified_diff(old[rel].decode('utf-8-sig').splitlines(True),raw.decode('utf-8-sig').splitlines(True),fromfile='before/'+rel,tofile='source/'+rel))
            if patch:save('diff/'+rel+'.diff',patch.encode('utf-8'))
    dump('source/source-origins.json',origins)
    print(json.dumps({key:facts[key] for key in ['round','completed_parallel_agents','cn_native_character_summary_atomic_writers_added',
        'cn_native_character_summary_typed_commit_plans_added','cn_same_database_summary_commit_entries_added','new_complete_bidirectional_routes']}))

if __name__=='__main__':main()
