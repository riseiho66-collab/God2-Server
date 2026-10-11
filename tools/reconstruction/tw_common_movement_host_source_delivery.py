"""Immutable static file/source accounting; never runs native/gameplay/SQL."""
import copy
import difflib
import json
from pathlib import Path
import sys
from .parallel_game_connection_frontier_delivery import ROOT, sha, read, save, dump, matches, inventory

BASE=ROOT/'artifacts/integration/packet-connections-20261006'
NAME='tw-common-movement-host-source-01'
ROUND='20261008-tw-common-movement-host-source'
OUT=BASE/NAME
CAT=BASE/'endpoint-catalog170'
DOC='docs/research/tw-common-movement-host-source-20261008.md'
GAME=['src/game/SharedWorldPresence.h','src/game/SharedWorldPresence.cpp',
      'src/game/SharedTaiwanMovement.h','src/game/SharedTaiwanMovement.cpp',
      'src/game/SharedTaiwanMovementSource.h','src/game/SharedTaiwanMovementSource.cpp',
      'src/core/SharedWorldHostPlan.h','src/core/Application.cpp']
WRITTEN=GAME+[DOC,'tools/reconstruction/tw_common_movement_host_source_delivery.py',
              'tools/reconstruction/cn_receiver_slot_selection170.py',
              'tools/reconstruction/dual_client_route_catalog.py']
BOOKS=['docs/PACKET_CONNECTION_GOAL_20261006.md',
       'artifacts/integration/packet-connections-20261006/packet-route-ledger.json']
AGENTS=['movement-core','movement-source','cn-slot-selection']
PINS={'tw-native-record-grammar-source-01':'2c757040137e96f04fdd4e80535d6404a594236f457391708a1b7c2f501aa150',
      'endpoint-catalog169':'49fd69cb34f2a9233870744203bdbf2590537447f253594dc5aac09ff37ba1d3'}
NATIVE_INPUT='artifacts/research/enemy-blackbox-20261006/consumer-experiment/inputs/native-image.bin'
REMAINING=[
 'Actual TW native entry/reservation/resources/appearance/fullpeer policy/Current/Install/Cleanup remain mandatory inputs; the movement source does not recover native scene authority.',
 'Actual TW WorldOwner/native raw cells/revisions/timing/collision/actor/transfer/battle authority and complete5D remain unsupplied. Source/controller/vault binding is opt-in and unselected in ordinary Main.',
 'TW mixed world-record dispatch remains separately owned; this explicit movement binding rejects incompatible dispatchers and does not silently replace frozen CUSTOM rules.',
 'CN0047DE70/004812B0 phase/calling slots remain unknown. New slot witnesses qualify already-known callers only;14contexts/12qualified unchanged.',
 'CN actual native account issuer/rights/catalog/summary/assets/world Reservation/gameplay/scene publishers and ordinary Main selection remain open.',
 'Wide numeric persistent profiles/recovery/TW-CN-web wire/object/display, stack99 mutation callers, web WSS/TLS/hosting, whole-game denominator/routes and later comprehensive tests/repair/release remain open.']

def reports():
 return [BASE/'packet-progress-latest.json',BASE/'packet-progress-latest.md',
         BASE/'round-reports'/(ROUND+'.json'),BASE/'round-reports'/(ROUND+'.md')]

def before():
 p=OUT/'before-manifest.json'
 if sha(p.read_bytes())!='eac8cc89ce5c147dacac2af079bdad484b7c7691beaf54ac5f849f6a94269a93':
  raise RuntimeError('Original before1220 inventory changed')
 rows=read(p)
 if len(rows)!=1220 or len({r['path'] for r in rows})!=1220:raise RuntimeError('Before1220 required')
 return rows,{r['path']:matches(OUT/r['snapshot'],r) for r in rows}

def prior():
 total=0
 for name,pin in PINS.items():
  raw=(BASE/name/'manifest.json').read_bytes()
  if sha(raw)!=pin or (OUT/'retained-prior'/name/'manifest.json').read_bytes()!=raw:
   raise RuntimeError('Immutable prior169 manifest changed')
  for row in json.loads(raw)['files']:matches(BASE/name/row['path'],row);total+=1
 if total!=2003:raise RuntimeError('Entire prior2003 members required')

def protected(rows,old):
 excluded=set(WRITTEN+BOOKS)|{p.relative_to(ROOT).as_posix() for p in reports()[:2]}
 result=[r for r in rows if r['path'] not in excluded]
 if len(result)!=1209:raise RuntimeError('Protected1209 required')
 for row in result:
  if (ROOT/row['path']).read_bytes()!=old[row['path']]:raise RuntimeError('Protected source drift: '+row['path'])
 return result

def agent_records():
 deliveries=[];paths=set();records=[]
 for name in AGENTS:
  folder=OUT/'agents'/name;seal=read(folder/'seal.json')
  entries=seal.get('files',seal.get('entries',seal.get('members',[])))
  if not entries:raise RuntimeError('Entire agent seal required')
  for row in entries:matches(folder/row['path'],row)
  actual=inventory(folder)
  if {r['path'] for r in actual}!={r['path'] for r in entries}|{'seal.json'}:
   raise RuntimeError('Agent entire inventory differs: '+name)
  current=read(folder/'current-source-origins.json')
  if not isinstance(current,list) or not current:raise RuntimeError('Simple full original list required')
  for row in current:
   raw=matches(folder/row['copy'],row);p=Path(row['path'])
   if not p.is_absolute():p=ROOT/p
   rel=p.relative_to(ROOT).as_posix()
   if rel.startswith('artifacts/') and rel!=NATIVE_INPUT:raise RuntimeError('Receipt is not original source: '+rel)
   if rel in BOOKS or rel=='tools/reconstruction/dual_client_route_catalog.py':raise RuntimeError('Mutable root current pin')
   if p.read_bytes()!=raw:raise RuntimeError('Actual current original drift: '+rel)
   paths.add(rel);records.append(dict(agent=name,path=rel,source_kind='original-source-file',source=row))
  native_inputs=[];native_path=folder/'native-original-inputs.json'
  if native_path.exists():
   native_inputs=read(native_path)
   if not isinstance(native_inputs,list):raise RuntimeError('Simple original native input list required')
   for row in native_inputs:
    p=Path(row['path'])
    if not p.is_absolute() or p.read_bytes()!=matches(folder/row['copy'],row):raise RuntimeError('Native original drift')
  deliveries.append(dict(agent=name,seal_sha256=sha((folder/'seal.json').read_bytes()),
    findings=read(folder/'findings.json'),native_original_inputs=native_inputs,current_source_origins=current,files=actual))
 return deliveries,paths,records

def delta(sources=None,previous=None):
 value=dict(completed_parallel_agents=3,modified_gameplay_source_files=8,existing_source_files_modified=6,
  new_Cplusplus_source_files_added=2,actual_TW_active_ready_lease_queries_added=1,
  actual_TW_strong_owned_movement_controller_entries_added=1,actual_TW_common_movement_sources_added=1,
  actual_TW_Application_movement_selection_bindings_added=1,actual_TW_game_owned_movement_vaults_extended=1,
  CN_new_bounded_slot_instruction_spans=5,CN_new_mechanical_slot_relations=5,
  CN_receiver_contexts=14,CN_receiver_contexts_qualified=12,
  new_owned_raw_field_views=0,new_field_view_subcases=0,saved_TW_battle_variant_frontier_entries=30,
  new_native_values_discovered=0,new_packet_values=0,new_phase_bindings=0,new_complete_bidirectional_routes=0,
  source_segments=162,whole_game_completion_percent=None)
 if sources is not None:value.update(current_catalog_source_files=len(sources),new_catalog_source_files=len(set(sources)-set(previous)))
 return value

def account():
 if (OUT/'findings.json').exists() or (OUT/'manifest.json').exists():raise RuntimeError('Fresh unaccounted round required')
 rows,old=before();prior();guarded=protected(rows,old)
 agents,paths,records=agent_records();paths|=set(WRITTEN)
 review=read(OUT/'root-final-source-review.json')
 if {r['path'] for r in review['files']}!=set(GAME):raise RuntimeError('All8 actual C++ sources require review')
 for row in review['files']:
  matches(ROOT/row['path'],row)
  if row['path'] in old and old[row['path']]==(ROOT/row['path']).read_bytes():raise RuntimeError('No actual increment')
 original=BASE/'tw-native-record-grammar-source-01/source/tw-battle-variant-frontier.json'
 raw=original.read_bytes();saved=OUT/'retained-variant-inputs/prior169-frontier.json';save(saved,raw)
 origin=dict(path=original.relative_to(ROOT).as_posix(),copy=saved.relative_to(OUT).as_posix(),bytes=len(raw),sha256=sha(raw))
 variants=copy.deepcopy(json.loads(raw))
 if len(variants['entries'])!=30:raise RuntimeError('Prior30 battle entries required')
 variants.update(round=ROUND,prior169_inventory=origin,new_owned_raw_field_views=0,new_field_view_subcases=0,
                 new_native_values_discovered=0,new_complete_routes=0,original_169_entries_unchanged=True)
 dump(OUT/'source/tw-battle-variant-frontier.json',variants);dump(OUT/'retained-variant-inputs/origins.json',[origin])
 relations=dict(source_only=True,
  actual_TW_call_chain='Explicit Application Context -> actual movement source -> exact published ready lease -> strong controller/actual WorldOwner -> native Lua geometry/authority/full5D -> one common position CAS -> actual peer5E -> Session response queue',
  actual_active_ready_lease_qualified_by_session_account_character_generation=True,
  actual_current_saved_position_loaded_for_each_step=True,lease_original_position_not_recompared_after_movement=True,
  actual_source_owns_rules_and_WorldOwner=True,source_has_no_native_value_or_permission_defaults=True,
  actual_vault_movement_facades_are_weak_and_real_callbacks_game_owned=True,
  source_slot_requires_actual_Session_pointer_and_exact_full_lease=True,
  disconnect_release_requires_stored_Session_identity_not_cleared_delivery_identity=True,
  source_release_mutates_common_registries=False,malformed_entire_batch_rejected_before_actual_factory=True,
  caught_source_or_vault_reentry_invalidates_actual_provider_before_next_CAS=True,
  committed_position_prefix_rolled_back=False,full5D_encoded_and_peer_projection_prepared_before_CAS=True,
  old_frozen_source_retention=read(OUT/'root-retained-source-spans.json'),
  CN_receiver_context_count_changed=False,CN_unknown_helpers_phase_still_null=True,
  full_native_peer_policy_or_resources_recovered=False,native_scene_supplier_or_WorldOwner_implemented=False,
  actual_Main_selects_world_plan=False,local_queue_release_is_native_receipt=False,
  fanout_is_distributed_atomic=False,formal_application_hosted=False,complete_route=False,
  saved_variant_frontier=variants,parallel_agent_findings=[x['findings'] for x in agents],remaining=REMAINING)
 facts=dict(delta(),round=ROUND,previous_goal_turn_classification='progress: actual4 C++source increments and3sealedagentdeliveries in169',
  new_source_owner_chains=0,new_tw_source_owner_chains=0,new_native_phase_source_bindings=0,
  whole_game_route_total=None,whole_game_completed_routes=None,source_origin_records=len(records),
  formal_application_hosted=False,actual_world_plan_selected_in_Main=False,
  build_run=False,tests_run=False,new_tests_written=0,runtime_run=False,native_execution=False,
  Cplusplus_source_run=False,Lua_run=False,Windows_API_run=False,database_access=False,SQL_run=False,deployed=False,
  numeric_caps_changed=False,levels_changed=False,original_native_wire_layout_changed=False,
  formatter_capacity_chain_retried=False,protected_contexts=guarded,remaining=REMAINING)
 dump(OUT/'parallel-agent-deliveries.json',agents);dump(OUT/'source/reviewed-current-source-records.json',records)
 dump(OUT/'source/tw-common-movement-host-relations.json',relations);dump(OUT/'findings.json',facts)
 ledger_path=ROOT/BOOKS[1];ledger=read(ledger_path);old_ledger=json.loads(old[BOOKS[1]])
 if ledger['dual_client_source_segments']!=old_ledger['dual_client_source_segments'] or len(ledger['dual_client_source_segments'])!=161:
  raise RuntimeError('All161 prior source segments must remain')
 ledger['tw_common_movement_host_source']=dict(facts,evidence=OUT.relative_to(ROOT).as_posix())
 ledger['dual_client_source_segments'].append(dict(name=NAME,round=ROUND,
  version_scope='TW-CN-web-native-TW-common-movement-host-and-CN-receive-slot-source',
  status='Exact published lease connects owned movement source and explicit Application facade; real native WorldOwner and Main remain open',
  source_paths=sorted(paths),native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,
  tw_source_owner_chains_added=0,formal_application_hosted=False,complete_gameplay_routes_added=0,
  evidence=OUT.relative_to(ROOT).as_posix(),remaining=REMAINING))
 ledger['dual_client_execution_plan']['latest_work_round']=ROUND
 ledger['dual_client_execution_plan']['next_source_frontier']='Actual TW entry/reservation/resources/fullpeer policy/phased Current/Install/Cleanup/WorldOwner/full5D and mixed dispatcher; CN rights/native summary/world sources and0047DE70/004812B0 slots; ordinary Main. Whole gameplay/native state/variants and numeric TW-CN-web storage/wire/object/display remain open. PHASE1 no execution/tests.'
 ledger_path.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 with (ROOT/BOOKS[0]).open('a',encoding='utf-8') as handle:
  handle.write('\n\n## Actual TW common movement host source ('+ROUND+')\n\n'
   'Three agents delivered eight C++source increments (sixexisting/twonew) plus five bounded CN slot/callback relations. '
   'The actual game-owned published lease supplies a strongly owned controller/native WorldOwner/rules; malformed wholebatch rejects beforefactory. '
   'Explicit Application Context selects the actual movement/release/invalidate_active trio, weakVault facade requires completedscene; disconnect releases controller before lifecycle/DBteardown. '
   'Caught source or Vault reentry invalidates actual provider before next positionCAS; complete native5D is supplied and peerprojections prepared before singleCAS. Committedprefix remains durable. '
   'No actual native WorldOwner/resources/rights/full5D/Main was invented or selected; mixedworldrecords remain separate and frozenCUSTOM remains unchanged. '
   'CN slotcopies and knowncaller ECX/threadcallback relations add no unknownphase;14contexts/12qualified unchanged. Entire prior1692003sealedmembers and30battleentries retained. '
   'Packet/phase/fullroute0; source162; denominator/percentage null. No build/test/native/C++/Lua/API/DB/SQL/runtime/deployment; full TW-CN-web goal active.\n')
 origins=[]
 for i,rel in enumerate(sorted(paths|set(BOOKS))):
  raw=(ROOT/rel).read_bytes();dest=OUT/'source/current'/('s%03d'%i+Path(rel).suffix);save(dest,raw)
  origins.append(dict(path=rel,copy=dest.relative_to(OUT).as_posix(),bytes=len(raw),sha256=sha(raw),changed_this_round=rel not in old or old[rel]!=raw))
  if rel in old and old[rel]!=raw:
   diff=''.join(difflib.unified_diff(old[rel].decode('utf-8-sig').splitlines(True),raw.decode('utf-8-sig').splitlines(True),fromfile='before/'+rel,tofile='current/'+rel))
   if diff:save(OUT/'diff'/('d%03d.diff'%i),diff.encode('utf-8'))
 dump(OUT/'source/source-origins.json',origins)
 print(json.dumps(dict(round=ROUND,source_paths=len(paths),protected_files=len(guarded),modified_gameplay_source_files=8,new_complete_routes=0)))

def enrich():
 for p in reports():save(OUT/'reports/raw'/(p.parent.name+'-'+p.name),p.read_bytes())
 facts=read(OUT/'findings.json');relations=read(OUT/'source/tw-common-movement-host-relations.json')
 agents=read(OUT/'parallel-agent-deliveries.json');sources=read(CAT/'source-file-manifest.json')
 receipt=delta(sources,read(BASE/'endpoint-catalog169/source-file-manifest.json'))
 for p in [reports()[0],reports()[2]]:
  value=read(p);value['tw_common_movement_host_source']=facts;value['tw_common_movement_host_relations']=relations
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
  if (ROOT/row['path']).read_bytes()!=matches(OUT/row['copy'],row):raise RuntimeError('Retained variant drift')
 for row in read(OUT/'source/source-origins.json'):
  if (ROOT/row['path']).read_bytes()!=matches(OUT/row['copy'],row):raise RuntimeError('Root original source drift')
 for row in read(OUT/'root-final-source-review.json')['files']:matches(ROOT/row['path'],row)
 ledger=read(BASE/'packet-route-ledger.json');old_ledger=json.loads(old[BOOKS[1]])
 if len(ledger['dual_client_source_segments'])!=162 or ledger['dual_client_source_segments'][:161]!=old_ledger['dual_client_source_segments']:
  raise RuntimeError('Prior161 source segments changed')
 source_files=read(CAT/'source-file-manifest.json')
 for path,row in source_files.items():matches(ROOT/path,row)
 ledger_rows=[r for r in read(CAT/'input-manifest.json') if r['input']=='source-ledger']
 if len(ledger_rows)!=1 or matches(CAT/ledger_rows[0]['snapshot'],ledger_rows[0])!=(BASE/'packet-route-ledger.json').read_bytes():raise RuntimeError('Catalog ledger drift')
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
 cm=dict(format='god2-static-endpoint-catalog-seal-v1',round=CAT.name,**flags,files=inventory(CAT),current_source_files=len(source_files));dump(CAT/'manifest.json',cm)
 rm=dict(format='god2-static-source-delivery-seal-v1',round=ROUND,**flags,catalog=CAT.name,
  catalog_manifest_sha256=sha((CAT/'manifest.json').read_bytes()),before_files=len(rows),protected_files=len(guarded),
  gameplay_source_modified=True,modified_gameplay_source_files=8,completed_parallel_agents=3,
  new_complete_bidirectional_routes=0,whole_game_completion_percent=None,files=inventory(OUT));dump(OUT/'manifest.json',rm)
 print(json.dumps(dict(before_files=len(rows),protected_files=len(guarded),catalog_source_files=len(source_files),
  catalog_sealed_files=len(cm['files']),source_sealed_files=len(rm['files']),
  catalog_manifest_sha256=sha((CAT/'manifest.json').read_bytes()),source_manifest_sha256=sha((OUT/'manifest.json').read_bytes()))))

def main():
 if len(sys.argv)!=2 or sys.argv[1] not in ['account','enrich','seal']:raise RuntimeError('Choose account/enrich/seal')
 globals()[sys.argv[1]]()

if __name__=='__main__':main()
