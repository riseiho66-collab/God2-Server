"""Round208 static source accounting only; active TW-first source round; old five-round stop revoked."""
from pathlib import Path
import json,sys,difflib
from .parallel_game_connection_frontier_delivery import ROOT,sha,read,save,dump,matches,inventory
BASE=ROOT/'artifacts/integration/packet-connections-20261006'
OUT=BASE/'tw-first-route-closure-01';CAT=BASE/'endpoint-catalog208'
ROUND='20261009-tw-first-scalar-move-quantity-source'
DOC='docs/research/tw-first-scalar-move-quantity-source-20261009.md'
GAME=['src/handlers/InventoryMoveService.h','src/handlers/InventoryMoveService.cpp','src/db/SqliteInventoryMove.cpp','src/db/SqliteRecoveredCharacterRepository.h']
WRITTEN=GAME+[DOC,'AGENTS.md','docs/STACK_LIMIT_20261007.md','tools/reconstruction/tw_first_route_closure_source_delivery.py','tools/reconstruction/dual_client_route_catalog.py','tools/reconstruction/tw_native_frontier208.py']
BOOKS=['docs/PACKET_CONNECTION_GOAL_20261006.md',(BASE/'packet-route-ledger.json').relative_to(ROOT).as_posix()]
PINS={'cn-roster-skill-checkpoint-source-01':'a9d618866265fdbd6f6080c254e6627eb30ae4b27bab47f49b44a5f864441cd6','endpoint-catalog207':'8dfaf809602842f9e4737e5413a36f0fd9616b5a2c088800f5be4a4e7f236eaf'}

def reports():return [BASE/'packet-progress-latest.json',BASE/'packet-progress-latest.md',BASE/'round-reports'/(ROUND+'.json'),BASE/'round-reports'/(ROUND+'.md')]

def before():
 b=(OUT/'before-manifest.json').read_bytes()
 if sha(b)!='94ac71ffe47b106efd6b993a379d3612894e9c6b63b528474e455ed74ab8ccb1':raise RuntimeError('Actual before208 drift')
 rows=json.loads(b)
 if len(rows)!=1467:raise RuntimeError('1467 actual before sources required')
 return rows,{r['path']:matches(OUT/r['snapshot'],r) for r in rows}

def prior():
 count=0
 for n,pin in PINS.items():
  b=(BASE/n/'manifest.json').read_bytes()
  if sha(b)!=pin or b!=(OUT/'retained-prior'/n/'manifest.json').read_bytes():raise RuntimeError('Pinned207 seal drift')
  for r in json.loads(b)['files']:matches(BASE/n/r['path'],r);count+=1
 if count!=2496:raise RuntimeError('Full2496 retained207 members required')

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
 r=read(OUT/'actual-accounting-input207.json');matches(OUT/r['copy'],r);matches(Path(r['path']),r)

def reviewer():
 pins=read(OUT/'sealed-agent-pins.json');deliveries=[];paths=set()
 if len(pins)!=2:raise RuntimeError('Two actual208 bounded deliveries required')
 rows,old=before()
 for name in ['tw-native-frontier','tw-scalar-move-source-review']:
  folder=OUT/'agents'/name;b=(folder/'seal.json').read_bytes()
  if sha(b)!=pins[name]:raise RuntimeError('Actual208 seal drift')
  seal=json.loads(b);members=seal.get('files',seal.get('members'))
  if not isinstance(members,list):raise RuntimeError('Complete seal member list required')
  for r in members:matches(folder/r['path'],r)
  if {r['path'] for r in inventory(folder)}!={r['path'] for r in members}|{'seal.json'}:raise RuntimeError('Full actual208 agent inventory drift')
  current=read(folder/'current-source-origins.json')
  for r in current:
   p=Path(r['path']);p=p if p.is_absolute() else ROOT/p;rel=p.relative_to(ROOT).as_posix()
   artifact_tool=p==folder/'review_account.py'
   if (rel.startswith('artifacts/') and not artifact_tool) or rel in BOOKS:raise RuntimeError('Mutable receipt cannot be source original')
   if matches(p,r)!=matches(folder/r['copy'],r):raise RuntimeError('Actual final208 source drift')
   if not artifact_tool:paths.add(rel)
  refs=read(folder/'native-input-references.json') if (folder/'native-input-references.json').exists() else []
  if isinstance(refs,dict):
   if refs.get('new_inputs')!=[] or refs.get('new_raw_bytes')!=0:raise RuntimeError('Bounded208 retained-only native scope required')
   refs=refs['retained_evidence']
  if not isinstance(refs,list):raise RuntimeError('Actual retained native reference list required')
  for r in refs:
   if matches(Path(r['path']),r)!=matches(folder/r['copy'],r):raise RuntimeError('Actual retained native original/copy drift')
  if name=='tw-scalar-move-source-review':
   for r in read(folder/'original-inputs.json'):
    p=Path(r['path']);p=p if p.is_absolute() else ROOT/p;rel=p.relative_to(ROOT).as_posix()
    raw=matches(OUT/r['original'],r)
    if rel not in old or raw!=old[rel] or matches(folder/r['copy'],r)!=raw:raise RuntimeError('Full before208 source drift')
   for r in read(folder/'final-original-inputs.json'):
    p=Path(r['path']);p=p if p.is_absolute() else ROOT/p
    if matches(p,r)!=matches(folder/r['copy'],r):raise RuntimeError('Full final208 source drift')
  if name=='tw-native-frontier':
   for r in read(folder/'original-inputs.json'):
    if matches(Path(r['path']),r)!=matches(folder/r['copy'],r):raise RuntimeError('Actual native207 complete original drift')
  deliveries.append(dict(agent=name,seal_sha256=sha(b),findings=read(folder/'findings.json'),current_source_origins=current,files=inventory(folder)))
 return deliveries,paths

def account():
 if (OUT/'findings.json').exists():raise RuntimeError('Fresh208 only')
 rows,old=before();prior();guarded=protected(rows,old);original_copies();reviews,paths=reviewer()
 cap=read(OUT/'policy/capacity-before-final-account.json')
 if cap['unreadable_count'] or not cap['under_limit']:raise RuntimeError('WholeGod2 capacity required')
 changed=[p for p in GAME if p in old and (ROOT/p).read_bytes()!=old[p]];new=[p for p in GAME if p not in old]
 if len(changed)!=4 or len(new)!=0:raise RuntimeError('Actual4 modified and0 new CPP required')
 paths|=set(WRITTEN)|{r['path'] for r in read(OUT/'root-source-initial/origins.json')}|{'CMakeLists.txt'}
 ledger=read(ROOT/BOOKS[1]);previous=json.loads(old[BOOKS[1]])
 if ledger['dual_client_source_segments']!=previous['dual_client_source_segments'] or len(ledger['dual_client_source_segments'])!=197:raise RuntimeError('Historical197 drift')
 facts=dict(round=ROUND,research_only=False,completed_parallel_agents=2,new_Cplusplus_source_files_added=0,existing_Cplusplus_source_files_modified=4,new_source_segments=1,source_segments=198,new_packet_values=0,new_source_phase_bindings=0,new_complete_bidirectional_routes=0,whole_game_completion_percent=None,whole_game_denominator=None,source_paths=sorted(paths),
  actual_TW_scalar_move_quantity99_write_domains_connected=1,new_bounded_native_bytes=0,existing_Application_call_bound_in_source=True,new_Main_common_world_plan_selected=False,current_runtime_config_read=False,
  source_conclusion='Existing actual TW Application C2S24 scalar eligibility/projection -> InventoryMoveService OwnedStackQuantity99 before reply preparation -> same SQLite whole-slot CAS writer rechecks both quantities/occupancy/nonzero revisions -> original prepared encrypted41(clear)/3B/41(absolute) reply; empty slot41(clear) only. Existing caller retained in source, present runtime not checked; no invented swap/merge/stackability/instance authority.',
  authority_scope='Owner CUSTOM0089 ceiling in existing CUSTOM0037 qualified scalar whole-stack swap only. Native3-byte24 and signedBYTE127 presentation are preserved. Legacy over99 rows are neither clipped nor migrated. This does not close all24 variants, item creation/trade/bank/splitting or complete native TW gameplay.',
  source_notes=['Only production commit_inventory_move caller is InventoryMoveService. Actual Application eligibility for existing pinned map/MED/material scalar domain remains; there is no new grant or broadened metadata domain.','Both scalar snapshots require quantity0..99 at service before prepared native output and again within original writer after baseline CAS/readback. Empty destination occupancy and positive bounded revisions are checked; bothslot identity and each physical slot revision remain conserved.','All native encoding/allocation remains before BEGIN/commit; writer swap and readback remain exact.30 remains bag slots; whole-instance PET/equipment/weapon/gem paths, shop30 and legacy native projection127 are unchanged.','Saved legacy100..127 quantities retain original bytes and read projection; new qualified swap refuses them without clipping or save rewrite. No live DB queried or SQL executed.','Before4, complete firstcandidate4 and final4 plus actual call/dependencies retained with distinct epochs. Latest AGENTS/goal amendment revokes historical five-roundstop; APIactive receipt retained.','TW upstream full-native entry/scene material SourceFactory/Main, full variants/unresolved13/default-off branches and authoritative rules/storage/replies remain explicit frontier. Reviewed42/65 and partial segments are not TW completion denominator.'],
  remaining=['Implement actual TW full entry/initial scene material/SourceFactory/Main host and native movement authority with complete per-scene replies; never silently promote historical candidate2A or caller-only Current/Authority to full route.','Connect remaining TW gameplay and all variants including PK, quest/activity/PET, OrangeShop, dialogs, spectator and deferred battle paths; close inventory/reward/trade/bank/split quantity99 and numeric64 edges with real authority.','Establish complete TW directional/phase/state/variant/deferred route denominator, then reach actual TW source100% before stopping. Preserve CN/web/common scope; comprehensive tests/repair/release only after all required source routes connected.'],
  owner_explicit_resume=True,owner_TW_first=True,prior_five_round_stop_revoked=True,owner_requested_stop_after_round=None,owner_requested_pause_at_round_end=False,owner_stop_condition='TW complete source routes100% over actual full inventory',goal_status_at_source_account='active',build_run=False,tests_run=False,native_execution=False,runtime_run=False,codec_execution=False,database_access=False,SQL_run=False,deployed=False)

 dump(OUT/'parallel-agent-deliveries.json',reviews);dump(OUT/'findings.json',facts)
 ledger['tw_first_route_closure_source208']=facts
 ledger['dual_client_source_segments'].append(dict(name=OUT.name,round=ROUND,version_scope='TW-existing-Application-C2S24-qualified-scalar-CAS-S2C41clear-3B-41absolute-quantity99-source',status=facts['source_conclusion'],source_paths=sorted(paths),native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,tw_source_owner_chains_added=0,formal_application_hosted=False,existing_Application_call_bound_in_source=True,complete_gameplay_routes_added=0,evidence=OUT.relative_to(ROOT).as_posix(),remaining=facts['remaining']))
 plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND;plan['owner_requested_stop_after_work_round']=None;plan['owner_requested_stop_after_round_number']=None;plan['continuation_requires_owner_resume']=False;plan['owner_TW_first']=True;plan['prior_five_round_stop_revoked']=True;plan['historical_completed_owner_five_rounds']=[203,204,205,206,207];plan['owner_five_round_start']=None;plan['owner_five_round_end']=None;plan['owner_stop_condition']='TW actual complete source routes100%';plan['next_source_frontier']=facts['remaining'][0]
 (ROOT/BOOKS[1]).write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 with (ROOT/BOOKS[0]).open('a',encoding='utf-8') as f:f.write('\n\n## 第208輪：TW-first正式scalar數量來源\n\n'+(ROOT/DOC).read_text(encoding='utf-8')+'\n台服全部串接100%前持續工作；207 paused回條僅為歷史，不在208停下。\n')

 origins=[]
 for i,n in enumerate(sorted(paths|set(BOOKS))):
  b=(ROOT/n).read_bytes();copy=f'source/current/f{i:03d}'+Path(n).suffix;save(OUT/copy,b)
  origins.append(dict(path=n,copy=copy,bytes=len(b),sha256=sha(b),changed_this_round=n not in old or old[n]!=b))
  if n in old and old[n]!=b:
   diff=''.join(difflib.unified_diff(old[n].decode('utf-8-sig').splitlines(True),b.decode('utf-8-sig').splitlines(True),fromfile='before/'+n,tofile='current/'+n))
   if diff:save(OUT/'diff'/f'd{i:03d}.diff',diff.encode())
 dump(OUT/'source/source-origins.json',origins)
 print(json.dumps(dict(protected_files=len(guarded),source_files=len(paths),source_segments=198,new_CPP=0,modified_CPP=4,new_complete_routes=0,owner_TW_first=True,goal_status='active')))

def enrich():
 for p in reports():save(OUT/'reports/raw'/(p.parent.name+'-'+p.name),p.read_bytes())
 receipt=dict(new_CPP=0,modified_CPP=4,source_segments=198,new_source_segments=1,new_complete_bidirectional_routes=0,whole_game_percent=None,current_catalog_source_files=len(read(CAT/'source-file-manifest.json')),owner_requested_pause_at_round_end=False)
 for p in [reports()[0],reports()[2]]:
  v=read(p);v['tw_first_route_closure_source208']=read(OUT/'findings.json');v['parallel_agent_deliveries']=read(OUT/'parallel-agent-deliveries.json');v['current_round_source_delta']=receipt;p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 for p in [reports()[1],reports()[3]]:p.write_text((ROOT/DOC).read_text(encoding='utf-8')+'\n\nStatic accounting: '+json.dumps(receipt)+'\n',encoding='utf-8')
 dump(OUT/'reports/enrichment-receipt.json',receipt);print(json.dumps(receipt))

def seal():
 if (OUT/'manifest.json').exists() or (CAT/'manifest.json').exists():raise RuntimeError('Fresh208 seals required')
 rows,old=before();prior();guarded=protected(rows,old);original_copies();reviews,paths=reviewer()
 if reviews!=read(OUT/'parallel-agent-deliveries.json'):raise RuntimeError('Reviewer delivery drift')
 for r in read(OUT/'source/source-origins.json'):
  if matches(ROOT/r['path'],r)!=matches(OUT/r['copy'],r):raise RuntimeError('Final current source drift')
 ledger=read(ROOT/BOOKS[1])
 if ledger['dual_client_source_segments'][:197]!=json.loads(old[BOOKS[1]])['dual_client_source_segments'] or len(ledger['dual_client_source_segments'])!=198:raise RuntimeError('Historical197/new198 drift')
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
 rm=dict(round=ROUND,**flags,before_files=len(rows),protected_files=len(guarded),source_segments=198,new_source_segments=1,new_CPP=0,modified_CPP=4,new_complete_bidirectional_routes=0,whole_game_percent=None,owner_requested_stop_after_round=None,catalog_manifest_sha256=sha((CAT/'manifest.json').read_bytes()),files=inventory(OUT));dump(OUT/'manifest.json',rm)
 print(json.dumps(dict(root_members=len(rm['files']),catalog_members=len(cm['files']),root_sha256=sha((OUT/'manifest.json').read_bytes()),catalog_sha256=sha((CAT/'manifest.json').read_bytes()))))

if __name__=='__main__':
 if len(sys.argv)!=2 or sys.argv[1] not in ['account','enrich','seal']:raise RuntimeError('account/enrich/seal required')
 globals()[sys.argv[1]]()
