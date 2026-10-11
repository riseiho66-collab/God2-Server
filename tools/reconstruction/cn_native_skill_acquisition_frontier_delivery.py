"""Round198 immutable static acquisition evidence/accounting; no gameplay execution."""
from pathlib import Path
import json,sys,difflib
from .parallel_game_connection_frontier_delivery import ROOT,sha,read,save,dump,matches,inventory
BASE=ROOT/'artifacts/integration/packet-connections-20261006'
OUT=BASE/'cn-native-skill-acquisition-frontier-01'
CAT=BASE/'endpoint-catalog198'
ROUND='20261009-cn-native-skill-acquisition-frontier'
DOC='docs/research/cn-native-skill-acquisition-frontier-20261009.md'
BOOKS=['docs/PACKET_CONNECTION_GOAL_20261006.md',str((BASE/'packet-route-ledger.json').relative_to(ROOT).as_posix())]
WRITTEN=[DOC,'tools/reconstruction/cn_native_skill_acquisition_frontier_delivery.py','tools/reconstruction/cn_skill_acquisition_candidate198.py','tools/reconstruction/cn_native_acquisition_producer198.py','tools/reconstruction/dual_client_route_catalog.py']
AGENTS=['native-acquisition-producer','native-acquisition-history','shared-acquisition-store']
PINS={'cn-native-shared-skill-supply-01':'af9f03d7dd34eb3090c7aca09ede6d01f06169c01be00337bf43330193023bcd','endpoint-catalog197':'1dd12feffb28ebba24bdc6b3a9205fb24f1f237f5fac5d3129dcfb5c272ea0e4'}
AGENT_PINS=['0162e9e8d1f9da34b462046cac2f863502302fde81cd863ffea19e80b341dd8f','a4b09081729bc3787f745baa21750e8b8af07939678251a8bb1e85cfab10f4e8','533d35fe877285ccba89a09486a5eaa0c7340449fd2c5a5e3d0bdce57cc92bbb']

def reports():return [BASE/'packet-progress-latest.json',BASE/'packet-progress-latest.md',BASE/'round-reports'/(ROUND+'.json'),BASE/'round-reports'/(ROUND+'.md')]

def before():
 b=(OUT/'before-manifest.json').read_bytes()
 if sha(b)!='d1618c378d170d44bd6489e0f43dfb9dcb20333a20e1b80040002a30613b194d':raise RuntimeError('Original before198 drift')
 rows=json.loads(b)
 if len(rows)!=1415:raise RuntimeError('Before1415 required')
 return rows,{r['path']:matches(OUT/r['snapshot'],r) for r in rows}

def prior():
 total=0
 for n,pin in PINS.items():
  b=(BASE/n/'manifest.json').read_bytes()
  if sha(b)!=pin or b!=(OUT/'retained-prior'/n/'manifest.json').read_bytes():raise RuntimeError('Prior197 manifest drift')
  for r in json.loads(b)['files']:matches(BASE/n/r['path'],r);total+=1
 if total!=2381:raise RuntimeError('Full2381 prior members required')

def protected(rows,old):
 excluded=set(WRITTEN+BOOKS)|{p.relative_to(ROOT).as_posix() for p in reports()[:2]}
 guarded=[r for r in rows if r['path'] not in excluded]
 for r in guarded:
  if (ROOT/r['path']).read_bytes()!=old[r['path']]:raise RuntimeError('Protected source drift: '+r['path'])
 for r in rows:
  if r['path'].startswith('src/') and (ROOT/r['path']).read_bytes()!=old[r['path']]:raise RuntimeError('Research round changed gameplay source')
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
 elif not (row.get('retained_complete_in_place') is True or 'retained in place' in row.get('disposition','')):
  raise RuntimeError('Explicit full-hashed in-place disposition required')
 return raw

def raw_spans(folder,rows,pe):
 for r in rows:
  raw=matches(folder/r.get('copy',r.get('raw_copy')),r)
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
   if rel in BOOKS or rel.startswith('artifacts/') or rel=='tools/reconstruction/dual_client_route_catalog.py':raise RuntimeError('Mutable receipt is not source origin')
   if matches(p,r)!=matches(folder/r['copy'],r):raise RuntimeError('Agent actual source drift')
   paths.add(rel);records.append(dict(agent=n,path=rel,source=r))
  inputs=read(folder/'original-inputs.json')
  for r in inputs:original(folder,r)
  refs=[]
  if (folder/'native-input-references.json').exists():
   refs=read(folder/'native-input-references.json')
   for r in refs:original(folder,r)
  if n!='shared-acquisition-store':
   pe_rows=[r for r in inputs+refs if Path(r['path']).suffix.lower()=='.exe']
   if len(pe_rows)!=1:raise RuntimeError('Exactly one qualified PE origin required')
   pe=matches(Path(pe_rows[0]['path']),pe_rows[0])
   spanpath='refinement/native-spans.json' if n=='native-acquisition-producer' else 'native-spans.json'
   raw_spans(folder,read(folder/spanpath),pe)
  deliveries.append(dict(agent=n,seal_sha256=pin,findings=read(folder/'findings.json'),original_inputs=inputs,external_references=refs,current_source_origins=current,files=actual))
 return deliveries,paths,records

def root_native():
 folder=OUT/'root-native';origin=read(folder/'native-origin.json');pe=matches(Path(origin['path']),origin)
 if origin['full_file_copied'] or not origin['full_file_hashed']:raise RuntimeError('Bounded full-hashed input scope required')
 raw_spans(folder,read(folder/'span-manifest.json'),pe)
 for r in read(folder/'original-inputs.json'):original(folder,r)

def account():
 if (OUT/'findings.json').exists():raise RuntimeError('Fresh198 only')
 rows,old=before();prior();guarded=protected(rows,old);deliveries,paths,records=agents();root_native()
 cap=read(OUT/'policy/capacity-before-final-account.json')
 if cap['unreadable_count'] or not cap['under_limit']:raise RuntimeError('Whole-project capacity required')
 paths|=set(WRITTEN)
 ledger=read(ROOT/BOOKS[1]);previous=json.loads(old[BOOKS[1]])
 if ledger['dual_client_source_segments']!=previous['dual_client_source_segments'] or len(ledger['dual_client_source_segments'])!=188:raise RuntimeError('Historical188 changed')
 facts=dict(round=ROUND,research_only=True,completed_parallel_agents=3,new_Cplusplus_source_files_added=0,existing_Cplusplus_source_files_modified=0,new_source_segments=0,source_segments=188,new_packet_values=0,new_phase_bindings=0,new_complete_bidirectional_routes=0,whole_game_completion_percent=None,whole_game_denominator=None,source_paths=sorted(paths),
  skill_books=386,inventory_direct_C25=367,inventory_confirmation_3B=19,shortcut_books_C26=True,C25_body3_is_original_arg8_high_BYTE=True,C25_third_argument_ignored=True,C26_final_body_BYTE_unwritten=True,
  root_candidate_findings=read(OUT/'root-native/findings.json'),
  source_conclusion='Pinned actual producer operands and source-domain relationships qualified; book learning issuer, confirmation/custody/consume/store/full replies still OPEN. No gameplay source changed or full route completed.',
  scope_notes=['C25 precise bag caller highBYTE zero is a scoped alias fact, not global padding. C26 targetWORD remains native namespace, not common identity.','Parsed F1 mask0x04 and0x08 clear; avoid ambiguous bit4 notation in retained source evidence.','Lua book catalog is a mutable value snapshot of qualified source data, not a frozen or unforgeable Lua capability.','Existing selected TW supply admission reaches Lua CUSTOM inventory/resource CAS/replies; its MED02/item3101 domain excludes skill books. This is newly traced existing source, not newly connected gameplay.','Preborn81/83 actual raw issued choice transport is not qualified creation/learning semantics.','Full original file hashing is not full semantic recovery; bounded capture bytes are not globally unique new coverage.'],
  remaining=['Trace actual saved modal3B item/slot confirmation event and typed emitter without entering formatter/render interiors.','Qualify native owned subject identity, true learned grant, book debit/cost/save/current issuer and ONE common durable transaction with full replies.','Finish all TW/CN/web phases/states/variants and common64/stack99 wire/object/display before comprehensive build/tests/repair/release.'],
  build_run=False,tests_run=False,native_execution=False,runtime_run=False,codec_execution=False,database_access=False,SQL_run=False,deployed=False,owner_stop_after_this_round=True)
 dump(OUT/'parallel-agent-deliveries.json',deliveries);dump(OUT/'source/reviewed-current-source-records.json',records);dump(OUT/'findings.json',facts)
 ledger['native_skill_acquisition_frontier198']=facts
 plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND;plan['owner_requested_stop_after_work_round']=ROUND;plan['next_source_frontier']=facts['remaining'][0]
 (ROOT/BOOKS[1]).write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 origins=[]
 for i,n in enumerate(sorted(paths|set(BOOKS))):
  b=(ROOT/n).read_bytes();c='source/current/f%03d'%i+Path(n).suffix;save(OUT/c,b);origins.append(dict(path=n,copy=c,bytes=len(b),sha256=sha(b),changed_this_round=n not in old or old[n]!=b))
  if n in old and old[n]!=b:
   d=''.join(difflib.unified_diff(old[n].decode('utf-8-sig').splitlines(True),b.decode('utf-8-sig').splitlines(True),fromfile='before/'+n,tofile='current/'+n))
   if d:save(OUT/'diff'/('d%03d.diff'%i),d.encode())
 dump(OUT/'source/source-origins.json',origins)
 print(json.dumps(dict(protected_files=len(guarded),source_files=len(paths),source_segments=188,new_complete_routes=0)))

def enrich():
 for p in reports():save(OUT/'reports/raw'/(p.parent.name+'-'+p.name),p.read_bytes())
 receipt=dict(research_only=True,new_CPP=0,modified_CPP=0,source_segments=188,new_source_segments=0,new_complete_bidirectional_routes=0,whole_game_percent=None,current_catalog_source_files=len(read(CAT/'source-file-manifest.json')),owner_stop_after_this_round=True)
 for p in [reports()[0],reports()[2]]:
  v=read(p);v['native_skill_acquisition_frontier198']=read(OUT/'findings.json');v['parallel_agent_deliveries']=read(OUT/'parallel-agent-deliveries.json');v['current_round_source_delta']=receipt;p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 for p in [reports()[1],reports()[3]]:p.write_text((ROOT/DOC).read_text(encoding='utf-8')+'\n\nStatic accounting: '+json.dumps(receipt)+'\n',encoding='utf-8')
 dump(OUT/'reports/enrichment-receipt.json',receipt);print(json.dumps(receipt))

def seal():
 if (OUT/'manifest.json').exists() or (CAT/'manifest.json').exists():raise RuntimeError('Fresh198 seals required')
 rows,old=before();prior();guarded=protected(rows,old);deliveries,_,_=agents();root_native()
 if deliveries!=read(OUT/'parallel-agent-deliveries.json'):raise RuntimeError('Agent delivery drift')
 for r in read(OUT/'source/source-origins.json'):
  if matches(ROOT/r['path'],r)!=matches(OUT/r['copy'],r):raise RuntimeError('Final source drift')
 ledger=read(ROOT/BOOKS[1])
 if ledger['dual_client_source_segments']!=json.loads(old[BOOKS[1]])['dual_client_source_segments']:raise RuntimeError('Source188 historical drift')
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
 flags=dict(sealed=True,method='STATIC_SOURCE_RESEARCH_ONLY',build_run=False,tests_run=False,native_execution=False,runtime_run=False,database_access=False,deployed=False)
 cm=dict(round=CAT.name,**flags,current_source_files=len(sources),files=inventory(CAT));dump(CAT/'manifest.json',cm)
 rm=dict(round=ROUND,**flags,before_files=len(rows),protected_files=len(guarded),source_segments=188,new_source_segments=0,new_CPP=0,modified_CPP=0,new_complete_bidirectional_routes=0,whole_game_percent=None,owner_stop_after_this_round=True,catalog_manifest_sha256=sha((CAT/'manifest.json').read_bytes()),files=inventory(OUT));dump(OUT/'manifest.json',rm)
 print(json.dumps(dict(root_members=len(rm['files']),catalog_members=len(cm['files']),root_sha256=sha((OUT/'manifest.json').read_bytes()),catalog_sha256=sha((CAT/'manifest.json').read_bytes()))))

if __name__=='__main__':
 if len(sys.argv)!=2 or sys.argv[1] not in ['account','enrich','seal']:raise RuntimeError('account/enrich/seal required')
 globals()[sys.argv[1]]()
