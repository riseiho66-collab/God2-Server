"""Account actual deferred CN stored-directory composition; static files only."""
import difflib
import hashlib
import json
from pathlib import Path
from .cn_wrapper_route_frontier import ROOT

NAME='cn-deferred-stored-directory-source-01'
ROUND='20261008-cn-deferred-stored-directory-source'
GAME=['src/cn/auth/SharedStoredAccountProfileSource.h','src/cn/auth/SharedStoredAccountProfileSource.cpp',
 'src/cn/auth/SharedLoginComposition.cpp','src/cn/auth/SharedIssuedAccountSource.cpp']
WRITTEN=GAME+['docs/research/cn-deferred-stored-directory-source-20261008.md',
 'tools/reconstruction/cn_deferred_stored_directory_delivery.py','tools/reconstruction/dual_client_route_catalog.py']
BOOKS=['docs/PACKET_CONNECTION_GOAL_20261006.md',
 'artifacts/integration/packet-connections-20261006/packet-route-ledger.json']
REMAINING=[
 'Actual deferred directory is connected to the explicitly selected stored-profile branch; Main still does not select a native CN source factory.',
 'Real complete account snapshot, native catalog metadata/deadline and phased entitlement, stored summary authority and world Reserve owners remain mandatory and missing from selected production sources.',
 'No provider data/schema/key/endpoint/rights are synthesized; missing inputs remain unavailable. Native callbacks and exact catalog output retain all existing authority gates.',
 'Full TW-CN-web authority/hosting/WSS, numeric producer-consumer-object-display and save-preserving persistent profile/schema recovery remain OPEN.',
 'Full-game denominator/every gameplay connection and later comprehensive builds/tests/repairs/recovery/playable release remain required.']

def sha(raw):return hashlib.sha256(raw).hexdigest()

def main():
 base=ROOT/'artifacts/integration/packet-connections-20261006';out=base/NAME
 if not (out/'before-manifest.json').exists() or (out/'findings.json').exists() or (out/'manifest.json').exists():
  raise RuntimeError('Fresh unaccounted round required')
 def save(rel,raw):
  p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
  with p.open('xb') as f:f.write(raw)
 def dump(rel,value):save(rel,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
 before=json.loads((out/'before-manifest.json').read_text(encoding='utf-8'));old={}
 for row in before:
  raw=(out/row['snapshot']).read_bytes()
  if len(raw)!=row['bytes'] or sha(raw)!=row['sha256']:raise RuntimeError('Before receipt differs')
  old[row['path']]=raw
 if len(before)!=932:raise RuntimeError('Expected932 before originals')
 excluded=set(WRITTEN+BOOKS)|{f'artifacts/integration/packet-connections-20261006/packet-progress-latest.{x}' for x in ['json','md']}
 protected=[]
 for row in before:
  if row['path'] not in excluded:
   if (ROOT/row['path']).read_bytes()!=old[row['path']]:raise RuntimeError('Protected source differs: '+row['path'])
   protected.append(row)
 for name,pin in [('shared-supply-health64-source-01','7d238fb25345eb48a397c6b5cce211a8bd854cd89b785fdf499debe4562fa011'),
                  ('endpoint-catalog161','946416b25a5eef0c42fa8465c6f53dc4599ccd9eace8e0f3f0df2f9b375bf3c5')]:
  raw=(out/'retained-prior'/name/'manifest.json').read_bytes()
  if sha(raw)!=pin or (base/name/'manifest.json').read_bytes()!=raw:raise RuntimeError('Prior161 seal differs')
 paths=set(WRITTEN);agents=[];records=[]
 for name in ['deferred-directory-source','deferred-directory-composition','directory-lifetime-review']:
  folder=out/'agents'/name
  seal_path=folder/'seal.json'
  findings_path=folder/'findings.json'
  seal=json.loads(seal_path.read_text(encoding='utf-8-sig'))
  rows=seal.get('files',seal.get('entries',[]))
  if not rows:raise RuntimeError('Missing agent seal entries')
  for row in rows:
   raw=(folder/row['path']).read_bytes()
   if len(raw)!=row['bytes'] or sha(raw)!=row['sha256']:raise RuntimeError('Agent seal differs')
  current=json.loads((folder/'current-source-origins.json').read_text(encoding='utf-8-sig'))
  if isinstance(current,dict):current=current['source_files']
  if not isinstance(current,list) or not current:raise RuntimeError('Final-current source list required')
  for row in current:
   p=Path(row['path']);p=p if p.is_absolute() else ROOT/p;rel=p.relative_to(ROOT).as_posix()
   if rel.startswith('artifacts/'):raise RuntimeError('Receipt path is not an original source')
   raw=(folder/row['copy']).read_bytes()
   if len(raw)!=row['bytes'] or sha(raw)!=row['sha256'] or p.read_bytes()!=raw:
    raise RuntimeError('Final-current source copy differs: '+rel)
   paths.add(rel);records.append(dict(folder=folder.relative_to(out).as_posix(),epoch='final-current',path=rel,source=row))
  agents.append(dict(agent=name,seal_file=seal_path.name,seal_sha256=sha(seal_path.read_bytes()),
    findings_file=findings_path.name,findings=json.loads(findings_path.read_text(encoding='utf-8-sig')),
    current_source_origins=current,files=[dict(path=p.relative_to(folder).as_posix(),bytes=p.stat().st_size,sha256=sha(p.read_bytes())) for p in sorted(folder.rglob('*')) if p.is_file()]))
 for rel in GAME:
  if rel in old and old[rel]==(ROOT/rel).read_bytes():raise RuntimeError('Actual gameplay change required: '+rel)
 if old['docs/custom-designs.json']!=(ROOT/'docs/custom-designs.json').read_bytes():
  raise RuntimeError('No custom design or metadata change in native mechanical bridge')
 dump('parallel-agent-deliveries.json',agents);dump('source/reviewed-current-source-records.json',records)
 relations=dict(source_only=True,custom_design_added=False,native_formula_added=False,
  actual_helper='SharedStoredAccountProfileSource::with_active_directory',
  actual_callsite='compose_native_login selected stored_issued_account_source profile.prepare before create()',
  callback_chain='stored snapshot/fulltuple -> real Prepare -> active host Directory -> existing Profile/issuer -> unchanged native directory bind/issue/publish',
  retained_same_actual_listener_registry_and_selected_configuration=True,
  actual_prepare_and_registry_observe_called_at_construction=False,
  callback_same_owner_thread_and_RAII_busy_guard=True,
  actual_provider_invoked_only_with_active_host_snapshot=True,
  callback_requires_snapshot_current_after_real_provider=True,
  raw_catalog_qualified_via_existing_from_catalog=True,
  raw_catalog_emplaced_owned_directory_then_cleared=True,
  valid_supplied_directory_original_source_preserved=True,
  ambiguous_missing_stale_directory_forms_rejected=True,
  complete_original_profile_create_and_phased_entitlement_unchanged=True,
  issued_key_policy_CNG_native_bytes_credentials_and_summaries_unchanged=True,
  original_supplied_directory_retained_before_key_and_credential_copies=True,
  original_supplied_directory_Current_checked_all_native_phases=True,
  original_supplied_directory_exact_matches_before_issue_publish=True,
  original_supplied_directory_Current_rechecked_after_real_authority=True,
  original_and_Context_directory_gates_both_retained=True,
  publication_completion_releases_Current_no_remote_rollback_claim=True,
  existing_NativeData_directory_current_and_exact_matches_before_issue_publish_retained=True,
  Main_Config_Application_world_SQL_and_numeric_gameplay_sources_unchanged=True,
  actual_native_data_imported=False,schema_installed=False,
  M2_real_rights_summary_world_Reserve_owners_and_Main_selection_open=True,
  complete_route=False,formal_application_hosted=False,parallel_agent_findings=[x['findings'] for x in agents])
 dump('source/deferred-stored-directory-relations.json',relations)
 facts=dict(round=ROUND,previous_goal_turn_classification='progress:161 actual Supply HP64/exact Lua64/projected atomic transaction and concrete M2 startup dependency preserved in immutable seals',
  completed_parallel_agents=3,actual_deferred_directory_prepare_wrappers_added=1,
  actual_stored_profile_composition_bindings_added=1,actual_directory_lifetime_frontiers_reviewed=1,
  actual_supplied_directory_publication_gates_added=1,
  modified_gameplay_source_files=len(GAME),source_origin_records=len(records),
  actual_native_factory_selected_in_Main=False,schema_registered_or_installed=False,
  new_packet_values=0,new_native_phase_source_bindings=0,new_source_owner_chains=0,new_tw_source_owner_chains=0,
  new_complete_bidirectional_routes=0,whole_game_route_total=None,whole_game_completed_routes=None,whole_game_completion_percent=None,
  formal_application_hosted=False,levels_changed=False,original_native_wire_layout_changed=False,
  build_run=False,tests_run=False,new_tests_written=0,runtime_run=False,native_execution=False,
  Cplusplus_source_run=False,Windows_API_run=False,database_access=False,deployed=False,protected_contexts=protected,remaining=REMAINING)
 dump('findings.json',facts)
 ledger_path=ROOT/BOOKS[1];ledger=json.loads(ledger_path.read_text(encoding='utf-8'))
 if len(ledger['dual_client_source_segments'])!=153 or any(x['name']==NAME for x in ledger['dual_client_source_segments']):
  raise RuntimeError('Preserve153 existing segments; fresh round required')
 sources=sorted(paths);ledger['cn_deferred_stored_directory_source']=dict(facts,evidence=out.relative_to(ROOT).as_posix())
 ledger['dual_client_source_segments'].append(dict(name=NAME,round=ROUND,
  version_scope='cn-explicit-stored-native-account-provider-deferred-active-host-directory-composition',
  status='Actual retained host/config deferred directory callback connected before stored-profile creation; actual native entitlement/summary/world providers and Main selection pending',
  source_paths=sources,native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,tw_source_owner_chains_added=0,
  formal_application_hosted=False,complete_gameplay_routes_added=0,evidence=out.relative_to(ROOT).as_posix(),remaining=REMAINING))
 plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
 plan['next_source_frontier']='M2 actual account Prepare/phased entitlement/native snapshot summary providers and concrete world Reservation ownership, exact native outputs and save-preserving schema binding before Main selection; full TW-CN-web numeric wire/object/display and whole-game denominator/guarded53 remain OPEN. PHASE1.'
 ledger_path.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 with (ROOT/BOOKS[0]).open('a',encoding='utf-8') as f:
  f.write('\n\n## Actual deferred stored-account directory source ('+ROUND+')\n\n'
   'with_active_directory retains real Prepare, exact managed listener/configuration owners and same game thread; observes only on account preparation after host start, with busy/current guards. '
   'Actual compose_native_login stored-profile branch wraps Prepare before existing create. Raw complete catalog becomes an owned qualified directory; valid supplied directory-only source and its authority are preserved. '
   'Supplied directory previously lost its Current after catalog copy; issuer now retains that original Plan before key/credential copies, checks current all phases/exact catalog before issue/publish, rechecks after actual Authority. Actual Context gate also remains. '
   'No invented fields/rights/defaults/opcodes/native formulas. Existing create fulltuple and credential/key/native output/summary unchanged. No late post-release source veto or remote rollback claim. '
   'Main production selection, actual native data/phased entitlement/summary/world Reservation and schema inputs remain OPEN. '
   'Actual4 source files changed, three bounded agent deliveries. New packet/phase/fullroute0, percentage null, no builds/tests/native/API/Lua/DB/migration/deploy. Full TW-CN-web objective remains active.\n')
 origins=[]
 for rel in sorted(paths|set(BOOKS)):
  raw=(ROOT/rel).read_bytes();save('source/current/'+rel,raw);origins.append(dict(path=rel,bytes=len(raw),sha256=sha(raw),changed_this_round=rel not in old or old[rel]!=raw))
  if rel in old:
   diff=''.join(difflib.unified_diff(old[rel].decode('utf-8-sig').splitlines(True),raw.decode('utf-8-sig').splitlines(True),fromfile='before/'+rel,tofile='current/'+rel))
   if diff:save('diff/'+rel+'.diff',diff.encode('utf-8'))
 dump('source/source-origins.json',origins)
 print(json.dumps(dict(round=ROUND,source_paths=len(sources),protected_files=len(protected),source_origin_records=len(records),modified_gameplay_files=len(GAME),new_complete_routes=0)))

if __name__=='__main__':main()
