"""Round200 static source acquisition/accounting only; never execute game/SQL."""
from pathlib import Path
import json,sys,difflib
from .parallel_game_connection_frontier_delivery import ROOT,sha,read,save,dump,matches,inventory
BASE=ROOT/'artifacts/integration/packet-connections-20261006'
OUT=BASE/'cn-native-item-control-source-frontier-01'
CAT=BASE/'endpoint-catalog200'
ROUND='20261009-cn-native-item-control-source-frontier'
DOC='docs/research/cn-native-item-control-source-frontier-20261009.md'
BOOKS=['docs/PACKET_CONNECTION_GOAL_20261006.md',str((BASE/'packet-route-ledger.json').relative_to(ROOT).as_posix())]
GAME=['src/db/NativeSkillBookSourceCatalog.h','src/db/NativeSkillBookSourceCatalog.cpp','src/cn/assets/CnNativeSkillBookSourceImport.h','src/cn/assets/CnNativeSkillBookSourceImport.cpp','src/db/SqliteDatabase.h','src/db/SqliteDatabase.cpp']
WRITTEN=GAME+[DOC,'tools/reconstruction/cn_native_item_control_source_frontier_delivery.py','tools/reconstruction/cn_ready1f_context200.py','tools/reconstruction/cn_book_eligibility200.py','tools/reconstruction/dual_client_route_catalog.py']
AGENTS=['native-ready1f-context','native-book-eligibility','shared-book-source-storage']
PINS={'cn-native-skill-confirmation-frontier-01':'b557ea4ce467ba2a60e70a52fd135572e09dbd850bcb87aec82353d648efab08','endpoint-catalog199':'0e943aeb210f684ee29e0428634e205edc451d33e1e5a0db8878241c266f8cd1'}

def reports():return [BASE/'packet-progress-latest.json',BASE/'packet-progress-latest.md',BASE/'round-reports'/(ROUND+'.json'),BASE/'round-reports'/(ROUND+'.md')]

def before():
 b=(OUT/'before-manifest.json').read_bytes()
 if sha(b)!='61d1be29c2fca9b7bf511cbd612fb811b8035e2feb4462d0de43e5cd2e8c6dac':raise RuntimeError('Original before200 drift')
 rows=json.loads(b)
 if len(rows)!=1426:raise RuntimeError('Before1426 required')
 return rows,{r['path']:matches(OUT/r['snapshot'],r) for r in rows}

def prior():
 total=0
 for n,pin in PINS.items():
  b=(BASE/n/'manifest.json').read_bytes()
  if sha(b)!=pin or b!=(OUT/'retained-prior'/n/'manifest.json').read_bytes():raise RuntimeError('Prior199 manifest drift')
  for r in json.loads(b)['files']:matches(BASE/n/r['path'],r);total+=1
 if total!=2444:raise RuntimeError('Full2444 prior members required')

def protected(rows,old):
 excluded=set(WRITTEN+BOOKS)|{p.relative_to(ROOT).as_posix() for p in reports()[:2]}
 guarded=[r for r in rows if r['path'] not in excluded]
 for r in guarded:
  if (ROOT/r['path']).read_bytes()!=old[r['path']]:raise RuntimeError('Protected source drift: '+r['path'])
 for r in rows:
  if r['path'].startswith('src/') and r['path'] not in GAME and (ROOT/r['path']).read_bytes()!=old[r['path']]:raise RuntimeError('Unassigned gameplay source changed')
 return guarded

def original(folder,row,old):
 p=Path(row['path'])
 if not p.is_absolute():raise RuntimeError('Absolute original input required')
 if row.get('epoch')=='before200':
  rel=p.relative_to(ROOT).as_posix()
  if rel not in old:raise RuntimeError('Historical before200 missing')
  raw=matches(folder/row['copy'],row)
  if raw!=old[rel]:raise RuntimeError('Historical before200 source differs')
  return raw
 raw=matches(p,row)
 if row.get('copy') is not None:
  if matches(folder/row['copy'],row)!=raw:raise RuntimeError('Full original copy drift')
 elif not (row.get('retained_complete_in_place') is True or row.get('complete_retained_in_place') is True or 'retained in place' in row.get('disposition','')):
  raise RuntimeError('Explicit full-hashed in-place disposition required')
 return raw

def raw_spans(folder,rows,pe):
 for r in rows:
  raw=matches(folder/r.get('copy',r.get('raw_copy',r.get('raw'))),r);offset=r['file_offset']
  if offset<0 or offset+len(raw)>len(pe) or pe[offset:offset+len(raw)]!=raw:raise RuntimeError('Bounded span differs from full-hashed actual PE')

def agents(old):
 pins=read(OUT/'sealed-agent-pins.json');deliveries=[];paths=set();records=[]
 if len(pins)!=len(AGENTS):raise RuntimeError('Three agent pins required')
 for n,pin in zip(AGENTS,pins):
  folder=OUT/'agents'/n;b=(folder/'seal.json').read_bytes()
  if sha(b)!=pin:raise RuntimeError('Agent seal drift')
  seal=json.loads(b);members=seal.get('files',seal.get('members'))
  if not isinstance(members,list):raise RuntimeError('Full agent members required')
  for r in members:matches(folder/r['path'],r)
  actual=inventory(folder)
  if {r['path'] for r in actual}!={r['path'] for r in members}|{'seal.json'}:raise RuntimeError('Agent inventory drift')
  current=read(folder/'current-source-origins.json')
  for r in current:
   p=Path(r['path']);p=p if p.is_absolute() else ROOT/p;rel=p.relative_to(ROOT).as_posix()
   artifact_tool=p==OUT/'agents/shared-book-source-storage/source_account.py' and n=='shared-book-source-storage'
   if rel in BOOKS or (rel.startswith('artifacts/') and not artifact_tool) or rel=='tools/reconstruction/dual_client_route_catalog.py':raise RuntimeError('Mutable receipt is not source origin')
   if matches(p,r)!=matches(folder/r['copy'],r):raise RuntimeError('Agent actual current source drift')
   if not artifact_tool:paths.add(rel)
   records.append(dict(agent=n,path=rel,source=r,immutable_artifact_static_tool=artifact_tool))
  inputs=read(folder/'original-inputs.json')
  for r in inputs:original(folder,r,old)
  historical=[]
  if (folder/'before-source-origins.json').exists():
   historical=read(folder/'before-source-origins.json')
   for r in historical:
    p=Path(r['path']);rel=p.relative_to(ROOT).as_posix();raw=matches(folder/r['copy'],r)
    expected=old[rel] if rel in old else matches(p,r)
    if r.get('epoch')!='actual-read200-before' or raw!=expected:raise RuntimeError('Historical actual before200 epoch drift')
  refs=read(folder/'native-input-references.json') if (folder/'native-input-references.json').exists() else []
  for r in refs:original(folder,r,old)
  if n!='shared-book-source-storage':
   pe_rows=[r for r in inputs+refs if Path(r['path']).suffix.lower()=='.exe']
   if len(pe_rows)!=1:raise RuntimeError('One full actual PE required')
   pe=matches(Path(pe_rows[0]['path']),pe_rows[0]);raw_spans(folder,read(folder/'native-spans.json'),pe)
   if (folder/'data-sites.json').exists():raw_spans(folder,read(folder/'data-sites.json'),pe)
  deliveries.append(dict(agent=n,seal_sha256=pin,findings=read(folder/'findings.json'),original_inputs=inputs,historical_before_source_origins=historical,external_references=refs,current_source_origins=current,files=actual))
 return deliveries,paths,records

def root_native():
 for r in read(OUT/'root-source-review/source-origins.json'):
  if matches(ROOT/r['path'],r)!=matches(OUT/r['copy'],r):raise RuntimeError('Full root current source review drift')

def account():
 if (OUT/'findings.json').exists():raise RuntimeError('Fresh200 only')
 rows,old=before();prior();guarded=protected(rows,old);deliveries,paths,records=agents(old);root_native()
 cap=read(OUT/'policy/capacity-before-final-account.json')
 if cap['unreadable_count'] or not cap['under_limit']:raise RuntimeError('Whole project capacity required')
 paths|=set(WRITTEN)|{r['path'] for r in read(OUT/'root-source-review/source-origins.json')}
 ledger=read(ROOT/BOOKS[1]);previous=json.loads(old[BOOKS[1]])
 if ledger['dual_client_source_segments']!=previous['dual_client_source_segments'] or len(ledger['dual_client_source_segments'])!=189:raise RuntimeError('Historical189 changed')
 changed=[p for p in GAME if p in old and (ROOT/p).read_bytes()!=old[p]];new=[p for p in GAME if p not in old]
 if len(changed)!=2 or len(new)!=4:raise RuntimeError('Actual2 modified and4 new C++ sources required')
 facts=dict(round=ROUND,research_only=False,completed_parallel_agents=3,new_Cplusplus_source_files_added=4,existing_Cplusplus_source_files_modified=2,new_source_segments=1,source_segments=190,new_packet_values=0,new_phase_bindings=0,new_source_phase_bindings=0,new_complete_bidirectional_routes=0,whole_game_completion_percent=None,whole_game_denominator=None,source_paths=sorted(paths),
  actual_shared_raw_book_source_catalogs_added=1,actual_CN_source_records_in_import_source=386,source_import_executed=False,
  source_conclusion='Pinned386 CN SKB owned records -> explicit sameDB transaction/source metadata/shared raw evidence table -> exact item+ordinal reader/readback and lazy sameconnection SqliteDatabase APIs. TW381/396 parsed projection frozen. Ready1F/window and67/42 input gates qualified independently of learning authority.',
  authority_scope='Raw source materialization is neither learned/custody/cost authority nor a completed game route. No native learning mutation, true1F owner/reply, Main/default migration/import execution supplied.',
  source_notes=['Shared raw source table avoids TW index<=380/mandatory396 projection conflict without splitting TW/CN gameplay tables. Exact dataset-qualified source identity is not common item identity.','CN raw hashes include CRLF; TW existing importer strips CRLF. No normalization or alias inversion.','Same main schema/connection, explicit FK/schema identity, no enclosing transaction, immutable complete386 materialization before SQL, exact all-row readback source and conflict rollback. No SQL was executed.','Current native resource epoch is not DB/store/game owner authority. Borrowed reader database must outlive every lookup.','Actual4960A0 checks current UI profile window flags20, not role/learned permission.5176B0 rewrites430A8 in both4AF370 modes;1F00 does not identify its originating caller or actor.','Client definition BYTE67 and WORD42/DWORD inline64 gate precedes actual control2C C56→C1F; BYTE6B is separate prompt/arm condition. Unknown64 counter/subject taxonomy not relabeled MP or entitlement.'],
  remaining=['Trace real owner/current supplier of CN inline430A8+64 and selected subject learned rows to connect authoritative book entitlement/custody/durable mutation; true native reply correlation remains open.','Trace actual ready1F multiple caller families and profile component replacement to qualify real current owner/replies; do not infer initial bootstrap or ACK from identical wire.','Complete whole TW/CN/web phase/state/variant/deferred routes, common64/stack99 wire/object/display before comprehensive build/tests/repair/release.'],
  build_run=False,tests_run=False,native_execution=False,runtime_run=False,codec_execution=False,database_access=False,SQL_run=False,deployed=False,owner_explicit_resume=True,goal_status='active')
 dump(OUT/'parallel-agent-deliveries.json',deliveries);dump(OUT/'source/reviewed-current-source-records.json',records);dump(OUT/'findings.json',facts)
 ledger['native_item_control_source_frontier200']=facts
 ledger['dual_client_source_segments'].append(dict(name=OUT.name,round=ROUND,version_scope='CN-pinned-SKB-shared-source-materialization',status=facts['source_conclusion'],source_paths=sorted(paths),native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,tw_source_owner_chains_added=0,formal_application_hosted=False,complete_gameplay_routes_added=0,evidence=OUT.relative_to(ROOT).as_posix(),remaining=facts['remaining']))
 plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND;plan['owner_requested_stop_after_work_round']=None;plan['owner_explicit_resume_after_stop']=ROUND;plan['next_source_frontier']=facts['remaining'][0]
 (ROOT/BOOKS[1]).write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 origins=[]
 for i,n in enumerate(sorted(paths|set(BOOKS))):
  b=(ROOT/n).read_bytes();c='source/current/f%03d'%i+Path(n).suffix;save(OUT/c,b);origins.append(dict(path=n,copy=c,bytes=len(b),sha256=sha(b),changed_this_round=n not in old or old[n]!=b))
  if n in old and old[n]!=b:
   d=''.join(difflib.unified_diff(old[n].decode('utf-8-sig').splitlines(True),b.decode('utf-8-sig').splitlines(True),fromfile='before/'+n,tofile='current/'+n))
   if d:save(OUT/'diff'/('d%03d.diff'%i),d.encode())
 dump(OUT/'source/source-origins.json',origins)
 print(json.dumps(dict(protected_files=len(guarded),source_files=len(paths),source_segments=190,new_complete_routes=0)))

def enrich():
 for p in reports():save(OUT/'reports/raw'/(p.parent.name+'-'+p.name),p.read_bytes())
 receipt=dict(research_only=False,new_CPP=4,modified_CPP=2,source_segments=190,new_source_segments=1,new_complete_bidirectional_routes=0,whole_game_percent=None,current_catalog_source_files=len(read(CAT/'source-file-manifest.json')),owner_explicit_resume=True)
 for p in [reports()[0],reports()[2]]:
  v=read(p);v['native_item_control_source_frontier200']=read(OUT/'findings.json');v['parallel_agent_deliveries']=read(OUT/'parallel-agent-deliveries.json');v['current_round_source_delta']=receipt;p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 for p in [reports()[1],reports()[3]]:p.write_text((ROOT/DOC).read_text(encoding='utf-8')+'\n\nStatic accounting: '+json.dumps(receipt)+'\n',encoding='utf-8')
 dump(OUT/'reports/enrichment-receipt.json',receipt);print(json.dumps(receipt))

def seal():
 if (OUT/'manifest.json').exists() or (CAT/'manifest.json').exists():raise RuntimeError('Fresh200 seals required')
 rows,old=before();prior();guarded=protected(rows,old);deliveries,_,_=agents(old);root_native()
 if deliveries!=read(OUT/'parallel-agent-deliveries.json'):raise RuntimeError('Agent delivery drift')
 for r in read(OUT/'source/source-origins.json'):
  if matches(ROOT/r['path'],r)!=matches(OUT/r['copy'],r):raise RuntimeError('Final source drift')
 ledger=read(ROOT/BOOKS[1])
 if ledger['dual_client_source_segments'][:189]!=json.loads(old[BOOKS[1]])['dual_client_source_segments'] or len(ledger['dual_client_source_segments'])!=190:raise RuntimeError('Historical189/new190 drift')
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
 rm=dict(round=ROUND,**flags,before_files=len(rows),protected_files=len(guarded),source_segments=190,new_source_segments=1,new_CPP=4,modified_CPP=2,new_complete_bidirectional_routes=0,whole_game_percent=None,owner_explicit_resume=True,catalog_manifest_sha256=sha((CAT/'manifest.json').read_bytes()),files=inventory(OUT));dump(OUT/'manifest.json',rm)
 print(json.dumps(dict(root_members=len(rm['files']),catalog_members=len(cm['files']),root_sha256=sha((OUT/'manifest.json').read_bytes()),catalog_sha256=sha((CAT/'manifest.json').read_bytes()))))

if __name__=='__main__':
 if len(sys.argv)!=2 or sys.argv[1] not in ['account','enrich','seal']:raise RuntimeError('account/enrich/seal required')
 globals()[sys.argv[1]]()
