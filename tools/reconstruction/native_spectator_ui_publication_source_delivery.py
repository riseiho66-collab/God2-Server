"""Immutable static source accounting only; no gameplay, build or DB execution."""
import difflib
import json
from pathlib import Path
import sys
from .parallel_game_connection_frontier_delivery import ROOT, sha, read, save, dump, matches, inventory

BASE=ROOT/'artifacts/integration/packet-connections-20261006'
NAME='native-spectator-ui-publication-source-01'
ROUND='20261009-native-spectator-ui-publication-source'
OUT=BASE/NAME
CAT=BASE/'endpoint-catalog187'
DOC='docs/research/native-spectator-ui-publication-source-20261009.md'
GAME=['src/game/SharedWorldHost.h', 'src/game/SharedWorldHost.cpp', 'src/game/SharedNativeWorldTransports.h', 'src/game/SharedNativeWorldTransports.cpp', 'src/game/SharedNativeSpectatorPublication.h', 'src/game/SharedNativeSpectatorPublication.cpp', 'src/cn/protocol/CnSpectatorTargetsD0.h', 'src/game/SharedTaiwanNativeSpectatorSource.h', 'src/game/SharedTaiwanNativeSpectatorSource.cpp', 'src/core/SharedTaiwanNativeWorldHostPlan.h', 'src/core/SharedTaiwanNativeWorldHostPlan.cpp']
BOOKS=['docs/PACKET_CONNECTION_GOAL_20261006.md',
 'artifacts/integration/packet-connections-20261006/packet-route-ledger.json']
WRITTEN=GAME+[DOC,'tools/reconstruction/native_spectator_ui_publication_source_delivery.py',
 'tools/reconstruction/dual_client_route_catalog.py','tools/reconstruction/native_spectator_publication187.py',
 'tools/reconstruction/tw_spectator_publication_host187.py','tools/reconstruction/tw_spectator_window_epoch187.py']
AGENTS=['native-spectator-publication','tw-spectator-publication-host','tw-spectator-window-epoch-frontier']
PINS={'tw-native-spectator-record-source-01':'191b0d87c6aebaca25a5bd6f47dd151f3850d7fe977888f4c874563f7c974860',
 'endpoint-catalog186':'dbe6ddab3ecb7aa42b1b46b996bb705bb9841cb6dc5bcaafc3f8ab5a672e2523'}
REMAINING=[
 'Actual same-host supplied UI publication uses real native held queues and typed6E reads its exact recipient/token history, but true native window/epoch/issuer/rules remain mandatory providers; raw history is not client receipt or spectator rights.',
 'TW F7 reset sets local mode2 and does not qualify mode1 spectator lineage; A3/CB body1 is saved-this high byte, not a nonce/epoch. Target namespace/common64 mapping/battle membership/real replies remain OPEN.',
 'Full native entry/appearance/audience/rights/header/body/codepage/cipher suppliers, Main selection and whole-game directional-phase-state-variant route denominator remain OPEN.',
 'TW-CN-web common64 storage/wire/object/display, qualified stack99 mutations and gateway WSS/TLS/hosting remain pending; all source routes before build/tests/acceptance/repair/recovery/release.']

def reports():
 return [BASE/'packet-progress-latest.json',BASE/'packet-progress-latest.md',
  BASE/'round-reports'/(ROUND+'.json'),BASE/'round-reports'/(ROUND+'.md')]

def before():
 raw=(OUT/'before-manifest.json').read_bytes()
 if sha(raw)!='4bd04968a085573630848601024f740b49f5e72fcb513b0efdac6c044ab45f13':
  raise RuntimeError('Original before1333 changed')
 rows=json.loads(raw)
 if len(rows)!=1333 or len({r['path'] for r in rows})!=1333:raise RuntimeError('Before1333 required')
 return rows,{r['path']:matches(OUT/r['snapshot'],r) for r in rows}

def prior():
 count=0
 for name,pin in PINS.items():
  raw=(BASE/name/'manifest.json').read_bytes()
  if sha(raw)!=pin or raw!=(OUT/'retained-prior'/name/'manifest.json').read_bytes():
   raise RuntimeError('Prior186 immutable manifest drift')
  for row in json.loads(raw)['files']:matches(BASE/name/row['path'],row);count+=1
 if count!=2377:raise RuntimeError('Entire prior2377 members required')

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
 common=read(OUT/'agents/native-spectator-publication/findings.json')
 mixed=read(OUT/'agents/tw-spectator-publication-host/findings.json')
 native=read(OUT/'agents/tw-spectator-window-epoch-frontier/findings.json')
 v=dict(completed_parallel_agents=3,new_Cplusplus_source_files_added=3,
  existing_Cplusplus_source_files_modified=8,modified_gameplay_source_files=11,
  actual_same_host_UI_publication_installations_added=1,
  actual_TW_held_queue_publication_callers_added=1,
  actual_CN_held_queue_publication_callers_added=1,
  actual_TW_typed_scope_UI_history_suppliers_added=1,
  actual_same_Context_UI_publication_factories_added=1,
  exact_private_transport_registration_comparators_added=1,
  readonly_CN_D0_views_added=1,
  native_spectator_publication_findings=common,tw_spectator_publication_host_findings=mixed,
  tw_spectator_window_epoch_findings=native,
  new_packet_values=0,new_phase_bindings=0,new_complete_bidirectional_routes=0,
  source_segments=179,whole_game_completion_percent=None,
  owner_explicit_resume=True,whole_source_before_build_tests=True)
 if sources is not None:
  previous=read(BASE/'endpoint-catalog186/source-file-manifest.json')
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
 if {r['path'] for r in review['files']}!=set(GAME):raise RuntimeError('All11 C++ sources require complete original copies and current definition review')
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
 if ledger['dual_client_source_segments']!=previous['dual_client_source_segments'] or len(ledger['dual_client_source_segments'])!=178:
  raise RuntimeError('Prior178 source segments changed')
 paths|=set(WRITTEN)
 ledger['native_spectator_ui_publication_source']=facts
 ledger['dual_client_source_segments'].append(dict(name=NAME,round=ROUND,
  version_scope='TW-CN-native-UI-held-publication-and-TW-exact-recipient-typed-scope-history',
  status='Actual supplied same-host native UI publisher sends exact CD/D0 through true TW/CN held queues; private local-release history reaches TW typed6E full Scope through the real Context factory. Raw observations are not UI/battle rights or client receipt; actual window epochs, target issuer/mapping/full replies/Main/all-game routes remain OPEN',
  source_paths=sorted(paths),native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,
  tw_source_owner_chains_added=0,formal_application_hosted=False,complete_gameplay_routes_added=0,
  evidence=OUT.relative_to(ROOT).as_posix(),remaining=REMAINING))
 plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
 plan['owner_explicit_resume_after_stop']=ROUND
 plan['owner_requested_stop_after_work_round']=None
 plan['next_source_frontier']='Concrete window event/epoch/target identity suppliers and real common battle membership/execution for TW/CN; full entry/appearance/native rights/replies, web C56 opaque authority, Main/worldplans/all-game routes before build/tests.'
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
  v=read(p);v['native_spectator_ui_publication_source']=facts;v['parallel_agent_deliveries']=agents;v['current_round_source_delta']=receipt
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
 if len(ledger['dual_client_source_segments'])!=179 or ledger['dual_client_source_segments'][:178]!=previous['dual_client_source_segments']:
  raise RuntimeError('Prior178 segments changed')
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
  before_files=len(rows),protected_files=len(guarded),modified_gameplay_source_files=11,
  completed_parallel_agents=3,new_complete_bidirectional_routes=0,whole_game_completion_percent=None,files=inventory(OUT));dump(OUT/'manifest.json',rm)
 print(json.dumps(dict(before_files=len(rows),protected_files=len(guarded),catalog_source_files=len(sources),
  catalog_sealed_files=len(cm['files']),source_sealed_files=len(rm['files']),catalog_manifest_sha256=sha((CAT/'manifest.json').read_bytes()),source_manifest_sha256=sha((OUT/'manifest.json').read_bytes()))))

if __name__=='__main__':
 if len(sys.argv)!=2 or sys.argv[1] not in ['account','enrich','seal']:raise RuntimeError('Choose account/enrich/seal')
 globals()[sys.argv[1]]()
