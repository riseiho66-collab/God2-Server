"""Round213 immutable static file/source accounting; never executes game/SQL."""
from pathlib import Path
import json,sys,difflib
from .parallel_game_connection_frontier_delivery import ROOT,sha,read,save,dump,matches,inventory

BASE=ROOT/'artifacts/integration/packet-connections-20261006'
OUT=BASE/'tw-native-advertised-route-source-01';CAT=BASE/'endpoint-catalog213'
ROUND='20261009-tw-native-advertised-route-source'
DOC='docs/research/tw-native-advertised-route-source-20261009.md'
GAME=['src/net/Session.h', 'src/net/Session.cpp', 'src/game/SharedTaiwanNativeCharacterListSource.h', 'src/game/SharedTaiwanNativeCharacterListSource.cpp', 'src/protocol/RecoveredTaiwanServerAdvertisement.h']
WRITTEN=GAME+[DOC,'tools/reconstruction/tw_native_advertised_route_source_delivery.py','tools/reconstruction/dual_client_route_catalog.py']
BOOKS=['docs/PACKET_CONNECTION_GOAL_20261006.md',(BASE/'packet-route-ledger.json').relative_to(ROOT).as_posix()]
PINS={'tw-native-server-select-source-01':'1c766ee8adbde3127acd3f8ae67d2f2998691126cb8ecffd639df6f2d156173d','endpoint-catalog212':'bc70f4f66df0977453a14ff483d1b842e9cb424ec395540bfc7cbba7e1f43da6'}
REMAINING=['Actual advertised table/target/phase/current and native07 issuer remain required; preserve raw A6 inputs without guessed group/server or candidate success.',
 'Connect real cross-socket published-list/selection epoch, queue-current atomics and full2A lineage; independent world socket has no account A6 observation.',
 'Complete post-create native header/issuer, initial-scene/peer publication/full5D Authority/Main and all remaining TW native routes, numeric64/stack99 and complete denominator; TW first, preserve CN/web/common. Latest owner request pauses after213; resume requires owner instruction.',
 'No builds/tests/native/codec/runtime/DB/SQL/deploy execution in Phase1; comprehensive tests and repair/release follow all source connections.']

def reports():return [BASE/'packet-progress-latest.json',BASE/'packet-progress-latest.md',BASE/'round-reports'/(ROUND+'.json'),BASE/'round-reports'/(ROUND+'.md')]
def before():
 raw=(OUT/'before-manifest.json').read_bytes()
 if sha(raw)!='e0791d9893e6ceb22ecdcf53024c7b3bc649979afd810f396a934ece70bb1cfd':raise RuntimeError('Actual213 before drift')
 rows=json.loads(raw)
 if len(rows)!=1489:raise RuntimeError('Full1489 before required')
 return rows,{r['path']:matches(OUT/r['snapshot'],r) for r in rows}
def prior():
 count=0
 for n,pin in PINS.items():
  raw=(BASE/n/'manifest.json').read_bytes()
  if sha(raw)!=pin or raw!=(OUT/'retained-prior'/n/'manifest.json').read_bytes():raise RuntimeError('Prior212 seal drift')
  for r in json.loads(raw)['files']:matches(BASE/n/r['path'],r);count+=1
 if count!=2541:raise RuntimeError('Full2541 prior212 members required')
def protected(rows,old):
 excluded=set(WRITTEN+BOOKS)|{p.relative_to(ROOT).as_posix() for p in reports()[:2]}
 guarded=[r for r in rows if r['path'] not in excluded]
 for r in guarded:
  if (ROOT/r['path']).read_bytes()!=old[r['path']]:raise RuntimeError('Protected source drift: '+r['path'])
 for r in rows:
  if r['path'].startswith('src/') and r['path'] not in GAME and (ROOT/r['path']).read_bytes()!=old[r['path']]:raise RuntimeError('Unassigned CPP drift')
 return guarded
def originals(old):
 initial=read(OUT/'root-source-initial/origins.json');candidate=read(OUT/'root-source-candidate/origins.json');final=read(OUT/'root-source-final/origins.json')
 if len(initial)!=4 or len(candidate)!=5 or len(final)!=5:raise RuntimeError('Full initial4/candidate5/final5 required')
 if {r['path'] for r in candidate}!=set(GAME) or {r['path'] for r in final}!=set(GAME):raise RuntimeError('Exact assigned5 CPP required')
 if {r['path'] for r in initial}!={p for p in GAME if p in old}:raise RuntimeError('Exact initial4 source set required')
 for r in initial:
  if matches(OUT/r['copy'],r)!=old[r['path']]:raise RuntimeError('Initial-before epoch mismatch')
 for r in candidate:matches(OUT/r['copy'],r)
 for r in final:
  if matches(ROOT/r['path'],r)!=matches(OUT/r['copy'],r):raise RuntimeError('Final CPP epoch mismatch')
 r=read(OUT/'retained-accounting-source212.json')
 if matches(OUT/r['copy'],r)!=matches(ROOT/r['path'],r):raise RuntimeError('Retained complete prior accounting source differs')
 if read(OUT/'policy/goal-before213.json')['goal']['status']!='active':raise RuntimeError('Actual active goal snapshot required')
def absolute(value):
 p=Path(value);return p if p.is_absolute() else ROOT/p
def agents(old):
 pins=read(OUT/'sealed-agent-pins.json');deliveries=[];paths=set();epochs=[]
 names=['tw-selector-advertisement-fields','tw-advertisement-source-review']
 if set(pins)!=set(names):raise RuntimeError('Two actual213 bounded deliveries required')
 for name in names:
  folder=OUT/'agents'/name;raw=(folder/'seal.json').read_bytes()
  if sha(raw)!=pins[name]:raise RuntimeError('Agent213 seal drift')
  members=json.loads(raw).get('files',json.loads(raw).get('members'))
  if not isinstance(members,list):raise RuntimeError('Full agent member inventory required')
  for r in members:matches(folder/r['path'],r)
  if {r['path'] for r in inventory(folder)}!={r['path'] for r in members}|{'seal.json'}:raise RuntimeError('Full213 member drift')
  current=read(folder/'current-source-origins.json')
  for r in current:
   p=absolute(r['path']);rel=p.relative_to(ROOT).as_posix()
   retained=matches(folder/r['copy'],r)
   if p.read_bytes()!=retained:raise RuntimeError('Actual213 current source drift: '+rel)
   artifact_tool=p in [folder/'review_account.py',folder/'static_capture.py']
   if (rel.startswith('artifacts/') and not artifact_tool) or rel in BOOKS:raise RuntimeError('Receipt is not source original')
   if not artifact_tool:paths.add(rel)
  for r in read(folder/'native-input-references.json') if (folder/'native-input-references.json').exists() else []:
   original=matches(absolute(r['path']),r)
   if r.get('copy') and original!=matches(folder/r['copy'],r):raise RuntimeError('Native complete retained source differs')
  for r in read(folder/'original-inputs.json'):
   p=absolute(r['path']);rel=p.relative_to(ROOT).as_posix();raw=matches(folder/r['copy'],r)
   if name=='tw-advertisement-source-review':
    if rel not in old or raw!=old[rel]:raise RuntimeError('Actual initial213 epoch differs')
   elif p.read_bytes()!=raw:raise RuntimeError('Retained213 native evidence drift')
  if name=='tw-advertisement-source-review':
   for r in read(folder/'final-original-inputs.json'):
    if matches(absolute(r['path']),r)!=matches(folder/r['copy'],r):raise RuntimeError('Actual final213 differs')
  deliveries.append(dict(agent=name,seal_sha256=sha((folder/'seal.json').read_bytes()),findings=read(folder/'findings.json'),current_source_origins=current,files=inventory(folder)))
 return deliveries,paths,epochs
def account():
 if (OUT/'findings.json').exists():raise RuntimeError('Fresh213 account only')
 rows,old=before();prior();guarded=protected(rows,old);originals(old);reviews,paths,epochs=agents(old)
 cap=read(OUT/'policy/capacity-before-final-account.json')
 if cap['unreadable_count'] or not cap['under_limit']:raise RuntimeError('WholeGod2 capacity required')
 added=[p for p in GAME if p not in old];changed=[p for p in GAME if p in old and (ROOT/p).read_bytes()!=old[p]]
 if len(added)!=1 or len(changed)!=4:raise RuntimeError('Actual1 new and4 changed CPP required')
 ledger=read(ROOT/BOOKS[1]);previous=json.loads(old[BOOKS[1]])
 if ledger['dual_client_source_segments']!=previous['dual_client_source_segments'] or len(ledger['dual_client_source_segments'])!=202:raise RuntimeError('Historical202 drift')
 paths|=set(WRITTEN)|{'CMakeLists.txt'}
 facts=dict(round=ROUND,research_only=False,completed_parallel_agents=2,new_Cplusplus_source_files_added=1,
  existing_Cplusplus_source_files_modified=4,new_source_segments=1,source_segments=203,new_packet_values=0,
  new_source_phase_bindings=0,new_complete_bidirectional_routes=0,whole_game_completion_percent=None,whole_game_denominator=None,
  tw_completion_percent=None,tw_denominator=None,source_paths=sorted(paths),new_bounded_native_bytes=0,
  retained_native_caller_bytes=939,retained_native_caller_instructions=267,retained_native_caller_spans=23,retained_native_switch_bytes=55,retained_native_length_pointer_bytes=12,
  actual_socket_write_completed_advertisement_observation=True,actual_write_queue_identity_bytes_session_checked=True,immutable_advertisement_captured_strand_to_game=True,candidate_origin_retained=True,actual_S04_full_body_ordinal_mask_preserved=True,actual_known_profile_S04_S05_S06_lengths_retained=True,actual_native_list_Scope_advertised_rows_connected=True,malformed_present_advertisement_rejected=True,independent_world_socket_selection_observation_absent=True,native_advertisement_grants_invented=False,dynamic_seed_generalization=False,queue_current_atomicity_complete=False,cross_socket_issued_list_epoch_complete=False,
  actual_plan_capability_default_false=True,raw07_selected40_equivalent=False,
  actual_complete_native_issuer_supplied=False,actual_Main_factory_selected=False,formal_application_hosted=False,
  source_conclusion='Actual native-list-only queued advertisement bytes/session/candidate origin -> exact successful socket write observation -> owned A6 request and immutable advertisement captured to game -> once immutable selection -> native List/Select Scope parsed complete S04 ordinal/body/mask and original05/06 wire -> real Target/Current/Qualify. Malformed present advertisement rejects, independent world remains genuinely absent. Socket write is not peer ACK/native authority; full issued list/queue/crosssocket/native07/Main remain OPEN',
  remaining=REMAINING,source_epoch_reconciliation=epochs,owner_TW_first=True,prior_five_round_stop_revoked=True,
  owner_requested_stop_after_round=213,owner_requested_pause_at_round_end=True,goal_status_at_source_account='active',
  build_run=False,tests_run=False,native_execution=False,runtime_run=False,codec_execution=False,database_access=False,SQL_run=False,deployed=False)
 dump(OUT/'parallel-agent-deliveries.json',reviews);dump(OUT/'source-epoch-reconciliation.json',epochs);dump(OUT/'findings.json',facts)
 ledger['tw_native_advertised_route_source213']=facts
 ledger['dual_client_source_segments'].append(dict(name=OUT.name,round=ROUND,version_scope='TW-native-advertised-S04-S05-S06-actual-write-A6-immutable-character-source',status=facts['source_conclusion'],source_paths=sorted(paths),native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,tw_source_owner_chains_added=0,formal_application_hosted=False,complete_gameplay_routes_added=0,evidence=OUT.relative_to(ROOT).as_posix(),remaining=REMAINING))
 plan=ledger['dual_client_execution_plan'];plan.update(latest_work_round=ROUND,owner_requested_stop_after_work_round=ROUND,owner_requested_stop_after_round_number=213,continuation_requires_owner_resume=True,owner_TW_first=True,prior_five_round_stop_revoked=True,owner_stop_condition='Latest owner instruction: finish round213 and pause; TW100 remains unfinished objective',next_source_frontier=REMAINING[0])
 (ROOT/BOOKS[1]).write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 with (ROOT/BOOKS[0]).open('ab') as handle:handle.write(('\n\n## 第213輪：TW实际送出清单与选服输入来源\n\n'+(ROOT/DOC).read_text(encoding='utf8')+'\n').encode())
 origins=[]
 for i,p in enumerate(sorted(paths|set(BOOKS))):
  raw=(ROOT/p).read_bytes();copy=f'source/current/f{i:03d}'+Path(p).suffix;save(OUT/copy,raw)
  origins.append(dict(path=p,copy=copy,bytes=len(raw),sha256=sha(raw),changed_this_round=p not in old or old[p]!=raw))
  if p in old and raw!=old[p]:
   diff=''.join(difflib.unified_diff(old[p].decode('utf-8-sig').splitlines(True),raw.decode('utf-8-sig').splitlines(True),fromfile='before/'+p,tofile='final/'+p))
   if diff:save(OUT/'diff'/f'd{i:03d}.diff',diff.encode())
 dump(OUT/'source/source-origins.json',origins)
 print(json.dumps(dict(protected_files=len(guarded),source_files=len(paths),source_segments=203,new_CPP=1,modified_CPP=4,new_complete_routes=0,goal_status='active')))
def enrich():
 for p in reports():save(OUT/'reports/raw'/(p.parent.name+'-'+p.name),p.read_bytes())
 receipt=dict(new_CPP=1,modified_CPP=4,source_segments=203,new_source_segments=1,new_complete_bidirectional_routes=0,whole_game_percent=None,tw_percent=None,current_catalog_source_files=len(read(CAT/'source-file-manifest.json')),owner_requested_pause_at_round_end=True)
 for p in [reports()[0],reports()[2]]:
  v=read(p);v['tw_native_advertised_route_source213']=read(OUT/'findings.json');v['parallel_agent_deliveries']=read(OUT/'parallel-agent-deliveries.json');v['current_round_source_delta']=receipt
  p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 for p in [reports()[1],reports()[3]]:p.write_text((ROOT/DOC).read_text(encoding='utf8')+'\n\nStatic accounting: '+json.dumps(receipt)+'\n',encoding='utf8')
 dump(OUT/'reports/enrichment-receipt.json',receipt);print(json.dumps(receipt))
def seal():
 if (OUT/'manifest.json').exists() or (CAT/'manifest.json').exists():raise RuntimeError('Fresh213 seals required')
 rows,old=before();prior();guarded=protected(rows,old);originals(old);reviews,paths,epochs=agents(old)
 if reviews!=read(OUT/'parallel-agent-deliveries.json') or epochs!=read(OUT/'source-epoch-reconciliation.json'):raise RuntimeError('Agent/epoch drift')
 for r in read(OUT/'source/source-origins.json'):
  if matches(ROOT/r['path'],r)!=matches(OUT/r['copy'],r):raise RuntimeError('Root final source drift')
 ledger=read(ROOT/BOOKS[1])
 if ledger['dual_client_source_segments'][:202]!=json.loads(old[BOOKS[1]])['dual_client_source_segments'] or len(ledger['dual_client_source_segments'])!=203:raise RuntimeError('Historical202/new203 drift')
 sources=read(CAT/'source-file-manifest.json')
 for n,r in sources.items():matches(ROOT/n,r)
 entries=[r for r in read(CAT/'input-manifest.json') if r['input']=='source-ledger']
 if len(entries)!=1 or matches(CAT/entries[0]['snapshot'],entries[0])!=(ROOT/BOOKS[1]).read_bytes():raise RuntimeError('Current catalog ledger drift')
 a,b,c,d=reports()
 if a.read_bytes()!=c.read_bytes() or b.read_bytes()!=d.read_bytes():raise RuntimeError('Final report mismatch')
 v=read(a)
 if v['round']!=ROUND or v['route_ledger_sha256']!=sha((ROOT/BOOKS[1]).read_bytes()) or v['dual_client_endpoint_catalog']['summary']!=read(CAT/'summary.json'):raise RuntimeError('Report/catalog mismatch')
 for k in ['whole_game_distinct_packet_count','whole_game_completed_route_count','whole_game_completion_percent']:
  if v['counts'][k] is not None:raise RuntimeError('False whole-game denominator')
 for p in reports():save(OUT/'reports/final'/(p.parent.name+'-'+p.name),p.read_bytes())
 flags=dict(sealed=True,method='STATIC_SOURCE_INTEGRATION_ONLY',build_run=False,tests_run=False,native_execution=False,runtime_run=False,database_access=False,SQL_run=False,deployed=False)
 cm=dict(round=CAT.name,**flags,current_source_files=len(sources),files=inventory(CAT));dump(CAT/'manifest.json',cm)
 rm=dict(round=ROUND,**flags,before_files=len(rows),protected_files=len(guarded),source_segments=203,new_source_segments=1,new_CPP=1,modified_CPP=4,new_complete_bidirectional_routes=0,whole_game_percent=None,tw_percent=None,owner_requested_stop_after_round=213,catalog_manifest_sha256=sha((CAT/'manifest.json').read_bytes()),files=inventory(OUT));dump(OUT/'manifest.json',rm)
 print(json.dumps(dict(root_members=len(rm['files']),catalog_members=len(cm['files']),root_sha256=sha((OUT/'manifest.json').read_bytes()),catalog_sha256=sha((CAT/'manifest.json').read_bytes()))))
if __name__=='__main__':
 if len(sys.argv)!=2 or sys.argv[1] not in ['account','enrich','seal']:raise RuntimeError('account/enrich/seal required')
 globals()[sys.argv[1]]()
