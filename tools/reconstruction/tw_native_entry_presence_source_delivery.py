"""Round222 immutable static file/source accounting; no game/SQL execution."""
from pathlib import Path
import json,sys,difflib
from .parallel_game_connection_frontier_delivery import ROOT,sha,read,save,dump,matches,inventory

BASE=ROOT/'artifacts/integration/packet-connections-20261006'
OUT=BASE/'tw-native-entry-presence-source-01';CAT=BASE/'endpoint-catalog222'
ARCHIVE=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261010/tw-native-entry-presence-source-01')
ROUND='20261010-tw-native-entry-presence-source'
DOC='docs/research/tw-native-entry-presence-source-20261010.md'
GAME=['src/game/SharedTaiwanWorldEntrySource.h','src/game/SharedTaiwanWorldEntrySource.cpp','src/core/SharedTaiwanNativeWorldHostPlan.cpp']
WRITTEN=GAME+[DOC,'tools/reconstruction/tw_native_entry_presence_source_delivery.py','tools/reconstruction/dual_client_route_catalog.py','tools/reconstruction/packet_connection_report.py']
BOOKS=['docs/PACKET_CONNECTION_GOAL_20261006.md',(BASE/'packet-route-ledger.json').relative_to(ROOT).as_posix()]
PINS={'tw-native-entry-offer-source-01':'9422ee4302219a1e4914047c132cf7208a3a6b5b7025e9fb8d01630a2ff9058f','endpoint-catalog221':'87c8658d0fe67199d8e8fd8fe891915d36bb4963debf40d534d64cf435aff8c1'}
AGENTS={'tw-entry-presence-native':'e5f0d209862baa716eecf37a098d22052fd2594eafeb676f4f3081370cc83eb7','tw-entry-presence-review':'5027c0d3d3c0c001e8544fb33913d3ce4b634112f02459b6f65e677271b5e53a'}
REMAINING=[
 'Provide actual complete40 TW native opaque/resource/status issuer and concrete authority policy. Entry prewrite now observes actual same CommonPresence character exclusion; it creates no Lease or admission rights.',
 'Connect once-per-Issued admission, parallel/cross-G replay rights, complete lifecycle/scene/replies and post-return queue consistency. Different-character actor-handle collisions still fail in existing later lifecycle.prepare. No admission CAS claim.',
 'Select explicitly qualified Main sources and connect all remaining actual TW gameplay handlers/rules/storage/replies/consumers. Preserve CN/web and all frozen functionality.',
 'Finish TW direction/state/variant/deferred complete route inventory. TW and whole-game denominator/percentage remain null; no Phase1 builds/tests/native/runtime/codec/DB/SQL/migrations/deploy. Continue until actual TW100 before stop.']

def reports():return [BASE/'packet-progress-latest.json',BASE/'packet-progress-latest.md',BASE/'round-reports'/(ROUND+'.json'),BASE/'round-reports'/(ROUND+'.md')]
def absolute(value,base=ROOT):
 p=Path(value);return p if p.is_absolute() else base/p
def before():
 raw=(OUT/'before-manifest.json').read_bytes()
 if sha(raw)!='db1f35f024c259c6c73abbadaf160ed4f94d613f07d9175cb779bb6e5c636a84':raise RuntimeError('Actual222 before drift')
 rows=json.loads(raw)
 if len(rows)!=1521:raise RuntimeError('Full1521 before required')
 return rows,{r['path']:matches(absolute(r['snapshot'],OUT),r) for r in rows}
def prior():
 count=0
 for name,pin in PINS.items():
  raw=(BASE/name/'manifest.json').read_bytes()
  if sha(raw)!=pin or raw!=(OUT/'retained-prior'/name/'manifest.json').read_bytes():raise RuntimeError('Immutable prior221 seal drift')
  for row in json.loads(raw)['files']:matches(BASE/name/row['path'],row);count+=1
 if count!=1142:raise RuntimeError('Full1142 prior221 members required')
 for row in read(BASE/'tw-native-entry-offer-source-01/source/source-origins.json'):
  matches(absolute(row['copy'],BASE/'tw-native-entry-offer-source-01'),row)
def protected(rows,old):
 excluded=set(WRITTEN+BOOKS)|{p.relative_to(ROOT).as_posix() for p in reports()[:2]}
 guarded=[r for r in rows if r['path'] not in excluded]
 for row in guarded:
  if (ROOT/row['path']).read_bytes()!=old[row['path']]:raise RuntimeError('Protected source drift: '+row['path'])
 for row in rows:
  if row['path'].startswith('src/') and row['path'] not in GAME and (ROOT/row['path']).read_bytes()!=old[row['path']]:raise RuntimeError('Unassigned CPP drift')
 return guarded
def originals(old):
 groups=[read(OUT/f'root-source-{stage}/origins.json') for stage in ['initial','candidate','final']]
 for rows in groups:
  if len(rows)!=3 or {r['path'] for r in rows}!=set(GAME):raise RuntimeError('Exact initial/candidate/final3 required')
 for row in groups[0]:
  if matches(OUT/row['copy'],row)!=old[row['path']]:raise RuntimeError('Genuine initial epoch mismatch')
 candidate={r['path']:matches(OUT/r['copy'],r) for r in groups[1]}
 for row in groups[2]:
  if matches(ROOT/row['path'],row)!=matches(OUT/row['copy'],row) or candidate[row['path']]!=(ROOT/row['path']).read_bytes():raise RuntimeError('Final/candidate epoch mismatch')
 row=read(OUT/'retained-accounting-source221.json')
 if matches(OUT/row['copy'],row)!=matches(ROOT/row['path'],row):raise RuntimeError('Complete prior accounting source differs')
 if read(OUT/'policy/goal-before222.json')['goal']['status']!='active':raise RuntimeError('Actual active goal snapshot required')
def agent_records(old):
 deliveries=[];paths=set()
 for name,pin in AGENTS.items():
  folder=OUT/'agents'/name;raw=(folder/'seal.json').read_bytes()
  if sha(raw)!=pin:raise RuntimeError('Actual222 agent seal drift')
  seal=json.loads(raw);members=seal.get('files',seal.get('members'))
  if not isinstance(members,list):raise RuntimeError('Actual full agent inventory required')
  for row in members:matches(folder/row['path'],row)
  if {r['path'] for r in inventory(folder)}!={r['path'] for r in members}|{'seal.json'}:raise RuntimeError('Agent extra/missing files')
  current=read(folder/'current-source-origins.json')
  for row in current:
   path=absolute(row['path']);rel=path.relative_to(ROOT).as_posix()
   if matches(path,row)!=matches(absolute(row['copy'],folder),row):raise RuntimeError('Current agent source drift')
   artifact_tool=path in [folder/'review_account.py',folder/'static_capture.py']
   if (rel.startswith('artifacts/') and not artifact_tool) or rel in BOOKS:raise RuntimeError('Receipt is not a source original')
   if not artifact_tool:paths.add(rel)
  for row in read(folder/'original-inputs.json'):
   path=absolute(row['path']);rel=path.relative_to(ROOT).as_posix();raw=matches(absolute(row['copy'],folder),row)
   if name=='tw-entry-presence-review':
    if rel not in old or raw!=old[rel]:raise RuntimeError('Actual initial222 epoch differs')
   elif raw!=path.read_bytes() and (rel not in old or raw!=old[rel]):raise RuntimeError('Native original epoch differs')
  for filename in ['before-source-origins.json','before-supplemental-source-origins.json']:
   if not (folder/filename).exists():continue
   for row in read(folder/filename):
    rel=absolute(row['path']).relative_to(ROOT).as_posix()
    if rel not in old or matches(absolute(row['copy'],folder),row)!=old[rel]:raise RuntimeError('Before epoch drift')
  for filename in ['final-original-inputs.json','final-context-origins.json']:
   if not (folder/filename).exists():continue
   for row in read(folder/filename):
    path=absolute(row['path']);rel=path.relative_to(ROOT).as_posix()
    if matches(path,row)!=matches(absolute(row['copy'],folder),row):raise RuntimeError('Final agent epoch drift')
    if not rel.startswith('artifacts/'):paths.add(rel)
  for filename in ['native-input-references.json','retained-references.json','prior221-whole-inplace-references.json','source-inplace-references.json']:
   if not (folder/filename).exists():continue
   for row in read(folder/filename):
    path=absolute(row['path']);raw=matches(path,row)
    if row.get('copy') and raw!=matches(absolute(row['copy'],folder),row):raise RuntimeError('Referenced full original differs')
    if filename=='source-inplace-references.json':paths.add(path.relative_to(ROOT).as_posix())
  if (folder/'current-inplace-source-origins.json').exists():
   for row in read(folder/'current-inplace-source-origins.json'):
    path=absolute(row['path']);rel=path.relative_to(ROOT).as_posix();raw=matches(path,row)
    if raw!=matches(Path(row['immutable_copy']),row) or raw!=matches(Path(row['true_before']),row) or raw!=old[rel]:raise RuntimeError('Actual unchanged large source original drift')
    paths.add(rel)
  findings=read(folder/'findings.json')
  if findings.get('blocking',0):raise RuntimeError('Unresolved static source blocker')
  deliveries.append(dict(agent=name,seal_sha256=pin,findings=findings,current_source_origins=current,files=inventory(folder)))
 return deliveries,paths
def external_write(rel,raw):
 path=ARCHIVE/rel;save(path,raw)
 if path.read_bytes()!=raw:raise RuntimeError('Complete external original readback differs')
 return dict(path=str(path),bytes=len(raw),sha256=sha(raw))
def retain_reports(stage):
 rows=[]
 for path in reports():rows.append(external_write('reports/'+stage+'/'+path.parent.name+'-'+path.name,path.read_bytes()))
 dump(OUT/'reports'/(stage+'-full-originals.json'),rows)
def capacities():
 for name in ['capacity-before-final-account.json','capacity-full-before-final-account.json']:
  cap=read(OUT/'policy'/name)
  if cap['unreadable_count'] or not cap['under_limit'] or cap.get('cycles'):raise RuntimeError('Required full current God2 capacity scope failed')
def account():
 if (OUT/'findings.json').exists() or ARCHIVE.exists():raise RuntimeError('Fresh222 account and owned archive only')
 rows,old=before();prior();guarded=protected(rows,old);originals(old);reviews,paths=agent_records(old);capacities()
 added=[p for p in GAME if p not in old];changed=[p for p in GAME if (ROOT/p).read_bytes()!=old[p]]
 if added or len(changed)!=3:raise RuntimeError('Actual0new3modified CPP required')
 ledger=read(ROOT/BOOKS[1]);previous=json.loads(old[BOOKS[1]])
 if ledger['dual_client_source_segments']!=previous['dual_client_source_segments'] or len(ledger['dual_client_source_segments'])!=211:raise RuntimeError('Historical211 drift')
 paths|=set(WRITTEN)|{'CMakeLists.txt'}
 facts=dict(round=ROUND,research_only=False,previous_goal_turn_classification='progress',completed_parallel_agents=2,
  new_Cplusplus_source_files_added=0,existing_Cplusplus_source_files_modified=3,new_source_segments=1,source_segments=212,
  new_packet_values=0,new_source_phase_bindings=0,new_complete_bidirectional_routes=0,whole_game_completion_percent=None,
  whole_game_denominator=None,tw_completion_percent=None,tw_denominator=None,source_paths=sorted(paths),new_bounded_native_bytes=0,
  retained_native_caller_bytes=2308,retained_native_caller_spans=8,actual_same_CommonPresence_selected_entry_required=True,
  actual_same_characters_repository_required=True,actual_raw_character_reserved_before_after_common_source_reads=True,
  actual_initial_supply_and_three_issuer_boundaries_parent_Current=True,actual_Prepared_active_stale_unreleased_all_excluded=True,
  actual_same_session_exemption=False,actual_Lease_created_released_or_taken_over=False,actual_presence_native_rights_inferred=False,
  actual_different_character_actor_collision_prechecked=False,actual_admission_CAS_replay_parallelG_complete=False,
  actual_post_return_queue_atomicity=False,actual_complete2A_producer_policy_supplied=False,actual_Main_factory_selected=False,
  formal_application_hosted=False,external_full_source_report_and_catalog_originals_retained=True,
  source_conclusion='Actual same CommonHost Presence and actual same characters repository -> native Selected Entry unchanged Current reads raw full-character reservation before/after common roots/position/map -> first supply and Prepare Prepared/BeforeWrite/BeforeCommit parent Current -> fresh full native entry. Existing Prepared/active/unreleased and same-session exclusion is preserved without creating/taking/releasing a Lease. Existing later lifecycle still reserves and checks actor collisions. Pure synchronous pre-use policy; no admission CAS, cross-G replay right, invented native issuer/frame or queue/publication claim.',
  remaining=REMAINING,owner_TW_first=True,prior_five_round_stop_revoked=True,owner_requested_stop_after_round=None,
  owner_requested_pause_at_round_end=False,goal_status_at_source_account='active',build_run=False,tests_run=False,
  native_execution=False,runtime_run=False,codec_execution=False,database_access=False,SQL_run=False,deployed=False)
 dump(OUT/'parallel-agent-deliveries.json',reviews);dump(OUT/'findings.json',facts);dump(OUT/'sealed-agent-pins.json',AGENTS)
 ledger['tw_native_entry_presence_source222']=facts
 ledger['dual_client_source_segments'].append(dict(name=OUT.name,round=ROUND,version_scope='TW-native-actual-same-CommonPresence-entry-prewrite-current',status=facts['source_conclusion'],source_paths=sorted(paths),native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,tw_source_owner_chains_added=0,formal_application_hosted=False,complete_gameplay_routes_added=0,evidence=OUT.relative_to(ROOT).as_posix(),remaining=REMAINING))
 ledger['dual_client_execution_plan'].update(latest_work_round=ROUND,owner_requested_stop_after_work_round=None,owner_requested_stop_after_round_number=None,continuation_requires_owner_resume=False,owner_TW_first=True,prior_five_round_stop_revoked=True,owner_stop_condition='Owner resumed20261010: TW actual complete source routes100% before stop',next_source_frontier=REMAINING[0])
 (ROOT/BOOKS[1]).write_bytes((json.dumps(ledger,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
 with (ROOT/BOOKS[0]).open('ab') as handle:handle.write(('\n\n## 第222輪：TW入場前共用角色占用來源\n\n'+(ROOT/DOC).read_text(encoding='utf8')+'\n').encode('utf8'))
 origins=[]
 for i,path in enumerate(sorted(paths|set(BOOKS))):
  raw=(ROOT/path).read_bytes();entry=external_write(f'source/current/f{i:03d}'+Path(path).suffix,raw)
  origins.append(dict(path=path,copy=entry['path'],bytes=entry['bytes'],sha256=entry['sha256'],changed_this_round=path not in old or old[path]!=raw))
  if path in old and raw!=old[path]:
   diff=''.join(difflib.unified_diff(old[path].decode('utf-8-sig').splitlines(True),raw.decode('utf-8-sig').splitlines(True),fromfile='before/'+path,tofile='final/'+path))
   if diff:external_write(f'diff/d{i:03d}.diff',diff.encode('utf8'))
 dump(OUT/'source/source-origins.json',origins)
 print(json.dumps(dict(protected_files=len(guarded),source_files=len(paths),source_segments=212,new_CPP=0,modified_CPP=3,new_complete_routes=0,goal_status='active')))
def enrich():
 retain_reports('raw')
 receipt=dict(new_CPP=0,modified_CPP=3,source_segments=212,new_source_segments=1,new_complete_bidirectional_routes=0,whole_game_percent=None,tw_percent=None,current_catalog_source_files=len(read(CAT/'source-file-manifest.json')),owner_requested_pause_at_round_end=False)
 for path in [reports()[0],reports()[2]]:
  value=read(path);value['tw_native_entry_presence_source222']=read(OUT/'findings.json');value['parallel_agent_deliveries']=read(OUT/'parallel-agent-deliveries.json');value['current_round_source_delta']=receipt
  path.write_bytes((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
 for path in [reports()[1],reports()[3]]:path.write_bytes(((ROOT/DOC).read_text(encoding='utf8')+'\n\nStatic accounting: '+json.dumps(receipt)+'\n').encode('utf8'))
 dump(OUT/'reports/enrichment-receipt.json',receipt);print(json.dumps(receipt))
def archive_inventory(folder):return [dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p.read_bytes())) for p in sorted(folder.rglob('*')) if p.is_file()]
def full_external_manifest(path):
 manifest=read(path);folder=Path(manifest['root'])
 owned=(Path.home()/'.codex/artifact-archives/god2-server').resolve()
 if not folder.is_absolute() or not folder.resolve().is_relative_to(owned) or folder.resolve()==owned or not manifest.get('verified') or not manifest.get('original_bytes_retained'):raise RuntimeError('Owned complete external archive required')
 for row in manifest['files']:
  item=Path(row['path'])
  if not item.resolve().is_relative_to(folder.resolve()):raise RuntimeError('External archive path escape')
  matches(item,row)
 if {r['path'] for r in manifest['files']}!={r['path'] for r in archive_inventory(folder)}:raise RuntimeError('External full archive inventory mismatch')
 return manifest
def seal():
 if (OUT/'manifest.json').exists() or (CAT/'manifest.json').exists():raise RuntimeError('Fresh222 seals required')
 rows,old=before();prior();guarded=protected(rows,old);originals(old);reviews,paths=agent_records(old)
 if reviews!=read(OUT/'parallel-agent-deliveries.json'):raise RuntimeError('Agent epoch drift')
 for row in read(OUT/'source/source-origins.json'):
  if matches(ROOT/row['path'],row)!=matches(Path(row['copy']),row):raise RuntimeError('Full root final source drift')
 ledger=read(ROOT/BOOKS[1])
 if ledger['dual_client_source_segments'][:211]!=json.loads(old[BOOKS[1]])['dual_client_source_segments'] or len(ledger['dual_client_source_segments'])!=212:raise RuntimeError('Historical211/new212 drift')
 sources=read(CAT/'source-file-manifest.json')
 for name,row in sources.items():matches(ROOT/name,row)
 archive=full_external_manifest(CAT/'external-archive-manifest.json')
 entries=[row for row in read(CAT/'input-manifest.json') if row['input']=='source-ledger']
 if len(entries)!=1 or matches(absolute(entries[0]['snapshot'],CAT),entries[0])!=(ROOT/BOOKS[1]).read_bytes():raise RuntimeError('Current catalog full ledger drift')
 a,b,c,d=reports()
 if a.read_bytes()!=c.read_bytes() or b.read_bytes()!=d.read_bytes():raise RuntimeError('Final report mismatch')
 value=read(a)
 if value['round']!=ROUND or value['route_ledger_sha256']!=sha((ROOT/BOOKS[1]).read_bytes()) or value['dual_client_endpoint_catalog']['summary']!=read(CAT/'summary.json'):raise RuntimeError('Report/current catalog mismatch')
 for key in ['whole_game_distinct_packet_count','whole_game_completed_route_count','whole_game_completion_percent']:
  if value['counts'][key] is not None:raise RuntimeError('False whole-game denominator')
 retain_reports('final')
 own=dict(root=str(ARCHIVE),verified=True,original_bytes_retained=True,files=archive_inventory(ARCHIVE))
 dump(OUT/'external-full-originals-receipt.json',own);full_external_manifest(OUT/'external-full-originals-receipt.json')
 flags=dict(sealed=True,method='STATIC_SOURCE_INTEGRATION_ONLY',build_run=False,tests_run=False,native_execution=False,runtime_run=False,database_access=False,SQL_run=False,deployed=False)
 cm=dict(round=CAT.name,**flags,current_source_files=len(sources),external_originals_verified=True,external_full_file_count=len(archive['files']),external_archive_manifest_sha256=sha((CAT/'external-archive-manifest.json').read_bytes()),files=inventory(CAT));dump(CAT/'manifest.json',cm)
 rm=dict(round=ROUND,**flags,before_files=len(rows),protected_files=len(guarded),source_segments=212,new_source_segments=1,new_CPP=0,modified_CPP=3,new_complete_bidirectional_routes=0,whole_game_percent=None,tw_percent=None,owner_requested_stop_after_round=None,external_originals_verified=True,catalog_manifest_sha256=sha((CAT/'manifest.json').read_bytes()),files=inventory(OUT));dump(OUT/'manifest.json',rm)
 print(json.dumps(dict(root_members=len(rm['files']),catalog_members=len(cm['files']),root_sha256=sha((OUT/'manifest.json').read_bytes()),catalog_sha256=sha((CAT/'manifest.json').read_bytes()),external_catalog_files=len(archive['files']),external_root_files=len(own['files']))))
if __name__=='__main__':
 if len(sys.argv)!=2 or sys.argv[1] not in ['account','enrich','seal']:raise RuntimeError('account/enrich/seal required')
 globals()[sys.argv[1]]()
