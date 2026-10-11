"""Save actual CN18/common initial-position CAS source, without executing gameplay."""
import hashlib
import json
from .cn_wrapper_route_frontier import ROOT, PIN

NAME='cn-choice-common-position-cas-01'
ROUND='20261007-cn-choice-common-position-cas'
SOURCES=('src/db/SqliteRecoveredCharacterRepository.h','src/db/SqliteOwnedCreationPosition.cpp',
    'src/cn/auth/SharedCharacterCreateOperation.h','src/cn/auth/SharedCharacterCreateOperation.cpp',
    'tools/reconstruction/cn_choice_common_position_cas_delivery.py',
    'tools/reconstruction/dual_client_route_catalog.py',
    'docs/research/cn-choice-common-position-cas-20261007.md')


def sha(raw):return hashlib.sha256(raw).hexdigest()


def main():
    base=ROOT/'artifacts/integration/packet-connections-20261006';out=base/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():
        raise RuntimeError('Require fresh before sources and preserve previous delivery')
    unchanged=[]
    for row in json.loads((out/'before-manifest.json').read_text(encoding='utf-8')):
        raw=(out/'before'/row['path']).read_bytes()
        if sha(raw)!=row['sha256']:raise RuntimeError('Before source changed')
        if row['path'] not in SOURCES:
            if raw!=(ROOT/row['path']).read_bytes():raise RuntimeError('Existing/frozen source changed')
            unchanged.append(row)
    for name in ('cn-create-common-cas-01','cn-character-create-operation-01'):
        original=base/name
        manifest=json.loads((original/'manifest.json').read_text(encoding='utf-8'))
        pins={r['path']:r['sha256'] for r in manifest['files']}
        raw=(original/'findings.json').read_bytes()
        if not manifest['sealed'] or sha(raw)!=pins['findings.json']:
            raise RuntimeError('Sealed prior native/source evidence changed')
        p=out/'retained-source'/name/'findings.json';p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
    findings={'round':ROUND,'native_sha256':PIN,
        'previous_goal_turn_classification':'progress: concrete common creation CAS wired into existing17, catalog82 sealed',
        'new_common_initial_position_cas_writers':1,'existing_cn18_source_bindings_strengthened':1,
        'native_fields_newly_recovered':0,'native_spawn_mapping_guessed':False,
        'new_packet_values':0,'new_source_owner_chains':0,'new_native_phase_source_bindings':0,
        'new_complete_bidirectional_routes':0,'whole_game_route_total':None,'whole_game_completion_percent':None,
        'existing_sources_unchanged':unchanged,'levels_changed':False,'build_run':False,
        'tests_run':False,'runtime_run':False,'database_access':False,'deployed':False,
        'remaining':['Actual native choice-to-common area/scene/spawn and availability/permission source; full18 and native slot association.',
            'Post-create/post18 client summary/native slot/common-ID offer and owned admission update before1A.',
            'Durable semantic operation/replay/receipt and commit-versus-queue recovery; other native character initialization.',
            'Complete native account/world suppliers, all gameplay, hosting and whole-game directional/state/variant inventory.']}
    relations={'source_route':'existing ordinary18 identity ->actual NativeChoicePlan ->same shared SQLite repository ->insert_owned_creation_position ->existing ChoiceResult ->full native18 queue',
        'storage_tables':['accounts','recovered_characters','recovered_positions'],
        'transaction':'BEGIN IMMEDIATE; exact root/current owner and position absent; BeforeInsert; explicit INSERT revision1; staged root/position readback; BeforeCommit; COMMIT',
        'root_cas_fields':['id','account_id','slot','profile40','created_at','name_codepage','streamer_privilege'],
        'root_mutated':False,'existing_position_updated':False,'position_revision':'existing common persistence1, not native payload',
        'actual_position_source_required':True,'packed_choice_to_map_or_spawn_inference':False,
        'scope':'retained actual17 request pointer/common created ID/account/world session/permitted choice; exact repository identity',
        'native_slot_authority':'actual source predicate receives full18 first-byte low3 bits; no common-slot equality or clamp',
        'callbacks':'observe only, no writes/yields/event pumping/nested transactions; explicit Prepared/BeforeInsert/BeforeCommit/ReadyForReply',
        'before_commit_identity':'root is unchanged, so actual pending17 and SharedCreationLocationIdentity can be rechecked around rule predicate',
        'after_commit_identity':'actual NativeChoicePlan current scope/choice/native slot plus saved position exact revision rechecked before/after queue',
        'old_direct_choice_supplier':'preserved when choose supplied alone; typed prepare_choice is exclusive alternative',
        'initial_position_single_assignment':'existing position prevents repeat write; not a semantic idempotency receipt or native operation-consumption proof',
        'new_schema_or_table':False,'native_reply_defaults_added':False,'post_create_offer_refresh_added':False,
        'commit_vs_queue_gap':'saved position remains if subsequent allocation/queue/close fails; durable recovery is open'}
    doc=ROOT/SOURCES[-1]
    with doc.open('x',encoding='utf-8') as f:
        f.write('# CN18 initial common-position CAS source connection\n\n'
            'PHASE1 source work only: no builds/tests/native/server/SQL execution, migration or deploy. Levels unchanged. Pinned native17/18 identity and full-record contracts retained; no new native format, rule or spawn value recovered.\n\n'
            'Added insert_owned_creation_position to the actual common SQLite repository. It requires the exact previously created common root snapshot, actual source-supplied area/scene/x/y and observing operation/rule callbacks. Under BEGIN IMMEDIATE, existing loaders qualify the actual account/owned row and raw profile/name/codepage/style. The complete root must match and position must be absent. BeforeInsert rechecks actual pending choice; INSERT creates revision1 using existing persistence semantics. Root and inserted position are read back, then BeforeCommit rechecks rules/identity against staged position. False/throw rolls back. No existing position, movement save or character profile is changed.\n\n'
            'The existing ordinary18 controller now accepts either choose or prepare_choice, exclusively. A typed NativeChoicePlan requires exact Scope, created common ID, permitted choice, complete3-byte18, explicit initial position and actual authority. Sources.characters must be the same repository checked when the creation owner was prepared. The unchanged identity resolver rechecks pending17/permitted choices/common root around the in-transaction native rule predicate; it never derives coordinates from its packed reference. After COMMIT, ChoiceResult retains the real plan and saved position. Exact revision/coordinates, current scope/choice and native low3 slot relation are checked again through native18 queue acceptance. Full18 bytes remain raw, including the opaque second payload byte.\n\n'
            'The18 table at008865CC supplies routing/scene-selector/location-index projections, not common map IDs or spawn positions. NativeMapCatalog raw readiness is also not native spawn/permission evidence. The actual source must qualify destination availability, spawn and native slot/common-ID relation; no default(0,0), all18-open rule, slot-to-ID equality or native success bytes are added. The source API allows direct/direct, typed-create/direct-choice, direct-create/typed-choice and both typed, with exact repository identity and mutually exclusive providers. No populated production supplier is claimed.\n\n'
            'Existing commit_position, TW creation/movement, common creation CAS implementation, Application, Session, Selection, login composition and migration source remain unchanged. This new writer uses accounts/recovered_characters/recovered_positions, not version-specific tables or a CN DB. Prepared/BeforeInsert/BeforeCommit/ReadyForReply callbacks are observing and own captures. The identity is borrowed synchronously only during the SQL call.\n\n'
            'Initial-position absence plus its primary key prevents a second write; it is not a durable semantic replay/result receipt or proof that every native side effect/pending operation was atomically consumed. Other native resources/profile/role initialization, post-create/post18 native slot/common-ID summary and owned offer/admission update before1A remain open. The current world-preparation path already reads shared saved position, but the missing post-create offer means this alone cannot make a newly created role enter the world. Subsequent queue/allocation/close failures keep committed position; no rollback fiction or compensating saved-state deletion. Durable recovery and actual production hosting remain required.\n\n'
            'Increment: common initial-position CAS writer1, existing18 binding strengthened1. Previous18 owner is not counted twice. New opcode/phase/owner/full-route counts0. Whole-game total/percentage null. Next connect actual native destination/reply providers and post18 selection/admission lifecycle, then continue all gameplay and the native denominator.\n')
    for name,value in [('findings.json',findings),('source-relations.json',relations)]:
        with (out/name).open('x',encoding='utf-8') as f:f.write(json.dumps(value,indent=2)+'\n')
    for rel in SOURCES:
        p=out/'source'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/rel).read_bytes())
    print(json.dumps({k:findings[k] for k in ('round','new_common_initial_position_cas_writers','existing_cn18_source_bindings_strengthened','new_complete_bidirectional_routes')}))


if __name__=='__main__':main()
