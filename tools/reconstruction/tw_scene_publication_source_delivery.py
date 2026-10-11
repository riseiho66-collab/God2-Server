"""Immutable static source accounting; no game/native/SQL/test execution."""
import copy
import difflib
import json
from pathlib import Path
import sys
from .parallel_game_connection_frontier_delivery import ROOT, sha, read, save, dump, matches, inventory

BASE=ROOT/'artifacts/integration/packet-connections-20261006'
NAME='tw-scene-publication-source-01'
ROUND='20261008-tw-scene-publication-source'
OUT=BASE/NAME
CAT=BASE/'endpoint-catalog168'
DOC='docs/research/tw-scene-publication-source-20261008.md'
GAME=['src/net/Session.h','src/net/Session.cpp','src/core/SharedWorldHostPlan.h','src/core/Application.cpp',
      'src/cn/world/SharedActorVisibility.h','src/cn/world/SharedActorVisibility.cpp',
      'src/game/SharedTaiwanWorldLifecycle.h','src/game/SharedTaiwanWorldLifecycle.cpp',
      'src/game/SharedTaiwanWorldEntered.h','src/game/SharedTaiwanWorldEntered.cpp']
WRITTEN=GAME+[DOC,'tools/reconstruction/tw_scene_publication_source_delivery.py',
              'tools/reconstruction/dual_client_route_catalog.py']
BOOKS=['docs/PACKET_CONNECTION_GOAL_20261006.md',
       'artifacts/integration/packet-connections-20261006/packet-route-ledger.json']
AGENTS=['tw-initial-visibility','tw-async-hosting','tw-scene-entered']
PINS={'common-world-preparation-source-01':
      '889bbbcd44f8f581bdd82157fa72e8977ebbbc96b52b92251126ef1978685efd',
      'endpoint-catalog167':'6b5b32434b72c24197f62f5b6a0a6ddb4e778f7d25e504d9a9b15f0ea5b167ee'}
REMAINING=[
 'Actual TW full native frame/reservation/resources/appearance/fullpeer policy/Current/Install/Cleanup remain mandatory issuer inputs. The new async publisher connects those inputs, but does not recover or select the actual native scene authority.',
 'Phased BeforeQueue/held BeforePublish/AfterInstall/QueueReleased-or-LocalPublished/outward Current calls are connected. The real native predicates, opaque aggregate grammar, complete movement authority/5D and gameplay dispatcher remain open.',
 'CN actual native account issuer/rights/catalog/summary/assets/world Reservation/gameplay/scene publishers remain open; shared preparation identity alone supplies no native values.',
 'Ordinary Main has not selected the explicit world plan or CN native factory; arbitrary CN callback lifetime/drain and actual world ownership still need integration.',
 'Wide numeric persistent profiles/recovery/TW-CN-web wire-object-display, stack99 mutation callers, whole-game denominator/full routes and later testing/repair/release remain open.']

def reports():
 return [BASE/'packet-progress-latest.json',BASE/'packet-progress-latest.md',
         BASE/'round-reports'/(ROUND+'.json'),BASE/'round-reports'/(ROUND+'.md')]

def before():
 p=OUT/'before-manifest.json'
 if sha(p.read_bytes())!='713f854768b2f374cbae7ac7f5e4a8030293a0d197f0d20bef1ce3f431b1007b':
  raise RuntimeError('Preserve original before966 inventory')
 rows=read(p)
 if len(rows)!=966 or len({r['path'] for r in rows})!=966:raise RuntimeError('Before966 required')
 return rows,{r['path']:matches(OUT/r['snapshot'],r) for r in rows}

def prior():
 total=0
 for name,pin in PINS.items():
  raw=(BASE/name/'manifest.json').read_bytes()
  if sha(raw)!=pin or (OUT/'retained-prior'/name/'manifest.json').read_bytes()!=raw:
   raise RuntimeError('Immutable prior167 manifest changed')
  for row in json.loads(raw)['files']:matches(BASE/name/row['path'],row);total+=1
 if total!=1990:raise RuntimeError('Entire prior1990 inventory required')

def protected(rows,old):
 excluded=set(WRITTEN+BOOKS)|{p.relative_to(ROOT).as_posix() for p in reports()[:2]}
 result=[r for r in rows if r['path'] not in excluded]
 if len(result)!=953:raise RuntimeError('Protected953 required')
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
   raise RuntimeError('Agent seal inventory incomplete: '+name)
  current=read(folder/'current-source-origins.json')
  if isinstance(current,dict):current=current['source_files']
  if not current:raise RuntimeError('Full original current copies required')
  for row in current:
   raw=matches(folder/row['copy'],row);p=Path(row['path'])
   if not p.is_absolute():p=ROOT/p
   rel=p.relative_to(ROOT).as_posix()
   if rel.startswith('artifacts/'):raise RuntimeError('Receipt cannot substitute for source: '+rel)
   if p.read_bytes()!=raw:raise RuntimeError('Current original source drift: '+rel)
   paths.add(rel);records.append(dict(agent=name,path=rel,source_kind='original-source-file',source=row))
  delivery=dict(agent=name,seal_file='seal.json',seal_sha256=sha((folder/'seal.json').read_bytes()),
   findings=read(folder/'findings.json'),current_source_origins=current,files=actual)
  deliveries.append(delivery)
 return deliveries,paths,records

def retain_variants():
 original=BASE/'common-world-preparation-source-01/source/tw-battle-variant-frontier.json'
 raw=original.read_bytes();saved=OUT/'retained-variant-inputs/prior167-frontier.json';save(saved,raw)
 origin=dict(path=original.relative_to(ROOT).as_posix(),copy=saved.relative_to(OUT).as_posix(),bytes=len(raw),sha256=sha(raw))
 previous=json.loads(raw)
 if len(previous['entries'])!=30:raise RuntimeError('Retain previous30 inventory entries')
 result=copy.deepcopy(previous)
 result.update(round=ROUND,prior167_inventory=origin,new_owned_raw_field_views=0,new_field_view_subcases=0,
  new_native_values_discovered=0,new_complete_routes=0,original_167_entries_unchanged=True)
 if result['entries']!=previous['entries']:raise RuntimeError('Prior variant entries changed')
 dump(OUT/'source/tw-battle-variant-frontier.json',result)
 dump(OUT/'retained-variant-inputs/origins.json',[origin]);return result

def delta(sources=None,previous=None):
 value=dict(completed_parallel_agents=3,modified_gameplay_source_files=10,existing_source_files_modified=8,
  new_Cplusplus_source_files_added=2,actual_TW_initial_visibility_preparation_entries_added=1,
  actual_TW_async_scene_entered_publishers_added=1,actual_TW_async_lifecycle_factories_added=1,
  actual_TW_held_entry_publication_transport_entries_added=1,actual_TW_async_Application_vault_bindings_added=1,
  new_owned_raw_field_views=0,new_field_view_subcases=0,saved_TW_battle_variant_frontier_entries=30,
  new_native_values_discovered=0,new_packet_values=0,new_phase_bindings=0,new_complete_bidirectional_routes=0,
  source_segments=160,whole_game_completion_percent=None)
 if sources is not None:
  value.update(current_catalog_source_files=len(sources),new_catalog_source_files=len(set(sources)-set(previous)))
 return value

def account():
 if (OUT/'findings.json').exists() or (OUT/'manifest.json').exists():raise RuntimeError('Fresh unaccounted round required')
 rows,old=before();prior();guarded=protected(rows,old)
 agents,paths,records=agent_records();paths|=set(WRITTEN)
 for rel in GAME:
  if rel in old and old[rel]==(ROOT/rel).read_bytes():raise RuntimeError('Actual source increment required: '+rel)
 review=read(OUT/'root-final-source-review.json')
 if {r['path'] for r in review['files']}!=set(GAME):raise RuntimeError('Final review requires all10 sources')
 for row in review['files']:matches(ROOT/row['path'],row)
 variants=retain_variants()
 relations=dict(source_only=True,
  actual_TW_call_chain='Actual native tail -> explicit async common lifecycle -> exact prepared lease/full entry -> mandatory scene issuer Plan -> staged initial TW native models -> pending entry held transport -> phased Current -> real scene Install/InWorld -> exact common activation/ready identity -> incoming model publication -> incoming queue release or explicit local-only publication -> actual outward TW-CN observer publication -> async completion -> resume original world input',
  actual_initial_TW_visibility_token_added=True,initial_models_preallocated_before_IO=True,
  initial_TW_recipient_still_prepared_before_publication=True,
  actual_async_tail_input_wait_and_cancellation_connected=True,
  actual_pending_entry_publication_transport_added=True,
  actual_async_hooks_and_publication_payload_game_owned=True,
  old_CN_initial_visibility_and_sync_TW_lifecycle_bodies_retained=True,
  complete_native_records_and_full_observer_set_are_mandatory_issuer_inputs=True,
  explicit_empty_scene_output_requires_actual_source_decision=True,
  all_supplied_incoming_models_matched_to_exact_ordered6F_slices=True,
  opaque_native_aggregate_record_boundaries_exhaustively_recovered=False,
  native_peer_visibility_policy_or_resource_rules_invented=False,
  local_queue_release_is_native_receipt=False,fanout_is_distributed_atomic=False,
  native_scene_supplier_or_WorldOwner_implemented=False,actual_Main_selects_world_plan=False,
  actual_native_account_issuer_or_login_rights_supplied=False,CN_all_callback_lifetime_drain_proven=False,
  native_wire_or_formula_changed=False,formal_application_hosted=False,complete_route=False,
  saved_variant_frontier=variants,parallel_agent_findings=[x['findings'] for x in agents],remaining=REMAINING)
 facts=dict(delta(),round=ROUND,
  previous_goal_turn_classification='progress: ten actual C++ source increments and three sealed agent deliveries in167',
  new_native_phase_source_bindings=0,new_source_owner_chains=0,new_tw_source_owner_chains=0,
  whole_game_route_total=None,whole_game_completed_routes=None,source_origin_records=len(records),
  formal_application_hosted=False,actual_native_factory_selected_in_Main=False,actual_world_plan_selected_in_Main=False,
  build_run=False,tests_run=False,new_tests_written=0,runtime_run=False,native_execution=False,
  Cplusplus_source_run=False,Lua_run=False,Windows_API_run=False,database_access=False,SQL_run=False,deployed=False,
  numeric_caps_changed=False,levels_changed=False,original_native_wire_layout_changed=False,
  formatter_capacity_chain_retried=False,protected_contexts=guarded,remaining=REMAINING)
 dump(OUT/'parallel-agent-deliveries.json',agents);dump(OUT/'source/reviewed-current-source-records.json',records)
 dump(OUT/'source/tw-scene-publication-relations.json',relations);dump(OUT/'findings.json',facts)
 ledger_path=ROOT/BOOKS[1];ledger=read(ledger_path);old_ledger=json.loads(old[BOOKS[1]])
 if ledger['dual_client_source_segments']!=old_ledger['dual_client_source_segments'] or len(ledger['dual_client_source_segments'])!=159:
  raise RuntimeError('All159 prior source segments must remain')
 ledger['tw_scene_publication_source']=dict(facts,evidence=OUT.relative_to(ROOT).as_posix())
 ledger['dual_client_source_segments'].append(dict(name=NAME,round=ROUND,
  version_scope='TW-CN-web-explicit-TW-async-scene-initial-visibility-and-native-publication-source',
  status='Actual async TW scene source and initial native model publication connect through held entry transport and game-owned Application vault; original native scene suppliers and Main remain open',
  source_paths=sorted(paths),native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,
  tw_source_owner_chains_added=0,formal_application_hosted=False,complete_gameplay_routes_added=0,
  evidence=OUT.relative_to(ROOT).as_posix(),remaining=REMAINING))
 plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
 plan['next_source_frontier']='Actual TW native entry/reservation/resources/appearance/fullpeer policy/phased Current/scene Install/Cleanup/WorldOwner; CN actual native account issuer/rights/summary/assets/world Reservation/gameplay publication; ordinary Main source selection and lifetime drain. Whole battle producer-consumer state/variant and numeric persistent/wire/object/display remain open. PHASE1 no execution/testing.'
 ledger_path.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 with (ROOT/BOOKS[0]).open('a',encoding='utf-8') as handle:
  handle.write('\n\n## Actual asynchronous TW scene publication ('+ROUND+')\n\n'
   'Three agents delivered ten C++ source increments. Separate initial TW visibility tokens retain exact prepared recipients, source generations, saved positions and complete supplied native6F/5E/73 models. '
   'Explicit asynchronous lifecycle and mandatory scene issuer connect the actual native tail to held entry publication, phased Current, real scene Install/InWorld, exact common presence activation/ready identity and incoming model publication. '
   'After the actual incoming queue release, the full supplied TW/CN outward observer set publishes through the existing native visibility owner before gameplay input resumes. Cancellation and game-owned revocable callback storage cover pending operation failure and release. '
   'Legacy sync/default handlers and CN initial publication remain separate. Local queue release is not native receipt; no guessed native values, visibility policy, scene resource rules or distributed atomic fanout. '
   'Original scene issuer/reservation/assets/WorldOwner, CN native rights/data/Reservation, Main selection and full gameplay still open. Entire prior1671990 sealed members and30 battle entries preserved. Packet/phase/fullroute0; denominator/percentage null. '
   'No build/test/native/C++/Lua/API/DB/SQL/runtime/deployment; full TW-CN-web goal remains active.\n')
 origins=[]
 for i,rel in enumerate(sorted(paths|set(BOOKS))):
  raw=(ROOT/rel).read_bytes();dest=OUT/'source/current'/('s%03d'%i+Path(rel).suffix);save(dest,raw)
  origins.append(dict(path=rel,copy=dest.relative_to(OUT).as_posix(),bytes=len(raw),sha256=sha(raw),changed_this_round=rel not in old or old[rel]!=raw))
  if rel in old and old[rel]!=raw:
   diff=''.join(difflib.unified_diff(old[rel].decode('utf-8-sig').splitlines(True),raw.decode('utf-8-sig').splitlines(True),fromfile='before/'+rel,tofile='current/'+rel))
   if diff:save(OUT/'diff'/('d%03d.diff'%i),diff.encode('utf-8'))
 dump(OUT/'source/source-origins.json',origins)
 print(json.dumps(dict(round=ROUND,source_paths=len(paths),protected_files=len(guarded),modified_gameplay_source_files=10,new_complete_routes=0)))

def enrich():
 for p in reports():save(OUT/'reports/raw'/(p.parent.name+'-'+p.name),p.read_bytes())
 facts=read(OUT/'findings.json');relations=read(OUT/'source/tw-scene-publication-relations.json')
 agents=read(OUT/'parallel-agent-deliveries.json');sources=read(CAT/'source-file-manifest.json')
 receipt=delta(sources,read(BASE/'endpoint-catalog167/source-file-manifest.json'))
 for p in [reports()[0],reports()[2]]:
  value=read(p);value['tw_scene_publication_source']=facts;value['tw_scene_publication_relations']=relations
  value['parallel_agent_deliveries']=agents;value['current_round_source_delta']=receipt
  p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 text=(ROOT/DOC).read_text(encoding='utf-8')+'\n\nStatic report delta:\n\n```json\n'+json.dumps(receipt,indent=2)+'\n```\n'
 for p in [reports()[1],reports()[3]]:p.write_text(text,encoding='utf-8')
 dump(OUT/'reports/enrichment-receipt.json',receipt);print(json.dumps(receipt))

def seal():
 if (OUT/'manifest.json').exists() or (CAT/'manifest.json').exists():raise RuntimeError('Fresh seals required')
 rows,old=before();prior();guarded=protected(rows,old)
 agents,_,_=agent_records()
 if agents!=read(OUT/'parallel-agent-deliveries.json'):raise RuntimeError('Agent delivery drift')
 for row in read(OUT/'retained-variant-inputs/origins.json'):
  if (ROOT/row['path']).read_bytes()!=matches(OUT/row['copy'],row):raise RuntimeError('Prior variant drift')
 for row in read(OUT/'source/source-origins.json'):
  if (ROOT/row['path']).read_bytes()!=matches(OUT/row['copy'],row):raise RuntimeError('Root source drift')
 for row in read(OUT/'root-final-source-review.json')['files']:matches(ROOT/row['path'],row)
 ledger=read(BASE/'packet-route-ledger.json');old_ledger=json.loads(old[BOOKS[1]])
 if len(ledger['dual_client_source_segments'])!=160 or ledger['dual_client_source_segments'][:159]!=old_ledger['dual_client_source_segments']:
  raise RuntimeError('Prior159 segments changed')
 source_files=read(CAT/'source-file-manifest.json')
 for path,row in source_files.items():matches(ROOT/path,row)
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
 cm=dict(format='god2-static-endpoint-catalog-seal-v1',round=CAT.name,**flags,files=inventory(CAT),current_source_files=len(source_files))
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
