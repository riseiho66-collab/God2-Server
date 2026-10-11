"""Static file/source accounting only; never executes game/native/SQL/tests."""
import copy
import difflib
import json
from pathlib import Path
import sys
from .parallel_game_connection_frontier_delivery import ROOT, sha, read, save, dump, matches, inventory

BASE=ROOT/'artifacts/integration/packet-connections-20261006'
NAME='tw-battle-state-source-01'
ROUND='20261008-tw-battle-state-source'
OUT=BASE/NAME
CAT=BASE/'endpoint-catalog165'
DOC='docs/research/tw-battle-state-source-20261008.md'
GAME=['src/protocol/RecoveredBattleActorControl.h','src/protocol/RecoveredBattleManagerControl.h',
      'src/net/Session.h','src/net/Session.cpp',
      'src/game/SharedTaiwanWorldLifecycle.h','src/game/SharedTaiwanWorldLifecycle.cpp']
WRITTEN=GAME+[DOC,'tools/reconstruction/tw_battle_state_source_delivery.py',
              'tools/reconstruction/dual_client_route_catalog.py']
BOOKS=['docs/PACKET_CONNECTION_GOAL_20261006.md',
       'artifacts/integration/packet-connections-20261006/packet-route-ledger.json']
AGENTS=['actor-control','manager-control','session-lifecycle']
PINS={'parallel-game-connection-frontier-01':
      '22faeaa28f404a8368456efb9cbb7ceb99c21967a16fecdbfbb768f43952d016',
      'endpoint-catalog164':'9ef70b8ab6c7569e774ba210e40282e13a31bd6e2cc7dcbc3fa5dd377f74c0fb'}
NATIVE_INPUT='artifacts/research/enemy-blackbox-20261006/consumer-experiment/inputs/native-image.bin'
REMAINING=[
 'TW battle raw views need actual native authority/prototype producers, lifetime/queue/state grammar and formal callers; no C2S pairing is inferred.',
 'Actual Application must supply per-session lifecycle factory, persisted position/revision, scene and full native 5D/6F/5E/73; legacy CharacterSelected is not actual InWorld publication.',
 'Actual TW/CN shared presence/visibility hosting and CN native issuer/rights/catalog/summary/world Reservation/Main selection remain required.',
 'Wide numeric persistent profiles/recovery and actual TW/CN/web wire/object/display plus qualified stack99 mutation callers remain open.',
 'Whole-game directional/state/variant denominator and complete bidirectional routes remain unknown; later full builds/tests/repairs/recovery/playable release remain open.']

def reports():
 return [BASE/'packet-progress-latest.json',BASE/'packet-progress-latest.md',
         BASE/'round-reports'/(ROUND+'.json'),BASE/'round-reports'/(ROUND+'.md')]

def before():
 p=OUT/'before-manifest.json'
 if sha(p.read_bytes())!='944325fea210b413201035bd84c1b8e925ebe5fb55c4aff67c113a4e8b81bfb1':
  raise RuntimeError('Preserve original before942 inventory')
 rows=read(p)
 if len(rows)!=942 or len({r['path'] for r in rows})!=942:raise RuntimeError('Before942 required')
 return rows,{r['path']:matches(OUT/r['snapshot'],r) for r in rows}

def prior():
 total=0
 for name,pin in PINS.items():
  raw=(BASE/name/'manifest.json').read_bytes()
  if sha(raw)!=pin or (OUT/'retained-prior'/name/'manifest.json').read_bytes()!=raw:
   raise RuntimeError('Immutable prior164 manifest changed')
  for row in json.loads(raw)['files']:matches(BASE/name/row['path'],row);total+=1
 if total!=2167:raise RuntimeError('Entire prior2167 inventory required')

def protected(rows,old):
 excluded=set(WRITTEN+BOOKS)|{p.relative_to(ROOT).as_posix() for p in reports()[:2]}
 result=[r for r in rows if r['path'] not in excluded]
 if len(result)!=933:raise RuntimeError('Protected933 required')
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
   if rel.startswith('artifacts/') and rel!=NATIVE_INPUT:
    raise RuntimeError('A receipt cannot substitute for an original source')
   if p.read_bytes()!=raw:raise RuntimeError('Current original source drift: '+rel)
   paths.add(rel);records.append(dict(agent=name,path=rel,source=row))
  deliveries.append(dict(agent=name,seal_file='seal.json',seal_sha256=sha((folder/'seal.json').read_bytes()),
   findings=read(folder/'findings.json'),current_source_origins=current,files=actual))
 return deliveries,paths,records

def variant_frontier():
 original=BASE/'parallel-game-connection-frontier-01/source/tw-battle-variant-frontier.json'
 raw=original.read_bytes();saved=OUT/'retained-variant-inputs/prior164-frontier.json';save(saved,raw)
 origin=dict(path=original.relative_to(ROOT).as_posix(),copy=saved.relative_to(OUT).as_posix(),bytes=len(raw),sha256=sha(raw))
 previous=json.loads(raw);result=copy.deepcopy(previous)
 if len(result['entries'])!=30:raise RuntimeError('Retain previous30 inventory entries')
 actor=read(OUT/'agents/actor-control/findings.json')
 manager=read(OUT/'agents/manager-control/source-map.json')
 for entry in result['entries']:
  # Retain every old field exactly. New annotation never silently changes164 qualifications.
  note=dict(round=ROUND,previous_inventory_entry_retained=True,complete_route=False,
            matched_native_C2S_producers=[],original_server_pairing_proven=False)
  if entry['opcode']=='83':
   action=entry['native_action_hex']
   if action in ['02','0C']:
    note.update(new_owned_consumer_view='RecoveredBattleActorControl::parse/encode',
     source_paths=[GAME[0]],logical_bytes=15,raw_fields=['BYTE2 source<28','BYTE3 operand','WORD5/7 target masks'],
     opaque_fields=['BYTE4','bytes9..14'],effect=actor['implementation']['distinct_effects'][action],
     runtime_emission_enabled=False,runtime_mutation_enabled=False,
     qualification='conditional consumer setup only; no game authority, HP-loss/single-enemy constraint or original native producer')
   elif action=='08':
    note.update(research_only=True,new_owned_consumer_view=None,
     native_effect='first stage acting-side0 nonzero WORD9 changes manager+4880/1; conditional actor setup+1EB=88,+232=0',
     source_evidence='agents/actor-control/native-evidence.json')
  else:
   selector=str(entry['native_selector'])
   if selector in ['2','3','4','5','6']:
    note.update(source_map=manager['selector'+selector],
     source_evidence='agents/manager-control/source-map.json',
     new_owned_consumer_view='RecoveredBattleManagerControl::parse_logical/encode_logical' if selector=='2' else None,
     field_view_native_sha256='5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde',
     previous_mapped_dispatch_sha256=entry['native_sha256'],
     evidence_epochs_separate=True,existing_3_4_5_source_metadata_only=selector in ['3','4','5'],
     runtime_emission_enabled=False,runtime_mutation_enabled=False)
  entry['round165_annotation']=note
 for old,new in zip(previous['entries'],result['entries']):
  if {k:v for k,v in new.items() if k!='round165_annotation'}!=old:raise RuntimeError('Retain old variant inventory fields')
 result.update(round=ROUND,prior164_inventory=origin,new_owned_raw_field_views=2,
  new_field_view_subcases=3,new_native_values_discovered=0,new_complete_routes=0,
  original_164_fields_unchanged=True,annotations_are_not_native_issuance_or_full_routes=True)
 dump(OUT/'source/tw-battle-variant-frontier.json',result)
 dump(OUT/'retained-variant-inputs/origins.json',[origin])
 return result

def account():
 if (OUT/'findings.json').exists() or (OUT/'manifest.json').exists():raise RuntimeError('Fresh unaccounted round required')
 rows,old=before();prior();guarded=protected(rows,old)
 agents,paths,records=agent_records();paths|=set(WRITTEN)
 for rel in GAME:
  if rel in old and old[rel]==(ROOT/rel).read_bytes():raise RuntimeError('Actual source increment required: '+rel)
 variants=variant_frontier()
 relations=dict(source_only=True,actual_session_call_chain=
  'TcpServer copies handler descriptor -> Session constructor validates without invoking -> actual select_character on game executor -> selected+complete world_frame -> once factory(Session&) -> fresh Binding hooks -> original prepared -> original world-tail ready -> original disconnect cleanup',
  actual_factory_assembly='SharedTaiwanWorldLifecycle::factory(actual shared presence, matching visibility, mandatory real Entered) -> fresh hooks/Binding per Session',
  external_direct_and_factory_configuration_exclusive=True,all_hooks_required=True,
  existing_Binding_and_hook_bodies_retained=True,legacy_world_state_not_promoted=True,
  actual_Application_factory_selected=False,actual_world_owner_data_supplied=False,
  shared_TW_CN_presence_visibility_Application_context_supplied=False,
  actual_native_account_issuer_or_login_rights_supplied=False,
  native_field_views=[GAME[0],GAME[1]],new_native_opcode_or_formula=False,
  native_83_views_emission_or_mutation_enabled=False,native_86_view_emission_or_mutation_enabled=False,
  saved_variant_frontier=variants,parallel_agent_findings=[a['findings'] for a in agents],
  formal_application_hosted=False,complete_route=False,remaining=REMAINING)
 facts=dict(round=ROUND,completed_parallel_agents=3,modified_gameplay_source_files=6,
  existing_source_files_modified=4,new_Cplusplus_source_files_added=2,
  new_owned_raw_field_views=2,new_field_view_subcases=3,
  actual_per_session_lifecycle_factory_callers_added=1,actual_per_session_lifecycle_factory_assemblers_added=1,
  source_origin_records=len(records),saved_TW_battle_variant_frontier_entries=30,
  new_packet_values=0,new_native_values_discovered=0,new_native_phase_source_bindings=0,
  new_source_owner_chains=0,new_tw_source_owner_chains=0,new_complete_bidirectional_routes=0,
  whole_game_route_total=None,whole_game_completed_routes=None,whole_game_completion_percent=None,
  formal_application_hosted=False,actual_native_factory_selected_in_Main=False,
  build_run=False,tests_run=False,new_tests_written=0,runtime_run=False,native_execution=False,
  Cplusplus_source_run=False,Lua_run=False,Windows_API_run=False,database_access=False,SQL_run=False,deployed=False,
  numeric_caps_changed=False,levels_changed=False,original_native_wire_layout_changed=False,
  formatter_capacity_chain_retried=False,protected_contexts=guarded,remaining=REMAINING)
 dump(OUT/'parallel-agent-deliveries.json',agents)
 dump(OUT/'source/reviewed-current-source-records.json',records)
 dump(OUT/'source/battle-state-and-world-lifecycle-relations.json',relations);dump(OUT/'findings.json',facts)
 ledger_path=ROOT/BOOKS[1];ledger=read(ledger_path);old_ledger=json.loads(old[BOOKS[1]])
 if ledger['dual_client_source_segments']!=old_ledger['dual_client_source_segments'] or len(ledger['dual_client_source_segments'])!=156:
  raise RuntimeError('All156 prior source segments must remain')
 ledger['tw_battle_state_source']=dict(facts,evidence=OUT.relative_to(ROOT).as_posix())
 ledger['dual_client_source_segments'].append(dict(name=NAME,round=ROUND,
  version_scope='TW-native-consumer-views-and-actual-per-session-world-lifecycle-in-shared-TW-CN-web-plan',
  status='Two owned native raw consumer views for three known subcases and actual per-Session factory invocation; Application/data owner not yet connected',
  source_paths=sorted(paths),native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,
  tw_source_owner_chains_added=0,formal_application_hosted=False,complete_gameplay_routes_added=0,
  evidence=OUT.relative_to(ROOT).as_posix(),remaining=REMAINING))
 plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
 plan['next_source_frontier']='Actual persisted TW position/scene owner -> per-session Application lifecycle factory -> same TW/CN presence/visibility. Continue battle producer-consumer state/variant grammar; actual CN issuer/rights/world Reservation/Main and wide persistent profiles/wire/object/display remain open. PHASE1 no execution/testing.'
 ledger_path.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 with (ROOT/BOOKS[0]).open('a',encoding='utf-8') as handle:
  handle.write('\n\n## TW battle fields and actual Session lifecycle ('+ROUND+')\n\n'
   'Three agents delivered six C++ source increments: two owned raw consumer field views for known83/02,0C and86/2; four existing source files connect the actual once-per-Session factory caller and fresh Binding assembly. '
   'Native emission/state mutation and actual Application hosting remain absent. Original30 battle inventory entries retained with separate new annotations; existing86/3/4/5 metadata and6 disjoint sides do not count as new discovery. '
   'Actual persisted world position/revision/scene/full native movement and recipient appearance sources, shared TW/CN presence and CN issuer/rights/Main remain open. '
   'Packet/phase/fullroute additions0; whole-game denominator/percentage null. No build/test/native/C++/Lua/DB/SQL/runtime/deploy. Full TW-CN-web goal remains active.\n')
 origins=[]
 for i,rel in enumerate(sorted(paths|set(BOOKS))):
  raw=(ROOT/rel).read_bytes();dest=OUT/'source/current'/('s%03d'%i+Path(rel).suffix);save(dest,raw)
  origins.append(dict(path=rel,copy=dest.relative_to(OUT).as_posix(),bytes=len(raw),sha256=sha(raw),
                      changed_this_round=rel not in old or old[rel]!=raw))
  if rel in old:
   delta=''.join(difflib.unified_diff(old[rel].decode('utf-8-sig').splitlines(True),raw.decode('utf-8-sig').splitlines(True),fromfile='before/'+rel,tofile='current/'+rel))
   if delta:save(OUT/'diff'/('d%03d.diff'%i),delta.encode('utf-8'))
 dump(OUT/'source/source-origins.json',origins)
 print(json.dumps(dict(round=ROUND,source_paths=len(paths),protected_files=len(guarded),modified_gameplay_source_files=6,new_complete_routes=0)))

def enrich():
 # Preserve the four raw CLI products exclusively before any report enrichment.
 for p in reports():save(OUT/'reports/raw'/(p.parent.name+'-'+p.name),p.read_bytes())
 facts=read(OUT/'findings.json');relations=read(OUT/'source/battle-state-and-world-lifecycle-relations.json')
 agents=read(OUT/'parallel-agent-deliveries.json');sources=read(CAT/'source-file-manifest.json')
 old_sources=read(BASE/'endpoint-catalog164/source-file-manifest.json')
 delta=dict(completed_parallel_agents=3,modified_gameplay_source_files=6,existing_source_files_modified=4,
  new_Cplusplus_source_files_added=2,new_owned_raw_field_views=2,new_field_view_subcases=3,
  actual_per_session_lifecycle_factory_callers_added=1,actual_per_session_lifecycle_factory_assemblers_added=1,
  saved_TW_battle_variant_frontier_entries=30,new_native_values_discovered=0,new_packet_values=0,
  new_phase_bindings=0,new_complete_bidirectional_routes=0,source_segments=157,
  current_catalog_source_files=len(sources),new_catalog_source_files=len(set(sources)-set(old_sources)),
  whole_game_completion_percent=None)
 for p in [reports()[0],reports()[2]]:
  v=read(p);v['tw_battle_state_source']=facts;v['battle_state_and_world_lifecycle_relations']=relations
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
 if len(ledger['dual_client_source_segments'])!=157 or ledger['dual_client_source_segments'][:156]!=old_ledger['dual_client_source_segments']:
  raise RuntimeError('Prior156 segments changed')
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
  gameplay_source_modified=True,modified_gameplay_source_files=6,completed_parallel_agents=3,
  new_complete_bidirectional_routes=0,whole_game_completion_percent=None,files=inventory(OUT))
 dump(OUT/'manifest.json',rm)
 print(json.dumps(dict(before_files=len(rows),protected_files=len(guarded),catalog_source_files=len(source_files),
  catalog_sealed_files=len(cm['files']),source_sealed_files=len(rm['files']),
  catalog_manifest_sha256=sha((CAT/'manifest.json').read_bytes()),source_manifest_sha256=sha((OUT/'manifest.json').read_bytes()))))

def main():
 if len(sys.argv)!=2 or sys.argv[1] not in ['account','enrich','seal']:raise RuntimeError('Choose account/enrich/seal')
 globals()[sys.argv[1]]()

if __name__=='__main__':main()
