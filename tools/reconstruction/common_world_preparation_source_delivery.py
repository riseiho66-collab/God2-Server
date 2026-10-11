"""Immutable static source accounting; no game/native/SQL/test execution."""
import copy
import difflib
import json
from pathlib import Path
import sys
from .parallel_game_connection_frontier_delivery import ROOT, sha, read, save, dump, matches, inventory

BASE=ROOT/'artifacts/integration/packet-connections-20261006'
NAME='common-world-preparation-source-01'
ROUND='20261008-common-world-preparation-source'
OUT=BASE/NAME
CAT=BASE/'endpoint-catalog167'
DOC='docs/research/common-world-preparation-source-20261008.md'
GAME=['src/cn/auth/SharedLoginComposition.h','src/cn/auth/SharedLoginComposition.cpp',
      'src/cn/world/SharedWorldPreparation.h','src/cn/world/SharedWorldPreparation.cpp',
      'src/core/SharedWorldHostPlan.h','src/core/Application.cpp',
      'src/handlers/RecoveredMovementService.h','src/handlers/RecoveredMovementService.cpp',
      'src/game/SharedTaiwanWorldEntrySource.h','src/game/SharedTaiwanWorldEntrySource.cpp']
WRITTEN=GAME+[DOC,'tools/reconstruction/common_world_preparation_source_delivery.py',
              'tools/reconstruction/dual_client_route_catalog.py']
BOOKS=['docs/PACKET_CONNECTION_GOAL_20261006.md',
       'artifacts/integration/packet-connections-20261006/packet-route-ledger.json']
AGENTS=['cn-preparation','tw-entry-hosting','tw-entry-source']
PINS={'shared-world-host-context-source-01':
      'f37dcc4e27bc355e47a8b1770f04cd0238c8707f0199f6228e1471edf2dbe6c7',
      'endpoint-catalog166':'f838cddb740162796de6e725979a32191d5e733a1f0e8dd92f1ab7b3d665be95'}
REMAINING=[
 'Actual TW full native frame/reservation/Current/Entered/scene owner/5D/recipient publication remain mandatory external inputs; source selection is not native acceptance.',
 'The explicit movement adoption retains existing navigation qualification and ready binding, not a recovered whole-game native movement authority. Queue-stage Current remains open.',
 'CN actual native account issuer/rights/catalog/summary/assets/world Reservation/gameplay/scene publishers remain open; shared preparation identity alone supplies no native values.',
 'Ordinary Main has not selected the explicit world plan or CN native factory; arbitrary CN callback lifetime/drain and actual world ownership still need integration.',
 'Wide numeric persistent profiles/recovery/TW-CN-web wire-object-display, stack99 mutation callers, whole-game denominator/full routes and later testing/repair/release remain open.']

def reports():
 return [BASE/'packet-progress-latest.json',BASE/'packet-progress-latest.md',
         BASE/'round-reports'/(ROUND+'.json'),BASE/'round-reports'/(ROUND+'.md')]

def before():
 p=OUT/'before-manifest.json'
 if sha(p.read_bytes())!='08331209b7908063eaf09ba914beac011c27b1e1b70fa5c5ca016823b6ff82df':
  raise RuntimeError('Preserve original before962 inventory')
 rows=read(p)
 if len(rows)!=962 or len({r['path'] for r in rows})!=962:raise RuntimeError('Before962 required')
 return rows,{r['path']:matches(OUT/r['snapshot'],r) for r in rows}

def prior():
 total=0
 for name,pin in PINS.items():
  raw=(BASE/name/'manifest.json').read_bytes()
  if sha(raw)!=pin or (OUT/'retained-prior'/name/'manifest.json').read_bytes()!=raw:
   raise RuntimeError('Immutable prior166 manifest changed')
  for row in json.loads(raw)['files']:matches(BASE/name/row['path'],row);total+=1
 if total!=1853:raise RuntimeError('Entire prior1853 inventory required')

def protected(rows,old):
 excluded=set(WRITTEN+BOOKS)|{p.relative_to(ROOT).as_posix() for p in reports()[:2]}
 result=[r for r in rows if r['path'] not in excluded]
 if len(result)!=949:raise RuntimeError('Protected949 required')
 for row in result:
  if (ROOT/row['path']).read_bytes()!=old[row['path']]:raise RuntimeError('Protected source changed: '+row['path'])
 return result

def receiver_history(folder):
 receipt=read(folder/'receipt-correction.json')
 pin='e5a199e0497ab23357e469e587eb1a5108bebb0f3139bde99642f08373fdeccb'
 raw=(folder/receipt['first_seal_raw_copy']).read_bytes()
 if sha(raw)!=pin or receipt['first_seal_sha256']!=pin or receipt['formal_source_edits']!=0:
  raise RuntimeError('Receiver original seal/correction scope differs')
 original=json.loads(raw)['files'];mapping=read(folder/receipt['initial_member_preservation_map'])['initial_members']
 saved={r['initial_path']:r for r in mapping}
 if len(original)!=108 or len(mapping)!=108 or len(saved)!=108 or set(saved)!={r['path'] for r in original}:
  raise RuntimeError('Preserve all108 original receiver members')
 for row in original:
  item=saved[row['path']]
  if (item['bytes'],item['sha256'])!=(row['bytes'],row['sha256']):raise RuntimeError('Receiver history metadata changed')
  matches(folder/item['preserved_path'],row)
 return dict(first_seal_sha256=pin,all_original_members_preserved=108,formal_source_correction_edits=0,
  correction_receipt_sha256=sha((folder/'receipt-correction.json').read_bytes()))

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
  if name=='tw-entry-hosting':delivery['receipt_correction']=receiver_history(folder)
  deliveries.append(delivery)
 return deliveries,paths,records

def retain_variants():
 original=BASE/'shared-world-host-context-source-01/source/tw-battle-variant-frontier.json'
 raw=original.read_bytes();saved=OUT/'retained-variant-inputs/prior166-frontier.json';save(saved,raw)
 origin=dict(path=original.relative_to(ROOT).as_posix(),copy=saved.relative_to(OUT).as_posix(),bytes=len(raw),sha256=sha(raw))
 previous=json.loads(raw)
 if len(previous['entries'])!=30:raise RuntimeError('Retain previous30 inventory entries')
 result=copy.deepcopy(previous)
 result.update(round=ROUND,prior166_inventory=origin,new_owned_raw_field_views=0,new_field_view_subcases=0,
  new_native_values_discovered=0,new_complete_routes=0,original_166_entries_unchanged=True)
 if result['entries']!=previous['entries']:raise RuntimeError('Prior variant entries changed')
 dump(OUT/'source/tw-battle-variant-frontier.json',result)
 dump(OUT/'retained-variant-inputs/origins.json',[origin]);return result

def delta(sources=None,previous=None):
 value=dict(completed_parallel_agents=3,modified_gameplay_source_files=10,existing_source_files_modified=8,
  new_Cplusplus_source_files_added=2,actual_CN_common_preparation_composition_bindings_added=1,
  actual_CN_both_registry_identity_observations_added=1,actual_TW_saved_entry_sources_added=1,
  actual_TW_full_entry_Application_selection_bindings_added=1,actual_TW_game_owned_entry_vaults_extended=1,
  actual_TW_native_frame_movement_adoption_entries_added=1,new_owned_raw_field_views=0,
  new_field_view_subcases=0,saved_TW_battle_variant_frontier_entries=30,new_native_values_discovered=0,
  new_packet_values=0,new_phase_bindings=0,new_complete_bidirectional_routes=0,source_segments=159,
  whole_game_completion_percent=None)
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
  actual_CN_call_chain='Context.common_world exact repository/presence/visibility -> explicit actual assets/Reserve/budgets config -> SharedWorldPreparation::create once -> world supplier leaves preparation empty -> same selected()/prepare()/native02/2A/ready chain',
  CN_legacy_supplied_preparation_requires_exact_both_registries_when_host_present=True,
  CN_account_naming_bind_is_explicit_opt_in=True,CN_competing_preparation_is_rejected=True,
  actual_TW_call_chain='Application game Context -> explicit make_taiwan_world_entry -> game-owned WorldLifecycleVault actual source -> revocable entry facade -> actual Session world_entry -> supplied full frame -> prepare_native actual saved geometry -> unchanged ready bind and mandatory common lifecycle/Entered',
  TW_full_entry_source_qualifications=['same full owned character tuple','actual saved position/revision','current full NativeMapRecord','mandatory native full frame/Current','40-byte wire/37-byte logical op2A view','decoded actor handle equals full selected64 ID','exact persisted area/scene/x/y','re-read after native supplier and Current','game owner/reentry rejection'],
  arbitrary_Plan_Entry_type_certifies_native_provenance=False,
  TW_frame_all_opaque_original_bytes_retained=True,TW_wire_kind_not_inferred_from_map_kind=True,
  TW_candidate_native_frame_not_constructed_or_normalized=True,TW_no_initial_placement_or_SQL_write=True,
  actual_game_owned_TW_entry_callback_vault_extended=True,TW_late_network_copies_retain_only_revocable_entry_facade=True,
  TW_existing_movement_prepare_and_bind_bodies_retained=True,TW_existing_candidate_entry_and_ready_bodies_retained=True,
  TW_native_adoption_requires_actual_saved_frame_geometry_and_existing_navigation=True,
  TW_conflicting_candidate_appearance_and_visibility_diagnostic_modes_rejected=True,
  native_queue_stage_Current_atomicity_solved=False,actual_native_full_frame_producer_supplied=False,
  actual_native_scene_Entered_or_world_owner_supplied=False,actual_Main_selects_world_plan=False,
  actual_native_account_issuer_or_login_rights_supplied=False,CN_all_callback_lifetime_drain_proven=False,
  native_wire_or_formula_changed=False,formal_application_hosted=False,complete_route=False,
  saved_variant_frontier=variants,parallel_agent_findings=[x['findings'] for x in agents],remaining=REMAINING)
 facts=dict(delta(),round=ROUND,
  previous_goal_turn_classification='progress: ten actual C++ source increments and three sealed agent deliveries in166',
  new_native_phase_source_bindings=0,new_source_owner_chains=0,new_tw_source_owner_chains=0,
  whole_game_route_total=None,whole_game_completed_routes=None,source_origin_records=len(records),
  formal_application_hosted=False,actual_native_factory_selected_in_Main=False,actual_world_plan_selected_in_Main=False,
  build_run=False,tests_run=False,new_tests_written=0,runtime_run=False,native_execution=False,
  Cplusplus_source_run=False,Lua_run=False,Windows_API_run=False,database_access=False,SQL_run=False,deployed=False,
  numeric_caps_changed=False,levels_changed=False,original_native_wire_layout_changed=False,
  formatter_capacity_chain_retried=False,protected_contexts=guarded,remaining=REMAINING)
 dump(OUT/'parallel-agent-deliveries.json',agents);dump(OUT/'source/reviewed-current-source-records.json',records)
 dump(OUT/'source/common-world-preparation-relations.json',relations);dump(OUT/'findings.json',facts)
 ledger_path=ROOT/BOOKS[1];ledger=read(ledger_path);old_ledger=json.loads(old[BOOKS[1]])
 if ledger['dual_client_source_segments']!=old_ledger['dual_client_source_segments'] or len(ledger['dual_client_source_segments'])!=158:
  raise RuntimeError('All158 prior source segments must remain')
 ledger['common_world_preparation_source']=dict(facts,evidence=OUT.relative_to(ROOT).as_posix())
 ledger['dual_client_source_segments'].append(dict(name=NAME,round=ROUND,
  version_scope='TW-CN-web-explicit-common-world-preparation-and-actual-TW-native-entry-source',
  status='Exact CN common preparation selection plus actual TW saved-position/full-frame source and explicit Application entry caller/movement adoption; mandatory native suppliers/WorldOwner/Main still open',
  source_paths=sorted(paths),native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,
  tw_source_owner_chains_added=0,formal_application_hosted=False,complete_gameplay_routes_added=0,
  evidence=OUT.relative_to(ROOT).as_posix(),remaining=REMAINING))
 plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
 plan['next_source_frontier']='Actual TW native entry/reservation/Current/Entered/WorldOwner and CN actual native account issuer/rights/summary/assets/world Reservation/gameplay publication; ordinary Main source selection and lifetime drain. Whole battle producer-consumer state/variant and numeric persistent/wire/object/display remain open. PHASE1 no execution/testing.'
 ledger_path.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 with (ROOT/BOOKS[0]).open('a',encoding='utf-8') as handle:
  handle.write('\n\n## Actual common preparation and TW saved native entry ('+ROUND+')\n\n'
   'Three agents delivered ten C++ source increments. CN explicit assets/Reserve/budgets select one actual preparation from the exact Context host repository/presence/visibility; legacy world and naming sources check both registry identities. Optional naming bind requires explicit intent and an absent competing preparation. '
   'TW actual saved character tuple/position revision/map record and mandatory full native frame/Current source connect through an explicit Application factory and a game-owned revocable entry vault. '
   'A newly discovered actual dependency requires adopting the native frame geometry into existing movement state before the preserved ready bind. The dedicated opt-in preparation uses actual saved geometry and existing qualified navigation; no candidate frame, placement defaults, SQL write or invented appearance. Conflicting candidate appearance/visibility diagnostic modes reject explicitly. '
   'Existing default entry/ready/prepare/bind bodies remain; all original native frame bytes retained. Actual native producers, scene owner, queue-stage Current, CN rights/assets/Reservation, Main selection and full-game routes remain open. '
   'Full prior166 inventory and30 battle entries preserved. New packet/phase/fullroute0; denominator/percentage null. No build/test/native/C++/Lua/DB/SQL/runtime/deployment. Full TW-CN-web goal active.\n')
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
 facts=read(OUT/'findings.json');relations=read(OUT/'source/common-world-preparation-relations.json')
 agents=read(OUT/'parallel-agent-deliveries.json');sources=read(CAT/'source-file-manifest.json')
 receipt=delta(sources,read(BASE/'endpoint-catalog166/source-file-manifest.json'))
 for p in [reports()[0],reports()[2]]:
  value=read(p);value['common_world_preparation_source']=facts;value['common_world_preparation_relations']=relations
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
 if len(ledger['dual_client_source_segments'])!=159 or ledger['dual_client_source_segments'][:158]!=old_ledger['dual_client_source_segments']:
  raise RuntimeError('Prior158 segments changed')
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
