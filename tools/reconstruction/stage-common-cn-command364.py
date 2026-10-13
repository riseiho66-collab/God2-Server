from pathlib import Path
import json,hashlib,subprocess
S=Path('C:/Users/risei/Desktop/God2/God2-Server');A=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261013');D=A/'tw-cn-common-skill-saved-supplier-364';sha=lambda b:hashlib.sha256(b).hexdigest()
L='artifacts/integration/packet-connections-20261006/packet-route-ledger.json';F='artifacts/integration/packet-connections-20261006/s2c-world-consumer-frontier-v23.json';G='docs/PACKET_CONNECTION_GOAL_20261006.md';R='tools/reconstruction/packet_connection_report.py';K='tw_cn_common_skill_command_source364';OLDK='tw_cn_owned_skill_input_continuation_source363';DOC='docs/research/common-cn-command-definitions-20261013.md';CONTRACT='docs/integration/SHARED_SKILL_SERVER_SOURCE_V5.json';REPORT='20261013-tw-cn-common-skill-command-source-364'
def write(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(b)
def js(p,v):write(p,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
def package(row):
 root=Path(row['root']);name=row['seal_filename'];raw=(root/name).read_bytes();assert sha(raw)==row['seal_sha256'];v=json.loads(raw);seen=set();total=0
 for m in v['members']:
  rel=m.get('path') or m['name'];p=root/rel;b=p.read_bytes();assert p.resolve().is_relative_to(root.resolve()) and rel not in seen and type(m['bytes']) is int and m['bytes']>=0 and len(b)==m['bytes'] and sha(b)==m['sha256'];seen.add(rel);total+=len(b)
 assert type(v['member_count']) is int and len(seen)==v['member_count']==row['members'] and total==row['member_bytes']
 for k in ['member_bytes','total_bytes']:
  if k in v:assert type(v[k]) is int and v[k]==total
 return row
review=json.loads((D/'approved-candidate.json').read_bytes());assert review['status']=='PASS_ROOT_AND_INDEPENDENT_STATIC_SOURCE_REVIEW';pins=review['source_files'];inverse=review['inverse_edits'];upstreams=[package(r) for r in review['upstream_packages']];assert len(pins)==2 and len(inverse)==19 and len(upstreams)==4
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=S,text=True).strip()=='1d22ee991fa4ca899ddef051511bba738a54cb77'
for r in pins:
 b=(S/r['path']).read_bytes();assert len(b)==r['bytes'] and sha(b)==r['sha256']
 for e in reversed(inverse):
  if e['path']==r['path']:
   n,o=bytes.fromhex(e['new_hex']),bytes.fromhex(e['old_hex']);assert b.count(n)==e.get('count',1);b=b.replace(n,o)
 assert b==(D/'before-extra'/r['path']).read_bytes()
for r in json.loads((D/'before-manifest.json').read_bytes())['members']:assert (S/r['path']).read_bytes()==(D/'before'/r['path']).read_bytes()
for r in json.loads((D/'before-extra-manifest.json').read_bytes())['members']:
 b=(D/'before-extra'/r['path']).read_bytes();assert len(b)==r['bytes'] and sha(b)==r['sha256']
copies=[]
for p in [Path(p) for p in review['published_helpers']]+[A/'stage-common-cn-command364.py']:
 b=p.read_bytes();assert b'\r' not in b and not b.startswith(b'\xef\xbb\xbf') and b.endswith(b'\n') and not b.endswith(b'\n\n');rel='tools/reconstruction/'+p.name;assert not (S/rel).exists();copies.append(dict(original_path=p.as_posix(),published_path=rel,bytes=len(b),sha256=sha(b)))
ib=(S/'docs/custom-designs.json').read_bytes();oldindex=json.loads(ib);assert len(oldindex['designs'])==139 and ib.endswith(b'\n]\n}\n') and not any(x['id']=='CUSTOM-0142' for x in oldindex['designs'])
entry=dict(id='CUSTOM-0142',name='CN existing C35 common definition handoff and retained skill group prefix',authority='OWNER_COMMON_SOURCE_COMPOSITION_NOT_NATIVE_FORMULA_PERMISSION_OR_HOST',implementation=[r['path'] for r in pins],native_gap='CN original453 lacks owner126/150; extended native profile/resources, actor/control/learned/committed87 provider and actual common action host remain unqualified.',rules=dict(definition='Existing qualified CnSharedSkillCatalog.lookup_shared supplies owning common definition plus exact requested native CN row; raw skill_fields are read ONLY from original CN row.',handoff='Actual existing DataAuthority current/prepare/execute_group receives owning common value; reobserve the same requested row and full definition around sequential observer cuts, never silently replace.',continuation='Skill-containing Append groups retain exact prior plan/requests/lease/token and unconsumed original prefix rows/private native selection holders; equivalent fresh values cannot substitute those private holders.',mixed='New suffix is checked, next plan stays Append/Final with same group/issuer capabilities and generations; referenced mixed inventory stays with actual Current and used-cell bytes. Pure Item/Opaque prefix policy remains.',limits='Sequential checks are not cross-source atomic CAS. Existing execute-once/actual-result and durable-prefix behavior remain; no retry/rollback after COMMIT, native learned/MP/grant/effects or hosting inferred.'),activation=False,production_activated=False,schema_installed=False,deployment=False,native_client_acceptance=False,tests=[],verification_status='NOT_RUN_PHASE1_STATIC_SOURCE_ONLY',reason='One common TW/CN skill definition must reach the real existing CN command data handoff while regional wire provenance remains exact.',replacement='Complete actual common action authority, native actor/list/profile/learned/persistence providers and CN custom adapters, then comprehensive build/tests/current-client acceptance.')
newindex=ib[:-len(b'\n]\n}\n')]+b',\n'+json.dumps(entry,ensure_ascii=False,indent=2).encode()+b'\n]\n}\n';assert json.loads(newindex)['designs'][:-1]==oldindex['designs']
agn=(S/'AGENTS.md').read_bytes();agn_append=b'\nCUSTOM-0142 passes the common owning definition through the existing CN C35\nDataAuthority current/prepare/execute handoff. Keep requested native CN raw\nseparate; no common TW profile may replace CN wire/permission fields. Recheck\nsame owning material across sequential observers; no cross-source atomic CAS.\nSkill group continuations retain the exact old prefix/private selection and\nplan/lease/token rather than replacing it with fresh equal keys. Preserve\nItem/Opaque policy, actual inventory Current and execute-once/result contracts.\nOriginalCN453 missing126/150, extended resources/actor/learned/87/host and\nnative formula/cost/acceptance remain independently OPEN.\n'
doc='''# Common definition at the existing mainland C35 data handoff

PHASE1 static source only; CUSTOM-0142. The common definition, complete-source
selection and original TW Traditional names now reach the existing CN command
data interface. This does not establish a hosted action authority or native
skill arithmetic, learning, actor/control, MP charge or effect acceptance.

## Actual source

SharedNativeBattleCommandData::resolve uses existing qualified lookup_shared in
both direct-key and optional native-list-selection branches. requested_native
must remain the complete original CN NativeSkillRecord. An actual selection
must match that same full record. The original raw skill_fields and key/domain
gates continue to read CN bytes, independently of the common chosen TW base.

Row's appended owning common_definition reaches actual DataAuthority.current,
prepare and execute_group calls through their existing complete Resolved input.
Current reobserves the exact original CN row and full common value, including
profiles/provenance/raw/text/qualification/owner rule. It does not rebase to a
newer value or treat metadata as learned or cast permission.

Preparation owns arguments and brackets both authority observers with checks
of the same snapshot. These are sequential source cuts, not a cross-catalog
atomic CAS. The final old-prefix check itself observes resources; later actual
Groups.current/Data.execute still rechecks the complete next input before action.

## Continuation and settlement

For groups containing a Skill, saved requests/plan must match the unconsumed
prior Append Input, original lease/token and plan. Fresh prefix values must
match, then the OLD prefix Row/private selection holder is retained. A fresh
equal native snapshot is not proof of private-holder identity. The next plan
must remain Append/Final with the same issuer/group capabilities and generations.
New groups do not borrow consumed Single/Final input. Pure Item/Opaque prefix
policy remains; mixed inventory uses actual Current and referenced item bytes,
without adding a whole-bank equality policy.

Existing execute-once and actual-result checks remain. A post-COMMIT source
mismatch refuses later publication; it cannot reverse or replay durable work.
No new factory, default controller, native packet, grant, actor or database
schema is supplied. Missing original CN126/150 rows still reject in this native
adapter; a qualified separate owner profile and real shared gameplay host are
required for 瞬影三煞斬 and 牛轉仙界踏.

## Native source frontier

Original582f553BC0..553E86 is now a complete710-byte/190-site static body,
with seven closed direct branches and soleRET24h. Actual CALL is54A6DF;
formal7 is the R+90 row source and formal9 the H+9D223C bank pointer.
Its16-row/100WORD primary footprint and independent3x10WORD secondary footprint
remain distinct. Opaque GUI/74FC50 contracts, ESI lineage and currentness do not
become learned/actor/grant proof. Old87/38/loader/control bodies are referenced
in place. This is one local body closure, zero global new-method/full-route credit.

Original CN453 and compiled907 row pins, TW Session/DB/service/custom effects
remain unchanged. Source contract shared-skills/source/5. Two existing data
handoff branches gain common values; whole bidirectional route credit is zero.
TW156 C2S/252 S2C and CN156 C2S/280 phase/253 supported lengths remain unchanged;
whole-game denominator/percentage are unknown. No build/tests/runtime/native,
VM/codec/gameDBSQL/migration/activation/deployment were performed.

The owner requested stopping after this round. Finalize publication and pause
the goal; do not begin another round without a later resume.
'''.encode()
v4=json.loads((S/'docs/integration/SHARED_SKILL_SERVER_SOURCE_V4.json').read_bytes());contract=dict(v4);allpins=v4['source_files']+pins;assert len(allpins)==11
for r in allpins:
 b=(S/r['path']).read_bytes();assert len(b)==r['bytes'] and sha(b)==r['sha256']
contract.update(contract_version='god2-server/shared-skills/source/5',custom_designs=v4['custom_designs']+['CUSTOM-0142'],source_files=allpins,qualification=dict(v4['qualification'],actual_CN_command_data_common_definition_handoff_source_connected=True,actual_CN_command_data_host_complete=False),CN_command_source='Exact qualified original CN requested row + owning common definition -> existing actual DataAuthority current/prepare/execute_group; sequential same-value checks and original skill-group prefix/private holder retained',cross_source_atomic_CAS=False,original_CN_row_absence_not_bypassed=True)
oldledger=json.loads((S/L).read_bytes());assert K not in oldledger;rb=(S/R).read_bytes();assert K.encode() not in rb
for old,line in [(f"                   set(ledger.get('{OLDK}', {{}}).get('source_paths', [])) |\n".encode(),f"                   set(ledger.get('{K}', {{}}).get('source_paths', [])) |\n".encode()),(f"        '{OLDK}': ledger.get('{OLDK}'),\n".encode(),f"        '{K}': ledger.get('{K}'),\n".encode())]:assert rb.count(old)==1;rb=rb.replace(old,old+line)
gb=(S/G).read_bytes();append=b'\n\n## Round364 - common definition at existing CN command handoff (2026-10-13)\n\nCUSTOM-0142 retains original CN raw plus full common definition through actual\nexisting DataAuthority current/prepare/execute. Same sequential snapshot and\nold Skill-prefix private holders retained across Append continuations; no\ncross-source atomic CAS, learned/cost/actor/default-host or postCOMMIT rollback.\nCN126/150 extended profile/resources/actual actor/list/87/commonhost remainOPEN.\nOriginal553BC0 complete710B/190sites/RET24h plus actual54A6DF caller9formals\nclosed; opaque children/currentness remainOPEN. Localbodyclosure1, globalnew\nmethod/opcode/fullroute/formula credit0. TW156/252 world74=50partial+11control+\n13unconnected; CN156/280phase/253 supported unchanged. Sourcecontract source/5.\nPHASE1 no build/tests/native/runtime/VM/codec/gameDBSQL/migrate/activate/deploy.\nOwner requests stop after round364: finalize publication then pause goal; no\nnext round until resume. Whole denominator/percentage unknown.\n'
paths=sorted(set(oldledger[OLDK]['source_paths']+[p['path'] for p in pins]+[DOC,CONTRACT]+[r['published_path'] for r in copies]));assert len(paths)==391+2+2+len(copies)
value=dict(round=REPORT,round_number=364,classification='EXISTING_CN_COMMAND_COMMON_DEFINITION_HANDOFF',previous_goal_turn_classification='progress',source_paths=paths,document=DOC,source_contract=CONTRACT,custom_design='CUSTOM-0142',existing_Cplusplus_files_modified=2,new_Cplusplus_files=0,new_native_opcode_values=0,new_native_methods_credited=0,new_recovered_skill_formulas=0,new_authoritative_handlers=0,new_world_parser_opcode_values=0,new_independent_S2C_format_classes=0,new_connected_source_branches=2,new_complete_bidirectional_routes=0,new_phase_source_bindings=0,connected_source_branches=[dict(C2S='original CN35 Skill03/17/83/97',source=mode,handoff='actual DataAuthority current/prepare/execute_group',native_acceptance=False,host_complete=False) for mode in ['qualified_direct_key','optional_actual_native_selection']],owning_common_definition=True,original_requested_CN_raw_preserved=True,old_private_prefix_holder_retained=True,same_prefix_value_not_rebase=True,sequential_not_atomic_CAS=True,pure_Item_Opaque_prefix_policy_preserved=True,CN_custom_cast_source_connected=False,CN_actual_data_host_complete=False,original_CN_453_unchanged=True,compiled907_row_pins_unchanged=True,postCOMMIT_rollback_claim=False,native_source=dict(body='553BC0..553E86',complete_code_bytes=710,aligned_reachable_sites=190,closed_direct_branches=7,RET_sites=1,RET_cleanup_bytes=36,actual_caller='54A6DF',formals=9,local_new_body_closure=1,global_new_method_credit=0,opaque_children_expanded=False,learned_actor_grant_qualified=False),all_prior_ledger_fields_preserved=True,frontier_v23_byte_identical=True,whole_game_denominator=None,whole_game_completion_percent=None,goal_status='active_during_round',owner_requested_stop_after_round=True,planned_goal_status_after_publication='paused',phase='PHASE1',build=False,test=False,runtime=False,native_execution=False,VM=False,codec=False,game_database_SQL=False,migrate=False,activate=False,deploy=False,remaining=['Actual common native action authority and full TW native providers','CN126/150 native extended profiles/effects/actor/committed87 and actualhost','Every original skill formula and poison current maximumHP/10 status pipeline','Complete TW-CN-fourWS direction/phase/state/variant routes and later runtime acceptance'])
assert not (S/DOC).exists() and not (S/CONTRACT).exists()
for r in copies:write(S/r['published_path'],Path(r['original_path']).read_bytes())
(S/'docs/custom-designs.json').write_bytes(newindex);(S/'AGENTS.md').write_bytes(agn+agn_append);write(S/DOC,doc);js(S/CONTRACT,contract);(S/R).write_bytes(rb);(S/G).write_bytes(gb+append);ledger=dict(oldledger);ledger[K]=value;assert all(ledger[k]==v for k,v in oldledger.items());(S/L).write_bytes((json.dumps(ledger,ensure_ascii=False,indent=2)+'\n').encode())
js(D/'final-Cplusplus-source-pins.json',pins);js(D/'ledger-value.json',value);js(D/'capture-publication-copies.json',copies);js(D/'upstream-packages.json',upstreams);js(D/'goal-append-custody.json',dict(before_bytes=len(gb),before_sha256=sha(gb),append_bytes=len(append),after_bytes=len(gb+append),after_sha256=sha(gb+append)));js(D/'stage-custody.json',dict(source_paths=len(paths),source_pins=pins,contract_pins=allpins,inverse_edits=19,copied_helpers=len(copies),new_id='CUSTOM-0142',document=DOC,source_contract=CONTRACT,custom_designs_before=139,custom_designs_after=140,owner_requested_pause_after_round=True))
print(json.dumps(dict(source_paths=len(paths),modified_Cplusplus=2,copied_helpers=len(copies),inverse_edits=19,upstream_members=sum(x['members'] for x in upstreams),upstream_bytes=sum(x['member_bytes'] for x in upstreams),new_source_branches=2,complete_routes=0,pause_after_publication=True)))
