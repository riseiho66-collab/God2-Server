"""Retain actual shared experience award64 settlement/replay and owner frontiers; static only."""
import difflib
import hashlib
import json
from .cn_wrapper_route_frontier import ROOT

NAME='shared-experience-award64-source-01'
ROUND='20261008-shared-experience-award64-source'
SOURCES=['src/game/ExtendedExperienceAmount.h','src/db/RecoveredCharacterRepository.h',
 'src/db/SqliteRecoveredCharacterRepository.h','src/db/SqliteRecoveredCharacterRepository.cpp',
 'src/core/Config.h','src/core/Config.cpp','src/core/Application.cpp',
 'src/protocol/DiagnosticBattleParticipants.h','tests/test_recovered_player_snapshot.cpp',
 'docs/research/shared-experience-award64-source-20261008.md',
 'tools/reconstruction/shared_experience_award64_delivery.py','tools/reconstruction/dual_client_route_catalog.py']
REMAINING=[
 'Actual native TW/CN/web extended EXP producer/consumer/object/display/profile and native award rules remain open; shared storage width is not gameplay completion.',
 'HP/damage shared actors/rules/checkpoints/resources/SQL/Lua and precise numeric64 projections need connection; no coin cap applies to EXP/HP/damage.',
 'Existing coin wallet/bank receipt CHECK constraints need actual reversible migration source/release; stack99 and full shared economy routes remain open.',
 'Actual native deletion/summary-wide issuer/schema/data/Main/durable recovery and general worldoffer/CAS/account40+16/world reservation/bootstrap/presence remain open.',
 'WORLD68 child write/register evidence is conditional; runtime nonalias/later assertion/upstream effects/common item/stack99 remain open; next407E93->40B4B0 re-read index.',
 'Interrupted prior title research remains unreviewed partial; capacity/selector4 Current/firstNUL/42CA20 caller/record revision remain open, not retried.',
 'Full TW/CN/PC/web/WSS/save/replay/hosting/denominator/all source first, then comprehensive builds/testing/repairs/recovery/playable release still required.']

def sha(raw):return hashlib.sha256(raw).hexdigest()

def main():
    base=ROOT/'artifacts/integration/packet-connections-20261006';out=base/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():raise RuntimeError('Fresh before required')
    def save(rel,raw):
        path=out/rel;path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('xb') as stream:stream.write(raw)
    def dump(rel,value):save(rel,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    before=json.loads((out/'before-manifest.json').read_text(encoding='utf-8'))
    if len(before)!=233:raise RuntimeError('Expected233 before files')
    old={row['path']:(out/row['snapshot']).read_bytes() for row in before}
    books=['docs/PACKET_CONNECTION_GOAL_20261006.md','artifacts/integration/packet-connections-20261006/packet-route-ledger.json']
    reports={f'artifacts/integration/packet-connections-20261006/packet-progress-latest.{ext}' for ext in ['json','md']}
    protected=[]
    for row in before:
        if sha(old[row['path']])!=row['sha256']:raise RuntimeError('Before receipt differs')
        if row['path'] not in set(SOURCES+books)|reports:
            if (ROOT/row['path']).read_bytes()!=old[row['path']]:raise RuntimeError('Protected source differs: '+row['path'])
            protected.append(row)
    prior=(out/'retained-prior/cn-native-delete-commit-observation-source-01/manifest.json').read_bytes()
    if sha(prior)!='95d69811a83f28753aca6122773d1723b2e0b75b62bbc783b0ee4112dead2a1f' or not json.loads(prior)['sealed']:
        raise RuntimeError('Prior155 seal differs')
    agents=[]
    for name,entry in [('m2-source-hosting','design-review.json'),('receiver-frontier','findings.json'),
                       ('shared-numeric-frontier','boundedfindings.json'),('m2-source-review','findings.json')]:
        folder=out/'agents'/name;raw=(folder/entry).read_bytes()
        files=[dict(path=path.relative_to(folder).as_posix(),bytes=path.stat().st_size,sha256=sha(path.read_bytes()))
               for path in sorted(folder.rglob('*')) if path.is_file()]
        agents.append(dict(agent=name,entry=entry,findings_sha256=sha(raw),findings=json.loads(raw),files=files,
                           formal_source_modified_by_agent=False))
    receiver=agents[1]['findings'];numeric=agents[2]['findings']
    seal=(out/'agents/shared-numeric-frontier/seal.json').read_bytes()
    if sha(seal)!='ca101a8a038aae28c208ea99108a0254e9e865bca45b6d7a8dfddd631548d37f':raise RuntimeError('Numeric source seal differs')
    for row in json.loads(seal)['files']:
        raw=(out/'agents/shared-numeric-frontier'/row['path']).read_bytes()
        if sha(raw)!=row['sha256'] or len(raw)!=row['bytes']:raise RuntimeError('Numeric source receipt differs')
    dump('parallel-agent-deliveries.json',agents)
    relations=dict(source_only=True,version_scope='shared64 storage/calculation with unchanged CUSTOM diagnostic/native baseline',
        shared_experience=dict(domain='ExtendedExperienceAmount',value_type='uint64',SQLite_Lua_integer_representation='nonnegative signed64',
            INT64_MAX_is_representation_not_owner_selected_gameplay_cap=True,coin_cap_applied_to_EXP=False,
            saved_and_earned_validated_before_subtraction_and_addition=True,implicit_narrowing_allowed=False,
            actual_entries=['RecoveredCharacterRepository::settle_battle','SqliteRecoveredCharacterRepository::settle_battle',
                            'SqliteRecoveredCharacterRepository::settle_checkpoint','SqliteRecoveredCharacterRepository::settle_battle_impl'],
            award_domain_checked_before_canonical_request_or_replay=True,canonical_numeric_JSON_and_versions123_preserved=True,
            historical_decimal_request_compatibility='bounded source inference, not executed serialization proof',
            actual_whole_request_CAS_reservation_owner_loss_role_checkpoint_and_preCOMMIT_readback_preserved=True,
            actual_SQL_bindings_use_validated_explicit_signed64=True,existing_SQL_integer_columns_already_signed64=True,SQL_schema_changed=False,
            actual_Application_progression_uses_same_checked_accumulate=True,Lua_level_thresholds_and_native_levels_unchanged=True,
            Config_value_type_uint64_but_original_zero_signed32_bound_and_terminal_permit_preserved=True,
            diagnostic_producer='opcode89,logical57,offset5 four bytes, CUSTOM-0012',
            diagnostic_input_uint64_checked_before_explicit_DWORD_projection=True,original_diagnostic_opaque_bytes_and_wire_preserved=True,
            existing_test_fake_override_mechanically_updated_only=True,new_tests_written=False,
            CUSTOM_rules_not_CN_native_award_authority=True,TW_CN_web_extended_wire_and_display_connected=False,formal_deployed=False),
        WORLD68_child_store_qualification=receiver,shared_HP_damage_storage_calculation_frontier=dict(numeric,
            exact_frontier=json.loads((out/'agents/shared-numeric-frontier/storage-calculation-frontier.json').read_text(encoding='utf-8'))),
        prior_title_interrupted_research_retried=False,complete_route=False,formal_application_hosted=False)
    dump('source/experience64-and-native-owner-relations.json',relations)
    facts=dict(round=ROUND,previous_goal_turn_classification='progress:155 actual common COMMIT observation/owned CN failure state and native lookup output evidence; title partial not qualified',
        delegated_parallel_agents=3,completed_parallel_agents=3,completed_agent_deliveries_with_source_review=4,
        shared_checked_experience_amount_domains_added=1,actual_experience_award64_settlement_entries_added=2,
        actual_experience_award64_replay_storage_bindings_added=1,actual_Application_checked_progression_accumulation_bindings_added=1,
        legacy_diagnostic_experience64_input_checked_projections_added=1,existing_test_fake_interface_updates=1,new_tests_written=0,
        WORLD68_child_store_qualifications_added=receiver['new_actual_child_owner_store_relations'],
        shared_HP_damage_storage_calculation_frontiers_added=numeric['new_precise_storage_calculation_frontiers'],
        source_review_definite_new_implementation_errors_found=0,
        full_native_TW_CN_web_experience64_completed=False,actual_native_award_rules_selected=False,HP_damage_numeric64_completed=False,
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
    ledger['shared_experience_award64_source']=dict(facts,evidence=out.relative_to(ROOT).as_posix())
    ledger['dual_client_source_segments'].append(dict(name=NAME,round=ROUND,
        version_scope='shared-experience-award64-actual-settlement-canonical-replay-unchanged-CUSTOM-native-baseline-source-only',
        status='Actual shared settlement/checkpoint entry/replay/storage and progression accept validated award64; legacy wire checked and unchanged, actual native rules/extended profile/acceptance absent',
        source_paths=SOURCES,native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,
        tw_source_owner_chains_added=0,formal_application_hosted=False,complete_gameplay_routes_added=0,
        evidence=out.relative_to(ROOT).as_posix(),remaining=REMAINING))
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next_source_frontier']='Shared HP/damage actors/rules/checkpoints/resources/SQL/Lua checked64 and actual TW/CN/web extended numeric producer/consumer/object/display; coin migration/stack99; WORLD68 actual407E93->40B4B0 re-read index; actual deletion/summary-wide issuer/durable recovery/generalworldoffer/native07+22/Main/account40+16/world; interrupted title OPEN;full denominator/hosting. PHASE1.'
    path.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (ROOT/books[0]).open('a',encoding='utf-8') as stream:
        stream.write('\n\n## Shared experience award64 settlement source ('+ROUND+')\n\n'
            'ExtendedExperienceAmount validates saved/earned signed64 representability before arithmetic, not EXP gameplay cap or coin cap. Actual virtual/SQLite battle and checkpoint award entries now64, actual canonical numeric request versions/replay/CAS retained, accumulated amount bound explicitly signed64 to existing integer columns. '
            'Application progression uses same checked helper; Config type64 but legacy signed32 limit/zero/terminal authorization unchanged; diagnostic opcode89 logical57 accepts64 input then exact bound before explicit DWORD projection. '
            'Only existing test fake signature mechanically matched, no tests added/run. CUSTOM award not CNnative; extended TW/CN/web wire/object/display/native award rules stillOPEN. '
            'Three workers+source review delivered WORLD68 child owner write/register and server-only HP/damage storage+calculation frontier; no retry of interrupted native title research. '
            'New packet/phase/owner/fullroute0, percent null; no schema/build/test/native/API/C++/SQLDB/deploy. Full goal active.\n')
    origins=[]
    for rel in SOURCES+books:
        raw=(ROOT/rel).read_bytes();save('source/current/'+rel,raw);origins.append(dict(path=rel,bytes=len(raw),sha256=sha(raw)))
        if rel in old:
            patch=''.join(difflib.unified_diff(old[rel].decode('utf-8-sig').splitlines(True),raw.decode('utf-8-sig').splitlines(True),fromfile='before/'+rel,tofile='source/'+rel))
            if patch:save('diff/'+rel+'.diff',patch.encode('utf-8'))
    dump('source/source-origins.json',origins)
    print(json.dumps({key:facts[key] for key in ['round','completed_parallel_agents','shared_checked_experience_amount_domains_added',
        'actual_experience_award64_settlement_entries_added','new_complete_bidirectional_routes']}))

if __name__=='__main__':main()
