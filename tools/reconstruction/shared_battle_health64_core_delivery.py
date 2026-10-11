"""Retain real Battle HP64 source changes and bounded agent receipts; files only."""
import difflib
import hashlib
import json
from pathlib import Path
from .cn_wrapper_route_frontier import ROOT

NAME='shared-battle-health64-core-source-01'
ROUND='20261008-shared-battle-health64-core-source'
GAME=['src/game/Battle.h','src/game/Battle.cpp','src/game/CombatRule.h',
 'src/game/RevivalRule.h','src/game/ExtendedHealthAmount.h','src/game/BattleCheckpointCodec.cpp',
 'src/scripting/LuaEngine.cpp','src/core/Application.cpp','src/db/SqliteRecoveredCharacterRepository.cpp',
 'src/db/SqliteOwnedPkRoomRepository.cpp','src/protocol/DiagnosticBattleParticipants.h',
 'src/protocol/RecoveredBattleAttackPresentation.h','src/protocol/RecoveredBattleBootstrap.h',
 'src/protocol/ShunyingSanshazhanReply.h','src/protocol/DiagnosticShunyingManual.h',
 'src/protocol/ThousandBullsReply.h','src/protocol/DiagnosticBattleRevival.h',
 'src/protocol/RecoveredPkActionProjection.h']
WRITTEN=GAME+['docs/research/shared-battle-health64-core-source-20261008.md',
 'tools/reconstruction/shared_battle_health64_core_delivery.py','tools/reconstruction/dual_client_route_catalog.py']
BOOKS=['docs/PACKET_CONNECTION_GOAL_20261006.md',
 'artifacts/integration/packet-connections-20261006/packet-route-ledger.json']
REMAINING=[
 'Explicit HP64 Battle operations and version2 storage codec are source capabilities, not actual native/client/Web numeric profile activation or complete routes.',
 'Actual existing Battle constructors remain LegacyCustom; diagnostic-v1 and PK read/write policies stay v1Legacy. Extended admission/role authority/persistence policy must be connected.',
 'Exact wide Lua combat/revival/Supply/native rules, schema additive routing and guarded53 preservation, recovery and native TW-CN-web producer/consumer/object/floatingtext remain OPEN.',
 'MP and dual attack/defense/skill percentages remain original widths/CUSTOM bounds; coin cap only99999999999 and native levels unchanged; no HP/damage/EXP gameplay cap selected.',
 'Full accounts/admission/world/hosting/denominator and all gameplay source connections, comprehensive later builds/tests/repair/recovery/playable release remain required.']

def sha(raw):return hashlib.sha256(raw).hexdigest()

def main():
 base=ROOT/'artifacts/integration/packet-connections-20261006';out=base/NAME
 if not (out/'before-manifest.json').exists() or (out/'findings.json').exists() or (out/'manifest.json').exists():
  raise RuntimeError('Fresh unaccounted source round required')
 def save(rel,raw):
  p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
  with p.open('xb') as f:f.write(raw)
 def dump(rel,value):save(rel,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
 before=json.loads((out/'before-manifest.json').read_text(encoding='utf-8'));old={}
 for row in before:
  raw=(out/row['snapshot']).read_bytes()
  if len(raw)!=row['bytes'] or sha(raw)!=row['sha256']:raise RuntimeError('Before receipt differs')
  old[row['path']]=raw
 if len(before)!=924:raise RuntimeError('Expected924 before originals')
 excluded=set(WRITTEN+BOOKS)|{f'artifacts/integration/packet-connections-20261006/packet-progress-latest.{x}' for x in ['json','md']}
 protected=[]
 for row in before:
  if row['path'] not in excluded:
   if (ROOT/row['path']).read_bytes()!=old[row['path']]:raise RuntimeError('Protected source differs: '+row['path'])
   protected.append(row)
 for name,pin in [('shared-hp-storage64-source-01','3ddedcddbac01337f42bf40e5553eb62de08ca59d5b2059853cdeb99c1951620'),
                  ('endpoint-catalog158','9f93a4f87d6589d87ba131fcf60fa11a2c6342dfe2105a246e1c80ad91fc3f5e')]:
  raw=(out/'retained-prior'/name/'manifest.json').read_bytes()
  if sha(raw)!=pin or (base/name/'manifest.json').read_bytes()!=raw:raise RuntimeError('Prior158 seal differs')
 paths=set(WRITTEN);agents=[];records=[]
 for name in ['checkpoint-profile','lua-calculation-boundaries','recipient-health64-boundaries']:
  folder=out/'agents'/name
  seal=json.loads((folder/'seal.json').read_text(encoding='utf-8-sig'))
  for row in seal.get('files',seal.get('entries',[])):
   raw=(folder/row['path']).read_bytes()
   if len(raw)!=row['bytes'] or sha(raw)!=row['sha256']:raise RuntimeError('Agent seal differs')
  current=json.loads((folder/'current-source-origins.json').read_text(encoding='utf-8-sig'))
  if isinstance(current,dict):current=current['source_files']
  if not isinstance(current,list) or not current:raise RuntimeError('Final-current source list required')
  for row in current:
   p=Path(row['path']);p=p if p.is_absolute() else ROOT/p;rel=p.relative_to(ROOT).as_posix()
   if rel.startswith('artifacts/'):raise RuntimeError('Receipt path is not an original source: '+rel)
   raw=(folder/row['copy']).read_bytes()
   if len(raw)!=row['bytes'] or sha(raw)!=row['sha256'] or p.read_bytes()!=raw:
    raise RuntimeError('Final-current source copy differs: '+rel)
   paths.add(rel);records.append(dict(folder=folder.relative_to(out).as_posix(),epoch='final-current',path=rel,source=row))
  agents.append(dict(agent=name,seal_sha256=sha((folder/'seal.json').read_bytes()),
    findings=json.loads((folder/'findings.json').read_text(encoding='utf-8-sig')),
    current_source_origins=current,files=[dict(path=p.relative_to(folder).as_posix(),bytes=p.stat().st_size,sha256=sha(p.read_bytes())) for p in sorted(folder.rglob('*')) if p.is_file()]))
 for rel in GAME:
  if rel not in old or old[rel]==(ROOT/rel).read_bytes():raise RuntimeError('Actual gameplay change required: '+rel)
 dump('parallel-agent-deliveries.json',agents);dump('source/reviewed-current-source-records.json',records)
 relations=dict(source_only=True,actor_HP_maxHP='uint64',MP_stats_percentages='unchanged uint32',
  damage_loss_revival_HP='uint64 within nonnegative signed64 representation',
  explicit_profiles=['LegacyCustom','ExtendedHealth64'],existing_constructor_default='LegacyCustom',
  actual_extended_operations=['Battle::act','Battle::revive'],
  signed_delta_apply='ExtendedHealthAmount::apply uses ExtendedBattleDeltaAmount magnitude and bounded headroom; no overflowing intermediate',
  native_DWORD_bitmath='original operations onlyLegacyCustom; apply_native_deltas rejectsExtendedHealth64',
  staged_snapshot_rng_encoder_before_noexcept_commit=True,
  checkpoint_v1_original_nine_keys_preserved=True,checkpoint_v2_explicit_tag='extended-health64',
  original_checkpoint_compatibility='static source inference, not executed proof',
  actual_diagnostic_and_PK_read_write_policy_remains_v1Legacy=True,
  actual_numeric_profile_invariance_before_after=True,
  Lua_combat_revival_original_formula_and_bounds=True,Lua_full_wide_formula=False,
  actual_native_DWORD_writers_check_full_uint64_before_projection=True,
  actual_native_short_damage_helper_inputs_uint64_before_bounds=True,
  Application_raw_HP_writer_sites_checked=3,
  original_wire_layout_changed=False,HP64_schema_activated=False,native_web_numeric_profiles_activated=False,
  complete_route=False,formal_application_hosted=False,parallel_agent_findings=[x['findings'] for x in agents])
 dump('source/battle-health64-core-relations.json',relations)
 facts=dict(round=ROUND,previous_goal_turn_classification='progress:158 actual HP64 storage/boundary source changes and immutable final source/catalog seals',
  completed_parallel_agents=3,actual_extended_health_operation_paths_added=2,
  actual_extended_checkpoint_profiles_added=1,actual_legacy_Application_HP_writer_sites_checked=3,
  modified_gameplay_source_files=len(GAME),source_origin_records=len(records),
  HP_damage64_full_calculation_or_native_profiles_completed=False,
  HP64_schema_registered_or_installed=False,new_packet_values=0,new_native_phase_source_bindings=0,
  new_source_owner_chains=0,new_tw_source_owner_chains=0,new_complete_bidirectional_routes=0,
  whole_game_route_total=None,whole_game_completed_routes=None,whole_game_completion_percent=None,
  formal_application_hosted=False,levels_changed=False,original_native_wire_layout_changed=False,
  build_run=False,tests_run=False,new_tests_written=0,runtime_run=False,native_execution=False,
  Cplusplus_source_run=False,Windows_API_run=False,database_access=False,deployed=False,
  protected_contexts=protected,remaining=REMAINING)
 dump('findings.json',facts)
 ledger_path=ROOT/BOOKS[1];ledger=json.loads(ledger_path.read_text(encoding='utf-8'))
 if len(ledger['dual_client_source_segments'])!=150 or any(x['name']==NAME for x in ledger['dual_client_source_segments']):
  raise RuntimeError('Preserve existing150 segments; this round must be fresh')
 sources=sorted(paths)
 ledger['shared_Battle_health64_core_source']=dict(facts,evidence=out.relative_to(ROOT).as_posix())
 ledger['dual_client_source_segments'].append(dict(name=NAME,round=ROUND,
  version_scope='shared-Battle-HP64-act-revive-checkpoint-explicit-profile-legacy-wire-checked-source',
  status='Actual shared HP64 Battle operations and explicit checkpoint v2 connected in source; native profile, wide rules, authority and migration remain OPEN',
  source_paths=sources,native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,
  tw_source_owner_chains_added=0,formal_application_hosted=False,complete_gameplay_routes_added=0,
  evidence=out.relative_to(ROOT).as_posix(),remaining=REMAINING))
 plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
 plan['next_source_frontier']='Exact wide Lua/native rules and shared role authority/profile admission/schema recovery, TW-CN-web numeric producer-consumer-object-floatingtext; old guarded53 migration and full-game/hosting/denominator frontiers remain OPEN. PHASE1.'
 ledger_path.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 with (ROOT/BOOKS[0]).open('a',encoding='utf-8') as f:
  f.write('\n\n## Shared Battle HP64 core source ('+ROUND+')\n\n'
   'Battle actor HP/maxHP, damage/loss and revival input/output carry64-bit exact values. Explicit ExtendedHealth64 profile connects signed loss/healing arithmetic and staged act/revive; LegacyCustom default preserves prior limits/native DWORD behavior. '
   'Checkpoint v1 unchanged shape and v2 explicit profile tag, strict restore/canonical/runtime identity; diagnostic and PK reader/writer admission stays v1Legacy with profile invariance. '
   'Original bounded Lua formulas, MP/stats/levels/wire preserve; full native/WSS/web numeric profile, exact wide rules, role authority and additive recoverable schema remainOPEN. '
   'Three bounded agent deliveries retained real before/current sources and late observation copies. Actual18 gameplay files modified; no opcode/phase/fullroute added, percentage null. No build/tests/native/API/Lua/DB/migration/deploy. Full goal remains active.\n')
 origins=[]
 for rel in sorted(paths|set(BOOKS)):
  raw=(ROOT/rel).read_bytes();save('source/current/'+rel,raw)
  origins.append(dict(path=rel,bytes=len(raw),sha256=sha(raw),changed_this_round=rel not in old or old[rel]!=raw))
  if rel in old:
   diff=''.join(difflib.unified_diff(old[rel].decode('utf-8-sig').splitlines(True),raw.decode('utf-8-sig').splitlines(True),fromfile='before/'+rel,tofile='current/'+rel))
   if diff:save('diff/'+rel+'.diff',diff.encode('utf-8'))
 dump('source/source-origins.json',origins)
 print(json.dumps(dict(round=ROUND,source_paths=len(sources),protected_files=len(protected),source_origin_records=len(records),modified_gameplay_files=len(GAME),new_complete_routes=0)))

if __name__=='__main__':main()
