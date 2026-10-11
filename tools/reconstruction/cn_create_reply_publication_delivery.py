"""File-only receipt: actual CN ordinary02/18 source publication before IO release."""
import hashlib
import json
from .cn_wrapper_route_frontier import ROOT,PIN

NAME='cn-create-reply-publication-01'
ROUND='20261007-cn-create-reply-publication'
SOURCES=('src/cn/net/SharedCredentialConnection.h','src/cn/net/SharedCredentialConnection.cpp',
    'src/cn/auth/SharedCharacterCreateOperation.h','src/cn/auth/SharedCharacterCreateOperation.cpp',
    'tools/reconstruction/cn_create_reply_publication_delivery.py','tools/reconstruction/dual_client_route_catalog.py',
    'docs/research/cn-create-reply-publication-20261007.md')
REMAINING=[
    'Actual native ordinary17/18 default/profile/non-root resources/roles/fees/rules/choice/replay/02/18 issuers and configured providers/hosting remain open.',
    'Durable create/choice/semantic replay receipts, cross-process policy and real committed-save/publication/crash recovery remain open.',
    'Other selected-world/bootstrap/terminal/source publication chains require their own actual owner/current-data checks; this ordinary creation chain does not close all world publication.',
    'All TW/CN/web gameplay and numeric wire/object/display, full phase/state/variant/indirect/deferred denominator and later comprehensive native acceptance remain open. Levels unchanged.']
DOCUMENT='''# CN ordinary02/18 replies: qualification and operation publication before IO

PHASE1 static source accounting only. No build, tests, codec/native/API/DLL/server/SQL execution, migration or deployment. Prior creation-name integration was progress. Native levels, profiles, wire formats, packet values, existing SQL saves and frozen functionality remain unchanged.

The existing actual CnTransportSession::send_batch_with_publication is reused, with unchanged source bytes. It reserves the bounded frame count, encodes the entire native batch and checks queue/byte capacity on the IO strand, holds its first native frame behind publication_barrier_, then asks the serial game owner to publish. write_next stops at that held head and later ordinary output cannot overtake it. False/throw closes without writing the held batch; true releases on the strand before its local queue callback. Existing earlier writes may finish. This is an application publication order, not peer TCP receipt/native acceptance or an assertion that game state cannot ever change after publication.

Added SharedCredentialConnection::send_world_batch_with_publication. It requires the actual verified account, world-session identity, admitted WORLD role and exact current registry-owned world ticket before scheduling and around the observing game publication callback. It sends through the existing same transport/codec/barrier. No credential bypass, arbitrary endpoint, raw guessed packet or default-current predicate. Existing account publication and ordinary send_batch bodies remain unchanged.

SharedCharacterCreateOperation previously sent02/18 with ordinary send_batch, then consulted actual rules/roots and promoted phase in its queue callback. Native bytes could already leave before that check. Both ordinary create02 and chosen18 now call the new real world publication entry. Scope/request/result pointer and mandatory rules/common state are retained through the IO scheduling gap. ReplyCheck explicitly distinguishes BeforePublish from QueueAccepted; the concrete native create/choice plans receive their corresponding new QueueAccepted checks. Direct real transaction result suppliers must also supply these observing stages; no compatibility/default-true callback is generated. These are unhosted source API changes, and no configured direct/native plan provider exists yet.

At02 publication, the exact pending CreateResult, CreateReplyQueued phase, actual selection/session and full newly created row (when success) are checked before and after the mandatory result lease. Then the exact next stage is published: AwaitingChoice on actual success; RetryAvailable only for existing source status49; Failed for other actual complete failures. The state transition and local publication marker precede IO release, without allocating or calling a rule after the transition within this operation callback. Existing complete23-byte02 record/status/opaque bytes remain supplied by the real issuer; nonzero failure still does not perform a common CAS mutation.

At18 publication, the exact pending ChoiceResult, ChoiceReplyQueued phase, current selection and owner-bound common character are rechecked around its actual committed-choice rule/operation lease. The concrete CAS source also rereads the exact committed position and native reply low3 slot association. A choice legitimately changing the common profile is not compared against its old pre-choice snapshot. Completed is published before IO release; the existing native terminal03/world close/account0A/fresh-login path can then observe that phase. No fabricated creation success/native slot/default destination or fresh entry through the old grant.

Local queue callbacks consult the exact published result/marker and same live verified account/world-session identity. They neither repeat an obsolete pre-choice/pre-publication root/rule predicate nor pretend to roll back a valid saved COMMIT. Single held ingress completion is returned once; capacity/close/qualification failure still closes through the actual existing transport cleanup. A published stage followed by connection close is not a durable client receipt. Persisted create/choice changes survive output failure; durable operation/publication recovery remains an explicit missing owner.

SharedWorldSelection, real common create/position writers, prior immutable name projections and underlying transport implementation remain unchanged. Historical create/ordinary reconnect/account-barrier/name records are retained with seals/hashes; no native fields, opcodes or whole-game denominator are newly proved. This round adds world publication source1 and strengthens existing02/18 publication bindings2 plus stage-qualified rule handoff1; new owner chains/phase bindings/packet values/complete bidirectional routes0. Actual native defaults, rule/data/issuer providers, configured Application hosting, other world/bootstrap/terminal publication, all gameplay/numeric sources, durable operation/recovery and phase/state/variant/indirect/deferred denominator remain required. Full completion and percentages remain unknown.
'''

def sha(raw):return hashlib.sha256(raw).hexdigest()

def main():
    base=ROOT/'artifacts/integration/packet-connections-20261006';out=base/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():raise RuntimeError('Fresh before receipt required')
    def save(rel,raw):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as f:f.write(raw)
    def dump(rel,value):save(rel,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    unchanged=[]
    for row in json.loads((out/'before-manifest.json').read_text(encoding='utf-8')):
        raw=(out/'before'/row['path']).read_bytes()
        if sha(raw)!=row['sha256']:raise RuntimeError('Before bytes differ')
        if row['path'] not in SOURCES and row['path'] not in (
            'artifacts/integration/packet-connections-20261006/packet-route-ledger.json',
            'docs/PACKET_CONNECTION_GOAL_20261006.md'):
            if raw!=(ROOT/row['path']).read_bytes():raise RuntimeError('Preserved source changed')
            unchanged.append(row)
    retained=[]
    for name in ('cn-create-name-encoding-01','cn-character-create-operation-01',
                 'cn-create-post-choice-reconnect-01','cn-account-selection-queue-commit-01'):
        prior=base/name;seal=json.loads((prior/'manifest.json').read_text(encoding='utf-8'))
        pins={r['path']:r['sha256'] for r in seal['files']};raw=(prior/'findings.json').read_bytes()
        if not seal['sealed'] or sha(raw)!=pins['findings.json']:raise RuntimeError('Prior receipt changed')
        save('retained-source/'+name+'/findings.json',raw)
        retained.append({'artifact':prior.relative_to(ROOT).as_posix(),'findings_sha256':sha(raw),'native_rules_or_acceptance_newly_proven':False})
    dump('source-relations.json',{'actual_chain':'source actual committed create/choice result ->same verified world connection ->bounded IO encoding/capacity ->held native frame ->serial game rule/common-state/result/operation checks ->publish exact next operation stage ->IO release ->single local ingress queue acknowledgement',
        'create02':'full exact created snapshot before/after mandatory QueueAccepted lease; publish AwaitingChoice/actual49 retry/actual failure before bytes leave',
        'choice18':'actual committed-choice lease/position/slot/common ownership; no stale pre-choice profile; publish Completed before bytes leave',
        'ordinary18_lifecycle':'existing native terminal/world/account close then new login/reselection; no entry on old grant',
        'local_completion':'exact published result marker/account/world session, no late old-root lease veto; not native client receipt',
        'failure':'held batch never written if qualification false/throws; preserve real saved COMMIT; no fake rollback or guessed error',
        'direct_suppliers':'actual result Current receives explicit ReplyCheck; no configured provider/default predicate',
        'retained':retained})
    findings={'round':ROUND,'native_sha256':PIN,'previous_goal_turn_classification':'progress: sealed full45/common40 CN ordinary create name projection and web controller source ACK, catalog94',
        'world_connection_publication_sources_added':1,'existing_create_choice_publication_bindings_strengthened':2,
        'create_choice_stage_qualified_rule_handoffs_added':1,'underlying_transport_barrier_reused_not_recounted':True,
        'new_source_owner_chains':0,'new_native_phase_source_bindings':0,'new_packet_values':0,'new_complete_bidirectional_routes':0,
        'whole_game_route_total':None,'whole_game_completion_percent':None,'levels_changed':False,
        'configured_native_providers_installed':False,'formal_application_hosted':False,'durable_recovery_complete':False,
        'build_run':False,'tests_run':False,'runtime_run':False,'database_access':False,'deployed':False,
        'existing_sources_unchanged':unchanged,'remaining':REMAINING}
    dump('findings.json',findings)
    with (ROOT/SOURCES[-1]).open('x',encoding='utf-8') as f:f.write(DOCUMENT)
    for rel in SOURCES:save('source/'+rel,(ROOT/rel).read_bytes())
    print(json.dumps({k:findings[k] for k in ('round','world_connection_publication_sources_added',
        'existing_create_choice_publication_bindings_strengthened','create_choice_stage_qualified_rule_handoffs_added','new_complete_bidirectional_routes')}))

if __name__=='__main__':main()
