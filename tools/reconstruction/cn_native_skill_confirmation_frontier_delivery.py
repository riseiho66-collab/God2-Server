"""Round199 immutable static acquisition evidence/accounting; no gameplay execution."""
from pathlib import Path
import json,sys,difflib
from .parallel_game_connection_frontier_delivery import ROOT,sha,read,save,dump,matches,inventory
BASE=ROOT/'artifacts/integration/packet-connections-20261006'
OUT=BASE/'cn-native-skill-confirmation-frontier-01'
CAT=BASE/'endpoint-catalog199'
ROUND='20261009-cn-native-skill-confirmation-frontier'
DOC='docs/research/cn-native-skill-confirmation-frontier-20261009.md'
BOOKS=['docs/PACKET_CONNECTION_GOAL_20261006.md',str((BASE/'packet-route-ledger.json').relative_to(ROOT).as_posix())]
GAME=['src/cn/protocol/CnSkillBookUse25.h','src/cn/world/SharedNativeSkillBookUseSource.h','src/cn/world/SharedNativeSkillBookUseSource.cpp','src/cn/assets/CnNativeSkillBookBindings.h','src/cn/assets/CnNativeSkillBookBindings.cpp','src/cn/world/SharedWorldGameplay.h','src/cn/world/SharedWorldGameplay.cpp']
WRITTEN=GAME+[DOC,'tools/reconstruction/cn_native_skill_confirmation_frontier_delivery.py','tools/reconstruction/cn_modal_confirmation199.py','tools/reconstruction/cn_learning_reply199.py','tools/reconstruction/dual_client_route_catalog.py']
AGENTS=['native-modal-confirmation','cn-learning-reply-frontier','shared-book-use-integration-frontier']
PINS={'cn-native-skill-acquisition-frontier-01':'d80cfab37de3953d82c07d8323c576622e88547c057874a1b27cd5f770ca478d','endpoint-catalog198':'f7ae701dcb2b65164a0fbdeba83c746471069d95add356cb979e5fa4f5f0b60b'}
AGENT_PINS=read(OUT/'sealed-agent-pins.json')

def reports():return [BASE/'packet-progress-latest.json',BASE/'packet-progress-latest.md',BASE/'round-reports'/(ROUND+'.json'),BASE/'round-reports'/(ROUND+'.md')]

def before():
 b=(OUT/'before-manifest.json').read_bytes()
 if sha(b)!='983a6fcb68088787bfb2a69cc6d4215784e5083f9ca82c918c2dd91fbdf1212c':raise RuntimeError('Original before198 drift')
 rows=json.loads(b)
 if len(rows)!=1419:raise RuntimeError('Before1419 required')
 return rows,{r['path']:matches(OUT/r['snapshot'],r) for r in rows}

def prior():
 total=0
 for n,pin in PINS.items():
  b=(BASE/n/'manifest.json').read_bytes()
  if sha(b)!=pin or b!=(OUT/'retained-prior'/n/'manifest.json').read_bytes():raise RuntimeError('Prior198 manifest drift')
  for r in json.loads(b)['files']:matches(BASE/n/r['path'],r);total+=1
 if total!=2464:raise RuntimeError('Full2464 prior members required')

def protected(rows,old):
 excluded=set(WRITTEN+BOOKS)|{p.relative_to(ROOT).as_posix() for p in reports()[:2]}
 guarded=[r for r in rows if r['path'] not in excluded]
 for r in guarded:
  if (ROOT/r['path']).read_bytes()!=old[r['path']]:raise RuntimeError('Protected source drift: '+r['path'])
 for r in rows:
  if r['path'].startswith('src/') and r['path'] not in GAME and (ROOT/r['path']).read_bytes()!=old[r['path']]:raise RuntimeError('Unassigned gameplay source changed')
 return guarded

def original(folder,row):
 p=Path(row['path'])
 if not p.is_absolute():raise RuntimeError('Absolute original input required')
 if folder==OUT/'agents/native-acquisition-producer' and p==ROOT/'tools/reconstruction/cn_native_acquisition_producer198.py' and row.get('copy')=='initial/s02.py' and row['sha256']=='1c1e4dabe00e30945b1f0fbc4ab6ab1c7e20471c4674399b4b9f2d435071f596':
  raw=matches(folder/row['copy'],row)
  if raw!=matches(folder/'epochs/initial-body-comment/tool.py',row):raise RuntimeError('Historical own-tool initial epoch drift')
  current=[r for r in read(folder/'current-source-origins.json') if Path(r['path'])==p]
  if len(current)!=1 or matches(p,current[0])!=matches(folder/current[0]['copy'],current[0]):raise RuntimeError('Final tool epoch/current input drift')
  return raw
 raw=matches(p,row)
 if row.get('copy') is not None:
  if matches(folder/row['copy'],row)!=raw:raise RuntimeError('Full original copy drift')
 elif not (row.get('retained_complete_in_place') is True or row.get('complete_retained_in_place') is True or 'retained in place' in row.get('disposition','')):
  raise RuntimeError('Explicit full-hashed in-place disposition required')
 return raw

def raw_spans(folder,rows,pe):
 for r in rows:
  raw=matches(folder/r.get('copy',r.get('raw_copy',r.get('raw'))),r)
  offset=r['file_offset']
  if offset<0 or offset+len(raw)>len(pe) or pe[offset:offset+len(raw)]!=raw:raise RuntimeError('Bounded span differs from actual full-hashed PE')

def agents():
 deliveries=[];paths=set();records=[]
 for n,pin in zip(AGENTS,AGENT_PINS):
  folder=OUT/'agents'/n;b=(folder/'seal.json').read_bytes()
  if sha(b)!=pin:raise RuntimeError('Agent seal drift')
  seal=json.loads(b);members=seal.get('files',seal.get('members'))
  if not isinstance(members,list):raise RuntimeError('Full agent member list required')
  for r in members:matches(folder/r['path'],r)
  actual=inventory(folder)
  if {r['path'] for r in actual}!={r['path'] for r in members}|{'seal.json'}:raise RuntimeError('Agent inventory drift')
  current=read(folder/'current-source-origins.json')
  for r in current:
   p=Path(r['path']);p=p if p.is_absolute() else ROOT/p;rel=p.relative_to(ROOT).as_posix()
   artifact_tool=p==OUT/'agents/shared-book-use-integration-frontier/source_account.py' and n=='shared-book-use-integration-frontier'
   if rel in BOOKS or (rel.startswith('artifacts/') and not artifact_tool) or rel=='tools/reconstruction/dual_client_route_catalog.py':raise RuntimeError('Mutable receipt is not source origin')
   if matches(p,r)!=matches(folder/r['copy'],r):raise RuntimeError('Agent actual source drift')
   if not artifact_tool:paths.add(rel)
   records.append(dict(agent=n,path=rel,source=r,immutable_artifact_static_tool=artifact_tool))
  inputs=read(folder/'original-inputs.json')
  for r in inputs:original(folder,r)
  refs=[]
  if (folder/'native-input-references.json').exists():
   refs=read(folder/'native-input-references.json')
   for r in refs:original(folder,r)
  if n!='shared-book-use-integration-frontier':
   pe_rows=[r for r in inputs+refs if Path(r['path']).suffix.lower()=='.exe']
   if len(pe_rows)!=1:raise RuntimeError('Exactly one qualified PE origin required')
   pe=matches(Path(pe_rows[0]['path']),pe_rows[0])
   spanpath='native-spans.json'
   raw_spans(folder,read(folder/spanpath),pe)
   if (folder/'data-sites.json').exists():raw_spans(folder,read(folder/'data-sites.json'),pe)
  deliveries.append(dict(agent=n,seal_sha256=pin,findings=read(folder/'findings.json'),original_inputs=inputs,external_references=refs,current_source_origins=current,files=actual))
 return deliveries,paths,records

def root_native():
 for r in read(OUT/'root-source-review/source-origins.json'):
  if matches(ROOT/r['path'],r)!=matches(OUT/r['copy'],r):raise RuntimeError('Full root current source review drift')

def account():
 if (OUT/'findings.json').exists():raise RuntimeError('Fresh199 only')
 rows,old=before();prior();guarded=protected(rows,old);deliveries,paths,records=agents();root_native()
 cap=read(OUT/'policy/capacity-before-final-account.json')
 if cap['unreadable_count'] or not cap['under_limit']:raise RuntimeError('Whole-project capacity required')
 paths|=set(WRITTEN)|{r['path'] for r in read(OUT/'root-source-review/source-origins.json')}
 ledger=read(ROOT/BOOKS[1]);previous=json.loads(old[BOOKS[1]])
 if ledger['dual_client_source_segments']!=previous['dual_client_source_segments'] or len(ledger['dual_client_source_segments'])!=188:raise RuntimeError('Historical188 changed')
 changed=[p for p in GAME if p in old and (ROOT/p).read_bytes()!=old[p]]
 new=[p for p in GAME if p not in old]
 if len(changed)!=4 or len(new)!=3:raise RuntimeError('Actual4 modified and3 new C++ sources required')
 facts=dict(round=ROUND,research_only=False,completed_parallel_agents=3,new_Cplusplus_source_files_added=3,existing_Cplusplus_source_files_modified=4,new_source_segments=1,source_segments=189,new_packet_values=0,new_phase_bindings=0,new_source_phase_bindings=2,new_complete_bidirectional_routes=0,whole_game_completion_percent=None,whole_game_denominator=None,source_paths=sorted(paths),
  actual_CN_ready_item_source_adapters_added=1,actual_C25_typed_request_views_added=1,actual_ready_C1F_independent_source_controls_added=1,exact_book_item_record_lookup_added=1,
  source_conclusion='Actual modal3B -> C25 native5-byte view -> selected ready split/dispatch -> strong current exact SKB record -> explicit actual game owner + immutable operation evidence/full native reply queue; separate conditional1F00 uses independent owner, never initial bootstrap. No learning rules/Main/default owner invented.',
  authority_scope='Owner implementation, true native entitlement/custody/learned/book debit/durable event transaction and complete response correlation remain OPEN; source class connects only an explicitly selected real owner. Full routes remain unknown, new full routes zero.',
  source_notes=['All5 C25 bytes preserved; only exact native confirmation caller proves tail0, no global padding gate.','Book item lookup is a value copy of actual SKB source, not an inverse native alias mapping or shared skill grant.','BeforeCatalog requires real store/current lifetime authority; native resource hashes are not database ownership/revision evidence.','Control1F00 can occur even if25 producer suppressed; its real owner is independent and no prior25 receipt is inferred. Unknown/missing control owner rejects full25+1F aggregate before effects.','Aggregate shape preflight is not an atomic multi-request transaction; committed prefixes are not retried/rolled back by this adapter.','Native S3C subtract/slotclear does not read incoming itemWORD in the qualified consumer; WORLD35 flag3 is not learned pointer/count deletion.'],
  remaining=['Supply actual CN native learned/common subject/book custody/current single durable mutation owner with full native replies; formal Main selection still OPEN.','Qualify ready1F native semantics/real owner and all C25 families/C26 targeted use/C28 source branches without borrowing TW CUSTOM.','Complete whole TW/CN/web phase/state/variant/deferred routes, common64/stack99 wire/object/display before later comprehensive builds/tests/repair/release.'],
  build_run=False,tests_run=False,native_execution=False,runtime_run=False,codec_execution=False,database_access=False,SQL_run=False,deployed=False,owner_explicit_resume=True,goal_status='active')
 dump(OUT/'parallel-agent-deliveries.json',deliveries);dump(OUT/'source/reviewed-current-source-records.json',records);dump(OUT/'findings.json',facts)
 ledger['native_skill_confirmation_frontier199']=facts
 ledger['dual_client_source_segments'].append(dict(name=OUT.name,round=ROUND,version_scope='CN-native-ready-C25-and-independent-ready1F',status=facts['source_conclusion'],source_paths=sorted(paths),native_c2s_by_phase={'world-ready':['25','1F']},native_s2c_by_phase={},source_owner_chains_added=0,tw_source_owner_chains_added=0,formal_application_hosted=False,complete_gameplay_routes_added=0,evidence=OUT.relative_to(ROOT).as_posix(),remaining=facts['remaining']))
 plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND;plan['owner_requested_stop_after_work_round']=None;plan['owner_explicit_resume_after_stop']=ROUND;plan['next_source_frontier']=facts['remaining'][0]
 (ROOT/BOOKS[1]).write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 origins=[]
 for i,n in enumerate(sorted(paths|set(BOOKS))):
  b=(ROOT/n).read_bytes();c='source/current/f%03d'%i+Path(n).suffix;save(OUT/c,b);origins.append(dict(path=n,copy=c,bytes=len(b),sha256=sha(b),changed_this_round=n not in old or old[n]!=b))
  if n in old and old[n]!=b:
   d=''.join(difflib.unified_diff(old[n].decode('utf-8-sig').splitlines(True),b.decode('utf-8-sig').splitlines(True),fromfile='before/'+n,tofile='current/'+n))
   if d:save(OUT/'diff'/('d%03d.diff'%i),d.encode())
 dump(OUT/'source/source-origins.json',origins)
 print(json.dumps(dict(protected_files=len(guarded),source_files=len(paths),source_segments=189,new_complete_routes=0)))

def enrich():
 for p in reports():save(OUT/'reports/raw'/(p.parent.name+'-'+p.name),p.read_bytes())
 receipt=dict(research_only=False,new_CPP=3,modified_CPP=4,source_segments=189,new_source_segments=1,new_complete_bidirectional_routes=0,whole_game_percent=None,current_catalog_source_files=len(read(CAT/'source-file-manifest.json')),owner_explicit_resume=True)
 for p in [reports()[0],reports()[2]]:
  v=read(p);v['native_skill_confirmation_frontier199']=read(OUT/'findings.json');v['parallel_agent_deliveries']=read(OUT/'parallel-agent-deliveries.json');v['current_round_source_delta']=receipt;p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 for p in [reports()[1],reports()[3]]:p.write_text((ROOT/DOC).read_text(encoding='utf-8')+'\n\nStatic accounting: '+json.dumps(receipt)+'\n',encoding='utf-8')
 dump(OUT/'reports/enrichment-receipt.json',receipt);print(json.dumps(receipt))

def seal():
 if (OUT/'manifest.json').exists() or (CAT/'manifest.json').exists():raise RuntimeError('Fresh199 seals required')
 rows,old=before();prior();guarded=protected(rows,old);deliveries,_,_=agents();root_native()
 if deliveries!=read(OUT/'parallel-agent-deliveries.json'):raise RuntimeError('Agent delivery drift')
 for r in read(OUT/'source/source-origins.json'):
  if matches(ROOT/r['path'],r)!=matches(OUT/r['copy'],r):raise RuntimeError('Final source drift')
 ledger=read(ROOT/BOOKS[1])
 if ledger['dual_client_source_segments'][:188]!=json.loads(old[BOOKS[1]])['dual_client_source_segments'] or len(ledger['dual_client_source_segments'])!=189:raise RuntimeError('Historical188/new189 drift')
 sources=read(CAT/'source-file-manifest.json')
 for n,r in sources.items():matches(ROOT/n,r)
 entries=[r for r in read(CAT/'input-manifest.json') if r['input']=='source-ledger']
 if len(entries)!=1 or matches(CAT/entries[0]['snapshot'],entries[0])!=(ROOT/BOOKS[1]).read_bytes():raise RuntimeError('Catalog ledger drift')
 a,b,c,d=reports()
 if a.read_bytes()!=c.read_bytes() or b.read_bytes()!=d.read_bytes():raise RuntimeError('Final report mismatch')
 v=read(a)
 if v['round']!=ROUND or v['route_ledger_sha256']!=sha((ROOT/BOOKS[1]).read_bytes()) or v['dual_client_endpoint_catalog']['summary']!=read(CAT/'summary.json'):raise RuntimeError('Report/catalog drift')
 for k in ['whole_game_distinct_packet_count','whole_game_completed_route_count','whole_game_completion_percent']:
  if v['counts'][k] is not None:raise RuntimeError('False denominator')
 for p in reports():save(OUT/'reports/final'/(p.parent.name+'-'+p.name),p.read_bytes())
 flags=dict(sealed=True,method='STATIC_SOURCE_INTEGRATION_ONLY',build_run=False,tests_run=False,native_execution=False,runtime_run=False,database_access=False,deployed=False)
 cm=dict(round=CAT.name,**flags,current_source_files=len(sources),files=inventory(CAT));dump(CAT/'manifest.json',cm)
 rm=dict(round=ROUND,**flags,before_files=len(rows),protected_files=len(guarded),source_segments=189,new_source_segments=1,new_CPP=3,modified_CPP=4,new_complete_bidirectional_routes=0,whole_game_percent=None,owner_explicit_resume=True,catalog_manifest_sha256=sha((CAT/'manifest.json').read_bytes()),files=inventory(OUT));dump(OUT/'manifest.json',rm)
 print(json.dumps(dict(root_members=len(rm['files']),catalog_members=len(cm['files']),root_sha256=sha((OUT/'manifest.json').read_bytes()),catalog_sha256=sha((CAT/'manifest.json').read_bytes()))))

if __name__=='__main__':
 if len(sys.argv)!=2 or sys.argv[1] not in ['account','enrich','seal']:raise RuntimeError('account/enrich/seal required')
 globals()[sys.argv[1]]()
