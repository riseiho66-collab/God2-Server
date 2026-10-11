"""Round219 immutable static file/source accounting; never executes game/SQL."""
from pathlib import Path
import json,sys,difflib
from .parallel_game_connection_frontier_delivery import ROOT,sha,read,save,dump,matches,inventory

BASE=ROOT/'artifacts/integration/packet-connections-20261006'
OUT=BASE/'tw-native-character-offer-source-01';CAT=BASE/'endpoint-catalog219'
ROUND='20261010-tw-native-character-offer-source'
DOC='docs/research/tw-native-character-offer-source-20261010.md'
GAME=['src/game/SharedTaiwanNativeCharacterOfferSource.h', 'src/game/SharedTaiwanNativeCharacterOfferSource.cpp', 'src/game/SharedTaiwanNativeCharacterListSource.h', 'src/game/SharedTaiwanNativeCharacterListSource.cpp', 'src/core/SharedTaiwanNativeWorldHostPlan.h', 'src/core/SharedTaiwanNativeWorldHostPlan.cpp', 'src/core/SharedWorldHostPlan.h', 'src/core/Application.cpp']
WRITTEN=GAME+[DOC,'tools/reconstruction/tw_native_character_offer_source_delivery.py','tools/reconstruction/dual_client_route_catalog.py']
BOOKS=['docs/PACKET_CONNECTION_GOAL_20261006.md',(BASE/'packet-route-ledger.json').relative_to(ROOT).as_posix()]
PINS={'tw-native-configured-table-source-01':'eeee71a320b5b81953ee93019dae5cd8327a196a7eeae2277c8c56d808de711d','endpoint-catalog218':'d3b113057f5326d2e6d5b0b4809e2e472d1f5547691764c6ff601417d035eb2c'}
REMAINING=['Actual full TW75 offer source is now callable by List through the same Application writer and reader. Supply concrete issuer/visibility/route/resource/revision policy; do not use experimental candidate or synthesize opaque bytes/order/token.', 'Actual native selection still returns commonID without a typed entry admission ticket; one-time CAS/replay/parallel G and full2A/scene/5D/Main remain OPEN. No invented TW check_key/TTL or constant admission tuple.', 'Preserve actual configuration/startup/cache/source epoch and G rights, postcreate/localbacking/clampedtoken4..7/fallback/larger-table variants; current source readbacks are not a client ACK or wire atomicity.', 'Complete directional/state/variant/deferred TW denominator, remaining gameplay, numeric64 and stack99; retain CN/web/common/frozen; no Phase1 execution/tests/DB/SQL/deploy. TW100 before stop.']

def reports():return [BASE/'packet-progress-latest.json',BASE/'packet-progress-latest.md',BASE/'round-reports'/(ROUND+'.json'),BASE/'round-reports'/(ROUND+'.md')]
def before():
 raw=(OUT/'before-manifest.json').read_bytes()
 if sha(raw)!='80915f77e2e44082b1b7b71f7be2a4954248e1bef1e27a35a096bc5cfdfec57b':raise RuntimeError('Actual219 before drift')
 rows=json.loads(raw)
 if len(rows)!=1511:raise RuntimeError('Full1511 before required')
 return rows,{r['path']:matches(OUT/r['snapshot'],r) for r in rows}
def prior():
 count=0
 for n,pin in PINS.items():
  raw=(BASE/n/'manifest.json').read_bytes()
  if sha(raw)!=pin or raw!=(OUT/'retained-prior'/n/'manifest.json').read_bytes():raise RuntimeError('Prior218 seal drift')
  for r in json.loads(raw)['files']:matches(BASE/n/r['path'],r);count+=1
 if count!=2592:raise RuntimeError('Full2592 prior218 members required')
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
 if len(initial)!=6 or len(candidate)!=8 or len(final)!=8:raise RuntimeError('Full initial6/candidate8/final8 required')
 if {r['path'] for r in candidate}!=set(GAME) or {r['path'] for r in final}!=set(GAME):raise RuntimeError('Exact assigned8 CPP required')
 if {r['path'] for r in initial}!={p for p in GAME if p in old}:raise RuntimeError('Exact initial6 source set required')
 for r in initial:
  if matches(OUT/r['copy'],r)!=old[r['path']]:raise RuntimeError('Initial-before epoch mismatch')
 for r in candidate:matches(OUT/r['copy'],r)
 for r in final:
  if matches(ROOT/r['path'],r)!=matches(OUT/r['copy'],r):raise RuntimeError('Final CPP epoch mismatch')
 r=read(OUT/'retained-accounting-source218.json')
 if matches(OUT/r['copy'],r)!=matches(ROOT/r['path'],r):raise RuntimeError('Retained complete prior accounting source differs')
 if read(OUT/'policy/goal-before219.json')['goal']['status']!='active':raise RuntimeError('Actual active goal snapshot required')
def absolute(value):
 p=Path(value);return p if p.is_absolute() else ROOT/p
def agents(old):
 pins=read(OUT/'sealed-agent-pins.json');deliveries=[];paths=set();epochs=[]
 names=['tw-character-offer-native','tw-character-offer-review']
 if set(pins)!=set(names):raise RuntimeError('Two actual219 bounded deliveries required')
 for name in names:
  folder=OUT/'agents'/name;raw=(folder/'seal.json').read_bytes()
  if sha(raw)!=pins[name]:raise RuntimeError('Agent219 seal drift')
  members=json.loads(raw).get('files',json.loads(raw).get('members'))
  if not isinstance(members,list):raise RuntimeError('Full agent member inventory required')
  for r in members:matches(folder/r['path'],r)
  if {r['path'] for r in inventory(folder)}!={r['path'] for r in members}|{'seal.json'}:raise RuntimeError('Full219 member drift')
  current=read(folder/'current-source-origins.json')
  for r in current:
   p=absolute(r['path']);rel=p.relative_to(ROOT).as_posix()
   retained=matches(folder/r['copy'],r)
   if p.read_bytes()!=retained:
    if name!='tw-character-offer-native' or rel not in old or old[rel]!=retained:raise RuntimeError('Actual219 source epoch drift: '+rel)
    epochs.append(dict(agent=name,path=rel,retained_epoch='actual219-before-parent-edits',retained_sha256=sha(retained),current_sha256=sha(p.read_bytes()),root_current_original_retained_separately=True))
   artifact_tool=p in [folder/'review_account.py',folder/'static_capture.py']
   if (rel.startswith('artifacts/') and not artifact_tool) or rel in BOOKS:raise RuntimeError('Receipt is not source original')
   if not artifact_tool:paths.add(rel)
  for r in read(folder/'native-input-references.json') if (folder/'native-input-references.json').exists() else []:
   original=matches(absolute(r['path']),r)
   if r.get('copy') and original!=matches(folder/r['copy'],r):raise RuntimeError('Native complete retained source differs')
  for references in ['prior-whole-inplace-references.json','retained-references.json']:
   if (folder/references).exists():
    for r in read(folder/references):matches(absolute(r['path']),r)
  for r in read(folder/'original-inputs.json'):
   p=absolute(r['path']);rel=p.relative_to(ROOT).as_posix();raw=matches(folder/r['copy'],r)
   if name=='tw-character-offer-review':
    if rel not in old or raw!=old[rel]:raise RuntimeError('Actual initial219 epoch differs')
   elif p.read_bytes()!=raw and (rel not in old or old[rel]!=raw):raise RuntimeError('Retained219 native original epoch drift')
  if name=='tw-character-offer-review':
   for r in read(folder/'final-original-inputs.json'):
    if matches(absolute(r['path']),r)!=matches(folder/r['copy'],r):raise RuntimeError('Actual final219 differs')
  if (folder/'actual-read-context-origins.json').exists():
   for r in read(folder/'actual-read-context-origins.json'):
    rel=absolute(r['path']).relative_to(ROOT).as_posix()
    if rel not in old or matches(folder/r['copy'],r)!=old[rel]:raise RuntimeError('Historical actual context epoch mismatch')
  deliveries.append(dict(agent=name,seal_sha256=sha((folder/'seal.json').read_bytes()),findings=read(folder/'findings.json'),current_source_origins=current,files=inventory(folder)))
 return deliveries,paths,epochs
def account():
 if (OUT/'findings.json').exists():raise RuntimeError('Fresh219 account only')
 rows,old=before();prior();guarded=protected(rows,old);originals(old);reviews,paths,epochs=agents(old)
 cap=read(OUT/'policy/capacity-before-final-account.json')
 if cap['unreadable_count'] or not cap['under_limit']:raise RuntimeError('WholeGod2 capacity required')
 added=[p for p in GAME if p not in old];changed=[p for p in GAME if p in old and (ROOT/p).read_bytes()!=old[p]]
 if len(added)!=2 or len(changed)!=6:raise RuntimeError('Actual2 new and6 changed CPP required')
 ledger=read(ROOT/BOOKS[1]);previous=json.loads(old[BOOKS[1]])
 if ledger['dual_client_source_segments']!=previous['dual_client_source_segments'] or len(ledger['dual_client_source_segments'])!=208:raise RuntimeError('Historical208 drift')
 paths|=set(WRITTEN)|{'CMakeLists.txt'}
 facts=dict(round=ROUND,research_only=False,previous_goal_turn_classification='progress',completed_parallel_agents=2,new_Cplusplus_source_files_added=2,
  existing_Cplusplus_source_files_modified=6,new_source_segments=1,source_segments=209,new_packet_values=0,new_source_phase_bindings=0,
  new_complete_bidirectional_routes=0,whole_game_completion_percent=None,whole_game_denominator=None,tw_completion_percent=None,tw_denominator=None,
  source_paths=sorted(paths),new_bounded_native_bytes=0,retained_native_caller_bytes=298,retained_native_caller_instructions=106,retained_native_caller_spans=4,retained_native_data_bytes=0,
  actual_full75_ordered_issuer_required=True,actual_original_name_only_CP950_qualification=True,actual_same_object_Application_writer_reader=True,
  actual_List_only_prepare=True,Select_Current_write=False,actual_parent_reentry_guard_before_commit=True,actual_staged_next_not_old_tuple_Current=True,
  actual_shared_writer_fulltuple_CAS_consumed=True,actual_failed_prepare_never_old_list_fallback=True,actual_post_commit_retry=False,
  native_appearance_serializer_proven=False,actual_concrete_issuer_policy_supplied=False,actual_selection_to_entry_typed_admission_complete=False,
  actual_admission_CAS_replay_parallelG_complete=False,actual_Main_factory_selected=False,formal_application_hosted=False,
  source_conclusion='Actual native75 offer/ordered commonIDs/revision/origin and mandatory issuer -> strict common-root ownership and original-name CP950 qualification -> actual same-object Application summary writer/reader -> List-only Prepare with independent parent session/roots/Target/reentry guard -> existing exact expected-fulltuple CAS and staged-next Prepared/BeforeWrite/BeforeCommit -> fresh committed list observation -> existing guarded actual socket write/issued Handoff. No Select/Current writes, candidate zeros, native slot inference, key/TTL invention or post-COMMIT provider retry. Concrete issuer and selection-to-full2A/admission/Main/gameplay remain OPEN.',
  remaining=REMAINING,source_epoch_reconciliation=epochs,owner_TW_first=True,prior_five_round_stop_revoked=True,owner_requested_stop_after_round=None,
  owner_requested_pause_at_round_end=False,goal_status_at_source_account='active',build_run=False,tests_run=False,native_execution=False,runtime_run=False,codec_execution=False,database_access=False,SQL_run=False,deployed=False)
 dump(OUT/'parallel-agent-deliveries.json',reviews);dump(OUT/'source-epoch-reconciliation.json',epochs);dump(OUT/'findings.json',facts)
 ledger['tw_native_character_offer_source219']=facts
 ledger['dual_client_source_segments'].append(dict(name=OUT.name,round=ROUND,version_scope='TW-native-actual-character-offer-List-only-shared-writer-Context',status=facts['source_conclusion'],source_paths=sorted(paths),native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,tw_source_owner_chains_added=0,formal_application_hosted=False,complete_gameplay_routes_added=0,evidence=OUT.relative_to(ROOT).as_posix(),remaining=REMAINING))
 plan=ledger['dual_client_execution_plan'];plan.update(latest_work_round=ROUND,owner_requested_stop_after_work_round=None,owner_requested_stop_after_round_number=None,continuation_requires_owner_resume=False,owner_TW_first=True,prior_five_round_stop_revoked=True,owner_stop_condition='Owner resumed20261010: TW actual complete source routes100% before stop',next_source_frontier=REMAINING[0])
 (ROOT/BOOKS[1]).write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 with (ROOT/BOOKS[0]).open('ab') as handle:handle.write(('\n\n## 第219輪：TW角色清單實際issuer與共用寫入接線\n\n'+(ROOT/DOC).read_text(encoding='utf8')+'\n').encode())
 origins=[]
 for i,p in enumerate(sorted(paths|set(BOOKS))):
  raw=(ROOT/p).read_bytes();copy=f'source/current/f{i:03d}'+Path(p).suffix;save(OUT/copy,raw)
  origins.append(dict(path=p,copy=copy,bytes=len(raw),sha256=sha(raw),changed_this_round=p not in old or old[p]!=raw))
  if p in old and raw!=old[p]:
   diff=''.join(difflib.unified_diff(old[p].decode('utf-8-sig').splitlines(True),raw.decode('utf-8-sig').splitlines(True),fromfile='before/'+p,tofile='final/'+p))
   if diff:save(OUT/'diff'/f'd{i:03d}.diff',diff.encode())
 dump(OUT/'source/source-origins.json',origins)
 print(json.dumps(dict(protected_files=len(guarded),source_files=len(paths),source_segments=209,new_CPP=2,modified_CPP=6,new_complete_routes=0,goal_status='active')))
def enrich():
 for p in reports():save(OUT/'reports/raw'/(p.parent.name+'-'+p.name),p.read_bytes())
 receipt=dict(new_CPP=2,modified_CPP=6,source_segments=209,new_source_segments=1,new_complete_bidirectional_routes=0,whole_game_percent=None,tw_percent=None,current_catalog_source_files=len(read(CAT/'source-file-manifest.json')),owner_requested_pause_at_round_end=False)
 for p in [reports()[0],reports()[2]]:
  v=read(p);v['tw_native_character_offer_source219']=read(OUT/'findings.json');v['parallel_agent_deliveries']=read(OUT/'parallel-agent-deliveries.json');v['current_round_source_delta']=receipt
  p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 for p in [reports()[1],reports()[3]]:p.write_text((ROOT/DOC).read_text(encoding='utf8')+'\n\nStatic accounting: '+json.dumps(receipt)+'\n',encoding='utf8')
 dump(OUT/'reports/enrichment-receipt.json',receipt);print(json.dumps(receipt))
def seal():
 if (OUT/'manifest.json').exists() or (CAT/'manifest.json').exists():raise RuntimeError('Fresh219 seals required')
 rows,old=before();prior();guarded=protected(rows,old);originals(old);reviews,paths,epochs=agents(old)
 if reviews!=read(OUT/'parallel-agent-deliveries.json') or epochs!=read(OUT/'source-epoch-reconciliation.json'):raise RuntimeError('Agent/epoch drift')
 for r in read(OUT/'source/source-origins.json'):
  if matches(ROOT/r['path'],r)!=matches(OUT/r['copy'],r):raise RuntimeError('Root final source drift')
 ledger=read(ROOT/BOOKS[1])
 if ledger['dual_client_source_segments'][:208]!=json.loads(old[BOOKS[1]])['dual_client_source_segments'] or len(ledger['dual_client_source_segments'])!=209:raise RuntimeError('Historical208/new209 drift')
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
 rm=dict(round=ROUND,**flags,before_files=len(rows),protected_files=len(guarded),source_segments=209,new_source_segments=1,new_CPP=2,modified_CPP=6,new_complete_bidirectional_routes=0,whole_game_percent=None,tw_percent=None,owner_requested_stop_after_round=None,catalog_manifest_sha256=sha((CAT/'manifest.json').read_bytes()),files=inventory(OUT));dump(OUT/'manifest.json',rm)
 print(json.dumps(dict(root_members=len(rm['files']),catalog_members=len(cm['files']),root_sha256=sha((OUT/'manifest.json').read_bytes()),catalog_sha256=sha((CAT/'manifest.json').read_bytes()))))
if __name__=='__main__':
 if len(sys.argv)!=2 or sys.argv[1] not in ['account','enrich','seal']:raise RuntimeError('account/enrich/seal required')
 globals()[sys.argv[1]]()
