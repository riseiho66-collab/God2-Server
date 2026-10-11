"""Retain actual common removal commit facts and precise lookup output evidence; static only."""
import difflib
import hashlib
import json
from .cn_wrapper_route_frontier import ROOT

NAME='cn-native-delete-commit-observation-source-01'
ROUND='20261008-cn-native-delete-commit-observation-source'
SOURCES=['src/auth/SharedCharacterRemoval.h','src/auth/SharedCharacterRemoval.cpp',
 'src/cn/auth/SharedCharacterDeleteOperation.h','src/cn/auth/SharedCharacterDeleteOperation.cpp',
 'docs/research/cn-native-delete-commit-observation-source-20261008.md',
 'tools/reconstruction/cn_native_delete_commit_observation_delivery.py','tools/reconstruction/dual_client_route_catalog.py']
REMAINING=[
 'Actual native deletion/summary-wide issuer, source factory/Main CN plan/schema/native07+22 data remain unconfigured; no hosting.',
 'Process-local commit fact survives prepared offer apply failure but is not durable receipt/permission; postCOMMIT transport/replay/disconnect/crash recovery/1E remain open.',
 'General summary CAS and whole-account worldoffer refresh/revocation/historical malformed repair remain open; selected removal retains existing affected-character plan only.',
 'Actual account40+16/world reservation/bootstrap/presence/per-session TW/save/replay/hosting and full TW/CN/PC/web/WSS/numeric64/stack99/denominator remain open.',
 'WORLD68 effective stack lookup base/null/output/normal-return preservation do not qualify later child or upstream effects/common authority/stack99; next407E59->40A530.',
 'Title boundary research interrupted by safety; retained partial files are unreviewed, not native qualification. Capacity/selector4 Current/firstNUL/42CA20 caller/record revision remain open.',
 'All source routes first; then comprehensive builds/testing/repairs/recovery/playable release still required.']

def sha(raw):return hashlib.sha256(raw).hexdigest()

def main():
    base=ROOT/'artifacts/integration/packet-connections-20261006';out=base/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():raise RuntimeError('Fresh before required')
    def save(rel,raw):
        path=out/rel;path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('xb') as stream:stream.write(raw)
    def dump(rel,value):save(rel,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    before=json.loads((out/'before-manifest.json').read_text(encoding='utf-8'))
    if len(before)!=221:raise RuntimeError('Expected221 before files')
    old={row['path']:(out/row['snapshot']).read_bytes() for row in before}
    books=['docs/PACKET_CONNECTION_GOAL_20261006.md','artifacts/integration/packet-connections-20261006/packet-route-ledger.json']
    reports={f'artifacts/integration/packet-connections-20261006/packet-progress-latest.{ext}' for ext in ['json','md']}
    protected=[]
    for row in before:
        if sha(old[row['path']])!=row['sha256']:raise RuntimeError('Before receipt differs')
        if row['path'] not in set(SOURCES+books)|reports:
            if (ROOT/row['path']).read_bytes()!=old[row['path']]:raise RuntimeError('Protected source differs: '+row['path'])
            protected.append(row)
    prior=(out/'retained-prior/cn-native-delete-held-reply-source-01/manifest.json').read_bytes()
    if sha(prior)!='613a5011610805cbf76899c28b0e0937e9afa9916d6a819dd31bb61f05e8e3ca' or not json.loads(prior)['sealed']:
        raise RuntimeError('Prior154 seal differs')
    agents=[]
    for name,entry,complete in [('m2-source-hosting','design-review.json',True),('receiver-frontier','findings.json',True),
                               ('title32-boundary','partial-findings.json',False),('m2-source-review','findings.json',True)]:
        folder=out/'agents'/name;raw=(folder/entry).read_bytes()
        files=[dict(path=path.relative_to(folder).as_posix(),bytes=path.stat().st_size,sha256=sha(path.read_bytes()))
               for path in sorted(folder.rglob('*')) if path.is_file()]
        agents.append(dict(agent=name,entry=entry,complete=complete,findings_sha256=sha(raw),findings=json.loads(raw),files=files,
                           formal_source_modified_by_agent=False))
    seal=(out/'agents/title32-boundary/sealed-partial-manifest.json').read_bytes()
    if sha(seal)!='7c2b78cc5cf49d1b24578495379c417b28490baab3580420135d8ea88f7cc729':raise RuntimeError('Partial seal differs')
    for row in json.loads(seal)['files']:
        raw=(out/'agents/title32-boundary'/row['path']).read_bytes()
        if sha(raw)!=row['sha256'] or len(raw)!=row['bytes']:raise RuntimeError('Partial receipt differs')
    dump('parallel-agent-deliveries.json',agents)
    receiver=agents[1]['findings'];partial=agents[2]['findings']
    relations=dict(source_only=True,version_scope='pinned-cn-native19/native02 actual common removal fact observation',
        native_delete=dict(observation='SharedCharacterRemoval::CommitObservation',states=['Unused','Started','Committed','Invalidated'],
            observation_copy_move_reset_allowed=False,first_entry_consumed_before_presence_plan_or_Current=True,
            rejected_throwing_attempt_never_reverts_to_Unused=True,argument_construction_before_entry_not_observed=True,
            expected_account_character_metadata_not_authority=True,
            actual_commit_fact_recorded_immediately_after_SQL_writer_true=True,
            no_callback_allocation_yield_between_writer_success_and_scalar_fact=True,
            prepared_offer_application_false_or_throw_preserves_committed_fact=True,Invalidated_requires_actual_apply_true=True,
            observed_entries=['commit_observed','commit_with_native_summaries_observed'],
            existing_bool_callers_preserve_false_exception_and_prepared_apply_behavior=True,
            actual_SQL_writer_or_SQL_changed=False,mandatory_actual_permission_presence_scope_fullrow_summary_CAS_preserved=True,
            both_CN_success_branches_use_same_operation_owned_observation=True,nonzero_reply_does_not_consume_observation=True,
            ReplyHeld_resume_rejects_any_attempted_observation=True,
            queue_requires_successful_return_Invalidated_and_exact_account_character=True,
            stopped_committed_failure_phase='CommittedFailure, neither quiescent nor nonzero reply success',
            readonly_outcome='game-owner checked owned {attempted,storage_committed,offers_invalidated}',
            process_local_fact_not_permission_or_durable_receipt=True,durable_recovery_connected=False,actual_issuer_or_host_configured=False),
        WORLD68_lookup_output_qualification=receiver,
        WORLD32_research_interruption={key:partial[key] for key in ['taskinterrupted_by_safety','complete','qualification_status',
            'administrative_only','blocked_native_research_retried','native_helper_qualified_by_this_partial','declared_capacity_qualified_by_this_partial','remaining_OPEN']},
        complete_route=False,formal_application_hosted=False)
    dump('source/commit-observation-and-native-output-relations.json',relations)
    facts=dict(round=ROUND,previous_goal_turn_classification='progress:154 actual pre-SQL native framing/held game commit plus native owner/layout evidence, no complete route',
        delegated_parallel_agents=3,completed_parallel_agents=2,incomplete_research_agents=1,completed_agent_deliveries_with_source_review=3,
        title_research_interrupted_by_safety=True,title_partial_files_are_native_qualification=False,
        one_attempt_commit_observations_added=1,observed_common_removal_entries_added=2,actual_CN_commit_fact_bindings_added=1,
        WORLD68_lookup_output_qualifications_added=receiver['new_context_lookup_input_output_qualifications'],
        WORLD68_native_NULL_case_distinctions_added=receiver['new_native_NULL_case_distinctions'],
        source_review_definite_new_implementation_errors_found=0,actual_postCOMMIT_apply_failure_fact_gap_addressed=True,
        process_local_commit_fact_is_durable_receipt=False,post_COMMIT_failure_recovery_completed=False,
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
    ledger['cn_native_delete_commit_observation_source']=dict(facts,evidence=out.relative_to(ROOT).as_posix())
    ledger['dual_client_source_segments'].append(dict(name=NAME,round=ROUND,
        version_scope='pinned-cn-native19/native02-common-COMMIT-fact-before-prepared-offer-application-source-only',
        status='Actual common SQL successful return marks operation-owned commit fact before offer apply; legacy behavior retained; issuer/config/durable recovery/hosting absent',
        source_paths=SOURCES,native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,
        tw_source_owner_chains_added=0,formal_application_hosted=False,complete_gameplay_routes_added=0,
        evidence=out.relative_to(ROOT).as_posix(),remaining=REMAINING))
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next_source_frontier']='Actual deletion/summary-wide issuer/durable recovery; general worldoffer/CAS; native07+22/Main/source factory/account40+16/world/presence;WORLD68 actual407E59->40A530 child effects;title research interrupted/unknown capacity and Current remain OPEN;full TW/CN/web/numeric64/stack99/denominator. PHASE1.'
    path.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (ROOT/books[0]).open('a',encoding='utf-8') as stream:
        stream.write('\n\n## Actual common removal commit observation ('+ROUND+')\n\n'
            'Single-attempt noncopy/nonmove process-local observation marks Started before observing calls, actual Committed immediately after SQL writer true, Invalidated only after prepared offer apply true. False/throw consumes attempt; apply failure preserves actual committed fact. '
            'Two observed shared entries preserve bool-only semantics through null observer. CN both success branches retain same member fact, exact account/character/Invalidated before queue, distinct nonquiescent CommittedFailure and owner-checked outcome; nonzero skips observation. '
            'No new native permission/reply/durable receipt, SQL or frozen TW handler changes. WORLD68 actual stack-base/NULL outputs/normal-return preservation refined. '
            'Two research/design workers completed plus source review; title worker interrupted by safety and inventory-only sealed partial, not retried or counted qualified. '
            'Actual issuer/config/schema/data/Main/recovery still absent; new packet/phase/owner/fullroute0, percent null; no build/test/native/API/C++/SQLDB/deploy. Full goal active.\n')
    origins=[]
    for rel in SOURCES+books:
        raw=(ROOT/rel).read_bytes();save('source/current/'+rel,raw);origins.append(dict(path=rel,bytes=len(raw),sha256=sha(raw)))
        if rel in old:
            patch=''.join(difflib.unified_diff(old[rel].decode('utf-8-sig').splitlines(True),raw.decode('utf-8-sig').splitlines(True),fromfile='before/'+rel,tofile='source/'+rel))
            if patch:save('diff/'+rel+'.diff',patch.encode('utf-8'))
    dump('source/source-origins.json',origins)
    print(json.dumps({key:facts[key] for key in ['round','completed_parallel_agents','incomplete_research_agents',
        'one_attempt_commit_observations_added','observed_common_removal_entries_added','new_complete_bidirectional_routes']}))

if __name__=='__main__':main()
