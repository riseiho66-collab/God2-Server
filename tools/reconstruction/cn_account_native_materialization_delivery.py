"""Account actual native account source writer/backend/Plan; static files only."""
import difflib
import hashlib
import json
from pathlib import Path
from .cn_wrapper_route_frontier import ROOT

NAME='cn-account-native-source-materialization-01'
ROUND='20261008-cn-account-native-source-materialization'
GAME=['src/db/SqliteNativeAccountSnapshotRepository.h','src/db/SqliteNativeAccountSnapshotRepository.cpp',
 'src/db/SqliteDatabase.h','src/db/SqliteDatabase.cpp',
 'src/cn/auth/CnNativeAccountSnapshotCommit.h','src/cn/auth/CnNativeAccountSnapshotCommit.cpp']
WRITTEN=GAME+['docs/research/cn-account-native-source-materialization-20261008.md',
 'tools/reconstruction/cn_account_native_materialization_delivery.py','tools/reconstruction/dual_client_route_catalog.py']
BOOKS=['docs/PACKET_CONNECTION_GOAL_20261006.md',
 'artifacts/integration/packet-connections-20261006/packet-route-ledger.json']
REMAINING=[
 'Actual materialization Plan and whole-tuple writer are connected to the shared same-object reader/backend; no actual native issuer implementation or snapshot bytes were provided.',
 'Actual native metadata40/billing16, supplied revisions/origins, phased write issuer and independent login entitlement/catalog/deadline, summary and world sources remain mandatory.',
 'Main native source selection, installed save-preserving schema, actual source publication/invalidation and complete native account/world login remain OPEN.',
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
 if len(before)!=934:raise RuntimeError('Expected934 before originals')
 excluded=set(WRITTEN+BOOKS)|{f'artifacts/integration/packet-connections-20261006/packet-progress-latest.{x}' for x in ['json','md']}
 protected=[]
 for row in before:
  if row['path'] not in excluded:
   if (ROOT/row['path']).read_bytes()!=old[row['path']]:raise RuntimeError('Protected source differs: '+row['path'])
   protected.append(row)
 for name,pin in [('cn-deferred-stored-directory-source-01','14b7405399a16ea67eb116e8bd4bd0ed2d5e6b7097f38c8bcf929d103a290c7b'),
                  ('endpoint-catalog162','861a064a00babd84f589aa8622749505a02577284de05fe309a1f59501014322')]:
  raw=(out/'retained-prior'/name/'manifest.json').read_bytes()
  if sha(raw)!=pin or (base/name/'manifest.json').read_bytes()!=raw:raise RuntimeError('Prior162 seal differs')
 paths=set(WRITTEN);agents=[];records=[]
 for name in ['account-snapshot-writer','account-snapshot-backend','account-native-source-plan']:
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
  actual_call_chain='CnNativeAccountSnapshotCommit::Plan -> commit_actual_source -> SqliteDatabase::native_account_snapshot_writer -> same reader replace_from_issuer',
  actual_stored_reader_chain='same account_native_snapshots -> SharedStoredAccountProfileSource::create -> unchanged actual Prepare/Authority/native issuer',
  explicit_actual_issuer_mandatory=True,write_checks=['Prepared','BeforeWrite','BeforeCommit'],
  BeforeCommit_observes_staged_next_not_old_snapshot_Current=True,
  generic_storage_domain='positive signed64 account/revision, opaque bytes1..4096, actual lowercase hashes/origin',
  CN_Plan_domain='pinned582f profile, positive uint32 native account, signed64 revision, exact metadata40/billing16',
  strict_supplied_same_scope_increasing_revision=True,generated_revisions_or_native_bytes=False,
  same_read_write_repository_object_connection_accounts=True,
  creation_game_owner_busy_RAII_foreign_keys_and_own_transaction=True,
  private_complete_account_baseline_unchanged=True,account_credentials_passed_or_logged_to_issuer=False,
  whole_expected_snapshot_verified_before_after_both_prewrite_callbacks=True,
  affected_row_revision_CAS_and_complete_staged_readback=True,
  whole_account_and_staged_snapshot_rechecked_after_real_BeforeCommit=True,
  owned_no_throw_move_result_prepared_before_COMMIT=True,
  callbacks_reloads_allocations_after_COMMIT=False,
  constructor_accessor_reader_implicit_DDL_or_writes=False,
  existing_schema_text_unchanged_and_unregistered=True,
  original_login_profile_authority_and_native_data_key_directory_sources_unchanged=True,
  source_storage_commit_is_native_ACK_or_authority=False,
  automatic_snapshot_mutation_or_grant_invalidation=False,
  actual_native_data_imported=False,schema_installed=False,
  real_native_materialization_source_and_login_rights_summary_world_Main_open=True,
  complete_route=False,formal_application_hosted=False,parallel_agent_findings=[x['findings'] for x in agents])
 dump('source/account-native-materialization-relations.json',relations)
 facts=dict(round=ROUND,previous_goal_turn_classification='progress:162 actual deferred native directory composition and original supplied-directory Current through held publication preserved in immutable seals',
  completed_parallel_agents=3,actual_account_snapshot_atomic_writers_added=1,
  actual_same_reader_writer_backend_bindings_added=1,actual_CN_native_source_materialization_plans_added=1,
  modified_gameplay_source_files=len(GAME),source_origin_records=len(records),
  existing_source_files_modified=4,new_Cplusplus_source_files_added=2,
  actual_native_factory_selected_in_Main=False,schema_registered_or_installed=False,
  new_packet_values=0,new_native_phase_source_bindings=0,new_source_owner_chains=0,new_tw_source_owner_chains=0,
  new_complete_bidirectional_routes=0,whole_game_route_total=None,whole_game_completed_routes=None,whole_game_completion_percent=None,
  formal_application_hosted=False,levels_changed=False,original_native_wire_layout_changed=False,
  build_run=False,tests_run=False,new_tests_written=0,runtime_run=False,native_execution=False,
  Cplusplus_source_run=False,Windows_API_run=False,database_access=False,deployed=False,protected_contexts=protected,remaining=REMAINING)
 dump('findings.json',facts)
 ledger_path=ROOT/BOOKS[1];ledger=json.loads(ledger_path.read_text(encoding='utf-8'))
 if len(ledger['dual_client_source_segments'])!=154 or any(x['name']==NAME for x in ledger['dual_client_source_segments']):
  raise RuntimeError('Preserve154 existing segments; fresh round required')
 sources=sorted(paths);ledger['cn_account_native_source_materialization']=dict(facts,evidence=out.relative_to(ROOT).as_posix())
 ledger['dual_client_source_segments'].append(dict(name=NAME,round=ROUND,
  version_scope='cn-explicit-actual-native-account-source-materialization-same-shared-reader-fulltuple-atomic-CAS',
  status='Actual native40/16 input Plan ->same shared reader/writer atomic account snapshot source connected; actual source bytes/issuer/login rights/schema/hosting pending',
  source_paths=sources,native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,tw_source_owner_chains_added=0,
  formal_application_hosted=False,complete_gameplay_routes_added=0,evidence=out.relative_to(ROOT).as_posix(),remaining=REMAINING))
 plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
 plan['next_source_frontier']='M2 actual native account40/16 issuer materialization/caller and phased rights, catalog/deadline/summary/world Reservation sources and save-preserving schema before Main selection; actual publication/invalidation and full TW-CN-web numeric wire/object/display/full-game denominator remain OPEN. PHASE1.'
 ledger_path.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 with (ROOT/BOOKS[0]).open('a',encoding='utf-8') as f:
  f.write('\n\n## Actual native account source materialization ('+ROUND+')\n\n'
   'Explicit CN native account40/16/pinned-build input Plan and actual phased Issuer connect through same-object Application account reader/writer. '
   'Game-owner/reentry/owntransaction/FK guards, complete account and expected snapshot, supplied increasing revision CAS and staged readback before real BeforeCommit; result owned preCOMMIT with no postcommit callback/reload/allocation. '
   'No password/account record passed to issuer, generated native values/revision, default rights or native ACK. Existing schema text/registration, login Authority/native serializers/key/directory and all saves/frozen features unchanged. '
   'Actual source bytes/issuer implementation/caller, phased login entitlement/summary/world/schema/Main selection and publication/invalidation remain OPEN. '
   'Actual6 source files changed/added, three bounded agent deliveries. New packet/phase/fullroute0, percentage null, no builds/tests/native/API/Lua/DB/migration/deploy. Full TW-CN-web objective remains active.\n')
 origins=[]
 for rel in sorted(paths|set(BOOKS)):
  raw=(ROOT/rel).read_bytes();save('source/current/'+rel,raw);origins.append(dict(path=rel,bytes=len(raw),sha256=sha(raw),changed_this_round=rel not in old or old[rel]!=raw))
  if rel in old:
   diff=''.join(difflib.unified_diff(old[rel].decode('utf-8-sig').splitlines(True),raw.decode('utf-8-sig').splitlines(True),fromfile='before/'+rel,tofile='current/'+rel))
   if diff:save('diff/'+rel+'.diff',diff.encode('utf-8'))
 dump('source/source-origins.json',origins)
 print(json.dumps(dict(round=ROUND,source_paths=len(sources),protected_files=len(protected),source_origin_records=len(records),modified_gameplay_files=len(GAME),new_complete_routes=0)))

if __name__=='__main__':main()
