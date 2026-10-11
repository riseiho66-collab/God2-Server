"""Retain actual typed CN world-preparation source wiring; files only.

No builds, tests, native/server/Lua/resource execution, DB access or deploy.
Source identities are integration policy; they are not invented native rules.
"""
import hashlib
import json

from .cn_wrapper_route_frontier import ROOT, PIN

NAME = 'cn-typed-world-preparation-composition-01'
ROUND = '20261007-cn-typed-world-preparation-composition'
MODIFIED = ('src/cn/auth/SharedLoginComposition.h', 'src/cn/auth/SharedLoginComposition.cpp',
            'src/cn/world/SharedWorldPreparation.h', 'src/cn/world/SharedWorldPreparation.cpp',
            'src/cn/world/SharedInitialScene.h', 'src/cn/world/SharedInitialScene.cpp')
CONTEXT = ('src/cn/net/SharedCredentialServer.h', 'src/cn/net/SharedCredentialServer.cpp',
           'src/cn/auth/SharedWorldSelection.h', 'src/cn/auth/SharedWorldSelection.cpp',
           'src/cn/auth/SharedCharacterDeleteOperation.h', 'src/cn/auth/SharedCharacterDeleteOperation.cpp',
           'src/auth/SharedCharacterRemovalPresence.h', 'src/auth/SharedCharacterRemovalPresence.cpp',
           'src/game/SharedWorldPresence.h', 'src/game/SharedWorldPresence.cpp',
           'src/cn/world/SharedNativeMovementScene.h', 'src/cn/world/SharedNativeMovementScene.cpp',
           'src/db/NativeMapCatalog.h', 'src/db/RecoveredCharacterRepository.h')
SOURCES = MODIFIED + CONTEXT + ('tools/reconstruction/cn_typed_world_preparation_composition_delivery.py',
    'docs/research/cn-typed-world-preparation-composition-20261007.md')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    base = ROOT / 'artifacts/integration/packet-connections-20261006'
    out = base / NAME
    if not (out / 'before-manifest.json').exists() or (out / 'findings.json').exists():
        raise RuntimeError('Fresh before sources required; preserve earlier deliveries')
    ledger = json.loads((base / 'packet-route-ledger.json').read_text(encoding='utf-8'))
    files = []

    def save(rel, raw, original):
        p = out / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open('xb') as stream:
            stream.write(raw)
        files.append({'path': rel, 'original': str(original), 'bytes': len(raw),
                      'sha256': digest(raw)})

    def dump(rel, value):
        save(rel, (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode(),
             'static source accounting; no gameplay execution')

    # Keep the older conditional selection/bootstrap/native contracts intact;
    # this round changes composition identity, not native packet semantics.
    old = base / 'cn-selected-world-preparation-01'
    pins = ledger['cn_account_admission_evidence']['cn-selected-world-preparation-01']['artifact_sha256']
    for rel in ('integration-manifest.json', 'selected-world-preparation-source-relations.json'):
        code = (old / rel).read_bytes()
        if digest(code) != pins[rel]:
            raise RuntimeError('Prior native/source provenance changed')
        save('retained-source/cn-selected-world-preparation-01/' + rel, code, old / rel)
    for name, rels in (('shared-character-removal-presence-01', ('findings.json', 'delivery.json')),
                       ('cn-crt-winapi-thunk-map-01', ('findings.json', 'delivery.json'))):
        old = base / name
        manifest = json.loads((old / 'manifest.json').read_text(encoding='utf-8'))
        pins = {r['path']: r['sha256'] for r in manifest['files']}
        for rel in rels:
            code = (old / rel).read_bytes()
            if not manifest['sealed'] or digest(code) != pins[rel]:
                raise RuntimeError('Sealed source provenance changed')
            save('retained-source/' + name + '/' + rel, code, old / rel)
    preserved = []
    for rel in ('src/core/Application.cpp', 'src/net/Session.cpp',
                'src/auth/RecoveredAccountLogin.cpp', 'src/cn/net/SharedCredentialServer.cpp',
                'src/cn/auth/SharedWorldSelection.cpp', 'src/auth/SharedCharacterRemovalPresence.cpp'):
        code = (ROOT / rel).read_bytes()
        if code != (out / 'before' / rel).read_bytes():
            raise RuntimeError('Frozen/existing source changed')
        preserved.append({'path': rel, 'byte_identical': True, 'sha256': digest(code)})
    rel = 'src/cn/auth/SharedLoginComposition.cpp'
    before = (out / 'before' / rel).read_text(encoding='utf-8')
    after = (ROOT / rel).read_text(encoding='utf-8')
    old_account = before[before.index('    result.account='):before.index('    result.world=')]
    new_account = after[after.index('    result.account='):after.index('    result.world=')]
    if old_account != new_account:
        raise RuntimeError('Account authentication/catalog source block changed')
    facts = {'old_source_shape': 'NativeOffer + arbitrary Selected callback + separately declared presence',
        'new_source_shape': 'NativeOffer + actual SharedWorldPreparation pointer',
        'listener_sources': ['same actual RecoveredCharacterRepository', 'same actual const NativeMapCatalog'],
        'pre_attach_source_check': 'SharedWorldPreparation::owns_sources(context characters/maps)',
        'selection_source': 'actual preparation.selected(); callback retains that exact controller',
        'deletion_exclusion_source': 'actual preparation.presence_registry(), not independently supplied declaration',
        'deletion_source_check': 'actual complete deletion source must own the exact preparation registry',
        'catalog_const_flow': 'SharedServerPlan::Context::maps ->SharedWorldPreparation ->SharedInitialScene; only NativeMapCatalog::lookup used',
        'const_cast_or_catalog_copy_added': False,
        'normal_and_transfer_selection_controller': 'existing preparation; mandatory transfer reservation qualifier preserved',
        'native_wire_changed': False, 'native_reply_default_added': False,
        'spawn_actor_rule_invented': False, 'new_schema_or_table': False,
        'account_controller_source_block_byte_identical': True,
        'account_controller_source_block_sha256': digest(new_account.encode()),
        'native_controller_data_suppliers_implemented': False,
        'global_tw_cn_occupancy_host_proven': False,
        'formal_application_hosted': False}
    findings = {'round': ROUND, 'native_sha256': PIN,
        'previous_goal_turn_classification': 'progress: catalog79 retained actual CRT API cache/name/module/argument provenance; full server remains incomplete',
        'existing_world_preparation_composition_bindings_strengthened': 1,
        'read_only_exact_source_identity_views_added': 1,
        'modified_existing_cpp_source_files': len(MODIFIED),
        'new_source_owner_chains': 0, 'new_native_phase_source_bindings': 0,
        'new_packet_values': 0, 'new_complete_bidirectional_routes': 0,
        'native_contracts_newly_recovered': False,
        'native_permission_or_reply_authority_added': False,
        'formal_application_hosted': False, 'schema_or_table_change': False,
        'account_controller_source_block_byte_identical': True,
        'preserved_existing_sources': preserved,
        'whole_game_route_total': None, 'whole_game_completion_percent': None,
        'levels_changed': False, 'build_run': False, 'tests_run': False,
        'runtime_run': False, 'database_access': False, 'deployed': False,
        'remaining': [
            'Actual production world supplier must construct/retain this controller using the actual common repository/catalog/presence/visibility and qualified native assets/reservation authorities.',
            'Complete native account success/catalog/summary/offer/02/2A/03, real actor allocation/placement/permission/timing and transfer gameplay sources remain missing.',
            'Actual TW/CN shared presence and legacy World/movement host binding, native mutation/guild/replay/durable recovery and CN1E remain incomplete.',
            'Whole-game phase/state/variant/indirect/deferred denominator, all gameplay and formal native/web hosting remain open.']}
    doc = ROOT / SOURCES[-1]
    if doc.exists():
        raise RuntimeError('Preserve prior research document')
    doc.write_text('# CN login composition bound to actual shared world preparation\n\n'
        'PHASE1 source integration only: no builds/tests/native/server/Lua/resource execution, gameplay DB access or deployment. Levels unchanged. Pinned CN contracts retained from the existing selection/preparation receipt, not newly invented.\n\n'
        'Previously SharedLoginSources::World accepted Selected and presence independently. Comparing the deletion guard to the separately supplied presence did not establish that the arbitrary Selected callback used that registry. The world continuation now requires an actual SharedWorldPreparation pointer. Before attaching the world selection owner, compose_native_login compares its retained character repository and map catalog to the listener Context, obtains its real presence_registry(), and checks complete deletion sources against that exact registry. It obtains Selected only through preparation.selected(), which retains the same controller.\n\n'
        'The new owns_sources() accessor checks exact object identity on the serial game owner; it neither queries SQLite nor grants native permission. RecoveredCharacterRepository/NativeMapCatalog remain the actual host-owned sources and must outlive drain. Absence or foreign sources fail before native1F selection attachment; no success or fallback controller is invented. The world supplier no longer accepts independent .selected or .presence fields and must return .preparation. No concrete enabled provider in the current source tree used those removed fields; future configured providers must use this typed API.\n\n'
        'SharedServerPlan::Context already exposes a const NativeMapCatalog. The actual preparation and initial-scene APIs now borrow const NativeMapCatalog& consistently, so a controller can be constructed from that exact Context without casting away constness or duplicating the catalog. Their only catalog operations remain existing lookup() calls; scene qualification, loaders, movement adoption, transfer handling and save mutations are unchanged.\n\n'
        'The existing preparation still requires common presence/visibility, pinned assets, a real actor Reservation, full native02/2A, generation-qualified saved position, initial scene or actual transfer qualifier, and gameplay/movement authorities. This source wiring does not implement those missing suppliers, bootstrap issuers or production placement/rules. It does not prove TW lifecycle uses that registry; actual common/legacy host wiring remains necessary. Native deletion permission, guild/replay/receipts and1E remain open.\n\n'
        'Application, Session, actual credential auth, listener, selection owner and removal occupancy implementation remain byte-identical. The account success/catalog lambda body remains byte-identical inside the changed composition file. This is an existing conditional source seam strengthened once, not a new owner chain/opcode/phase count; prior preparation owner is not counted twice.\n\n'
        'Existing preparation composition bindings strengthened1; read-only exact-source getter1; modified C++ headers/implementations6. New packet values, owner chains, phase bindings and complete bidirectional routes0. Whole-game total and percentage null. Accounts/saves/chat/IME/native fonts/encoding/numeric/level behavior preserved; no schema/table change. Next supply actual native world/account data and production source owners through this real typed continuation, while continuing the whole-game native denominator.\n', encoding='utf-8')
    for rel in SOURCES:
        save('source/' + rel, (ROOT / rel).read_bytes(), ROOT / rel)
    dump('typed-world-preparation-source-relations.json', facts)
    dump('findings.json', findings)
    dump('source-manifest.json', {'files': files})
    print(json.dumps({k: findings[k] for k in ('round',
        'existing_world_preparation_composition_bindings_strengthened',
        'modified_existing_cpp_source_files', 'new_source_owner_chains',
        'new_complete_bidirectional_routes', 'account_controller_source_block_byte_identical')}))


if __name__ == '__main__':
    main()
