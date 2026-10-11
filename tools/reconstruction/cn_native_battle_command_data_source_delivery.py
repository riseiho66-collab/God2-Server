"""Immutable static source accounting only; no gameplay, build or DB execution."""
import difflib
import json
from pathlib import Path
import sys
from .parallel_game_connection_frontier_delivery import ROOT, sha, read, save, dump, matches, inventory

BASE=ROOT/'artifacts/integration/packet-connections-20261006'
NAME='cn-native-battle-command-data-source-01'
ROUND='20261009-cn-native-battle-command-data-source'
OUT=BASE/NAME
CAT=BASE/'endpoint-catalog192'
DOC='docs/research/cn-native-battle-command-data-source-20261009.md'
GAME=['src/cn/world/SharedWorldGameplay.h','src/cn/world/SharedWorldGameplay.cpp',
 'src/cn/world/SharedNativeBattleCommandData.h','src/cn/world/SharedNativeBattleCommandData.cpp',
 'src/cn/protocol/CnBattleSkillDefinition.h','src/cn/protocol/CnBattleInventorySlot.h']
BOOKS=['docs/PACKET_CONNECTION_GOAL_20261006.md',
 'artifacts/integration/packet-connections-20261006/packet-route-ledger.json']
WRITTEN=GAME+[DOC,'tools/reconstruction/cn_native_battle_command_data_source_delivery.py',
 'tools/reconstruction/dual_client_route_catalog.py','tools/reconstruction/cn_battle_skill_command_frontier192.py',
 'tools/reconstruction/cn_battle_inventory_frontier192.py','tools/reconstruction/cn_battle_command_data192.py']
AGENTS=['cn-battle-skill-command-frontier','cn-battle-inventory-frontier','cn-battle-command-data']
PINS={'cn-native-battle-command-group-source-01':'bdba4b6214ac40646531e75880550675408cc646ba31b2f4b8f642d4378dd911',
 'endpoint-catalog191':'5112934946f0cda8a34b77d5f20dada633af5eacad86e087d28c1227c0df3fe3'}
REMAINING=[
 'Actual CN C2S35 full17-byte source reaches an explicitly selected real battle owner through ongoing Gameplay; no default battle admission, grant, target/core identity, rule, cost or success.',
 'Native S82 context/S86 grant/current battle incarnation/actor ownership/primary-secondary/targets/formation/learned skills/MP/range/held item/duplicates/once settlement and actual reply suppliers remain mandatory OPEN work.',
 'Unknown command kinds/opaque bytes remain raw; C56 and S2C world35 and TW CUSTOM are separate evidence/authority scopes.',
 'Actual shared skill definition and inventory dictionary lookup sources reach necessary DataAuthority, but native grouping, learned/custody/target/cost/settlement/reply authority remains OPEN; do not infer rights from a record or raw key.',
 'Full native close/window/target/entry/appearance/audience/rights/header/body/codepage/cipher suppliers, Main and whole-game directional/state/variant denominator remain OPEN.',
 'TW-CN-web common64/qualified stack99 and production WSS/TLS/hosting remain full scope; all source connections before comprehensive build/tests/verification/repair/recovery/release.']

def reports():
 return [BASE/'packet-progress-latest.json',BASE/'packet-progress-latest.md',
  BASE/'round-reports'/(ROUND+'.json'),BASE/'round-reports'/(ROUND+'.md')]

def before():
 raw=(OUT/'before-manifest.json').read_bytes()
 if sha(raw)!='9daea736af7dd6bfb890e0e197d31072d64d5cba75f21aa6ee2bd7aa22df1ae2':
  raise RuntimeError('Original before1373 changed')
 rows=json.loads(raw)
 if len(rows)!=1373 or len({r['path'] for r in rows})!=1373:raise RuntimeError('Before1373 required')
 return rows,{r['path']:matches(OUT/r['snapshot'],r) for r in rows}

def prior():
 count=0
 for name,pin in PINS.items():
  raw=(BASE/name/'manifest.json').read_bytes()
  if sha(raw)!=pin or raw!=(OUT/'retained-prior'/name/'manifest.json').read_bytes():
   raise RuntimeError('Prior191 immutable manifest drift')
  for row in json.loads(raw)['files']:matches(BASE/name/row['path'],row);count+=1
 if count!=2448:raise RuntimeError('Entire prior2448 members required')

def protected(rows,old):
 excluded=set(WRITTEN+BOOKS)|{p.relative_to(ROOT).as_posix() for p in reports()[:2]}
 guarded=[r for r in rows if r['path'] not in excluded]
 for row in guarded:
  if (ROOT/row['path']).read_bytes()!=old[row['path']]:raise RuntimeError('Protected source changed: '+row['path'])
 return guarded

def agent_records():
 records=[];paths=set();deliveries=[]
 for name in AGENTS:
  folder=OUT/'agents'/name;seal=read(folder/'seal.json')
  members=seal if isinstance(seal,list) else next((seal[key] for key in ('files','entries','members') if isinstance(seal.get(key),list)),None)
  if members is None and (folder/'LIST.json').exists():
   raw=(folder/'LIST.json').read_bytes();listed=json.loads(raw)
   if sha(raw)!=seal.get('list_sha256') or not isinstance(listed,list) or len(listed)!=seal.get('listed_members'):
    raise RuntimeError('Actual separately sealed LIST drift: '+name)
   members=listed+[dict(path='LIST.json',bytes=len(raw),sha256=sha(raw))]
   if len(members)!=seal.get('members'):raise RuntimeError('Full LIST member count drift')
  if not members:raise RuntimeError('Full agent seal required: '+name)
  for row in members:matches(folder/row['path'],row)
  actual=inventory(folder)
  if {r['path'] for r in actual}!={r['path'] for r in members}|{'seal.json'}:
   raise RuntimeError('Agent inventory drift: '+name)
  current=read(folder/'current-source-origins.json')
  if not isinstance(current,list) or not current:raise RuntimeError('Full current source originals required')
  for row in current:
   raw=matches(folder/row['copy'],row);p=Path(row['path'])
   if not p.is_absolute():p=ROOT/p
   rel=p.relative_to(ROOT).as_posix()
   if rel in BOOKS or rel=='tools/reconstruction/dual_client_route_catalog.py' or rel.startswith('artifacts/'):
    raise RuntimeError('Mutable receipt is not agent source original: '+rel)
   if p.read_bytes()!=raw:raise RuntimeError('Actual current source drift: '+rel)
   paths.add(rel);records.append(dict(agent=name,path=rel,source=row))
  inputs=read(folder/'original-inputs.json')
  if not isinstance(inputs,list):raise RuntimeError('Simple actual original input list required')
  for row in inputs:
   p=Path(row['path'])
   archived=matches(folder/row['copy'],row)
   if not p.is_absolute():raise RuntimeError('Absolute actual original input required')
   if p.read_bytes()!=archived:raise RuntimeError('Actual full original input drift: '+str(p))
  deliveries.append(dict(agent=name,seal_sha256=sha((folder/'seal.json').read_bytes()),
   findings=read(folder/'findings.json'),original_inputs=inputs,current_source_origins=current,files=actual))
 return deliveries,paths,records

def delta(sources=None):
 items=read(OUT/'agents/cn-battle-inventory-frontier/findings.json')
 data=read(OUT/'agents/cn-battle-command-data/findings.json')
 skills=read(OUT/'agents/cn-battle-skill-command-frontier/findings.json')
 v=dict(completed_parallel_agents=3,new_Cplusplus_source_files_added=4,
  existing_Cplusplus_source_files_modified=2,modified_gameplay_source_files=6,
  readonly_CN_skill_definition_views_added=1,readonly_CN_inventory_slot_views_added=1,
  actual_CN_battle_command_data_sources_added=1,
  actual_CN_battle_command_data_ingress_compositions_added=1,
  actual_CN_shared_skill_command_lookups_added=1,actual_CN_inventory_command_source_lookups_added=1,
  cn_battle_inventory_findings=items,cn_battle_command_data_findings=data,cn_battle_skill_command_findings=skills,
  new_packet_values=0,new_phase_bindings=0,new_complete_bidirectional_routes=0,
  source_segments=184,whole_game_completion_percent=None,
  owner_explicit_resume=True,whole_source_before_build_tests=True)
 if sources is not None:
  previous=read(BASE/'endpoint-catalog191/source-file-manifest.json')
  v.update(current_catalog_source_files=len(sources),new_catalog_source_files=len(set(sources)-set(previous)))
 return v

def account():
 if (OUT/'findings.json').exists() or (OUT/'manifest.json').exists():raise RuntimeError('Fresh round required')
 rows,old=before();prior();guarded=protected(rows,old);agents,paths,records=agent_records()
 review=read(OUT/'root-final-source-review.json')
 capacity=read(OUT/'policy/capacity-before-final-account.json')
 if capacity['unreadable_count'] or capacity['logical_bytes']>=capacity['limit_bytes']:raise RuntimeError('Whole project capacity input incomplete or over limit')
 for row in read(OUT/'root-context-source-origins.json'):
  if matches(ROOT/row['path'],row)!=matches(OUT/row['copy'],row):raise RuntimeError('Actual root transport/source context drift')
  paths.add(row['path'])
 if {r['path'] for r in review['files']}!=set(GAME):raise RuntimeError('All6 C++ sources require complete original copies and current definition review')
 for row in review['files']:
  if matches(ROOT/row['path'],row)!=matches(OUT/row['copy'],row):raise RuntimeError('Reviewed full original drift')
  if row['path'] in old and (ROOT/row['path']).read_bytes()==old[row['path']]:raise RuntimeError('No actual source increment')
 facts=dict(delta(),round=ROUND,new_source_owner_chains=0,new_tw_source_owner_chains=0,
  whole_game_route_total=None,whole_game_completed_routes=None,formal_application_hosted=False,
  actual_world_plan_selected_in_Main=False,build_run=False,tests_run=False,runtime_run=False,
  native_execution=False,Cplusplus_source_run=False,Lua_run=False,Windows_API_run=False,
  database_access=False,SQL_run=False,deployed=False,formatter_capacity_chain_retried=False,
  protected_contexts=guarded,remaining=REMAINING)
 dump(OUT/'parallel-agent-deliveries.json',agents);dump(OUT/'source/reviewed-current-source-records.json',records)
 dump(OUT/'findings.json',facts)
 ledger_path=ROOT/BOOKS[1];ledger=read(ledger_path);previous=json.loads(old[BOOKS[1]])
 if ledger['dual_client_source_segments']!=previous['dual_client_source_segments'] or len(ledger['dual_client_source_segments'])!=183:
  raise RuntimeError('Prior183 source segments changed')
 paths|=set(WRITTEN)
 ledger['cn_native_battle_command_data_source']=facts
 if ledger['world_unconnected_gameplay_opcodes']!=previous['world_unconnected_gameplay_opcodes']:
  raise RuntimeError('Prior unconnected gameplay classification changed')
 ledger['dual_client_source_segments'].append(dict(name=NAME,round=ROUND,
  version_scope='CN-native-C2S35-actual-shared-skill-and-inventory-command-data-source',
  status='Actual native C35 skill/item selectors connect pinned shared skill records and owned current inventory dictionaries to mandatory real DataAuthority through existing ordered grouping. Existence is not learned permission, item custody or native settlement; actual authority/core/cost/replies/Main remain OPEN',
  source_paths=sorted(paths),native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,
  tw_source_owner_chains_added=0,formal_application_hosted=False,complete_gameplay_routes_added=0,
  evidence=OUT.relative_to(ROOT).as_posix(),remaining=REMAINING))
 plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
 plan['owner_explicit_resume_after_stop']=ROUND
 plan['owner_requested_stop_after_work_round']=None
 plan['next_source_frontier']='Actual CN battle context/grant issuer, shared common skill/item custody/rules, once settlement/native replies/Main and all TW-CN-web routes before comprehensive builds/tests.'
 ledger_path.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 origins=[]
 for i,rel in enumerate(sorted(paths|set(BOOKS))):
  raw=(ROOT/rel).read_bytes();dest=OUT/'source/current'/('s%03d'%i+Path(rel).suffix);save(dest,raw)
  origins.append(dict(path=rel,copy=dest.relative_to(OUT).as_posix(),bytes=len(raw),sha256=sha(raw),
   changed_this_round=rel not in old or old[rel]!=raw))
  if rel in old and raw!=old[rel]:
   diff=''.join(difflib.unified_diff(old[rel].decode('utf-8-sig').splitlines(True),raw.decode('utf-8-sig').splitlines(True),fromfile='before/'+rel,tofile='current/'+rel))
   if diff:save(OUT/'diff'/('d%03d.diff'%i),diff.encode())
 dump(OUT/'source/source-origins.json',origins)
 print(json.dumps(dict(round=ROUND,protected_files=len(guarded),source_files=len(paths),new_complete_routes=0)))

def enrich():
 for p in reports():save(OUT/'reports/raw'/(p.parent.name+'-'+p.name),p.read_bytes())
 receipt=delta(read(CAT/'source-file-manifest.json'));facts=read(OUT/'findings.json');agents=read(OUT/'parallel-agent-deliveries.json')
 for p in [reports()[0],reports()[2]]:
  v=read(p);v['cn_native_battle_command_data_source']=facts;v['parallel_agent_deliveries']=agents;v['current_round_source_delta']=receipt
  p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 text=(ROOT/DOC).read_text(encoding='utf-8')+'\n\nStatic source accounting delta:\n\n```json\n'+json.dumps(receipt,indent=2)+'\n```\n'
 for p in [reports()[1],reports()[3]]:p.write_text(text,encoding='utf-8')
 dump(OUT/'reports/enrichment-receipt.json',receipt);print(json.dumps(receipt))

def seal():
 if (OUT/'manifest.json').exists() or (CAT/'manifest.json').exists():raise RuntimeError('Fresh immutable seals required')
 rows,old=before();prior();guarded=protected(rows,old);agents,_,_=agent_records()
 if agents!=read(OUT/'parallel-agent-deliveries.json'):raise RuntimeError('Agent delivery drift')
 for row in read(OUT/'source/source-origins.json'):
  if (ROOT/row['path']).read_bytes()!=matches(OUT/row['copy'],row):raise RuntimeError('Root source drift')
 for row in read(OUT/'root-final-source-review.json')['files']:matches(ROOT/row['path'],row)
 ledger=read(BASE/'packet-route-ledger.json');previous=json.loads(old[BOOKS[1]])
 if len(ledger['dual_client_source_segments'])!=184 or ledger['dual_client_source_segments'][:183]!=previous['dual_client_source_segments']:
  raise RuntimeError('Prior183 segments changed')
 sources=read(CAT/'source-file-manifest.json')
 for path,row in sources.items():matches(ROOT/path,row)
 lm=[r for r in read(CAT/'input-manifest.json') if r['input']=='source-ledger']
 if len(lm)!=1 or matches(CAT/lm[0]['snapshot'],lm[0])!=(BASE/'packet-route-ledger.json').read_bytes():raise RuntimeError('Catalog ledger drift')
 latest,latestmd,unique,uniquemd=reports()
 if latest.read_bytes()!=unique.read_bytes() or latestmd.read_bytes()!=uniquemd.read_bytes():raise RuntimeError('Final reports differ')
 report=read(latest)
 if report['round']!=ROUND or report['route_ledger_sha256']!=sha((BASE/'packet-route-ledger.json').read_bytes()):raise RuntimeError('Report identity drift')
 if report['dual_client_endpoint_catalog']['summary']!=read(CAT/'summary.json'):raise RuntimeError('Report catalog drift')
 for key in ['whole_game_distinct_packet_count','whole_game_completed_route_count','whole_game_completion_percent']:
  if report['counts'][key] is not None:raise RuntimeError('Whole-game denominator fabricated')
 for p in reports():save(OUT/'reports/final'/(p.parent.name+'-'+p.name),p.read_bytes())
 if len(list((OUT/'reports/raw').iterdir()))!=4 or len(list((OUT/'reports/final').iterdir()))!=4:raise RuntimeError('Four raw and final reports required')
 flags=dict(sealed=True,method='STATIC_FILES_SOURCE_ONLY',native_execution=False,Cplusplus_source_run=False,
  Lua_run=False,Windows_API_run=False,build_run=False,tests_run=False,runtime_run=False,database_access=False,SQL_run=False,deployed=False)
 cm=dict(round=CAT.name,**flags,files=inventory(CAT),current_source_files=len(sources));dump(CAT/'manifest.json',cm)
 rm=dict(round=ROUND,**flags,catalog=CAT.name,catalog_manifest_sha256=sha((CAT/'manifest.json').read_bytes()),
  before_files=len(rows),protected_files=len(guarded),modified_gameplay_source_files=6,
  completed_parallel_agents=3,new_complete_bidirectional_routes=0,whole_game_completion_percent=None,files=inventory(OUT));dump(OUT/'manifest.json',rm)
 print(json.dumps(dict(before_files=len(rows),protected_files=len(guarded),catalog_source_files=len(sources),
  catalog_sealed_files=len(cm['files']),source_sealed_files=len(rm['files']),catalog_manifest_sha256=sha((CAT/'manifest.json').read_bytes()),source_manifest_sha256=sha((OUT/'manifest.json').read_bytes()))))

if __name__=='__main__':
 if len(sys.argv)!=2 or sys.argv[1] not in ['account','enrich','seal']:raise RuntimeError('Choose account/enrich/seal')
 globals()[sys.argv[1]]()
