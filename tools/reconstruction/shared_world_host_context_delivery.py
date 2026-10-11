"""Static file/source accounting only; never executes game/native/SQL/tests."""
import copy
import difflib
import json
from pathlib import Path
import sys
from .parallel_game_connection_frontier_delivery import ROOT, sha, read, save, dump, matches, inventory

BASE=ROOT/'artifacts/integration/packet-connections-20261006'
NAME='shared-world-host-context-source-01'
ROUND='20261008-shared-world-host-context-source'
OUT=BASE/NAME
CAT=BASE/'endpoint-catalog166'
DOC='docs/research/shared-world-host-context-source-20261008.md'
GAME=['src/game/SharedWorldHost.h','src/game/SharedWorldHost.cpp',
      'src/cn/net/SharedCredentialServer.h','src/cn/net/SharedCredentialServer.cpp',
      'src/core/Application.h','src/core/Application.cpp','src/core/SharedWorldHostPlan.h',
      'src/protocol/RecoveredBattleAction08Control.h','src/net/Session.h','src/net/Session.cpp']
WRITTEN=GAME+[DOC,'tools/reconstruction/shared_world_host_context_delivery.py',
              'tools/reconstruction/dual_client_route_catalog.py']
BOOKS=['docs/PACKET_CONNECTION_GOAL_20261006.md',
       'artifacts/integration/packet-connections-20261006/packet-route-ledger.json']
AGENTS=['common-context','application-world-host','action08-control']
PINS={'tw-battle-state-source-01':
      '57396aecd94c63fb6805d765ebc1969227791dcb631f7c064bfa38575ac5c6b0',
      'endpoint-catalog165':'0c868aa13a51a4603ca1e9dd1baf98a4e9721f95228c83d90665f6b6243f0820'}
NATIVE_INPUT='artifacts/research/enemy-blackbox-20261006/consumer-experiment/inputs/native-image.bin'
EVIDENCE_INPUTS={NATIVE_INPUT,
 'artifacts/integration/packet-connections-20261006/s2c-battle83-action-frontier-v1.json',
 'artifacts/integration/packet-connections-20261006/tw-battle-state-source-01/agents/actor-control/findings.json',
 'artifacts/integration/packet-connections-20261006/tw-battle-state-source-01/agents/actor-control/capture_native.py'}
REMAINING=[
 'Actual Taiwan Entered/world-scene owner and persisted position/revision/full native entry/5D/recipient6F-5E-73 must still be supplied; candidate frames are not qualified by a shared host.',
 'CN actual controllers must consume the supplied same common context for real world publishers; native account issuer/rights/catalog/summary/world Reservation remain open.',
 'Ordinary Main still has not selected the explicit world plan or CN native factory; no live shared registry/gameplay is claimed.',
 'Native battle08 field view lacks original authority/prototype producer, full state/queue/lifetime and formal emitter; no native C2S pairing is inferred.',
 'Wide numeric persistent profiles/recovery/TW-CN-web wire-object-display and stack99 mutation callers plus whole-game denominator/full routes/later testing-repair-release remain open.']

def reports():
 return [BASE/'packet-progress-latest.json',BASE/'packet-progress-latest.md',
         BASE/'round-reports'/(ROUND+'.json'),BASE/'round-reports'/(ROUND+'.md')]

def before():
 p=OUT/'before-manifest.json'
 if sha(p.read_bytes())!='6b53a53a6e4866fc28339f82796c8f2b7f104c95d651a7537054560d15ccabf5':
  raise RuntimeError('Preserve original before952 inventory')
 rows=read(p)
 if len(rows)!=952 or len({r['path'] for r in rows})!=952:raise RuntimeError('Before952 required')
 return rows,{r['path']:matches(OUT/r['snapshot'],r) for r in rows}

def prior():
 total=0
 for name,pin in PINS.items():
  raw=(BASE/name/'manifest.json').read_bytes()
  if sha(raw)!=pin or (OUT/'retained-prior'/name/'manifest.json').read_bytes()!=raw:
   raise RuntimeError('Immutable prior165 manifest changed')
  for row in json.loads(raw)['files']:matches(BASE/name/row['path'],row);total+=1
 if total!=1812:raise RuntimeError('Entire prior1812 inventory required')

def protected(rows,old):
 excluded=set(WRITTEN+BOOKS)|{p.relative_to(ROOT).as_posix() for p in reports()[:2]}
 result=[r for r in rows if r['path'] not in excluded]
 if len(result)!=941:raise RuntimeError('Protected941 required')
 for row in result:
  if (ROOT/row['path']).read_bytes()!=old[row['path']]:raise RuntimeError('Protected source changed: '+row['path'])
 return result

def agent_records():
 deliveries=[];paths=set();records=[]
 for name in AGENTS:
  folder=OUT/'agents'/name;seal=read(folder/'seal.json')
  entries=seal.get('files',seal.get('entries',[]))
  if not entries:raise RuntimeError('Agent full seal required')
  for row in entries:matches(folder/row['path'],row)
  actual=inventory(folder)
  if {r['path'] for r in actual}!={r['path'] for r in entries}|{'seal.json'}:
   raise RuntimeError('Agent seal inventory is incomplete: '+name)
  current=read(folder/'current-source-origins.json')
  if isinstance(current,dict):current=current['source_files']
  if not current:raise RuntimeError('Full original current copies required')
  for row in current:
   raw=matches(folder/row['copy'],row);p=Path(row['path'])
   if not p.is_absolute():p=ROOT/p
   rel=p.relative_to(ROOT).as_posix()
   if rel.startswith('artifacts/') and rel not in EVIDENCE_INPUTS:
    raise RuntimeError('A receipt cannot substitute for an original source')
   if p.read_bytes()!=raw:raise RuntimeError('Current original source drift: '+rel)
   kind='retained-original-native-evidence-input' if rel in EVIDENCE_INPUTS else 'original-source-file'
   if kind=='original-source-file':paths.add(rel)
   records.append(dict(agent=name,path=rel,source_kind=kind,source=row))
  deliveries.append(dict(agent=name,seal_file='seal.json',seal_sha256=sha((folder/'seal.json').read_bytes()),
   findings=read(folder/'findings.json'),current_source_origins=current,files=actual))
 return deliveries,paths,records

def variant_frontier():
 original=BASE/'tw-battle-state-source-01/source/tw-battle-variant-frontier.json'
 raw=original.read_bytes();saved=OUT/'retained-variant-inputs/prior165-frontier.json';save(saved,raw)
 origin=dict(path=original.relative_to(ROOT).as_posix(),copy=saved.relative_to(OUT).as_posix(),bytes=len(raw),sha256=sha(raw))
 previous=json.loads(raw);result=copy.deepcopy(previous)
 if len(result['entries'])!=30:raise RuntimeError('Retain previous30 inventory entries')
 for entry in result['entries']:
  note=dict(round=ROUND,previous_inventory_entry_retained=True,complete_route=False,
   matched_native_C2S_producers=[],original_server_pairing_proven=False)
  if entry['opcode']=='83' and entry['native_action_hex']=='08':
   note.update(new_owned_consumer_view='RecoveredBattleAction08Control::parse/encode',
    source_paths=[GAME[7]],logical_bytes=15,native_sha256='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763',
    raw_fields=['BYTE2 source<28','BYTE3 operand','WORD5/7 target masks','unsigned WORD9 zero/nonzero control'],
    opaque_fields=['BYTE4','bytes11..14'],
    first_stage='acting side0 WORD9 zero/nonzero clears/sets manager+488; side1 preserves flag',
    conditional_setup='common actor+1E7/+1E9 then08 setup actor+1EB=88,+232=0',
    normal_forward_return1_is_actor_apply_success=False,
    source_evidence='agents/action08-control/findings.json',runtime_emission_enabled=False,runtime_mutation_enabled=False)
  entry['round166_annotation']=note
 for old,new in zip(previous['entries'],result['entries']):
  if {k:v for k,v in new.items() if k!='round166_annotation'}!=old:raise RuntimeError('Retain old inventory fields')
 result.update(round=ROUND,prior165_inventory=origin,new_owned_raw_field_views=1,new_field_view_subcases=1,
  new_native_values_discovered=0,new_complete_routes=0,original_165_fields_unchanged=True)
 dump(OUT/'source/tw-battle-variant-frontier.json',result)
 dump(OUT/'retained-variant-inputs/origins.json',[origin]);return result

def account():
 if (OUT/'findings.json').exists() or (OUT/'manifest.json').exists():raise RuntimeError('Fresh unaccounted round required')
 rows,old=before();prior();guarded=protected(rows,old)
 agents,paths,records=agent_records();paths|=set(WRITTEN)
 for rel in GAME:
  if rel in old and old[rel]==(ROOT/rel).read_bytes():raise RuntimeError('Actual source increment required: '+rel)
 variants=variant_frontier()
 relations=dict(source_only=True,actual_Application_call_chain=
  'Four explicit run_server world-plan overloads -> actual game lifetime -> one SharedWorldHost(same character repository) -> mandatory make_taiwan_entered(Context) -> character listener handlers receive lifecycle factory -> actual Session selection invokes independent Binding -> mandatory real Entered',
  actual_CN_call_chain='Same Application host -> explicit SharedCredentialServer constructor -> State strong host before controllers -> exact same Context.common_world -> actual plan.controllers factory -> retained controllers/connection lifetime',
  shared_presence_and_visibility_created_once=True,same_character_backend_required=True,
  same_registry_pointer_supplied_to_TW_and_CN=True,legacy_null_creates_no_CN_registry=True,
  explicit_Application_world_plan_source_bindings_connected=True,
  actual_Main_selects_world_plan=False,actual_native_world_sources_supplied=False,
  candidate_frame_promoted_to_native=False,legacy_world_state_not_promoted=True,
  existing_Application_world_entry_ready_records_bodies_retained=True,
  actual_game_owned_TW_factory_hooks_cleanup_vault_connected=True,
  TW_network_copies_retain_only_revocable_facades=True,
  factory_created_closed_before_prepared_slot_consumed_on_game_disconnect=True,
  game_owner_scope_guard_revokes_before_source_or_database_destruction=True,
  default_TcpServer_stop_body_retained=True,
  native_action08_consumer_view=GAME[7],native_action08_emission_or_mutation_enabled=False,
  actual_native_account_issuer_or_login_rights_supplied=False,
  native_wire_or_formula_changed=False,formal_application_hosted=False,complete_route=False,
  saved_variant_frontier=variants,parallel_agent_findings=[x['findings'] for x in agents],remaining=REMAINING)
 facts=dict(round=ROUND,previous_goal_turn_classification='progress: six actual C++ source increments and three sealed agent evidence deliveries completed in165',
  completed_parallel_agents=3,modified_gameplay_source_files=10,existing_source_files_modified=6,new_Cplusplus_source_files_added=4,
  actual_game_owned_TW_callback_vaults_added=1,actual_Session_cleanup_owner_projections_added=1,
  actual_Session_abandon_owner_entries_added=1,
  actual_shared_world_host_implementations_added=1,actual_CN_common_context_constructor_overloads_added=1,
  actual_Application_world_plan_public_overloads_added=4,actual_Application_world_host_call_chains_added=1,
  actual_TW_per_session_factory_host_bindings_added=1,actual_CN_same_host_controller_context_bindings_added=1,
  new_owned_raw_field_views=1,new_field_view_subcases=1,source_origin_records=len(records),saved_TW_battle_variant_frontier_entries=30,
  new_packet_values=0,new_native_values_discovered=0,new_native_phase_source_bindings=0,
  new_source_owner_chains=0,new_tw_source_owner_chains=0,new_complete_bidirectional_routes=0,
  whole_game_route_total=None,whole_game_completed_routes=None,whole_game_completion_percent=None,
  explicit_Application_world_plan_source_bindings_connected=True,
  formal_application_hosted=False,actual_native_factory_selected_in_Main=False,actual_world_plan_selected_in_Main=False,
  build_run=False,tests_run=False,new_tests_written=0,runtime_run=False,native_execution=False,
  Cplusplus_source_run=False,Lua_run=False,Windows_API_run=False,database_access=False,SQL_run=False,deployed=False,
  numeric_caps_changed=False,levels_changed=False,original_native_wire_layout_changed=False,
  formatter_capacity_chain_retried=False,protected_contexts=guarded,remaining=REMAINING)
 dump(OUT/'parallel-agent-deliveries.json',agents);dump(OUT/'source/reviewed-current-source-records.json',records)
 dump(OUT/'source/shared-world-host-context-relations.json',relations);dump(OUT/'findings.json',facts)
 ledger_path=ROOT/BOOKS[1];ledger=read(ledger_path);old_ledger=json.loads(old[BOOKS[1]])
 if ledger['dual_client_source_segments']!=old_ledger['dual_client_source_segments'] or len(ledger['dual_client_source_segments'])!=157:
  raise RuntimeError('All157 prior source segments must remain')
 ledger['shared_world_host_context_source']=dict(facts,evidence=OUT.relative_to(ROOT).as_posix())
 ledger['dual_client_source_segments'].append(dict(name=NAME,round=ROUND,
  version_scope='TW-CN-web-explicit-common-world-Application-source-hosting-and-TW83-08-consumer',
  status='Same actual Application world host/repository/presence/visibility -> TW per-session lifecycle factory and CN controller Context; mandatory real Entered remains external; source08 raw fieldview only',
  source_paths=sorted(paths),native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,
  tw_source_owner_chains_added=0,formal_application_hosted=False,complete_gameplay_routes_added=0,
  evidence=OUT.relative_to(ROOT).as_posix(),remaining=REMAINING))
 plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
 plan['next_source_frontier']='Mandatory actual TW Entered/position revision/full native entry/scene WorldOwner and CN controller consumption of same common context; native account issuer/rights/world Reservation/Main source selection. Continue full battle producer-consumer state/variant and numeric persistent/wire/object/display connections. PHASE1 no execution/testing.'
 ledger_path.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 with (ROOT/BOOKS[0]).open('a',encoding='utf-8') as handle:
  handle.write('\n\n## Actual common Application world context ('+ROUND+')\n\n'
   'Three agents delivered ten C++ source increments. One game-owner SharedWorldHost creates the actual same repository/presence/visibility pair; explicit Application world plan and four public entrypoints pass it to TW per-Session lifecycle factory and the CN controller Context. '
   'A game-owned vault retains actual TW factory/hooks/installed cleanup behind revocable network facades, with cleanup-owner source projection and normal/startup-failure scope revocation before database destruction. '
   'The actual game disconnect also abandons the correct still-owned slot when close arrives after factory but before prepared/cleanup installation; identity/reentry guard failures cannot consume another slot. '
   'Mandatory actual Entered and world data remain caller-owned; default Main and frozen handler bodies are preserved, no candidate frame/state promotion/native gameplay success. '
   'Native83/08 unsigned WORD9 control field and side-specific bounded consumer view added without damage semantics, runtime emitter, authority or native pairing. '
   'Prior30 battle entries and full prior165 sealed inventory retained. Packet/phase/fullroute additions0; whole-game denominator/percentage null. No build/test/native/C++/Lua/DB/SQL/runtime/deployment; full TW-CN-web goal remains active.\n')
 origins=[]
 for i,rel in enumerate(sorted(paths|set(BOOKS)|{r['path'] for r in records})):
  raw=(ROOT/rel).read_bytes();dest=OUT/'source/current'/('s%03d'%i+Path(rel).suffix);save(dest,raw)
  origins.append(dict(path=rel,copy=dest.relative_to(OUT).as_posix(),bytes=len(raw),sha256=sha(raw),changed_this_round=rel not in old or old[rel]!=raw))
  if rel in old:
   # Binary original inputs are copied and hash-accounted, never text-decoded.
   if old[rel]==raw:continue
   delta=''.join(difflib.unified_diff(old[rel].decode('utf-8-sig').splitlines(True),raw.decode('utf-8-sig').splitlines(True),fromfile='before/'+rel,tofile='current/'+rel))
   if delta:save(OUT/'diff'/('d%03d.diff'%i),delta.encode('utf-8'))
 dump(OUT/'source/source-origins.json',origins)
 print(json.dumps(dict(round=ROUND,source_paths=len(paths),protected_files=len(guarded),modified_gameplay_source_files=10,new_complete_routes=0)))

def enrich():
 for p in reports():save(OUT/'reports/raw'/(p.parent.name+'-'+p.name),p.read_bytes())
 facts=read(OUT/'findings.json');relations=read(OUT/'source/shared-world-host-context-relations.json')
 agents=read(OUT/'parallel-agent-deliveries.json');sources=read(CAT/'source-file-manifest.json')
 old_sources=read(BASE/'endpoint-catalog165/source-file-manifest.json')
 delta=dict(completed_parallel_agents=3,modified_gameplay_source_files=10,existing_source_files_modified=6,new_Cplusplus_source_files_added=4,
  actual_game_owned_TW_callback_vaults_added=1,actual_Session_cleanup_owner_projections_added=1,
  actual_Session_abandon_owner_entries_added=1,
  actual_shared_world_host_implementations_added=1,actual_Application_world_plan_public_overloads_added=4,
  actual_Application_world_host_call_chains_added=1,actual_TW_per_session_factory_host_bindings_added=1,
  actual_CN_same_host_controller_context_bindings_added=1,new_owned_raw_field_views=1,new_field_view_subcases=1,
  saved_TW_battle_variant_frontier_entries=30,new_native_values_discovered=0,new_packet_values=0,new_phase_bindings=0,
  new_complete_bidirectional_routes=0,source_segments=158,current_catalog_source_files=len(sources),
  new_catalog_source_files=len(set(sources)-set(old_sources)),whole_game_completion_percent=None)
 for p in [reports()[0],reports()[2]]:
  v=read(p);v['shared_world_host_context_source']=facts;v['shared_world_host_context_relations']=relations
  v['parallel_agent_deliveries']=agents;v['current_round_source_delta']=delta
  p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 text=(ROOT/DOC).read_text(encoding='utf-8')+'\n\nStatic report delta:\n\n```json\n'+json.dumps(delta,indent=2)+'\n```\n'
 for p in [reports()[1],reports()[3]]:p.write_text(text,encoding='utf-8')
 dump(OUT/'reports/enrichment-receipt.json',delta);print(json.dumps(delta))

def seal():
 if (OUT/'manifest.json').exists() or (CAT/'manifest.json').exists():raise RuntimeError('Fresh seals required')
 rows,old=before();prior();guarded=protected(rows,old)
 agents,_,_=agent_records()
 if agents!=read(OUT/'parallel-agent-deliveries.json'):raise RuntimeError('Agent delivery drift')
 for row in read(OUT/'retained-variant-inputs/origins.json'):
  if (ROOT/row['path']).read_bytes()!=matches(OUT/row['copy'],row):raise RuntimeError('Prior variant drift')
 for row in read(OUT/'source/source-origins.json'):
  if (ROOT/row['path']).read_bytes()!=matches(OUT/row['copy'],row):raise RuntimeError('Root source drift')
 ledger=read(BASE/'packet-route-ledger.json');old_ledger=json.loads(old[BOOKS[1]])
 if len(ledger['dual_client_source_segments'])!=158 or ledger['dual_client_source_segments'][:157]!=old_ledger['dual_client_source_segments']:
  raise RuntimeError('Prior157 segments changed')
 source_files=read(CAT/'source-file-manifest.json')
 for p,row in source_files.items():matches(ROOT/p,row)
 ledger_rows=[r for r in read(CAT/'input-manifest.json') if r['input']=='source-ledger']
 if len(ledger_rows)!=1 or matches(CAT/ledger_rows[0]['snapshot'],ledger_rows[0])!=(BASE/'packet-route-ledger.json').read_bytes():
  raise RuntimeError('Catalog ledger drift')
 latest,latest_md,round_json,round_md=reports()
 if latest.read_bytes()!=round_json.read_bytes() or latest_md.read_bytes()!=round_md.read_bytes():raise RuntimeError('Final report mismatch')
 report=read(latest)
 if report['round']!=ROUND or report['route_ledger_sha256']!=sha((BASE/'packet-route-ledger.json').read_bytes()):raise RuntimeError('Report ledger mismatch')
 if report['dual_client_endpoint_catalog']['summary']!=read(CAT/'summary.json'):raise RuntimeError('Report catalog mismatch')
 for key in ['whole_game_distinct_packet_count','whole_game_completed_route_count','whole_game_completion_percent']:
  if report['counts'][key] is not None:raise RuntimeError('Whole-game denominator fabricated')
 for p in reports():save(OUT/'reports/final'/(p.parent.name+'-'+p.name),p.read_bytes())
 if len(list((OUT/'reports/raw').iterdir()))!=4 or len(list((OUT/'reports/final').iterdir()))!=4:raise RuntimeError('Four raw/final reports required')
 flags=dict(sealed=True,method='STATIC_FILES_SOURCE_ONLY',native_execution=False,Cplusplus_source_run=False,
  Lua_run=False,Windows_API_run=False,build_run=False,tests_run=False,runtime_run=False,database_access=False,SQL_run=False,deployed=False)
 cm=dict(format='god2-static-endpoint-catalog-seal-v1',round=CAT.name,**flags,
         files=inventory(CAT),current_source_files=len(source_files))
 dump(CAT/'manifest.json',cm)
 rm=dict(format='god2-static-source-delivery-seal-v1',round=ROUND,**flags,catalog=CAT.name,
  catalog_manifest_sha256=sha((CAT/'manifest.json').read_bytes()),before_files=len(rows),protected_files=len(guarded),
  gameplay_source_modified=True,modified_gameplay_source_files=10,completed_parallel_agents=3,
  new_complete_bidirectional_routes=0,whole_game_completion_percent=None,files=inventory(OUT))
 dump(OUT/'manifest.json',rm)
 print(json.dumps(dict(before_files=len(rows),protected_files=len(guarded),catalog_source_files=len(source_files),
  catalog_sealed_files=len(cm['files']),source_sealed_files=len(rm['files']),
  catalog_manifest_sha256=sha((CAT/'manifest.json').read_bytes()),source_manifest_sha256=sha((OUT/'manifest.json').read_bytes()))))

def main():
 if len(sys.argv)!=2 or sys.argv[1] not in ['account','enrich','seal']:raise RuntimeError('Choose account/enrich/seal')
 globals()[sys.argv[1]]()

if __name__=='__main__':main()
