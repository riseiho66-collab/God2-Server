"""Account actual HP64 storage and explicit legacy boundaries; files only."""
import difflib
import argparse
import hashlib
import json
from pathlib import Path
from .cn_wrapper_route_frontier import ROOT

NAME='shared-hp-storage64-source-01'
ROUND='20261008-shared-hp-storage64-source'
WRITTEN=['src/game/ExtendedHealthAmount.h','src/game/CharacterResources.h',
 'src/db/SqliteRecoveredCharacterRepository.cpp','src/protocol/RecoveredRoleVitals.h',
 'src/handlers/DiagnosticSupplyService.cpp','src/protocol/DiagnosticShunyingManual.h',
 'src/db/SqliteOwnedPkRoomRepository.cpp','src/core/Application.cpp',
 'src/protocol/DiagnosticBattleParticipants.h','src/game/NativeParty.h','src/protocol/RecoveredParty.h',
 'docs/research/shared-hp-storage64-source-20261008.md','tools/reconstruction/shared_hp_storage64_delivery.py',
 'tools/reconstruction/dual_client_route_catalog.py']
BOOKS=['docs/PACKET_CONNECTION_GOAL_20261006.md','artifacts/integration/packet-connections-20261006/packet-route-ledger.json']
REMAINING=[
 'Full HP/damage64 Battle/rules/exact Lua/checkpoint/role authority/recipient TW-CN-web producer-consumer-object-floatingtext remains OPEN; checked legacy refusal is not wide gameplay.',
 'Compiled migration6 HP DWORD CHECK remains unchanged; actual schema54 cannot bypass guarded53 preservation or exact-version readers/factories; installed opaque dependency qualification/additive recovery migration needed.',
 'Stored role native DWORD maxima equality remains mandatory; future extended authority/projection must connect without narrowing or weakening that check.',
 'Original legacy Battle/codec/Supply/RNG/levels/native DWORD bitmath/CUSTOM rules preserved; HP/damage/EXP maxima undecided, coin cap does not apply.',
 'Existing settlement return copies after COMMIT are unchanged prior source, not a new durability/recovery repair; full PK terminal owner/save/outbox and native profile still OPEN.',
 'Coin wallet CHECK/migration/stack99, account/admission/world/native issuer/Main/generalworldoffer, WORLD68 re-read index/receiver phase/alias and interrupted title work remain OPEN.',
 'Whole-game directional-phase-state-variant denominator, all TW/CN/PC/web routes/hosting/WSS, later comprehensive builds/tests/repairs/recovery/playable release remain required.']

def sha(raw):return hashlib.sha256(raw).hexdigest()

def main(resume=False):
    base=ROOT/'artifacts/integration/packet-connections-20261006';out=base/NAME
    if not (out/'before-manifest.json').exists() or (out/'manifest.json').exists() or ((out/'findings.json').exists() and not resume):raise RuntimeError('Fresh before or explicit unsealed recovery required')
    def save(rel,raw):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
        if p.exists():
            prior=p.read_bytes()
            if prior==raw:return
            if not resume:raise RuntimeError('Preserve existing receipt')
            recovery=out/'recovery/delivery-interrupted-01';recovery.mkdir(parents=True,exist_ok=True)
            key=sha(rel.encode('utf-8'))[:16]
            with (recovery/(key+'.bin')).open('xb') as stream:stream.write(prior)
            with (recovery/(key+'.json')).open('x',encoding='utf-8') as stream:
                json.dump(dict(original_relative_path=rel,bytes=len(prior),sha256=sha(prior),reason='unsealed delivery source-path classification correction'),stream,indent=2)
            p.write_bytes(raw)
        else:
            with p.open('xb') as f:f.write(raw)
    def dump(rel,value):save(rel,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    before=json.loads((out/'before-manifest.json').read_text(encoding='utf-8'));old={x['path']:(out/x['snapshot']).read_bytes() for x in before}
    if len(before)!=921:raise RuntimeError('Expected921 before sources')
    reports={f'artifacts/integration/packet-connections-20261006/packet-progress-latest.{x}' for x in ['json','md']}
    protected=[]
    for row in before:
        if sha(old[row['path']])!=row['sha256']:raise RuntimeError('Before receipt differs')
        if row['path'] not in set(WRITTEN+BOOKS)|reports:
            if (ROOT/row['path']).read_bytes()!=old[row['path']]:raise RuntimeError('Protected source differs: '+row['path'])
            protected.append(row)
    for name,pin in [('shared-hp-damage-connection-frontier-01','0b788b97da4d70f295dac3a86eafaf49117ce9093fad04c688feaf26e7d3f413'),
                     ('endpoint-catalog157','ac30f7cc75087e588e9a372c6ecc2870c8b86e63f96e0e53edd3f77dee6b88e1')]:
        raw=(out/'retained-prior'/name/'manifest.json').read_bytes()
        if sha(raw)!=pin or not json.loads(raw)['sealed']:raise RuntimeError('Prior157 seal differs')
    paths=set(WRITTEN);agents=[];records=[]
    def retain_origin(folder,row,epoch):
        rel=row.get('source_relative_path',row['path']);p=Path(rel)
        if not p.is_absolute():p=ROOT/p
        repo=p.relative_to(ROOT).as_posix();paths.add(repo)
        raw=(folder/row['copy']).read_bytes()
        if len(raw)!=row['bytes'] or sha(raw)!=row['sha256']:raise RuntimeError('Retained source copy differs')
        current=p.read_bytes();matches=sha(current)==row['sha256'] and len(current)==row['bytes']
        if epoch=='current' and not matches:raise RuntimeError('Current source receipt differs: '+repo)
        if not matches and (repo not in old or old[repo]!=raw):raise RuntimeError('Changed observed source lacks correct before921 basis')
        records.append(dict(folder=folder.relative_to(out).as_posix(),epoch=epoch,path=repo,current_matches_observed=matches,source=row))
    for name in ['resource-migration','calculation-boundaries','recipient-boundaries','storage-source-review']:
        folder=out/'agents'/name;raw=(folder/'findings.json').read_bytes()
        seal=json.loads((folder/'seal.json').read_text(encoding='utf-8-sig'));files=seal.get('files',seal.get('entries',[]))
        if not files:raise RuntimeError('Missing agent seal files')
        for row in files:
            v=(folder/row['path']).read_bytes()
            if len(v)!=row['bytes'] or sha(v)!=row['sha256']:raise RuntimeError('Agent seal differs')
        origin=json.loads((folder/'source-origin.json').read_text(encoding='utf-8-sig'))
        if name=='recipient-boundaries':
            for row in origin['sources']:
                if row['first_read'] is not None:
                    retain_origin(folder,dict(path=row['path'],**row['first_read']),'observed-before')
                retain_origin(folder,dict(path=row['path'],**row['current']),'current')
        elif name=='calculation-boundaries':
            for row in origin['source_files']:retain_origin(folder,row,'current' if row.get('snapshot')=='observed-current' else 'observed-before')
        else:
            for row in origin['files']:
                epoch='observed-migration-source' if name=='resource-migration' else ('current' if row['kind']=='current' else 'observed-before')
                retain_origin(folder,row,epoch)
        inventory=[dict(path=p.relative_to(folder).as_posix(),bytes=p.stat().st_size,sha256=sha(p.read_bytes())) for p in sorted(folder.rglob('*')) if p.is_file()]
        agents.append(dict(agent=name,findings=json.loads(raw),findings_sha256=sha(raw),files=inventory,source_origin=origin,
            formal_source_modified_by_agent=name=='recipient-boundaries',agent_owned_source_edits=['src/game/NativeParty.h','src/protocol/RecoveredParty.h'] if name=='recipient-boundaries' else []))
    dump('parallel-agent-deliveries.json',agents);dump('source/reviewed-source-records.json',records)
    relations=dict(source_only=True,absolute_HP_domain='ExtendedHealthAmount',HP_maxHP_type='uint64',MP_maxMP_type='uint32',
        nonnegative_signed64_is_storage_representability_not_gameplay_maximum=True,coin_cap_applied=False,
        actual_load_resources_uint64=True,actual_shared_CAS_writer_checked_explicit_signed64_bind=True,
        actual_settlement_HP_MP_bounds_before_canonical_and_replay=True,canonical_numeric_versions123_preserved=True,
        legacy_JSON_decimal_compatibility='source inference, not executed proof',
        actual_owner_whole_tuple_revision_role_maxima_SQL_affected_count_readback_preserved=True,
        legacy_vitals_checked_before_Supply_Lua_inventory_change_manual_actor_PK_entry_and_initialHP=True,
        role24_and_diagnostic_progress_checked_HP64_to_original_DWORD=True,
        party_snapshot_preserves_wide_HP_before_original_signedWORD_HUD_gate=True,
        party_MP_snapshot_carries_original_uint32_authority=True,party58_checked_full_input_before_unchanged21byte_body=True,
        party_chat_identity_readiness_logic_unchanged=True,old_legacy_party_helper_bounds_not_added=True,
        migration=agents[0]['findings'],calculation_review=agents[1]['findings'],recipient_review=agents[2]['findings'],storage_review=agents[3]['findings'],
        migration_Application_snapshot_is_before_root_edit=True,migration_routing_current_review_retained=True,
        old_migrations_and_original_native_wire_unchanged=True,HP64_schema_registered_or_installed=False,
        Battle_rule_checkpoint_supply_current_profiles_unchanged=True,HP64_native_role_authority_and_extended_wire_qualified=False,
        complete_route=False,formal_application_hosted=False)
    dump('source/storage64-and-legacy-boundary-relations.json',relations)
    facts=dict(round=ROUND,previous_goal_turn_classification='progress:157 three bounded actual storage/calculation/projection dependency investigations changed next source implementation; no routes falsely completed',
        delegated_parallel_agents=3,completed_parallel_agents=3,completed_agent_deliveries_with_source_review=4,
        checked_absolute_HP64_domains_added=1,actual_shared_HP_fields_widened=2,
        actual_HP64_repository_load_and_write_entries_added=2,actual_HP64_settlement_before_replay_guards_added=1,
        actual_legacy_checked_boundary_kinds_added=7,actual_party_complete_value_snapshot_bindings_added=1,
        source_review_definite_new_implementation_errors_found=0,actual_additive_migration_frontiers_added=1,
        modified_gameplay_source_files=11,new_tests_written=0,source_origin_records=len(records),
        HP_damage64_full_calculation_or_native_profiles_completed=False,HP64_schema_registered_or_installed=False,
        new_packet_values=0,new_native_phase_source_bindings=0,new_source_owner_chains=0,new_tw_source_owner_chains=0,new_complete_bidirectional_routes=0,
        whole_game_route_total=None,whole_game_completed_routes=None,whole_game_completion_percent=None,
        formal_application_hosted=False,actual_native_data_imported=False,actual_issuer_selected=False,
        original_native_wire_layout_changed=False,levels_changed=False,build_run=False,tests_run=False,runtime_run=False,native_execution=False,
        Cplusplus_source_run=False,Windows_API_run=False,database_access=False,deployed=False,protected_contexts=protected,remaining=REMAINING)
    dump('findings.json',facts)
    sources=sorted(paths);lp=ROOT/BOOKS[1];ledger=json.loads(lp.read_text(encoding='utf-8'))
    existing=[i for i,s in enumerate(ledger['dual_client_source_segments']) if s['name']==NAME]
    if existing and (not resume or len(existing)!=1 or ledger['dual_client_source_segments'][existing[0]]['round']!=ROUND):raise RuntimeError('Preserve prior segments')
    if existing:save('recovery/ledger-before-correction.json',lp.read_bytes())
    ledger['shared_HP_storage64_source']=dict(facts,evidence=out.relative_to(ROOT).as_posix())
    segment=dict(name=NAME,round=ROUND,
        version_scope='shared-HP64-actual-load-CAS-bind-canonical-replay-explicit-legacy-source-boundaries-no-schema-activation',
        status='Actual shared HP/maxHP64 load/write/replay and full party value snapshots connected; original native checked projections preserved, actual migration/wideBattle/native profiles pending',
        source_paths=sources,native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,tw_source_owner_chains_added=0,
        formal_application_hosted=False,complete_gameplay_routes_added=0,evidence=out.relative_to(ROOT).as_posix(),remaining=REMAINING)
    if existing:ledger['dual_client_source_segments'][existing[0]]=segment
    else:ledger['dual_client_source_segments'].append(segment)
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next_source_frontier']='Actual shared Battle/damage/HP exact64 calculation and explicit checkpoint/profile, extended role authority/native TW-CN-web recipient producer-consumer-object-display; additive migration must retain guarded53 routing/readers/opaque dependencies. Prior full-game/hosting/denominator/native frontiers remain OPEN. PHASE1.'
    lp.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (ROOT/BOOKS[0]).open('a',encoding='utf-8') as stream:
        if not existing:
            stream.write('\n\n## Actual shared HP64 storage and legacy boundaries ('+ROUND+')\n\n'
            'CharacterResources HP/maxHP64, checked absolute signed64 storage representation, actual repository uint64 load/explicit signed64 CAS bind and complete HP/MP guards before settlement canonical replay connected. '
            'Whole owner/revision/role maxima/readback/receipt/version123 preserved. Supply/manual/PK/diagnostic initialHP and role/progress/party native inputs check full values before narrowing; party snapshot retains full values before original HUD guard and independent chat readiness. '
            'Three agents plus fresh storage review retained separate before/current receipts; recipient worker authored onlytwo party files. Old migration/Application snapshot retained and currentrouting reviewed separately. '
            'Schema DWORD/mandatory role equality and Battle/rules/checkpoint/native profiles remainOPEN; do not bypass guarded53 for54 or guess dependency-dropping migration. No cap selected or level/CUSTOM/nativewire changes. '
            'New packet/phase/fullroute0, percentnull; no build/test/native/C++/Lua/API/DB/SQL/deploy. Full objective remains active.\n')
    origins=[]
    for rel in sorted(set(sources+BOOKS)):
        raw=(ROOT/rel).read_bytes();save('source/current/'+rel,raw);origins.append(dict(path=rel,bytes=len(raw),sha256=sha(raw),changed_this_round=rel not in old or old[rel]!=raw))
        if rel in old:
            patch=''.join(difflib.unified_diff(old[rel].decode('utf-8-sig').splitlines(True),raw.decode('utf-8-sig').splitlines(True),fromfile='before/'+rel,tofile='current/'+rel))
            if patch:save('diff/'+rel+'.diff',patch.encode('utf-8'))
    dump('source/source-origins.json',origins)
    print(json.dumps(dict(round=ROUND,source_paths=len(sources),protected_files=len(protected),source_records=len(records),actual_HP64_repository_load_and_write_entries_added=2,new_complete_bidirectional_routes=0)))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--resume-unsealed',action='store_true')
    main(parser.parse_args().resume_unsealed)
