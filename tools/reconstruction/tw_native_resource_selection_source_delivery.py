"""Immutable static file/source accounting; never runs native/gameplay/SQL."""
import copy
import difflib
import json
from pathlib import Path
import sys
from .parallel_game_connection_frontier_delivery import ROOT, sha, read, save, dump, matches, inventory

BASE=ROOT/'artifacts/integration/packet-connections-20261006'
NAME='tw-native-resource-selection-source-01'
ROUND='20261008-tw-native-resource-selection-source'
OUT=BASE/NAME
CAT=BASE/'endpoint-catalog175'
DOC='docs/research/tw-native-resource-selection-source-20261008.md'
GAME=['src/game/TaiwanNativeResourceSelection.h','src/game/TaiwanNativeResourceSelection.cpp','src/game/TaiwanNativeSceneResourceOwner.h',
      'src/game/TaiwanNativeSceneResourceOwner.cpp']
WRITTEN=GAME+[DOC,'tools/reconstruction/tw_native_resource_selection_source_delivery.py',
              'tools/reconstruction/cn_account_location_frontier175.py',
              'tools/reconstruction/tw_native_resource_selection175.py',
              'tools/reconstruction/dual_client_route_catalog.py']
BOOKS=['docs/PACKET_CONNECTION_GOAL_20261006.md',
       'artifacts/integration/packet-connections-20261006/packet-route-ledger.json']
AGENTS=['tw-resource-selection','tw-resource-owner','cn-location-frontier']
PINS={'tw-native-rom-geometry-source-01':'69159870422beaaae3b9d437ba8744f22ddcfe63dead1ee34ddd847d6b9aeb91',
      'endpoint-catalog174':'f03cc32160771225d090278449b3c6eee0d2bd74b3eef911a556dab0b07b10b6'}
NATIVE_INPUT='artifacts/research/enemy-blackbox-20261006/consumer-experiment/inputs/native-image.bin'
REMAINING=[
 'Actual TW native entry/reservation/resources/appearance/fullpeer policy/Current/Install/Cleanup remain mandatory inputs; request/prefix/cwd issuer, non-ASCII path mapping, native temporary-file failure behavior, dynamic asset/cache/object lifetime and real resource/scene generations remain required beyond the qualified selected-source owner.',
 'TW qualified asset/mask/material producers connect to original-derived grid and retained scene source, but runtime resource/cache replacement, timing/collision/pending/transfer/battle authority and complete5D remain unsupplied. Ordinary Main remains unselected.',
 'TW mixed world-record dispatch remains separately owned; this explicit movement binding rejects incompatible dispatchers and does not silently replace frozen CUSTOM rules.',
 'CN0047DE70/004812B0 phase/calling slots remain unknown. Actual nested receive owner/cursor transfer is not receive phase registration;14contexts/12qualified unchanged.',
 'CN actual native account issuer/rights/catalog/summary/assets/world Reservation/gameplay/scene publishers and ordinary Main selection remain open.',
 'Wide numeric persistent profiles/recovery/TW-CN-web wire/object/display, stack99 mutation callers, web WSS/TLS/hosting, whole-game denominator/routes and later comprehensive tests/repair/release remain open.']

def reports():
 return [BASE/'packet-progress-latest.json',BASE/'packet-progress-latest.md',
         BASE/'round-reports'/(ROUND+'.json'),BASE/'round-reports'/(ROUND+'.md')]

def before():
 p=OUT/'before-manifest.json'
 if sha(p.read_bytes())!='d41be7e12f13e1bbf802932483b03a98a20cc06f8601e316d79d7e7991d47cf0':
  raise RuntimeError('Original before1252 inventory changed')
 rows=read(p)
 if len(rows)!=1252 or len({r['path'] for r in rows})!=1252:raise RuntimeError('Before1252 required')
 return rows,{r['path']:matches(OUT/r['snapshot'],r) for r in rows}

def prior():
 total=0
 for name,pin in PINS.items():
  raw=(BASE/name/'manifest.json').read_bytes()
  if sha(raw)!=pin or (OUT/'retained-prior'/name/'manifest.json').read_bytes()!=raw:
   raise RuntimeError('Immutable prior174 manifest changed')
  for row in json.loads(raw)['files']:matches(BASE/name/row['path'],row);total+=1
 if total!=2124:raise RuntimeError('Entire prior2124 members required')

def protected(rows,old):
 excluded=set(WRITTEN+BOOKS)|{p.relative_to(ROOT).as_posix() for p in reports()[:2]}
 result=[r for r in rows if r['path'] not in excluded]
 if len(result)!=1247:raise RuntimeError('Protected1247 required')
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
  native_inputs=[];native_path=None
  for filename in ['original-inputs.json','native-original-inputs.json','native-input-originals.json','input-originals.json']:
   if (folder/filename).exists():native_path=folder/filename;break
  if native_path is not None:
   native_inputs=read(native_path)
   if not isinstance(native_inputs,list):raise RuntimeError('Simple original native input list required')
  if not native_inputs:raise RuntimeError('Complete original native input list required')
  for row in native_inputs:
   p=Path(row['path'])
   if not p.is_absolute() or p.read_bytes()!=matches(folder/row['copy'],row):raise RuntimeError('Native original drift')
  deliveries.append(dict(agent=name,seal_sha256=sha((folder/'seal.json').read_bytes()),
    findings=read(folder/'findings.json'),native_original_inputs=native_inputs,current_source_origins=current,files=actual))
 return deliveries,paths,records

def delta(sources=None,previous=None):
 cn=read(OUT/'agents/cn-location-frontier/findings.json')
 value=dict(completed_parallel_agents=3,modified_gameplay_source_files=4,existing_source_files_modified=0,
  new_Cplusplus_source_files_added=4,actual_TW_native_resource_selection_producers_added=1,
  actual_TW_game_owned_scene_resource_suppliers_added=1,
  CN_new_bounded_location_consumer_instruction_spans=cn['new_bounded_native_spans'],
  CN_new_location_source_relations=len(cn['new_native_relations']),
  CN_receiver_contexts=14,CN_receiver_contexts_qualified=12,
  new_owned_raw_field_views=0,new_field_view_subcases=0,saved_TW_battle_variant_frontier_entries=30,
  new_native_values_discovered=0,new_packet_values=0,new_phase_bindings=0,new_complete_bidirectional_routes=0,
  source_segments=167,whole_game_completion_percent=None,owner_requested_stop_after_round=True)
 if sources is not None:value.update(current_catalog_source_files=len(sources),new_catalog_source_files=len(set(sources)-set(previous)))
 return value

def account():
 if (OUT/'findings.json').exists() or (OUT/'manifest.json').exists():raise RuntimeError('Fresh unaccounted round required')
 rows,old=before();prior();guarded=protected(rows,old)
 agents,paths,records=agent_records();paths|=set(WRITTEN)
 review=read(OUT/'root-final-source-review.json')
 if {r['path'] for r in review['files']}!=set(GAME):raise RuntimeError('All4 actual C++ sources require review')
 for row in review['files']:
  matches(ROOT/row['path'],row)
  if row['path'] in old and old[row['path']]==(ROOT/row['path']).read_bytes():raise RuntimeError('No actual increment')
 original=BASE/'tw-native-rom-geometry-source-01/source/tw-battle-variant-frontier.json'
 raw=original.read_bytes();saved=OUT/'retained-variant-inputs/prior174-frontier.json';save(saved,raw)
 origin=dict(path=original.relative_to(ROOT).as_posix(),copy=saved.relative_to(OUT).as_posix(),bytes=len(raw),sha256=sha(raw))
 variants=copy.deepcopy(json.loads(raw))
 if len(variants['entries'])!=30:raise RuntimeError('Prior30 battle entries required')
 variants.update(round=ROUND,prior174_inventory=origin,new_owned_raw_field_views=0,new_field_view_subcases=0,
                 new_native_values_discovered=0,new_complete_routes=0,original_174_entries_unchanged=True)
 dump(OUT/'source/tw-battle-variant-frontier.json',variants);dump(OUT/'retained-variant-inputs/origins.json',[origin])
 relations=dict(source_only=True,
  actual_TW_call_chain='Actual TW raw request/prefix/context and qualified native file selection -> full owned selected HMD and ordinal/name ROM sources -> existing174 RomBound model geometry/material -> existing172 mode2 grid -> concrete game-owned scene resource supplier -> existing Scene factory/WorldOwner -> existing170 source/controller -> mandatory actual authority/full5D -> one common position CAS -> retained actor publication -> recipient-native5E -> Session5D',
  prior171_to174_reader_grid_mask_ROM_HMD_decoder_recovery_not_recounted=True,
  actual_TW_native_file_selection_and_raw_request_concatenation_recovered=True,
  native_file_selection_evidence_distinct_from_CN_reference=True,
  ROM_and_text_candidate_suffix_rules_are_distinct=True,
  selected_0516_failure_does_not_qualify_plain_fallback=True,
  original_raw_reference_prefix_context_and_opened_candidate_retained=True,
  selected_filename_domain_ASCII_only_other_mappings_remain_open=True,
  native_text_temporary_file_reopen_failures_recreated=False,
  concrete_game_owned_resource_supplier_calls_existing_scene_factory=True,
  install_replace_remove_exact_entry_lineage_implemented=True,
  every_scene_supply_has_private_exact_incarnation=True,
  pending_retains_exact_one_use_actual_permit_identity=True,
  caught_reentry_detaches_affected_entry_without_reviving_on_next_operation=True,
  stale_scene_or_permit_does_not_invalidate_successor_incarnation=True,
  CN_account_location_field_gameplay_semantics_recovered=False,
  CN_state1A_projection_is_local_cache_mutation_not_server07_producer=True,
  qualified_HMD_version='exact v1.6',prior173_original0516_resource_decoder_retained=True,
  prior173_native_initial_placement_selector_to_object_plus30_retained=True,
  native_stable_order_uses_screenY_plus_actual_model_height_not_mask_height=True,
  prior_explicit_geometry_domain_native_tile_types=[2,7],
  full_raw_ROM_reference_and_actual_ordinal_binding_mandatory=True,
  ROM_action_operand_retains_full_DWORD_bits=True,
  first_step_terminal_scan_does_not_execute_commands=True,
  image_metadata_domain_is_qualified_not_all_native_image_formats=True,
  unknown_or_missing_ROM_image_geometry_is_unknown_not_mask_height=True,
  actual_asset_to_existing_Resources_and_Native_producer_implemented=True,
  actual_immutable_grid_and_generations_qualified_before_and_after_delegate_Current=True,
  composed_grid_has_no_fake_native_addresses=True,
  material_deep_copied_before_composition_and_storage_immutable=True,
  existing_scene_owns_grid_value_without_mutable_shared_grid_alias=True,
  qualified_domain_positive_full_masks_and_nonoverflow_DWORD=True,
  complete_known_selected_mask_OOB_uses_recovered_AL1_not_permission=True,
  destination_OOB_uses_recovered_assert_and_skip_not_missing_mask_default=True,
  native_cell_tags_preserved_without_static_consensus_normalization=True,
  missing_or_incomplete_material_is_unknown_not_zero=True,actual_scene_inputs_strongly_owned=True,
  actual_source_factory_compatible_with_existing170_handler=True,
  exact_Session_and_lease_and_saved_position_qualified=True,
  native_scene_generation_and_resource_Current_mandatory=True,
  native_server_timing_permissions_or_full5D_guessed=False,
  full5D_and_one_use_authority_publication_prepared_before_position_CAS=True,
  committed_prefix_rolled_back=False,retained_actor_direction_and_position_updated_after_actual_CAS=True,
  scene_publication_incarnation_is_original_native_counter=False,
  existing_CPP_and_all_Lua_unchanged=True,new_selection_and_resource_owner_CPP_sources_added=4,
  CN_receiver_context_count_changed=False,CN_unknown_helpers_phase_still_null=True,
  full_native_peer_policy_or_resources_recovered=False,concrete_native_WorldOwner_implemented=True,
  actual_native_material_issuer_configured=False,actual_original_server_authority_configured=False,
  actual_per_ROM_runtime_resource_generation_Current_supplied=False,
  actual_Main_selects_world_plan=False,local_queue_release_is_native_receipt=False,
  fanout_is_distributed_atomic=False,formal_application_hosted=False,complete_route=False,
  saved_variant_frontier=variants,parallel_agent_findings=[x['findings'] for x in agents],remaining=REMAINING)
 facts=dict(delta(),round=ROUND,previous_goal_turn_classification='progress: actual2 new ROM and2 modified map C++sources and3sealedagentdeliveries in174',
  new_source_owner_chains=0,new_tw_source_owner_chains=0,new_native_phase_source_bindings=0,
  whole_game_route_total=None,whole_game_completed_routes=None,source_origin_records=len(records),
  formal_application_hosted=False,actual_world_plan_selected_in_Main=False,
  build_run=False,tests_run=False,new_tests_written=0,runtime_run=False,native_execution=False,
  Cplusplus_source_run=False,Lua_run=False,Windows_API_run=False,database_access=False,SQL_run=False,deployed=False,
  numeric_caps_changed=False,levels_changed=False,original_native_wire_layout_changed=False,
  formatter_capacity_chain_retried=False,protected_contexts=guarded,remaining=REMAINING)
 dump(OUT/'parallel-agent-deliveries.json',agents);dump(OUT/'source/reviewed-current-source-records.json',records)
 dump(OUT/'source/tw-native-resource-selection-relations.json',relations);dump(OUT/'findings.json',facts)
 ledger_path=ROOT/BOOKS[1];ledger=read(ledger_path);old_ledger=json.loads(old[BOOKS[1]])
 if ledger['dual_client_source_segments']!=old_ledger['dual_client_source_segments'] or len(ledger['dual_client_source_segments'])!=166:
  raise RuntimeError('All166 prior source segments must remain')
 ledger['tw_native_resource_selection_source']=dict(facts,evidence=OUT.relative_to(ROOT).as_posix())
 ledger['dual_client_source_segments'].append(dict(name=NAME,round=ROUND,
  version_scope='TW-CN-web-native-TW-resource-selection-scene-source-owner-and-CN-account-location-frontier',
  status='Qualified native TW selected resources feed concrete game-owned map/ROM/material/scene supplier; dynamic lifecycle/authority/Main remain open',
  source_paths=sorted(paths),native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,
  tw_source_owner_chains_added=0,formal_application_hosted=False,complete_gameplay_routes_added=0,
  evidence=OUT.relative_to(ROOT).as_posix(),remaining=REMAINING))
 ledger['dual_client_execution_plan']['latest_work_round']=ROUND
 ledger['dual_client_execution_plan']['owner_requested_stop_after_work_round']=ROUND
 ledger['dual_client_execution_plan']['next_source_frontier']='Actual TW native map selection/resource and ordered object lifecycle/cache replacement, entry/fullpeer Current/Install/Cleanup, actual timing/pending/server rights/full5D and mixed dispatcher; CN rights/native summary/world sources and0047DE70/004812B0 slots; ordinary Main. Whole gameplay/native variants and numeric TW-CN-web storage/wire/object/display remain open. PHASE1 no execution/tests.'
 ledger_path.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 with (ROOT/BOOKS[0]).open('a',encoding='utf-8') as handle:
  handle.write('\n\n## TW native resource selection and game-owned scene source ('+ROUND+')\n\n'
   'Three agents delivered four new selection/resource owner C++sources. Qualified actual native TW selected resources feed exact ordinal/reference-bound map material and a concrete game-owned source supplier for the existing scene factory. '
   'TW proof remains distinct from CN references; rawtags and actual material provenance/generation/Current remain mandatory. No native x86 addresses or unknown permissions are fabricated. '
   'The existing WorldOwner/movement factory/controller/one common position CAS remain unchanged; actualAuthority/full5D/one-use publication still required. '
   'CN actual account location consumer evidence does not invent map/coordinate semantics or unknown receivephase;14contexts/12qualified unchanged. ExistingC++/allLua/nativeEXE/DB unchanged. '
   'Entire prior1742124sealedmembers and30battleentries retained. Packet/phase/fullroute0; source167; denominator/percentage null. '
   'Unqualifiednativepaths/dynamiclifecycle/actualserverrights/full5D/runtimecache/Main/fullgame remain OPEN. No build/test/native/C++/Lua/API/DB/SQL/runtime/deployment. '
   'Owner explicitly requested stopping after this175 round; preserve full objective and pause goal after completed accounting/seal, no next round.\n')
 origins=[]
 for i,rel in enumerate(sorted(paths|set(BOOKS))):
  raw=(ROOT/rel).read_bytes();dest=OUT/'source/current'/('s%03d'%i+Path(rel).suffix);save(dest,raw)
  origins.append(dict(path=rel,copy=dest.relative_to(OUT).as_posix(),bytes=len(raw),sha256=sha(raw),changed_this_round=rel not in old or old[rel]!=raw))
  if rel in old and old[rel]!=raw:
   diff=''.join(difflib.unified_diff(old[rel].decode('utf-8-sig').splitlines(True),raw.decode('utf-8-sig').splitlines(True),fromfile='before/'+rel,tofile='current/'+rel))
   if diff:save(OUT/'diff'/('d%03d.diff'%i),diff.encode('utf-8'))
 dump(OUT/'source/source-origins.json',origins)
 print(json.dumps(dict(round=ROUND,source_paths=len(paths),protected_files=len(guarded),modified_gameplay_source_files=4,new_complete_routes=0)))

def enrich():
 for p in reports():save(OUT/'reports/raw'/(p.parent.name+'-'+p.name),p.read_bytes())
 facts=read(OUT/'findings.json');relations=read(OUT/'source/tw-native-resource-selection-relations.json')
 agents=read(OUT/'parallel-agent-deliveries.json');sources=read(CAT/'source-file-manifest.json')
 receipt=delta(sources,read(BASE/'endpoint-catalog174/source-file-manifest.json'))
 for p in [reports()[0],reports()[2]]:
  value=read(p);value['tw_native_resource_selection_source']=facts;value['tw_native_resource_selection_relations']=relations
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
 if len(ledger['dual_client_source_segments'])!=167 or ledger['dual_client_source_segments'][:166]!=old_ledger['dual_client_source_segments']:
  raise RuntimeError('Prior166 source segments changed')
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
  gameplay_source_modified=True,modified_gameplay_source_files=4,completed_parallel_agents=3,
  new_complete_bidirectional_routes=0,whole_game_completion_percent=None,files=inventory(OUT));dump(OUT/'manifest.json',rm)
 print(json.dumps(dict(before_files=len(rows),protected_files=len(guarded),catalog_source_files=len(source_files),
  catalog_sealed_files=len(cm['files']),source_sealed_files=len(rm['files']),
  catalog_manifest_sha256=sha((CAT/'manifest.json').read_bytes()),source_manifest_sha256=sha((OUT/'manifest.json').read_bytes()))))

def main():
 if len(sys.argv)!=2 or sys.argv[1] not in ['account','enrich','seal']:raise RuntimeError('Choose account/enrich/seal')
 globals()[sys.argv[1]]()

if __name__=='__main__':main()
