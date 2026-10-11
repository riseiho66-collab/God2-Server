"""Round202 static source accounting only; owner-requested pause follows seal."""
from pathlib import Path
import json,sys,difflib
from .parallel_game_connection_frontier_delivery import ROOT,sha,read,save,dump,matches,inventory
BASE=ROOT/'artifacts/integration/packet-connections-20261006'
OUT=BASE/'cn-inline-role-publication-source-01';CAT=BASE/'endpoint-catalog202'
ROUND='20261009-cn-inline-role-publication-source'
DOC='docs/research/cn-inline-role-publication-source-20261009.md'
GAME=['src/cn/world/SharedInlineRoleCountersPublication.h','src/cn/world/SharedInlineRoleCountersPublication.cpp','src/cn/world/SharedWorldGameplay.h','src/cn/world/SharedWorldGameplay.cpp']
WRITTEN=GAME+[DOC,'tools/reconstruction/cn_inline_role_publication_source_delivery.py','tools/reconstruction/dual_client_route_catalog.py']
BOOKS=['docs/PACKET_CONNECTION_GOAL_20261006.md',(BASE/'packet-route-ledger.json').relative_to(ROOT).as_posix()]
PINS={'cn-native-shared-book-request-source-01':'133d1383668b1159ac4679f17a48031a3b86d3e9e60b437ac534d03ad89f49e9','endpoint-catalog201':'355da0428588a44173128efa9f437bbd45d2acf474f58fe5cb13fd3f99c3df71'}

def reports():return [BASE/'packet-progress-latest.json',BASE/'packet-progress-latest.md',BASE/'round-reports'/(ROUND+'.json'),BASE/'round-reports'/(ROUND+'.md')]

def before():
 b=(OUT/'before-manifest.json').read_bytes()
 if sha(b)!='bcc5a21043951b7c03334c36ca700b1f92e2eac5a5693dcd6a416a86e13deb96':raise RuntimeError('Actual before202 drift')
 rows=json.loads(b)
 if len(rows)!=1442:raise RuntimeError('1442 actual before sources required')
 return rows,{r['path']:matches(OUT/r['snapshot'],r) for r in rows}

def prior():
 count=0
 for n,pin in PINS.items():
  b=(BASE/n/'manifest.json').read_bytes()
  if sha(b)!=pin or b!=(OUT/'retained-prior'/n/'manifest.json').read_bytes():raise RuntimeError('Pinned201 seal drift')
  for r in json.loads(b)['files']:matches(BASE/n/r['path'],r);count+=1
 if count!=2510:raise RuntimeError('Full2510 retained201 members required')

def protected(rows,old):
 excluded=set(WRITTEN+BOOKS)|{p.relative_to(ROOT).as_posix() for p in reports()[:2]}
 guarded=[r for r in rows if r['path'] not in excluded]
 for r in guarded:
  if (ROOT/r['path']).read_bytes()!=old[r['path']]:raise RuntimeError('Protected actual source drift: '+r['path'])
 for r in rows:
  if r['path'].startswith('src/') and r['path'] not in GAME and (ROOT/r['path']).read_bytes()!=old[r['path']]:raise RuntimeError('Unassigned source modified')
 return guarded

def original_copies():
 before_rows,old=before()
 for r in read(OUT/'actual-inputs/origins.json'):
  raw=matches(OUT/r['copy'],r)
  if r['path'] not in old or raw!=old[r['path']]:raise RuntimeError('Actual original202 source drift')
 for r in read(OUT/'source-initial/origins.json'):matches(OUT/r['copy'],r)

def reviewer():
 folder=OUT/'agents/inline-role-source-review'
 b=(folder/'seal.json').read_bytes();seal=json.loads(b);members=seal.get('files',seal.get('members'))
 if sha(b)!='003e9a61811411ea669aeccb84d1f71cbaf9df519a11f0a499fd723e64ab955d':raise RuntimeError('Pinned final202 reviewer seal drift')
 if not isinstance(members,list):raise RuntimeError('Full reviewer member inventory required')
 for r in members:matches(folder/r['path'],r)
 if {r['path'] for r in inventory(folder)}!={r['path'] for r in members}|{'seal.json'}:raise RuntimeError('Reviewer inventory drift')
 current=read(folder/'current-source-origins.json');paths=set()
 for r in current:
  p=Path(r['path']);p=p if p.is_absolute() else ROOT/p
  rel=p.relative_to(ROOT).as_posix()
  artifact_tool=p==folder/'review_account.py'
  if (rel.startswith('artifacts/') and not artifact_tool) or rel in BOOKS:raise RuntimeError('Current source origins cannot be mutable receipts')
  if matches(p,r)!=matches(folder/r['copy'],r):raise RuntimeError('Full actual final reviewed-source drift')
  if not artifact_tool:paths.add(rel)
 for r in read(folder/'original-inputs.json'):
  if matches(Path(r['path']),r)!=matches(folder/r['copy'],r):raise RuntimeError('Full final original input drift')
 for r in read(folder/'initial-source-origins.json'):
  matches(folder/r['copy'],r)
 return dict(seal_sha256=sha(b),findings=read(folder/'findings.json'),current_source_origins=current,files=inventory(folder)),paths

def account():
 if (OUT/'findings.json').exists():raise RuntimeError('Fresh202 only')
 rows,old=before();prior();guarded=protected(rows,old);original_copies();review,paths=reviewer()
 cap=read(OUT/'policy/capacity-before-final-account.json')
 if cap['unreadable_count'] or not cap['under_limit']:raise RuntimeError('WholeGod2 capacity required')
 changed=[p for p in GAME if p in old and (ROOT/p).read_bytes()!=old[p]];new=[p for p in GAME if p not in old]
 if len(changed)!=2 or len(new)!=2:raise RuntimeError('Actual2 modified and2 new CPP required')
 paths|=set(WRITTEN)|{r['path'] for r in read(OUT/'actual-inputs/origins.json')}|{'CMakeLists.txt'}
 ledger=read(ROOT/BOOKS[1]);previous=json.loads(old[BOOKS[1]])
 if ledger['dual_client_source_segments']!=previous['dual_client_source_segments'] or len(ledger['dual_client_source_segments'])!=191:raise RuntimeError('Historical191 drift')
 facts=dict(round=ROUND,research_only=False,completed_parallel_agents=1,new_Cplusplus_source_files_added=2,existing_Cplusplus_source_files_modified=2,new_source_segments=1,source_segments=192,new_packet_values=0,new_source_phase_bindings=0,new_complete_bidirectional_routes=0,whole_game_completion_percent=None,whole_game_denominator=None,source_paths=sorted(paths),
  actual_CN_WORLD24_publication_sources_added=1,actual_concrete_common_issuer_Main_complete=False,
  source_conclusion='Owned original native WORLD24 records -> exact same ready CN connection/root/private registry Token -> explicit actual post-commit WorldOwner at BeforeQueue/BeforeRelease/AfterRelease -> original held publication queue. Same1C composition installs optional source and cleanup, without startup output or default issuer.',
  authority_scope='No actual common numeric mutation/save/durable event issuer, native stat semantics, C1F/C25 causal reply, Main activation or numeric64 completion. New complete routes zero.',
  source_notes=['Original17-byte records and raw unsigned DWORD order5C/64/60/68 retained; no actor/subject ID or guessed stat labels.','Mandatory event/revision nonzero and explicit output budgets are integration contracts, not recovered native numeric rules.','Actual common WorldOwner must qualify this ready recipient inline-role identity/profile/lifetime, event/save/durable replay/revision, values and order before releasing exact bytes.','Strong original connection and same private registry incarnation/root/position held throughout. No successor lookup/close, shared Token release or pending lifecycle writes to common state.','A delivered true callback is confirmed local release only. Existing transport masks accepted by closing before game delivery, so false or no receipt leaves release UNKNOWN and grants no replay permission. Legacy transport unchanged.','Receipt alternatives are allocated before release. Delivered true is retained after cancellation/late completion/throwing send even if AfterRelease current fails.','One nonreentrant stage ends before original asynchronous send. Exact source installed during real1C publication only, with own pending invalidation/release on gameplay termination.'],
  remaining=['Implement actual common post-commit inline-role event/save/durable replay issuer and recover raw DWORD semantics/recipient mapping before selecting a formal Main plan.','Trace actual initial native primary-skill population and world-to-battle list source; complete common owned book/skill mutation and qualified native replies.','Complete whole TW/CN/web bidirectional/state/variant/deferred sources and numeric64/stack99, then comprehensive testing/repair/release.'],
  owner_requested_stop_after_round=202,owner_requested_pause_at_round_end=True,goal_status_at_source_account='active',build_run=False,tests_run=False,native_execution=False,runtime_run=False,codec_execution=False,database_access=False,SQL_run=False,deployed=False)
 dump(OUT/'parallel-agent-deliveries.json',[review]);dump(OUT/'findings.json',facts)
 ledger['native_inline_role_publication_source202']=facts
 ledger['dual_client_source_segments'].append(dict(name=OUT.name,round=ROUND,version_scope='CN-pinned-native-WORLD24-committed-recipient-publication',status=facts['source_conclusion'],source_paths=sorted(paths),native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,tw_source_owner_chains_added=0,formal_application_hosted=False,complete_gameplay_routes_added=0,evidence=OUT.relative_to(ROOT).as_posix(),remaining=facts['remaining']))
 plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND;plan['owner_requested_stop_after_work_round']='round202';plan['owner_requested_stop_after_round_number']=202;plan['continuation_requires_owner_resume']=True;plan['next_source_frontier']=facts['remaining'][0]
 (ROOT/BOOKS[1]).write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 with (ROOT/BOOKS[0]).open('a',encoding='utf-8') as f:f.write('\n\n## 第202輪來源與使用者指定停止點\n\n'+(ROOT/DOC).read_text(encoding='utf-8')+'\n封存此輪後呼叫目標暫停；停止子代理，不開始第203輪，等待使用者續行。\n')
 origins=[]
 for i,n in enumerate(sorted(paths|set(BOOKS))):
  b=(ROOT/n).read_bytes();copy=f'source/current/f{i:03d}'+Path(n).suffix;save(OUT/copy,b)
  origins.append(dict(path=n,copy=copy,bytes=len(b),sha256=sha(b),changed_this_round=n not in old or old[n]!=b))
  if n in old and old[n]!=b:
   diff=''.join(difflib.unified_diff(old[n].decode('utf-8-sig').splitlines(True),b.decode('utf-8-sig').splitlines(True),fromfile='before/'+n,tofile='current/'+n))
   if diff:save(OUT/'diff'/f'd{i:03d}.diff',diff.encode())
 dump(OUT/'source/source-origins.json',origins)
 print(json.dumps(dict(protected_files=len(guarded),source_files=len(paths),source_segments=192,new_CPP=2,modified_CPP=2,new_complete_routes=0,stop_after_round=202)))

def enrich():
 for p in reports():save(OUT/'reports/raw'/(p.parent.name+'-'+p.name),p.read_bytes())
 receipt=dict(new_CPP=2,modified_CPP=2,source_segments=192,new_source_segments=1,new_complete_bidirectional_routes=0,whole_game_percent=None,current_catalog_source_files=len(read(CAT/'source-file-manifest.json')),owner_requested_pause_at_round_end=True)
 for p in [reports()[0],reports()[2]]:
  v=read(p);v['native_inline_role_publication_source202']=read(OUT/'findings.json');v['parallel_agent_deliveries']=read(OUT/'parallel-agent-deliveries.json');v['current_round_source_delta']=receipt;p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 for p in [reports()[1],reports()[3]]:p.write_text((ROOT/DOC).read_text(encoding='utf-8')+'\n\nStatic accounting: '+json.dumps(receipt)+'\n',encoding='utf-8')
 dump(OUT/'reports/enrichment-receipt.json',receipt);print(json.dumps(receipt))

def seal():
 if (OUT/'manifest.json').exists() or (CAT/'manifest.json').exists():raise RuntimeError('Fresh202 seals required')
 rows,old=before();prior();guarded=protected(rows,old);original_copies();review,paths=reviewer()
 if [review]!=read(OUT/'parallel-agent-deliveries.json'):raise RuntimeError('Reviewer delivery drift')
 for r in read(OUT/'source/source-origins.json'):
  if matches(ROOT/r['path'],r)!=matches(OUT/r['copy'],r):raise RuntimeError('Final current source drift')
 ledger=read(ROOT/BOOKS[1])
 if ledger['dual_client_source_segments'][:191]!=json.loads(old[BOOKS[1]])['dual_client_source_segments'] or len(ledger['dual_client_source_segments'])!=192:raise RuntimeError('Historical191/new192 drift')
 sources=read(CAT/'source-file-manifest.json')
 for n,r in sources.items():matches(ROOT/n,r)
 entries=[r for r in read(CAT/'input-manifest.json') if r['input']=='source-ledger']
 if len(entries)!=1 or matches(CAT/entries[0]['snapshot'],entries[0])!=(ROOT/BOOKS[1]).read_bytes():raise RuntimeError('Current catalog ledger drift')
 a,b,c,d=reports()
 if a.read_bytes()!=c.read_bytes() or b.read_bytes()!=d.read_bytes():raise RuntimeError('Final report mismatch')
 v=read(a)
 if v['round']!=ROUND or v['route_ledger_sha256']!=sha((ROOT/BOOKS[1]).read_bytes()) or v['dual_client_endpoint_catalog']['summary']!=read(CAT/'summary.json'):raise RuntimeError('Report/catalog drift')
 for k in ['whole_game_distinct_packet_count','whole_game_completed_route_count','whole_game_completion_percent']:
  if v['counts'][k] is not None:raise RuntimeError('False whole-game denominator')
 for p in reports():save(OUT/'reports/final'/(p.parent.name+'-'+p.name),p.read_bytes())
 flags=dict(sealed=True,method='STATIC_SOURCE_INTEGRATION_ONLY',build_run=False,tests_run=False,native_execution=False,runtime_run=False,database_access=False,deployed=False)
 cm=dict(round=CAT.name,**flags,current_source_files=len(sources),files=inventory(CAT));dump(CAT/'manifest.json',cm)
 rm=dict(round=ROUND,**flags,before_files=len(rows),protected_files=len(guarded),source_segments=192,new_source_segments=1,new_CPP=2,modified_CPP=2,new_complete_bidirectional_routes=0,whole_game_percent=None,owner_requested_pause_after_seal=True,catalog_manifest_sha256=sha((CAT/'manifest.json').read_bytes()),files=inventory(OUT));dump(OUT/'manifest.json',rm)
 print(json.dumps(dict(root_members=len(rm['files']),catalog_members=len(cm['files']),root_sha256=sha((OUT/'manifest.json').read_bytes()),catalog_sha256=sha((CAT/'manifest.json').read_bytes()))))

if __name__=='__main__':
 if len(sys.argv)!=2 or sys.argv[1] not in ['account','enrich','seal']:raise RuntimeError('account/enrich/seal required')
 globals()[sys.argv[1]]()
