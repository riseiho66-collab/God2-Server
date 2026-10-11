"""Account actual explicit Battle/Lua64/profile source integration; files only."""
import difflib
import hashlib
import json
from pathlib import Path
from .cn_wrapper_route_frontier import ROOT

NAME='shared-battle-lua64-source-01'
ROUND='20261008-shared-battle-lua64-source'
GAME=['src/game/BattleNumericProfile.h','src/game/Battle.h','src/game/Battle.cpp',
 'src/game/CombatRule.h','src/game/RevivalRule.h','src/scripting/LuaEngine.cpp',
 'scripts/gameplay/combat_health64.lua','src/handlers/RecoveredBattleService.h',
 'src/handlers/RecoveredBattleService.cpp']
WRITTEN=GAME+['docs/custom-designs.json','docs/research/shared-battle-lua64-source-20261008.md',
 'tools/reconstruction/shared_battle_lua64_delivery.py','tools/reconstruction/dual_client_route_catalog.py']
BOOKS=['docs/PACKET_CONNECTION_GOAL_20261006.md',
 'artifacts/integration/packet-connections-20261006/packet-route-ledger.json']
REMAINING=[
 'Exact Lua64 inherited custom-rule arithmetic and trusted matching profile are source capabilities, not official formulas, native CN permission or activated native TW-CN-web routes.',
 'Application, PK and diagnostic admission remain LegacyCustom; owner/role/monster/native skill data, extended persistent policy/schema recovery and native wire/object/display still require actual bindings.',
 'Original native damage/defense/critical and revival execution remain unqualified; CUSTOM0090 is separately labeled and not a substitute for native recovery.',
 'Exact wide Supply and all owned mutation/settlement/storage/profile paths, additive guarded53 migration preserving unknown dependencies and save recovery remain OPEN.',
 'Full accounts/admission/world/hosting/denominator and every gameplay connection, later comprehensive builds/tests/repairs/recovery/playable release remain required.']

def sha(raw):return hashlib.sha256(raw).hexdigest()

def main():
 base=ROOT/'artifacts/integration/packet-connections-20261006';out=base/NAME
 if not (out/'before-manifest.json').exists() or (out/'findings.json').exists() or (out/'manifest.json').exists():
  raise RuntimeError('Fresh unaccounted round required')
 def save(rel,raw):
  p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
  with p.open('xb') as f:f.write(raw)
 def dump(rel,value):save(rel,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
 before=json.loads((out/'before-manifest.json').read_text(encoding='utf-8'));old={}
 for row in before:
  raw=(out/row['snapshot']).read_bytes()
  if len(raw)!=row['bytes'] or sha(raw)!=row['sha256']:raise RuntimeError('Before receipt differs')
  old[row['path']]=raw
 if len(before)!=926:raise RuntimeError('Expected926 before originals')
 excluded=set(WRITTEN+BOOKS)|{f'artifacts/integration/packet-connections-20261006/packet-progress-latest.{x}' for x in ['json','md']}
 protected=[]
 for row in before:
  if row['path'] not in excluded:
   if (ROOT/row['path']).read_bytes()!=old[row['path']]:raise RuntimeError('Protected source differs: '+row['path'])
   protected.append(row)
 for name,pin in [('shared-battle-health64-core-source-01','dd36b46ab12505825e8b5073e1411a9d12ea3c0a0cded06a67adb885a070dfa3'),
                  ('endpoint-catalog159','30160c26c6bdaafe7614de2bcc3e0e94f4106211ad61f07d8f11fd192c5a0cae')]:
  raw=(out/'retained-prior'/name/'manifest.json').read_bytes()
  if sha(raw)!=pin or (base/name/'manifest.json').read_bytes()!=raw:raise RuntimeError('Prior159 seal differs')
 paths=set(WRITTEN);agents=[];records=[]
 for name in ['exact-lua64','trusted-profile-binding','arithmetic-provenance']:
  folder=out/'agents'/name
  seal_path=folder/('final-seal.json' if name=='exact-lua64' else 'seal.json')
  findings_path=folder/('corrected-findings.json' if name=='exact-lua64' else 'findings.json')
  seal=json.loads(seal_path.read_text(encoding='utf-8-sig'))
  rows=seal.get('files',seal.get('entries',[]))
  if not rows:raise RuntimeError('Missing agent seal entries')
  for row in rows:
   raw=(folder/row['path']).read_bytes()
   if len(raw)!=row['bytes'] or sha(raw)!=row['sha256']:raise RuntimeError('Agent seal differs')
  current=json.loads((folder/'current-source-origins.json').read_text(encoding='utf-8-sig'))
  if isinstance(current,dict):current=current['source_files']
  if not isinstance(current,list) or not current:raise RuntimeError('Final-current source list required')
  for row in current:
   p=Path(row['path']);p=p if p.is_absolute() else ROOT/p;rel=p.relative_to(ROOT).as_posix()
   if rel.startswith('artifacts/'):raise RuntimeError('Receipt path is not an original source')
   raw=(folder/row['copy']).read_bytes()
   if len(raw)!=row['bytes'] or sha(raw)!=row['sha256'] or p.read_bytes()!=raw:
    raise RuntimeError('Final-current source copy differs: '+rel)
   paths.add(rel);records.append(dict(folder=folder.relative_to(out).as_posix(),epoch='final-current',path=rel,source=row))
  agents.append(dict(agent=name,seal_file=seal_path.name,seal_sha256=sha(seal_path.read_bytes()),
    findings_file=findings_path.name,findings=json.loads(findings_path.read_text(encoding='utf-8-sig')),
    current_source_origins=current,files=[dict(path=p.relative_to(folder).as_posix(),bytes=p.stat().st_size,sha256=sha(p.read_bytes())) for p in sorted(folder.rglob('*')) if p.is_file()]))
 for rel in GAME:
  if rel in old and old[rel]==(ROOT/rel).read_bytes():raise RuntimeError('Actual gameplay change required: '+rel)
 prior_registry=json.loads(old['docs/custom-designs.json']);registry=json.loads((ROOT/'docs/custom-designs.json').read_text(encoding='utf-8'))
 if len(prior_registry['designs'])!=87 or len(registry['designs'])!=88 or registry['designs'][:87]!=prior_registry['designs'] or registry['designs'][-1]['id']!='CUSTOM-0090':
  raise RuntimeError('Preserve existing87 design records; only0090 append allowed')
 for key in prior_registry:
  if key!='designs' and registry[key]!=prior_registry[key]:raise RuntimeError('Preserve registry metadata')
 dump('parallel-agent-deliveries.json',agents);dump('source/reviewed-current-source-records.json',records)
 relations=dict(source_only=True,design_id='CUSTOM-0090',native_formula=False,
  explicit_numeric_profile_shared_header=True,actual_profile_callback_bindings=['Battle::act -> CombatRuleInput','Battle::revive -> RevivalInput'],
  actual_exact_Lua64_entries=['LuaEngine::combat_damage ExtendedHealth64','LuaEngine::revival ExtendedHealth64'],
  exact_integer_boundary='Lua5.4 signed64; actual lua_isinteger/lua_Integer, stack restored, checked nonnegative range before unsigned conversion',
  new_wide_return_uses_double=False,new_wide_inputs_explicit_lua_Integer=True,
  extended_module='scripts/gameplay/combat_health64.lua',old_combat_and_revival_modules_unchanged=True,
  inherited_damage_order='CUSTOM0006 scaled attack/defense floors, minimum1, critical predicate and floor order',
  extended_final_1m_clip=False,legacy_1m_clip_preserved=True,
  maximum_combat_intermediate_product=429496729500000,
  extended_stats='uint32 representation only; no native stat data inferred',MP_and_percent_limits_unchanged=True,
  extended_revival='unchanged CUSTOM0017 HP1/MP66, target maxHP exact nonnegative signed64',
  trusted_Policy_numeric_profile_default='LegacyCustom',bind_requires_known_equal_Battle_and_Policy_profiles=True,
  Application_PK_diagnostic_admission_unchanged=True,actual_native_data_imported=False,
  HP_damage_experience_gameplay_caps=None,coin_cap_applied_to_other_fields=False,levels_changed=False,
  HP64_schema_activated=False,native_web_numeric_profiles_activated=False,
  complete_route=False,formal_application_hosted=False,parallel_agent_findings=[x['findings'] for x in agents])
 dump('source/battle-lua64-relations.json',relations)
 facts=dict(round=ROUND,previous_goal_turn_classification='progress:159 actual Battle64 act/revive, checkpoint v2 and recipient/policy source modifications preserved in immutable seals',
  completed_parallel_agents=3,actual_exact_Lua64_entries_added=2,actual_profile_callback_bindings_added=2,
  actual_trusted_profile_bind_checks_added=1,actual_exact_Lua64_modules_added=1,
  actual_arithmetic_provenance_records_added=1,modified_gameplay_source_files=len(GAME),source_origin_records=len(records),
  HP_damage64_full_native_profiles_completed=False,HP64_schema_registered_or_installed=False,
  new_packet_values=0,new_native_phase_source_bindings=0,new_source_owner_chains=0,new_tw_source_owner_chains=0,
  new_complete_bidirectional_routes=0,whole_game_route_total=None,whole_game_completed_routes=None,whole_game_completion_percent=None,
  formal_application_hosted=False,levels_changed=False,original_native_wire_layout_changed=False,
  build_run=False,tests_run=False,new_tests_written=0,runtime_run=False,native_execution=False,
  Cplusplus_source_run=False,Windows_API_run=False,database_access=False,deployed=False,protected_contexts=protected,remaining=REMAINING)
 dump('findings.json',facts)
 ledger_path=ROOT/BOOKS[1];ledger=json.loads(ledger_path.read_text(encoding='utf-8'))
 if len(ledger['dual_client_source_segments'])!=151 or any(x['name']==NAME for x in ledger['dual_client_source_segments']):
  raise RuntimeError('Preserve151 existing segments; fresh round required')
 sources=sorted(paths);ledger['shared_Battle_Lua64_source']=dict(facts,evidence=out.relative_to(ROOT).as_posix())
 ledger['dual_client_source_segments'].append(dict(name=NAME,round=ROUND,
  version_scope='shared-explicit-Battle-profile-exact-Lua64-inherited-custom-arithmetic-no-native-promotion',
  status='Actual profile callback propagation/exact Lua64 damage-revival/trusted matching binding source connected; native rules, admission, persistence and full TW-CN-web profiles pending',
  source_paths=sources,native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,tw_source_owner_chains_added=0,
  formal_application_hosted=False,complete_gameplay_routes_added=0,evidence=out.relative_to(ROOT).as_posix(),remaining=REMAINING))
 plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
 plan['next_source_frontier']='Native-qualified rules and shared authority/admission/persistent extended profile/schema recovery; exact Supply and TW-CN-web native producer-consumer-object-floatingtext. Full-game/hosting/denominator and guarded53 native source frontiers remain OPEN. PHASE1.'
 ledger_path.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 with (ROOT/BOOKS[0]).open('a',encoding='utf-8') as f:
  f.write('\n\n## Actual explicit Battle profile and exact Lua64 source ('+ROUND+')\n\n'
   'Shared profile header and actual act/revive callback propagation connected; ExtendedHealth64 uses exact Lua integer inputs/returns and inherited custom formula integer floors in separately labeled CUSTOM0090. '
   'LegacyCustom modules/caps retained; new trusted Policy profile must match Battle before binding. No inferred official formulas, skills/stats, native CN custom permission or client numeric profile. '
   'Registry0090 appended without changing prior87 records. Application/PK/diagnostic/schema/native wire unchanged and full admission/authority/persistence/native/web display remainOPEN. '
   'Actual9 gameplay source files plus provenance registry changed, three actual bounded agent deliveries. New packet/phase/fullroute0, percentage null, no builds/tests/native/API/Lua/DB/migration/deploy. Full objective remains active.\n')
 origins=[]
 for rel in sorted(paths|set(BOOKS)):
  raw=(ROOT/rel).read_bytes();save('source/current/'+rel,raw);origins.append(dict(path=rel,bytes=len(raw),sha256=sha(raw),changed_this_round=rel not in old or old[rel]!=raw))
  if rel in old:
   diff=''.join(difflib.unified_diff(old[rel].decode('utf-8-sig').splitlines(True),raw.decode('utf-8-sig').splitlines(True),fromfile='before/'+rel,tofile='current/'+rel))
   if diff:save('diff/'+rel+'.diff',diff.encode('utf-8'))
 dump('source/source-origins.json',origins)
 print(json.dumps(dict(round=ROUND,source_paths=len(sources),protected_files=len(protected),source_origin_records=len(records),modified_gameplay_files=len(GAME),new_complete_routes=0)))

if __name__=='__main__':main()
