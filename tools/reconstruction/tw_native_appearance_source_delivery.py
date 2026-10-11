"""Round227 static file accounting. Never executes native/game/codec/SQL."""
from pathlib import Path
import json,sys,difflib
from .parallel_game_connection_frontier_delivery import ROOT,sha,read,save,dump,matches,inventory
from .tw_native_entry_presence_source_delivery import full_external_manifest
BASE=ROOT/'artifacts/integration/packet-connections-20261006'
TASK=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261010/tw-native-appearance-source-01')
OUT=TASK/'root';ARCHIVE=OUT/'full-originals';CAT=TASK/'catalog-metadata'
LOCAL=BASE/'tw-native-appearance-source-01';INDEX=BASE/'endpoint-catalog227'
ROUND='20261010-tw-native-appearance-source'
DOC='docs/research/tw-native-appearance-source-20261010.md'
GAME=['src/protocol/RecoveredWorldEntryView.h','src/game/SharedTaiwanWorldEntered.h']
TOOLS=['tools/reconstruction/dual_client_route_catalog.py','tools/reconstruction/packet_connection_report.py']
AGENTS={'tw-appearance-native':'a58645c961f1e4c7b737d70e2c73eb038792af0d42444cb91af679b481ec9b17','tw-appearance-review':'64c399fda8ef88020c5f391acc5182d7c81c4b2d4e8f50d49d5db971fc144ebe'}
WRITTEN=GAME+TOOLS+[DOC,'tools/reconstruction/tw_native_appearance_source_delivery.py']
BOOKS=['docs/PACKET_CONNECTION_GOAL_20261006.md',(BASE/'packet-route-ledger.json').relative_to(ROOT).as_posix()]
REMAINING=['Actual entry baseline now directly available from same complete scene Scope view; recover true149c mutation/committed after-state issuer and item/transform mapping, then update full witness and qualify already-spawned observers. Old2A baseline is not current after-state;6bf/CUSTOM0047 is not149c authority.',
 'Recover B0/B4 resource/status and B8..11/B26..27/kind actual producer. B26 highWORD scene-argument claim is corrected; unknown callee aliases remain OPEN, no zero/default inference.',
 'Complete actual40 native2A issuer, once-per-Issued admission/lifecycle/scene/replies, explicit Main and remaining TW whole gameplay. Preserve CN/web/common/numeric64/stack99/frozen features. Denominator/percent null; Phase1 no execution/test/DB/SQL/deploy.']

def absolute(v,base=ROOT):
 p=Path(v);return p if p.is_absolute() else base/p

def external(rel,raw):
 p=ARCHIVE/rel;save(p,raw)
 if p.read_bytes()!=raw:raise RuntimeError('Full original readback drift')
 return dict(path=str(p),bytes=len(raw),sha256=sha(raw))

def reports():return [BASE/'packet-progress-latest.json',BASE/'packet-progress-latest.md',ARCHIVE/'round-reports'/(ROUND+'.json'),ARCHIVE/'round-reports'/(ROUND+'.md')]

def before():
 raw=(OUT/'before-manifest.json').read_bytes()
 if sha(raw)!='9eda87fbc6452b368e7b0e01e7f96aae36912049fc6b50d8891433b728221a9b':raise RuntimeError('Truebefore1550 pin drift')
 rows=json.loads(raw)
 if len(rows)!=1550:raise RuntimeError('Truebefore1550 required')
 return rows,{r['path']:matches(absolute(r['snapshot']),r) for r in rows}

def prior():
 count=0
 for name,pin in read(OUT/'before-receipt.json')['pins'].items():
  folder=Path(pin['root']);raw=(folder/'manifest.json').read_bytes()
  if sha(raw)!=pin['sha256'] or raw!=(OUT/'retained-prior'/name/'manifest.json').read_bytes():raise RuntimeError('Prior226 seal drift')
  for r in json.loads(raw)['files']:matches(folder/r['path'],r);count+=1
 if count!=89:raise RuntimeError('Prior226 full89 required')
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

def agent_deliveries():
 paths=set();reviews=[];_,old=before()
 if set(AGENTS)!={'tw-appearance-native','tw-appearance-review'}:raise RuntimeError('Two terminal agent pins required')
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
  for filename in ['original-inputs.json','final-original-inputs.json','final-context-origins.json','current-source-origins.json','initial-source-origins.json','before-source-origins.json','supplemental-source-origins.json']:
   if not (folder/filename).exists():continue
   value=read(folder/filename);value=value.get('files',[]) if isinstance(value,dict) else value
   for r in value:
    if not isinstance(r,dict) or 'path' not in r or 'copy' not in r:continue
    data=matches(absolute(r['copy'],folder),r)
    p=absolute(r['path'])
    rel=p.relative_to(ROOT).as_posix() if p.is_relative_to(ROOT) else None
    initial=filename in ['initial-source-origins.json','before-source-origins.json'] or (name=='tw-appearance-review' and filename=='original-inputs.json')
    if initial and rel in old and data!=old[rel]:raise RuntimeError('Truebefore agent source drift')
    if filename in ['final-original-inputs.json','final-context-origins.json','current-source-origins.json'] and matches(p,r)!=data:raise RuntimeError('Agent final source drift')
    if rel and not rel.startswith('artifacts/'):paths.add(rel)
  for filename in ['native-input-references.json','native-image-reference.json','preserved-history.json','preserved-history-references.json','history-input-references.json','peer-mask-table-reference.json','root-before-reference.json','before-input-reference.json','addendum-source-reference.json']:
   if (folder/filename).exists():refs(read(folder/filename))
  facts=read(folder/'findings.json')
  if facts.get('blocking',0):raise RuntimeError('Agent blocking finding')
  reviews.append(dict(agent=name,seal_sha256=sha(raw),files=inventory(folder),findings=facts))
 return reviews,paths

def capture():
 rows,old=before();result=[]
 for i,path in enumerate(TOOLS):
  raw=(ROOT/path).read_bytes();r=external(f'tools/first/f{i}.py',raw)
  result.append(dict(path=path,copy=r['path'],bytes=r['bytes'],sha256=r['sha256']))
 dump(OUT/'root-tool-firstcandidate-origins.json',result)

def cpp_originals(old):
 first=read(OUT/'root-source-firstcandidate-origins.json')
 if {r['path'] for r in first}!=set(GAME):raise RuntimeError('Two actual CPP candidates required')
 for r in first:
  if r['path'] not in old or old[r['path']]==matches(ROOT/r['path'],r) or matches(Path(r['copy']),r)!=(ROOT/r['path']).read_bytes():raise RuntimeError('Two modified unchanged-final CPP required')

def tool_originals():
 for r in read(OUT/'root-tool-firstcandidate-origins.json'):
  if matches(Path(r['copy']),r)!=matches(ROOT/r['path'],r):raise RuntimeError('Tool firstcandidate/final drift')

def account():
 if (OUT/'findings.json').exists():raise RuntimeError('Fresh227 account required')
 rows,old=before();prior();guarded=protected(rows,old);tool_originals();cpp_originals(old);reviews,paths=agent_deliveries()
 if read(OUT/'policy/goal-before227.json')['goal']['status']!='active':raise RuntimeError('Active goal required')
 ledger=read(ROOT/BOOKS[1]);previous=json.loads(old[BOOKS[1]])
 if ledger['dual_client_source_segments']!=previous['dual_client_source_segments'] or len(ledger['dual_client_source_segments'])!=214:raise RuntimeError('Historical214 drift')
 paths|=set(WRITTEN)|{'CMakeLists.txt'}
 facts=dict(round=ROUND,research_only=False,completed_parallel_agents=2,new_Cplusplus_source_files_added=0,existing_Cplusplus_source_files_modified=2,new_source_segments=0,source_segments=214,new_packet_values=0,new_complete_bidirectional_routes=0,whole_game_completion_percent=None,whole_game_denominator=None,tw_completion_percent=None,tw_denominator=None,source_paths=sorted(paths),new_bounded_native_bytes=0,retained_native_bytes=713,retained_native_instructions=242,retained_native_spans=12,actual_same_entry_view_to_scene_baseline=True,entry_baseline_is_current_after_state=False,ordinary_transform0_local_DA_full8_component_saved_copy=True,remote_DA_full8_saved_copy=False,remote_DA_override_updates_saved_odd_bytes=False,actual_complete2A_producer_policy_supplied=False,formal_application_hosted=False,source_conclusion='Actual complete2A entry view retained by Binding/AsyncBinding and Scene Scope now exposes owned by-value full8components, transformWORD and two raw scalars plus boundactor directly to scene source. Same149c ordinary transform0 local DA full8 saved copy independently reconciled; remote DA only updates saved odd-byte high3 absent override, not full8. Entry baseline only, no current after-state/DA grant, new DB/cache,6bf promotion, opaque defaults, full producer or completed route.',remaining=REMAINING,owner_TW_first=True,owner_requested_pause_at_round_end=False,goal_status_at_source_account='active',build_run=False,tests_run=False,native_execution=False,runtime_run=False,codec_execution=False,database_access=False,SQL_run=False,deployed=False)
 dump(OUT/'findings.json',facts);dump(OUT/'parallel-agent-deliveries.json',reviews)
 dump(OUT/'sealed-agent-pins.json',{r['agent']:r['seal_sha256'] for r in reviews})
 ledger['tw_native_appearance227']=facts
 ledger['dual_client_execution_plan'].update(latest_work_round=ROUND,owner_requested_stop_after_work_round=None,owner_requested_stop_after_round_number=None,continuation_requires_owner_resume=False,owner_TW_first=True,owner_stop_condition='Actual TW complete source100% before stop',next_source_frontier=REMAINING[0])
 (ROOT/BOOKS[1]).write_bytes((json.dumps(ledger,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
 with (ROOT/BOOKS[0]).open('ab') as h:h.write(('\n\n## 第227輪：實際入場資料直接供應場景外觀基準\n\n'+(ROOT/DOC).read_text(encoding='utf8')+'\n').encode('utf8'))
 origins=[]
 for i,path in enumerate(sorted(paths|set(BOOKS))):
  raw=(ROOT/path).read_bytes();r=external(f'source/current/f{i:03d}'+Path(path).suffix,raw)
  origins.append(dict(path=path,copy=r['path'],bytes=r['bytes'],sha256=r['sha256'],changed_this_round=path not in old or old[path]!=raw))
  if path in old and raw!=old[path]:
   diff=''.join(difflib.unified_diff(old[path].decode('utf-8-sig').splitlines(True),raw.decode('utf-8-sig').splitlines(True),fromfile='before/'+path,tofile='final/'+path))
   if diff:external(f'diff/d{i:03d}.diff',diff.encode('utf8'))
 dump(OUT/'source/source-origins.json',origins)
 print(json.dumps(dict(protected_files=len(guarded),source_files=len(paths),source_segments=214,new_CPP=0,modified_CPP=2,new_complete_routes=0,goal_status='active')))

def retain_reports(stage):dump(OUT/'reports'/(stage+'-full-originals.json'),[external('reports/'+stage+'/'+p.parent.name+'-'+p.name,p.read_bytes()) for p in reports()])

def enrich():
 retain_reports('raw');receipt=dict(new_CPP=0,modified_CPP=2,source_segments=214,new_source_segments=0,new_complete_bidirectional_routes=0,tw_percent=None,whole_game_percent=None,current_catalog_source_files=len(read(CAT/'source-file-manifest.json')),owner_requested_pause_at_round_end=False)
 for p in [reports()[0],reports()[2]]:
  v=read(p);v['tw_native_appearance227']=read(OUT/'findings.json');v['parallel_agent_deliveries']=read(OUT/'parallel-agent-deliveries.json');v['current_round_source_delta']=receipt;p.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
 for p in [reports()[1],reports()[3]]:p.write_bytes(((ROOT/DOC).read_text(encoding='utf8')+'\n\nStatic accounting: '+json.dumps(receipt)+'\n').encode('utf8'))
 dump(OUT/'reports/enrichment-receipt.json',receipt);print(json.dumps(receipt))

def seal():
 if (OUT/'manifest.json').exists() or (CAT/'manifest.json').exists():raise RuntimeError('Fresh227 seals required')
 rows,old=before();prior();guarded=protected(rows,old);tool_originals();cpp_originals(old);reviews,paths=agent_deliveries()
 if reviews!=read(OUT/'parallel-agent-deliveries.json'):raise RuntimeError('Agent epoch drift')
 for r in read(OUT/'source/source-origins.json'):
  if matches(ROOT/r['path'],r)!=matches(Path(r['copy']),r):raise RuntimeError('Full current source drift')
 ledger=read(ROOT/BOOKS[1])
 if ledger['dual_client_source_segments']!=json.loads(old[BOOKS[1]])['dual_client_source_segments'] or len(ledger['dual_client_source_segments'])!=214:raise RuntimeError('Historical214 changed')
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
 for name in ['capacity-before-seal.json','capacity-full-before-seal.json']:
  cap=read(OUT/'policy'/name)
  if not cap['under_limit'] or cap['unreadable_count'] or cap.get('cycles'):raise RuntimeError('WholeGod2 capacity failed')
 retain_reports('final')
 full=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p.read_bytes())) for p in sorted(ARCHIVE.rglob('*')) if p.is_file()]
 dump(OUT/'external-full-originals-receipt.json',dict(root=str(ARCHIVE),verified=True,original_bytes_retained=True,files=full));full_external_manifest(OUT/'external-full-originals-receipt.json')
 flags=dict(sealed=True,research_only=False,method='STATIC_SOURCE_ACCOUNTING_ONLY',build_run=False,tests_run=False,native_execution=False,runtime_run=False,codec_execution=False,database_access=False,SQL_run=False,deployed=False)
 cm=dict(round=INDEX.name,**flags,current_source_files=len(sources),external_originals_verified=True,external_full_file_count=len(arc['files']),files=inventory(CAT));dump(CAT/'manifest.json',cm)
 rm=dict(round=ROUND,**flags,before_files=len(rows),protected_files=len(guarded),source_segments=214,new_source_segments=0,new_CPP=0,modified_CPP=2,final_CPP_bytes=sum(r['bytes'] for r in read(OUT/'root-source-firstcandidate-origins.json')),new_complete_bidirectional_routes=0,tw_percent=None,whole_game_percent=None,external_originals_verified=True,catalog_manifest_sha256=sha((CAT/'manifest.json').read_bytes()),files=inventory(OUT));dump(OUT/'manifest.json',rm)
 pins=dict(root=str(OUT),root_manifest_sha256=sha((OUT/'manifest.json').read_bytes()),root_members=len(rm['files']),catalog_root=str(CAT),catalog_manifest_sha256=sha((CAT/'manifest.json').read_bytes()),verified=True,original_bytes_retained=True)
 dump(LOCAL/'external-final-seal.json',pins);dump(INDEX/'external-final-seal.json',pins)
 print(json.dumps(dict(root_members=len(rm['files']),catalog_members=len(cm['files']),root_sha256=pins['root_manifest_sha256'],catalog_sha256=pins['catalog_manifest_sha256'],source_segments=214,new_complete_routes=0)))

if __name__=='__main__':
 if len(sys.argv)!=2 or sys.argv[1] not in ['capture','account','enrich','seal']:raise RuntimeError('capture/account/enrich/seal required')
 globals()[sys.argv[1]]()
