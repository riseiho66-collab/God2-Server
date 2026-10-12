"""One-shot source/text/hash custody only; never import or execute product code."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path('C:/Users/risei/Desktop/God2/God2-Server')
OUT = Path(__file__).resolve().parent
HEAD = '31d79bad16484d0a2021a938cb1a99b58231ba14'
SOURCES = [
    'src/db/NativeWorldEntrySnapshotRepository.h',
    'src/db/SqliteNativeWorldEntrySnapshotRepository.h',
    'src/db/SqliteNativeWorldEntrySnapshotRepository.cpp',
    'src/db/NativeEquipmentSnapshotRepository.h',
    'src/db/SqliteNativeEquipmentSnapshotRepository.h',
    'src/db/NativeItemDefinitionObservation.h',
    'src/db/NativeMapItemCatalog.h',
    'src/db/OwnedInventoryRepository.h',
    'src/db/SqliteOwnedInventoryRepository.h',
    'src/db/SqliteOwnedInventoryRepository.cpp',
    'src/db/SqliteOwnedEquipmentTransaction.h',
    'src/db/SqliteArmorSlotRepository.h',
    'src/db/SqliteArmorSlotRepository.cpp',
    'src/db/SqliteOwnedInstanceTradeRepository.cpp',
    'src/game/TaiwanOwnedBagItemMaterial.h',
    'src/game/SharedTaiwanNativeWorldEntryOfferSource.h',
    'src/game/SharedTaiwanNativeWorldEntryOfferSource.cpp',
    'src/game/SharedTaiwanStoredWorldEntrySource.h',
    'src/protocol/RecoveredInventoryProjection.h',
    'src/protocol/RecoveredTaiwanInventoryItemRecord.h',
    'tools/strike_lab/import_native_armor_20261002.py',
    'tools/strike_lab/private_armor_transfer_20261002.py',
    'tools/strike_lab/private_owned_foreign_bank_v02_20261003.py',
    'tools/strike_lab/private_owned_instance_trade_20261003.py',
    'tools/strike_lab/run_private_owned_companions.py',
]
CUTS = [
    ('src/core/Application.cpp', 1068, 1110, 'hosted-owned-and-scalar-projection'),
    ('src/core/Application.cpp', 1417, 1461, 'hosted-trade-owner-construction'),
    ('src/core/Application.cpp', 5340, 5359, 'saved-scalar-restoration'),
    ('src/db/SqliteOwnedInventoryRepository.cpp', 133, 168, 'common-supplied-tuple-stage'),
    ('src/db/SqliteOwnedInventoryRepository.cpp', 214, 245, 'definition-observation-separate'),
    ('src/db/SqliteOwnedInstanceTradeRepository.cpp', 251, 309, 'actual-transfer-transaction'),
    ('src/game/SharedTaiwanNativeWorldEntryOfferSource.cpp', 242, 279, 'full-entry-issuer-required'),
    ('tools/strike_lab/private_armor_transfer_20261002.py', 26, 79, 'armor-synthetic-instance-declaration'),
    ('tools/strike_lab/private_armor_transfer_20261002.py', 247, 276, 'armor-explicit-overlay-seed'),
    ('tools/strike_lab/run_private_owned_companions.py', 60, 81, 'weapon-synthetic-declaration-and-seed'),
    ('tools/strike_lab/private_owned_foreign_bank_v02_20261003.py', 173, 215, 'pre-trade-overlay-material-lineage'),
    ('tools/strike_lab/private_owned_instance_trade_20261003.py', 156, 183, 'trade-custom-seed-lineage'),
    ('tools/strike_lab/private_owned_instance_trade_20261003.py', 277, 299, 'post-fixture-client-cache-observation'),
    ('tools/strike_lab/import_native_armor_20261002.py', 1, 53, 'pinned-definition-only-source-envelope'),
    ('tools/strike_lab/import_native_armor_20261002.py', 117, 148, 'definition-cache-import-not-player-instance'),
    ('docs/research/town-guide-content-evidence-20260921.md', 459, 490, 'custom-precondition-and-observed-town-cache'),
]

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)

def save_json(name, value):
    (OUT / name).write_bytes((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))

assert git('rev-parse', 'HEAD').decode().strip() == HEAD
assert not (OUT / 'SEAL.json').exists()
refs = []
source_bytes = {}
for path in sorted(set(SOURCES + [c[0] for c in CUTS])):
    raw = (ROOT / path).read_bytes()
    pinned = git('show', HEAD + ':' + path)
    assert raw == pinned, path
    source_bytes[path] = raw
    item = {'path': path, 'head': HEAD, 'bytes': len(raw), 'sha256': sha(raw), 'current_equals_git_show': True}
    if path in SOURCES:
        target = OUT / 'sources' / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        item['retained_member'] = target.relative_to(OUT).as_posix()
    refs.append(item)
cuts = []
for path, start, end, label in CUTS:
    raw = source_bytes[path]
    lines = raw.splitlines(keepends=True)
    assert 1 <= start <= end <= len(lines)
    begin = sum(map(len, lines[:start - 1]))
    finish = sum(map(len, lines[:end]))
    content = raw[begin:finish]
    member = 'cuts/' + label + '.txt'
    target = OUT / member
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    cuts.append({'path': path, 'start_line': start, 'end_line': end, 'start_byte': begin,
                 'end_byte_exclusive': finish, 'member': member, 'bytes': len(content), 'sha256': sha(content)})
save_json('source-references.json', {'head': HEAD, 'sources': refs, 'cuts': cuts,
    'operations': 'file reads, SHA256, git show/rev-parse; source text only',
    'target_execution_count': 0, 'sql_execution_count': 0, 'native_execution_count': 0,
    'resource_decode_or_parser_execution_count': 0})
save_json('bounded-search-and-corrections.json', {
    'discovery': 'rg --files on current src/tools/docs, followed by literal source searches; no retired source read',
    'OriginalClientInventory_exact_symbol': 'No match in current src/tools/docs; this is scoped, not global absence.',
    'read_errors_preserved': [
        'Early broad filename list included artifacts and was truncated; no artifact values from that listing were used.',
        'Guessed private_owned_armor_transfer_20261002.py did not exist; corrected through filename discovery to private_armor_transfer_20261002.py.',
        'Guessed SqliteOwnedEquipmentEntryTransaction.h did not exist; actual declarations are in SqliteOwnedEquipmentTransaction.h.',
        'Windows literal wildcard source paths failed; no values were read; corrected to real discovered paths.',
        'Declared old native-armor/town-run artifact directories were absent at their old repository paths; no DB or JSON was read there.'
    ],
    'input_pin_qualification': 'Historical encoded70a4/decoded75c3/parser149c and installed c5d8/currentef297 are source declarations here, not new in-place image/resource qualification.',
    'helper_failures': [{'helper': 'capture_material_source352.py', 'exit_code': 1, 'range': '117..156 beyond148; preserved failure-initial'}], 'helper_successes': 1})
save_json('supplier-gap.json', {
    'selected_actual_host': 'TW owned whole-instance trade29..2D CUSTOM-0069, Application1417..1461',
    'closed_supplier': 'Existing scalar/armor/weapon/gem overlays can be transferred with preserved20 provenance and a real transfer receipt.',
    'pre_overlay_material_declarations': [
        'Armor instance() explicitly packs key/selector plus zero16 then writes test dimension bytes8..11; ORIGIN CUSTOM_TEST_NOT_NATIVE.',
        'Weapon seed_weapon_transfers() provides two literal synthetic20 operands; CUSTOM-0046/CUSTOM_TEST_NOT_NATIVE.',
        'Foreign-bank v02 copies accepted fixture armor/weapon, XORs alternate opaque tail and synthesizes TWP20; all CUSTOM_TEST_NOT_NATIVE.',
        'Trade prepare() clones that fixture lineage and relabels neither origin nor generation authority.'
    ],
    'definitions': 'NativeItemDefinitionObservation preserves token0 native_key independently of metadataDWORD0 token5; native historical parsed396 is not common definition mapping or item instance.',
    'original25': 'No genuine original-server25 declaration is established by these selected seed/import paths; legacy projection supplies opaqueWORD0 explicitly.',
    'observed_prefix': 'Native post-fixture raw24 cache observation confirms consumption of supplied fixtures; it does not turn their source into original acquisition or an original25 packet.',
    'world_entry': 'NativeWorldEntrySnapshot is a separate version-keyed raw2A/root/pose delivery witness requiring a genuine full issuer. It does not create bag1215 or common identities.',
    'earliest_missing_before_mint': [
        'Genuine same-event per-instance original25 source, including incoming count/slot/opaqueWORD and complete20, with immutable capture/save/import identity and original producer chain.',
        'Explicit qualified common definition binding and globally stable instance identity plus immutable acquisition event/entitlement for the real saved owner, before stage_replace line143.',
        'Complete current native50x24+DA15 witness tied to root/positive pose/actualactor; rowprefix1..3 cannot be inferred from3B opaqueWORD or from conditional cache clear.'
    ],
    'smallest_seam_if_supplier_obtained': 'Existing same-DB SqliteOwnedEquipmentTransaction::replace_from_issuer accepts both complete populations atomically; it does not supply missing origin/entitlement. Only after genuine authority exists may material aliases item20/full3b25 be retained from the same declaration.',
    'next_concrete_location': 'First existing fixture overlay seed is private_armor_transfer_20261002.py247..276 or run_private_owned_companions.py60..81. Replace authority only from a retained genuine original-server event/save/import producer; tracing client U8560D..8560F+24I writes addresses cache-prefix provenance but does not by itself recover acquisition entitlement.',
    'native5D': 'Separate full movement ACK authority; not a bag1215/full25 material supplier.',
    'implementation_proposed': False, 'new_route_credit': 0, 'native_acceptance_credit': 0})

report = '''# Round352 original bag material issuer source audit

Snapshot: clean published351 HEAD31d79bad16484d0a2021a938cb1a99b58231ba14. This package is source/text/hash only. No tracked files changed and no target API, SQL, resource parser/codec, native code, compiler or tests executed.

The selected actual hosted alternate is CUSTOM-0069 whole-instance trade, not another public town receipt wrapper. Application1417..1461 binds real owned repositories and peers; SqliteOwnedInstanceTradeRepository251..309 moves existing legacy overlays under paired owner CAS and one real transfer receipt. Its response preparation at254 is before the owned transaction. This conserves an existing legacy20 instance; it does not establish where that instance originated or a common acquisition identity.

Following its pre-overlay lineage reaches exact explicit fixture producers. private_armor_transfer_20261002.py56..79 constructs20 from key/selector/zero bytes and test dimension bytes8..11, then247..276 seeds the overlay. run_private_owned_companions.py60..81 declares literal synthetic weapon20. private_owned_foreign_bank_v02_20261003.py173..215 copies those fixture instances, makes an alternate tail by XOR and constructs a TWP20 bytearray. Every such overlay is marked CUSTOM_TEST_NOT_NATIVE. private_owned_instance_trade_20261003.py156..183 retains that same fixture lineage. An actual client consuming and later exposing the full24 cache, at277..299, proves transport of these supplied operands; it does not establish original-server acquisition. No fixture values are proposed for production/common population.

The actual definition importer is independently narrower: import_native_armor_20261002.py1..53 and117..148 declare historical70a4/75c3 parsed396 EQU/TEQ definition authority only and player_instances_created0. NativeItemDefinitionObservation likewise keeps native token0 key separate from metadataDWORD0 token5 and explicitly excludes common definition mapping, acquisition and entitlement. Its current SQL reader at214..245 cannot mint that authority. Historical/source/build pins in these scripts are declarations, not new verification of resource/EXE bytes here.

The older town observation is a separate narrow example: the retained document459..490 states an explicitly constructed empty CUSTOM-0015 fixture, then original-client24 occupancy after the CUSTOM-0022 scalar5569/count1 reward. This is authentic client consumption of an own-server custom scalar result, not an original25 record/instance/acquisition declaration. Application1089..1108 explicitly describes that scalar item's18zero metadata and constructs a projection with zero metadata; RecoveredInventoryProjection separately supplies opaqueWORD0. This is not the genuine full25 material required by TaiwanOwnedBagItemMaterial.

NativeWorldEntrySnapshotRepository and the full-entry offer source are separate raw2A/root/pose delivery custody. SharedTaiwanNativeWorldEntryOfferSource242..279 requires a supplied exact full Offer and real issuer before the writer; SharedTaiwanStoredWorldEntrySource.h requires full producer/resource/phase qualification. No bag1215/common-instance supplier follows from this entry custody. NativeEquipmentSnapshotRepository.h requires every50x24 byte including prefix1..3 plus DA15; it expressly rejects inference from additive3B/41. The genuine raw25 contract preserves count/slot/opaqueWORD/full20 and the material capability requires two aliases from one genuine declaration. Neither validation contract generates its source.

The earliest actionable missing predicate is before the first overlay installation, not a later replay or observation callback: a retained genuine original per-instance25/save/import declaration, qualified common definition binding, stable global identity and same-event acquisition entitlement for the actual saved owner. The current common stage_replace133..168 merely inserts supplied identity/acquisition at143 and aliases at164; syntax, uniqueness and CAS do not provide their origin. A real full50+DA witness is separately required. Once genuine suppliers exist, the existing same-DB joint replace_from_issuer is the actual atomic seam. There is no justified C++ increment now.

Next native cache question is actual writes U8560D..8560F+24I after known reset; full498DD0 copies only row+4 full20 and its opaqueWORD is not a direct occupied-prefix writer. Existing client copy/formatters cannot supply an original server grant or common acquisition identity. Full native5D remains a separate movement authority. These are scoped gaps in the selected current paths, not a claim of global absence or impossibility.

Custody: source-references.json gives exact full-file HEAD hashes and source cuts with byte offsets, inclusive line bounds and hashes. Full retained sources equal git show at the pinned HEAD. bounded-search-and-corrections.json preserves unsuccessful readonly path attempts and scope; no product target was executed. The initial range assertion and every partial member are retained in failure-initial; the exclusive successor corrects only the importer cut end148 and custody wording. supplier-gap.json retains the precise typed gap. This task contributes zero route/native acceptance/grant credit. No prior seal is modified.
'''
(OUT / 'REPORT.md').write_bytes(report.encode('utf-8'))

for ref in refs:
    assert (ROOT / ref['path']).read_bytes() == source_bytes[ref['path']], ref['path']
members = []
for path in sorted(OUT.rglob('*')):
    if path.is_file():
        raw = path.read_bytes()
        members.append({'path': path.relative_to(OUT).as_posix(), 'bytes': len(raw), 'sha256': sha(raw)})
save_json('SEAL.json', {'head': HEAD, 'members': members, 'member_count': len(members),
    'member_bytes': sum(m['bytes'] for m in members), 'accounting': 'individual regular-file sizes, excludes this seal',
    'source_only': True, 'tracked_edits': 0, 'target_execution_count': 0})
seal = (OUT / 'SEAL.json').read_bytes()
for m in members:
    raw = (OUT / m['path']).read_bytes()
    assert len(raw) == m['bytes'] and sha(raw) == m['sha256']
print(json.dumps({'member_count': len(members), 'member_bytes': sum(m['bytes'] for m in members),
    'seal_bytes': len(seal), 'seal_sha256': sha(seal), 'head': HEAD}))
