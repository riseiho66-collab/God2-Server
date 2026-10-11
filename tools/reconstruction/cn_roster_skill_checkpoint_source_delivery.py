"""Round207 static source accounting only; active source round; owner requests pause after207."""
from pathlib import Path
import json,sys,difflib
from .parallel_game_connection_frontier_delivery import ROOT,sha,read,save,dump,matches,inventory
BASE=ROOT/'artifacts/integration/packet-connections-20261006'
OUT=BASE/'cn-roster-skill-checkpoint-source-01';CAT=BASE/'endpoint-catalog207'
ROUND='20261009-cn-roster-skill-checkpoint-source'
DOC='docs/research/cn-roster-skill-checkpoint-source-20261009.md'
GAME=['src/cn/world/CnRosterSkillCheckpointSource.h','src/cn/world/CnRosterSkillCheckpointSource.cpp','src/cn/world/SharedSubjectRosterPublication.h','src/cn/world/SharedSubjectRosterPublication.cpp']
WRITTEN=GAME+[DOC,'tools/reconstruction/cn_roster_skill_checkpoint_source_delivery.py','tools/reconstruction/dual_client_route_catalog.py','tools/reconstruction/cn_roster_checkpoint207.py']
BOOKS=['docs/PACKET_CONNECTION_GOAL_20261006.md',(BASE/'packet-route-ledger.json').relative_to(ROOT).as_posix()]
PINS={'cn-primary-skill-update-source-01':'a2bffc90141264bbb151c4b2ce5445bfa14f281351ee8bb0e834565952d33860','endpoint-catalog206':'b92ffa55dd88ec3a406cff43ea5babbab2df99823e9a71ce80fed57eb7265355'}

def reports():return [BASE/'packet-progress-latest.json',BASE/'packet-progress-latest.md',BASE/'round-reports'/(ROUND+'.json'),BASE/'round-reports'/(ROUND+'.md')]

def before():
 b=(OUT/'before-manifest.json').read_bytes()
 if sha(b)!='53b26124fa3756812450820ded3632271cd3dce5bbd74f8d68d9c8b9891a3987':raise RuntimeError('Actual before207 drift')
 rows=json.loads(b)
 if len(rows)!=1462:raise RuntimeError('1462 actual before sources required')
 return rows,{r['path']:matches(OUT/r['snapshot'],r) for r in rows}

def prior():
 count=0
 for n,pin in PINS.items():
  b=(BASE/n/'manifest.json').read_bytes()
  if sha(b)!=pin or b!=(OUT/'retained-prior'/n/'manifest.json').read_bytes():raise RuntimeError('Pinned206 seal drift')
  for r in json.loads(b)['files']:matches(BASE/n/r['path'],r);count+=1
 if count!=2414:raise RuntimeError('Full2414 retained206 members required')

def protected(rows,old):
 excluded=set(WRITTEN+BOOKS)|{p.relative_to(ROOT).as_posix() for p in reports()[:2]}
 guarded=[r for r in rows if r['path'] not in excluded]
 for r in guarded:
  if (ROOT/r['path']).read_bytes()!=old[r['path']]:raise RuntimeError('Protected actual source drift: '+r['path'])
 for r in rows:
  if r['path'].startswith('src/') and r['path'] not in GAME and (ROOT/r['path']).read_bytes()!=old[r['path']]:raise RuntimeError('Unassigned source modified')
 return guarded

def original_copies():
 for r in read(OUT/'root-source-initial/origins.json'):matches(OUT/r['copy'],r)

 for r in read(OUT/'root-first-candidate/origins.json'):matches(OUT/r['copy'],r)
 r=read(OUT/'actual-accounting-input206.json');matches(OUT/r['copy'],r);matches(Path(r['path']),r)

def reviewer():
 pins=read(OUT/'sealed-agent-pins.json');deliveries=[];paths=set()
 if len(pins)!=2:raise RuntimeError('Two actual207 bounded deliveries required')
 rows,old=before()
 for name in ['roster-checkpoint-native','roster-checkpoint-source-review']:
  folder=OUT/'agents'/name;b=(folder/'seal.json').read_bytes()
  if sha(b)!=pins[name]:raise RuntimeError('Actual207 seal drift')
  seal=json.loads(b);members=seal.get('files',seal.get('members'))
  if not isinstance(members,list):raise RuntimeError('Complete seal member list required')
  for r in members:matches(folder/r['path'],r)
  if {r['path'] for r in inventory(folder)}!={r['path'] for r in members}|{'seal.json'}:raise RuntimeError('Full actual207 agent inventory drift')
  current=read(folder/'current-source-origins.json')
  for r in current:
   p=Path(r['path']);p=p if p.is_absolute() else ROOT/p;rel=p.relative_to(ROOT).as_posix()
   artifact_tool=p==folder/'review_account.py'
   if (rel.startswith('artifacts/') and not artifact_tool) or rel in BOOKS:raise RuntimeError('Mutable receipt cannot be source original')
   if matches(p,r)!=matches(folder/r['copy'],r):raise RuntimeError('Actual final207 source drift')
   if not artifact_tool:paths.add(rel)
  refs=read(folder/'native-input-references.json') if (folder/'native-input-references.json').exists() else []
  for r in refs:matches(Path(r['path']),r)
  if name=='roster-checkpoint-source-review':
   for r in read(folder/'original-inputs.json'):
    p=Path(r['path']);p=p if p.is_absolute() else ROOT/p;rel=p.relative_to(ROOT).as_posix()
    raw=matches(OUT/r['original'],r)
    if rel not in old or raw!=old[rel] or matches(folder/r['copy'],r)!=raw:raise RuntimeError('Full before207 source drift')
   for r in read(folder/'final-original-inputs.json'):
    p=Path(r['path']);p=p if p.is_absolute() else ROOT/p
    if matches(p,r)!=matches(folder/r['copy'],r):raise RuntimeError('Full final207 source drift')
  if name=='roster-checkpoint-native':
   for r in read(folder/'original-inputs.json'):
    if matches(Path(r['path']),r)!=matches(folder/r['copy'],r):raise RuntimeError('Actual native207 complete original drift')
   pe_rows=[r for r in refs if Path(r['path']).suffix.lower()=='.exe']
   if len(pe_rows)!=1:raise RuntimeError('One full pinned actual native PE required')
   pe=matches(Path(pe_rows[0]['path']),pe_rows[0])
   if pe_rows[0]['sha256']!='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8':raise RuntimeError('Pinned actual native image required')
   for r in read(folder/'native-spans.json'):
    raw=matches(folder/r['raw'],r);at=r['file_offset']
    if pe[at:at+len(raw)]!=raw:raise RuntimeError('Native bounded207 byte mismatch')
  deliveries.append(dict(agent=name,seal_sha256=sha(b),findings=read(folder/'findings.json'),current_source_origins=current,files=inventory(folder)))
 return deliveries,paths

def account():
 if (OUT/'findings.json').exists():raise RuntimeError('Fresh207 only')
 rows,old=before();prior();guarded=protected(rows,old);original_copies();reviews,paths=reviewer()
 cap=read(OUT/'policy/capacity-before-final-account.json')
 if cap['unreadable_count'] or not cap['under_limit']:raise RuntimeError('WholeGod2 capacity required')
 changed=[p for p in GAME if p in old and (ROOT/p).read_bytes()!=old[p]];new=[p for p in GAME if p not in old]
 if len(changed)!=2 or len(new)!=2:raise RuntimeError('Actual2 modified and2 new CPP required')
 paths|=set(WRITTEN)|{r['path'] for r in read(OUT/'root-source-initial/origins.json')}|{'CMakeLists.txt'}
 ledger=read(ROOT/BOOKS[1]);previous=json.loads(old[BOOKS[1]])
 if ledger['dual_client_source_segments']!=previous['dual_client_source_segments'] or len(ledger['dual_client_source_segments'])!=196:raise RuntimeError('Historical196 drift')
 facts=dict(round=ROUND,research_only=False,completed_parallel_agents=2,new_Cplusplus_source_files_added=2,existing_Cplusplus_source_files_modified=2,new_source_segments=1,source_segments=197,new_packet_values=0,new_source_phase_bindings=0,new_complete_bidirectional_routes=0,whole_game_completion_percent=None,whole_game_denominator=None,source_paths=sorted(paths),
  actual_CN_mixed_roster_skill_checkpoint_sources_added=1,new_bounded_native_bytes=0,retained_native_data_bytes=968,
  source_conclusion='Original mixed30/31/32/33/39/34/35 sequence -> explicit real before-image checkpoints covering each34/35 once without crossing non-skill records -> owned original data stages and exact common-store definition bytes/hash/offset -> actual additive native qualifier plus mandatory actual common post-commit qualifier in both held publication stages.',
  authority_scope='Prepared immutable actual checkpoint sources require a real event owner; not automatic client memory or proof the client processed records. Intervening resets/selection/rows/revisions and conditional unknown log/UI callback effects remain actual owner obligations. No Main issuer, common learned transaction, native mutation or complete gameplay route added.',
  source_notes=['30 writes inactive row before duplicate inline count-only return; negative30 selects only actual appended row.31 signextends ID and firstmatching active row;34/35 zeroextend ID and iterate ALLmatching rows.32/33/39 act on the current selection and have no subject ID.','Strongly own all records, aligned definitions and sources before any Current observer. Eachskill covered exactly once; no overlaps/missing/out-of-order/cross-nonSkill segments. Operational640-record source bound does not become native gameplay limit.','Actual checkpoints may split a contiguous skillrun but are never synthesized. Unknown non-skill effects and conditional inner callbacks are retained as unresolved owner obligations; no default/stale/future revision or adjacency equality is invented.','Exact native vs actual shared-store source/kind/id/fileoffset/hash/fullraw check preserves definition custody. Strong sources and immutable projection survive BeforeQueue and QueueAccepted with original framing/order.','Explicit opt-in requires extra native qualifier; mandatory original common qualifier remains. Unselected legacy branch rejects supplied checkpoints; missing sources cannot fall back for selected skill records. No issuer/default host activated.','Before existingPub2, complete actual firstcandidate4 and complete final4+dependencies are physically retained with distinct epochs. Prior206 missing firstcandidate receipts remain immutable historical limitations.','Local queue release/acceptance is not client processing/nativeACK. Actual common durable event and real per-sequence checkpoint supplier still absent.'],
  remaining=['Implement real common post-commit mixed-roster event and prepared immutable per-run checkpoint supplier with qualified interleaving, resets/selections and remaining log/UI callbacks; actual Main issuer remains OPEN.','Implement common learned/book custody/debit/save/durable event and WORLD-to-battle primary materializer; never claim skill-source comparison itself grants learning or battle eligibility.','Complete TW/CN/web whole-game bidirectional/state/variant/deferred routes and numeric64/stack99; comprehensive builds/tests/repair/release only after all sources connected.'],
  owner_explicit_resume=True,owner_five_round_start=203,owner_five_round_end=207,owner_requested_stop_after_round=207,owner_requested_pause_at_round_end=True,goal_status_at_source_account='active',pause_required_after_full_round=True,do_not_start_round208=True,build_run=False,tests_run=False,native_execution=False,runtime_run=False,codec_execution=False,database_access=False,SQL_run=False,deployed=False)

 dump(OUT/'parallel-agent-deliveries.json',reviews);dump(OUT/'findings.json',facts)
 ledger['native_roster_skill_checkpoint_source207']=facts
 ledger['dual_client_source_segments'].append(dict(name=OUT.name,round=ROUND,version_scope='CN-pinned-ordered-WORLD30-31-32-33-39-34-35-checkpoint-publication-source',status=facts['source_conclusion'],source_paths=sorted(paths),native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,tw_source_owner_chains_added=0,formal_application_hosted=False,complete_gameplay_routes_added=0,evidence=OUT.relative_to(ROOT).as_posix(),remaining=facts['remaining']))
 plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND;plan['owner_requested_stop_after_work_round']='round207';plan['owner_requested_stop_after_round_number']=207;plan['owner_five_round_start']=203;plan['owner_five_round_end']=207;plan['continuation_requires_owner_resume']=True;plan['next_source_frontier']=facts['remaining'][0]
 (ROOT/BOOKS[1]).write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 with (ROOT/BOOKS[0]).open('a',encoding='utf-8') as f:f.write('\n\n## 第207輪來源及五輪停止指示\n\n'+(ROOT/DOC).read_text(encoding='utf-8')+'\n本次由203算第1輪，本207為第5輪；本207完整封存交接完成後依使用者指示暫停目標並停止，不開始208。\n')

 origins=[]
 for i,n in enumerate(sorted(paths|set(BOOKS))):
  b=(ROOT/n).read_bytes();copy=f'source/current/f{i:03d}'+Path(n).suffix;save(OUT/copy,b)
  origins.append(dict(path=n,copy=copy,bytes=len(b),sha256=sha(b),changed_this_round=n not in old or old[n]!=b))
  if n in old and old[n]!=b:
   diff=''.join(difflib.unified_diff(old[n].decode('utf-8-sig').splitlines(True),b.decode('utf-8-sig').splitlines(True),fromfile='before/'+n,tofile='current/'+n))
   if diff:save(OUT/'diff'/f'd{i:03d}.diff',diff.encode())
 dump(OUT/'source/source-origins.json',origins)
 print(json.dumps(dict(protected_files=len(guarded),source_files=len(paths),source_segments=197,new_CPP=2,modified_CPP=2,new_complete_routes=0,stop_after_round=207)))

def enrich():
 for p in reports():save(OUT/'reports/raw'/(p.parent.name+'-'+p.name),p.read_bytes())
 receipt=dict(new_CPP=2,modified_CPP=2,source_segments=197,new_source_segments=1,new_complete_bidirectional_routes=0,whole_game_percent=None,current_catalog_source_files=len(read(CAT/'source-file-manifest.json')),owner_requested_pause_at_round_end=True)
 for p in [reports()[0],reports()[2]]:
  v=read(p);v['native_roster_skill_checkpoint_source207']=read(OUT/'findings.json');v['parallel_agent_deliveries']=read(OUT/'parallel-agent-deliveries.json');v['current_round_source_delta']=receipt;p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 for p in [reports()[1],reports()[3]]:p.write_text((ROOT/DOC).read_text(encoding='utf-8')+'\n\nStatic accounting: '+json.dumps(receipt)+'\n',encoding='utf-8')
 dump(OUT/'reports/enrichment-receipt.json',receipt);print(json.dumps(receipt))

def seal():
 if (OUT/'manifest.json').exists() or (CAT/'manifest.json').exists():raise RuntimeError('Fresh207 seals required')
 rows,old=before();prior();guarded=protected(rows,old);original_copies();reviews,paths=reviewer()
 if reviews!=read(OUT/'parallel-agent-deliveries.json'):raise RuntimeError('Reviewer delivery drift')
 for r in read(OUT/'source/source-origins.json'):
  if matches(ROOT/r['path'],r)!=matches(OUT/r['copy'],r):raise RuntimeError('Final current source drift')
 ledger=read(ROOT/BOOKS[1])
 if ledger['dual_client_source_segments'][:196]!=json.loads(old[BOOKS[1]])['dual_client_source_segments'] or len(ledger['dual_client_source_segments'])!=197:raise RuntimeError('Historical196/new197 drift')
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
 rm=dict(round=ROUND,**flags,before_files=len(rows),protected_files=len(guarded),source_segments=197,new_source_segments=1,new_CPP=2,modified_CPP=2,new_complete_bidirectional_routes=0,whole_game_percent=None,owner_requested_stop_after_round=207,catalog_manifest_sha256=sha((CAT/'manifest.json').read_bytes()),files=inventory(OUT));dump(OUT/'manifest.json',rm)
 print(json.dumps(dict(root_members=len(rm['files']),catalog_members=len(cm['files']),root_sha256=sha((OUT/'manifest.json').read_bytes()),catalog_sha256=sha((CAT/'manifest.json').read_bytes()))))

if __name__=='__main__':
 if len(sys.argv)!=2 or sys.argv[1] not in ['account','enrich','seal']:raise RuntimeError('account/enrich/seal required')
 globals()[sys.argv[1]]()
