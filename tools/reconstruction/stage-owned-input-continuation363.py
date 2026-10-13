from pathlib import Path
import json,hashlib,subprocess
S=Path('C:/Users/risei/Desktop/God2/God2-Server');A=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261013');D=A/'tw-cn-owned-skill-input-continuation-363'
L='artifacts/integration/packet-connections-20261006/packet-route-ledger.json';F='artifacts/integration/packet-connections-20261006/s2c-world-consumer-frontier-v23.json';G='docs/PACKET_CONNECTION_GOAL_20261006.md';R='tools/reconstruction/packet_connection_report.py';K='tw_cn_owned_skill_input_continuation_source363';OLDK='tw_cn_owned_skill_bootstrap_write_source362'
DOC='docs/research/common-owned-skill-input-continuation-20261013.md';CONTRACT='docs/integration/SHARED_SKILL_SERVER_SOURCE_V4.json';REPORT='20261013-tw-cn-owned-skill-input-continuation-source-363';sha=lambda b:hashlib.sha256(b).hexdigest()
def write(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(b)
def js(p,v):write(p,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
def package(root):
 name='seal.json' if (root/'seal.json').is_file() else 'SEAL.json';raw=(root/name).read_bytes();v=json.loads(raw);seen=set();total=0
 for m in v['members']:
  rel=m.get('path') or m['name'];p=root/rel;b=p.read_bytes();assert p.resolve().is_relative_to(root.resolve()) and rel not in seen and type(m['bytes']) is int and m['bytes']>=0 and len(b)==m['bytes'] and sha(b)==m['sha256'];seen.add(rel);total+=len(b)
 assert type(v['member_count']) is int and v['member_count']==len(seen)
 for key in ['member_bytes','total_bytes']:
  if key in v:assert type(v[key]) is int and v[key]==total
 return dict(root=root.as_posix(),seal_filename=name,seal_sha256=sha(raw),members=len(seen),member_bytes=total)
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=S,text=True).strip()=='566923291db5de40dcc7d1a153cde60cfc94d87c'
review=json.loads((D/'approved-candidate.json').read_bytes());pins=review['source_files'];inverse=review['inverse_edits'];assert len(pins)==3 and {r['path'] for r in pins}=={'src/net/Session.h','src/net/Session.cpp','src/core/Application.cpp'}
for r in pins:
 b=(S/r['path']).read_bytes();assert len(b)==r['bytes'] and sha(b)==r['sha256']
 for e in reversed(inverse):
  if e['path']==r['path']:
   n=bytes.fromhex(e['new_hex']);o=bytes.fromhex(e['old_hex']);assert b.count(n)==e.get('count',1);b=b.replace(n,o)
 assert b==(D/'before'/r['path']).read_bytes()
upstreams=[package(Path(p)) for p in review['upstream_roots']];assert len(upstreams)==4 and upstreams==review['upstream_packages']
helpers=[Path(p) for p in review['published_helpers']]+[A/'stage-owned-input-continuation363.py'];copies=[]
for p in helpers:
 b=p.read_bytes();assert b'\r' not in b and not b.startswith(b'\xef\xbb\xbf') and b.endswith(b'\n') and not b.endswith(b'\n\n');rel='tools/reconstruction/'+p.name;assert not (S/rel).exists();copies.append(dict(original_path=p.as_posix(),published_path=rel,bytes=len(b),sha256=sha(b)))
oldledger=json.loads((D/'before'/L).read_bytes());assert (S/L).read_bytes()==(D/'before'/L).read_bytes() and (S/F).read_bytes()==(D/'before'/F).read_bytes() and K not in oldledger
for r in json.loads((D/'before-manifest.json').read_bytes())['members']:
 if r['path'] not in {p['path'] for p in pins}:assert (S/r['path']).read_bytes()==(D/'before'/r['path']).read_bytes()
index=(S/'docs/custom-designs.json').read_bytes();oldindex=json.loads(index);assert len(oldindex['designs'])==138 and not any(x['id']=='CUSTOM-0141' for x in oldindex['designs']) and index.endswith(b'\n]\n}\n')
entry=dict(id='CUSTOM-0141',name='Actual owned bootstrap response input continuation',authority='OWNER_CUSTOM_SOURCE_OWNERSHIP_NOT_NATIVE_ACK_LIST_OR_TURN_GRANT',implementation=[r['path'] for r in pins],native_gap='Local bootstrap input ordering was not fenced by passive Written receipt. CN host/list/actor/resources/effects and client acceptance remain unqualified.',rules=dict(scope='Only actual typed owner126/150 bootstrap arms its existing private response Attempt; ordinary and passive receipt paths preserve their defaults.',installation='Exact private Attempt installed atomically on game before original response handoff; network observes immutable receipt and atomic lifecycle/phase/epoch, never game-owned account fields.',input='Preserve original bounded raw bytes, staged batch semantics, native skill generation/deadline and read ownership; no extra read, packet split or reclassification.',completion='Same FIFO full response must physically complete and old completion/bookkeeping succeed before exact current hold releases input once.',failure='Retire hold and prohibit continuation before fallible logging/close paths; stale epoch/drop/exception never releases. Physical Written fact remains local and is not demoted.',limits='No native ACK, remote cache/list adoption, turn grant, learned rights, durable rollback or CN wire/effect proof is inferred.'),activation=False,production_activated=False,schema_installed=False,deployment=False,native_client_acceptance=False,tests=[],verification_status='NOT_RUN_PHASE1_STATIC_SOURCE_ONLY',reason='Connect existing actual owner-skill bootstrap to original input continuation while preserving authoritative common learned/persistence rules.',replacement='Complete native providers and CN actual gameplay adapter, then comprehensive build/tests/current-client acceptance.')
newindex=index[:-len(b'\n]\n}\n')]+b',\n'+json.dumps(entry,ensure_ascii=False,indent=2).encode()+b'\n]\n}\n';check=json.loads(newindex);assert check['designs'][:-1]==oldindex['designs']
agents=(S/'AGENTS.md').read_bytes();agents_append=b'\nCUSTOM-0141 connects only the actual typed owner126/150 bootstrap to an exact\nprivate response input continuation. Install its Attempt atomically on game\nbefore the original handoff; retain bounded raw input and original batches.\nOnly that FIFO response full write plus successful old bookkeeping/current\nphase and epoch may release once, preserving read ownership. Retire first on\nfailure/drop/exception, before fallible logging; Written stays physical local\ncustody, not native ACK/cache/list adoption/turn grant or durable rollback.\nOther passive/ordinary defaults and CN host/list/resources/effects remain open.\n'
doc='''# Common owner skills: original response input continuation

PHASE1 static source only. CUSTOM-0141 extends the actual isolated TW
diagnostic bootstrap for 瞬影三煞斬 (126, CUSTOM-0058) and 牛轉仙界踏
(150, CUSTOM-0059). Both remain required in the common TW/CN definition,
Traditional names, learned-rights and persistence pipeline. CN actual hosting,
native framing/effect resources and live acceptance remain open.

## Actual source connection

The existing bootstrap already derives both keys from ONE full saved roster,
fences its original battle transition and captures the SAME complete callback
response before actual service binding. The passive local write receipt alone
did not prevent input continuation while the response waited in the FIFO.

The actual final typed bootstrap now opts that same private Attempt into an
input hold before returning the original response. The game executor publishes
the exact hold atomically before posting the response to the network strand.
Older posted feed/read continuations see this identity rather than a later
strand-only flag. IO uses immutable receipt data and atomic phase/epoch/lifecycle
checks; it does not read game-owned account or character fields.

The hold retains bounded original input. It does not split a previously parsed
Timer36/C35 batch, reinterpret an old prefix, create learned keys, bypass
staged-record quotas, renew native deadlines or create a second read. The
existing native battle and PK holds keep their separate contracts.

The hold begins at the actual game arm. It cannot retroactively turn already
parsed or queued pre-arm batches into raw input. Such ambiguous overlap must
not commit through the new hold; whole-batch rejection/retirement is distinct
from successful input continuation. Native timing acceptance remains open.

Only the identical full FIFO response can complete this hold. Its entire write,
original completion markers, logging and queue bookkeeping must succeed first.
The same current phase/epoch then releases once through the original input
continuation and preserves game_busy/read_inflight ownership.

Failure, rejected callback, dropped handoff, stale epoch and opted exceptions
retire the hold before fallible logging or close handling; they do not continue
successor input. The physically Written receipt is never relabeled as Failed
after a later failure. A local write is not native ACK, cache/list adoption,
turn grant or a successful durable rollback. General executor convergence when
an external executor stops without destroying queued work remains open.

## Scope and evidence limits

Only Session.h/.cpp and the actual Application bootstrap change. Existing
Service/DB transaction ownership, original custom rule values, TW direction,
caster shadows, clones and four presentation phases remain unchanged. The
complete original CN453 source and all compiled row pins remain unchanged.

This does not prove original client formula equality or add a custom opcode.
Complete native primary/secondary/control/auxiliary roster sources, CN actors,
list/resources/87/effects, queued HP arithmetic and poison current maximumHP/10
status/turn/checkpoint integration remain separate work.

Source contract: shared-skills/source/4. Two existing owner bootstrap source
branches gain this continuation; complete bidirectional route credit is zero.
TW156 C2S/252 supported S2C; CN156 C2S/280 phase entries/253 supported lengths
are unchanged. Whole-game denominator and percentage remain unknown.

No compiler, build, tests, native/runtime/VM/codec execution, game DB SQL,
migration, activation or deployment was performed.
'''.encode()
oldcontract=json.loads((S/'docs/integration/SHARED_SKILL_SERVER_SOURCE_V3.json').read_bytes());contract=dict(oldcontract);by={r['path']:r for r in pins};allpins=[by.get(r['path'],r) for r in oldcontract['source_files']]+[by[p] for p in ['src/net/Session.h','src/net/Session.cpp']];assert len(allpins)==9
for r in allpins:
 b=(S/r['path']).read_bytes();assert len(b)==r['bytes'] and sha(b)==r['sha256']
contract.update(contract_version='god2-server/shared-skills/source/4',custom_designs=oldcontract['custom_designs']+['CUSTOM-0141'],source_files=allpins,remaining_timing='Exact opted original callback response holds bounded input through actual full write and successful old bookkeeping; native interaction acceptance/general executor convergence remain open',owned_input_continuation='Exact private Attempt published atomically on game; same FIFO full response/current phase+epoch releases original input once; failure retires first',qualification=dict(oldcontract['qualification'],actual_owned_response_input_continuation_source_connected=True,native_input_barrier=False))
rb=(S/R).read_bytes();assert K.encode() not in rb
for old,line in [(f"                   set(ledger.get('{OLDK}', {{}}).get('source_paths', [])) |\n".encode(),f"                   set(ledger.get('{K}', {{}}).get('source_paths', [])) |\n".encode()),(f"        '{OLDK}': ledger.get('{OLDK}'),\n".encode(),f"        '{K}': ledger.get('{K}'),\n".encode())]:assert rb.count(old)==1;rb=rb.replace(old,old+line)
gb=(S/G).read_bytes();append=('\n\n## Round363 — actual owned bootstrap input continuation (2026-10-13)\n\n'
 'CUSTOM-0141 connects the actual126/150 bootstrap private response Attempt\n'
 'to original input continuation: atomic game publication before handoff,\n'
 'bounded raw bytes and old batch/read/deadline ownership; identical FIFO\n'
 'full write plus successful old bookkeeping/current phase+epoch releases\n'
 'once. Failure/drop/exception retires first, before fallible logging. Local\n'
 'Written is not native ACK/cache/list adoption/turn grant or durable rollback.\n'
 'Source contract shared-skills/source/4; 3existing C++files, 2existing owner\n'
 'bootstrap branches, 0complete bidirectional routes/opcodes/native formulas.\n'
 'TW156/252 world74=50partial+11control+13unconnected; CN156/280phase/253\n'
 'supported lengths unchanged. CN actual host/list/resources/87/effects and\n'
 'full native roster/control/auxiliary/queuedHP/poison status remain OPEN.\n'
 'PHASE1 static only: no compiler/build/tests/runtime/native/VM/codec/gameDBSQL/\n'
 'migrate/activate/deploy. Whole denominator/percentage unknown; goal active.\n').encode()
paths=sorted(set(oldledger[OLDK]['source_paths']+[DOC,CONTRACT]+[r['published_path'] for r in copies]));assert len(paths)==len(oldledger[OLDK]['source_paths'])+2+len(copies)
value=dict(round=REPORT,round_number=363,classification='ACTUAL_OWNED_BOOTSTRAP_ORIGINAL_INPUT_CONTINUATION',previous_goal_turn_classification='progress',source_paths=paths,document=DOC,source_contract=CONTRACT,custom_design='CUSTOM-0141',existing_Cplusplus_files_modified=3,new_Cplusplus_files=0,new_native_opcode_values=0,new_native_methods_credited=0,new_recovered_skill_formulas=0,new_authoritative_handlers=0,new_world_parser_opcode_values=0,new_independent_S2C_format_classes=0,new_connected_source_branches=2,new_complete_bidirectional_routes=0,new_phase_source_bindings=0,connected_source_branches=[dict(C2S='existing Timer36 bootstrap then ownedC35',S2C='same full original callback response',key=[0,i],actual_source='exact private response Attempt->bounded original input continuation',native_acceptance=False) for i in [126,150]],exact_private_attempt=True,game_atomic_publication=True,original_bounded_raw_input=True,same_FIFO_full_write=True,old_bookkeeping_before_release=True,read_ownership_preserved=True,failure_retires_before_logging=True,Written_not_demoted=True,local_Written_not_native_ACK_or_cache=True,native_input_barrier=False,original_CN_453_unchanged=True,CN_host_or_cast_source_connected=False,full_native_issued_list_qualified=False,postCOMMIT_rollback_claim=False,all_prior_ledger_fields_preserved=True,frontier_v23_byte_identical=True,whole_game_denominator=None,whole_game_completion_percent=None,tw_completion_percent=None,goal_status='active',phase='PHASE1',build=False,test=False,runtime=False,native_execution=False,VM=False,codec=False,game_database_SQL=False,migrate=False,activate=False,deploy=False,remaining=['Actual CN custom host/actor/list/resources/native87/effects','Full native TW roster/control/auxiliary/primary-secondary sources and native interaction acceptance','Actual queued HP arithmetic/death/wide64 consumers','Poison current maximumHP/10 actual status/turn/checkpoint','Complete TW-CN-fourWS original direction/phase/state/variant coverage'])
assert not (S/DOC).exists() and not (S/CONTRACT).exists()
for r in copies:write(S/r['published_path'],Path(r['original_path']).read_bytes())
(S/'docs/custom-designs.json').write_bytes(newindex);(S/'AGENTS.md').write_bytes(agents+agents_append);write(S/DOC,doc);js(S/CONTRACT,contract);(S/R).write_bytes(rb);(S/G).write_bytes(gb+append)
ledger=dict(oldledger);ledger[K]=value;assert all(ledger[k]==x for k,x in oldledger.items());(S/L).write_bytes((json.dumps(ledger,ensure_ascii=False,indent=2)+'\n').encode())
js(D/'final-Cplusplus-source-pins.json',pins);js(D/'ledger-value.json',value);js(D/'capture-publication-copies.json',copies);js(D/'upstream-packages.json',upstreams);js(D/'goal-append-custody.json',dict(before_bytes=len(gb),before_sha256=sha(gb),append_bytes=len(append),after_bytes=len(gb+append),after_sha256=sha(gb+append)));js(D/'stage-custody.json',dict(source_paths=len(paths),source_pins=pins,contract_pins=allpins,inverse_edits=len(inverse),copied_helpers=len(copies),new_id='CUSTOM-0141',document=DOC,source_contract=CONTRACT,custom_designs_before=138,custom_designs_after=139,agents_append_bytes=len(agents_append)))
print(json.dumps(dict(source_paths=len(paths),modified_Cplusplus=3,copied_helpers=len(copies),inverse_edits=len(inverse),upstream_members=sum(x['members'] for x in upstreams),upstream_bytes=sum(x['member_bytes'] for x in upstreams),new_source_branches=2,complete_routes=0,goal_status='active')))
