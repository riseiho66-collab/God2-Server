from pathlib import Path
import json,hashlib,base64
S=Path('C:/Users/risei/Desktop/God2/God2-Server');A=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261013');D=A/'tw-cn-common-owned-skill-commit-361';N=A/'round361-cn-skill-queued-delta-reader-source'
L='artifacts/integration/packet-connections-20261006/packet-route-ledger.json';F='artifacts/integration/packet-connections-20261006/s2c-world-consumer-frontier-v23.json';G='docs/PACKET_CONNECTION_GOAL_20261006.md';R='tools/reconstruction/packet_connection_report.py';K='tw_cn_common_owned_skill_commit_source361';REPORT='20261013-tw-cn-common-owned-skill-commit-source-361';DOC='docs/research/common-owned-skill-commit-20261013.md';CONTRACT='docs/integration/SHARED_SKILL_SERVER_SOURCE_V2.json';sha=lambda b:hashlib.sha256(b).hexdigest()
def write(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(b)
def js(p,v):write(p,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
def package(root,seal_name='seal.json'):
 raw=(root/seal_name).read_bytes();v=json.loads(raw);seen=set();total=0
 for m in v['members']:
  rel=m.get('path') or m['name'];p=root/rel;b=p.read_bytes();assert p.resolve().is_relative_to(root.resolve()) and rel not in seen and type(m['bytes']) is int and len(b)==m['bytes'] and sha(b)==m['sha256'];seen.add(rel);total+=len(b)
 assert type(v['member_count']) is int and v['member_count']==len(seen)
 for key in ['member_bytes','total_bytes']:
  if key in v:assert type(v[key]) is int and v[key]==total
 return dict(root=root.as_posix(),seal_filename=seal_name,seal_sha256=sha(raw),members=len(seen),member_bytes=total)
pins=json.loads((D/'final-Cplusplus-source-pins-v2.json').read_bytes());assert len(pins)==7
for row in pins:
 b=(S/row['path']).read_bytes();assert len(b)==row['bytes'] and sha(b)==row['sha256']
inverse=[]
for rel in ['source-inverse-edits.json','source-inverse-supplement.json','source-inverse-repairs.json','source-inverse-mp-refusal-repair.json']:inverse+=json.loads((D/rel).read_bytes())
for row in pins:
 b=(S/row['path']).read_bytes()
 for edit in reversed(inverse):
  if edit['path']==row['path']:
   new=base64.b64decode(edit['new_base64']);old=base64.b64decode(edit['old_base64']);assert b.count(new)==1;b=b.replace(new,old)
 assert b==(D/'before-extra'/row['path']).read_bytes()
baseline=json.loads((D/'before-manifest.json').read_bytes());oldledger=json.loads((D/'before'/L).read_bytes());assert (S/L).read_bytes()==(D/'before'/L).read_bytes();assert (S/F).read_bytes()==(D/'before'/F).read_bytes()
allowed={x['path'] for x in pins}|{'AGENTS.md','docs/custom-designs.json'}
for row in baseline['members']:
 if row['path'] not in allowed:assert (S/row['path']).read_bytes()==(D/'before'/row['path']).read_bytes()
oldindex=json.loads((D/'before'/'docs/custom-designs.json').read_bytes());newindex=json.loads((S/'docs/custom-designs.json').read_bytes());assert newindex['designs'][:-1]==oldindex['designs'] and len(newindex['designs'])==137 and newindex['designs'][-1]['id']=='CUSTOM-0139'
assert (S/'AGENTS.md').read_bytes().startswith((D/'before'/'AGENTS.md').read_bytes())
n=package(N);assert n['members']==19 and n['member_bytes']==67662 and n['seal_sha256']=='6347e4dfa8da5523bf4926a53d2b88773cc708bb9cb634188895d93acd16a824'
helpers=[N/'discover_queued_delta361.py',N/'capture_modifier_mapping361.py',A/'apply-owned-skill-commit361_v3.py',A/'finish-owned-skill-policy361_v2.py',A/'repair-owned-skill-boundary361.py',A/'stage-owned-skill-source361.py']
copies=[]
for p in helpers:
 b=p.read_bytes();assert b'\r' not in b and not b.startswith(b'\xef\xbb\xbf') and b.endswith(b'\n') and not b.endswith(b'\n\n');rel='tools/reconstruction/'+p.name;assert not (S/rel).exists();copies.append(dict(original_path=p.as_posix(),published_path=rel,bytes=len(b),sha256=sha(b)))
rb=(S/R).read_bytes();assert K.encode() not in rb
for old,line in [(b"                   set(ledger.get('tw_cn_common_owner_skill_definition_source360', {}).get('source_paths', [])) |\n",b"                   set(ledger.get('tw_cn_common_owned_skill_commit_source361', {}).get('source_paths', [])) |\n"),(b"        'tw_cn_common_owner_skill_definition_source360': ledger.get('tw_cn_common_owner_skill_definition_source360'),\n",b"        'tw_cn_common_owned_skill_commit_source361': ledger.get('tw_cn_common_owned_skill_commit_source361'),\n")]:
 assert rb.count(old)==1;rb=rb.replace(old,old+line)
contract=dict(contract_version='god2-server/shared-skills/source/2',phase='PHASE1',custom_design='CUSTOM-0139',source_files=pins,traditional_names_primary=True,skills=[dict(kind=0,id=126,design_id='CUSTOM-0058',name='瞬影三煞斬'),dict(kind=0,id=150,design_id='CUSTOM-0059',name='牛轉仙界踏')],qualification=dict(common_definition_query_source_connected=True,common_saved_readset_consumption_source_connected=True,existing_TW_diagnostic_Application_supplier_connected=True,actual_general_TW_gameplay_host_complete=False,CN_custom_cast_source_connected=False,CN_custom_native_profile_qualified=False,CN_native_effect_source_qualified=False,CN_runtime_enabled=False,learned_grant=False,native_source=False),persistence_branches=['active_checkpoint','terminal_checkpoint','resources_without_checkpoint','settlement_without_checkpoint'],owned_settlement_request_version=4,ordinary_requests_preserved=True,explicit_nonpersistent_scope='existing isolated diagnostic with no durable callbacks',callback_contract='synchronous game executor; no reentry/send/event pumping',postcommit_fence_limit='refuse stale memory publication; cannot roll back successful COMMIT',new_native_formulas=0,build=False,test=False,runtime=False,game_database_SQL=False,migrate=False,activate=False,deploy=False)
append=('\n\n## Round361 — common owner skill action saved readset (2026-10-13)\n\n'
 'CUSTOM-0139 connects the actual selected deity learned observation for both\n'
 'kind0/126 CUSTOM-0058 and kind0/150 CUSTOM-0059 after authenticated complete\n'
 'C35 selection. Actual Application forwards the typed readset to active and\n'
 'terminal checkpoints and noncheckpoint resources/settlement writers, with\n'
 'same-connection private full-row checks inside BEGIN IMMEDIATE before writes\n'
 'and immediately before COMMIT. Owned canonical settlement replay version4\n'
 'pins complete saved selection/deity/provenance/skill bytes. No saved requests\n'
 'or schemas are rewritten. Ordinary/trial/revival/formulas/effect bodies stay\n'
 'unchanged. Existing isolated nonpersistent owner casts are explicitly scoped.\n'
 'Nested operations poison the action; removal is deferred to RAII cleanup.\n'
 'Final memory-publication fence cannot undo an already successful COMMIT; the\n'
 'existing synchronous no-reentry/no-send callback contract still applies.\n\n'
 'Actual Application hosting remains the existing TW diagnostic encounter,\n'
 'not a completed CN cast/list/actor/resource/87/effect pipeline. Original\n'
 'CN453 remains unchanged and provides no fabricated126/150 rows or rights.\n'
 'Server source capability is versioned in SHARED_SKILL_SERVER_SOURCE_V2.json.\n'
 'Bounded CN562510 complete152B/46sites only maps modifiers and calls564A30;\n'
 '80B table data, queuedHP/death/64-bit consumer child remains OPEN. Native\n'
 'package19/67662 seal6347e4dfa8da5523bf4926a53d2b88773cc708bb9cb634188895d93acd16a824.\n\n'
 'New actual source persistence branches4; complete bidirectional routes0;\n'
 'native opcodes/method credit/formulas0. TW156C2S/252S2C, world74=50partial+\n'
 '11control+13unconnected; CN156C2S/280phase/253supported lengths unchanged.\n'
 'Whole route denominator/percentage unknown. PHASE1 only: no build/tests/\n'
 'runtime/native/VM/codec/gameDBSQL/migration/activation/deployment. Goalactive.\n').encode()
gb=(S/G).read_bytes();assert gb==(D/'before'/G).read_bytes()
for row in copies:write(S/row['published_path'],Path(row['original_path']).read_bytes())
js(S/CONTRACT,contract);(S/R).write_bytes(rb);(S/G).write_bytes(gb+append)
paths=sorted(set(oldledger['tw_cn_common_owner_skill_definition_source360']['source_paths']+[x['path'] for x in pins]+[DOC,CONTRACT]+[x['published_path'] for x in copies]))
v=dict(round=REPORT,round_number=361,classification='ACTUAL_COMMON_OWNED_SKILL_SAVED_READSET_CONSUMPTION_SOURCE',previous_goal_turn_classification='progress',source_paths=paths,document=DOC,source_contract=CONTRACT,custom_design='CUSTOM-0139',existing_Cplusplus_files_modified=7,new_Cplusplus_files=0,new_native_opcode_values=0,new_native_methods_credited=0,new_recovered_skill_formulas=0,new_authoritative_handlers=0,new_world_parser_opcode_values=0,new_independent_S2C_format_classes=0,new_connected_source_branches=4,new_complete_bidirectional_routes=0,new_phase_source_bindings=0,connected_source_branches=[dict(C2S='existing authenticated C35 key/sequence/targets',S2C='existing staged skill reply',variant=x,keys=[[0,126],[0,150]],actual_source='Application diagnostic persist_resources',native_acceptance=False) for x in contract['persistence_branches']],common_saved_source=True,original_CN_453_unchanged=True,CN_host_or_cast_source_connected=False,explicit_nonpersistent_diagnostic_scope=True,postCOMMIT_rollback_claim=False,native_source=dict(body='562510..5625A8',complete_code_bytes=152,aligned_reachable_sites=46,table_bytes=80,actual_HP_mutation_qualified=False,queued_delta_reader_qualified=False,next_child='564A30',child_expanded=False),all_prior_ledger_fields_preserved=True,frontier_v23_byte_identical=True,whole_game_denominator=None,whole_game_completion_percent=None,tw_completion_percent=None,goal_status='active',phase='PHASE1',build=False,test=False,runtime=False,native_execution=False,VM=False,codec=False,game_database_SQL=False,migrate=False,activate=False,deploy=False,remaining=['Real CN host/actor/list/resources/native87 and custom effect bindings','CN564A30 and actual queued HP arithmetic/death/wide64 consumers','Common poison maximumHP/10 status/turn/checkpoint integration','Every original skill formula and whole TW-CN-fourWS directional/state/variant inventory'])
assert K not in oldledger;ledger=dict(oldledger);ledger[K]=v;assert all(ledger[k]==x for k,x in oldledger.items());(S/L).write_bytes((json.dumps(ledger,ensure_ascii=False,indent=2)+'\n').encode())
js(D/'ledger-value.json',v);js(D/'capture-publication-copies.json',copies);js(D/'native-upstream-package.json',n);js(D/'goal-append-custody.json',dict(before_bytes=len(gb),before_sha256=sha(gb),append_bytes=len(append),after_bytes=len(gb+append),after_sha256=sha(gb+append)));js(D/'stage-custody.json',dict(source_paths=len(paths),inverse_edit_count=len(inverse),source_pins=pins,copied_helpers=len(copies),new_custom_id='CUSTOM-0139',document=DOC,source_contract=CONTRACT))
print(json.dumps(dict(source_paths=len(paths),modified_Cplusplus=7,inverse_edit_count=len(inverse),new_source_branches=4,complete_routes=0,copied_helpers=len(copies),goal_status='active')))
