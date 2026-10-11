"""Round204 static source accounting only; active source round; owner requests pause after207."""
from pathlib import Path
import json,sys,difflib
from .parallel_game_connection_frontier_delivery import ROOT,sha,read,save,dump,matches,inventory
BASE=ROOT/'artifacts/integration/packet-connections-20261006'
OUT=BASE/'cn-primary-skill-ordinal-source-01';CAT=BASE/'endpoint-catalog204'
ROUND='20261009-cn-primary-skill-ordinal-source'
DOC='docs/research/cn-primary-skill-ordinal-source-20261009.md'
GAME=['src/cn/world/CnWorldPrimarySkillSource.h','src/cn/world/CnWorldPrimarySkillSource.cpp','src/cn/world/CnPrebornSkillChoiceSource.h','src/cn/world/CnPrebornSkillChoiceSource.cpp']
WRITTEN=GAME+[DOC,'tools/reconstruction/cn_primary_skill_ordinal_source_delivery.py','tools/reconstruction/dual_client_route_catalog.py','tools/reconstruction/cn_primary_ordinal204.py']
BOOKS=['docs/PACKET_CONNECTION_GOAL_20261006.md',(BASE/'packet-route-ledger.json').relative_to(ROOT).as_posix()]
PINS={'cn-primary-skill-definition-source-01':'e61eb2afe79bbdc4ab5603c15c6547412286119efe1ff32879b9a217841e6ed1','endpoint-catalog203':'103241dd1d30c600a179551f33a292496ba8e495b76d51532e57edccf4107b5f'}

def reports():return [BASE/'packet-progress-latest.json',BASE/'packet-progress-latest.md',BASE/'round-reports'/(ROUND+'.json'),BASE/'round-reports'/(ROUND+'.md')]

def before():
 b=(OUT/'before-manifest.json').read_bytes()
 if sha(b)!='dcb0baf02d3abd6ea5850dae145e63f594dbdcb064e0e49ec39208cc2611b8be':raise RuntimeError('Actual before204 drift')
 rows=json.loads(b)
 if len(rows)!=1451:raise RuntimeError('1451 actual before sources required')
 return rows,{r['path']:matches(OUT/r['snapshot'],r) for r in rows}

def prior():
 count=0
 for n,pin in PINS.items():
  b=(BASE/n/'manifest.json').read_bytes()
  if sha(b)!=pin or b!=(OUT/'retained-prior'/n/'manifest.json').read_bytes():raise RuntimeError('Pinned203 seal drift')
  for r in json.loads(b)['files']:matches(BASE/n/r['path'],r);count+=1
 if count!=2459:raise RuntimeError('Full2459 retained203 members required')

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
 r=read(OUT/'actual-accounting-input203.json');matches(OUT/r['copy'],r);matches(Path(r['path']),r)

def reviewer():
 pins=read(OUT/'sealed-agent-pins.json');deliveries=[];paths=set()
 if len(pins)!=2:raise RuntimeError('Two actual204 bounded deliveries required')
 rows,old=before()
 for name in ['primary-ordinal-native','primary-ordinal-source-review']:
  folder=OUT/'agents'/name;b=(folder/'seal.json').read_bytes()
  if sha(b)!=pins[name]:raise RuntimeError('Actual204 seal drift')
  seal=json.loads(b);members=seal.get('files',seal.get('members'))
  if not isinstance(members,list):raise RuntimeError('Complete seal member list required')
  for r in members:matches(folder/r['path'],r)
  if {r['path'] for r in inventory(folder)}!={r['path'] for r in members}|{'seal.json'}:raise RuntimeError('Full actual204 agent inventory drift')
  current=read(folder/'current-source-origins.json')
  for r in current:
   p=Path(r['path']);p=p if p.is_absolute() else ROOT/p;rel=p.relative_to(ROOT).as_posix()
   artifact_tool=p==folder/'review_account.py'
   if (rel.startswith('artifacts/') and not artifact_tool) or rel in BOOKS:raise RuntimeError('Mutable receipt cannot be source original')
   if matches(p,r)!=matches(folder/r['copy'],r):raise RuntimeError('Actual final204 source drift')
   if not artifact_tool:paths.add(rel)
  refs=read(folder/'native-input-references.json') if (folder/'native-input-references.json').exists() else []
  for r in refs:matches(Path(r['path']),r)
  if name=='primary-ordinal-source-review':
   for r in read(folder/'original-inputs.json'):
    p=Path(r['path']);p=p if p.is_absolute() else ROOT/p;rel=p.relative_to(ROOT).as_posix()
    raw=matches(OUT/r['original'],r)
    if rel not in old or raw!=old[rel] or matches(folder/r['copy'],r)!=raw:raise RuntimeError('Full before204 source drift')
   for r in read(folder/'final-original-inputs.json'):
    p=Path(r['path']);p=p if p.is_absolute() else ROOT/p
    if matches(p,r)!=matches(folder/r['copy'],r):raise RuntimeError('Full final204 source drift')
  if name=='primary-ordinal-native':
   for r in read(folder/'original-inputs.json'):
    if matches(Path(r['path']),r)!=matches(folder/r['copy'],r):raise RuntimeError('Actual native204 complete original drift')
   pe_rows=[r for r in refs if Path(r['path']).suffix.lower()=='.exe']
   if len(pe_rows)!=1:raise RuntimeError('One full pinned actual native PE required')
   pe=matches(Path(pe_rows[0]['path']),pe_rows[0])
   if pe_rows[0]['sha256']!='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8':raise RuntimeError('Pinned actual native image required')
   for r in read(folder/'native-spans.json'):
    raw=matches(folder/r['raw'],r);at=r['file_offset']
    if pe[at:at+len(raw)]!=raw:raise RuntimeError('Native bounded204 byte mismatch')
  deliveries.append(dict(agent=name,seal_sha256=sha(b),findings=read(folder/'findings.json'),current_source_origins=current,files=inventory(folder)))
 return deliveries,paths

def account():
 if (OUT/'findings.json').exists():raise RuntimeError('Fresh204 only')
 rows,old=before();prior();guarded=protected(rows,old);original_copies();reviews,paths=reviewer()
 cap=read(OUT/'policy/capacity-before-final-account.json')
 if cap['unreadable_count'] or not cap['under_limit']:raise RuntimeError('WholeGod2 capacity required')
 changed=[p for p in GAME if p in old and (ROOT/p).read_bytes()!=old[p]];new=[p for p in GAME if p not in old]
 if len(changed)!=4 or len(new)!=0:raise RuntimeError('Actual4 modified and0 new CPP required')
 paths|=set(WRITTEN)|{r['path'] for r in read(OUT/'root-source-initial/origins.json')}|{'CMakeLists.txt'}
 ledger=read(ROOT/BOOKS[1]);previous=json.loads(old[BOOKS[1]])
 if ledger['dual_client_source_segments']!=previous['dual_client_source_segments'] or len(ledger['dual_client_source_segments'])!=193:raise RuntimeError('Historical193 drift')
 facts=dict(round=ROUND,research_only=False,completed_parallel_agents=2,new_Cplusplus_source_files_added=0,existing_Cplusplus_source_files_modified=4,new_source_segments=1,source_segments=194,new_packet_values=0,new_source_phase_bindings=0,new_complete_bidirectional_routes=0,whole_game_completion_percent=None,whole_game_denominator=None,source_paths=sorted(paths),
  actual_CN_primary_ordinal_projections_added=1,new_bounded_native_bytes=272,native_leaf_bytes=93,native_caller_bounded_bytes=179,
  source_conclusion='Actual complete owned selected primary row/bank -> qualified original first physical ordinal lookup with full DWORD operands -> optional owned primary-ordinal selection facts through existing common-operation inputs. No flags filter, BYTE truncation or learned/cast authority.',
  authority_scope='The actual4DA630 caller has signed-WORD mode tables and a separate downstream gate. The existing selection-word projection does not attest that caller or that gate. No learned issuer, common transaction, WORLD-to-battle materializer or Main activation added; complete gameplay routes zero.',
  source_notes=['Native4D2B50 reads BYTE count once; compares record BYTE1/BYTE0 zeroextended against whole DWORD kind/id; first physical duplicate wins even with zero flags.','Qualified absent ordinal represents native -1; outer absent result rejects stale Current and cannot become successful no-match. Actual bank/row retained intact, no null/missing pointer fabricated.','Optional primary source only; selection facts keep lookup distinct from filtered offer/book binding/entitlement and own exact operands/ordinal after commit.','Actual4DA630 type2 mode tables signextend each WORD to DWORD. Upper bits and negative operands are preserved; downstream4D3B60 first-match gate failure is not a retry on duplicate.','Raw recovery bounded to93-byte pure leaf and179-byte caller data; no formatter/UIcallee entered.'],
  remaining=['Recover actual4D3B60 pure ordinal gate and nonGUI primary-list positive writers; do not infer a learned or cast grant from first-match membership.','Connect real common learned/book custody/debit/save/durable owner and exact native replies; actual store lifetime/current/Main issuer remains required.','Complete TW/CN/web full-game bidirectional/state/variant/deferred routes, numeric64/stack99; comprehensive builds/tests/repair/release after all sources connected.'],
  owner_explicit_resume=True,owner_five_round_start=203,owner_requested_stop_after_round=207,owner_requested_pause_at_round_end=False,goal_status_at_source_account='active',build_run=False,tests_run=False,native_execution=False,runtime_run=False,codec_execution=False,database_access=False,SQL_run=False,deployed=False)

 dump(OUT/'parallel-agent-deliveries.json',reviews);dump(OUT/'findings.json',facts)
 ledger['native_primary_skill_ordinal_source204']=facts
 ledger['dual_client_source_segments'].append(dict(name=OUT.name,round=ROUND,version_scope='CN-pinned-primary-first-ordinal-source',status=facts['source_conclusion'],source_paths=sorted(paths),native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,tw_source_owner_chains_added=0,formal_application_hosted=False,complete_gameplay_routes_added=0,evidence=OUT.relative_to(ROOT).as_posix(),remaining=facts['remaining']))
 plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND;plan['owner_requested_stop_after_work_round']='round207';plan['owner_requested_stop_after_round_number']=207;plan['owner_five_round_start']=203;plan['owner_five_round_end']=207;plan['continuation_requires_owner_resume']=False;plan['next_source_frontier']=facts['remaining'][0]
 (ROOT/BOOKS[1]).write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 with (ROOT/BOOKS[0]).open('a',encoding='utf-8') as f:f.write('\n\n## 第204輪來源及五輪停止指示\n\n'+(ROOT/DOC).read_text(encoding='utf-8')+'\n本次由203算第1輪，本204為第2輪，完成203至207共5輪後暫停；本204仍active，不開始208。\n')

 origins=[]
 for i,n in enumerate(sorted(paths|set(BOOKS))):
  b=(ROOT/n).read_bytes();copy=f'source/current/f{i:03d}'+Path(n).suffix;save(OUT/copy,b)
  origins.append(dict(path=n,copy=copy,bytes=len(b),sha256=sha(b),changed_this_round=n not in old or old[n]!=b))
  if n in old and old[n]!=b:
   diff=''.join(difflib.unified_diff(old[n].decode('utf-8-sig').splitlines(True),b.decode('utf-8-sig').splitlines(True),fromfile='before/'+n,tofile='current/'+n))
   if diff:save(OUT/'diff'/f'd{i:03d}.diff',diff.encode())
 dump(OUT/'source/source-origins.json',origins)
 print(json.dumps(dict(protected_files=len(guarded),source_files=len(paths),source_segments=194,new_CPP=0,modified_CPP=4,new_complete_routes=0,stop_after_round=207)))

def enrich():
 for p in reports():save(OUT/'reports/raw'/(p.parent.name+'-'+p.name),p.read_bytes())
 receipt=dict(new_CPP=0,modified_CPP=4,source_segments=194,new_source_segments=1,new_complete_bidirectional_routes=0,whole_game_percent=None,current_catalog_source_files=len(read(CAT/'source-file-manifest.json')),owner_requested_pause_at_round_end=False)
 for p in [reports()[0],reports()[2]]:
  v=read(p);v['native_primary_skill_ordinal_source204']=read(OUT/'findings.json');v['parallel_agent_deliveries']=read(OUT/'parallel-agent-deliveries.json');v['current_round_source_delta']=receipt;p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 for p in [reports()[1],reports()[3]]:p.write_text((ROOT/DOC).read_text(encoding='utf-8')+'\n\nStatic accounting: '+json.dumps(receipt)+'\n',encoding='utf-8')
 dump(OUT/'reports/enrichment-receipt.json',receipt);print(json.dumps(receipt))

def seal():
 if (OUT/'manifest.json').exists() or (CAT/'manifest.json').exists():raise RuntimeError('Fresh204 seals required')
 rows,old=before();prior();guarded=protected(rows,old);original_copies();reviews,paths=reviewer()
 if reviews!=read(OUT/'parallel-agent-deliveries.json'):raise RuntimeError('Reviewer delivery drift')
 for r in read(OUT/'source/source-origins.json'):
  if matches(ROOT/r['path'],r)!=matches(OUT/r['copy'],r):raise RuntimeError('Final current source drift')
 ledger=read(ROOT/BOOKS[1])
 if ledger['dual_client_source_segments'][:193]!=json.loads(old[BOOKS[1]])['dual_client_source_segments'] or len(ledger['dual_client_source_segments'])!=194:raise RuntimeError('Historical193/new194 drift')
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
 rm=dict(round=ROUND,**flags,before_files=len(rows),protected_files=len(guarded),source_segments=194,new_source_segments=1,new_CPP=0,modified_CPP=4,new_complete_bidirectional_routes=0,whole_game_percent=None,owner_requested_stop_after_round=207,catalog_manifest_sha256=sha((CAT/'manifest.json').read_bytes()),files=inventory(OUT));dump(OUT/'manifest.json',rm)
 print(json.dumps(dict(root_members=len(rm['files']),catalog_members=len(cm['files']),root_sha256=sha((OUT/'manifest.json').read_bytes()),catalog_sha256=sha((CAT/'manifest.json').read_bytes()))))

if __name__=='__main__':
 if len(sys.argv)!=2 or sys.argv[1] not in ['account','enrich','seal']:raise RuntimeError('account/enrich/seal required')
 globals()[sys.argv[1]]()
