"""Round224 immutable source/file accounting only; no game/SQL execution."""
from pathlib import Path
import json,sys,difflib
from .parallel_game_connection_frontier_delivery import ROOT,sha,read,save,dump,matches,inventory
from .tw_native_entry_presence_source_delivery import full_external_manifest
BASE=ROOT/'artifacts/integration/packet-connections-20261006'
OUT=BASE/'tw-native-scene-content-source-01';CAT=BASE/'endpoint-catalog224'
ARCHIVE=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261010/tw-native-scene-content-source-01/root-source-account')
ROUND='20261010-tw-native-scene-content-source'
DOC='docs/research/tw-native-scene-content-source-20261010.md'
GAME=['src/game/TaiwanNativeNpcSceneGroups.h','src/game/TaiwanNativeNpcSceneGroups.cpp','src/db/NativeEnemyDisplayCatalog.h','src/db/NativeEnemyDisplayCatalog.cpp']
WRITTEN=GAME+[DOC,'tools/reconstruction/tw_native_scene_content_source_delivery.py','tools/reconstruction/dual_client_route_catalog.py']
BOOKS=['docs/PACKET_CONNECTION_GOAL_20261006.md',(BASE/'packet-route-ledger.json').relative_to(ROOT).as_posix()]
AGENTS={'tw-scene-content-native':'6ec014f558a52361a8ff91933dc2d5ec2595da755ce2730795244f87e74900ef','tw-scene-content-review':'a00d119d0ba65b8b03c788697c655dae43fbbc8b92d8ec8025ce97b1832c9379'}
REMAINING=['Connect actual immutable NPCList and fully qualified EnyName scene contents to the complete TW2A resource/status issuer; B26 highWORD and downstream scene boundary remain opaque. No invented142/26B padding, entity IDs, monster stats or skills.',
 'Actual current gamedata ef297/3131095B is not historical70a4. Factory needs genuine full75c3 decoded source; no encoded-present/decoded/imported/actual DB-loaded claim and no silently refreshed baseline.',
 'Complete actual40 native2A issuer, once-per-Issued admission/lifecycle/scene/replies, explicit Main and all remaining TW gameplay. Retain CN/web/common/numeric64/stack99/frozen features. TW and whole-game denominator/percent null; no Phase1 build/test/native/VM/codec/runtime/DB/SQL/migration/deploy.']
def absolute(value,base=ROOT):
 p=Path(value);return p if p.is_absolute() else base/p
def reports():return [BASE/'packet-progress-latest.json',BASE/'packet-progress-latest.md',ARCHIVE/'round-reports'/(ROUND+'.json'),ARCHIVE/'round-reports'/(ROUND+'.md')]
def external(rel,raw):
 p=ARCHIVE/rel;save(p,raw)
 if p.read_bytes()!=raw:raise RuntimeError('Full external original readback drift')
 return dict(path=str(p),bytes=len(raw),sha256=sha(raw))
def before():
 receipt=read(OUT/'before-receipt.json');raw=matches(Path(receipt['before_manifest']),dict(bytes=Path(receipt['before_manifest']).stat().st_size,sha256='bf6863993f6706ae229e6ef98693ea23ddca5dac9ba885ee27dd61f50d6de069'))
 rows=json.loads(raw)
 if len(rows)!=1537:raise RuntimeError('True1537 before required')
 return rows,{r['path']:matches(absolute(r['snapshot']),r) for r in rows}
def prior():
 receipt=read(OUT/'before-receipt.json');count=0
 for name,pin in receipt['pins'].items():
  raw=(BASE/name/'manifest.json').read_bytes()
  if sha(raw)!=pin or raw!=(ARCHIVE/'retained-prior'/name/'manifest.json').read_bytes():raise RuntimeError('Prior223 seal drift')
  for r in json.loads(raw)['files']:matches(BASE/name/r['path'],r);count+=1
 if count!=92:raise RuntimeError('Full92 prior members required')
 for r in read(OUT/'retained-prior/external-archive-pins.json'):
  matches(Path(r['path']),r);full_external_manifest(Path(r['path']))
def protected(rows,old):
 excluded=set(WRITTEN+BOOKS)|{p.relative_to(ROOT).as_posix() for p in reports()[:2]}
 guarded=[r for r in rows if r['path'] not in excluded]
 for r in guarded:
  if (ROOT/r['path']).read_bytes()!=old[r['path']]:raise RuntimeError('Protected source drift: '+r['path'])
 for r in rows:
  if r['path'].startswith('src/') and r['path'] not in GAME and (ROOT/r['path']).read_bytes()!=old[r['path']]:raise RuntimeError('Unassigned CPP changed')
 return guarded
def agents(old):
 deliveries=[];paths=set()
 for name,pin in AGENTS.items():
  folder=OUT/'agents'/name;raw=(folder/'seal.json').read_bytes()
  if sha(raw)!=pin:raise RuntimeError('Agent seal drift')
  seal=json.loads(raw);members=seal.get('files',seal.get('members'))
  if not isinstance(members,list):raise RuntimeError('Actual full agent member inventory required')
  for r in members:matches(folder/r['path'],r)
  if {r['path'] for r in members}|{'seal.json'}!={r['path'] for r in inventory(folder)}:raise RuntimeError('Agent inventory drift')
  for filename in ['before-source-origins.json','initial-source-origins.json','original-inputs.json','current-source-origins.json','final-original-inputs.json','final-context-origins.json','candidate-context-origins.json','enemy-candidate-source-origins.json']:
   if not (folder/filename).exists():continue
   for r in read(folder/filename):
    path=absolute(r['path']);rel=path.relative_to(ROOT).as_posix();copy=absolute(r['copy'],folder);data=matches(copy,r)
    initial=filename in ['before-source-origins.json','initial-source-origins.json'] or (filename=='original-inputs.json' and rel in old)
    if initial:
     if rel not in old or data!=old[rel]:raise RuntimeError('True source before mismatch: '+rel)
    elif filename not in ['enemy-candidate-source-origins.json'] and data!=matches(path,r):raise RuntimeError('Final source drift: '+rel)
    if r.get('original') and data!=matches(absolute(r['original']),r):raise RuntimeError('In-place before original drift')
    if not rel.startswith('artifacts/'):paths.add(rel)
  for filename in ['native-input-references.json','retained-leaf-references.json','retained-whole-source-references.json']:
   if (folder/filename).exists():
    for r in read(folder/filename):matches(absolute(r['path']),r)
  findings=read(folder/'findings.json')
  if findings.get('blocking',0):raise RuntimeError('Unresolved source blocker')
  deliveries.append(dict(agent=name,seal_sha256=pin,findings=findings,files=inventory(folder)))
 return deliveries,paths
def capture():
 rows,old=before();first=read(OUT/'root-source-firstcandidate-origins.json');initial=[];final=[]
 if {r['path'] for r in first}!=set(GAME):raise RuntimeError('Actual four firstcandidate files required')
 for i,r in enumerate(first):
  if matches(Path(r['copy']),r)!=(ROOT/r['path']).read_bytes():raise RuntimeError('Firstcandidate to final changed')
  value=external('root-source-final/f%d'%i+Path(r['path']).suffix,(ROOT/r['path']).read_bytes())
  final.append(dict(path=r['path'],copy=value['path'],bytes=value['bytes'],sha256=value['sha256']))
  if r['path'] in old:
   row=next(x for x in rows if x['path']==r['path']);initial.append(dict(path=r['path'],copy=row['snapshot'],bytes=row['bytes'],sha256=row['sha256']))
 if len(initial)!=2:raise RuntimeError('Two actual initial originals plus two new files required')
 dump(OUT/'root-source-initial-origins.json',initial);dump(OUT/'root-source-final-origins.json',final)
 print(json.dumps(dict(new_CPP=2,modified_CPP=2,final_bytes=sum(r['bytes'] for r in final),firstcandidate_final_identical=True)))
def originals(old):
 for r in read(OUT/'root-source-initial-origins.json'):
  if matches(Path(r['copy']),r)!=old[r['path']]:raise RuntimeError('True root source initial drift')
 first={r['path']:matches(Path(r['copy']),r) for r in read(OUT/'root-source-firstcandidate-origins.json')}
 for r in read(OUT/'root-source-final-origins.json'):
  if matches(Path(r['copy']),r)!=matches(ROOT/r['path'],r) or first[r['path']]!=(ROOT/r['path']).read_bytes():raise RuntimeError('Full final CPP drift')
def retain_reports(stage):
 dump(OUT/'reports'/(stage+'-full-originals.json'),[external('reports/'+stage+'/'+p.parent.name+'-'+p.name,p.read_bytes()) for p in reports()])
def account():
 if (OUT/'findings.json').exists():raise RuntimeError('Fresh224 account only')
 rows,old=before();prior();guarded=protected(rows,old);originals(old);reviews,paths=agents(old)
 if read(OUT/'policy/goal-before224.json')['goal']['status']!='active':raise RuntimeError('Active goal snapshot required')
 if len([p for p in GAME if p not in old])!=2 or len([p for p in GAME if p in old and (ROOT/p).read_bytes()!=old[p]])!=2:raise RuntimeError('Actual2new2modified CPP required')
 ledger=read(ROOT/BOOKS[1]);previous=json.loads(old[BOOKS[1]])
 if ledger['dual_client_source_segments']!=previous['dual_client_source_segments'] or len(ledger['dual_client_source_segments'])!=212:raise RuntimeError('Historical212 drift')
 paths|=set(WRITTEN)|{'CMakeLists.txt','tools/reconstruction/packet_connection_report.py','tools/strike_lab/recover_companions.py'}
 facts=dict(round=ROUND,research_only=False,previous_goal_turn_classification='progress',completed_parallel_agents=2,new_Cplusplus_source_files_added=2,existing_Cplusplus_source_files_modified=2,new_source_segments=1,source_segments=213,new_packet_values=0,new_source_phase_bindings=0,new_complete_bidirectional_routes=0,whole_game_completion_percent=None,whole_game_denominator=None,tw_completion_percent=None,tw_denominator=None,source_paths=sorted(paths),new_bounded_native_bytes=0,retained_native_bytes=579,retained_native_instructions=193,retained_native_spans=5,retained_query_leaf_bytes=195,actual_NPCList_immutable_full_decoded_pin_required=True,actual_NPCList_full_original_loaded=False,actual_NPCList_451rows_251groups_1509codes=True,actual_NPCList_ordered_append_and_empty_groups=True,actual_NPCList_unsafe_native_input_subset_rejected=True,actual_NPCList_resource_code_not_entity_ID=True,actual_EnyName_full_scene_same_read_snapshot_API=True,actual_EnyName_unloaded_and_missing_scene_distinguished=True,actual_EnyName_ordinal_generation_raw_source_preserved=True,actual_monster_stats_or_skill_data_supplied=False,installed_gamedata_matches_original_source_pin=False,old_source_baseline_refreshed=False,actual_complete2A_producer_policy_supplied=False,actual_Main_factory_selected=False,formal_application_hosted=False,source_conclusion='Actual complete75c3 decoded immutable ownership -> NPCList451 source-row parser -> first-seen251 ordered scene groups /1509 original resource codes -> native quotient/remainder lowBYTE pairs with full occurrence/code retained. Same DB read snapshot -> existing complete7815-row EnyName catalog fingerprint -> exactmain source -> one ordered visible scene record set preserving generation/ordinal/raw provenance; unloaded != qualified absent. New additive source APIs, no bank padding/monster stat/skill/native2A issuer/Main activation claim.',remaining=REMAINING,owner_TW_first=True,owner_requested_stop_after_round=None,owner_requested_pause_at_round_end=False,goal_status_at_source_account='active',build_run=False,tests_run=False,native_execution=False,runtime_run=False,codec_execution=False,database_access=False,SQL_run=False,deployed=False)
 dump(OUT/'findings.json',facts);dump(OUT/'parallel-agent-deliveries.json',reviews);dump(OUT/'sealed-agent-pins.json',AGENTS)
 ledger['tw_native_scene_content_source224']=facts
 ledger['dual_client_source_segments'].append(dict(name=OUT.name,round=ROUND,version_scope='TW-native149c-NPCList-EnyName-actual-ordered-scene-content-source',status=facts['source_conclusion'],source_paths=sorted(paths),native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,tw_source_owner_chains_added=0,formal_application_hosted=False,complete_gameplay_routes_added=0,evidence=OUT.relative_to(ROOT).as_posix(),remaining=REMAINING))
 ledger['dual_client_execution_plan'].update(latest_work_round=ROUND,owner_requested_stop_after_work_round=None,owner_requested_stop_after_round_number=None,continuation_requires_owner_resume=False,owner_TW_first=True,owner_stop_condition='Actual TW complete source100% before stop',next_source_frontier=REMAINING[0])
 (ROOT/BOOKS[1]).write_bytes((json.dumps(ledger,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
 with (ROOT/BOOKS[0]).open('ab') as h:h.write(('\n\n## 第224輪：TW原生場景內容來源\n\n'+(ROOT/DOC).read_text(encoding='utf8')+'\n').encode('utf8'))
 origins=[]
 for i,path in enumerate(sorted(paths|set(BOOKS))):
  data=(ROOT/path).read_bytes();r=external(f'source/current/f{i:03d}'+Path(path).suffix,data);origins.append(dict(path=path,copy=r['path'],bytes=r['bytes'],sha256=r['sha256'],changed_this_round=path not in old or old[path]!=data))
  if path in old and data!=old[path]:
   diff=''.join(difflib.unified_diff(old[path].decode('utf-8-sig').splitlines(True),data.decode('utf-8-sig').splitlines(True),fromfile='before/'+path,tofile='final/'+path))
   if diff:external(f'diff/d{i:03d}.diff',diff.encode('utf8'))
 dump(OUT/'source/source-origins.json',origins)
 print(json.dumps(dict(protected_files=len(guarded),source_files=len(paths),source_segments=213,new_CPP=2,modified_CPP=2,new_complete_routes=0,goal_status='active')))
def enrich():
 retain_reports('raw');receipt=dict(new_CPP=2,modified_CPP=2,source_segments=213,new_source_segments=1,new_complete_bidirectional_routes=0,tw_percent=None,whole_game_percent=None,current_catalog_source_files=len(read(CAT/'source-file-manifest.json')),owner_requested_pause_at_round_end=False)
 for p in [reports()[0],reports()[2]]:
  v=read(p);v['tw_native_scene_content_source224']=read(OUT/'findings.json');v['parallel_agent_deliveries']=read(OUT/'parallel-agent-deliveries.json');v['current_round_source_delta']=receipt;p.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
 for p in [reports()[1],reports()[3]]:p.write_bytes(((ROOT/DOC).read_text(encoding='utf8')+'\n\nStatic accounting: '+json.dumps(receipt)+'\n').encode('utf8'))
 dump(OUT/'reports/enrichment-receipt.json',receipt);print(json.dumps(receipt))
def seal():
 if (OUT/'manifest.json').exists() or (CAT/'manifest.json').exists():raise RuntimeError('Fresh224 seals required')
 rows,old=before();prior();guarded=protected(rows,old);originals(old);reviews,paths=agents(old)
 if reviews!=read(OUT/'parallel-agent-deliveries.json'):raise RuntimeError('Agent epoch drift')
 for r in read(OUT/'source/source-origins.json'):
  if matches(ROOT/r['path'],r)!=matches(Path(r['copy']),r):raise RuntimeError('Full current source drift')
 ledger=read(ROOT/BOOKS[1])
 if ledger['dual_client_source_segments'][:212]!=json.loads(old[BOOKS[1]])['dual_client_source_segments'] or len(ledger['dual_client_source_segments'])!=213:raise RuntimeError('Historical212/new213 drift')
 sources=read(CAT/'source-file-manifest.json')
 for path,r in sources.items():matches(ROOT/path,r)
 arc=full_external_manifest(CAT/'external-archive-manifest.json')
 entries=[r for r in read(CAT/'input-manifest.json') if r['input']=='source-ledger']
 if len(entries)!=1 or matches(absolute(entries[0]['snapshot'],CAT),entries[0])!=(ROOT/BOOKS[1]).read_bytes():raise RuntimeError('Full catalog ledger drift')
 a,b,c,d=reports()
 if a.read_bytes()!=c.read_bytes() or b.read_bytes()!=d.read_bytes():raise RuntimeError('Final full report mismatch')
 value=read(a)
 if value['round']!=ROUND or value['route_ledger_sha256']!=sha((ROOT/BOOKS[1]).read_bytes()) or value['dual_client_endpoint_catalog']['summary']!=read(CAT/'summary.json'):raise RuntimeError('Report/catalog mismatch')
 for key in ['whole_game_distinct_packet_count','whole_game_completed_route_count','whole_game_completion_percent']:
  if value['counts'][key] is not None:raise RuntimeError('False whole-game denominator')
 for name in ['capacity-before-seal.json','capacity-full-before-seal.json']:
  cap=read(OUT/'policy'/name)
  if not cap['under_limit'] or cap['unreadable_count'] or cap.get('cycles'):raise RuntimeError('WholeGod2 capacity failed')
 retain_reports('final')
 full=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p.read_bytes())) for p in sorted(ARCHIVE.rglob('*')) if p.is_file()]
 dump(OUT/'external-full-originals-receipt.json',dict(root=str(ARCHIVE),verified=True,original_bytes_retained=True,files=full));full_external_manifest(OUT/'external-full-originals-receipt.json')
 flags=dict(sealed=True,research_only=False,method='STATIC_SOURCE_CONNECTION_ACCOUNTING_ONLY',build_run=False,tests_run=False,native_execution=False,runtime_run=False,codec_execution=False,database_access=False,SQL_run=False,deployed=False)
 cm=dict(round=CAT.name,**flags,current_source_files=len(sources),external_originals_verified=True,external_full_file_count=len(arc['files']),files=inventory(CAT));dump(CAT/'manifest.json',cm)
 rm=dict(round=ROUND,**flags,before_files=len(rows),protected_files=len(guarded),source_segments=213,new_source_segments=1,new_CPP=2,modified_CPP=2,final_CPP_bytes=sum(r['bytes'] for r in read(OUT/'root-source-final-origins.json')),new_complete_bidirectional_routes=0,tw_percent=None,whole_game_percent=None,external_originals_verified=True,catalog_manifest_sha256=sha((CAT/'manifest.json').read_bytes()),files=inventory(OUT));dump(OUT/'manifest.json',rm)
 print(json.dumps(dict(root_members=len(rm['files']),catalog_members=len(cm['files']),root_sha256=sha((OUT/'manifest.json').read_bytes()),catalog_sha256=sha((CAT/'manifest.json').read_bytes()),source_segments=213,new_complete_routes=0)))
if __name__=='__main__':
 if len(sys.argv)!=2 or sys.argv[1] not in ['capture','account','enrich','seal']:raise RuntimeError('capture/account/enrich/seal required')
 globals()[sys.argv[1]]()
