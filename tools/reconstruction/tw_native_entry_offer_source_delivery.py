"""Round221 immutable static file/source accounting; never executes game/SQL."""
from pathlib import Path
import json,sys,difflib
from .parallel_game_connection_frontier_delivery import ROOT,sha,read,save,dump,matches,inventory

BASE=ROOT/'artifacts/integration/packet-connections-20261006'
OUT=BASE/'tw-native-entry-offer-source-01';CAT=BASE/'endpoint-catalog221'
ROUND='20261010-tw-native-entry-offer-source'
DOC='docs/research/tw-native-entry-offer-source-20261010.md'
GAME=['src/game/SharedTaiwanNativeWorldEntryOfferSource.h', 'src/game/SharedTaiwanNativeWorldEntryOfferSource.cpp', 'src/game/SharedTaiwanWorldEntrySource.h', 'src/game/SharedTaiwanWorldEntrySource.cpp', 'src/core/SharedTaiwanNativeWorldHostPlan.h', 'src/core/SharedTaiwanNativeWorldHostPlan.cpp', 'src/core/SharedWorldHostPlan.h', 'src/core/Application.cpp', 'src/game/SharedTaiwanNativeCharacterListSource.h', 'src/game/SharedTaiwanNativeCharacterListSource.cpp']
WRITTEN=GAME+[DOC,'tools/reconstruction/tw_native_entry_offer_source_delivery.py','tools/reconstruction/dual_client_route_catalog.py']
BOOKS=['docs/PACKET_CONNECTION_GOAL_20261006.md',(BASE/'packet-route-ledger.json').relative_to(ROOT).as_posix()]
PINS={'tw-native-selected-entry-source-01':'e45de665ad1aac2d3344b77c8308cf07341d53ffd651aa6ae771da55d8fb363b','endpoint-catalog220':'1fb4da391c10295b2eed95522d9b1d00d29abc3814e2cde162b1476d8e63988f'}
REMAINING=['Actual complete40 TW entry issuer now reaches the exact shared writer and pre-read entry Prepare. Supply actual complete opaque/resource/status producer and true issuer policy; geometry or a raw blob alone is not native authority.', 'Complete once-per-Issued admission ownership, cross-G replay/parallel rights, lifecycle and post-return queue/publication consistency. Exact selection invalidation now fences caught Entry reentry before writer COMMIT; it is not admission CAS.', 'Wire explicitly qualified Main and all remaining TW authoritative world/item/quest/battle/skills/monster/party/guild/town routes with their native replies. Preserve CN/web and legacy/frozen behavior.', 'Finish complete TW directional/state/variant/deferred inventory; denominator and completion percentage remain null. No Phase1 build/tests/native/codec/runtime/DB/SQL/migration/deploy. TW actual100 before stop.']

def reports():return [BASE/'packet-progress-latest.json',BASE/'packet-progress-latest.md',BASE/'round-reports'/(ROUND+'.json'),BASE/'round-reports'/(ROUND+'.md')]
def before():
 raw=(OUT/'before-manifest.json').read_bytes()
 if sha(raw)!='16e0f3f2f993f53b6b732a7ad924aca52c5774e7473ed707ed7abdf7eb224bd7':raise RuntimeError('Actual221 before drift')
 rows=json.loads(raw)
 if len(rows)!=1517:raise RuntimeError('Full1517 before required')
 return rows,{r['path']:matches(OUT/r['snapshot'],r) for r in rows}
def prior():
 count=0
 for n,pin in PINS.items():
  raw=(BASE/n/'manifest.json').read_bytes()
  if sha(raw)!=pin or raw!=(OUT/'retained-prior'/n/'manifest.json').read_bytes():raise RuntimeError('Prior220 seal drift')
  for r in json.loads(raw)['files']:matches(BASE/n/r['path'],r);count+=1
 if count!=1157:raise RuntimeError('Full1157 prior220 members required')
def protected(rows,old):
 excluded=set(WRITTEN+BOOKS)|{p.relative_to(ROOT).as_posix() for p in reports()[:2]}
 guarded=[r for r in rows if r['path'] not in excluded]
 for r in guarded:
  if (ROOT/r['path']).read_bytes()!=old[r['path']]:raise RuntimeError('Protected source drift: '+r['path'])
 for r in rows:
  if r['path'].startswith('src/') and r['path'] not in GAME and (ROOT/r['path']).read_bytes()!=old[r['path']]:raise RuntimeError('Unassigned CPP drift')
 return guarded
def originals(old):
 initial=read(OUT/'root-source-initial/origins.json')+read(OUT/'root-source-initial-supplemental/origins.json');candidate=read(OUT/'root-source-candidate/origins.json');final=read(OUT/'root-source-final/origins.json')
 if len(initial)!=8 or len(candidate)!=10 or len(final)!=10:raise RuntimeError('Full initial8/candidate10/final10 required')
 if {r['path'] for r in candidate}!=set(GAME) or {r['path'] for r in final}!=set(GAME):raise RuntimeError('Exact assigned10 CPP required')
 if {r['path'] for r in initial}!={p for p in GAME if p in old}:raise RuntimeError('Exact initial8 source set required')
 for r in initial:
  if matches(OUT/r['copy'],r)!=old[r['path']]:raise RuntimeError('Initial-before epoch mismatch')
 for r in candidate:matches(OUT/r['copy'],r)
 for r in final:
  if matches(ROOT/r['path'],r)!=matches(OUT/r['copy'],r):raise RuntimeError('Final CPP epoch mismatch')
 r=read(OUT/'retained-accounting-source220.json')
 if matches(OUT/r['copy'],r)!=matches(ROOT/r['path'],r):raise RuntimeError('Retained complete prior accounting source differs')
 if read(OUT/'policy/goal-before221.json')['goal']['status']!='active':raise RuntimeError('Actual active goal snapshot required')
def absolute(value):
 p=Path(value);return p if p.is_absolute() else ROOT/p
def agents(old):
 pins=read(OUT/'sealed-agent-pins.json');deliveries=[];paths=set();epochs=[]
 names=['tw-entry-offer-native','tw-entry-offer-review']
 if set(pins)!=set(names):raise RuntimeError('Two actual221 bounded deliveries required')
 for name in names:
  folder=OUT/'agents'/name;raw=(folder/'seal.json').read_bytes()
  if sha(raw)!=pins[name]:raise RuntimeError('Agent221 seal drift')
  seal=json.loads(raw);members=seal.get('files',seal.get('members'))
  if not isinstance(members,list):raise RuntimeError('Full agent inventory required')
  for r in members:matches(folder/r['path'],r)
  if {r['path'] for r in inventory(folder)}!={r['path'] for r in members}|{'seal.json'}:raise RuntimeError('Full221 agent member drift')
  current=read(folder/'current-source-origins.json')
  for r in current:
   p=absolute(r['path']);rel=p.relative_to(ROOT).as_posix()
   if matches(p,r)!=matches(folder/r['copy'],r):raise RuntimeError('Actual221 current epoch drift: '+rel)
   artifact_tool=p in [folder/'review_account.py',folder/'static_capture.py']
   if (rel.startswith('artifacts/') and not artifact_tool) or rel in BOOKS:raise RuntimeError('Receipt is not source original')
   if not artifact_tool:paths.add(rel)
  for r in read(folder/'native-input-references.json') if (folder/'native-input-references.json').exists() else []:
   if r.get('copy'):
    if matches(absolute(r['path']),r)!=matches(folder/r['copy'],r):raise RuntimeError('Complete native input differs')
   else:matches(absolute(r['path']),r)
  for name_ref in ['prior-whole-inplace-references.json','prior220-whole-inplace-references.json','retained-references.json']:
   if (folder/name_ref).exists():
    for r in read(folder/name_ref):matches(absolute(r['path']),r)
  for r in read(folder/'original-inputs.json'):
   p=absolute(r['path']);rel=p.relative_to(ROOT).as_posix();raw=matches(folder/r['copy'],r)
   if name=='tw-entry-offer-review':
    if rel not in old or raw!=old[rel]:raise RuntimeError('Actual initial221 epoch differs')
   elif raw!=p.read_bytes() and (rel not in old or old[rel]!=raw):raise RuntimeError('Actual native original epoch differs')
  for name_ref in ['final-original-inputs.json','final-context-origins.json']:
   if (folder/name_ref).exists():
    for r in read(folder/name_ref):
     p=absolute(r['path']);rel=p.relative_to(ROOT).as_posix()
     if matches(p,r)!=matches(folder/r['copy'],r):raise RuntimeError('Actual final221 differs')
     if not rel.startswith('artifacts/'):paths.add(rel)
  for before_name in ['before-source-origins.json','before-supplemental-source-origins.json']:
   if not (folder/before_name).exists():continue
   for r in read(folder/before_name):
    rel=absolute(r['path']).relative_to(ROOT).as_posix()
    if rel not in old or matches(folder/r['copy'],r)!=old[rel]:raise RuntimeError('Before epoch drift')
  findings=read(folder/'findings.json')
  deliveries.append(dict(agent=name,seal_sha256=sha((folder/'seal.json').read_bytes()),findings=findings,current_source_origins=current,files=inventory(folder)))
 return deliveries,paths,epochs

def account():
 if (OUT/'findings.json').exists():raise RuntimeError('Fresh221 account only')
 rows,old=before();prior();guarded=protected(rows,old);originals(old);reviews,paths,epochs=agents(old)
 cap=read(OUT/'policy/capacity-before-final-account.json')
 if cap['unreadable_count'] or not cap['under_limit']:raise RuntimeError('WholeGod2 standard capacity required')
 fullcap=read(OUT/'policy/capacity-full-before-final-account.json')
 if fullcap['unreadable_count'] or fullcap['cycles'] or not fullcap['under_limit']:raise RuntimeError('WholeGod2 full recursive alias scope capacity required')
 added=[p for p in GAME if p not in old];changed=[p for p in GAME if p in old and (ROOT/p).read_bytes()!=old[p]]
 if len(added)!=2 or len(changed)!=8:raise RuntimeError('Actual2 new and8 changed CPP required')
 ledger=read(ROOT/BOOKS[1]);previous=json.loads(old[BOOKS[1]])
 if ledger['dual_client_source_segments']!=previous['dual_client_source_segments'] or len(ledger['dual_client_source_segments'])!=210:raise RuntimeError('Historical210 drift')
 paths|=set(WRITTEN)|{'CMakeLists.txt'}
 facts=dict(round=ROUND,research_only=False,previous_goal_turn_classification='progress',completed_parallel_agents=2,new_Cplusplus_source_files_added=2,
  existing_Cplusplus_source_files_modified=8,new_source_segments=1,source_segments=211,new_packet_values=0,new_source_phase_bindings=0,
  new_complete_bidirectional_routes=0,whole_game_completion_percent=None,whole_game_denominator=None,tw_completion_percent=None,tw_denominator=None,
  source_paths=sorted(paths),new_bounded_native_bytes=0,retained_native_caller_bytes=2308,retained_native_caller_spans=8,
  actual_complete40_entry_offer_required=True,actual_same_object_Application_entry_writer_reader=True,
  actual_Entry_only_Prepare=True,actual_Native_Current_prepare=False,actual_native_Selected_lineage_required=True,
  actual_parent_full_roots_position_map_Selected_Current=True,actual_staged_next_not_old_entry_tuple_Current=True,
  actual_existing_writer_fulltuple_CAS_consumed=True,actual_expected_old_root_position_allowed=True,
  actual_exact_selection_invalidation_before_commit=True,actual_failed_prepare_no_old_material_fallback=True,
  actual_post_commit_provider_reload_retry=False,actual_native_wire_opaque_rewritten=False,
  actual_complete2A_producer_policy_supplied=False,actual_admission_CAS_replay_parallelG_complete=False,
  actual_post_return_queue_atomicity=False,actual_Main_factory_selected=False,formal_application_hosted=False,
  external_full_book_originals_retained=True,
  source_conclusion='Actual complete40 TW2A snapshot plus mandatory true issuer -> same-object Application world-entry writer/reader -> Entry-only Prepare with exact Selected/full common roots/position/map/parent reentry Current -> existing expected-fulltuple CAS Prepared/BeforeWrite/BeforeCommit observing staged-next -> fresh NativeSource read and Current -> full original frame. Application caught Entry reentry revokes only exact Selected registry slot through Host relay, so subsequent parent Current rejects before COMMIT even between List Guards. No candidate/fake opaque bytes, old-material fallback, invented wire/key/TTL, post-COMMIT retry, admission CAS, ACK or complete gameplay claim.',
  remaining=REMAINING,source_epoch_reconciliation=epochs,owner_TW_first=True,prior_five_round_stop_revoked=True,owner_requested_stop_after_round=None,
  owner_requested_pause_at_round_end=False,goal_status_at_source_account='active',build_run=False,tests_run=False,native_execution=False,runtime_run=False,codec_execution=False,database_access=False,SQL_run=False,deployed=False)
 dump(OUT/'parallel-agent-deliveries.json',reviews);dump(OUT/'source-epoch-reconciliation.json',epochs);dump(OUT/'findings.json',facts)
 ledger['tw_native_entry_offer_source221']=facts
 ledger['dual_client_source_segments'].append(dict(name=OUT.name,round=ROUND,version_scope='TW-native-actual-full-entry-offer-same-writer-Prepare-exact-selection-invalidation',status=facts['source_conclusion'],source_paths=sorted(paths),native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,tw_source_owner_chains_added=0,formal_application_hosted=False,complete_gameplay_routes_added=0,evidence=OUT.relative_to(ROOT).as_posix(),remaining=REMAINING))
 plan=ledger['dual_client_execution_plan'];plan.update(latest_work_round=ROUND,owner_requested_stop_after_work_round=None,owner_requested_stop_after_round_number=None,continuation_requires_owner_resume=False,owner_TW_first=True,prior_five_round_stop_revoked=True,owner_stop_condition='Owner resumed20261010: TW actual complete source routes100% before stop',next_source_frontier=REMAINING[0])
 (ROOT/BOOKS[1]).write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 with (ROOT/BOOKS[0]).open('ab') as handle:handle.write(('\n\n## 第221輪：TW完整入場issuer與共用寫入接線\n\n'+(ROOT/DOC).read_text(encoding='utf8')+'\n').encode())
 origins=[]
 for i,p in enumerate(sorted(paths|set(BOOKS))):
  raw=(ROOT/p).read_bytes();copy=f'source/current/f{i:03d}'+Path(p).suffix
  if p in BOOKS:copy=str(Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261010/tw-native-entry-offer-source-01')/(f'f{i:03d}'+Path(p).suffix))
  save(OUT/copy,raw)
  origins.append(dict(path=p,copy=copy,bytes=len(raw),sha256=sha(raw),changed_this_round=p not in old or old[p]!=raw))
  if p in old and raw!=old[p]:
   diff=''.join(difflib.unified_diff(old[p].decode('utf-8-sig').splitlines(True),raw.decode('utf-8-sig').splitlines(True),fromfile='before/'+p,tofile='final/'+p))
   if diff:save(OUT/'diff'/f'd{i:03d}.diff',diff.encode())
 dump(OUT/'source/source-origins.json',origins)
 print(json.dumps(dict(protected_files=len(guarded),source_files=len(paths),source_segments=211,new_CPP=2,modified_CPP=8,new_complete_routes=0,goal_status='active')))
def enrich():
 for p in reports():save(OUT/'reports/raw'/(p.parent.name+'-'+p.name),p.read_bytes())
 receipt=dict(new_CPP=2,modified_CPP=8,source_segments=211,new_source_segments=1,new_complete_bidirectional_routes=0,whole_game_percent=None,tw_percent=None,current_catalog_source_files=len(read(CAT/'source-file-manifest.json')),owner_requested_pause_at_round_end=False)
 for p in [reports()[0],reports()[2]]:
  v=read(p);v['tw_native_entry_offer_source221']=read(OUT/'findings.json');v['parallel_agent_deliveries']=read(OUT/'parallel-agent-deliveries.json');v['current_round_source_delta']=receipt
  p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 for p in [reports()[1],reports()[3]]:p.write_text((ROOT/DOC).read_text(encoding='utf8')+'\n\nStatic accounting: '+json.dumps(receipt)+'\n',encoding='utf8')
 dump(OUT/'reports/enrichment-receipt.json',receipt);print(json.dumps(receipt))
def seal():
 if (OUT/'manifest.json').exists() or (CAT/'manifest.json').exists():raise RuntimeError('Fresh221 seals required')
 rows,old=before();prior();guarded=protected(rows,old);originals(old);reviews,paths,epochs=agents(old)
 if reviews!=read(OUT/'parallel-agent-deliveries.json') or epochs!=read(OUT/'source-epoch-reconciliation.json'):raise RuntimeError('Agent/epoch drift')
 for r in read(OUT/'source/source-origins.json'):
  if matches(ROOT/r['path'],r)!=matches(OUT/r['copy'],r):raise RuntimeError('Root final source drift')
 ledger=read(ROOT/BOOKS[1])
 if ledger['dual_client_source_segments'][:210]!=json.loads(old[BOOKS[1]])['dual_client_source_segments'] or len(ledger['dual_client_source_segments'])!=211:raise RuntimeError('Historical210/new211 drift')
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
 rm=dict(round=ROUND,**flags,before_files=len(rows),protected_files=len(guarded),source_segments=211,new_source_segments=1,new_CPP=2,modified_CPP=8,new_complete_bidirectional_routes=0,whole_game_percent=None,tw_percent=None,owner_requested_stop_after_round=None,catalog_manifest_sha256=sha((CAT/'manifest.json').read_bytes()),files=inventory(OUT));dump(OUT/'manifest.json',rm)
 print(json.dumps(dict(root_members=len(rm['files']),catalog_members=len(cm['files']),root_sha256=sha((OUT/'manifest.json').read_bytes()),catalog_sha256=sha((CAT/'manifest.json').read_bytes()))))
if __name__=='__main__':
 if len(sys.argv)!=2 or sys.argv[1] not in ['account','enrich','seal']:raise RuntimeError('account/enrich/seal required')
 globals()[sys.argv[1]]()
