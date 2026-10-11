"""Retain pre-SQL held native02 framing and exact native layout frontiers; static only."""
import difflib
import hashlib
import json
from .cn_wrapper_route_frontier import ROOT

NAME='cn-native-delete-held-reply-source-01'
ROUND='20261008-cn-native-delete-held-reply-source'
SOURCES=['src/cn/net/SharedCredentialConnection.h','src/cn/net/SharedCredentialConnection.cpp',
 'src/cn/auth/SharedCharacterDeleteOperation.h','src/cn/auth/SharedCharacterDeleteOperation.cpp',
 'docs/research/cn-native-delete-held-reply-source-20261008.md',
 'tools/reconstruction/cn_native_delete_held_reply_delivery.py','tools/reconstruction/dual_client_route_catalog.py']
REMAINING=[
 'Actual native deletion/summary-wide issuer, source factory/Main CN plan/schema/native07+22 data remain unconfigured; no hosting.',
 'Held framing prepares PendingSend/native wire/capacity before removal SQL, but postCOMMIT strand post/write/completion/Current/close still fail; durable receipt/replay/disconnect recovery/1E remain open.',
 'General summary CAS and whole-account worldoffer refresh/revocation/historical malformed repair remain open; selected removal retains existing affected-character plan only.',
 'Actual account40+16/world reservation/bootstrap/presence/per-session TW/save/replay/hosting and full TW/CN/PC/web/WSS/numeric64/stack99/denominator remain open.',
 'WORLD68 nested context and two no-child-call witnesses do not qualify other child calls/upstream preservation/common item authority/stack99; next407E16->409C00 actual outputs.',
 'GodLevel selected row stride3EC and13-to28 distance21 are not title capacity; selector4 Current/firstNUL/42CA20 caller/450B80 helpers/record revision remain open.',
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
    if len(before)!=217:raise RuntimeError('Expected217 before files')
    old={row['path']:(out/row['snapshot']).read_bytes() for row in before}
    books=['docs/PACKET_CONNECTION_GOAL_20261006.md','artifacts/integration/packet-connections-20261006/packet-route-ledger.json']
    reports={f'artifacts/integration/packet-connections-20261006/packet-progress-latest.{ext}' for ext in ['json','md']}
    protected=[]
    for row in before:
        if sha(old[row['path']])!=row['sha256']:raise RuntimeError('Before receipt differs')
        if row['path'] not in set(SOURCES+books)|reports:
            if (ROOT/row['path']).read_bytes()!=old[row['path']]:raise RuntimeError('Protected source differs: '+row['path'])
            protected.append(row)
    prior=(out/'retained-prior/cn-native-delete-summary-source-binding-01/manifest.json').read_bytes()
    if sha(prior)!='151671adfb5b3f4ae0001331166af145b0ebe4143af5c3fb2cf13e542a42650c' or not json.loads(prior)['sealed']:
        raise RuntimeError('Prior153 seal differs')
    agents=[]
    for name in ['m2-source-hosting','receiver-frontier','title32-boundary','m2-source-review']:
        folder=out/'agents'/name;entry='design-review.json' if name=='m2-source-hosting' else 'findings.json'
        raw=(folder/entry).read_bytes()
        files=[dict(path=path.relative_to(folder).as_posix(),bytes=path.stat().st_size,sha256=sha(path.read_bytes()))
               for path in sorted(folder.rglob('*')) if path.is_file()]
        agents.append(dict(agent=name,entry=entry,findings_sha256=sha(raw),findings=json.loads(raw),files=files,
                           formal_source_modified_by_agent=False))
    seal=(out/'agents/title32-boundary/seal.json').read_bytes()
    if sha(seal)!='0f682c23eb079ed462f9c083e19c67dd4ddf72a4bd48da227cfa020c24636d9d':raise RuntimeError('Title154 seal differs')
    for row in json.loads(seal)['files']:
        raw=(out/'agents/title32-boundary'/row['path']).read_bytes()
        if sha(raw)!=row['sha256'] or len(raw)!=row['bytes']:raise RuntimeError('Title receipt differs')
    dump('parallel-agent-deliveries.json',agents)
    receiver=agents[1]['findings'];title=agents[2]['findings']
    relations=dict(source_only=True,version_scope='pinned-cn-native19/native02 conditional common removal, no new phase',
        native_delete=dict(explicit_world_entry='SharedCredentialConnection::send_world_batch_with_commit',
            actual_callback='SharedCharacterDeleteOperation::commit_held_reply',
            original_native02_complete_bytes=23,original_wire_changed=False,
            order=['owned actual native Decision/optional SummaryDecision','ReplyHeld',
                   'PendingSend/callbacks/native encoding/frame and byte capacity/output staging',
                   'game callback requalifies exact attempt/fullrow/old identity',
                   'same common synchronous removal and optional all-account summary invalidation transaction',
                   'BeforeQueue/current/ReplyQueued','strand barrier release','AfterQueue'],
            original_observing_publication_behavior_preserved=True,world_wrapper_mixed_auto_declaration_split=True,
            actual_CN_transport_source_modified=False,held_bytes_cannot_write_before_commit_callback=True,
            exact_account_world_session_admission_checked_before_and_after=True,
            async_resume_requires_same_designated_operation_Phase_ReplyHeld_and_not_committed=True,
            entire_summary_and_root_CAS_rechecked_inside_actual_transaction=True,
            local_reference_captures_confined_to_synchronous_transaction=True,
            summary_selected_fail_never_falls_back=True,nonzero_native_reply_skips_summary_and_removal=True,
            legacy_common_removal_writer_preserved=True,BeforeQueue_double_phase_guard=True,
            queue_acceptance_not_client_receipt=True,AfterQueue_can_run_after_bytes_begin_writing=True,
            all_transport_work_pre_COMMIT=False,post_COMMIT_failure_points=['strand post','async_write','completion post','Current/storage','close'],
            durable_receipt_replay_disconnect_recovery_connected=False,actual_issuer_configured=False,formal_hosting=False),
        WORLD68_nested_owner_qualification=receiver,
        WORLD32_selected_row_layout_frontier=title,
        complete_route=False,formal_application_hosted=False)
    dump('source/held-reply-and-native-layout-relations.json',relations)
    facts=dict(round=ROUND,previous_goal_turn_classification='progress:153 selected actual summary-aware deletion source/owned observation; framing still postCOMMIT',
        completed_parallel_agents=3,completed_agent_deliveries_with_source_review=4,
        explicit_world_mutation_held_reply_entries_added=1,native_delete_pre_SQL_framing_bindings_added=1,
        asynchronous_full_root_identity_and_phase_resume_guards_added=1,
        WORLD68_nested_owner_context_qualifications_added=receiver['new_WORLD68_nested_owner_context_qualifications'],
        WORLD68_no_child_call_preservation_witnesses_added=receiver['selected_no_child_call_preservation_witnesses'],
        GodLevel_selected_row_layout_lineages_added=title['counts']['new_selected_row_layout_lineages'],
        GodLevel_declared_title_capacities_newly_qualified=title['counts']['newly_qualified_declared_title_capacities'],
        source_review_definite_new_implementation_errors_found=0,
        pre_SQL_native_framing_capacity_and_callbacks_connected=True,post_COMMIT_transport_failure_recovery_completed=False,
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
    ledger['cn_native_delete_held_reply_source']=dict(facts,evidence=out.relative_to(ROOT).as_posix())
    ledger['dual_client_source_segments'].append(dict(name=NAME,round=ROUND,
        version_scope='pinned-cn-native19/native02-pre-SQL-held-framing-common-removal-source-only',
        status='Actual deletion stages native frames/capacity/callbacks before synchronous common removal; config/issuer/schema/Main/durable recovery/hosting absent',
        source_paths=SOURCES,native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,
        tw_source_owner_chains_added=0,formal_application_hosted=False,complete_gameplay_routes_added=0,
        evidence=out.relative_to(ROOT).as_posix(),remaining=REMAINING))
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next_source_frontier']='Actual deletion/summary-wide issuer config and durable receipt/replay/disconnect recovery; general worldoffer/CAS; native07+22/Main/source factory/account40+16/world/presence;WORLD68 actual407E16->409C00 outputs/preservation;GodLevel selectedrow capacity/record revision/42CA20/string4/450B80 helper;full TW/CN/web/numeric64/stack99/denominator. PHASE1.'
    path.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (ROOT/books[0]).open('a',encoding='utf-8') as stream:
        stream.write('\n\n## Native deletion held reply before removal SQL ('+ROUND+')\n\n'
            'Dedicated world mutation entry preserves observing publication semantics. Actual native deletion owns decisions and reply, then existing native transport prepares PendingSend/callbacks/frame+byte capacity/encrypted frames behind barrier BEFORE synchronous game removal. '
            'ReplyHeld async resume requalifies exact designated operation/full common root/old identity; actual writer retains full inventory+root CAS and native/summary Current. Local reference callbacks remain confined to synchronous transaction. '
            'Nonzero replies skip summary/removal; selected failures never fall back; BeforeQueue gains double phase guard; AfterQueue retained. '
            'PostCOMMIT posts/writes/Current/close can still fail; durable receipts/replay/recovery/1E remain OPEN, not DB+network atomicity. '
            'Three agents and separate actualsource review delivered WORLD68 nestedowner/conditional preservation and GodLevel selectedrow layout; stride3EC and field distance21 do not prove title capacity. '
            'Actual issuer/config/schema/data/Main absent; new packet/phase/owner/fullroute0, percent null; no build/test/native/API/C++/SQLDB/deploy. Full goal active.\n')
    origins=[]
    for rel in SOURCES+books:
        raw=(ROOT/rel).read_bytes();save('source/current/'+rel,raw);origins.append(dict(path=rel,bytes=len(raw),sha256=sha(raw)))
        if rel in old:
            patch=''.join(difflib.unified_diff(old[rel].decode('utf-8-sig').splitlines(True),raw.decode('utf-8-sig').splitlines(True),fromfile='before/'+rel,tofile='source/'+rel))
            if patch:save('diff/'+rel+'.diff',patch.encode('utf-8'))
    dump('source/source-origins.json',origins)
    print(json.dumps({key:facts[key] for key in ['round','completed_parallel_agents','explicit_world_mutation_held_reply_entries_added',
        'native_delete_pre_SQL_framing_bindings_added','new_complete_bidirectional_routes']}))

if __name__=='__main__':main()
