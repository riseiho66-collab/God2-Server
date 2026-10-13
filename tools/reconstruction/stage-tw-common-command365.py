from pathlib import Path
import json,hashlib,subprocess
S=Path('C:/Users/risei/Desktop/God2/God2-Server');A=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261013');D=A/'tw-common-skill-command-handoff-365';sha=lambda b:hashlib.sha256(b).hexdigest()
L='artifacts/integration/packet-connections-20261006/packet-route-ledger.json';F='artifacts/integration/packet-connections-20261006/s2c-world-consumer-frontier-v23.json';G='docs/PACKET_CONNECTION_GOAL_20261006.md';R='tools/reconstruction/packet_connection_report.py';K='tw_common_skill_command_source365';OLDK='tw_cn_common_skill_command_source364';DOC='docs/research/common-tw-command-definitions-20261013.md';CONTRACT='docs/integration/SHARED_SKILL_SERVER_SOURCE_V6.json';REPORT='20261013-tw-common-skill-command-source-365'
def write(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(b)
def js(p,v):write(p,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
def package(row):
 root=Path(row['root']);raw=(root/row['seal_filename']).read_bytes();assert sha(raw)==row['seal_sha256'];v=json.loads(raw);seen=set();total=0
 for m in v['members']:
  rel=m.get('path') or m['name'];p=root/rel;b=p.read_bytes();assert p.resolve().is_relative_to(root.resolve()) and rel not in seen and type(m['bytes']) is int and m['bytes']>=0 and len(b)==m['bytes'] and sha(b)==m['sha256'];seen.add(rel);total+=len(b)
 assert type(v['member_count']) is int and len(seen)==v['member_count']==row['members'] and total==row['member_bytes']
 for k in ['member_bytes','total_bytes']:
  if k in v:assert type(v[k]) is int and v[k]==total
 return row
review=json.loads((D/'approved-candidate.json').read_bytes());assert review['status']=='PASS_ROOT_AND_INDEPENDENT_STATIC_SOURCE_REVIEW';pins=review['source_files'];inverse=review['inverse_edits'];upstreams=[package(r) for r in review['upstream_packages']];assert len(pins)==2 and len(upstreams)==4
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=S,text=True).strip()=='5a21cb97abb20c40080d4bf6be1a67cc4a071278'
for r in pins:
 b=(S/r['path']).read_bytes();assert len(b)==r['bytes'] and sha(b)==r['sha256']
 for e in reversed(inverse):
  if e['path']==r['path']:
   n,o=bytes.fromhex(e['new_hex']),bytes.fromhex(e['old_hex']);assert b.count(n)==e.get('count',1);b=b.replace(n,o)
 assert b==(D/'before-extra'/r['path']).read_bytes()
for r in json.loads((D/'before-manifest.json').read_bytes())['members']:assert (S/r['path']).read_bytes()==(D/'before'/r['path']).read_bytes()
copies=[]
for p in [Path(p) for p in review['published_helpers']]+[A/'stage-tw-common-command365.py']:
 b=p.read_bytes();assert b'\r' not in b and not b.startswith(b'\xef\xbb\xbf') and b.endswith(b'\n') and not b.endswith(b'\n\n');rel='tools/reconstruction/'+p.name;assert not (S/rel).exists();copies.append(dict(original_path=p.as_posix(),published_path=rel,bytes=len(b),sha256=sha(b)))
ib=(S/'docs/custom-designs.json').read_bytes();oldindex=json.loads(ib);assert len(oldindex['designs'])==140 and ib.endswith(b'\n]\n}\n') and not any(x['id']=='CUSTOM-0143' for x in oldindex['designs'])
entry=dict(id='CUSTOM-0143',name='TW existing C35 owning common definition handoff',authority='OWNER_COMMON_SOURCE_COMPOSITION_NOT_NATIVE_FORMULA_PERMISSION_OR_HOST',implementation=[r['path'] for r in pins],native_gap='Actual complete native issued roster/control, learned actor/grant and action owner hosting remain unqualified; common metadata cannot manufacture original TW or CN custom rows.',rules=dict(scope='Append owning common definition to existing Scope; actual qualification/current/action/after_action callbacks receive the same value without changing virtual signatures.',native='Original digestchecked TW record and issued selection must exactly equal shared requested_native; chosen common profile never replaces native grammar/MP/wire fields.',current='Before action reobserve original full TW plus full common definition through sequential current cuts; refuse missing common or any replacement/rebase.',settlement='After actual action pass retained Scope only; preserve real next receipt and complete reply validation without rereading consumed old grant/catalog or reversing durable work.',limits='No cross-source atomic CAS, learned/cost/actor/native formula/default host or client acceptance is inferred.'),activation=False,production_activated=False,schema_installed=False,deployment=False,native_client_acceptance=False,tests=[],verification_status='NOT_RUN_PHASE1_STATIC_SOURCE_ONLY',reason='One common TW/CN skill core requires the existing TW command action interface to receive the same owning common definition already available to the CN data handoff.',replacement='Complete actual full native list/actor/learned/action/persistence suppliers and adapters, then comprehensive build/tests/current-client acceptance.')
newindex=ib[:-len(b'\n]\n}\n')]+b',\n'+json.dumps(entry,ensure_ascii=False,indent=2).encode()+b'\n]\n}\n';assert json.loads(newindex)['designs'][:-1]==oldindex['designs']
agn=(S/'AGENTS.md').read_bytes();agn_append=b'\nOwner resume after round364 revokes its stop/pause request; continue the full\nTW-first common-core goal in PHASE1. CUSTOM-0143 carries the owning common\ndefinition in the existing TW C35 Scope through real WorldOwner callbacks.\nKeep original digestchecked TW/issued/requested-native full-row equality and\nall native grammar/actor/list gates. Require same common value before action,\nwithout rebasing. After action retain that input but only qualify the actual\nnext receipt, never requery consumed old catalog/grant or undo durable work.\nSequential source checks are not atomic CAS, native formulas or actual host.\n'
doc='''# Common definition at the existing Taiwan C35 action interface

The owner resumed after round364; the historical stop is revoked. PHASE1
continues with TW-first complete source routes and one common TW/CN skill core.
CUSTOM-0143 connects owning common definitions to the existing TW command
interface. This is source integration, not an actual complete gameplay host.

The existing Scope appends an optional owning SharedSkillDefinition. Its prior
lease/position/battle-generation fields and all WorldOwner virtual signatures
stay intact. Actual qualification/current/action/after_action calls already
receive that Scope, so the same common material now reaches each call.

Dispatch retains the actual complete input sequence and original issued-list
selection. The original TW digestchecked full row/image/actor/side checks remain.
Existing shared lookup must return requested_native exactly equal to that TW
row and the issued selection. The original observation tuple is not recaptured
after observers; only the owning common value is appended. An empty common value
cannot silently use a legacy pass. Common chosen CN/TW parameter bases never
replace the original TW record used by native grammar or client-only gates.

Before qualification and around both actual current callbacks, the source
reobserves the same complete TW record and full common definition. Equality
includes original profiles/provenance/raw bytes/text/qualification/owner rules.
Any change refuses the old operation; no new equal key or later source is
silently substituted. These observer cuts remain sequential, not a multi-source
atomic CAS or proof of external executor convergence.

The actual action and after_action receive the same retained Scope. After
mutation, existing next-receipt/ready(false)/complete-reply checks remain; no old
catalog, consumed grant, learned/MP snapshot is reread to reverse or retry a
durable prefix. This does not invent cost, formulas, actor membership or grants.

Only SharedTaiwanNativeSkillCommandSource.h/.cpp change. Existing host-plan
with_native_skills still requires an actual complete WorldOwner; Main does not
provide one by default. Primary/secondary issued-source/selector gates remain.
No raw original row is fabricated, and missing requested TW rows still refuse
even when a formal common owner rule exists. CN original453, compiled907 pins,
Session/DB transactions, owner126/150 rules and accepted TW visuals stay frozen.
CN126/150 real profile/resources/actor/learned/87/effects/host remain open.

Native N365 retains complete4AE520..4AE63F (287bytes/88sites/fourRET4) and
4AB650..4AB694 (68bytes/31sites/twoRET), actual parentCALL4AB675. The selected
type2 shortcut arm calls existing4A9110 then4A90D0 and opaque4834E0 before
saving lowBYTE kind/id at U+23D870/71. Mode0/1 tuple sources are explicit;
other modes leave stack tuple uninitialized in the original body. Parent
slot0..9 does not prove mode1 selected-row bounds/currentness. Opaque child
may change source state; saved bytes retain the earlier tuple. Existing item
and dailyquest arms and complete lookup/MP gates are referenced in place.
This is a world skill cursor/operand source, separate from battleC35. The
actual worldtargetC56/497A90 target supplier remains open, as do native debit,
damage formula, learned/grant and full gameplay route. Global new-method
credit is zero. Native evidence remains in the immutable N365 package.

Source contract shared-skills/source/6. Two existing primary/secondary command
handoff branches gain common data, zero new complete bidirectional routes.
TW156 C2S/252 supported S2C, world74=50partial+11control+13unconnected;
CN156 C2S/280 phase/253 supported lengths remain unchanged. Whole denominator
and completion percentage remain unknown. No compiler/build/tests/runtime,
native/API/VM/codec/gameDBSQL/migration/activation/deployment were performed.
'''.encode()
v5=json.loads((S/'docs/integration/SHARED_SKILL_SERVER_SOURCE_V5.json').read_bytes());contract=dict(v5);allpins=v5['source_files']+pins;assert len(allpins)==13
for r in allpins:
 b=(S/r['path']).read_bytes();assert len(b)==r['bytes'] and sha(b)==r['sha256']
contract.update(contract_version='god2-server/shared-skills/source/6',custom_designs=v5['custom_designs']+['CUSTOM-0143'],source_files=allpins,qualification=dict(v5['qualification'],actual_TW_command_common_definition_handoff_source_connected=True,actual_TW_native_command_host_complete=False),TW_command_source='Exact original digestchecked TW and issued/requested-native row + retained owning common Scope -> existing qualification/current/action/after_action callbacks; no old catalog/grant reread after actual action',owner_resumed_after_round364=True)
oldledger=json.loads((S/L).read_bytes());assert K not in oldledger;rb=(S/R).read_bytes();assert K.encode() not in rb
for old,line in [(f"                   set(ledger.get('{OLDK}', {{}}).get('source_paths', [])) |\n".encode(),f"                   set(ledger.get('{K}', {{}}).get('source_paths', [])) |\n".encode()),(f"        '{OLDK}': ledger.get('{OLDK}'),\n".encode(),f"        '{K}': ledger.get('{K}'),\n".encode())]:assert rb.count(old)==1;rb=rb.replace(old,old+line)
gb=(S/G).read_bytes();append=b'\n\n## Round365 - common definition at existing TW command interface (2026-10-13)\n\nOwner resumed; round364 stop is historical/revoked. CUSTOM-0143 adds owning\ncommon Scope to actual existing TW qualification/current/action/after_action\nhandoff. Original digestchecked TW/issued/requested-native exact row and all\nprimary/secondary grammar/actor/list gates stay. Preaction same common value\nreobserved, no rebase; after action only actual next receipt, no consumed old\ncatalog/grant reread or durable retry/rollback. Sequential cuts not atomic CAS.\nTwo source handoff branches; no actual default host/formula/opcode/fullroute\ncredit. TW156/252 world74=50partial+11control+13unconnected; CN156/280phase/253\nsupported unchanged. CN126/150 profile/resources/actor/learned/87/effects open.\nSourcecontract source/6; native slice facts retained in immutable N365 upstream.\nPHASE1 no build/tests/native/runtime/API/VM/codec/gameDBSQL/migrate/activate/deploy.\nWhole denominator/percentage unknown; full goal active.\n'
paths=sorted(set(oldledger[OLDK]['source_paths']+[p['path'] for p in pins]+[DOC,CONTRACT]+[r['published_path'] for r in copies]));assert len(paths)==404+2+2+len(copies)
value=dict(round=REPORT,round_number=365,classification='EXISTING_TW_COMMAND_COMMON_DEFINITION_HANDOFF',previous_goal_turn_classification='progress',source_paths=paths,document=DOC,source_contract=CONTRACT,custom_design='CUSTOM-0143',existing_Cplusplus_files_modified=2,new_Cplusplus_files=0,new_native_opcode_values=0,new_native_methods_credited=0,new_recovered_skill_formulas=0,new_authoritative_handlers=0,new_world_parser_opcode_values=0,new_independent_S2C_format_classes=0,new_connected_source_branches=2,new_complete_bidirectional_routes=0,new_phase_source_bindings=0,connected_source_branches=[dict(C2S='existing TW35 native skill sequence',source=mode,handoff='actual WorldOwner qualification/current/action/after_action Scope',native_acceptance=False,host_complete=False) for mode in ['actual_primary_issued_selection','actual_independent_secondary_issued_selection']],owning_common_definition=True,original_requested_TW_raw_preserved=True,same_full_common_not_rebase=True,sequential_not_atomic_CAS=True,old_source_not_queried_after_action=True,CN_custom_cast_source_connected=False,TW_native_command_actual_host_complete=False,original_CN_453_unchanged=True,compiled907_row_pins_unchanged=True,postCOMMIT_rollback_claim=False,native_source=review['native_source'],all_prior_ledger_fields_preserved=True,frontier_v23_byte_identical=True,whole_game_denominator=None,whole_game_completion_percent=None,goal_status='active',owner_resumed_after_round364=True,phase='PHASE1',build=False,test=False,runtime=False,native_execution=False,VM=False,codec=False,game_database_SQL=False,migrate=False,activate=False,deploy=False,remaining=['Actual full TW native issued roster/control/actor/learned/action/persistence suppliers','CN126/150 qualified profile/effects/actor/committed87 and actual host','Every original skill formula and poison current maximumHP/10 actual status pipeline','Complete TW-CN-fourWS direction/phase/state/variant routes and later acceptance'])
assert not (S/DOC).exists() and not (S/CONTRACT).exists()
for r in copies:write(S/r['published_path'],Path(r['original_path']).read_bytes())
(S/'docs/custom-designs.json').write_bytes(newindex);(S/'AGENTS.md').write_bytes(agn+agn_append);write(S/DOC,doc);js(S/CONTRACT,contract);(S/R).write_bytes(rb);(S/G).write_bytes(gb+append);ledger=dict(oldledger);ledger[K]=value;assert all(ledger[k]==v for k,v in oldledger.items());(S/L).write_bytes((json.dumps(ledger,ensure_ascii=False,indent=2)+'\n').encode())
js(D/'final-Cplusplus-source-pins.json',pins);js(D/'ledger-value.json',value);js(D/'capture-publication-copies.json',copies);js(D/'upstream-packages.json',upstreams);js(D/'goal-append-custody.json',dict(before_bytes=len(gb),before_sha256=sha(gb),append_bytes=len(append),after_bytes=len(gb+append),after_sha256=sha(gb+append)));js(D/'stage-custody.json',dict(source_paths=len(paths),source_pins=pins,contract_pins=allpins,inverse_edits=len(inverse),copied_helpers=len(copies),new_id='CUSTOM-0143',document=DOC,source_contract=CONTRACT,custom_designs_before=140,custom_designs_after=141,owner_resumed=True))
print(json.dumps(dict(source_paths=len(paths),modified_Cplusplus=2,copied_helpers=len(copies),inverse_edits=len(inverse),upstream_members=sum(x['members'] for x in upstreams),upstream_bytes=sum(x['member_bytes'] for x in upstreams),new_source_branches=2,complete_routes=0,goal_status='active')))
