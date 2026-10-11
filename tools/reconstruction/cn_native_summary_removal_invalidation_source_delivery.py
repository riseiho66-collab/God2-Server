"""Retain explicit complete-account summary invalidation with common root removal; static only."""
import difflib
import hashlib
import json
from .cn_wrapper_route_frontier import ROOT

NAME='cn-native-summary-removal-invalidation-source-01'
ROUND='20261008-cn-native-summary-removal-invalidation-source'
SOURCES=['src/db/SqliteNativeCharacterSummarySnapshotRepository.h',
 'src/db/SqliteRecoveredCharacterRepository.h','src/db/SqliteOwnedCharacterRemoval.cpp',
 'src/db/SqliteNativeSummaryRemovalInvalidation.cpp',
 'src/auth/SharedCharacterRemoval.h','src/auth/SharedCharacterRemoval.cpp',
 'src/cn/assets/CnSubjectTemplateNames.h',
 'docs/research/cn-native-summary-removal-invalidation-source-20261008.md',
 'tools/reconstruction/cn_native_summary_removal_invalidation_source_delivery.py',
 'tools/reconstruction/dual_client_route_catalog.py']
REMAINING=[
 'Actual native removal handler/issuer does not select new summary-aware entry; native rules/replies/replay/disconnect recovery and actual expected inventory/authority remain unconfigured.',
 'Schema registration/installation/native07+22 datasets/recovery/actual general CAS issuer+caller/Main CN plan/source factory remain absent.',
 'New removal source coordinates only stored account summaries and existing exact per-character admission invalidation; general summary CAS or whole-account worldoffer refresh/revocation remain open.',
 'GodLevel row reader overwrites parser return with1; source column/content/copy/current bytes/string4/firstNUL/intervening writes/42CA20 actual caller remain unqualified.',
 'Receiver old-record consumer contexts refine existing WORLD68; next4C7816->4C5320 and4C784E->4C5440 resource/key/output WORD; actual common item identity/authority/provider and47DE70/4812B0 network owner/phase open.',
 'Formal Application/account40+16/world reservation/bootstrap/presence/per-session TW/save/replay/hosting and complete TW/CN/PC/web/WSS/numeric64/stack99/whole-game denominator remain open; later full testing/repair/recovery release.']

def sha(raw):return hashlib.sha256(raw).hexdigest()

def main():
    base=ROOT/'artifacts/integration/packet-connections-20261006';out=base/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():raise RuntimeError('Fresh before required')
    def save(rel,raw):
        path=out/rel;path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('xb') as stream:stream.write(raw)
    def dump(rel,value):save(rel,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    before=json.loads((out/'before-manifest.json').read_text(encoding='utf-8'))
    if len(before)!=210:raise RuntimeError('Expected210 before files')
    old={row['path']:(out/row['snapshot']).read_bytes() for row in before}
    books=['docs/PACKET_CONNECTION_GOAL_20261006.md','artifacts/integration/packet-connections-20261006/packet-route-ledger.json']
    reports={f'artifacts/integration/packet-connections-20261006/packet-progress-latest.{ext}' for ext in ['json','md']}
    protected=[]
    for row in before:
        if sha(old[row['path']])!=row['sha256']:raise RuntimeError('Before receipt differs')
        if row['path'] not in set(SOURCES+books)|reports:
            if (ROOT/row['path']).read_bytes()!=old[row['path']]:raise RuntimeError('Protected source differs: '+row['path'])
            protected.append(row)
    prior=(out/'retained-prior/cn-native-character-summary-cas-source-01/manifest.json').read_bytes()
    if sha(prior)!='134d5209f10fceeed5e9b7aa9c82ac9546ff1122108c9e26ea46c7c9dcab8c6b' or not json.loads(prior)['sealed']:
        raise RuntimeError('Prior151 source seal differs')
    agents=[]
    for name in ['m2-source-hosting','receiver-frontier','title32-boundary','m2-source-review']:
        folder=out/'agents'/name;entry='design-review.json' if name=='m2-source-hosting' else 'findings.json'
        raw=(folder/entry).read_bytes()
        files=[dict(path=path.relative_to(folder).as_posix(),bytes=path.stat().st_size,sha256=sha(path.read_bytes()))
               for path in sorted(folder.rglob('*')) if path.is_file()]
        agents.append(dict(agent=name,entry=entry,findings_sha256=sha(raw),findings=json.loads(raw),files=files,
                           formal_source_modified_by_agent=False))
    seal=(out/'agents/title32-boundary/seal.json').read_bytes()
    if sha(seal)!='68cc961095590e0a8de87bb9f25c544efc4c450173529676b6658ba8cc6a6752':raise RuntimeError('Title152 seal differs')
    for row in json.loads(seal)['files']:
        raw=(out/'agents/title32-boundary'/row['path']).read_bytes()
        if sha(raw)!=row['sha256'] or len(raw)!=row['bytes']:raise RuntimeError('Title source receipt differs')
    dump('parallel-agent-deliveries.json',agents)
    relations=dict(source_only=True,version_scope='same common authority with pinned-CN evidence; inventory covers all stored client-build scopes',
        complete_inventory_reader='SqliteNativeCharacterSummarySnapshotRepository::load_for_account',
        caller_owner_transaction_required=True,implicit_BEGIN_or_schema_on_read=False,
        canonical_scope_order=['group','server','client SHA'],complete_tuple_and_all_optional_role_origins=True,
        inventory_all_account_scopes_not_only_deleted_ID=True,raw_child_cardinality_and_orphan_check_in_same_transaction=True,
        missing_schema_not_empty_success=True,
        explicit_storage_entry='SqliteRecoveredCharacterRepository::erase_owned_snapshot_with_native_summaries',
        actual_common_caller='SharedCharacterRemoval::commit_with_native_summaries ->erase_owned_snapshot_with_native_summaries',
        required_actual_issuer='CurrentNativeSummaryRemoval(phase,complete expected account summaries,complete original common roots)',
        actual_issuer_authorizes_account_wide_invalidation=True,actual_issuer_selected_or_executed=False,
        same_SQLite_account_mutable_character_identity=True,owner_thread_and_full_operation_summary_reentry_lease=True,
        own_BEGIN_IMMEDIATE=True,outer_transaction_rejected=True,foreign_keys_required=True,
        foreign_account_mapping_to_removed_ID_rejected=True,
        BeforeErase='complete expected inventory and exact original roots before/after actual observer',
        stage='delete every authorized account header before common root/descendant cleanup; exact header changes and independently checked child absence',
        after_header_delete='original full roots +empty header/child inventory +foreign account guard before cleanup',
        BeforeCommit='complete original roots minus exact ID and empty header/child inventory before/after actual observer',
        roles_names_slots_raw_native_bytes_not_generated=True,new_native_reply_or_refreshed07_generated=False,
        all_storage_mutations_same_transaction=True,existing_per_character_admission_plan_preallocated_and_rechecked=True,
        post_COMMIT='immediate prepared per-character admission invalidation without reads/callback/allocation/yield',
        general_summary_CAS_or_whole_account_worldoffer_invalidation=False,
        original_legacy_overload_and_frozen_handler_selection_preserved=True,
        actual_native_handler_or_Main_selected=False,schema_registered_or_installed=False,actual_native_data_imported=False,
        WORLD32_row_reader_qualification=dict(reader='00423480',parser='004234F0',override_site='004234D5',normal_EAX_result=1,
            actual_column_count='resource+C',scratch_stride='17C',scratch_content_limit=379,GodLevel_bank_stride=94,
            reader_success_not_column_completeness_or_bank_copy_bounds=True,
            misaligned42C9B0_displacement_excluded=True,current_selector4_string_qualified=False,actual42CA20_caller_qualified=False),
        WORLD68_old_record_context=dict(existing_opcode='68',existing_phase='world-connection-1',logical_bytes=13,
            caller='004C4060',call_site='004C409C',target='004C4880',actual_owner='entry UI=main+89B26C',
            actual_ECX_call_free_input_qualified=True,lookup_ESI_preservation_boundary_qualified=True,
            same_owner_callback='004C494A ->004C77E0',qualified_before_new_row_install=True,
            primary_functions=4,primary_bytes=1345,local_CFG_sites=375,local_frontiers=0,
            signed_record_BYTE_threshold1_or30_not_stack99=True,new_phase=False,common_item_mapping_or_authority_qualified=False,
            next_calls=['004C7816 ->004C5320','004C784E ->004C5440']),
        complete_route=False,formal_application_hosted=False)
    dump('source/removal-invalidation-and-native-consumer-relations.json',relations)
    facts=dict(round=ROUND,previous_goal_turn_classification='progress:151 complete issuer tuple atomic CAS writer, strict native75/25 Plan and actual sameDB commit entry; no hosting',
        completed_parallel_agents=3,completed_agent_deliveries_with_source_review=4,
        complete_account_summary_inventory_readers_added=1,atomic_summary_removal_invalidation_sources_added=1,
        actual_shared_summary_aware_removal_commit_entries_added=1,source_path_stale_header_gap_addressed=True,
        actual_native_removal_handler_selects_new_entry=False,
        GodLevel_row_parser_boolean_override_lineages_added=1,misaligned42C9B0_candidates_rejected=1,
        WORLD68_call_free_ECX_input_contexts_added=1,WORLD68_lookup_ESI_preservation_boundaries_added=1,
        WORLD68_same_owner_callback_contexts_added=1,source_review_definite_implementation_errors_found=0,
        new_packet_values=0,new_native_phase_source_bindings=0,new_source_owner_chains=0,new_tw_source_owner_chains=0,
        new_complete_bidirectional_routes=0,schema_registered_or_installed=False,actual_native_data_imported=False,
        actual_issuer_selected=False,actual_CN_plan_selected=False,formal_application_hosted=False,
        general_summary_or_whole_account_worldoffer_invalidation_connected=False,
        whole_game_route_total=None,whole_game_completed_routes=None,whole_game_completion_percent=None,
        original_native_wire_layout_changed=False,original_native_baseline_changed=False,levels_changed=False,
        build_run=False,tests_run=False,runtime_run=False,native_execution=False,Cplusplus_source_run=False,
        Windows_API_run=False,database_access=False,deployed=False,protected_contexts=protected,remaining=REMAINING)
    dump('findings.json',facts)
    path=ROOT/books[1];ledger=json.loads(path.read_text(encoding='utf-8'))
    if any(segment['name']==NAME for segment in ledger['dual_client_source_segments']):raise RuntimeError('Preserve existing segment')
    ledger['cn_native_summary_removal_invalidation_source']=dict(facts,evidence=out.relative_to(ROOT).as_posix())
    ledger['dual_client_source_segments'].append(dict(name=NAME,round=ROUND,
        version_scope='shared-complete-account-native-summary-invalidation-with-owned-removal-and-pinned-CN-consumer-refinement-source-only',
        status='Explicit same-backend atomic full-account summary invalidation with selected root deletion and prepared character offer apply; actual native issuer/handler/schema/hosting unconfigured',
        source_paths=SOURCES,native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,
        tw_source_owner_chains_added=0,formal_application_hosted=False,complete_gameplay_routes_added=0,
        evidence=out.relative_to(ROOT).as_posix(),remaining=REMAINING))
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next_source_frontier']='Actual new removal issuer/handler selection and complete inventory authorization/native reply/replay/recovery; general summary/worldoffer invalidation; actual native07+22/Main/factory/account40+16/world/presence;WORLD68 resource key WORD4C5320/4C5440;GodLevel contents/string4/42CA20;full TW/CN/web/numeric64/stack99/denominator. PHASE1.'
    path.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (ROOT/books[0]).open('a',encoding='utf-8') as stream:
        stream.write('\n\n## Complete native-summary invalidation with owned removal ('+ROUND+')\n\n'
            'Added complete all-account raw summary inventory in an actual owner transaction; exact canonical scope/tuple/role/ownership and always child-count checks. '
            'Explicit actual issuer authorizes whole account header invalidation in same root removal transaction; same backend/owner/FK/fullinterval reentry lease; '
            'expected inventory and full roots around BeforeErase, header+child absence before cleanup, roots-minus-ID and absence around BeforeCommit; foreign-account removed-ID references reject. '
            'Actual SharedCharacterRemoval with-summary caller preallocates existing character offer plan and applies immediately after COMMIT; general account/worldoffer revocation remains open. '
            'Old handler selection preserved; actual native issuer/handler/schema/data/Main not selected. '
            'GodLevel rowreader overwrites parser result with1; no column-completeness/bank bound inference. Misaligned42C9B0 excluded. '
            'Existing WORLD68 caller/lookup/callback refined; no new phase/stack99 claim. Three agents plus static source review retained. '
            'New packet/phase/owner/fullroute0; whole-game percent null; full TW/CN/web/numeric64/stack99 goal active, no build/test/native/API/C++/DB/deploy.\n')
    origins=[]
    for rel in SOURCES+books:
        raw=(ROOT/rel).read_bytes();save('source/current/'+rel,raw);origins.append(dict(path=rel,bytes=len(raw),sha256=sha(raw)))
        if rel in old:
            patch=''.join(difflib.unified_diff(old[rel].decode('utf-8-sig').splitlines(True),raw.decode('utf-8-sig').splitlines(True),fromfile='before/'+rel,tofile='source/'+rel))
            if patch:save('diff/'+rel+'.diff',patch.encode('utf-8'))
    dump('source/source-origins.json',origins)
    print(json.dumps({key:facts[key] for key in ['round','completed_parallel_agents','complete_account_summary_inventory_readers_added',
        'atomic_summary_removal_invalidation_sources_added','actual_shared_summary_aware_removal_commit_entries_added','new_complete_bidirectional_routes']}))

if __name__=='__main__':main()
