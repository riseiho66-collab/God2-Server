"""File-only receipt for native A6/07 queue/publication source integration.

No compilation, tests, native/runtime or gameplay DB execution.
"""
import hashlib
import json
import pefile
from .cn_wrapper_route_frontier import ROOT, CN, PIN
from .cn_pe_import_directory import FileView

NAME='cn-account-selection-queue-commit-01'
ROUND='20261007-cn-account-selection-queue-commit'
CHANGED=('src/auth/SharedWorldAdmission.h','src/auth/SharedWorldAdmission.cpp',
    'src/cn/auth/SharedAccountSelection.h','src/cn/auth/SharedAccountSelection.cpp',
    'src/cn/net/SharedCredentialConnection.h','src/cn/net/SharedCredentialConnection.cpp',
    'src/cn/net/CnTransportSession.h','src/cn/net/CnTransportSession.cpp',
    'tools/reconstruction/dual_client_route_catalog.py')
SOURCES=CHANGED+('tools/reconstruction/cn_account_selection_queue_commit_delivery.py',
    'docs/research/cn-account-selection-queue-commit-20261007.md')


def sha(raw):return hashlib.sha256(raw).hexdigest()


def main():
    base=ROOT/'artifacts/integration/packet-connections-20261006';out=base/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():
        raise RuntimeError('Require fresh before receipt; preserve historical artifacts')
    unchanged=[]
    for row in json.loads((out/'before-manifest.json').read_text(encoding='utf-8')):
        raw=(out/'before'/row['path']).read_bytes()
        if sha(raw)!=row['sha256']:raise RuntimeError('Before receipt changed')
        if row['path'] not in CHANGED:
            if raw!=(ROOT/row['path']).read_bytes():raise RuntimeError('Frozen/context source changed')
            unchanged.append(row)
    retained=[]
    for name,paths in (
        ('cn-account-summary-common-snapshot-01',('findings.json','source-relations.json')),
        ('cn-create-post-choice-reconnect-01',('findings.json','source-relations.json',
            'native/index.json','native/00449310.bin','native/00449310.asm','native/00449310.c','native/00449310.cfg.json'))):
        prior=base/name;manifest=json.loads((prior/'manifest.json').read_text(encoding='utf-8'))
        pins={r['path']:r['sha256'] for r in manifest['files']}
        if not manifest['sealed']:raise RuntimeError('Prior receipt not sealed')
        for rel in paths:
            raw=(prior/rel).read_bytes()
            if sha(raw)!=pins[rel]:raise RuntimeError('Retained source receipt changed')
            p=out/'retained-source'/name/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
            retained.append({'artifact':name,'path':rel,'bytes':len(raw),'sha256':sha(raw)})
    findings={'round':ROUND,'native_sha256':PIN,
        'previous_goal_turn_classification':'progress: scoped18 producer/selector research and raw choice field correction sealed in catalog86',
        'existing_account_selection_bindings_strengthened':1,
        'common_selection_queue_publication_sources_added':1,
        'transport_queue_write_barrier_sources_added':1,
        'account_terminal_reply_drain_sources_added':1,
        'native_fields_newly_recovered':0,'new_packet_values':0,
        'new_source_owner_chains':0,'new_native_phase_source_bindings':0,
        'new_complete_bidirectional_routes':0,'whole_game_route_total':None,
        'whole_game_completion_percent':None,'levels_changed':False,
        'build_run':False,'tests_run':False,'runtime_run':False,'database_access':False,'deployed':False,
        'existing_sources_unchanged':unchanged,
        'remaining':['Actual full native07 issuer/visibility/opaque bytes and ordered common-ID mapping.',
            'Complete native auth success/directory/world00-1F providers and actual Application hosting.',
            'Cross-process atomicity, durable crash/replay recovery and disconnect after legitimate world claim.',
            'All gameplay, extended numeric wire/object/display work and full state/variant/indirect denominator.']}
    relations={'route':'A6 aggregate -> all targets/native07/common roots qualified -> queued exact final offer, no world reserve -> actual encoded bounded output queue held at first frame -> game full common/native recheck -> exact revision commit -> IO release -> account ingress resume or terminal0A drain/close',
        'native_baseline':'Retained pinned ordinary449363->481640 A6/full07 call; no new native emission policy or packet shape recovered.',
        'queued_identity':['actual registry pointer','Grant key/generation','account session','offer revision','SelectionQueued stage','deadline','no character invalidation'],
        'aggregate':'Every target must be allowed by the same account grant and catalog. Every complete07 is qualified before queueing and again at QueueAccepted. Final request supersedes offer as before; preceding replies retain exact order.',
        'write_barrier':'strand-owned first frame; write_next stops there; prior writes may finish; subsequent ordinary sends append behind it. Encoding/frame/byte budget preparation happens before Game publication; original codec stays native.',
        'publication':'Mandatory observing Current at QueueAccepted with full common account snapshot reads before/after; serial exact token commit, no callbacks/yield/allocation inside commit. Failed native source/current/root check closes without writing held07.',
        'failure':'Cancel exact queued or still-unclaimed Selected revision, including already-detached Selected; never another generation/revision or Reserved/WorldOwned. Queue-stage detach removes unpublished offer. Failure does not fabricate SQL rollback or revoke a legitimately claimed world.',
        'terminal0A':'Exact authenticated account echo; terminal existing grammar. With preceding A6, accepted07 is drained locally before account close. Alone, close directly. No0A reply is generated.',
        'completion':'07 queue-release outcome; terminal aggregate additionally reports local TCP drain. Neither peer receipt, native client acceptance nor playable gameplay.',
        'source_policy_not_official_rules':True,'ordinary_send_batch_body_intentionally_unchanged':True,
        'native_level_changed':False,'native_record_rewritten':False,'schema_changed':False,
        'native_issuer_added':False,'production_hosted':False}
    doc=ROOT/SOURCES[-1]
    with doc.open('x',encoding='utf-8') as f:
        f.write('# CN A6/07 queue acceptance and publication\n\n'
            'PHASE1 source work only: no build, tests, gameplay/native execution, DB access, migration or deployment. Levels, curves, native level fields and display stay unchanged.\n\n'
            'The existing account-selection controller selected a usable world grant then sent each07 without a queue callback; it completed account ingress before encoding/capacity could fail. The ordinary transport callback also started writes before notifying Game. This round connects actual native07 queue preparation to shared grant publication and holds those bytes until current source qualification and grant commit finish on the serial game owner. This is our integration/lifetime policy, not recovered official issuance or TTL. The sealed native ordinary449363->481640 A6/full07 source and prior full common-account snapshot evidence are retained.\n\n'
            'SharedWorldAdmission now supplies a registry-bound QueuedSelection carrying exact generation, account session and offer revision. SelectionQueued cannot be reserved as a world grant. Every aggregate target is checked against the same grant allowed list as well as the native catalog; the entire aggregate is prepared before any native bytes are queued. Complete immutable07 sources and full common account roots remain retained. Ordered A6 requests supersede one grant, so its final target/ordered common IDs/raw07 become the pending offer, while every exact07 remains in the outgoing batch in order.\n\n'
            'CnTransportSession::send_batch_with_publication prepares original codec frames and the existing frame/byte budgets on its IO strand. The first new frame becomes a write barrier: prior accepted writes may finish, but write_next stops at that frame and later normal sends cannot overtake it. After actual queue preparation, the Game callback checks the live verified account, exact pending token and each full native source at QueueAccepted, reading the whole common account root set before and after its observing authority callback. It commits that exact queued revision without yielding, then IO releases the barrier and reports the queue outcome. Fast world ingress therefore sees the published grant before newly sent07 can reach the client. The original ordinary send_batch body and native codec remain unchanged.\n\n'
            'False/throw, stale roots/native source, changed revision, close or queue capacity failure reports failure and closes. The controller cancels only this queued or still-unclaimed Selected revision; cancellation also recognizes a Selected attempt detached by close before its Game completion. It never cancels a different attempt or Reserved/WorldOwned actor. Account cleanup removes unpublished queued offers. A world may legitimately progress after publication and before account completion; the late completion must not demand an obsolete queued stage or undo its claimed handoff. This is not a cross-process/crash atomic transaction or proof of peer receipt.\n\n'
            'Native terminal0A still requires the exact authenticated name and adds no reply. Alone it closes. Following qualified A6, it waits for07 publication and drains the real queued replies before account cleanup. Completion reports local TCP writes only; the selected/claimed world handoff retains its existing lifetime. Failed draining does not invent a compensating storage mutation. No account/storage schema, native success/seed/billing provider, full07 opaque fields, common40-to-native36 conversion or gameplay handler is fabricated.\n\n'
            'Increment: existing A6/07 binding strengthened1; common queued publication source1; transport write barrier1; account terminal drain1. New opcode/native field/phase/owner/full routes0; whole-game total and percentage null. Actual native suppliers/Application hosting, durable recovery, numeric extension and all gameplay remain open. Do not interpret this unbuilt source change as native acceptance.\n')
    for name,value in (('findings.json',findings),('source-relations.json',relations),('retained-evidence.json',retained)):
        with (out/name).open('x',encoding='utf-8') as f:f.write(json.dumps(value,indent=2)+'\n')
    # Existing human authorization for this web peer; retain its originals.
    # Read file bytes only, never run its tests/preview/native program.
    peer=ROOT.parent/'God2/output/web-prototype';handoff=out/'peer-handoff';handoff.mkdir()
    expected={
        'reports/client-goal-20261007/native-world-tile-queue-source.json':'b65426d8888422914e4af1276433bb54a49854fd9652fc23274780a3359ca414',
        'reports/client-goal-20261007/native-world-tile-queue-verification.json':'a35d450a291cb2ac3a6dc399d85304266978d0a4fb8e665e90a1462eb8d277fd',
        'WEB_SERVER_INTEGRATION.md':'b82ac3a82a3cbe5fa6b87d77a772e7e21ca3b3811cf1f4f6aabf3d462ab8a156'}
    files=[];values={}
    for rel,pin in expected.items():
        raw=(peer/rel).read_bytes()
        if sha(raw)!=pin:raise RuntimeError('Peer handoff file changed')
        dest=handoff/(peer/rel).name;dest.write_bytes(raw)
        files.append({'original':str(peer/rel),'path':dest.relative_to(out).as_posix(),'bytes':len(raw),'sha256':pin})
        if rel.endswith('.json'):values[dest.name]=json.loads(raw)
    source=values['native-world-tile-queue-source.json'];receipt=values['native-world-tile-queue-verification.json']
    raw=(CN.parent/'XJZ-CN/God2_opt.exe').read_bytes()
    if sha(raw)!=PIN:raise RuntimeError('Current CN primary changed')
    pe=pefile.PE(data=raw,fast_load=True);view=FileView(pe,raw);ib=pe.OPTIONAL_HEADER.ImageBase
    ranges=[]
    for version,blocks in source['blocks'].items():
        for name,row in blocks.items():
            data=bytes.fromhex(row['bytes'])
            if len(data)!=row['length'] or sha(data)!=row['sha256']:raise RuntimeError('Peer range receipt changed')
            current=version=='cn'
            if current and view.read(int(row['va'],16)-ib,len(data))!=data:
                raise RuntimeError('Current CN primary source mismatch')
            ranges.append({'version':version,'name':name,'va':row['va'],'bytes':len(data),
                'sha256':sha(data),'current_primary_file_compared':current,
                'scope':'CN current pinned primary file bytes' if current else
                    'TW historical peer-provided source range; mapped original absent, not independently reread'})
    peer_record={'round':receipt['round'],'files':files,'records':ranges,
        'source_ranges':len(ranges),'cn_current_primary_ranges_compared':sum(r['current_primary_file_compared'] for r in ranges),
        'tw_historical_mapped_original_recovered':False,'prior_initial_context_ack_read_confirmed_by_peer_message':True,
        'accepted_source_contract':'signedWORD persistent tile queue; equal depth does not reorder; ties append after equals; hide/show/image/XY preserve order; fresh mount/aux/body allocation and later action-reset ordering remain separate',
        'initial_camera_scope':'first whole-map ground minus400/300 +source viewerOffset at native800x600 1:1; preview zoom cannot select connected camera; actual moving cache/rebase owner not qualified',
        'renderReady':receipt['renderReady'],'peer_capacity_point_in_time':receipt['capacity'],
        'server_capacity_remeasured':False,'peer_tests_are_server_acceptance':False,
        'server_tests_run':False,'native_or_emulator_run_by_server':False,'new_complete_routes':0,
        'remaining':receipt['limits']}
    with (handoff/'server-file-source-receipt.json').open('x',encoding='utf-8') as f:
        f.write(json.dumps(peer_record,indent=2)+'\n')
    for rel in SOURCES:
        p=out/'source'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/rel).read_bytes())
    print(json.dumps({k:findings[k] for k in ('round','existing_account_selection_bindings_strengthened','common_selection_queue_publication_sources_added','new_complete_bidirectional_routes')}))


if __name__=='__main__':main()
