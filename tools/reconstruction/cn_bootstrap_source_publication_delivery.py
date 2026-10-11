"""File-only CN initial bootstrap actual issuer -> state/IO publication source."""
import hashlib
import json
from .cn_wrapper_route_frontier import ROOT,PIN

NAME='cn-bootstrap-source-publication-01'
ROUND='20261007-cn-bootstrap-source-publication'
SOURCES=('src/cn/world/SharedWorldReady.h','src/cn/world/SharedWorldReady.cpp',
    'src/cn/world/SharedWorldGameplay.h','tools/reconstruction/dual_client_route_catalog.py',
    'tools/reconstruction/cn_bootstrap_source_publication_delivery.py',
    'docs/research/cn-bootstrap-source-publication-20261007.md')
REMAINING=[
    'Actual native1F/23/30/36 data/control/issuer/rule suppliers must return the qualified full output or an explicitly proven no-output result; no configured provider or native response causality is recovered here.',
    'Initial1C still activates common presence before the actual entered callback; entered/visibility/gameplay publication, normal/CF lifecycle and configured Application hosting remain open.',
    'Durable operation/semantic replay and committed state/output/crash/cross-process recovery remain open.',
    'All TW/CN/web gameplay and numeric wire/object/display, exhaustive directional phase/state/variant/indirect/deferred denominator and later comprehensive original-client acceptance remain open. Levels unchanged.']
DOCUMENT='''# CN initial bootstrap: actual issuer and state publication before output

PHASE1 static source integration/accounting only. No build, test, native/API/codec/resource/server/SQL execution, migration or deployment. Previous selected1F/02/2A turn is progress: source changes and catalog96/report sealed. Levels, original wire, frozen accounts/saves/fonts/conversion and unrelated features unchanged.

The existing source consumed1F00 ->2300 ->1C(handle,0), allowing complete30(00) and36(opaque8) between initial steps. Bootstrap used a boolean completion, and changed its stage only after that callback. This did not bind full source output and the actual publication stage to the existing held native IO barrier. The retained ready-owner manifest and bounded native control contract remain historical evidence; this round does not reread a deleted TW mapped image or recover new native responses/rules.

Bootstrap now returns an optional BootstrapResult. A mandatory observing current predicate receives BeforePublish and QueueAccepted. with_output requires nonempty complete source-issued aggregates under the unchanged transport bounds; without_output is a separate explicit actual-source decision requiring the same predicate. Missing result/predicate or invalid bounds fails. Neither factory guesses formats, reply pairing, status, permissions or native no-response semantics. A provider must qualify causality/full bytes against the complete retained request, exact reservation/resources/rules and connection; it cannot send output itself, yield, write storage or pump events while observing publication.

The existing ready dispatch preserves each full request, including all eight opaque36 bytes. Its single-use source completion retains the actual result, expected current ready stage and batch. Before scheduling it checks the same connection/account/world session, exact common preparation lease/position/ownership and real world admission ticket before and after the actual issuer predicate. Output passes directly into SharedCredentialConnection::send_world_batch_with_publication, reusing its same verified identity/registry and native framing/capacity/held-head barrier. Inside that game publication, QueueAccepted is qualified around the same pending state, then the next ready stage is committed before any held bytes leave. Interleaved30/36 uses the same original stage rather than skipping/resetting1F/23.

Explicit no-output results run that same serial observing/publication transition without manufacturing an acknowledgement or invoking the IO transport with an empty batch. QueueAccepted in this branch means local source publication; it is not transport receipt or proof that native30/36 has no reply. Queue completion observes the exact published marker and live same lease/connection, then resumes the remaining original aggregate. It does not re-run an obsolete request/stage issuer predicate after bytes leave. A source callback is single-use across inline/deferred result and exceptions; completed-batch failure cannot tear down a successor. IO failure closes/releases this original incarnation; no saved-state rollback or client-receipt claim.

Ready-world ongoing30/36 remains a distinct Background authority callback in SharedWorldGameplay::Sources. It is not silently assigned initial-bootstrap suppliers or considered complete. Initial1C/Entered remains unchanged and open: common presence currently becomes active before the actual entered continuation. Visibility/initial scene/gameplay publication and real supplier/Application configuration need their own source contracts. Full native actor/default/profile/rules/issuers, normal/CF recovery, durable replay/crash and all other gameplay/numeric routes remain incomplete.

Increment: strengthen four existing pre-ready request publication bindings (1F/23/30/36), add one typed actual-source result boundary. No new owner chain, phase binding, opcode value, native field/rule/response causality or complete bidirectional route. Whole-game total/completed/percentage unknown. No tests or native acceptance run.
'''

def sha(data):return hashlib.sha256(data).hexdigest()

def main():
    base=ROOT/'artifacts/integration/packet-connections-20261006';out=base/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():raise RuntimeError('Fresh before receipt required')
    def save(rel,data):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as f:f.write(data)
    def dump(rel,value):save(rel,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    unchanged=[]
    for row in json.loads((out/'before-manifest.json').read_text(encoding='utf-8')):
        data=(out/'before'/row['path']).read_bytes()
        if sha(data)!=row['sha256']:raise RuntimeError('Before snapshot differs')
        if row['path'] not in SOURCES and row['path'] not in (
            'artifacts/integration/packet-connections-20261006/packet-route-ledger.json','docs/PACKET_CONNECTION_GOAL_20261006.md'):
            if data!=(ROOT/row['path']).read_bytes():raise RuntimeError('Preserved source changed')
            unchanged.append(row)
    prior=base/'cn-world-ready-owner-01';raw=(prior/'integration-manifest.json').read_bytes();manifest=json.loads(raw)
    if manifest['client_sha256']!=PIN:raise RuntimeError('Historical CN pin differs')
    save('retained-source/cn-world-ready-owner-01/integration-manifest.json',raw)
    retained=[]
    for row in manifest['snapshots']:
        if not row['path'].endswith(('SharedWorldReady.h','SharedWorldReady.cpp','worker-control-contract.json')):continue
        p=(prior/row['path']).resolve()
        if not p.is_relative_to(prior.resolve()):raise RuntimeError('Historical path outside artifact')
        data=p.read_bytes()
        if sha(data)!=row['sha256']:raise RuntimeError('Historical scoped source differs')
        save('retained-source/cn-world-ready-owner-01/'+row['path'],data);retained.append(row)
    prior=base/'cn-selected-world-publication-01';sealed=json.loads((prior/'manifest.json').read_text(encoding='utf-8'))
    pins={r['path']:r['sha256'] for r in sealed['files']};data=(prior/'findings.json').read_bytes()
    if not sealed['sealed'] or sha(data)!=pins['findings.json']:raise RuntimeError('Previous sealed source differs')
    save('retained-source/cn-selected-world-publication-01/findings.json',data)
    dump('source-relations.json',{'requests':['1F00','2300','30:00','36:opaque8'],
        'source':'complete retained C2S ->actual issuer full replies or explicit no-output plus mandatory observing current predicate',
        'publication':'same pending stage/lease/account/world session/world ticket ->BeforePublish ->actual native held IO ->QueueAccepted ->next stage ->IO release ->single completion ->remaining aggregate',
        'background':'initial30/36 keeps the same step; ready-world ongoing controls retain their independent source contract',
        'not_recovered':'native reply opcodes/fields/pairing/rules/permissions/no-output semantics and configured providers',
        'retained_historical_scoped_sources':retained,'all_original_native_evidence_reread':False})
    findings={'round':ROUND,'native_sha256':PIN,'previous_goal_turn_classification':'progress: selected1F/02/2A actual preparation publication and catalog96 sealed',
        'existing_bootstrap_request_publication_bindings_strengthened':4,'bootstrap_result_source_boundaries_added':1,
        'ongoing_background_contracts_preserved':1,'completed_batch_failure_guards_added':1,
        'underlying_world_transport_publication_reused_not_recounted':True,'new_source_owner_chains':0,
        'new_native_phase_source_bindings':0,'new_packet_values':0,'new_complete_bidirectional_routes':0,
        'whole_game_route_total':None,'whole_game_completion_percent':None,'levels_changed':False,
        'native_response_causality_recovered':False,'configured_native_bootstrap_providers_installed':False,
        'formal_application_hosted':False,'build_run':False,'tests_run':False,'runtime_run':False,
        'database_access':False,'deployed':False,'existing_sources_unchanged':unchanged,'remaining':REMAINING}
    dump('findings.json',findings)
    with (ROOT/SOURCES[-1]).open('x',encoding='utf-8') as f:f.write(DOCUMENT)
    for rel in SOURCES:save('source/'+rel,(ROOT/rel).read_bytes())
    ledger_path=base/'packet-route-ledger.json';ledger=json.loads(ledger_path.read_text(encoding='utf-8'))
    ledger['cn_bootstrap_source_publication']={k:v for k,v in findings.items() if k not in ('existing_sources_unchanged',)}
    ledger['cn_bootstrap_source_publication']['evidence']=out.relative_to(ROOT).as_posix()
    ledger['dual_client_source_segments'].append({'name':'CN initial bootstrap full actual-source output and next-state publication before IO',
        'version_scope':'cn-pre-ready-bootstrap-1F-23-30-36','status':'actual issuer full output/explicit no-output plus stage predicate ->same lease/world admission ->held IO ->publish next stage ->release ->single completion; actual suppliers/hosting/entered/recovery open',
        'source_paths':list(SOURCES),'native_c2s_by_phase':{},'native_s2c_by_phase':{},'source_owner_chains_added':0,
        'formal_application_hosted':False,'complete_gameplay_routes_added':0,
        'existing_bootstrap_request_publication_bindings_strengthened':4,'bootstrap_result_source_boundaries_added':1,
        'evidence':out.relative_to(ROOT).as_posix(),'remaining':REMAINING})
    ledger['dual_client_execution_plan']['latest_work_round']=ROUND
    ledger['dual_client_execution_plan']['next_source_frontier']='Continue initial1C entered/visibility/gameplay publication with the same actual common preparation/incarnation and normal/CF scene source. Initial1F/23/interleaved30/36 now publishes its stage before actual-source replies leave the verified world IO barrier. Actual native bootstrap data/control/issuer/rules/no-output causality and configured providers/hosting remain missing; durable operation/replay/crash, all gameplay/numeric and full directional state/variant/indirect/deferred denominator remain open. Levels unchanged; PHASE1 file-only.'
    ledger_path.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    plan=ROOT/'docs/PACKET_CONNECTION_GOAL_20261006.md'
    with plan.open('a',encoding='utf-8') as f:f.write('\n\n## CN bootstrap actual-source publication ('+ROUND+')\n\n'
        'Existing pre-ready1F/23/30/36 now requires a full actual issuer result and observing BeforePublish/QueueAccepted predicate. Full outputs reuse verified WORLD held IO; next ready stage is published before release. No-output is an explicit source choice requiring the same authority, never a default acknowledgement. Ongoing ready-world controls remain independent. Existing four publication bindings strengthened, one typed result boundary; new owner/phase/opcode/full route0. Actual native suppliers/response causality, initial1C entered/visibility/gameplay publication, Application hosting/recovery and whole-game routes remain open. Levels unchanged; PHASE1 no build/tests/runtime/SQL/deployment. See research/cn-bootstrap-source-publication-20261007.md.\n')
    print(json.dumps({k:findings[k] for k in ('round','existing_bootstrap_request_publication_bindings_strengthened','bootstrap_result_source_boundaries_added','new_complete_bidirectional_routes')}))

if __name__=='__main__':main()
