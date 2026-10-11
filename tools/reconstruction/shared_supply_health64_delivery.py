"""Account actual trusted Supply/Lua64/transaction source integration; files only."""
import difflib
import hashlib
import json
from pathlib import Path
from .cn_wrapper_route_frontier import ROOT

NAME='shared-supply-health64-source-01'
ROUND='20261008-shared-supply-health64-source'
GAME=['src/game/SupplyRule.h','src/scripting/LuaEngine.cpp',
 'src/handlers/DiagnosticSupplyService.h','src/handlers/DiagnosticSupplyService.cpp']
WRITTEN=GAME+['docs/custom-designs.json','docs/research/shared-supply-health64-source-20261008.md',
 'tools/reconstruction/shared_supply_health64_delivery.py','tools/reconstruction/dual_client_route_catalog.py']
BOOKS=['docs/PACKET_CONNECTION_GOAL_20261006.md',
 'artifacts/integration/packet-connections-20261006/packet-route-ledger.json']
REMAINING=[
 'Exact wide Supply inherits unchanged CUSTOM0016 and existing0050 amounts; CUSTOM0091 is not an official formula, native CN permission or activated native TW-CN-web route.',
 'Actual default factories remain LegacyCustom; native wide producer/consumer/object/display, extended persistent policy/schema recovery and native data still require bindings.',
 'Existing role maxHP DWORD equality and schema CHECK are retained; wide source projection is not activated wide save support.',
 'M2 controllers are created before listeners start; defer actual Directory assembly until account preparation. Real rights, summaries and world Reserve owners remain required before Main source selection.',
 'Full accounts/admission/world/hosting/denominator, all mutation/settlement/profile paths, later comprehensive builds/tests/repairs/recovery/playable release remain required.']

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
 if len(before)!=930:raise RuntimeError('Expected930 before originals')
 excluded=set(WRITTEN+BOOKS)|{f'artifacts/integration/packet-connections-20261006/packet-progress-latest.{x}' for x in ['json','md']}
 protected=[]
 for row in before:
  if row['path'] not in excluded:
   if (ROOT/row['path']).read_bytes()!=old[row['path']]:raise RuntimeError('Protected source differs: '+row['path'])
   protected.append(row)
 for name,pin in [('shared-battle-lua64-source-01','96fda3b75e62d825fcb9518c078d6a5cf3db3271028c35c73bcc4e2fad529d85'),
                  ('endpoint-catalog160','d4b7eb2184148d6c3aea9b68a862eab458ab0d1ca073372a5abd2d18dd8bdef3')]:
  raw=(out/'retained-prior'/name/'manifest.json').read_bytes()
  if sha(raw)!=pin or (base/name/'manifest.json').read_bytes()!=raw:raise RuntimeError('Prior160 seal differs')
 paths=set(WRITTEN);agents=[];records=[]
 for name in ['exact-supply64','supply-transaction-projection','supply-provenance-hosting']:
  folder=out/'agents'/name
  seal_path=folder/'seal.json'
  findings_path=folder/'findings.json'
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
 if len(prior_registry['designs'])!=88 or len(registry['designs'])!=89 or registry['designs'][:88]!=prior_registry['designs'] or registry['designs'][-1]['id']!='CUSTOM-0091':
  raise RuntimeError('Preserve existing88 design records; only0091 append allowed')
 for key in prior_registry:
  if key!='designs' and registry[key]!=prior_registry[key]:raise RuntimeError('Preserve registry metadata')
 dump('parallel-agent-deliveries.json',agents);dump('source/reviewed-current-source-records.json',records)
 relations=dict(source_only=True,design_id='CUSTOM-0091',native_formula=False,
  actual_profile_callback_bindings=['DiagnosticSupplyService::Policy -> SupplyInput -> LuaEngine::supply'],
  actual_exact_Lua64_entries=['LuaEngine::supply ExtendedHealth64'],
  exact_integer_boundary='Lua5.4 signed64; actual lua_isinteger/lua_Integer, stack restored, checked nonnegative range before unsigned conversion',
  new_wide_return_uses_double=False,new_wide_inputs_explicit_lua_Integer=True,
  existing_module='scripts/gameplay/supply.lua',supply_module_unchanged=True,
  inherited_supply_rule='CUSTOM0016 hp+min(restore,maximum-current); dead non-revival, consume only on resource change',
  HP_maxHP_restoreHP='uint64 admitted only through nonnegative signed64 Lua domain',MP_domain='existing uint32 and signed32 Lua bounds',
  trusted_Policy_numeric_profile_default='LegacyCustom',unknown_profile_rejected_before_decoder=True,
  Extended_requires_trusted_pure_full_value_projector=True,Legacy_with_projector_rejected=True,
  actual_projection_before_CAS=True,projection_nonempty_and_bounded=True,
  frame_scope='existing recovered TW zero-seed native26; no new CN frame qualification',
  legacy_inventory_and_RoleVitals_order_unchanged=True,
  original_baseline_inventory_resource_and_pending_battle_CAS_unchanged=True,
  current_policy_factories_unchanged_and_Legacy=True,
  M2_controller_factory_called_before_listener_start=True,
  M2_registry_observe_unavailable_before_start=True,
  M2_actual_directory_must_be_deferred_until_account_prepare=True,
  M2_real_rights_summary_world_Reserve_owners_and_Main_selection_open=True,
  Application_PK_diagnostic_admission_unchanged=True,actual_native_data_imported=False,
  HP_damage_experience_gameplay_caps=None,coin_cap_applied_to_other_fields=False,levels_changed=False,
  HP64_schema_activated=False,native_web_numeric_profiles_activated=False,
  complete_route=False,formal_application_hosted=False,parallel_agent_findings=[x['findings'] for x in agents])
 dump('source/supply-health64-relations.json',relations)
 facts=dict(round=ROUND,previous_goal_turn_classification='progress:160 actual Battle profile/exact Lua64 damage-revival/trusted binding preserved in immutable seals',
  completed_parallel_agents=3,actual_exact_Lua64_entries_added=1,actual_profile_callback_bindings_added=1,
  actual_projected_atomic_supply_entries_added=1,actual_M2_lifetime_dependency_frontiers_reviewed=1,
  actual_arithmetic_provenance_records_added=1,modified_gameplay_source_files=len(GAME),source_origin_records=len(records),
  HP_damage64_full_native_profiles_completed=False,HP64_schema_registered_or_installed=False,
  new_packet_values=0,new_native_phase_source_bindings=0,new_source_owner_chains=0,new_tw_source_owner_chains=0,
  new_complete_bidirectional_routes=0,whole_game_route_total=None,whole_game_completed_routes=None,whole_game_completion_percent=None,
  formal_application_hosted=False,levels_changed=False,original_native_wire_layout_changed=False,
  build_run=False,tests_run=False,new_tests_written=0,runtime_run=False,native_execution=False,
  Cplusplus_source_run=False,Windows_API_run=False,database_access=False,deployed=False,protected_contexts=protected,remaining=REMAINING)
 dump('findings.json',facts)
 ledger_path=ROOT/BOOKS[1];ledger=json.loads(ledger_path.read_text(encoding='utf-8'))
 if len(ledger['dual_client_source_segments'])!=152 or any(x['name']==NAME for x in ledger['dual_client_source_segments']):
  raise RuntimeError('Preserve152 existing segments; fresh round required')
 sources=sorted(paths);ledger['shared_Supply_HP64_source']=dict(facts,evidence=out.relative_to(ROOT).as_posix())
 ledger['dual_client_source_segments'].append(dict(name=NAME,round=ROUND,
  version_scope='shared-explicit-Supply-profile-exact-Lua64-inherited-custom-headroom-and-projected-CAS-no-native-promotion',
  status='Actual Supply HP64 input/exact Lua64/trusted bounded reply before atomic inventory-resource CAS connected; native rules/admission/persistence/full TW-CN-web profiles pending',
  source_paths=sources,native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,tw_source_owner_chains_added=0,
  formal_application_hosted=False,complete_gameplay_routes_added=0,evidence=out.relative_to(ROOT).as_posix(),remaining=REMAINING))
 plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
 plan['next_source_frontier']='M2 actual deferred stored-account Directory bridge after listener start, real entitlement/summary/world Reserve providers before Main selection; all extended mutation/settlement/persistent policy/schema recovery and TW-CN-web producer-consumer-object-floatingtext. Full-game denominator/guarded53 remain OPEN. PHASE1.'
 ledger_path.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 with (ROOT/BOOKS[0]).open('a',encoding='utf-8') as f:
  f.write('\n\n## Actual Supply HP64 and projected atomic source ('+ROUND+')\n\n'
   'Supply HP/maxHP/restoreHP widened, explicit ExtendedHealth64 uses exact Lua integers through unchanged CUSTOM0016 supply.lua. MP retains old signed32 bounds; actual known profile propagated from trusted Policy. '
   'Legacy bytes/order retained; Extended needs pure full-value bounded logical projection before existing atomic inventory/resources CAS. Current factories remain LegacyCustom; role maxHP DWORD/schema constraints retained. '
   'CUSTOM0091 appended preserving88 designs and metadata. No new recovery amounts, items, native formulas, CN framing or activated native wide profile. '
   'M2 actual factory-before-listener-start dependency requires deferred directory construction during account preparation; real rights/world providers and Main selection remainOPEN. '
   'Actual4 gameplay source files plus registry changed, three bounded agent deliveries. New packet/phase/fullroute0, percentage null, no builds/tests/native/API/Lua/DB/migration/deploy. Full objective remains active.\n')
 origins=[]
 for rel in sorted(paths|set(BOOKS)):
  raw=(ROOT/rel).read_bytes();save('source/current/'+rel,raw);origins.append(dict(path=rel,bytes=len(raw),sha256=sha(raw),changed_this_round=rel not in old or old[rel]!=raw))
  if rel in old:
   diff=''.join(difflib.unified_diff(old[rel].decode('utf-8-sig').splitlines(True),raw.decode('utf-8-sig').splitlines(True),fromfile='before/'+rel,tofile='current/'+rel))
   if diff:save('diff/'+rel+'.diff',diff.encode('utf-8'))
 dump('source/source-origins.json',origins)
 print(json.dumps(dict(round=ROUND,source_paths=len(sources),protected_files=len(protected),source_origin_records=len(records),modified_gameplay_files=len(GAME),new_complete_routes=0)))

if __name__=='__main__':main()
