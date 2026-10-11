"""Static actual world skill-output source delivery, never runtime or DB."""
import hashlib,json,difflib
from pathlib import Path
from .cn_wrapper_route_frontier import ROOT
NAME='cn-world-subject-skill-publication-source-01';ROUND='20261008-cn-world-subject-skill-publication-source'
SOURCES=['src/cn/world/SharedSubjectSkillPublication.h','src/cn/world/SharedSubjectSkillPublication.cpp','src/cn/world/SharedWorldGameplay.h','src/cn/world/SharedWorldGameplay.cpp','docs/research/cn-world-subject-skill-publication-source-20261008.md','tools/reconstruction/cn_world_subject_skill_publication_source_delivery.py','tools/reconstruction/dual_client_route_catalog.py']
REMAINING=['Actual CN catalog rows/binding/common event issuer/post-commit qualifier/subject and skill mapping/native qualification/rules/save/persistent replay/Application remain unconfigured.','TW/battle projection, native84 caller/full initial timing/full TW/CN/PC/web/WSS/gameplay/numeric64/stack99/whole-game denominator and later comprehensive tests/repair/release remain open.']
def sha(d):return hashlib.sha256(d).hexdigest()
def main():
 b=ROOT/'artifacts/integration/packet-connections-20261006';o=b/NAME
 if (o/'findings.json').exists():raise RuntimeError('Preserve prior delivery')
 def save(rel,d):
  p=o/rel;p.parent.mkdir(parents=True,exist_ok=True)
  with p.open('xb') as f:f.write(d)
 def dump(rel,v):save(rel,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
 before=json.loads((o/'before-manifest.json').read_text(encoding='utf-8'));old={r['path']:(o/r['snapshot']).read_bytes() for r in before}
 if len(before)!=138:raise RuntimeError('Expected138 before inputs')
 books=['docs/PACKET_CONNECTION_GOAL_20261006.md','artifacts/integration/packet-connections-20261006/packet-route-ledger.json'];reports={f'artifacts/integration/packet-connections-20261006/packet-progress-latest.{x}' for x in ['json','md']};protected=[]
 for row in before:
  if sha(old[row['path']])!=row['sha256']:raise RuntimeError('Before snapshot differs')
  if row['path'] not in set(SOURCES+books)|reports:
   if (ROOT/row['path']).read_bytes()!=old[row['path']]:raise RuntimeError('Protected source differs: '+row['path'])
   protected.append(row)
 prior=(o/'retained-prior/cn-world-subject-skill-format-source-01/manifest.json').read_bytes()
 if sha(prior)!='447db04358611341f7e34d59ac9c8f646d2bc824a644547f33d167ae8e9c7fa7':raise RuntimeError('Prior seal differs')
 for rel in ['src/cn/net/SharedCredentialConnection.h','src/cn/net/SharedCredentialConnection.cpp','src/game/SharedWorldPresence.h','src/cn/world/SharedWorldReady.cpp','src/cn/world/CnPrebornSkillReferences.h','src/cn/world/CnPrebornSkillReferences.cpp','src/cn/assets/CnSharedSkillCatalog.h','src/cn/assets/CnSharedSkillCatalog.cpp','src/cn/protocol/CnWorldSubjectSkillUpdate.h','CMakeLists.txt']:
  save('retained-inputs/'+rel,(ROOT/rel).read_bytes())
 for rel in ['native/retained-world-endpoints.json','native/00567B50.c','native/00567B50.bin','retained-consumers/native/skill-reference-relations.json']:
  save('retained-native/'+rel,(b/'cn-world-subject-skill-format-source-01'/rel).read_bytes())
 relations=dict(version='cn',phase='world-connection-1',native_opcodes=['34','35'],source_owner='SharedSubjectSkillPublication',existing_sender='SharedCredentialConnection::send_world_batch_with_publication',same_ready_presence_and_lease=True,actual1C_gameplay_binding=True,bind_sends_nothing=True,actual_post_commit_plan_required=True,actual_recipient_native_subject_and_common_skill_mapping_qualifier_required=True,actual_rule_save_persistent_replay_qualifier_required=True,qualify_before_queue_and_before_held_release=True,owning_plan_and_definition_records=True,exact_form_header_and_catalog_source_qualified=True,record_order_preserved=True,retired_preborn_window_Current_not_used=True,local_last_attempt_not_persistent_replay=True,world_only=True,TW_or_battle_implicitly_hosted=False,actual_common_source_issuer_configured=False,formal_application_hosted=False,complete_route=False)
 dump('source/publication-relations.json',relations)
 facts=dict(round=ROUND,previous_goal_turn_classification='progress:135 full WORLD34/35 format and definition binding sealed',cn_subject_skill_publication_source_owners_added=1,cn_subject_skill_held_publication_paths_added=1,cn_existing_gameplay_source_bindings_added=1,new_packet_values=0,new_native_phase_source_bindings=2,new_source_owner_chains=1,new_tw_source_owner_chains=0,new_complete_bidirectional_routes=0,actual_common_rule_save_replay_issuer_configured=False,formal_application_hosted=False,whole_game_route_total=None,whole_game_completed_routes=None,whole_game_completion_percent=None,build_run=False,tests_run=False,runtime_run=False,native_execution=False,Cplusplus_source_run=False,Windows_API_run=False,database_access=False,deployed=False,protected_contexts=protected,remaining=REMAINING)
 dump('findings.json',facts)
 p=b/'packet-route-ledger.json';ledger=json.loads(p.read_text(encoding='utf-8'));ledger['cn_world_subject_skill_publication_source']=dict(facts,evidence=o.relative_to(ROOT).as_posix())
 ledger['dual_client_source_segments'].append(dict(name='CN actual committed subject-skill event ->same ready lease ->held WORLD34/35 source publication',version_scope='pinned-cn-world1-conditional-post-commit-output-source-only',status='Actual output owner/publication/gameplay binding source; common issuer/rules/save/replay/rows/Application unconfigured',source_paths=SOURCES,native_c2s_by_phase={},native_s2c_by_phase={'world-connection-1':['34','35']},source_owner_chains_added=1,tw_source_owner_chains_added=0,formal_application_hosted=False,complete_gameplay_routes_added=0,evidence=o.relative_to(ROOT).as_posix(),remaining=REMAINING))
 ledger['dual_client_execution_plan']['latest_work_round']=ROUND
 ledger['dual_client_execution_plan']['next_source_frontier']='Actual common post-commit event issuer/subject and skill mapping/native rules/save/replay/Application; TW/battle outputs and native84/timing; whole TW/CN/PC/web/WSS/gameplay/numeric64/stack99/denominator. PHASE1.'
 p.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 with (ROOT/books[0]).open('a',encoding='utf-8') as f:f.write('\n\n## CN committed subject-skill output ('+ROUND+')\n\nAdded actual SharedSubjectSkillPublication owner bound in same1C gameplay/Lease; actual committed event/recipient/revision/native records/owning definitions ->existing held world publication, readonly common mapping/rule/save/persistent replay observations before queue and held release. Bind emits nothing; no old preborn Current, fabricated grant, new wire or local replay claim. Two overlapping phase associations/one partial owner, no complete route. Actual common issuer/rows/rules/save/replay/Application unconfigured; full goal and phase1/later comprehensive validation preserved.\n')
 for rel in SOURCES+books:
  d=(ROOT/rel).read_bytes();save('source/current/'+rel,d)
  if rel in old:
   diff=''.join(difflib.unified_diff(old[rel].decode('utf-8-sig').splitlines(True),d.decode('utf-8-sig').splitlines(True)))
   if diff:save('diff/'+rel+'.diff',diff.encode('utf-8'))
 print(json.dumps(dict(round=ROUND,new_native_phase_source_bindings=2,new_partial_source_owners=1,new_complete_bidirectional_routes=0)))
if __name__=='__main__':main()
