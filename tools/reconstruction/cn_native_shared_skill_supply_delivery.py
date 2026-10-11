"""Round197 static file/source accounting only; no game/build/codec/DB."""
from pathlib import Path
import json,sys,difflib
from .parallel_game_connection_frontier_delivery import ROOT,sha,read,save,dump,matches,inventory
BASE=ROOT/'artifacts/integration/packet-connections-20261006'
OUT=BASE/'cn-native-shared-skill-supply-01'
CAT=BASE/'endpoint-catalog197'
ROUND='20261009-cn-native-shared-skill-supply'
DOC='docs/research/cn-native-shared-skill-supply-20261009.md'
GAME=['src/cn/net/SharedCredentialServer.h','src/cn/net/SharedCredentialServer.cpp']
BOOKS=['docs/PACKET_CONNECTION_GOAL_20261006.md','artifacts/integration/packet-connections-20261006/packet-route-ledger.json']
WRITTEN=GAME+[DOC,'tools/reconstruction/cn_native_shared_skill_supply_delivery.py','tools/reconstruction/dual_client_route_catalog.py']
AGENTS=['native-catalog-supply','server-catalog-owner','shared-store-supply','shared-store-supply-root-context']
PINS={'cn-native-learned-skill-event-frontier-01':'ee78f1e769cf2b4cb21948575189e19c3715de8803a1745a38f78bd7cb1914ec','endpoint-catalog196':'712927797a25a2d3cab0e58ffca8ea02c9c33ad268c87052ddd4d7c0f85301d8'}
def reports():return [BASE/'packet-progress-latest.json',BASE/'packet-progress-latest.md',BASE/'round-reports'/(ROUND+'.json'),BASE/'round-reports'/(ROUND+'.md')]
def before():
 b=(OUT/'before-manifest.json').read_bytes()
 if sha(b)!='ba795771759736124a91913a26acdd2da9a94c838ab0ce29d122b3deb8535ddc':raise RuntimeError('Before197 drift')
 rows=json.loads(b)
 if len(rows)!=1413:raise RuntimeError('Before1413 required')
 return rows,{r['path']:matches(OUT/r['snapshot'],r) for r in rows}
def prior():
 count=0
 for name,pin in PINS.items():
  b=(BASE/name/'manifest.json').read_bytes()
  if sha(b)!=pin or b!=(OUT/'retained-prior'/name/'manifest.json').read_bytes():raise RuntimeError('Prior196 drift')
  for r in json.loads(b)['files']:matches(BASE/name/r['path'],r);count+=1
 if count!=2598:raise RuntimeError('Full2598 prior members required')
def protected(rows,old):
 excluded=set(WRITTEN+BOOKS)|{p.relative_to(ROOT).as_posix() for p in reports()[:2]}
 guarded=[r for r in rows if r['path'] not in excluded]
 for r in guarded:
  if (ROOT/r['path']).read_bytes()!=old[r['path']]:raise RuntimeError('Protected source drift: '+r['path'])
 for r in rows:
  if r['path'].startswith('src/') and Path(r['path']).suffix in ('.h','.cpp') and r['path'] not in GAME and (ROOT/r['path']).read_bytes()!=old[r['path']]:raise RuntimeError('Unassigned C++ drift')
 return guarded
def agents():
 from . import cn_native_battle_skill_publication_source_delivery as utility
 utility.OUT=OUT;utility.AGENTS=AGENTS;utility.BOOKS=BOOKS
 return utility.agent_records()
def external_inputs():
 for r in read(OUT/'web-peer/original-inputs.json'):
  if matches(Path(r['path']),r)!=matches(OUT/r['copy'],r):raise RuntimeError('Immutable named web source report drift')
def root_context():
 scopes={n:'Complete final current definition and full diff independently read; static source only' for n in GAME}
 scopes.update({n:'Complete definition read; no C++/SQL/codec/native execution' for n in ['src/cn/assets/CnNativeSkillCatalog.h','src/cn/assets/CnNativeSkillCatalog.cpp','src/cn/assets/CnSharedSkillCatalog.h','src/cn/assets/CnSharedSkillCatalog.cpp','src/cn/assets/CnNativeSkillCatalogImport.h','src/cn/assets/CnNativeSkillCatalogImport.cpp','src/db/NativeSkillCatalog.cpp','src/db/SqliteDatabase.h','src/cn/auth/SharedLoginComposition.h','src/cn/auth/SharedLoginComposition.cpp']})
 rows,old=before();origins=[]
 for i,(n,scope) in enumerate(scopes.items()):
  b=(ROOT/n).read_bytes();c='root-context/f%02d'%i+Path(n).suffix;save(OUT/c,b);origins.append(dict(path=n,copy=c,bytes=len(b),sha256=sha(b),semantic_scope=scope))
  if n in GAME:
   if old[n]==b:raise RuntimeError('Two actual modified definitions required')
   diff=''.join(difflib.unified_diff(old[n].decode('utf-8-sig').splitlines(True),b.decode('utf-8-sig').splitlines(True),fromfile='before/'+n,tofile='current/'+n));save(OUT/'root-diff'/('f%02d.diff'%i),diff.encode())
 dump(OUT/'root-read-source-origins.json',origins)
 print(json.dumps(dict(root_actual_sources=len(origins),modified_CPP=2)))
def account():
 if (OUT/'findings.json').exists():raise RuntimeError('Fresh197 only')
 rows,old=before();prior();external_inputs();guarded=protected(rows,old);deliveries,paths,records=agents()
 capacity=read(OUT/'policy/capacity-before-final-account.json')
 if capacity['unreadable_count'] or not capacity['under_limit']:raise RuntimeError('Current whole-project capacity required')
 root=read(OUT/'root-read-source-origins.json')
 for r in root:
  if matches(ROOT/r['path'],r)!=matches(OUT/r['copy'],r):raise RuntimeError('Root actual source drift')
 paths|=set(WRITTEN)|{r['path'] for r in root}
 ledger=read(ROOT/BOOKS[1])
 if len(ledger['dual_client_source_segments'])!=187:raise RuntimeError('Historical187 expected')
 facts=dict(completed_parallel_agents=3,agent_sealed_deliveries=len(deliveries),research_only=False,new_Cplusplus_source_files_added=0,existing_Cplusplus_source_files_modified=2,new_source_segments=1,source_segments=188,new_packet_values=0,new_phase_bindings=0,new_complete_bidirectional_routes=0,whole_game_completion_percent=None,whole_game_denominator=None,source_paths=sorted(paths),actual_CN_shared_catalog_supplier_connections_added=1,
  source_conclusion='Explicit pinned native provider -> same actual Application shared SQLite reader -> all453 declared definitions bind before existing controllers factory -> strong State owner and Context shared_ptr -> constructor/start/credential native Current guards; legacy absence preserved, no import/TW fallback/learned grants.',
  current_scope='Native current and game-owner thread only; bind reads every declared row but is not an atomic all-row DB snapshot or extra-row count; later lookups qualify their actual row. Same reader/connection must outlive game drain. External observer must not yield/reenter/mutate store; no universal fence claimed.',
  remaining=['Actual Main plan must select a true pinned provider, explicit populated same-store data, all native login/world sources; no default activation','Genuine common subject/learned native issuer/rules and ONE same-store learned+book custody/debit+durable event transaction; full independent WORLD34/35 and battle87 publications','Actor/context/grant/target/formation/range/cost/once settlement/full replies and all TW-CN-web gameplay phase/state/variant/deferred routes','Whole-game denominator remains unknown; common64 explicit wire/object/display,stack99,sharedtables/frozenfeatures and later comprehensive builds/tests/repair/recovery/release'],
  build_run=False,tests_run=False,runtime_run=False,native_execution=False,Cplusplus_source_run=False,Lua_run=False,codec_execution=False,Windows_API_run=False,database_access=False,SQL_run=False,deployed=False)
 dump(OUT/'parallel-agent-deliveries.json',deliveries);dump(OUT/'source/reviewed-current-source-records.json',records);dump(OUT/'findings.json',facts)
 ledger['native_shared_skill_supply197']=facts
 ledger['dual_client_source_segments'].append(dict(name=OUT.name,round=ROUND,version_scope='CN-pinned-definitions-on-actual-Application-common-SQLite-reader',status=facts['source_conclusion'],source_paths=sorted(paths),native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,tw_source_owner_chains_added=0,formal_application_hosted=False,complete_gameplay_routes_added=0,evidence=OUT.relative_to(ROOT).as_posix(),remaining=facts['remaining']))
 plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND;plan['next_source_frontier']='Use strong exact qualified CN shared definitions in real native skill acquisition/common actor owner; implement one same-store learned/book/durable event mutation and full native world/battle replies with real rules. No definition/flag grants, automatic history mirrors or guessed Main plan.'
 (ROOT/BOOKS[1]).write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 origins=[]
 for i,n in enumerate(sorted(paths|set(BOOKS))):
  b=(ROOT/n).read_bytes();c='source/current/f%03d'%i+Path(n).suffix;save(OUT/c,b);origins.append(dict(path=n,copy=c,bytes=len(b),sha256=sha(b),changed_this_round=n not in old or old[n]!=b))
  if n in old and old[n]!=b:
   diff=''.join(difflib.unified_diff(old[n].decode('utf-8-sig').splitlines(True),b.decode('utf-8-sig').splitlines(True),fromfile='before/'+n,tofile='current/'+n))
   if diff:save(OUT/'diff'/('d%03d.diff'%i),diff.encode())
 dump(OUT/'source/source-origins.json',origins)
 print(json.dumps(dict(protected_files=len(guarded),source_files=len(paths),source_segments=188,new_complete_routes=0)))
def enrich():
 for p in reports():save(OUT/'reports/raw'/(p.parent.name+'-'+p.name),p.read_bytes())
 sources=read(CAT/'source-file-manifest.json');old=read(BASE/'endpoint-catalog196/source-file-manifest.json')
 receipt=dict(research_only=False,new_CPP=0,modified_CPP=2,source_segments=188,new_source_segments=1,new_complete_bidirectional_routes=0,whole_game_percent=None,current_catalog_source_files=len(sources),new_catalog_source_paths=len(set(sources)-set(old)))
 for p in (reports()[0],reports()[2]):
  v=read(p);v['native_shared_skill_supply197']=read(OUT/'findings.json');v['parallel_agent_deliveries']=read(OUT/'parallel-agent-deliveries.json');v['current_round_source_delta']=receipt;p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 for p in (reports()[1],reports()[3]):p.write_text((ROOT/DOC).read_text(encoding='utf-8')+'\n\nStatic accounting: '+json.dumps(receipt)+'\n',encoding='utf-8')
 dump(OUT/'reports/enrichment-receipt.json',receipt);print(json.dumps(receipt))
def seal():
 if (OUT/'manifest.json').exists() or (CAT/'manifest.json').exists():raise RuntimeError('Fresh197 seals required')
 rows,old=before();prior();external_inputs();guarded=protected(rows,old);deliveries,_,_=agents()
 if deliveries!=read(OUT/'parallel-agent-deliveries.json'):raise RuntimeError('Agent drift')
 for r in read(OUT/'source/source-origins.json'):
  if matches(ROOT/r['path'],r)!=matches(OUT/r['copy'],r):raise RuntimeError('Final source drift')
 ledger=read(ROOT/BOOKS[1]);previous=json.loads(old[BOOKS[1]])
 if ledger['dual_client_source_segments'][:187]!=previous['dual_client_source_segments'] or len(ledger['dual_client_source_segments'])!=188:raise RuntimeError('Historical187 or new188 drift')
 sources=read(CAT/'source-file-manifest.json')
 for n,r in sources.items():matches(ROOT/n,r)
 entries=[r for r in read(CAT/'input-manifest.json') if r['input']=='source-ledger']
 if len(entries)!=1 or matches(CAT/entries[0]['snapshot'],entries[0])!=(ROOT/BOOKS[1]).read_bytes():raise RuntimeError('Catalog ledger drift')
 a,b,c,d=reports()
 if a.read_bytes()!=c.read_bytes() or b.read_bytes()!=d.read_bytes():raise RuntimeError('Final report mismatch')
 v=read(a)
 if v['round']!=ROUND or v['route_ledger_sha256']!=sha((ROOT/BOOKS[1]).read_bytes()) or v['dual_client_endpoint_catalog']['summary']!=read(CAT/'summary.json'):raise RuntimeError('Report/catalog identity drift')
 for k in ('whole_game_distinct_packet_count','whole_game_completed_route_count','whole_game_completion_percent'):
  if v['counts'][k] is not None:raise RuntimeError('False denominator')
 for p in reports():save(OUT/'reports/final'/(p.parent.name+'-'+p.name),p.read_bytes())
 flags=dict(sealed=True,method='STATIC_SOURCE_INTEGRATION_ONLY',build_run=False,tests_run=False,native_execution=False,runtime_run=False,codec_execution=False,database_access=False,SQL_run=False,deployed=False)
 cm=dict(round=CAT.name,**flags,current_source_files=len(sources),files=inventory(CAT));dump(CAT/'manifest.json',cm)
 rm=dict(round=ROUND,**flags,before_files=len(rows),protected_files=len(guarded),source_segments=188,new_source_segments=1,new_CPP=0,modified_CPP=2,new_complete_bidirectional_routes=0,whole_game_percent=None,catalog_manifest_sha256=sha((CAT/'manifest.json').read_bytes()),files=inventory(OUT));dump(OUT/'manifest.json',rm)
 print(json.dumps(dict(before_files=len(rows),protected_files=len(guarded),catalog_source_files=len(sources),root_members=len(rm['files']),catalog_members=len(cm['files']),root_sha256=sha((OUT/'manifest.json').read_bytes()),catalog_sha256=sha((CAT/'manifest.json').read_bytes()))))
if __name__=='__main__':
 if len(sys.argv)!=2 or sys.argv[1] not in ('root_context','account','enrich','seal'):raise RuntimeError('root_context/account/enrich/seal required')
 globals()[sys.argv[1]]()
