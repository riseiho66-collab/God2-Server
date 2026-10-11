"""Retain concrete shared creation CAS and existing CN17 source wiring, files only."""
import hashlib
import json
from .cn_wrapper_route_frontier import ROOT, PIN

NAME='cn-create-common-cas-01'
ROUND='20261007-cn-create-common-cas'
SOURCES=('src/db/SqliteRecoveredCharacterRepository.h','src/db/SqliteOwnedCharacterCreation.cpp',
    'src/cn/auth/SharedCharacterCreateOperation.h','src/cn/auth/SharedCharacterCreateOperation.cpp',
    'tools/reconstruction/cn_create_common_cas_delivery.py','tools/reconstruction/dual_client_route_catalog.py',
    'docs/research/cn-create-common-cas-20261007.md')


def sha(raw):return hashlib.sha256(raw).hexdigest()


def main():
    base=ROOT/'artifacts/integration/packet-connections-20261006';out=base/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():
        raise RuntimeError('Require fresh before sources; preserve prior delivery')
    before=json.loads((out/'before-manifest.json').read_text(encoding='utf-8'))
    unchanged=[]
    for row in before:
        raw=(out/'before'/row['path']).read_bytes()
        if sha(raw)!=row['sha256']:raise RuntimeError('Before source changed')
        if row['path'] not in SOURCES:
            if raw!=(ROOT/row['path']).read_bytes():raise RuntimeError('Frozen/existing source changed')
            unchanged.append(row)
    # Reuse the existing native17/18 contract and original owner receipts;
    # no new native rules, packet layouts or restored historical proof claimed.
    for name in ('cn-character-create-operation-01','cn-summary-local-cache-01'):
        original=base/name
        manifest=json.loads((original/'manifest.json').read_text(encoding='utf-8'))
        pins={r['path']:r['sha256'] for r in manifest['files']}
        raw=(original/'findings.json').read_bytes()
        if not manifest['sealed'] or sha(raw)!=pins['findings.json']:
            raise RuntimeError('Retained sealed native/source receipt changed')
        p=out/'retained-source'/name/'findings.json';p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
    findings={'round':ROUND,'native_sha256':PIN,
        'previous_goal_turn_classification':'progress: existing native local-cache projection first implemented; catalog81 sealed',
        'new_common_character_creation_cas_writers':1,
        'existing_cn17_creation_source_bindings_strengthened':1,
        'native_rules_or_default_values_invented':False,'native_fields_newly_recovered':0,
        'new_source_owner_chains':0,'new_native_phase_source_bindings':0,
        'new_packet_values':0,'new_complete_bidirectional_routes':0,
        'whole_game_route_total':None,'whole_game_completion_percent':None,
        'existing_sources_unchanged':unchanged,'levels_changed':False,
        'build_run':False,'tests_run':False,'runtime_run':False,'database_access':False,'deployed':False,
        'remaining':['Actual native common40-byte candidate/slot/name/entitlement/choice policy and full02 issuer.',
            'Native18 choice transaction/default resource/role/world data and production source providers.',
            'Durable operation/semantic replay/commit-versus-queue recovery and atomic non-root native initialization.',
            'Complete native account/world success suppliers, all gameplay/hosting and whole-game denominator.']}
    relations={'source_route':'existing current17 ->actual NativeCreatePlan ->same shared SQLite repository ->create_owned_snapshot ->existing CreateResult/full02 queue ->existing18 owner',
        'repository_identity':'typed SQLite base pointer must equal exact Selection RecoveredCharacterRepository',
        'source_modes':'exactly one of existing create callback OR characters+prepare; choose mandatory for both',
        'before_write_inputs':['current pointer-qualified request/account/world session','actual full expected common account rows','explicit common storage candidate','complete native23-byte02','actual permitted choices','observing native rule/operation predicate'],
        'cas_fields':['id','account_id','slot','profile40','created_at','name_codepage','streamer_privilege'],
        'raw_name_storage_validation':'existing list_for_account validates name_bytes against profile; new name copied as exact first1..14 bytes before NUL',
        'transaction':'BEGIN IMMEDIATE, exact row-set match, BeforeInsert, actual INSERT, staged new/existing readback, BeforeCommit, COMMIT; false/exception rolls back',
        'slot_domain':'existing shared root schema0..1; explicit slot, no first-free allocator and no equality claim with CN low3 native slot',
        'charset_style':'explicit0/936/950 and0..3 from actual source, no language preference or copied credential interpretation',
        'nonzero02':'no candidate/choices and no SQL mutation; full source reply remains mandatory',
        'predicate_phases':['Prepared','BeforeInsert','BeforeCommit','ReadyForReply through02 and pending18'],
        'new_schema':False,'native_slot_mapping_guessed':False,'wire_defaults_added':False,
        'existing_TW_create_implementation_changed':False,'existing_CN_choice_branch_changed':False,
        'commit_vs_reply_gap':'Queue/allocation/close failure after COMMIT does not erase created row; durable receipt/recovery is still required before production hosting'}
    doc=ROOT/SOURCES[-1]
    with doc.open('x',encoding='utf-8') as f:
        f.write('# Common character creation CAS wired into existing CN17\n\n'
            'PHASE1 actual source changes only. No build/test/native/server/SQL execution, migration or deployment. Native levels unchanged. Existing pinned CN17/02/18 evidence retained; this is not new native format or permission recovery.\n\n'
            'Added SqliteRecoveredCharacterRepository::create_owned_snapshot in an additive compilation unit. The writer uses the same common accounts/recovered_characters tables and DB handle. It requires the actual complete expected account row set, an explicitly supplied common40-byte profile/slot/name-codepage/style, and an observing operation predicate. A native44-byte17 is never copied or padded into that storage candidate. Shared schema slots0..1 are a storage constraint, not CN wire-slot identity; allocation is explicit and no new cap/level policy is selected.\n\n'
            'Under BEGIN IMMEDIATE, existing list_for_account checks actual account existence, every stored profile/raw name, ownership and bounded slots. Full existing snapshots are compared byID rather than positional order; size mismatch catches additional/deleted rows and comparison catches changed profiles/encoding/style/creation time. BeforeInsert then checks the real serial-game selection plus source operation/rules. INSERT uses the exact proposed name prefix and explicit metadata; schema UNIQUE/FK constraints remain authoritative. The actual new ID/created_at are read from SQLite, all old rows remain unchanged, and BeforeCommit sees staged insertion. False/throw rolls back. No existing row is replaced, selected by an incoming claimed ID, or implicitly assigned the first free slot.\n\n'
            'SharedCharacterCreateOperation::Sources now accepts either the unchanged direct create callback or a typed characters+prepare source, exclusively, with the existing real choose supplier still mandatory. The new path checks exact common repository identity at preparation, retains the full real account snapshots, and invokes the concrete writer from start(). NativeCreatePlan requires complete02, actual scope and observing permission/operation state before any write; status0 requires a real storage candidate and nonempty qualified unique choices. Nonzero status requires no candidate/choices and does not invoke SQL. Prepared/BeforeInsert/BeforeCommit/ReadyForReply distinguish staged and committed phases. The actual plan survives existing queue acceptance and the pending18 operation. Existing current-selection checks are repeated around in-transaction rule callbacks. No default-true rule or synthetic success is introduced.\n\n'
            'The old direct source mode, ordinary18 choice implementation, native serializers, TW create implementation, Application, Session, Selection, login composition and migration source remain unchanged. The shared storage loader already validates native names without converting them.0/936/950 name metadata and existing CUSTOM-0054 style domain are explicitly source supplied; this code does not infer entitlement or assign a streamer role.\n\n'
            'This writes the common identity root only. Actual native candidate/default resources/role/choice/profile mapping and full02 producer, fees and other native initialization, durable operation/replay receipts, cross-process policy and commit-versus-queue recovery remain required. After COMMIT, a queue/allocation/close failure leaves saved state; no compensating deletion or rollback fiction is claimed. Actual prepared source callbacks must not write/yield/pump events/nest transactions and must own captured lifetimes. The complete17 route, native18 writer and configured production host remain incomplete.\n\n'
            'Increment: concrete common CAS writer1 and existing CN17 source binding strengthened1. Prior17 owner chain is not counted twice; new packet values/phase bindings/owner chains/full routes0. Whole-game total/percentage null. The next action is to recover/provide actual native creation/choice data and durable source owners through this real backend, continuing whole-game native inventory.\n')
    for name,value in [('findings.json',findings),('source-relations.json',relations)]:
        with (out/name).open('x',encoding='utf-8') as f:f.write(json.dumps(value,indent=2)+'\n')
    for rel in SOURCES:
        p=out/'source'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/rel).read_bytes())
    print(json.dumps({k:findings[k] for k in ('round','new_common_character_creation_cas_writers','existing_cn17_creation_source_bindings_strengthened','new_complete_bidirectional_routes')}))


if __name__=='__main__':main()
