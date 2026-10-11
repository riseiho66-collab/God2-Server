"""Round196 static originals/accounting only; no gameplay/build/DB execution."""
from pathlib import Path
import json,sys,difflib
from .parallel_game_connection_frontier_delivery import ROOT,sha,read,save,dump,matches,inventory
BASE=ROOT/'artifacts/integration/packet-connections-20261006'
OUT=BASE/'cn-native-learned-skill-event-frontier-01'
CAT=BASE/'endpoint-catalog196'
ROUND='20261009-cn-native-learned-skill-event-frontier'
DOC='docs/research/cn-native-learned-skill-event-frontier-20261009.md'
BOOKS=['docs/PACKET_CONNECTION_GOAL_20261006.md','artifacts/integration/packet-connections-20261006/packet-route-ledger.json']
WRITTEN=['src/core/Application.cpp', 'src/core/SharedWorldHostPlan.h', 'src/core/SharedTaiwanNativeWorldHostPlan.cpp', 'src/cn/net/SharedCredentialServer.h', 'src/cn/net/SharedCredentialServer.cpp']+[DOC,'tools/reconstruction/cn_native_learned_skill_event_frontier_delivery.py','tools/reconstruction/dual_client_route_catalog.py',
 'tools/reconstruction/cn_native_learned_skill_event_frontier196.py','tools/reconstruction/cn_learned_event_history_frontier196.py','tools/reconstruction/shared_learned_event_store_frontier196.py']
AGENTS=['cn-learned-event-native-frontier','cn-learned-event-history-frontier','shared-learned-event-store-frontier']
PINS={'cn-native-learned-skill-owner-frontier-01':'e388a51eba010b23f7e863b1e26d1c5676d327f8e68700384bb0d178944a98b8','endpoint-catalog195':'e70991b250937dfc8f355f8956c1e72e85487579c1f633257027cca0ad2206c4'}
GAME=['src/core/Application.cpp', 'src/core/SharedWorldHostPlan.h', 'src/core/SharedTaiwanNativeWorldHostPlan.cpp', 'src/cn/net/SharedCredentialServer.h', 'src/cn/net/SharedCredentialServer.cpp']

def reports():return [BASE/'packet-progress-latest.json',BASE/'packet-progress-latest.md',BASE/'round-reports'/(ROUND+'.json'),BASE/'round-reports'/(ROUND+'.md')]
def before():
 raw=(OUT/'before-manifest.json').read_bytes()
 if sha(raw)!='953264e0a7624fbdc615fcd8c9d964460fd4287c2c505f4275c1d4b26cbb2c4d':raise RuntimeError('Before196 drift')
 rows=json.loads(raw)
 if len(rows)!=1403:raise RuntimeError('Before1403 required')
 return rows,{r['path']:matches(OUT/r['snapshot'],r) for r in rows}
def prior():
 count=0
 for name,pin in PINS.items():
  p=BASE/name/'manifest.json';raw=p.read_bytes()
  if sha(raw)!=pin or raw!=(OUT/'retained-prior'/name/'manifest.json').read_bytes():raise RuntimeError('Prior195 drift')
  for row in json.loads(raw)['files']:matches(BASE/name/row['path'],row);count+=1
 if count!=2611:raise RuntimeError('Full prior1952611 members required')
def protected(rows,old):
 excluded=set(WRITTEN+BOOKS)|{p.relative_to(ROOT).as_posix() for p in reports()[:2]}
 guarded=[r for r in rows if r['path'] not in excluded]
 for row in guarded:
  if (ROOT/row['path']).read_bytes()!=old[row['path']]:raise RuntimeError('Protected current drift: '+row['path'])
 # Only the five assigned source definitions may change.
 for row in rows:
  if row['path'].startswith('src/') and Path(row['path']).suffix in ('.h','.cpp') and row['path'] not in GAME and (ROOT/row['path']).read_bytes()!=old[row['path']]:raise RuntimeError('Unassigned C++ drift')
 return guarded
def agents():
 from . import cn_native_battle_skill_publication_source_delivery as utility
 # This utility only reads full manifests/originals. Rebind its file paths for196.
 utility.OUT=OUT;utility.AGENTS=AGENTS;utility.BOOKS=BOOKS
 # Agent's immutable seal omitted one nested historical seal by basename.
 # Qualify that exact full file against pinned195, never ignore arbitrary extras.
 folder=OUT/'agents/cn-learned-event-native-frontier'
 historical=folder/'retained195/seal.json'
 reference=BASE/'cn-native-learned-skill-owner-frontier-01/agents/cn-native-learned-subject-frontier/seal.json'
 raw=historical.read_bytes()
 if sha(raw)!='91848e42ed1b7bba15312d77f59a8a61862ba582bf4e1c8e4799cd0615a7b118' or raw!=reference.read_bytes():raise RuntimeError('Exact immutable historical agent seal required')
 extra=dict(path='retained195/seal.json',bytes=len(raw),sha256=sha(raw))
 original_inventory=utility.inventory
 def qualified_inventory(path):
  rows=original_inventory(path)
  if Path(path)==folder:
   if [r for r in rows if r['path']==extra['path']]!=[extra]:raise RuntimeError('Historical nested seal scope drift')
   return [r for r in rows if r['path']!=extra['path']]
  return rows
 utility.inventory=qualified_inventory
 try:deliveries,paths,records=utility.agent_records()
 finally:utility.inventory=original_inventory
 for delivery in deliveries:
  if delivery['agent']=='cn-learned-event-native-frontier':
   delivery['files']=original_inventory(folder)
   delivery['explicit_historical_seal_supplement']=extra
   delivery['scope']='Original seal90 members preserved; actual inventory92 includes top seal and this exact195 historical seal. No other unlisted member accepted.'
 copy=OUT/'qualification/retained195-native-agent-seal.json'
 if copy.exists():
  if copy.read_bytes()!=raw:raise RuntimeError('Retained historical seal addendum drift')
 else:
  save(copy,raw)
  dump(OUT/'qualification/agent-inventory-addendum.json',dict(reason='Root full inventory found one omitted nested seal after agent final report; exact basename filtering issue qualified separately',original_agent_seal_edited=False,actual_complete_files=92,original_listed_members=90,top_level_seal_files=1,extra=extra,reference=str(reference),copy=copy.relative_to(OUT).as_posix(),all_other_manifest_members_and_actual_current_inputs_required=True))
 return deliveries,paths,records
def external_inputs():
 for row in read(OUT/'root-native-original-inputs.json'):
  if matches(Path(row['path']),row)!=matches(OUT/row['copy'],row):raise RuntimeError('Root complete native original drift')
 for i,row in enumerate(read(OUT/'web-peer/original-inputs.json')):
  raw=matches(OUT/row['copy'],row)
  if i and Path(row['path']).read_bytes()!=raw:raise RuntimeError('Immutable named peer report drift')

def account():
 if (OUT/'findings.json').exists() or (OUT/'manifest.json').exists():raise RuntimeError('Fresh196 only')
 rows,old=before();prior();external_inputs();guarded=protected(rows,old);deliveries,paths,records=agents()
 capacity=read(OUT/'policy/capacity-before-final-account.json')
 if capacity['unreadable_count'] or not capacity['under_limit']:raise RuntimeError('Current whole project capacity required')
 review=read(OUT/'root-read-source-origins.json')
 for row in review:
  if matches(ROOT/row['path'],row)!=matches(OUT/row['copy'],row):raise RuntimeError('Root context drift')
  paths.add(row['path'])
 ledger=read(ROOT/BOOKS[1]);previous=json.loads(old[BOOKS[1]])
 if ledger['dual_client_source_segments']!=previous['dual_client_source_segments'] or len(ledger['dual_client_source_segments'])!=186:raise RuntimeError('Prior186 unchanged source chains required')
 if ledger['world_unconnected_gameplay_opcodes']!=previous['world_unconnected_gameplay_opcodes']:raise RuntimeError('Gameplay classifications changed')
 paths|=set(WRITTEN)
 facts=dict(round=ROUND,previous_goal_turn_classification='PROGRESS_COMPLETED195',completed_parallel_agents=3,research_only=False,
  new_Cplusplus_source_files_added=0,existing_Cplusplus_source_files_modified=5,new_source_segments=1,source_segments=187,
  actual_application_same_skill_reader_factory_bindings=2,new_native_owner_origin_relations=0,new_packet_values=0,new_phase_bindings=0,new_complete_bidirectional_routes=0,
  whole_game_route_total=None,whole_game_completed_routes=None,whole_game_completion_percent=None,
  formal_application_hosted=False,actual_world_plan_selected_in_Main=False,source_paths=sorted(paths),
  agent_findings={d['agent']:d['findings'] for d in deliveries},protected_files=len(guarded),
  source_conclusion='Same actual Application SqliteDatabase NativeSkillCatalog reader reaches TW Context factory/exact Owner identity and CN explicit constructor/Context/source factory. Old aggregate/constructors keep absent pointer; no query/import/default issuer or learned grant. Actual CN all453 pinned qualification and real learned/cost/store/rules/Main remain required.',
  storage_conclusion='Existing TW store_deity and inventory-resource consumption own separate transactions/COMMITs. They cannot be joined as an atomic native learning mutation. Actual common learned plus book custody and durable event remains OPEN.',
  remaining=['Genuine native common learned subject/core/store grant and independent actual world/battle event/order/profile mapping','Primary/secondary list current, actual actor/context/target/formation/range/cost/once settlement/full replies/Main','Whole TW-CN-web phases/variants/deferred denominator and all gameplay;64bit wire/object/display,stack99,sharedtables,frozenfeatures','All source connections before comprehensive builds/tests/verification/repair/recovery/release'],
  build_run=False,tests_run=False,runtime_run=False,native_execution=False,Cplusplus_source_run=False,Lua_run=False,codec_execution=False,Windows_API_run=False,database_access=False,SQL_run=False,deployed=False)
 dump(OUT/'parallel-agent-deliveries.json',deliveries);dump(OUT/'source/reviewed-current-source-records.json',records);dump(OUT/'findings.json',facts)
 ledger['native_learned_skill_event_frontier196']=facts
 ledger['dual_client_source_segments'].append(dict(name=OUT.name,round=ROUND,version_scope='TW-CN-Application-same-shared-SQLite-native-skill-reader-factories',status=facts['source_conclusion'],source_paths=sorted(paths),native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,tw_source_owner_chains_added=0,formal_application_hosted=False,complete_gameplay_routes_added=0,evidence=OUT.relative_to(ROOT).as_posix(),remaining=facts['remaining']))
 plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
 plan['next_source_frontier']='Use exact Application shared reader to qualify actual CN provider/catalog; implement genuine single atomic learned/book custody/save/durable events only with actual native issuer/rules. WORLD30/reset,34/35 and87 histories stay independent; full grant/core/replies/Main and all game routes remain OPEN.'
 (ROOT/BOOKS[1]).write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 origins=[]
 for i,n in enumerate(sorted(paths|set(BOOKS))):
  raw=(ROOT/n).read_bytes();copy='source/current/f%03d'%i+Path(n).suffix;save(OUT/copy,raw)
  origins.append(dict(path=n,copy=copy,bytes=len(raw),sha256=sha(raw),changed_this_round=n not in old or old[n]!=raw))
  if n in old and old[n]!=raw:
   diff=''.join(difflib.unified_diff(old[n].decode('utf-8-sig').splitlines(True),raw.decode('utf-8-sig').splitlines(True),fromfile='before/'+n,tofile='current/'+n))
   if diff:save(OUT/'diff'/('d%03d.diff'%i),diff.encode())
 dump(OUT/'source/source-origins.json',origins)
 print(json.dumps(dict(protected_files=len(guarded),source_files=len(paths),source_segments=187,new_complete_routes=0)))
def enrich():
 for p in reports():save(OUT/'reports/raw'/(p.parent.name+'-'+p.name),p.read_bytes())
 sources=read(CAT/'source-file-manifest.json');previous=read(BASE/'endpoint-catalog195/source-file-manifest.json')
 receipt=dict(research_only=False,new_CPP=0,modified_CPP=5,source_segments=187,new_source_segments=1,new_complete_bidirectional_routes=0,whole_game_percent=None,current_catalog_source_files=len(sources),new_catalog_source_paths=len(set(sources)-set(previous)))
 for p in (reports()[0],reports()[2]):
  v=read(p);v['native_learned_skill_event_frontier196']=read(OUT/'findings.json');v['parallel_agent_deliveries']=read(OUT/'parallel-agent-deliveries.json');v['current_round_source_delta']=receipt;p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 for p in (reports()[1],reports()[3]):p.write_text((ROOT/DOC).read_text(encoding='utf-8')+'\n\nStatic accounting: '+json.dumps(receipt)+'\n',encoding='utf-8')
 dump(OUT/'reports/enrichment-receipt.json',receipt);print(json.dumps(receipt))
def seal():
 if (OUT/'manifest.json').exists() or (CAT/'manifest.json').exists():raise RuntimeError('Fresh seals required')
 rows,old=before();prior();external_inputs();guarded=protected(rows,old);deliveries,_,_=agents()
 if deliveries!=read(OUT/'parallel-agent-deliveries.json'):raise RuntimeError('Agent drift')
 for row in read(OUT/'source/source-origins.json'):
  if matches(ROOT/row['path'],row)!=matches(OUT/row['copy'],row):raise RuntimeError('Final original drift')
 ledger=read(ROOT/BOOKS[1]);previous=json.loads(old[BOOKS[1]])
 if ledger['dual_client_source_segments'][:186]!=previous['dual_client_source_segments'] or len(ledger['dual_client_source_segments'])!=187:raise RuntimeError('Historical186 or new187 changed')
 sources=read(CAT/'source-file-manifest.json')
 for n,row in sources.items():matches(ROOT/n,row)
 entries=[r for r in read(CAT/'input-manifest.json') if r['input']=='source-ledger']
 if len(entries)!=1 or matches(CAT/entries[0]['snapshot'],entries[0])!=(ROOT/BOOKS[1]).read_bytes():raise RuntimeError('Catalog input ledger drift')
 a,b,c,d=reports()
 if a.read_bytes()!=c.read_bytes() or b.read_bytes()!=d.read_bytes():raise RuntimeError('Final report mismatch')
 v=read(a)
 if v['round']!=ROUND or v['route_ledger_sha256']!=sha((ROOT/BOOKS[1]).read_bytes()) or v['dual_client_endpoint_catalog']['summary']!=read(CAT/'summary.json'):raise RuntimeError('Report identity/catalog drift')
 for k in ('whole_game_distinct_packet_count','whole_game_completed_route_count','whole_game_completion_percent'):
  if v['counts'][k] is not None:raise RuntimeError('False denominator')
 for p in reports():save(OUT/'reports/final'/(p.parent.name+'-'+p.name),p.read_bytes())
 flags=dict(sealed=True,method='STATIC_SOURCE_INTEGRATION_ONLY',build_run=False,tests_run=False,native_execution=False,runtime_run=False,codec_execution=False,database_access=False,SQL_run=False,deployed=False)
 cm=dict(round=CAT.name,**flags,current_source_files=len(sources),files=inventory(CAT));dump(CAT/'manifest.json',cm)
 rm=dict(round=ROUND,**flags,before_files=len(rows),protected_files=len(guarded),source_segments=187,new_source_segments=1,new_CPP=0,modified_CPP=5,new_complete_bidirectional_routes=0,whole_game_percent=None,catalog_manifest_sha256=sha((CAT/'manifest.json').read_bytes()),files=inventory(OUT));dump(OUT/'manifest.json',rm)
 print(json.dumps(dict(before_files=len(rows),protected_files=len(guarded),catalog_source_files=len(sources),root_members=len(rm['files']),catalog_members=len(cm['files']),root_sha256=sha((OUT/'manifest.json').read_bytes()),catalog_sha256=sha((CAT/'manifest.json').read_bytes()))))
if __name__=='__main__':
 if len(sys.argv)!=2 or sys.argv[1] not in ('account','enrich','seal'):raise RuntimeError('account/enrich/seal required')
 globals()[sys.argv[1]]()
