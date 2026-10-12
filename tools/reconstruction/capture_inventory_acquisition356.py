from pathlib import Path
import hashlib
import json
import subprocess

S = Path('C:/Users/risei/Desktop/God2/God2-Server')
O = Path(__file__).resolve().parent
A = O.parent
HEAD = '6c2d3412e22316d1537323bc13e449f87ddfd03a'

def sha(b):
    return hashlib.sha256(b).hexdigest()

def put(rel, b):
    p = O / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('xb') as f:
        f.write(b)

def jout(rel, value):
    put(rel, (json.dumps(value, indent=2, ensure_ascii=False) + '\n').encode())

prior = A / 'round355-full-material-authority-source'
raw = (prior / 'SEAL.json').read_bytes()
assert sha(raw) == 'a7c2180670adf423fa946dc6e05cb32ca3a4be34a62ed21a0ff313610ede0805'
seal = json.loads(raw)
assert seal['member_count'] == len(seal['members']) == 59
assert seal['member_bytes'] == sum(m['bytes'] for m in seal['members']) == 1266463
for m in seal['members']:
    b = (prior / m['path']).read_bytes()
    assert len(b) == m['bytes'] and sha(b) == m['sha256']
put('prior355-SEAL.json', raw)
jout('prior355-individual-verification.json', dict(package=prior.as_posix(),
    seal_sha256=sha(raw), members=seal['members'], member_count=59, member_bytes=1266463,
    verified_in_place=True, prior_not_modified=True))
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=S).decode().strip() == HEAD
paths = [
    'src/core/Application.cpp', 'src/core/Config.h',
    'src/protocol/RecoveredTrade.h', 'src/protocol/RecoveredInventoryProjection.h',
    'src/handlers/OwnedInstanceTradeService.h', 'src/handlers/OwnedInstanceTradeService.cpp',
    'src/handlers/RecoveredTradeService.h',
    'src/db/SqliteOwnedInstanceTradeRepository.h', 'src/db/SqliteOwnedInstanceTradeRepository.cpp',
    'src/db/SqliteArmorSlotRepository.h', 'src/db/SqliteArmorSlotRepository.cpp',
    'src/db/OwnedInventoryRepository.h', 'src/db/SqliteOwnedInventoryRepository.h',
    'src/db/SqliteOwnedInventoryRepository.cpp', 'src/db/SqliteOwnedEquipmentTransaction.h',
    'src/db/SqliteOwnedEquipmentTransaction.cpp', 'src/db/NativeItemDefinitionObservation.h',
    'src/db/NativeEquipmentSnapshotRepository.h', 'src/game/TaiwanOwnedBagItemMaterial.h',
    'docs/research/native-owned-instance-trade-20261003.md',
]
refs = []
wholes = {}
for rel in sorted(paths):
    b = subprocess.check_output(['git', 'show', HEAD + ':' + rel], cwd=S)
    retained = 'published/' + rel
    put(retained, b)
    current = (S / rel).read_bytes()
    refs.append(dict(actual_path=(S / rel).as_posix(), retained=retained, bytes=len(b),
        sha256=sha(b), source_head=HEAD, source_state='immutable published git show, not relabeled concurrent working candidate',
        current_at_capture_bytes=len(current), current_at_capture_sha256=sha(current), current_equals_published=current == b))
    wholes[rel] = b
jout('source-references.json', refs)
cuts = []
for rel, spans in [
    ('src/core/Application.cpp', [(1403, 1415), (1446, 1491), (4004, 4028)]),
    ('src/protocol/RecoveredTrade.h', [(16, 58)]),
    ('src/protocol/RecoveredInventoryProjection.h', [(10, 36)]),
    ('src/handlers/OwnedInstanceTradeService.cpp', [(42, 62), (101, 123)]),
    ('src/db/SqliteOwnedInstanceTradeRepository.cpp', [(20, 25), (129, 151), (177, 245), (251, 308)]),
    ('src/db/SqliteOwnedInventoryRepository.cpp', [(120, 151), (169, 196)]),
    ('src/db/SqliteOwnedInventoryRepository.h', [(12, 63)]),
    ('src/game/TaiwanOwnedBagItemMaterial.h', [(9, 40)]),
    ('docs/research/native-owned-instance-trade-20261003.md', [(3, 39)])]:
    lines = wholes[rel].splitlines(keepends=True)
    for first, last in spans:
        assert 1 <= first <= last <= len(lines), (rel, first, last, len(lines))
        b = b''.join(lines[first-1:last])
        retained = 'cuts/' + Path(rel).stem + '-' + str(first) + '-' + str(last) + '.source'
        put(retained, b)
        cuts.append(dict(actual_path=(S / rel).as_posix(), source_head=HEAD, retained=retained,
            first_line=first, last_line=last, bytes=len(b), sha256=sha(b), whole_sha256=sha(wholes[rel])))
jout('cuts.json', cuts)
jout('selected-wire-and-mutation-seam.json', dict(
    route=dict(C2S=['29', '2A', '2B', '2C', '2D'], selected_acquisition_direction='2A offer then both 2C confirmations',
               issuer_variant='actual Main CUSTOM-0069 opt-in, accepted CUSTOM-0063 remains separate',
               native2A=dict(logical_bytes=7, item_WORD=[1, 2], source_slot_BYTE=3, quantity_BYTE=4, target_WORD=[5, 6],
                             opaque20_transmitted=False, full25_transmitted=False),
               phase='actual ready owned peer, projected legacy bag, same area/scene; serialized custom lease'),
    storage_seam=dict(plan='SqliteOwnedInstanceTradeRepository.cpp183..245',
        transaction='251..308; one real two-owner legacy settlement, complete before/after/offer receipt',
        transferred_material='legacy scalar + armor/weapon/gem opaque20 and optional beast custody; Plan from/source/to/destination/quantity',
        receipt_kind='server-generated unique settlement event receipt, not original acquisition receipt',
        original_acquisition_not_minted=True),
    source_limit=dict(origin_accepts=['NATIVE_CAPTURE_VERIFIED', 'CUSTOM_TEST_NOT_NATIVE'],
        original_full25_opaqueWORD_not_retained_by_projection=True,
        source_3B_reply_policy='RecoveredInventoryProjection uses literal opaqueWORD0, 41 absolute count, ordinary slots0..29',
        common_instance_definition_acquisition_binding_in_legacy_snapshot=False,
        full_native1215_cache_and_DA_in_legacy_snapshot=False),
    sequencing_gap=dict(single_owner_stage='SqliteOwnedInventoryRepository.cpp139..145 permanently INSERTs every ID absent from that owner before',
        one_owner_replace_cannot_transfer_existing_global_ID=True,
        two_call_or_postcommit_adapter_supported=False,
        required_future_boundary='after genuine donor legacy/common identity material is qualified; before any legacy/common writes, one real two-owner atomic transaction must move existing common IDs preserving original acquisition and update both full witnesses plus actual settlement receipt',
        currently_implementable_supplier=False)))
report = '''PASS: bounded round356 source frontier; no implementation authorized or claimed.

First the immutable prior355 material package59/1266463B was independently
verified member by member in place. Twenty whole sources below are immutable
published6c2d3412e22316d1537323bc13e449f87ddfd03a git-show bytes. Current
working-file hashes are recorded separately: concurrent party transport edits
must not relabel the old Application snapshot. Every selected cut retains exact
original line bytes and method/operation boundary labels; no product is executed.

Nearest actual route is hosted native trade, C2S2A followed by both2C confirmations.
RecoveredTrade Request carries only native itemWORD, sourceSlotBYTE, quantityBYTE,
targetWORD (logical7). Current native producer documentation names49E440->497290:
full bag24 is copied locally into self UI866E8, while the sent2A has no opaque20.
That local copy is not a server-owned incoming original full25 or grant. This is
current retained source documentation, not a new machine/runtime qualification.

Main1403..1415 supplies actual live ready owned peers with projected legacy bags;
1446..1491 constructs default-off CUSTOM0069 and4023 dispatches its actual handler.
Service validates current two-side saved before states and explicit whole/plain
admission. Both confirmations reach its repo.commit with prepared original reply
recipes. Repo183..245 carries exact legacy whole20/source provenance and explicit
from/source/to/destination/quantity. Repo251..308 owns one real two-owner legacy
transaction, CAS/readbacks and complete settlement receipt. This is a meaningful
same-event transfer seam, not an unhosted factory or scalar town increment.

It cannot presently issue the common tuple. Snapshot is ArmorSnapshot/wallet/
optional beast storage, not stable global common instance/definition/acquisition
identity or original full25/native1215. The origin predicate explicitly accepts
both NATIVE_CAPTURE_VERIFIED and CUSTOM_TEST_NOT_NATIVE; provenance text/hash
syntax does not select actual installed native material. No DB rows were read.
Metadata(saved) preserves qualified existing20 for whole overlays, but ordinary
plain metadata may be native key plus18 zero bytes. RecoveredInventoryProjection
builds3B with literal opaqueWORD0, clears first and ends41 absolute count; it
preserves client prefix1..3 rather than supplying it. These existing custom
transport recipes cannot reconstruct original full25/witness from offer data.
Historical396 native-key observations remain separate from common definition IDs.

New concrete sequencing boundary: the common single-owner replacement does not
support donor-to-recipient identity transfer. At stage_replace139..145, every ID
absent from that owner's before population is INSERTed into the permanent global
registry; identity/acquisition receipts remain globally unique after retirement.
Thus removing at donor then calling recipient replace would attempt forbidden
re-mint/resurrection, and two commits would split the actual settlement. A new
random settlement receipt cannot become the immutable original acquisition.

Actionable next source requirement is one genuine donor material binding BEFORE
the legacy settlement: associate its actual stored opaque20/provenance and full25
with already-owned stable common instance+definition+original acquisition and
the exact complete cache/DA witness, without derived IDs or fabricated prefix.
Only after that source is qualified can a single two-owner transaction preserve
that identity/acquisition, update both common populations/full native witnesses
and legacy settlement atomically while preparing original replies. The actual
commit251..308 is the boundary to connect, not an after-commit observation or
two-call adapter. Existing same-owner joint transactions are not that owner.

No concrete currently closed acquisition supplier was found in this selected
route scope; this is not global absence. No tracked changes, grants, seed formula,
factory, source rights, native fields or gameplay policy were added. CUSTOM0069/
0063/0092/0094 remain distinct. Zero method/format/full-route/native acceptance
credits; full goal remains active. No SQL/API/native/CRT/VM/parser/codec/compiler/
build/tests/runtime/import/migration/activation/deployment execution occurred.
'''
put('REPORT.md', report.encode())
jout('review-manifest.json', dict(status='PASS bounded source frontier', head=HEAD,
    whole_source_count=len(refs), exact_cut_count=len(cuts), prior355_members=59,
    prior355_bytes=1266463, selected_route='native trade2A/2C actual Main CUSTOM0069',
    actual_connected_delta_proposed=False, supplier_closed=False,
    original_acquisition_preserved_requirement=True, two_owner_atomic_seam_missing=True,
    no_global_absence=True, new_credits=0, target_execution=0, tracked_edits=0,
    helper='capture_inventory_acquisition356.py', successful_runs=1, helper_failures=[]))
for ref in refs:
    assert (O / ref['retained']).read_bytes() == subprocess.check_output(['git', 'show', HEAD + ':' + str(Path(ref['actual_path']).relative_to(S)).replace('\\', '/')], cwd=S)
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=S).decode().strip() == HEAD
members = []
for p in sorted(O.rglob('*')):
    if p.is_file():
        b = p.read_bytes()
        members.append(dict(path=p.relative_to(O).as_posix(), bytes=len(b), sha256=sha(b)))
jout('SEAL.json', dict(status='PASS bounded source frontier356', head=HEAD,
    member_count=len(members), member_bytes=sum(m['bytes'] for m in members), members=members))
final = json.loads((O / 'SEAL.json').read_bytes())
assert final['member_count'] == len(final['members'])
assert final['member_bytes'] == sum(m['bytes'] for m in final['members'])
for m in final['members']:
    b = (O / m['path']).read_bytes()
    assert len(b) == m['bytes'] and sha(b) == m['sha256']
hb = Path(__file__).read_bytes()
assert b'\r' not in hb
print(json.dumps(dict(status='PASS', member_count=final['member_count'], member_bytes=final['member_bytes'],
    seal_bytes=(O / 'SEAL.json').stat().st_size, seal_sha256=sha((O / 'SEAL.json').read_bytes()),
    helper_bytes=len(hb), helper_sha256=sha(hb))))
