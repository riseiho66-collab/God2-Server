from pathlib import Path
import json,hashlib
S=Path('C:/Users/risei/Desktop/God2/God2-Server');A=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261013');D=A/'tw-cn-owned-skill-bootstrap-write-362';T=A/'round362-owned-skill-bootstrap-write-implementation';N=A/'round362-cn-custom-skill-action-state-source';P=A/'round362-shared-owned-skill-publication-authority';I=A/'round362-owned-skill-bootstrap-independent-source-review'
L='artifacts/integration/packet-connections-20261006/packet-route-ledger.json';F='artifacts/integration/packet-connections-20261006/s2c-world-consumer-frontier-v23.json';G='docs/PACKET_CONNECTION_GOAL_20261006.md';R='tools/reconstruction/packet_connection_report.py';K='tw_cn_owned_skill_bootstrap_write_source362';REPORT='20261013-tw-cn-owned-skill-bootstrap-write-source-362';DOC='docs/research/common-owned-skill-bootstrap-20261013.md';CONTRACT='docs/integration/SHARED_SKILL_SERVER_SOURCE_V3.json';sha=lambda b:hashlib.sha256(b).hexdigest()
def write(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(b)
def js(p,v):write(p,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
def package(root):
 name='seal.json' if (root/'seal.json').exists() else 'SEAL.json';raw=(root/name).read_bytes();v=json.loads(raw);seen=set();total=0
 for m in v['members']:
  rel=m.get('path') or m['name'];p=root/rel;b=p.read_bytes();assert p.resolve().is_relative_to(root.resolve()) and rel not in seen and type(m['bytes']) is int and len(b)==m['bytes'] and sha(b)==m['sha256'];seen.add(rel);total+=len(b)
 assert type(v['member_count']) is int and v['member_count']==len(seen)
 for key in ['member_bytes','total_bytes']:
  if key in v:assert type(v[key]) is int and v[key]==total
 return dict(root=root.as_posix(),seal_filename=name,seal_sha256=sha(raw),members=len(seen),member_bytes=total)
upstreams=[package(N),package(P),package(T),package(I)]
expected=[(17,78839,'908e600e85b79a696b2045997bfd786b1d2be0db6e5c25b6a1a3750db5bf000c'),(46,1360898,'9d28223c7297bdd9ab1a9ba3dc18e65ac179e1fc932f433f55d215be77c1050b'),(60,5368563,'a204410db0e30bdb0dde9a4ad95bab66cca00b2b096e8313585ccff9710371fe'),(48,2975179,'b144687f8bbbf98b631f04175a4e83a22979bdbe8b253513906db8e96d882e69')]
assert [(r['members'],r['member_bytes'],r['seal_sha256']) for r in upstreams]==expected
pins=json.loads((D/'final-Cplusplus-source-pins.json').read_bytes());assert len(pins)==3 and sum(x['bytes'] for x in pins)==792710
for r in pins:
 b=(S/r['path']).read_bytes();assert len(b)==r['bytes'] and sha(b)==r['sha256']
inverse=[]
for name in ['exact-edits-and-inverse.json','identity-correction-v4.json','transition-correction-v5.json']:inverse+=json.loads((T/name).read_bytes())['edits']
assert len(inverse)==21
for r in pins:
 b=(S/r['path']).read_bytes()
 for e in reversed(inverse):
  if e['path']==r['path']:
   n=bytes.fromhex(e['new_hex']);o=bytes.fromhex(e['old_hex']);assert b.count(n)==e.get('count',1);b=b.replace(n,o)
 assert b==(D/'before'/r['path']).read_bytes()
oldledger=json.loads((D/'before'/L).read_bytes());assert (S/L).read_bytes()==(D/'before'/L).read_bytes() and (S/F).read_bytes()==(D/'before'/F).read_bytes()
allowed={r['path'] for r in pins}|{'AGENTS.md','docs/custom-designs.json'}
for r in json.loads((D/'before-manifest.json').read_bytes())['members']:
 if r['path'] not in allowed:assert (S/r['path']).read_bytes()==(D/'before'/r['path']).read_bytes()
oldindex=json.loads((D/'before'/'docs/custom-designs.json').read_bytes());newindex=json.loads((S/'docs/custom-designs.json').read_bytes());assert len(newindex['designs'])==138 and newindex['designs'][:-1]==oldindex['designs'] and newindex['designs'][-1]['id']=='CUSTOM-0140';assert (S/'AGENTS.md').read_bytes().startswith((D/'before'/'AGENTS.md').read_bytes())
helpers=[N/'discover_action_state362.py',N/'capture_action_state362.py',P/'capture_skill_publication_authority362.py',T/'capture_owned_bootstrap_custody362.py',T/'seal_owned_bootstrap_custody362.py',I/'capture_owned_skill_bootstrap_review362.py',A/'complete-owned-skill-publication-policy362_v2.py',A/'stage-owned-bootstrap-source362.py'];copies=[]
for p in helpers:
 b=p.read_bytes();assert b'\r' not in b and not b.startswith(b'\xef\xbb\xbf') and b.endswith(b'\n') and not b.endswith(b'\n\n');rel='tools/reconstruction/'+p.name;assert not (S/rel).exists();copies.append(dict(original_path=p.as_posix(),published_path=rel,bytes=len(b),sha256=sha(b)))
rb=(S/R).read_bytes();assert K.encode() not in rb
for old,line in [(b"                   set(ledger.get('tw_cn_common_owned_skill_commit_source361', {}).get('source_paths', [])) |\n",b"                   set(ledger.get('tw_cn_owned_skill_bootstrap_write_source362', {}).get('source_paths', [])) |\n"),(b"        'tw_cn_common_owned_skill_commit_source361': ledger.get('tw_cn_common_owned_skill_commit_source361'),\n",b"        'tw_cn_owned_skill_bootstrap_write_source362': ledger.get('tw_cn_owned_skill_bootstrap_write_source362'),\n")]:assert rb.count(old)==1;rb=rb.replace(old,old+line)
v2=json.loads((S/'docs/integration/SHARED_SKILL_SERVER_SOURCE_V2.json').read_bytes());by={r['path']:r for r in pins};allpins=[by.get(r['path'],r) for r in v2['source_files']];assert len(allpins)==7
for r in allpins:
 b=(S/r['path']).read_bytes();assert len(b)==r['bytes'] and sha(b)==r['sha256']
contract=dict(contract_version='god2-server/shared-skills/source/3',phase='PHASE1',custom_designs=['CUSTOM-0138','CUSTOM-0139','CUSTOM-0140'],source_files=allpins,traditional_names_primary=True,skills=v2['skills'],qualification=dict(common_definition_query_source_connected=True,common_saved_readset_consumption_source_connected=True,actual_TW_diagnostic_bootstrap_roster_source_connected=True,actual_original_callback_write_custody_source_connected=True,actual_general_TW_gameplay_host_complete=False,full_native_primary_secondary_list_qualified=False,native_list_adoption=False,native_turn_grant=False,native_processing_ACK=False,native_input_barrier=False,CN_custom_cast_source_connected=False,CN_custom_native_profile_qualified=False,CN_native_effect_source_qualified=False,CN_runtime_enabled=False,learned_grant=False,native_source=False),publication_source='One complete selected saved roster -> unchanged actual87/id/80 producer -> same full callback frame captured before actual service binding -> typed final full-roster qualifier',owned_bootstrap_epoch='Original tuple fence adjacent existing set_state; only actual result tuple, independent of cosmetic pose, no predicted increment or observer rebase',command_source='Optional opted receipt requires Written and current plus existing361 fresh learned observation and same-txn persistence',remaining_timing='Passive local receipt has no input barrier; Pending early-arrival ordering/native interaction acceptance open',postcommit_fence_limit=v2['postcommit_fence_limit'],persistence_branches=v2['persistence_branches'],owned_settlement_request_version=4,ordinary_requests_preserved=True,new_native_formulas=0,build=False,test=False,runtime=False,game_database_SQL=False,migrate=False,activate=False,deploy=False)
append=('\n\n## Round362 — actual common owner skill bootstrap/write custody (2026-10-13)\n\n'
 'CUSTOM-0140 replaces actualApp two owned-skill booleans with ONE complete\n'
 'saved deity roster for126/150; existing shared definition getter consumes\n'
 'formal owner-rule key/design only, not raw native data or learned grants.\n'
 'Keep original87/id/80 flags/order and finalvitals. Sameframe encoded once,\n'
 'captured by actualSession WorldResponseWrite before realservice bind, then\n'
 'returned through the same original world callback/FIFO. Typed fullroster\n'
 'qualifier guards actualbinding/controller/keyset/private receipt/Session\n'
 'around actualrepository observer with reentry poison/deferredremove. Fence\n'
 'originaltuple before existing InBattle transition and freeze only its actual\n'
 'result epoch, separate from cosmeticpose; no predicted increment or rebase.\n'
 'Optedowned C35 requires localWritten/current plus361 fresh savedreadset/CAS.\n'
 'Written is not nativeACK/cache/listadoption/turngrant or inputbarrier; Pending\n'
 'earlyarrival/native scheduling acceptance remainsOPEN. No-afterCOMMIT rollback\n'
 'is claimed. Ordinary/trial/revival packet/rule defaults and TW effects remain.\n\n'
 'OriginalCN564A30..564C6D closes573codeB/166sites/29branches/6RET14h.\n'
 'It consumes lowBYTE modifiers and updates actionstate/packedtarget arrays;\n'
 'no ownqueuedHP28A/arithmetic/death/64-bit reader proved. Opaquechildren OPEN.\n'
 'N36217/78839 seal908e600e85b79a696b2045997bfd786b1d2be0db6e5c25b6a1a3750db5bf000c.\n'
 'ActualCNhost/actor/list/resources/native87/effects and fullTWnativeprimary/\n'
 'secondary/control/auxiliary/roster providers remainOPEN; originalCN453 and\n'
 'full907 compiled row pins unchanged. Sourcecontract shared-skills/source/3.\n\n'
 'New actual ownedbootstrap sourcebranches2; completebidirectional routes0;\n'
 'nativeopcode/methodcredit/formulas0. TW156C2S/252S2C, world74=50partial+\n'
 '11control+13unconnected; CN156C2S/280phase/253supported lengths unchanged.\n'
 'Whole denominator/percentage unknown. PHASE1 no compiler/build/tests/runtime/\n'
 'native/API/CRT/VM/codec/gameDBSQL/migrate/activate/deploy. Goal active.\n').encode()
gb=(S/G).read_bytes();assert gb==(D/'before'/G).read_bytes()
for r in copies:write(S/r['published_path'],Path(r['original_path']).read_bytes())
js(S/CONTRACT,contract);(S/R).write_bytes(rb);(S/G).write_bytes(gb+append)
paths=sorted(set(oldledger['tw_cn_common_owned_skill_commit_source361']['source_paths']+[DOC,CONTRACT]+[r['published_path'] for r in copies]));assert len(paths)==382
value=dict(round=REPORT,round_number=362,classification='ACTUAL_COMMON_OWNER_BOOTSTRAP_ROSTER_AND_ORIGINAL_WRITE_CUSTODY',previous_goal_turn_classification='progress',source_paths=paths,document=DOC,source_contract=CONTRACT,custom_design='CUSTOM-0140',existing_Cplusplus_files_modified=3,new_Cplusplus_files=0,new_native_opcode_values=0,new_native_methods_credited=0,new_recovered_skill_formulas=0,new_authoritative_handlers=0,new_world_parser_opcode_values=0,new_independent_S2C_format_classes=0,new_connected_source_branches=2,new_complete_bidirectional_routes=0,new_phase_source_bindings=0,connected_source_branches=[dict(C2S='existing Timer36 bootstrap then ownedC35',S2C='same actual87/id/80 fullframed callback',key=[0,i],actual_source='Application one fullroster namespace and originalWWR->typedservice qualifier',native_acceptance=False) for i in [126,150]],one_full_saved_roster=True,formal_namespace_not_native_rows_or_grant=True,actual_original_write_custody=True,private_response_identity=True,independent_owned_epoch=True,only_actual_existing_transition=True,typed_same_repository_final_observer=True,local_Written_not_native_ACK_or_cache=True,native_input_barrier=False,early_arrival_acceptance_open=True,original_CN_453_unchanged=True,CN_host_or_cast_source_connected=False,full_native_issued_list_qualified=False,postCOMMIT_rollback_claim=False,native_source=dict(body='564A30..564C6D',complete_code_bytes=573,aligned_reachable_sites=166,closed_direct_branches=29,RET_sites=6,modifiers_low_BYTE=True,actual_HP_mutation_qualified=False,queued_delta_reader_qualified=False,opaque_children_expanded=False),all_prior_ledger_fields_preserved=True,frontier_v23_byte_identical=True,whole_game_denominator=None,whole_game_completion_percent=None,tw_completion_percent=None,goal_status='active',phase='PHASE1',build=False,test=False,runtime=False,native_execution=False,VM=False,codec=False,game_database_SQL=False,migrate=False,activate=False,deploy=False,remaining=['ActualCN custom host/actor/list/resources/native87/effects','FullTW native primary/secondary/control/auxiliary/roster sources and native early-input acceptance','Real queued HP arithmetic/death/wide64 consumers','Common poison maximumHP/10 status/turn/checkpoint','Every original skill formula and complete TW-CN-fourWS directional/state/variant inventory'])
assert K not in oldledger;ledger=dict(oldledger);ledger[K]=value;assert all(ledger[k]==x for k,x in oldledger.items());(S/L).write_bytes((json.dumps(ledger,ensure_ascii=False,indent=2)+'\n').encode())
js(D/'ledger-value.json',value);js(D/'capture-publication-copies.json',copies);js(D/'upstream-packages.json',upstreams);js(D/'goal-append-custody.json',dict(before_bytes=len(gb),before_sha256=sha(gb),append_bytes=len(append),after_bytes=len(gb+append),after_sha256=sha(gb+append)));js(D/'stage-custody.json',dict(source_paths=len(paths),source_pins=pins,contract_pins=allpins,inverse_edits=21,copied_helpers=len(copies),new_id='CUSTOM-0140',document=DOC,source_contract=CONTRACT))
print(json.dumps(dict(source_paths=len(paths),modified_Cplusplus=3,copied_helpers=len(copies),inverse_edits=21,upstream_members=sum(x['members'] for x in upstreams),upstream_bytes=sum(x['member_bytes'] for x in upstreams),new_source_branches=2,complete_routes=0,goal_status='active')))
