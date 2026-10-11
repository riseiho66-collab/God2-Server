"""Round237 static file accounting. Never executes native/game/codec/SQL."""
from pathlib import Path
import json,sys,difflib
from .parallel_game_connection_frontier_delivery import ROOT,sha,read,save,dump,matches,inventory
from .tw_native_entry_presence_source_delivery import full_external_manifest
BASE=ROOT/'artifacts/integration/packet-connections-20261006'
TASK=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261010/tw-native-owned-bag-move-source-01')
OUT=TASK/'root';ARCHIVE=OUT/'full-originals';CAT=TASK/'catalog-metadata'
LOCAL=BASE/'tw-native-owned-bag-move-source-01';INDEX=BASE/'endpoint-catalog237'
ROUND='20261010-tw-native-owned-bag-move-source'
DOC='docs/research/tw-native-owned-bag-move-source-20261010.md'
TOOLS=['tools/reconstruction/dual_client_route_catalog.py','tools/reconstruction/packet_connection_report.py']
GAME=['src/game/SharedTaiwanOwnedBagMoveSource.h', 'src/game/SharedTaiwanOwnedBagMoveSource.cpp', 'src/db/SqliteOwnedEquipmentTransaction.h', 'src/db/SqliteOwnedEquipmentTransaction.cpp', 'src/game/SharedTaiwanWorldRecordSource.h', 'src/game/SharedTaiwanWorldRecordSource.cpp', 'src/core/SharedTaiwanNativeWorldHostPlan.h', 'src/core/SharedTaiwanNativeWorldHostPlan.cpp', 'src/game/SharedTaiwanNativeRecordHandlerSource.cpp']
WRITTEN=GAME+TOOLS+[DOC,'tools/reconstruction/tw_native_owned_bag_move_source_delivery.py','docs/custom-designs.json']
BOOKS=['docs/PACKET_CONNECTION_GOAL_20261006.md',(BASE/'packet-route-ledger.json').relative_to(ROOT).as_posix()]
REMAINING=['General3B full25 opaque source and arbitrary metadata relocation, original C24 server rules, real custody/acquisition/witness issuance, Main hosting and all remaining TW variants/denominator remain OPEN. Native witness must still match actual saved position; movement-to-witness progression is not connected by this handler and stale witnesses are rejected.', 'Preserve CN/web/common/numeric64/stack99/native fonts/conversion/frozen features; Phase1 no build/test/runtime/native/codec/DBSQL/migrate/deploy.', 'Goal API actual blocked; owner-authorized manual work continues without fabricating resume or replacing goal.']

def absolute(v,base=ROOT):
 p=Path(v);return p if p.is_absolute() else base/p

def external(rel,raw):
 p=ARCHIVE/rel;save(p,raw)
 if p.read_bytes()!=raw:raise RuntimeError('Full original readback drift')
 return dict(path=str(p),bytes=len(raw),sha256=sha(raw))

def reports():return [BASE/'packet-progress-latest.json',BASE/'packet-progress-latest.md',ARCHIVE/'round-reports'/(ROUND+'.json'),ARCHIVE/'round-reports'/(ROUND+'.md')]

def before():
 raw=(OUT/'before-manifest.json').read_bytes()
 if sha(raw)!='f74107138c00815d849f924149fb5ed68007c713f991481243094ac7cbc434e0':raise RuntimeError('Truebefore1619 pin drift')
 rows=json.loads(raw)
 if len(rows)!=1619:raise RuntimeError('Truebefore1619 required')
 return rows,{r['path']:matches(absolute(r['snapshot']),r) for r in rows}

def prior():
 count=0
 for name,pin in read(OUT/'before-receipt.json')['pins'].items():
  folder=Path(pin['root']);raw=(folder/'manifest.json').read_bytes()
  if sha(raw)!=pin['sha256'] or raw!=(OUT/'retained-prior'/name/'manifest.json').read_bytes():raise RuntimeError('Prior236 seal drift')
  for r in json.loads(raw)['files']:matches(folder/r['path'],r);count+=1
 if count!=122:raise RuntimeError('Prior236 full122 required')
 for r in read(OUT/'retained-prior/external-archive-pins.json'):
  matches(Path(r['path']),r);full_external_manifest(Path(r['path']))

def protected(rows,old):
 excluded=set(WRITTEN+BOOKS)|{p.relative_to(ROOT).as_posix() for p in reports()[:2]}
 guarded=[r for r in rows if r['path'] not in excluded]
 for r in guarded:
  if (ROOT/r['path']).read_bytes()!=old[r['path']]:raise RuntimeError('Protected source drift: '+r['path'])
 for r in rows:
  if r['path'].startswith('src/') and r['path'] not in GAME and (ROOT/r['path']).read_bytes()!=old[r['path']]:raise RuntimeError('CPP changed in research round')
 return guarded

def agent_deliveries():
 AGENTS=read(OUT/'sealed-agent-pins-final.json')
 paths=set();reviews=[];_,old=before()
 if set(AGENTS)!={'tw-owned-bag-native','tw-owned-bag-source-review'}:raise RuntimeError('Two exact terminal237 agents required')
 def refs(value,base):
  if isinstance(value,list):
   for v in value:refs(v,base)
  elif isinstance(value,dict):
   if {'path','bytes','sha256'}<=value.keys():matches(absolute(value['path'],base),value)
   else:
    for v in value.values():refs(v,base)
 for name,pin in AGENTS.items():
  folder=TASK/'agents'/name;raw=(folder/'seal.json').read_bytes();seal=json.loads(raw);members=seal.get('files',seal.get('members'))
  if sha(raw)!=pin or not isinstance(members,list):raise RuntimeError('Agent seal/full inventory drift')
  for r in members:matches(folder/r['path'],r)
  if {r['path'] for r in members}|{'seal.json'}!={r['path'] for r in inventory(folder)}:raise RuntimeError('Agent member set drift')
  for path in folder.glob('*.json'):
   filename=path.name
   if 'origins' in filename or filename in ['original-inputs.json','supplemental-original-inputs.json','final-original-inputs.json','native-material-originals.json']:
    value=read(path);value=value.get('files',[]) if isinstance(value,dict) else value
    for r in value:
     if not isinstance(r,dict) or 'path' not in r or 'copy' not in r:continue
     data=matches(absolute(r['copy'],folder),r);p=absolute(r['path']);rel=p.relative_to(ROOT).as_posix() if p.is_relative_to(ROOT) else None
     truebefore=filename.startswith('before-') or filename.startswith('supplemental-before-') or (name=='tw-owned-bag-source-review' and filename=='original-inputs.json')
     if truebefore and rel in old and data!=old[rel]:raise RuntimeError('Truebefore agent epoch drift: '+filename+': '+str(rel))
     if filename in ['final-source-origins.json','final-context-origins.json','final-original-inputs.json','native-material-originals.json'] or (filename=='current-source-origins.json' and name!='tw-owned-bag-native'):
      if rel in BOOKS:
       if data!=old[rel]:raise RuntimeError('Retained agent policy epoch drift')
      elif matches(p,r)!=data:raise RuntimeError('Actual final agent source drift: '+str(rel))
     if rel and not rel.startswith('artifacts/'):paths.add(rel)
   if 'reference' in filename:refs(read(path),folder)
  facts=read(folder/'findings.json')
  if facts.get('blocking',0) or facts.get('blocking_findings') or facts.get('blocking_defects',0):raise RuntimeError('Agent blocker')
  reviews.append(dict(agent=name,source_epoch='actual237-terminal',seal_sha256=sha(raw),files=inventory(folder),findings=facts))
 return reviews,paths

def capture():
 rows,old=before();result=[]
 cpp=[];initial=[]
 for r in read(OUT/'firstcandidate/source-origins.json'):
  matches(Path(r['copy']),r);cpp.append(r);path=r['path']
  if path in old:
   row=next(row for row in rows if row['path']==path);initial.append(dict(path=path,copy=row['snapshot'],bytes=row['bytes'],sha256=row['sha256']))
 dump(OUT/'root-source-firstcandidate-origins.json',cpp);dump(OUT/'root-source-initial-origins.json',initial)
 final=[]
 for i,path in enumerate(GAME):
  raw=(ROOT/path).read_bytes();r=external('source/final-cpp/f'+str(i)+Path(path).suffix,raw);final.append(dict(path=path,copy=r['path'],bytes=r['bytes'],sha256=r['sha256']))
 dump(OUT/'root-source-final-origins.json',final)
 for i,path in enumerate(TOOLS):
  raw=(ROOT/path).read_bytes();r=external(f'tools/first/f{i}.py',raw)
  result.append(dict(path=path,copy=r['path'],bytes=r['bytes'],sha256=r['sha256']))
 dump(OUT/'root-tool-firstcandidate-origins.json',result)

def capture_final():
 rows,old=before();final=[];initial=[]
 for i,path in enumerate(GAME):
  raw=(ROOT/path).read_bytes();r=external('source/final-epoch3/f'+str(i)+Path(path).suffix,raw)
  final.append(dict(path=path,copy=r['path'],bytes=r['bytes'],sha256=r['sha256']))
  if path in old:
   row=next(v for v in rows if v['path']==path)
   initial.append(dict(path=path,copy=row['snapshot'],bytes=row['bytes'],sha256=row['sha256']))
 dump(OUT/'root-source-final-origins3.json',final);dump(OUT/'root-source-initial-origins3.json',initial)

def tool_originals():
 _,old=before()
 for r in read(OUT/'root-source-initial-origins.json'):
  if matches(Path(r['copy']),r)!=old[r['path']]:raise RuntimeError('Initial CPP drift')
 for r in read(OUT/'root-source-firstcandidate-origins.json'):matches(Path(r['copy']),r)
 for r in read(OUT/'root-source-final-origins.json'):
  matches(Path(r['copy']),r) # Retained historical first-candidate epoch.
 for r in read(OUT/'root-source-initial-origins2.json'):
  if matches(Path(r['copy']),r)!=old[r['path']]:raise RuntimeError('Final epoch truebefore drift')
 for r in read(OUT/'root-source-final-origins2.json'):
  matches(Path(r['copy']),r) # Retained pre-provenance-fix epoch.
 for r in read(OUT/'root-source-initial-origins3.json'):
  if matches(Path(r['copy']),r)!=old[r['path']]:raise RuntimeError('Final truebefore drift')
 for r in read(OUT/'root-source-final-origins3.json'):
  if matches(Path(r['copy']),r)!=matches(ROOT/r['path'],r):raise RuntimeError('Actual final CPP drift')
 for r in read(OUT/'root-tool-firstcandidate-origins.json'):
  if matches(Path(r['copy']),r)!=matches(ROOT/r['path'],r):raise RuntimeError('Tool firstcandidate/final drift')

def custom_registry():
 _,old=before()
 original=json.loads(old['docs/custom-designs.json']);current=read(ROOT/'docs/custom-designs.json')
 if current['designs'][:-1]!=original['designs'] or len(current['designs'])!=len(original['designs'])+1 or current['designs'][-1]['id']!='CUSTOM-0093':raise RuntimeError('Append-only0093 required')
 if {k:v for k,v in current.items() if k!='designs'}!={k:v for k,v in original.items() if k!='designs'}:raise RuntimeError('Prior registry policy drift')


def account():
 if (OUT/'findings.json').exists():raise RuntimeError('Fresh237 account required')
 rows,old=before();prior();custom_registry();guarded=protected(rows,old);tool_originals();reviews,paths=agent_deliveries()
 if read(OUT/'policy/goal-before237.json')['goal']['status']!='blocked':raise RuntimeError('Actual recorded goal API status required')
 ledger=read(ROOT/BOOKS[1]);previous=json.loads(old[BOOKS[1]])
 if ledger['dual_client_source_segments']!=previous['dual_client_source_segments'] or len(ledger['dual_client_source_segments'])!=222:raise RuntimeError('Historical222 drift')
 paths|=set(WRITTEN)|{'CMakeLists.txt'}
 if len([p for p in GAME if p not in old])!=2 or len([p for p in GAME if p in old and (ROOT/p).read_bytes()!=old[p]])!=7:raise RuntimeError('Actual2new7modified CPP required')
 facts={'round': 'ROUND_TOKEN', 'research_only': False, 'previous_goal_turn_classification': 'progress', 'completed_parallel_agents': 2, 'new_Cplusplus_source_files_added': 2, 'existing_Cplusplus_source_files_modified': 7, 'new_source_segments': 1, 'source_segments': 223, 'new_packet_values': 0, 'new_complete_bidirectional_routes': 0, 'whole_game_completion_percent': None, 'whole_game_denominator': None, 'tw_completion_percent': None, 'tw_denominator': None, 'new_bounded_native_bytes': 0, 'fresh_bounded_capture_bytes': 0, 'retained_native_bytes': 1108, 'retained_native_instruction_sites': 302, 'actual_C24_gameplay_handler': True, 'actual_same_connection_complete_before': True, 'actual_whole_instance_swap': True, 'actual_atomic_custody_native_CAS': True, 'actual_internal_concrete_issuer': True, 'actual_prepared_two41_reply': True, 'conditional_tail18_equality_required': True, 'original_server_gameplay_rules_recovered': False, 'custom_policy': 'CUSTOM-0093', 'actual_general3B_reply_source': False, 'actual_complete_C24_all_variants': False, 'actual_Main_factory_selected': False, 'formal_application_hosted': False, 'source_conclusion': 'Actual original mixed C24 singleton -> current ready owner lease -> full joint before -> CUSTOM-0093 whole existing instance relocation across explicit bag0..29 cells with exact native tail18 equality -> preencoded two41 -> one joint fulltuple CAS/internal concrete issuer -> durable exact token/current lease -> ordered native reply. No caller Action stub, new item grant, 3B opaque guess or C28 receipt misuse. Conditional opt-in source only; initial material and Main remain open.', 'owner_TW_first': True, 'owner_requested_pause_at_round_end': False, 'goal_status_at_source_account': 'blocked', 'owner_authorized_manual_work_continues': True, 'build_run': False, 'tests_run': False, 'native_execution': False, 'runtime_run': False, 'codec_execution': False, 'database_access': False, 'SQL_run': False, 'deployed': False}
 facts.update(round=ROUND,source_paths=sorted(paths),remaining=REMAINING)
 dump(OUT/'findings.json',facts);dump(OUT/'parallel-agent-deliveries.json',reviews)
 dump(OUT/'sealed-agent-pins.json',{r['agent']:r['seal_sha256'] for r in reviews})
 ledger['tw_owned_bag_move237']=facts
 ledger['dual_client_source_segments'].append(dict(name=LOCAL.name,round=ROUND,version_scope='TW149c-C24-owned-bag-whole-instance-joint-CAS-two41-tail18-subset',status=facts['source_conclusion'],source_paths=sorted(paths),native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,tw_source_owner_chains_added=0,formal_application_hosted=False,complete_gameplay_routes_added=0,evidence=LOCAL.relative_to(ROOT).as_posix(),external_full_evidence=str(OUT),remaining=REMAINING))
 ledger['dual_client_execution_plan'].update(latest_work_round=ROUND,owner_requested_stop_after_work_round=None,owner_requested_stop_after_round_number=None,continuation_requires_owner_resume=False,owner_TW_first=True,owner_stop_condition='Actual TW complete source100% before stop',next_source_frontier=REMAINING[0],actual_goal_api_status='blocked',owner_manual_work_continues=True)
 (ROOT/BOOKS[1]).write_bytes((json.dumps(ledger,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
 with (ROOT/BOOKS[0]).open('ab') as h:h.write(('\n\n## 第237輪：台服背包請求接完整持有物品交易與回覆\n\n'+(ROOT/DOC).read_text(encoding='utf8')+'\n').encode('utf8'))
 origins=[]
 for i,path in enumerate(sorted(paths|set(BOOKS))):
  raw=(ROOT/path).read_bytes();r=external(f'source/current/f{i:03d}'+Path(path).suffix,raw)
  origins.append(dict(path=path,copy=r['path'],bytes=r['bytes'],sha256=r['sha256'],changed_this_round=path not in old or old[path]!=raw))
  if path in old and raw!=old[path]:
   diff=''.join(difflib.unified_diff(old[path].decode('utf-8-sig').splitlines(True),raw.decode('utf-8-sig').splitlines(True),fromfile='before/'+path,tofile='final/'+path))
   if diff:external(f'diff/d{i:03d}.diff',diff.encode('utf8'))
 dump(OUT/'source/source-origins.json',origins)
 print(json.dumps(dict(protected_files=len(guarded),source_files=len(paths),source_segments=223,new_CPP=2,modified_CPP=7,new_complete_routes=0,goal_status='blocked',manual_work_continues=True)))

def retain_reports(stage):dump(OUT/'reports'/(stage+'-full-originals.json'),[external('reports/'+stage+'/'+p.parent.name+'-'+p.name,p.read_bytes()) for p in reports()])

def enrich():
 retain_reports('raw-final');receipt=dict(new_CPP=2,modified_CPP=7,source_segments=223,new_source_segments=1,new_complete_bidirectional_routes=0,tw_percent=None,whole_game_percent=None,current_catalog_source_files=len(read(CAT/'source-file-manifest.json')),owner_requested_pause_at_round_end=False,policy_read_epoch='Agent before policy originals retained; root final source origins independently retain appended policy.')
 for p in [reports()[0],reports()[2]]:
  v=read(p);v['tw_owned_bag_move237']=read(OUT/'findings.json');v['parallel_agent_deliveries']=read(OUT/'parallel-agent-deliveries.json');v['current_round_source_delta']=receipt;p.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
 for p in [reports()[1],reports()[3]]:
  p.write_bytes((p.read_text(encoding='utf8')+'\n\n'+(ROOT/DOC).read_text(encoding='utf8')+'\n\nStatic accounting: '+json.dumps(receipt)+'\n').encode('utf8'))
 dump(OUT/'reports/enrichment-receipt-final.json',receipt);print(json.dumps(receipt))

def seal():
 if (OUT/'manifest.json').exists() or (CAT/'manifest.json').exists():raise RuntimeError('Fresh237 seals required')
 rows,old=before();prior();custom_registry();guarded=protected(rows,old);tool_originals();reviews,paths=agent_deliveries()
 if reviews!=read(OUT/'parallel-agent-deliveries.json'):raise RuntimeError('Agent epoch drift')
 for r in read(OUT/'source/source-origins.json'):
  if matches(ROOT/r['path'],r)!=matches(Path(r['copy']),r):raise RuntimeError('Full current source drift')
 ledger=read(ROOT/BOOKS[1])
 if ledger['dual_client_source_segments'][:222]!=json.loads(old[BOOKS[1]])['dual_client_source_segments'] or len(ledger['dual_client_source_segments'])!=223:raise RuntimeError('Historical222 changed')
 sources=read(CAT/'source-file-manifest.json')
 for p,r in sources.items():matches(ROOT/p,r)
 arc=full_external_manifest(CAT/'external-archive-manifest.json')
 index=read(INDEX/'external-catalog.json')
 if Path(index['root'])!=CAT or not index['verified'] or not index['original_bytes_retained']:raise RuntimeError('External metadata pointer drift')
 for r in index['files']:matches(CAT/r['path'],r)
 entries=[r for r in read(CAT/'input-manifest.json') if r['input']=='source-ledger']
 if len(entries)!=1 or matches(absolute(entries[0]['snapshot'],CAT),entries[0])!=(ROOT/BOOKS[1]).read_bytes():raise RuntimeError('Catalog ledger drift')
 a,b,c,d=reports()
 if a.read_bytes()!=c.read_bytes() or b.read_bytes()!=d.read_bytes():raise RuntimeError('Final reports mismatch')
 v=read(a)
 if v['round']!=ROUND or v['route_ledger_sha256']!=sha((ROOT/BOOKS[1]).read_bytes()) or v['dual_client_endpoint_catalog']['summary']!=read(CAT/'summary.json'):raise RuntimeError('Report catalog drift')
 for k in ['whole_game_distinct_packet_count','whole_game_completed_route_count','whole_game_completion_percent']:
  if v['counts'][k] is not None:raise RuntimeError('False denominator')
 for name in ['capacity-final-before-seal.json','capacity-full-final-before-seal.json']:
  cap=read(OUT/'policy'/name)
  if not cap['under_limit'] or cap['unreadable_count'] or cap.get('cycles'):raise RuntimeError('WholeGod2 capacity failed')
 retain_reports('final')
 full=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p.read_bytes())) for p in sorted(ARCHIVE.rglob('*')) if p.is_file()]
 dump(OUT/'external-full-originals-receipt.json',dict(root=str(ARCHIVE),verified=True,original_bytes_retained=True,files=full));full_external_manifest(OUT/'external-full-originals-receipt.json')
 flags=dict(sealed=True,research_only=False,method='STATIC_SOURCE_ACCOUNTING_ONLY',build_run=False,tests_run=False,native_execution=False,runtime_run=False,codec_execution=False,database_access=False,SQL_run=False,deployed=False)
 cm=dict(round=INDEX.name,**flags,current_source_files=len(sources),external_originals_verified=True,external_full_file_count=len(arc['files']),files=inventory(CAT));dump(CAT/'manifest.json',cm)
 rm=dict(round=ROUND,**flags,before_files=len(rows),protected_files=len(guarded),source_segments=223,new_source_segments=1,new_CPP=2,modified_CPP=7,new_complete_bidirectional_routes=0,tw_percent=None,whole_game_percent=None,external_originals_verified=True,catalog_manifest_sha256=sha((CAT/'manifest.json').read_bytes()),files=inventory(OUT));dump(OUT/'manifest.json',rm)
 pins=dict(root=str(OUT),root_manifest_sha256=sha((OUT/'manifest.json').read_bytes()),root_members=len(rm['files']),catalog_root=str(CAT),catalog_manifest_sha256=sha((CAT/'manifest.json').read_bytes()),verified=True,original_bytes_retained=True)
 dump(LOCAL/'external-final-seal.json',pins);dump(INDEX/'external-final-seal.json',pins)
 print(json.dumps(dict(root_members=len(rm['files']),catalog_members=len(cm['files']),root_sha256=pins['root_manifest_sha256'],catalog_sha256=pins['catalog_manifest_sha256'],source_segments=223,new_complete_routes=0)))

if __name__=='__main__':
 if len(sys.argv)!=2 or sys.argv[1] not in ['capture','capture_final','account','enrich','seal']:raise RuntimeError('capture/capture_final/account/enrich/seal required')
 globals()[sys.argv[1]]()
