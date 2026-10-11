"""Static files/source accounting; does not execute C++/native/SQLite/tests."""
import difflib
import hashlib
import json
from pathlib import Path
import sys
from .cn_wrapper_route_frontier import ROOT

BASE=ROOT/'artifacts/integration/packet-connections-20261006'
NAME='parallel-game-connection-frontier-01'
ROUND='20261008-parallel-game-connection-frontier'
OUT=BASE/NAME
CAT=BASE/'endpoint-catalog164'
DOC='docs/research/parallel-game-connection-frontier-20261008.md'
GAME=['src/db/NativeDeliverySnapshotSchema.h','src/db/NativeDeliverySnapshotSchema.cpp',
      'src/db/SqliteDatabase.h','src/db/SqliteDatabase.cpp','src/main.cpp']
WRITTEN=GAME+[DOC,'tools/reconstruction/parallel_game_connection_frontier_delivery.py',
              'tools/reconstruction/dual_client_route_catalog.py']
BOOKS=['docs/PACKET_CONNECTION_GOAL_20261006.md',
       'artifacts/integration/packet-connections-20261006/packet-route-ledger.json']
AGENTS=['native-delivery-schema','native-delivery-backend','native-delivery-cli']
PINS={'cn-account-native-source-materialization-01':
      '40de1e67844730cae6c7736e5ba19a76222c2909e76464bc0e1b758f69857f89',
      'endpoint-catalog163':'d4160fcd57b64fd3e60e549bf3592eb9f6cf9666164781f58088cb1bf527bf8f'}
REMAINING=[
 'Actual native account40/16 issuer data, phased login rights/catalog/deadline and summary visibility remain required; no values or permissions are fabricated.',
 'Ordinary Main has not selected the CN native factory; actual world Reservation/02/2A/scene/gameplay sources remain required.',
 'TW83/86 saved action/selector evidence must be expanded into state/variant producer-consumer routes without recounting old opcodes.',
 'Wide wallet/HP durable schema recovery, explicit numeric profiles/projectors/callers/checkpoints and TW/CN/web object/display remain OPEN; stack99 domain is not all mutations.',
 'Whole-game denominator/all bidirectional gameplay and later comprehensive builds/tests/repairs/recovery/playable publication remain OPEN.']

def sha(raw):return hashlib.sha256(raw).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,raw):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as handle:handle.write(raw)
def dump(p,v):save(p,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
def matches(p,r):
 raw=p.read_bytes()
 if len(raw)!=r['bytes'] or sha(raw)!=r['sha256']:raise RuntimeError('File receipt differs: '+str(p))
 return raw
def reports():
 return [BASE/'packet-progress-latest.json',BASE/'packet-progress-latest.md',
         BASE/'round-reports'/(ROUND+'.json'),BASE/'round-reports'/(ROUND+'.md')]
def before():
 rows=read(OUT/'before-manifest.json')
 if len(rows)!=938:raise RuntimeError('Before938 required')
 return rows,{r['path']:matches(OUT/r['snapshot'],r) for r in rows}
def prior():
 for name,pin in PINS.items():
  raw=(BASE/name/'manifest.json').read_bytes()
  if sha(raw)!=pin or (OUT/'retained-prior'/name/'manifest.json').read_bytes()!=raw:
   raise RuntimeError('Immutable prior163 changed')
  for r in json.loads(raw)['files']:matches(BASE/name/r['path'],r)
def protected(rows,old):
 excluded=set(WRITTEN+BOOKS)|{p.relative_to(ROOT).as_posix() for p in reports()[:2]}
 result=[r for r in rows if r['path'] not in excluded]
 for r in result:
  if (ROOT/r['path']).read_bytes()!=old[r['path']]:raise RuntimeError('Protected source changed: '+r['path'])
 return result
def inventory(folder):
 return [dict(path=p.relative_to(folder).as_posix(),bytes=p.stat().st_size,sha256=sha(p.read_bytes()))
         for p in sorted(folder.rglob('*')) if p.is_file() and p!=folder/'manifest.json']
def agent_records():
 deliveries=[];paths=set();records=[]
 for name in AGENTS:
  folder=OUT/'agents'/name;seal=read(folder/'seal.json')
  entries=seal.get('files',seal.get('entries',[]))
  if not entries:raise RuntimeError('Agent seal entries required')
  for row in entries:matches(folder/row['path'],row)
  current=read(folder/'current-source-origins.json')
  if isinstance(current,dict):current=current['source_files']
  if not current:raise RuntimeError('Full original current source copies required')
  for row in current:
   raw=matches(folder/row['copy'],row);p=Path(row['path'])
   if not p.is_absolute():p=ROOT/p
   rel=p.relative_to(ROOT).as_posix()
   if rel.startswith('artifacts/'):raise RuntimeError('Receipt is not an original source')
   if p.read_bytes()!=raw:raise RuntimeError('Agent source drift: '+rel)
   paths.add(rel);records.append(dict(agent=name,path=rel,source=row))
  deliveries.append(dict(agent=name,seal_file='seal.json',seal_sha256=sha((folder/'seal.json').read_bytes()),
    findings=read(folder/'findings.json'),current_source_origins=current,files=inventory(folder)))
 return deliveries,paths,records
def battle_variant_frontier():
 # Reuse historical pinned tables; no PE/native execution or new opcode claim.
 inputs={
  'tw83':BASE/'s2c-battle83-action-frontier-v1.json',
  'tw_battle':BASE/'endpoint-catalog163/inputs/tw-battle-consumers.json'}
 origins=[];values={}
 for key,p in inputs.items():
  raw=p.read_bytes();dest=OUT/'retained-variant-inputs'/(key+'.json');save(dest,raw)
  origins.append(dict(path=p.relative_to(ROOT).as_posix(),copy=dest.relative_to(OUT).as_posix(),bytes=len(raw),sha256=sha(raw)))
  values[key]=json.loads(raw)
 actions=values['tw83'];battle=values['tw_battle']
 if len(actions['actions'])!=23 or len(battle['battle_86_subtype_cases'])!=7:
  raise RuntimeError('Retain exact saved23/7 cases')
 if actions['native_sha256']!=battle['native_sha256']:
  raise RuntimeError('Do not blend native evidence epochs')
 entries=[]
 for row in actions['actions']:
  qualified=row['action_hex'] in ['01','03']
  entries.append(dict(id='tw:S2C:battle:83:action:'+row['action_hex']+':states-open',
   parent_endpoint_id='tw:S2C:battle:83:variants-open',version='tw',direction='S2C',phase='battle',opcode='83',
   native_action_hex=row['action_hex'],native_dispatch=dict(row),native_sha256=actions['native_sha256'],
   evidence_epoch='historical mapped149c; current installed font-restored99cd remains a separate baseline',
   source_projection='RecoveredBattleAttackPresentation::parse/hit' if qualified else None,
   scoped_source_caller='RecoveredPkActionProjection::logical -> OwnedPkRoomState staged common result (CUSTOM-0086)' if qualified else None,
   source_paths=['src/protocol/RecoveredBattleAttackPresentation.h','src/protocol/RecoveredPkActionProjection.h','src/handlers/OwnedPkRoomState.h'] if qualified else [],
   projection_qualification='only existing raw scalar prototype, one opposing target, hp_loss<=32767; no other shared case licensed' if qualified else 'no source projection qualified by this inventory',
   matched_native_C2S_producers=[],original_server_pairing_proven=False,complete_route=False,
   unresolved=['full native state/variant grammar','actual original authority/prototype producer','formal hosting and lifecycle','all actor/side/outcome variants']))
 for selector,target in sorted(battle['battle_86_subtype_cases'].items(),key=lambda item:int(item[0])):
  qualified=selector in ['0','1']
  entries.append(dict(id='tw:S2C:battle:86:selector:'+selector+':states-open',
   parent_endpoint_id='tw:S2C:battle:86:variants-open',version='tw',direction='S2C',phase='battle',opcode='86',
   native_selector=int(selector),native_case_rva=target,native_sha256=battle['native_sha256'],
   evidence_epoch='historical mapped149c; current installed client remains separate',
   source_projection='RecoveredBattleVitals::parse_logical/encode_logical' if qualified else None,
   scoped_source_caller='RecoveredPkActionProjection::logical/vital with source-owned raw template (CUSTOM-0086)' if qualified else None,
   source_paths=['src/protocol/RecoveredBattleVitals.h','src/protocol/RecoveredPkActionProjection.h','src/handlers/OwnedPkRoomState.h'] if qualified else [],
   projection_qualification=('HP actor/side still caller-qualified' if selector=='0' else 'MP actor write only for own side0; opposing MP record is not an applied update') if qualified else 'shared target (including6==0) does not license source aliases',
   matched_native_C2S_producers=[],original_server_pairing_proven=False,complete_route=False,
   unresolved=['native state/actor lifecycle and original issuance','opaque prototype provenance','all queued/deferred variants','formal hosting']))
 result=dict(kind='saved-native-TW-battle-subdispatch-source-frontier',entries=entries,
  inputs=origins,case_inventory_entries=30,tw83_action_values=23,tw86_selector_values=7,
  existing_source_scalar_action_values=2,existing_source_vital_selector_values=2,
  new_native_values_discovered=0,new_complete_routes=0,whole_game_route_total=None,
  native_case_target_sharing_is_not_semantic_equivalence=True)
 dump(OUT/'source/tw-battle-variant-frontier.json',result)
 dump(OUT/'retained-variant-inputs/origins.json',origins)
 return result
def account():
 if (OUT/'findings.json').exists() or (OUT/'manifest.json').exists():raise RuntimeError('Fresh unaccounted round required')
 rows,old=before();prior();guarded=protected(rows,old)
 agents,paths,records=agent_records();paths|=set(WRITTEN)
 if (OUT/'source/tw-battle-variant-frontier.json').exists():
  variants=read(OUT/'source/tw-battle-variant-frontier.json')
  for row in variants['inputs']:
   if (ROOT/row['path']).read_bytes()!=matches(OUT/row['copy'],row):raise RuntimeError('Saved variant metadata differs')
 else:variants=battle_variant_frontier()
 paths|={'src/protocol/RecoveredBattleAttackPresentation.h','src/protocol/RecoveredBattleVitals.h',
         'src/protocol/RecoveredPkActionProjection.h','src/handlers/OwnedPkRoomState.h'}
 for rel in GAME:
  if rel in old and old[rel]==(ROOT/rel).read_bytes():raise RuntimeError('Actual source increment required: '+rel)
 if (ROOT/'docs/custom-designs.json').read_bytes()!=old['docs/custom-designs.json']:
  raise RuntimeError('No custom/gameplay formula change in native storage wiring')
 relations=dict(source_only=True,actual_call_chain='main --migrate-only --native-delivery-schema -> same configured SqliteDatabase.migrate -> install_native_delivery_snapshot_schema -> NativeDeliverySnapshotSchema::install -> original common account/summary schemas and independent storage ledger -> same original reader/CAS writers',
  actual_existing_qualification_entry='SqliteDatabase::require_native_delivery_snapshot_schema -> NativeDeliverySnapshotSchema::require_existing',
  shared_tables=['account_native_snapshots','account_native_character_summaries','account_native_character_summary_rows'],
  original_repository_DDL_unchanged=True,immutable_base_migrations_unchanged=True,
  independent_feature_ledger_not_account_entitlement=True,partial_or_altered_target_not_adopted=True,
  no_implicit_installer_in_login_accessors_or_default_start=True,
  actual_native_data_imported=False,issuer_or_login_rights_generated=False,schema_installed=False,
  native_login_factory_selected_in_Main=False,storage_commit_is_native_ACK=False,
  new_native_opcode_or_custom_formula=False,complete_route=False,formal_application_hosted=False,
  parallel_agent_findings=[a['findings'] for a in agents],tw_saved_variant_frontier=variants,remaining=REMAINING)
 facts=dict(round=ROUND,previous_goal_turn_classification='verified wait: explicit live running agent handles were polled; current turn received concrete source evidence and implements the actual missing storage chain',
  completed_parallel_agents=3,actual_native_delivery_schema_installers_added=1,
  actual_same_database_native_schema_entries_added=2,actual_storage_only_CLI_callers_added=1,
  modified_gameplay_source_files=5,existing_source_files_modified=3,new_Cplusplus_source_files_added=2,
  source_origin_records=len(records),saved_TW_battle_variant_frontier_entries=30,
  new_packet_values=0,new_native_phase_source_bindings=0,
  new_source_owner_chains=0,new_tw_source_owner_chains=0,new_complete_bidirectional_routes=0,
  whole_game_route_total=None,whole_game_completed_routes=None,whole_game_completion_percent=None,
  formal_application_hosted=False,actual_native_factory_selected_in_Main=False,schema_registered_in_default_migrations=False,
  schema_installed=False,build_run=False,tests_run=False,new_tests_written=0,runtime_run=False,
  native_execution=False,Cplusplus_source_run=False,Windows_API_run=False,database_access=False,deployed=False,
  levels_changed=False,original_native_wire_layout_changed=False,protected_contexts=guarded,remaining=REMAINING)
 dump(OUT/'parallel-agent-deliveries.json',agents);dump(OUT/'source/reviewed-current-source-records.json',records)
 dump(OUT/'source/native-delivery-storage-and-frontier-relations.json',relations);dump(OUT/'findings.json',facts)
 ledger_path=ROOT/BOOKS[1];ledger=read(ledger_path);old_ledger=json.loads(old[BOOKS[1]])
 if ledger['dual_client_source_segments']!=old_ledger['dual_client_source_segments'] or len(ledger['dual_client_source_segments'])!=155:
  raise RuntimeError('All155 existing source segments must remain')
 ledger['parallel_game_connection_frontier']=dict(facts,evidence=OUT.relative_to(ROOT).as_posix())
 ledger['dual_client_source_segments'].append(dict(name=NAME,round=ROUND,
  version_scope='shared-pinned-native-delivery-storage-CAS-readers-and-TW-CN-web-open-frontiers',
  status='Explicit three-table independent schema qualifier/installer -> same migrated database -> actual schema-only CLI selected in source; no execution/data/rights/login activation',
  source_paths=sorted(paths),native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,
  tw_source_owner_chains_added=0,formal_application_hosted=False,complete_gameplay_routes_added=0,
  evidence=OUT.relative_to(ROOT).as_posix(),remaining=REMAINING))
 plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
 plan['next_source_frontier']='M1 TW83/86 saved native state/variant producer-consumer denominator; actual TW world owner/lifecycle caller; actual CN native data/issuer/rights/summary/world Reservation/Main source selection; wide persistent profiles/recovery and numeric actual caller/wire/object/display. PHASE1 no execution/testing.'
 ledger_path.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 with (ROOT/BOOKS[0]).open('a',encoding='utf-8') as handle:
  handle.write('\n\n## Parallel actual native delivery storage ('+ROUND+')\n\n'
   'Three resumed agents connected original native account/summary schema -> independent explicit schema qualifier/installer -> same migrated SQLite backend -> actual --migrate-only --native-delivery-schema CLI caller. '
   'Original DDL/base migrations/readers/writers/common identities unchanged; no native data/default permissions/Main CN factory/activation. '
  'Five C++ source files changed/added.30 saved TW83/86 subdispatch inventory records explicitly separate native cases, existing scoped projections and unresolved original authority/state/caller; no new native discovery or complete route. Separate numeric matrix and actual TW-world caller evidence identify next source work. '
   'Packet/phase/fullroute additions0; whole-game denominator/percentage null. No build/test/C++/native/SQLite/runtime/migration/deployment. Full TW-CN-web goal active.\n')
 origins=[]
 for rel in sorted(paths|set(BOOKS)):
  raw=(ROOT/rel).read_bytes();save(OUT/'source/current'/rel,raw)
  origins.append(dict(path=rel,bytes=len(raw),sha256=sha(raw),changed_this_round=rel not in old or old[rel]!=raw))
  if rel in old:
   delta=''.join(difflib.unified_diff(old[rel].decode('utf-8-sig').splitlines(True),raw.decode('utf-8-sig').splitlines(True),fromfile='before/'+rel,tofile='current/'+rel))
   if delta:save(OUT/'diff'/(rel+'.diff'),delta.encode('utf-8'))
 dump(OUT/'source/source-origins.json',origins)
 print(json.dumps(dict(round=ROUND,source_paths=len(paths),protected_files=len(guarded),modified_gameplay_source_files=5,new_complete_routes=0)))
def enrich():
 for p in reports():save(OUT/'reports/raw'/(p.parent.name+'-'+p.name),p.read_bytes())
 facts=read(OUT/'findings.json');relations=read(OUT/'source/native-delivery-storage-and-frontier-relations.json')
 agents=read(OUT/'parallel-agent-deliveries.json');sources=read(CAT/'source-file-manifest.json')
 old_sources=read(BASE/'endpoint-catalog163/source-file-manifest.json')
 delta=dict(completed_parallel_agents=3,actual_native_delivery_schema_installers_added=1,
  actual_same_database_native_schema_entries_added=2,actual_storage_only_CLI_callers_added=1,
  modified_gameplay_source_files=5,existing_source_files_modified=3,new_Cplusplus_source_files_added=2,
  saved_TW_battle_variant_frontier_entries=30,
  new_packet_values=0,new_phase_bindings=0,new_complete_bidirectional_routes=0,source_segments=156,
  current_catalog_source_files=len(sources),new_catalog_source_files=len(set(sources)-set(old_sources)),whole_game_completion_percent=None)
 for p in [reports()[0],reports()[2]]:
  v=read(p);v['parallel_game_connection_frontier']=facts;v['native_delivery_storage_relations']=relations
  v['parallel_agent_deliveries']=agents;v['current_round_source_delta']=delta
  p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 text=(ROOT/DOC).read_text(encoding='utf-8')+'\n\nStatic report delta:\n\n```json\n'+json.dumps(delta,indent=2)+'\n```\n'
 for p in [reports()[1],reports()[3]]:p.write_text(text,encoding='utf-8')
 dump(OUT/'reports/enrichment-receipt.json',delta);print(json.dumps(delta))
def seal():
 if (OUT/'manifest.json').exists() or (CAT/'manifest.json').exists():raise RuntimeError('Fresh seals required')
 rows,old=before();prior();guarded=protected(rows,old)
 current_agents,_,_=agent_records()
 if current_agents!=read(OUT/'parallel-agent-deliveries.json'):raise RuntimeError('Agent delivery drift')
 for row in read(OUT/'retained-variant-inputs/origins.json'):
  if (ROOT/row['path']).read_bytes()!=matches(OUT/row['copy'],row):raise RuntimeError('Saved native variant metadata drift')
 for row in read(OUT/'source/source-origins.json'):
  if (ROOT/row['path']).read_bytes()!=matches(OUT/'source/current'/row['path'],row):raise RuntimeError('Root source drift')
 ledger=read(BASE/'packet-route-ledger.json');old_ledger=json.loads(old[BOOKS[1]])
 if len(ledger['dual_client_source_segments'])!=156 or ledger['dual_client_source_segments'][:155]!=old_ledger['dual_client_source_segments']:
  raise RuntimeError('Prior155 segments changed')
 if (ROOT/'docs/custom-designs.json').read_bytes()!=old['docs/custom-designs.json']:raise RuntimeError('Custom registry changed')
 source_files=read(CAT/'source-file-manifest.json')
 for p,row in source_files.items():matches(ROOT/p,row)
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
  Windows_API_run=False,build_run=False,tests_run=False,runtime_run=False,database_access=False,deployed=False)
 cm=dict(format='god2-static-endpoint-catalog-seal-v1',round=CAT.name,**flags,files=inventory(CAT),current_source_files=len(source_files))
 dump(CAT/'manifest.json',cm)
 rm=dict(format='god2-static-source-delivery-seal-v1',round=ROUND,**flags,catalog=CAT.name,
  catalog_manifest_sha256=sha((CAT/'manifest.json').read_bytes()),before_files=len(rows),protected_files=len(guarded),
  gameplay_source_modified=True,modified_gameplay_source_files=5,completed_parallel_agents=3,
  new_complete_bidirectional_routes=0,whole_game_completion_percent=None,files=inventory(OUT))
 dump(OUT/'manifest.json',rm)
 print(json.dumps(dict(before_files=len(rows),protected_files=len(guarded),catalog_source_files=len(source_files),
  catalog_sealed_files=len(cm['files']),source_sealed_files=len(rm['files']),
  catalog_manifest_sha256=sha((CAT/'manifest.json').read_bytes()),source_manifest_sha256=sha((OUT/'manifest.json').read_bytes()))))
def main():
 if len(sys.argv)!=2 or sys.argv[1] not in ['account','enrich','seal']:raise RuntimeError('Choose account/enrich/seal')
 globals()[sys.argv[1]]()
if __name__=='__main__':main()
