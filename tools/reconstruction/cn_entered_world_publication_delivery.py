"""File-only CN initial1C actual scene result ->presence/gameplay/IO publication."""
import hashlib
import json
from .cn_wrapper_route_frontier import ROOT,PIN

NAME='cn-entered-world-publication-01'
ROUND='20261007-cn-entered-world-publication'
SOURCES=('src/cn/world/SharedWorldReady.h','src/cn/world/SharedWorldReady.cpp',
    'src/cn/world/SharedWorldGameplay.h','src/cn/world/SharedWorldGameplay.cpp',
    'tools/reconstruction/dual_client_route_catalog.py','tools/reconstruction/cn_entered_world_publication_delivery.py',
    'docs/research/cn-entered-world-publication-20261007.md')
REMAINING=[
    'Actual full native initial1C scene/visibility/data/issuer/rule and no-output causality providers remain missing; this result contract does not fabricate initial replies or authorize client handle/language.',
    'Initial visibility full native actor bindings/fanout/publication/recovery, ongoing controls, actual scene/directory/chat/movement authorities and normal/CF lifecycle require their own source connections.',
    'Configured Application providers/hosting and durable operation/semantic replay/committed-state/publication/crash/cross-process recovery remain open.',
    'All TW/CN/web gameplay and numeric wire/object/display and exhaustive directional phase/state/variant/indirect/deferred denominator, followed by comprehensive original-client acceptance. Levels unchanged.']
DOCUMENT='''# CN initial1C: actual scene result, common readiness and gameplay publication

PHASE1 source integration/accounting only: no build/tests/native/API/codec/resource/server/SQL execution, migration or deployment. The preceding bootstrap source publication turn is progress: four existing request bindings and a result boundary were changed and catalog97 sealed. Levels, original wire/EXEs, accounts/saves and frozen fonts/chat/IME/auth/portraits/conversion unchanged.

Previously ready parsed1C and immediately activated common presence, before asking Entered for a bool. The first later gameplay request installed the actual movement/directory/chat controllers. That let prepared presence appear ready before the real entered source had supplied/qualified its result and did not place the controller handoff before native output.

Entered now receives the exact complete original five-byte1C plus the same generation-qualified common Lease. Claimed handle must equal this reserved handle and the initial language value must retain the existing native zero qualification. These client fields cannot identify a DB character, allocate an actor, select protocol or grant permission. The lease remains inactive while the actual scene source prepares its result. EnteredResult reuses the existing typed BootstrapResult: mandatory BeforePublish/QueueAccepted observing issuer predicate, complete source-native output or an explicit actual-source no-output decision. No new result boundary/packet value/rule/reply pairing is invented or recounted. A real provider must bind full input/resources/rules/normal-or-CF lifecycle and cannot activate presence, send these replies, write saves, yield or pump events itself.

The shared publication path retains the exact pending batch, connection/account/world session/world admission, original stage and current preparation ownership/position. Both sides of BeforePublish and QueueAccepted recheck it; entering additionally requires the same still-inactive actor handle. Full output uses the unchanged verified WORLD held native IO barrier. Only after the actual entered predicate passes does publication activate that exact common lease and invoke a mandatory Install hook. SharedWorldGameplay supplies the concrete hook: its existing initialize composes actual movement, directory, chat and mode0 generic/special controllers. Normal preparation's existing exact SharedNativeMovementScene::adopt runs here, retaining its same initial resources/scene/presence/position/generation. The source factory must not yield, pump events, send output or write saves. CF must retain its actual supplied movement source, never receive normal initial geometry.

After installation the publisher rereads same connection/stage/presence/admission and only then sets InWorld/published before IO releases the full native output. InWorld current requires active same-lease presence. Later gameplay receive requires already installed controllers and does not use a later C2S to repair/replace the initial handoff. Explicit no-output uses the same serial publication and emits no fabricated ACK. Queue completion resumes the complete aggregate remainder under the actual gameplay dispatcher, not an old entered/preparation source predicate.

Failed activation, thrown/failed controller installation or changed identity releases visibility/common presence and closes this original incarnation on the same game turn before another owner can observe failed ready presence. Visibility cleanup exceptions do not suppress presence cleanup. Already adopted scene state is not falsely rolled back/reused; this incarnation closes and existing native ReleaseOnce handles actual supplier lifetime. Held native bytes are refused; there is no saved-data rollback or peer/client receipt claim. A private outstanding ready batch also prevents a second ingress racing an asynchronous issuer/publication; source completion remains single-use and a finished batch cannot tear down a successor. Once gameplay owns the remainder its own existing serialization applies.

SharedActorVisibility itself remains unchanged: actual show/send/model bindings, full native6F/5E/73/rules/resources/recipient policy and asynchronous fanout/publication recovery are still open. This turn does not create default actor data, make raw output imply qualified visibility, claim atomic cross-peer delivery, or configure any Application native provider. Bootstrap1F/23/30/36 reuses its existing publisher; ready-world ongoing controls stay independently qualified. Full native rules/data/issuer, durable replay/crash recovery and all TW/CN/web gameplay/numeric routes remain incomplete.

The peer native-world-driver three original files and one controlled-raster reference are saved with exact SHA. All118 raw range lengths/hashes were read; CN59 matched the current pinned PE, TW59 remain historical and the specified old mapped original is still absent. Peer confirmed the prior controlled-raster ACK; driver SHA ACK was sent and its read remains pending. Peer16 frontend regressions/56 GPU frames/66 ticks/56 iterations/55 presentations and browser/time/FP fixtures are peer records, not server/native/full four-route WSS acceptance. renderReady=false/new complete gameplay0. Capacity40419839431 bytes is the peer's2026-10-07T10:02:25.166803+00:00 point-in-time measurement; this server did not remeasure.

Increment: strengthen existing initial1C publication1 and actual gameplay entry installation1; ready batch lifetime guard1 and same-turn failed activation cleanup1. Reuse previous source-result/IO contracts without recounting. New owner chain/phase binding/opcode/complete bidirectional route0; whole-game total/completed/percentage unknown. Next: actual initial visibility bindings/publication and full native suppliers/hosting/durable recovery.
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
    before_ledger=json.loads((out/'before/artifacts/integration/packet-connections-20261006/packet-route-ledger.json').read_text(encoding='utf-8'))
    for row in json.loads((out/'before-manifest.json').read_text(encoding='utf-8')):
        data=(out/'before'/row['path']).read_bytes()
        if sha(data)!=row['sha256']:raise RuntimeError('Before snapshot differs')
        if row['path'] not in SOURCES and row['path'] not in (
            'artifacts/integration/packet-connections-20261006/packet-route-ledger.json','docs/PACKET_CONNECTION_GOAL_20261006.md'):
            if data!=(ROOT/row['path']).read_bytes():raise RuntimeError('Preserved source changed')
            unchanged.append(row)
    prior=base/'cn-world-ready-owner-01';raw=(prior/'integration-manifest.json').read_bytes()
    pins=before_ledger['cn_account_admission_evidence']['cn-world-ready-owner-01']['artifact_sha256']
    if sha(raw)!=pins['integration-manifest.json']:raise RuntimeError('Historical ready receipt changed')
    manifest=json.loads(raw)
    if manifest['client_sha256']!=PIN:raise RuntimeError('Historical CN pin differs')
    save('retained-source/cn-world-ready-owner-01/integration-manifest.json',raw);retained=[]
    for row in manifest['snapshots']:
        if not row['path'].endswith(('SharedWorldReady.h','SharedWorldReady.cpp','worker-control-contract.json','CnWorldEntry.h')):continue
        p=(prior/row['path']).resolve()
        if not p.is_relative_to(prior.resolve()):raise RuntimeError('Historical path outside artifact')
        data=p.read_bytes()
        if sha(data)!=row['sha256'] or sha(data)!=pins[row['path']]:raise RuntimeError('Historical scoped source differs')
        save('retained-source/cn-world-ready-owner-01/'+row['path'],data);retained.append(row)
    prior=base/'cn-bootstrap-source-publication-01';raw=(prior/'manifest.json').read_bytes();sealed=json.loads(raw)
    pins={r['path']:r['sha256'] for r in sealed['files']};data=(prior/'findings.json').read_bytes()
    if not sealed['sealed'] or sha(data)!=pins['findings.json']:raise RuntimeError('Previous sealed source differs')
    save('retained-source/cn-bootstrap-source-publication-01/manifest.json',raw)
    save('retained-source/cn-bootstrap-source-publication-01/findings.json',data)
    peer=json.loads((out/'peer-handoff/server-file-source-receipt.json').read_text(encoding='utf-8'))
    dump('source-relations.json',{'input':'exact full initial1C/handle/zero language with inactive same common Lease ->actual scene issuer result',
        'publication':'pending batch/stage/connection/account/world session/admission/preparation ->actual source BeforePublish/QueueAccepted ->activate same Lease ->concrete retained gameplay initialize/normal movement adopt or actual CF ->recheck ->InWorld ->held output release',
        'failure':'same-turn exact visibility/presence cleanup/close; no save rollback, scene reuse or peer delivery claim',
        'visibility':'actual initial native model bindings/fanout/rules/current publication remain open; visibility source unchanged',
        'retained_historical_scoped_sources':retained,'all_original_native_evidence_reread':False,'peer_handoff':peer})
    findings={'round':ROUND,'native_sha256':PIN,'previous_goal_turn_classification':'progress: initial1F/23/30/36 actual-source result and IO-stage publication, catalog97 sealed',
        'existing_initial1C_publication_bindings_strengthened':1,'existing_gameplay_entry_install_bindings_strengthened':1,
        'ready_aggregate_lifetime_guards_added':1,'same_turn_failed_activation_cleanup_bindings_added':1,
        'source_result_boundary_reused_not_recounted':True,'underlying_world_transport_publication_reused_not_recounted':True,
        'new_source_owner_chains':0,'new_native_phase_source_bindings':0,'new_packet_values':0,
        'new_complete_bidirectional_routes':0,'whole_game_route_total':None,'whole_game_completion_percent':None,
        'levels_changed':False,'native_response_causality_recovered':False,'configured_native_entered_providers_installed':False,
        'formal_application_hosted':False,'build_run':False,'tests_run':False,'runtime_run':False,'database_access':False,
        'deployed':False,'existing_sources_unchanged':unchanged,'remaining':REMAINING}
    dump('findings.json',findings)
    with (ROOT/SOURCES[-1]).open('x',encoding='utf-8') as f:f.write(DOCUMENT)
    for rel in SOURCES:save('source/'+rel,(ROOT/rel).read_bytes())
    ledger_path=base/'packet-route-ledger.json';ledger=json.loads(ledger_path.read_text(encoding='utf-8'))
    ledger['cn_entered_world_publication']={k:v for k,v in findings.items() if k!='existing_sources_unchanged'}
    ledger['cn_entered_world_publication']['evidence']=out.relative_to(ROOT).as_posix()
    ledger['dual_client_source_segments'].append({'name':'CN initial1C actual source ->same common activation/gameplay installation before native IO release',
        'version_scope':'cn-normal-transfer-initial-ready-entered-publication','status':'full1C inactive same Lease ->actual scene result ->held world IO ->activate exact presence ->install existing gameplay/normal scene or actual CF ->InWorld ->release ->single completion; actual issuer/visibility/providers/hosting/recovery open',
        'source_paths':list(SOURCES),'native_c2s_by_phase':{},'native_s2c_by_phase':{},'source_owner_chains_added':0,
        'formal_application_hosted':False,'complete_gameplay_routes_added':0,
        'existing_initial1C_publication_bindings_strengthened':1,'existing_gameplay_entry_install_bindings_strengthened':1,
        'evidence':out.relative_to(ROOT).as_posix(),'remaining':REMAINING})
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next_source_frontier']='Continue actual initial visibility native actor bindings/fanout/current publication and ongoing controls, full native scene/default/profile/issuer/rules/reservation/providers and configured Application hosting. Initial1C now retains inactive common presence through actual scene result qualification and installs existing gameplay owners before held reply release. Durable operation/replay/crash recovery, all gameplay/numeric and full directional phase/state/variant/indirect/deferred denominator remain open. Levels unchanged; PHASE1 file-only.'
    plan['latest_coordination_round']=peer['round'];plan['latest_peer_handoff_round']=peer['round']
    ledger['web_native_world_driver_handoff']=peer
    if 'web_native_controlled_raster_handoff' in ledger:
        ledger['web_native_controlled_raster_handoff']['new_ACK_read_confirmed']=True
        ledger['web_native_controlled_raster_handoff']['ACK_read_confirmation_round']=peer['round']
    ledger_path.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (ROOT/'docs/PACKET_CONNECTION_GOAL_20261006.md').open('a',encoding='utf-8') as f:f.write(
        '\n\n## CN initial1C actual presence/gameplay publication ('+ROUND+')\n\n'
        'Exact full1C now reaches actual scene issuer with inactive same common Lease; required source result/BeforePublish/QueueAccepted precedes activation. Existing held world IO publishes exact presence, existing gameplay/normal movement scene installation and InWorld before release; failures clear original active presence on the same game turn. Later gameplay requires installed controllers. Existing1C publication strengthened1/gameplay entry installation1, lifetime guard1/failed activation cleanup1; source-result/transport contracts reused, new owner/phase/opcode/full route0. Full initial visibility/rules/native data/issuers/providers/hosting/durable recovery and all gameplay/denominator remain open. Peer driver originals SHA ACK with CN59 current/TW59 historical ranges; controlled-raster ACK read confirmed, new driver ACK read pending. Peer16 frontend/56 GPU fixtures not server/native acceptance; renderReady=false. Levels unchanged, PHASE1 no execution/tests/deploy. See research/cn-entered-world-publication-20261007.md.\n')
    print(json.dumps({k:findings[k] for k in ('round','existing_initial1C_publication_bindings_strengthened','existing_gameplay_entry_install_bindings_strengthened','new_complete_bidirectional_routes')}))

if __name__=='__main__':main()
