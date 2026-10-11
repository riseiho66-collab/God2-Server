"""File-only actual CN1F and selected02/2A preparation/dispatcher publication."""
import hashlib
import json
from .cn_wrapper_route_frontier import ROOT,PIN

NAME='cn-selected-world-publication-01'
ROUND='20261007-cn-selected-world-publication'
SOURCES=('src/cn/auth/SharedWorldSelection.h','src/cn/auth/SharedWorldSelection.cpp',
    'src/cn/world/SharedWorldPreparation.h','src/cn/world/SharedWorldPreparation.cpp',
    'tools/reconstruction/cn_selected_world_publication_delivery.py','tools/reconstruction/dual_client_route_catalog.py',
    'docs/research/cn-selected-world-publication-20261007.md')
REMAINING=[
    'Actual full native1F/02/2A reservation/actor/default/profile/rules/bootstrap/gameplay/transfer/movement sources and configured Application hosting remain open.',
    'Bootstrap1F/23/30/36 and initial1C entered/visibility/gameplay publication need their own actual source contracts; this selected entry does not close the world route.',
    'Durable native operation/semantic replay and committed state/publication/crash/cross-process recovery remain open.',
    'All TW/CN/web gameplay/numeric wire/object/display and whole-game phase/state/variant/indirect/deferred denominator, then comprehensive original-client acceptance. Levels unchanged.']
DOCUMENT='''# CN world list and selected entry: actual preparation before IO publication

PHASE1 static source integration/accounting only. No build/tests/native/API/DLL/codec/server/SQL execution, migration or deployment. Previous ordinary creation02/18 publication turn was progress. Levels, native wire, actor/role defaults, existing accounts/saves and frozen functionality unchanged. No new native rules/fields/packet values/complete routes.

SharedWorldSelection::attach now publishes the complete source-issued125-byte1F behind the existing same verified world connection/IO barrier. Current common offer/row-ID/slot lineage is checked while output is held. offer_queued is committed before bytes leave, then the single local queue completion releases the suspended world00 ingress. It does not repeat an obsolete offer/root predicate after a valid later selection or mutation. Exact NativeOffer/source/native data authority still must be provided; this does not recover all1F issuer rules or every slot/normal/transfer variant.

Selected entry previously installed ready ingress before calling ordinary send_batch, then checked ready/preparation snapshots only after02/2A might leave. It now holds a private selected_publication_pending exclusion, preallocates the exact ready ingress, and requires an actual preparation Publication predicate. complete02 precedes complete2A in the same retained aggregate, with no byte synthesis or record split. Mandatory BeforePublish and QueueAccepted distinguish scheduling from the game publication after actual native framing/capacity succeeds.

Both sides of the reservation predicate recheck this current pending character/account/world-session, ownership/offered mapping, exact SharedWorldReady at its original First1F stage/position/handle, fresh shared NativeMapCatalog row and full raw source identity, complete2A and actual previous transfer position. Normal selection also rechecks the exact SharedInitialScene/ready registry-generation and resource snapshot. CF transfer must supply its own reservation/lifecycle and actual predecessor; it never receives normal initial geometry. The observer cannot yield, write, pump events or confer authority from a client handle/name/position. A second preparation cannot obtain the choice connection while this publication is pending.

The held IO publication asks the mandatory preparation predicate at QueueAccepted, repeats all current ready/map/scene checks, then moves the preallocated dispatcher into selected_ingress and retains selected_ready/normal_scene before releasing native bytes. These member transitions do not allocate or invoke rules. Transport still performs its same exact verified WORLD identity/ticket checks around this callback; close or false/throw refuses the held batch. There is no automatic initial-ready acceptance or invented native status/handle/scene permission.

SharedWorldPreparation supplies that actual predicate with its same presence preparation lease and retained real Reservation::current. The reservation API now explicitly receives the publication stage (default BeforePublish for existing preparation observations); no default-current implementation/provider is created. At queue completion it consults the exact published result and same live account/world session rather than requiring the old prepared lease/First1F/position after native bootstrap may already progress. Selection's final1A completion likewise does not reread a stale offered-character snapshot after successful publication. Existing ready cleanup remains bound to this exact transport/incarnation, and the retained ReleaseOnce releases the native supplier once. Shared preparation completion is single-use across synchronous exceptions and posted queue callbacks; a late duplicate callback cannot tear down a later valid incarnation.

The existing underlying native transport barrier, verified world publication wrapper, SharedWorldReady/bootstrap, SharedInitialScene/resource loaders, shared scene/position/map/visibility sources, common storage and Application remain unchanged. Their prior integration manifests and scoped snapshots are retained as historical provenance, not current native runtime acceptance. Other bootstrap/entered/terminal publication and full providers/hosting/durable recovery remain open. No old historical mapped TW image is restored or acceptance baseline refreshed here.

Increment: existing world1F publication strengthened1, selected02/2A publication strengthened2, actual preparation-stage rule handoff1 and single preparation completion owner1. New owner chains/phase bindings/opcode values/complete bidirectional routes0. Whole-game denominator/completed/percentage unknown; this conditional source does not certify playable entry or all gameplay.
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
        if sha(data)!=row['sha256']:raise RuntimeError('Before bytes differ')
        if row['path'] not in SOURCES and row['path'] not in (
            'artifacts/integration/packet-connections-20261006/packet-route-ledger.json','docs/PACKET_CONNECTION_GOAL_20261006.md'):
            if data!=(ROOT/row['path']).read_bytes():raise RuntimeError('Preserved source changed')
            unchanged.append(row)
    retained=[]
    for name in ('cn-selected-world-preparation-01','cn-world-selection-owner-01','cn-initial-scene-provider-01'):
        prior=base/name;raw=(prior/'integration-manifest.json').read_bytes();manifest=json.loads(raw)
        save('retained-source/'+name+'/integration-manifest.json',raw);selected=[]
        for row in manifest['snapshots']:
            if not row['path'].endswith(('SharedWorldSelection.h','SharedWorldPreparation.cpp','CnWorldEntry.h')):continue
            path=(prior/row['path']).resolve()
            if not path.is_relative_to(prior.resolve()):raise RuntimeError('Prior snapshot path outside original artifact')
            data=path.read_bytes()
            if sha(data)!=row['sha256']:raise RuntimeError('Prior snapshot differs')
            save('retained-source/'+name+'/'+row['path'],data);selected.append(row)
        retained.append({'artifact':prior.relative_to(ROOT).as_posix(),'integration_manifest_sha256':sha(raw),
            'scoped_historical_snapshots':selected,'all_original_native_evidence_reread':False,'native_runtime_acceptance':False})
    prior=base/'cn-create-reply-publication-01';seal=json.loads((prior/'manifest.json').read_text(encoding='utf-8'))
    pins={r['path']:r['sha256'] for r in seal['files']};data=(prior/'findings.json').read_bytes()
    if not seal['sealed'] or sha(data)!=pins['findings.json']:raise RuntimeError('Previous sealed publication differs')
    save('retained-source/cn-create-reply-publication-01/findings.json',data)
    dump('source-relations.json',{'list1F':'actual NativeOffer/current common offer ->verified world IO barrier ->publish offer_queued ->native1F release ->single local world00 completion',
        'selected':'actual pending1A/common position/native actor reservation/same lease/scene/ready ->explicit stage predicate ->held02 then2A ->publish exact preallocated ready dispatcher/scene ->IO release ->single local1A completion',
        'current':'original pending choice/account/world-session, common ownership, ready First1F/position/handle, fresh raw map row/full2A, normal exact scene or actual transfer predecessor/lifecycle; before and after actual reservation predicate',
        'late_completion':'same published result/connection, no obsolete prepared lease/First1F stage/map/offer snapshot veto',
        'failure':'original incarnation visibility/presence cleanup plus actual native ReleaseOnce, no other session revocation or rollback/guessed success',
        'retained_historical_sources':retained})
    findings={'round':ROUND,'native_sha256':PIN,'previous_goal_turn_classification':'progress: sealed actual ordinary02/18 publication and controlled-raster ACK, catalog95',
        'existing_world_list_publication_bindings_strengthened':1,'existing_selected_entry_publication_bindings_strengthened':2,
        'preparation_stage_rule_handoffs_added':1,'single_preparation_completion_owners_added':1,
        'underlying_world_transport_publication_reused_not_recounted':True,'new_source_owner_chains':0,
        'new_native_phase_source_bindings':0,'new_packet_values':0,'new_complete_bidirectional_routes':0,
        'whole_game_route_total':None,'whole_game_completion_percent':None,'levels_changed':False,
        'configured_native_reservation_providers_installed':False,'formal_application_hosted':False,
        'build_run':False,'tests_run':False,'runtime_run':False,'database_access':False,'deployed':False,
        'existing_sources_unchanged':unchanged,'remaining':REMAINING}
    dump('findings.json',findings)
    with (ROOT/SOURCES[-1]).open('x',encoding='utf-8') as f:f.write(DOCUMENT)
    for rel in SOURCES:save('source/'+rel,(ROOT/rel).read_bytes())
    print(json.dumps({k:findings[k] for k in ('round','existing_world_list_publication_bindings_strengthened',
        'existing_selected_entry_publication_bindings_strengthened','preparation_stage_rule_handoffs_added','new_complete_bidirectional_routes')}))

if __name__=='__main__':main()
