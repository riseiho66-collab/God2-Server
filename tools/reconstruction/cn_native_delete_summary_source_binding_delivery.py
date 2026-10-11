"""Retain actual conditional native deletion ->same-backend summary invalidation, static only."""
import difflib
import hashlib
import json
from .cn_wrapper_route_frontier import ROOT

NAME='cn-native-delete-summary-source-binding-01'
ROUND='20261008-cn-native-delete-summary-source-binding'
SOURCES=['src/db/SqliteNativeCharacterSummarySnapshotRepository.h',
 'src/db/SqliteNativeSummaryRemovalInvalidation.cpp',
 'src/cn/auth/SharedCharacterDeleteOperation.h','src/cn/auth/SharedCharacterDeleteOperation.cpp',
 'src/cn/auth/SharedLoginComposition.h','src/cn/auth/SharedLoginComposition.cpp',
 'src/cn/assets/CnSubjectTemplateNames.h',
 'docs/research/cn-native-delete-summary-source-binding-20261008.md',
 'tools/reconstruction/cn_native_delete_summary_source_binding_delivery.py',
 'tools/reconstruction/dual_client_route_catalog.py']
REMAINING=[
 'Actual native deletion rule/reply and complete-account summary invalidation issuers, source factory/Main CN plan/schema/native07+22 data remain unconfigured; no hosting.',
 'Existing transport send_batch/completion construction and checks remain post-removal COMMIT and can fail; durable reply/replay/disconnect recovery/1E continuation remain open.',
 'General summary CAS and whole-account issued worldoffer refresh/revocation/historical malformed repair remain open; new path applies existing affected-character plan only.',
 'Actual account40+16/world reservation/bootstrap/presence/per-session TW/save/replay/hosting and full TW/CN/PC/web/WSS/numeric64/stack99/denominator remain open.',
 'WORLD68 key/output WORD and qualified GUI negative handle bridge do not establish common item mapping/rules/provider or other GUI effects; next4501BF->407D70 nested context.',
 'GodLevel scratch count ABI is not destination capacity; Current string4/firstNUL/42CA20 caller/selected-row capacity/owner content-mutation-lifetime receipts remain unknown.',
 'All source routes first; later complete builds/comprehensive testing/repairs/recovery/playable release still required.']

def sha(raw):return hashlib.sha256(raw).hexdigest()

def main():
    base=ROOT/'artifacts/integration/packet-connections-20261006';out=base/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():raise RuntimeError('Fresh before required')
    def save(rel,raw):
        path=out/rel;path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('xb') as stream:stream.write(raw)
    def dump(rel,value):save(rel,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    before=json.loads((out/'before-manifest.json').read_text(encoding='utf-8'))
    if len(before)!=215:raise RuntimeError('Expected215 before files')
    old={row['path']:(out/row['snapshot']).read_bytes() for row in before}
    books=['docs/PACKET_CONNECTION_GOAL_20261006.md','artifacts/integration/packet-connections-20261006/packet-route-ledger.json']
    reports={f'artifacts/integration/packet-connections-20261006/packet-progress-latest.{ext}' for ext in ['json','md']}
    protected=[]
    for row in before:
        if sha(old[row['path']])!=row['sha256']:raise RuntimeError('Before receipt differs')
        if row['path'] not in set(SOURCES+books)|reports:
            if (ROOT/row['path']).read_bytes()!=old[row['path']]:raise RuntimeError('Protected source differs: '+row['path'])
            protected.append(row)
    prior=(out/'retained-prior/cn-native-summary-removal-invalidation-source-01/manifest.json').read_bytes()
    if sha(prior)!='c8e8b493de6d55b119cc2d7e2859f6374120934bac3074f41793d78fa203db00' or not json.loads(prior)['sealed']:
        raise RuntimeError('Prior152 seal differs')
    agents=[]
    for name in ['m2-source-hosting','receiver-frontier','title32-boundary','m2-source-review']:
        folder=out/'agents'/name;entry='design-review.json' if name=='m2-source-hosting' else 'findings.json'
        raw=(folder/entry).read_bytes()
        files=[dict(path=path.relative_to(folder).as_posix(),bytes=path.stat().st_size,sha256=sha(path.read_bytes()))
               for path in sorted(folder.rglob('*')) if path.is_file()]
        agents.append(dict(agent=name,entry=entry,findings_sha256=sha(raw),findings=json.loads(raw),files=files,
                           formal_source_modified_by_agent=False))
    seal=(out/'agents/title32-boundary/seal.json').read_bytes()
    if sha(seal)!='753e153632f6568cf5eaef08491d0cfdef2b6ad9f31ec456f154b59729be58a4':raise RuntimeError('Title153 seal differs')
    for row in json.loads(seal)['files']:
        raw=(out/'agents/title32-boundary'/row['path']).read_bytes()
        if sha(raw)!=row['sha256'] or len(raw)!=row['bytes']:raise RuntimeError('Title source receipt differs')
    dump('parallel-agent-deliveries.json',agents)
    relations=dict(source_only=True,version_scope='pinned-cn-native19-to-existing-common-removal/native02 conditional source',
        actual_observation_reader='SqliteNativeCharacterSummarySnapshotRepository::read_removal_observation',
        same_account_mutable_characters_SQLite_identity=True,own_BEGIN_IMMEDIATE_for_consistent_observation=True,
        full_operation_owner_writing_lease=True,observation_complete_summaries_and_roots_owned_before_read_COMMIT=True,
        read_COMMIT_is_not_character_removal=True,no_post_read_COMMIT_callbacks_or_result_allocation=True,
        owned_actual_summary_decision='SharedCharacterDeleteOperation::SummaryDecision',
        exact_scope_Attempt_and_full_common_row_and_observation_match=True,
        complete_account_destination_build_record_mapping_role_origin_and_common_roots=True,
        selected_source='Sources.native_summary_removal {actual typed summary repository, mandatory actual Prepare}',
        actual_native_success_branch='native Decision status0 ->actual observation ->actual Prepare ->exact decision ->commit_with_native_summaries',
        nonzero_reply_skips_summary_read_prepare_and_invalidation=True,selected_source_failure_never_falls_back_to_legacy=True,
        actual_commit_caller='SharedCharacterDeleteOperation::start ->SharedCharacterRemoval::commit_with_native_summaries ->same-repository erase_owned_snapshot_with_native_summaries',
        BeforeErase_and_BeforeCommit_require_both_native_and_summary_actual_Current=True,
        BeforeCommit_uses_retained_original_roots_for_authorization_and_actual_staged_minus_ID_in_writer=True,
        queue_checks=['BeforeQueue','AfterQueue'],queue_summary_Current_requires_actual_committed_removal=True,
        queue_does_not_require_old_raw_summary_Current=True,existing_native_decision_selection_root_presence_gates_preserved=True,
        exact_Context_summary_accounts_characters_identity_guard=True,generic_SQLite_cast_or_second_DB=False,
        SummaryDecision_and_expected_inventory_owned_before_removal_SQL=True,
        all_transport_allocations_before_removal_COMMIT=False,existing_send_batch_completion_and_checks_remain_after_removal_COMMIT=True,
        durable_reply_or_replay_or_disconnect_recovery_connected=False,
        legacy_unselected_branch_and_frozen_TW_selection_preserved=True,
        actual_new_issuer_factory_Main_plan_or_schema_selected=False,actual_native_rows_imported=False,
        general_CAS_or_whole_account_worldoffer_invalidation_connected=False,
        WORLD68_resource_output_WORD_context=dict(target_helpers=['004C5320','004C5440'],new_primary_bytes=144,new_entry_sites=44,
            actual_first_UI_ECX_qualified=True,key='unsigned LOWWORD <35000',resource='UI+65364',
            null_lookup_not_absent_source=True,caller_LOWWORD_output_distinct_from_saved_index=True,
            second_same_UI_bridge='00450170 negative signed GUI handle path',bridge_bytes=89,bridge_sites=29,
            other_GUI_callbacks_preservation_qualified=False,threshold1_or30_not_stack99=True,
            existing_WORLD68_phase_counted_as_new=False,common_item_authority_qualified=False,next='004501BF ->00407D70'),
        WORLD32_typed_copy_qualification=dict(parser_CRT='0075AC90',scratch_count_limit=379,bank_copy='004231B0',
            selected_row_copy='004D5A10',source_columns_and_destination_capacity_separate=True,
            parser_count_does_not_qualify_bank94_or_selected_row_capacity=True,current_selector4_string_qualified=False,
            independent42CA20_caller_qualified=False),
        complete_route=False,formal_application_hosted=False)
    dump('source/native-delete-summary-binding-and-copy-relations.json',relations)
    facts=dict(round=ROUND,previous_goal_turn_classification='progress:152 complete-account snapshot inventory and atomic invalidation with common selected-root removal and concrete coordinator; no native source selection',
        completed_parallel_agents=3,completed_agent_deliveries_with_source_review=4,
        same_backend_owned_removal_observation_readers_added=1,owned_scope_bound_summary_removal_decisions_added=1,
        existing_native_delete_summary_storage_bindings_added=1,exact_login_Context_summary_removal_identity_guards_added=1,
        configured_native_delete_summary_aware_branch_implemented=True,actual_summary_removal_source_configured=False,
        WORLD68_resource_output_WORD_helpers_qualified=2,WORLD68_negative_GUI_handle_same_owner_bridges_qualified=1,
        GodLevel_typed_copy_boundary_lineages_added=1,source_review_definite_new_implementation_errors_found=0,
        post_removal_COMMIT_transport_failure_recovery_completed=False,
        new_packet_values=0,new_native_phase_source_bindings=0,new_source_owner_chains=0,new_tw_source_owner_chains=0,
        new_complete_bidirectional_routes=0,schema_registered_or_installed=False,actual_native_data_imported=False,
        actual_issuer_selected=False,actual_CN_plan_selected=False,formal_application_hosted=False,
        whole_game_route_total=None,whole_game_completed_routes=None,whole_game_completion_percent=None,
        original_native_wire_layout_changed=False,original_native_baseline_changed=False,levels_changed=False,
        build_run=False,tests_run=False,runtime_run=False,native_execution=False,Cplusplus_source_run=False,
        Windows_API_run=False,database_access=False,deployed=False,protected_contexts=protected,remaining=REMAINING)
    dump('findings.json',facts)
    path=ROOT/books[1];ledger=json.loads(path.read_text(encoding='utf-8'))
    if any(segment['name']==NAME for segment in ledger['dual_client_source_segments']):raise RuntimeError('Preserve existing segment')
    ledger['cn_native_delete_summary_source_binding']=dict(facts,evidence=out.relative_to(ROOT).as_posix())
    ledger['dual_client_source_segments'].append(dict(name=NAME,round=ROUND,
        version_scope='pinned-cn-native19/02-explicit-complete-account-summary-aware-common-removal-source-only',
        status='Actual existing native deletion selects configured same-backend observation/owned exact decision/all-scope invalidation caller; issuer/config/schema/Main/recovery/hosting absent',
        source_paths=SOURCES,native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,
        tw_source_owner_chains_added=0,formal_application_hosted=False,complete_gameplay_routes_added=0,
        evidence=out.relative_to(ROOT).as_posix(),remaining=REMAINING))
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next_source_frontier']='Actual deletion/native02/summary-wide issuer config and durable receipt/replay/disconnect recovery; general worldoffer/CAS; native07+22/Main/sourcefactory/account40+16/world/presence;WORLD68 GUI4501BF->407D70;GodLevel actualselectedrow capacity/42CA20/string4;full TW/CN/web/numeric64/stack99/denominator. PHASE1.'
    path.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (ROOT/books[0]).open('a',encoding='utf-8') as stream:
        stream.write('\n\n## Conditional native delete summary source binding ('+ROUND+')\n\n'
            'Existing native delete success source now explicitly selects complete summary invalidation when host supplies native_summary_removal. '
            'Actual same-backend owned observation of all summaries+roots in own read transaction feeds mandatory issuer; exact Attempt/fullrow/fulltuple Decision and both phased native+summary Current precede152atomic removal. '
            'Selected source failures do not fall back, nonzero native replies skip observation/preparation/invalidation, Context identity independently guards optional presence. '
            'Queue summary Current requires actual committed removal and receipt rather than old raw Current. '
            'All summary decisions/expected inventory owned before removal SQL; existing transport completion/send_batch work remains postCOMMIT with durable recovery OPEN. '
            'WORLD68 resource/key/outputWORD and negative-GUI-path owner refined; GodLevel scratch/copy destination qualifications separated. '
            'Actual issuer/config/schema/data/Main still absent; three agents+source review saved; new packet/phase/owner/fullroute0, percent null, no build/test/native/API/C++/DB/deploy. Full goal active.\n')
    origins=[]
    for rel in SOURCES+books:
        raw=(ROOT/rel).read_bytes();save('source/current/'+rel,raw);origins.append(dict(path=rel,bytes=len(raw),sha256=sha(raw)))
        if rel in old:
            patch=''.join(difflib.unified_diff(old[rel].decode('utf-8-sig').splitlines(True),raw.decode('utf-8-sig').splitlines(True),fromfile='before/'+rel,tofile='source/'+rel))
            if patch:save('diff/'+rel+'.diff',patch.encode('utf-8'))
    dump('source/source-origins.json',origins)
    print(json.dumps({key:facts[key] for key in ['round','completed_parallel_agents','same_backend_owned_removal_observation_readers_added',
        'owned_scope_bound_summary_removal_decisions_added','existing_native_delete_summary_storage_bindings_added','new_complete_bidirectional_routes']}))

if __name__=='__main__':main()
