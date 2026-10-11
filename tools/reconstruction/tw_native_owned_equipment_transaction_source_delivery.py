"""Round232 static file accounting. Never executes native/game/codec/SQL."""
from pathlib import Path
import json,sys,difflib
from .parallel_game_connection_frontier_delivery import ROOT,sha,read,save,dump,matches,inventory
from .tw_native_entry_presence_source_delivery import full_external_manifest
BASE=ROOT/'artifacts/integration/packet-connections-20261006'
TASK=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261010/tw-native-owned-equipment-transaction-source-01')
OUT=TASK/'root';ARCHIVE=OUT/'full-originals';CAT=TASK/'catalog-metadata'
LOCAL=BASE/'tw-native-owned-equipment-transaction-source-01';INDEX=BASE/'endpoint-catalog232'
ROUND='20261010-tw-native-owned-equipment-transaction-source'
DOC='docs/research/tw-native-owned-equipment-transaction-source-20261010.md'
TOOLS=['tools/reconstruction/dual_client_route_catalog.py','tools/reconstruction/packet_connection_report.py']
AGENTS=read(OUT/'sealed-agent-pins-final.json')
GAME=['src/db/SqliteOwnedEquipmentTransaction.h', 'src/db/SqliteOwnedEquipmentTransaction.cpp', 'src/db/SqliteOwnedInventoryRepository.h', 'src/db/SqliteOwnedInventoryRepository.cpp', 'src/db/SqliteNativeEquipmentSnapshotRepository.h', 'src/db/SqliteNativeEquipmentSnapshotRepository.cpp', 'src/game/SharedTaiwanNativeEquipmentPublicationSource.h', 'src/game/SharedTaiwanNativeEquipmentPublicationSource.cpp', 'src/core/SharedTaiwanNativeWorldHostPlan.h', 'src/core/SharedTaiwanNativeWorldHostPlan.cpp']
WRITTEN=GAME+TOOLS+[DOC,'tools/reconstruction/tw_native_owned_equipment_transaction_source_delivery.py']
BOOKS=['docs/PACKET_CONNECTION_GOAL_20261006.md',(BASE/'packet-route-ledger.json').relative_to(ROOT).as_posix()]
REMAINING=['Actual authenticated C28 dispatch/input freshness/action/equip/unequip/slot/Lua rules and genuine acquisition/drop/quest/common-definition issuer remain OPEN. Joint atomic storage and readonly231 Selection do not grant an item or make a complete route.', 'Actual full item-to-native1200/cache/DA15 producer and complete ordered inventory replies remain OPEN. Preserve full unknown bytes and supplied native provenance; no key/category/icon/row or raw20-to-commonID inference. Source/selflocal and mixedfanout remain OPEN.', 'Complete full2A/onceIssued admission/lifecycle/Main suppliers and remainingTW gameplay/denominator; preserve CN/web/common/64numeric/stack99/frozen sources. Phase1 no builds/tests/native/codec/runtime/DBSQL/migrate/deploy.']

def absolute(v,base=ROOT):
 p=Path(v);return p if p.is_absolute() else base/p

def external(rel,raw):
 p=ARCHIVE/rel;save(p,raw)
 if p.read_bytes()!=raw:raise RuntimeError('Full original readback drift')
 return dict(path=str(p),bytes=len(raw),sha256=sha(raw))

def reports():return [BASE/'packet-progress-latest.json',BASE/'packet-progress-latest.md',ARCHIVE/'round-reports'/(ROUND+'.json'),ARCHIVE/'round-reports'/(ROUND+'.md')]

def before():
 raw=(OUT/'before-manifest.json').read_bytes()
 if sha(raw)!='66df58e194b0e67e44b76bfd951f5d0957fbcdab1da7347391da57091fb63ff6':raise RuntimeError('Truebefore1586 pin drift')
 rows=json.loads(raw)
 if len(rows)!=1586:raise RuntimeError('Truebefore1586 required')
 return rows,{r['path']:matches(absolute(r['snapshot']),r) for r in rows}

def prior():
 count=0
 for name,pin in read(OUT/'before-receipt.json')['pins'].items():
  folder=Path(pin['root']);raw=(folder/'manifest.json').read_bytes()
  if sha(raw)!=pin['sha256'] or raw!=(OUT/'retained-prior'/name/'manifest.json').read_bytes():raise RuntimeError('Prior231 seal drift')
  for r in json.loads(raw)['files']:matches(folder/r['path'],r);count+=1
 if count!=165:raise RuntimeError('Prior231 full165 required')
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
 paths=set();reviews=[];_,old=before()
 if set(AGENTS)!={'tw-joint-equipment-native','tw-owned-equipment-transaction-review'}:raise RuntimeError('Two exact terminal232 agent pins required')
 def refs(value):
  if isinstance(value,list):
   for v in value:refs(v)
  elif isinstance(value,dict):
   if {'path','bytes','sha256'}<=value.keys():matches(absolute(value['path']),value)
   else:
    for v in value.values():refs(v)
 for name,pin in AGENTS.items():
  folder=TASK/'agents'/name;raw=(folder/'seal.json').read_bytes();seal=json.loads(raw);members=seal.get('files',seal.get('members'))
  if sha(raw)!=pin:raise RuntimeError('Agent seal pin drift')
  if not isinstance(members,list):raise RuntimeError('Agent full member inventory required')
  for r in members:matches(folder/r['path'],r)
  if {r['path'] for r in members}|{'seal.json'}!={r['path'] for r in inventory(folder)}:raise RuntimeError('Agent full inventory drift')
  for filename in ['original-inputs.json','supplemental-original-inputs.json','final-original-inputs.json','final-context-origins.json','current-source-origins.json','initial-source-origins.json','before-source-origins.json','supplemental-source-origins.json','before-supplemental-origins.json','candidate-source-origins.json','candidate-context-origins.json','firstcandidate-origins.json','final-changed-source-origins.json']:
   if not (folder/filename).exists():continue
   value=read(folder/filename);value=value.get('files',[]) if isinstance(value,dict) else value
   for r in value:
    if not isinstance(r,dict) or 'path' not in r or 'copy' not in r:continue
    data=matches(absolute(r['copy'],folder),r)
    p=absolute(r['path'])
    rel=p.relative_to(ROOT).as_posix() if p.is_relative_to(ROOT) else None
    initial=filename in ['initial-source-origins.json','before-source-origins.json','before-supplemental-origins.json'] or (name=='tw-owned-equipment-transaction-review' and filename in ['original-inputs.json','supplemental-original-inputs.json'])
    # The reviewer explicitly labels initial-source-origins as its first
    # actual observation AFTER root's candidate, not the true-before epoch.
    # Original-inputs retain its separate complete true-before originals.
    if filename=='initial-source-origins.json' and r.get('epoch')=='232-initial-actual-after-firstcandidate-and-parent-announced-refinement':initial=False
    if initial and rel in old and data!=old[rel]:raise RuntimeError('Truebefore agent source drift: '+filename+': '+str(rel))
    if filename in ['final-original-inputs.json','final-context-origins.json','current-source-origins.json']:
     if rel in BOOKS:
      # Agent's sealed policy read predates root accounting. Preserve that
      # exact true-before epoch; root final source origins pin the appended book.
      if data!=old[rel]:raise RuntimeError('Agent policy read epoch drift')
     elif matches(p,r)!=data:raise RuntimeError('Agent final source drift')
    if rel and not rel.startswith('artifacts/'):paths.add(rel)
  for filename in ['native-input-references.json','native-image-reference.json','preserved-history.json','preserved-history-references.json','history-input-references.json','root-before-reference.json','before-reference.json','before-input-reference.json','current-resource-identity.json','prior231-complete-inplace-references.json','native-retained-references.json','before-manifest-reference.json','root-final-manifest-reference.json']:
   if (folder/filename).exists():refs(read(folder/filename))
  facts=read(folder/'findings.json')
  if facts.get('blocking',0) or facts.get('blocking_findings'):raise RuntimeError('Agent blocking finding')
  reviews.append(dict(agent=name,seal_sha256=sha(raw),files=inventory(folder),findings=facts))
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

def tool_originals():
 _,old=before()
 for r in read(OUT/'root-source-initial-origins.json'):
  if matches(Path(r['copy']),r)!=old[r['path']]:raise RuntimeError('Initial CPP drift')
 for r in read(OUT/'root-source-firstcandidate-origins.json'):matches(Path(r['copy']),r)
 for r in read(OUT/'root-source-final-origins.json'):
  if matches(Path(r['copy']),r)!=matches(ROOT/r['path'],r):raise RuntimeError('Final CPP drift')
 for r in read(OUT/'root-tool-firstcandidate-origins.json'):
  if matches(Path(r['copy']),r)!=matches(ROOT/r['path'],r):raise RuntimeError('Tool firstcandidate/final drift')

def custom_registry():
 _,old=before()
 if (ROOT/'docs/custom-designs.json').read_bytes()!=old['docs/custom-designs.json']:raise RuntimeError('Prior custom registry changed')


def account():
 if (OUT/'findings.json').exists():raise RuntimeError('Fresh232 account required')
 rows,old=before();prior();custom_registry();guarded=protected(rows,old);tool_originals();reviews,paths=agent_deliveries()
 if read(OUT/'policy/goal-before232.json')['goal']['status']!='active':raise RuntimeError('Active goal required')
 ledger=read(ROOT/BOOKS[1]);previous=json.loads(old[BOOKS[1]])
 if ledger['dual_client_source_segments']!=previous['dual_client_source_segments'] or len(ledger['dual_client_source_segments'])!=217:raise RuntimeError('Historical217 drift')
 paths|=set(WRITTEN)|{'CMakeLists.txt'}
 if len([p for p in GAME if p not in old])!=2 or len([p for p in GAME if p in old and (ROOT/p).read_bytes()!=old[p]])!=8:raise RuntimeError('Actual2new8modified CPP required')
 facts={'round': 'ROUND_TOKEN', 'research_only': False, 'previous_goal_turn_classification': 'progress', 'completed_parallel_agents': 2, 'new_Cplusplus_source_files_added': 2, 'existing_Cplusplus_source_files_modified': 8, 'new_source_segments': 1, 'source_segments': 218, 'new_packet_values': 0, 'new_complete_bidirectional_routes': 0, 'whole_game_completion_percent': None, 'whole_game_denominator': None, 'tw_completion_percent': None, 'tw_denominator': None, 'new_bounded_native_bytes': 0, 'retained_native_bytes': 432, 'retained_native_instructions': 137, 'retained_native_spans': 2, 'retained_data_bytes': 0, 'retained_opaque_CALL_boundaries': 12, 'actual_shared_fullowner_custody_CAS': True, 'actual_permanent_global_instance_registry': True, 'actual_genuine_acquisition_issuer': False, 'actual_versioned_full_native_alias_storage': True, 'actual_private_custody_COMMIT_token': True, 'actual_joint_durable_read_observation': True, 'retained_ready_C28_owned_selection': True, 'actual_C28_gameplay_handler': False, 'actual_joint_canonical_native_COMMIT': True, 'actual_joint_consistent_current': True, 'actual_joint_DA_source_rereads': True, 'actual_same_Application_joint_factory': True, 'actual_item_to_DA_producer': False, 'actual_complete_mixedversion_fanout': False, 'actual_self_local_DA': False, 'actual_Main_factory_selected': False, 'formal_application_hosted': False, 'custom_design': 'CUSTOM-0092', 'source_conclusion': 'Actual same Application custody/native writers -> shared private fulltuple stage helpers -> one owned IMMEDIATE/full both-before CAS/common roots/position/no pendingbattle -> genuine fullpair issuer Prepared/BeforeWrite/both-staged BeforeCommit -> both private immutable individual receipts and joint writer identity preallocated -> one outer durable COMMIT -> actual same Context future joint publication factory -> each heldDA source reread checks both full committed tuples in one consistent read scope plus actual ready lease/actor/position. No inferred native mapping or grant. Actual acquisition/definition/rules/C28 dispatcher/input freshness/item-to-DA/replies/Main remain OPEN.', 'owner_TW_first': True, 'owner_requested_pause_at_round_end': False, 'goal_status_at_source_account': 'active', 'build_run': False, 'tests_run': False, 'native_execution': False, 'runtime_run': False, 'codec_execution': False, 'database_access': False, 'SQL_run': False, 'deployed': False}
 facts.update(round=ROUND,source_paths=sorted(paths),remaining=REMAINING)
 dump(OUT/'findings.json',facts);dump(OUT/'parallel-agent-deliveries.json',reviews)
 dump(OUT/'sealed-agent-pins.json',{r['agent']:r['seal_sha256'] for r in reviews})
 ledger['tw_owned_equipment_transaction232']=facts
 ledger['dual_client_source_segments'].append(dict(name=LOCAL.name,round=ROUND,version_scope='shared-owned-inventory-and-TW149c-native-equipment-joint-COMMIT-and-DA-source',status=facts['source_conclusion'],source_paths=sorted(paths),native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,tw_source_owner_chains_added=0,formal_application_hosted=False,complete_gameplay_routes_added=0,evidence=LOCAL.relative_to(ROOT).as_posix(),external_full_evidence=str(OUT),remaining=REMAINING))
 ledger['dual_client_execution_plan'].update(latest_work_round=ROUND,owner_requested_stop_after_work_round=None,owner_requested_stop_after_round_number=None,continuation_requires_owner_resume=False,owner_TW_first=True,owner_stop_condition='Actual TW complete source100% before stop',next_source_frontier=REMAINING[0])
 (ROOT/BOOKS[1]).write_bytes((json.dumps(ledger,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
 with (ROOT/BOOKS[0]).open('ab') as h:h.write(('\n\n## 第232輪：共用物品與台服原生外觀同筆交易及推播來源\n\n'+(ROOT/DOC).read_text(encoding='utf8')+'\n').encode('utf8'))
 origins=[]
 for i,path in enumerate(sorted(paths|set(BOOKS))):
  raw=(ROOT/path).read_bytes();r=external(f'source/current/f{i:03d}'+Path(path).suffix,raw)
  origins.append(dict(path=path,copy=r['path'],bytes=r['bytes'],sha256=r['sha256'],changed_this_round=path not in old or old[path]!=raw))
  if path in old and raw!=old[path]:
   diff=''.join(difflib.unified_diff(old[path].decode('utf-8-sig').splitlines(True),raw.decode('utf-8-sig').splitlines(True),fromfile='before/'+path,tofile='final/'+path))
   if diff:external(f'diff/d{i:03d}.diff',diff.encode('utf8'))
 dump(OUT/'source/source-origins.json',origins)
 print(json.dumps(dict(protected_files=len(guarded),source_files=len(paths),source_segments=218,new_CPP=2,modified_CPP=8,new_complete_routes=0,goal_status='active')))

def retain_reports(stage):dump(OUT/'reports'/(stage+'-full-originals.json'),[external('reports/'+stage+'/'+p.parent.name+'-'+p.name,p.read_bytes()) for p in reports()])

def enrich():
 retain_reports('raw-final');receipt=dict(new_CPP=2,modified_CPP=8,source_segments=218,new_source_segments=1,new_complete_bidirectional_routes=0,tw_percent=None,whole_game_percent=None,current_catalog_source_files=len(read(CAT/'source-file-manifest.json')),owner_requested_pause_at_round_end=False,policy_read_epoch='Agent before policy originals retained; root final source origins independently retain appended policy.')
 for p in [reports()[0],reports()[2]]:
  v=read(p);v['tw_owned_equipment_transaction232']=read(OUT/'findings.json');v['parallel_agent_deliveries']=read(OUT/'parallel-agent-deliveries.json');v['current_round_source_delta']=receipt;p.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
 for p in [reports()[1],reports()[3]]:p.write_bytes(((ROOT/DOC).read_text(encoding='utf8')+'\n\nStatic accounting: '+json.dumps(receipt)+'\n').encode('utf8'))
 dump(OUT/'reports/enrichment-receipt-final.json',receipt);print(json.dumps(receipt))

def seal():
 if (OUT/'manifest.json').exists() or (CAT/'manifest.json').exists():raise RuntimeError('Fresh232 seals required')
 rows,old=before();prior();custom_registry();guarded=protected(rows,old);tool_originals();reviews,paths=agent_deliveries()
 if reviews!=read(OUT/'parallel-agent-deliveries.json'):raise RuntimeError('Agent epoch drift')
 for r in read(OUT/'source/source-origins.json'):
  if matches(ROOT/r['path'],r)!=matches(Path(r['copy']),r):raise RuntimeError('Full current source drift')
 ledger=read(ROOT/BOOKS[1])
 if ledger['dual_client_source_segments'][:217]!=json.loads(old[BOOKS[1]])['dual_client_source_segments'] or len(ledger['dual_client_source_segments'])!=218:raise RuntimeError('Historical217 changed')
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
 rm=dict(round=ROUND,**flags,before_files=len(rows),protected_files=len(guarded),source_segments=218,new_source_segments=1,new_CPP=2,modified_CPP=8,new_complete_bidirectional_routes=0,tw_percent=None,whole_game_percent=None,external_originals_verified=True,catalog_manifest_sha256=sha((CAT/'manifest.json').read_bytes()),files=inventory(OUT));dump(OUT/'manifest.json',rm)
 pins=dict(root=str(OUT),root_manifest_sha256=sha((OUT/'manifest.json').read_bytes()),root_members=len(rm['files']),catalog_root=str(CAT),catalog_manifest_sha256=sha((CAT/'manifest.json').read_bytes()),verified=True,original_bytes_retained=True)
 dump(LOCAL/'external-final-seal.json',pins);dump(INDEX/'external-final-seal.json',pins)
 print(json.dumps(dict(root_members=len(rm['files']),catalog_members=len(cm['files']),root_sha256=pins['root_manifest_sha256'],catalog_sha256=pins['catalog_manifest_sha256'],source_segments=218,new_complete_routes=0)))

if __name__=='__main__':
 if len(sys.argv)!=2 or sys.argv[1] not in ['capture','account','enrich','seal']:raise RuntimeError('capture/account/enrich/seal required')
 globals()[sys.argv[1]]()
