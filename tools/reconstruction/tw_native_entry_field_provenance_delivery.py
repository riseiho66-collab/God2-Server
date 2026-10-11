"""Round223 static source/file research accounting; no game or SQL execution."""
from pathlib import Path
import json,sys
from .parallel_game_connection_frontier_delivery import ROOT,sha,read,save,dump,matches,inventory
from .tw_native_entry_presence_source_delivery import full_external_manifest

BASE=ROOT/'artifacts/integration/packet-connections-20261006'
OUT=BASE/'tw-native-entry-field-provenance-source-01';CAT=BASE/'endpoint-catalog223'
ARCHIVE=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261010/tw-native-entry-field-provenance-source-01/root-source-account')
ROUND='20261010-tw-native-entry-field-provenance'
DOC='docs/research/tw-native-entry-field-provenance-source-20261010.md'
WRITTEN=[DOC,'tools/reconstruction/tw_native_entry_field_provenance_delivery.py','tools/reconstruction/dual_client_route_catalog.py','tools/reconstruction/packet_connection_report.py']
BOOKS=['docs/PACKET_CONNECTION_GOAL_20261006.md',(BASE/'packet-route-ledger.json').relative_to(ROOT).as_posix()]
PINS={'tw-native-entry-presence-source-01':'33db456f2174d7d8cc30d7781c70fbbe72e54b50adb15754195ef5da4a0effbb','endpoint-catalog222':'f47aa89d69dc9370da91330451ed0bc662ab7d0f2c0b769027d4a3d7b09f1b82'}
AGENTS={'tw-entry-field-provenance':'523e4e93d898c2e2fe1fd4a6b5f7488276fa8d71a28b8a242645094487451df1','tw-entry-field-source-review':'ed7217dae5c35fbe4e169cca1d2c01d7865195fd9136c9293e38d0f3d00c7cb8'}
REMAINING=['Implement actual immutable NPCList ordered scene resource groups and EnyName scene descriptors from qualified original sources, preserving empty groups/order/duplicate-area replacement and source occurrence identity. Existing EnyName complete catalog contract is reusable; per-row lookup is not full bank.','Current installed gamedata ef297/3131095B differs from original70a4/75c3 pins. Qualify true original inputs or use independently fully qualified stored catalog; do not silently refresh evidence, decode/import current file, or call this a global blocker.','Complete actual full40 native2A issuer, one-use admission/lifecycle/scene/replies, explicit Main and all remaining TW gameplay; preserve CN/web/common/numeric64/stack99/frozen features. Whole TW and whole-game denominator/percent remain null; no Phase1 builds/tests/native/codec/runtime/DB/SQL/migrations/deploy.']
def absolute(value,base=ROOT):
 p=Path(value);return p if p.is_absolute() else base/p
def reports():return [BASE/'packet-progress-latest.json',BASE/'packet-progress-latest.md',ARCHIVE/'round-reports'/(ROUND+'.json'),ARCHIVE/'round-reports'/(ROUND+'.md')]
def before():
 raw=(OUT/'before-manifest.json').read_bytes()
 if sha(raw)!='6135f26a4cd6838b71349be872568fe1cbaeeaa524acda390f9f3274ca4a0239':raise RuntimeError('True223 before drift')
 rows=json.loads(raw)
 if len(rows)!=1523:raise RuntimeError('Full1523 before required')
 return rows,{r['path']:matches(absolute(r['snapshot'],OUT),r) for r in rows}
def prior():
 count=0
 for name,pin in PINS.items():
  raw=(BASE/name/'manifest.json').read_bytes()
  if sha(raw)!=pin or raw!=(OUT/'retained-prior'/name/'manifest.json').read_bytes():raise RuntimeError('Prior222 seal drift')
  for r in json.loads(raw)['files']:matches(BASE/name/r['path'],r);count+=1
 if count!=165:raise RuntimeError('Full165 local prior members required')
 for r in read(OUT/'retained-prior/external-archive-pins.json'):
  matches(Path(r['path']),r);full_external_manifest(Path(r['path']))
def protected(rows,old):
 excluded=set(WRITTEN+BOOKS)|{p.relative_to(ROOT).as_posix() for p in reports()[:2]}
 guarded=[r for r in rows if r['path'] not in excluded]
 for r in guarded:
  if (ROOT/r['path']).read_bytes()!=old[r['path']]:raise RuntimeError('Protected source drift: '+r['path'])
 for r in rows:
  if r['path'].startswith('src/') and (ROOT/r['path']).read_bytes()!=old[r['path']]:raise RuntimeError('Research223 cannot change CPP')
 return guarded
def agents(old):
 deliveries=[];paths=set()
 for name,pin in AGENTS.items():
  folder=OUT/'agents'/name;raw=(folder/'seal.json').read_bytes()
  if sha(raw)!=pin:raise RuntimeError('Actual223 agent seal drift')
  seal=json.loads(raw);members=seal.get('files',seal.get('members'))
  if not isinstance(members,list):raise RuntimeError('Full local agent inventory required')
  for r in members:matches(folder/r['path'],r)
  if {r['path'] for r in members}|{'seal.json'}!={r['path'] for r in inventory(folder)}:raise RuntimeError('Agent extra/missing file')
  for filename in ['current-source-origins.json','original-inputs.json','final-original-inputs.json','before-source-origins.json']:
   if not (folder/filename).exists():continue
   for r in read(folder/filename):
    path=absolute(r['path']);rel=path.relative_to(ROOT).as_posix();copy=absolute(r['copy'],folder);raw=matches(copy,r)
    if filename=='before-source-origins.json' or (filename=='original-inputs.json' and name=='tw-entry-field-source-review'):
     if rel in old:
      if raw!=old[rel]:raise RuntimeError('Genuine source before223 mismatch')
     elif filename!='original-inputs.json' or name!='tw-entry-field-source-review' or r.get('epoch')!='initial-actual-no-root-before-entry' or raw!=matches(path,r):
      raise RuntimeError('Untracked original must remain explicit actual agent initial, never invented root before')
    elif raw!=matches(path,r):raise RuntimeError('Actual current full source drift')
    if r.get('original') and raw!=matches(Path(r['original']),r):raise RuntimeError('Absolute original before drift')
    own=path in [folder/'static_capture.py',folder/'review_account.py']
    if rel.startswith('artifacts/') and not own:raise RuntimeError('Receipt cannot substitute source original')
    if not own:paths.add(rel)
  for filename in ['native-input-references.json','retained-whole-source-references.json']:
   if not (folder/filename).exists():continue
   for r in read(folder/filename):matches(absolute(r['path']),r)
  if (folder/'data-source-qualification.json').exists():matches(Path(read(folder/'data-source-qualification.json')['current_full_encoded_source']['path']),read(folder/'data-source-qualification.json')['current_full_encoded_source'])
  facts=read(folder/'findings.json')
  if facts.get('blocking',0):raise RuntimeError('Unresolved source review blocker')
  deliveries.append(dict(agent=name,seal_sha256=pin,findings=facts,files=inventory(folder)))
 return deliveries,paths
def external(rel,raw):
 p=ARCHIVE/rel;save(p,raw)
 if p.read_bytes()!=raw:raise RuntimeError('Full external byte readback differs')
 return dict(path=str(p),bytes=len(raw),sha256=sha(raw))
def retain_reports(stage):
 rows=[external('reports/'+stage+'/'+p.parent.name+'-'+p.name,p.read_bytes()) for p in reports()]
 dump(OUT/'reports'/(stage+'-full-originals.json'),rows)
def account():
 if (OUT/'findings.json').exists() or ARCHIVE.exists():raise RuntimeError('Fresh223 root accounting only')
 rows,old=before();prior();guarded=protected(rows,old);reviews,paths=agents(old)
 if read(OUT/'policy/goal-before223.json')['goal']['status']!='active':raise RuntimeError('Actual active goal snapshot required')
 ledger=read(ROOT/BOOKS[1]);previous=json.loads(old[BOOKS[1]])
 if ledger['dual_client_source_segments']!=previous['dual_client_source_segments'] or len(ledger['dual_client_source_segments'])!=212:raise RuntimeError('Historical212 source segments drift')
 paths|=set(WRITTEN)|{'tools/reconstruction/tw_native_entry_presence_source_delivery.py','CMakeLists.txt'}
 facts=dict(round=ROUND,research_only=True,previous_goal_turn_classification='progress',completed_parallel_agents=2,new_Cplusplus_source_files_added=0,existing_Cplusplus_source_files_modified=0,new_source_segments=0,source_segments=212,new_packet_values=0,new_source_phase_bindings=0,new_complete_bidirectional_routes=0,whole_game_completion_percent=None,whole_game_denominator=None,tw_completion_percent=None,tw_denominator=None,source_paths=sorted(paths),new_bounded_native_bytes=0,retained_native_leaf_bytes=195,retained_native_leaf_instructions=74,retained_native_leaf_spans=2,actual_two_pure_lookup_highWORD_narrowing_proven=True,whole_B26_highWORD_semantics_recovered=False,actual_NPCList_scene_groups_distinct_from_NPCAppearData=True,actual_EnyName_importer_build149c=True,actual_existing_EnyName_complete_catalog_contract_reusable=True,actual_EnyName_scene_bank_API_complete=False,actual_NPCList_formal_scene_group_catalog_available=False,installed_gamedata_matches_original_source_pin=False,old_source_baseline_refreshed=False,actual_complete2A_producer_policy_supplied=False,source_conclusion='Pinned149c pure NPCList and EnyName scene-query operands narrow area/scene and ignore body26 highWORD locally; later scene boundary remains opaque. Qualified existing same149c EnyName full catalog can supply a future ordered scene descriptor; current per-row API is not a bank. NPCList451/251/1509 is distinct from6bf NPCAppearData4043. Current encoded gamedata ef297 differs from original70a4; no silent new baseline/import/decoder. Next actual implementation: immutable original ordered NPCList groups and final-visible EnyName descriptors, no invented monster stats/placement/full2A.',remaining=REMAINING,owner_TW_first=True,owner_requested_stop_after_round=None,owner_requested_pause_at_round_end=False,goal_status_at_source_account='active',build_run=False,tests_run=False,native_execution=False,runtime_run=False,codec_execution=False,database_access=False,SQL_run=False,deployed=False)
 dump(OUT/'findings.json',facts);dump(OUT/'parallel-agent-deliveries.json',reviews);dump(OUT/'sealed-agent-pins.json',AGENTS)
 extra=[r for r in read(OUT/'agents/tw-entry-field-source-review/original-inputs.json') if r['path'] not in old]
 dump(OUT/'supplemental-source-read-epochs.json',dict(full_agent_initial_originals=extra,actual_originals_equal_current=True,parent_before_expanded=False,note='These12 newly read dependency originals have explicit initial-actual-no-root-before-entry;1523 parent before stays immutable. No CPP source changed.'))
 ledger['tw_native_entry_field_provenance223']=facts
 ledger.setdefault('dual_client_research_frontiers',[]).append(dict(name=OUT.name,round=ROUND,research_only=True,new_source_segments=0,new_complete_bidirectional_routes=0,source_paths=sorted(paths),evidence=OUT.relative_to(ROOT).as_posix(),conclusion=facts['source_conclusion'],remaining=REMAINING))
 ledger['dual_client_execution_plan'].update(latest_work_round=ROUND,owner_requested_stop_after_work_round=None,owner_requested_stop_after_round_number=None,continuation_requires_owner_resume=False,owner_TW_first=True,owner_stop_condition='Actual TW complete source100% before stop',next_source_frontier=REMAINING[0])
 (ROOT/BOOKS[1]).write_bytes((json.dumps(ledger,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
 with (ROOT/BOOKS[0]).open('ab') as h:h.write(('\n\n## 第223輪：TW2A場景bank資料來源研究\n\n'+(ROOT/DOC).read_text(encoding='utf8')+'\n').encode('utf8'))
 origins=[]
 for i,path in enumerate(sorted(paths|set(BOOKS))):
  r=external(f'source/current/f{i:03d}'+Path(path).suffix,(ROOT/path).read_bytes());origins.append(dict(path=path,copy=r['path'],bytes=r['bytes'],sha256=r['sha256'],changed_this_round=path not in old or old[path]!=(ROOT/path).read_bytes()))
 dump(OUT/'source/source-origins.json',origins)
 print(json.dumps(dict(protected_files=len(guarded),source_files=len(paths),source_segments=212,new_CPP=0,modified_CPP=0,new_complete_routes=0,research_only=True,goal_status='active')))
def enrich():
 retain_reports('raw');receipt=dict(new_CPP=0,modified_CPP=0,source_segments=212,new_source_segments=0,new_complete_bidirectional_routes=0,research_only=True,tw_percent=None,whole_game_percent=None,current_catalog_source_files=len(read(CAT/'source-file-manifest.json')),owner_requested_pause_at_round_end=False)
 for p in [reports()[0],reports()[2]]:
  v=read(p);v['tw_native_entry_field_provenance223']=read(OUT/'findings.json');v['parallel_agent_deliveries']=read(OUT/'parallel-agent-deliveries.json');v['current_round_source_delta']=receipt;p.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
 for p in [reports()[1],reports()[3]]:p.write_bytes(((ROOT/DOC).read_text(encoding='utf8')+'\n\nStatic accounting: '+json.dumps(receipt)+'\n').encode('utf8'))
 dump(OUT/'reports/enrichment-receipt.json',receipt);print(json.dumps(receipt))
def seal():
 if (OUT/'manifest.json').exists() or (CAT/'manifest.json').exists():raise RuntimeError('Fresh223 seals required')
 rows,old=before();prior();guarded=protected(rows,old);reviews,paths=agents(old)
 if reviews!=read(OUT/'parallel-agent-deliveries.json'):raise RuntimeError('Agent epoch drift')
 for r in read(OUT/'source/source-origins.json'):
  if matches(ROOT/r['path'],r)!=matches(Path(r['copy']),r):raise RuntimeError('Full final source drift')
 if read(ROOT/BOOKS[1])['dual_client_source_segments']!=json.loads(old[BOOKS[1]])['dual_client_source_segments']:raise RuntimeError('Research cannot add source segment')
 sources=read(CAT/'source-file-manifest.json')
 for path,r in sources.items():matches(ROOT/path,r)
 arc=full_external_manifest(CAT/'external-archive-manifest.json')
 ledgerrows=[r for r in read(CAT/'input-manifest.json') if r['input']=='source-ledger']
 if len(ledgerrows)!=1 or matches(absolute(ledgerrows[0]['snapshot'],CAT),ledgerrows[0])!=(ROOT/BOOKS[1]).read_bytes():raise RuntimeError('Current full catalog ledger mismatch')
 a,b,c,d=reports()
 if a.read_bytes()!=c.read_bytes() or b.read_bytes()!=d.read_bytes():raise RuntimeError('Final full report mismatch')
 value=read(a)
 if value['round']!=ROUND or value['route_ledger_sha256']!=sha((ROOT/BOOKS[1]).read_bytes()) or value['dual_client_endpoint_catalog']['summary']!=read(CAT/'summary.json'):raise RuntimeError('Report/catalog mismatch')
 for key in ['whole_game_distinct_packet_count','whole_game_completed_route_count','whole_game_completion_percent']:
  if value['counts'][key] is not None:raise RuntimeError('False denominator')
 for filename in ['capacity-before-seal.json','capacity-full-before-seal.json']:
  cap=read(OUT/'policy'/filename)
  if not cap['under_limit'] or cap['unreadable_count'] or cap.get('cycles'):raise RuntimeError('Actual whole God2 capacity scope failed')
 retain_reports('final')
 full=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p.read_bytes())) for p in sorted(ARCHIVE.rglob('*')) if p.is_file()]
 dump(OUT/'external-full-originals-receipt.json',dict(root=str(ARCHIVE),verified=True,original_bytes_retained=True,files=full));full_external_manifest(OUT/'external-full-originals-receipt.json')
 flags=dict(sealed=True,research_only=True,method='STATIC_SOURCE_RESEARCH_ONLY',build_run=False,tests_run=False,native_execution=False,runtime_run=False,codec_execution=False,database_access=False,SQL_run=False,deployed=False)
 cm=dict(round=CAT.name,**flags,current_source_files=len(sources),external_originals_verified=True,external_full_file_count=len(arc['files']),files=inventory(CAT));dump(CAT/'manifest.json',cm)
 rm=dict(round=ROUND,**flags,before_files=len(rows),protected_files=len(guarded),source_segments=212,new_source_segments=0,new_CPP=0,modified_CPP=0,new_complete_bidirectional_routes=0,tw_percent=None,whole_game_percent=None,external_originals_verified=True,catalog_manifest_sha256=sha((CAT/'manifest.json').read_bytes()),files=inventory(OUT));dump(OUT/'manifest.json',rm)
 print(json.dumps(dict(root_members=len(rm['files']),catalog_members=len(cm['files']),root_sha256=sha((OUT/'manifest.json').read_bytes()),catalog_sha256=sha((CAT/'manifest.json').read_bytes()),source_segments=212,new_complete_routes=0)))
if __name__=='__main__':
 if len(sys.argv)!=2 or sys.argv[1] not in ['account','enrich','seal']:raise RuntimeError('account/enrich/seal required')
 globals()[sys.argv[1]]()
