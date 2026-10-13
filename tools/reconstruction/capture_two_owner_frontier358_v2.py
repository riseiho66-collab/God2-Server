from pathlib import Path
import hashlib
import json
import subprocess

S = Path('C:/Users/risei/Desktop/God2/God2-Server')
O = Path(__file__).resolve().parent
A = O.parent
HEAD = '81566a8a7efb75e7ea768bb5f767e1e5f1ad9324'

def sha(b):
    return hashlib.sha256(b).hexdigest()

def put(rel, b):
    p = O / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('xb') as f:
        f.write(b)

def jout(rel, v):
    put(rel, (json.dumps(v, indent=2, ensure_ascii=False) + '\n').encode())

assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=S).decode().strip() == HEAD
prior_results = []
for name, pin, count, total in [
    ('round357-genuine-donor-material-source', 'c61a42e00074cc6033562455195cea4357028731e3aa4614a925768d7ccf482a', 52, 1141761),
    ('round357-party-callback-independent-source-review', 'b71176941db5b8a405787865451797d2d6d5a1cd4628ddbea6dd6c7bc8bda5be', 56, 3849652),
]:
    p = A / name
    b = (p / 'SEAL.json').read_bytes()
    assert sha(b) == pin
    seal = json.loads(b)
    assert seal['member_count'] == len(seal['members']) == count
    assert seal['member_bytes'] == sum(m['bytes'] for m in seal['members']) == total
    for m in seal['members']:
        raw = (p / m['path']).read_bytes()
        assert len(raw) == m['bytes'] and sha(raw) == m['sha256']
    put('upstream/' + name + '-SEAL.json', b)
    prior_results.append(dict(root=p.as_posix(), seal_sha256=pin, member_count=count,
                             member_bytes=total, members=seal['members'], verified_in_place=True))
jout('upstream-individual-verification.json', prior_results)

paths = [
    'AGENTS.md', 'docs/GOAL_ACCEPTANCE.md', 'src/core/Application.cpp',
    'src/db/OwnedInventoryRepository.h', 'src/db/SqliteOwnedInventoryRepository.h',
    'src/db/SqliteOwnedInventoryRepository.cpp', 'src/db/NativeEquipmentSnapshotRepository.h',
    'src/db/SqliteNativeEquipmentSnapshotRepository.h', 'src/db/SqliteNativeEquipmentSnapshotRepository.cpp',
    'src/db/SqliteOwnedEquipmentTransaction.h', 'src/db/SqliteOwnedEquipmentTransaction.cpp',
    'src/db/SqliteOwnedInstanceTradeRepository.h', 'src/db/SqliteOwnedInstanceTradeRepository.cpp',
    'src/handlers/OwnedInstanceTradeService.h', 'src/handlers/OwnedInstanceTradeService.cpp',
    'src/db/SqliteDatabase.cpp', 'src/db/SqliteSupport.h',
    'src/game/TaiwanOwnedBagItemMaterial.h', 'src/game/SharedTaiwanOwnedBagMoveSource.cpp',
    'src/game/SharedTaiwanOwnedItemSelectionSource.h',
    'src/protocol/RecoveredTrade.h', 'src/protocol/RecoveredInventoryProjection.h',
    'src/db/NativeItemDefinitionObservation.h',
]
assert len(paths) == len(set(paths)) == 23
wholes, refs = {}, []
for rel in sorted(paths):
    b = subprocess.check_output(['git', 'show', HEAD + ':' + rel], cwd=S)
    retained = 'published/' + rel
    put(retained, b)
    live = (S / rel).read_bytes()
    wholes[rel] = b
    refs.append(dict(actual_path=(S / rel).as_posix(), retained=retained, bytes=len(b), sha256=sha(b),
        source_head=HEAD, source_state='immutable published HEAD source; no target execution',
        working_at_capture_bytes=len(live), working_at_capture_sha256=sha(live), working_equals_published=live == b))
jout('source-references.json', refs)
specs = [
    ('src/core/Application.cpp', 1409, 1417, 'actual legacy trade peer/readiness supplier; partial lambda'),
    ('src/core/Application.cpp', 1449, 1505, 'actual CUSTOM0069 construction and ordinary sender; containing whole retained'),
    ('src/core/Application.cpp', 4012, 4033, 'actual hosted trade branch and result delivery; partial handler'),
    ('src/core/Application.cpp', 7591, 7605, 'actual C24 common/native consumer requires existing material; partial host'),
    ('src/handlers/OwnedInstanceTradeService.cpp', 28, 38, 'complete lease/current helpers'),
    ('src/handlers/OwnedInstanceTradeService.cpp', 44, 62, 'complete legacy metadata/project helpers'),
    ('src/handlers/OwnedInstanceTradeService.cpp', 96, 121, 'actual offer and both-confirm commit seam; partial handle'),
    ('src/db/SqliteOwnedInstanceTradeRepository.cpp', 183, 246, 'complete existing simultaneous two-owner plan'),
    ('src/db/SqliteOwnedInstanceTradeRepository.cpp', 251, 308, 'complete existing actual transaction commit'),
    ('src/db/SqliteOwnedInventoryRepository.cpp', 120, 168, 'complete common validate/stage; incoming receiver identity cannot be reminted'),
    ('src/db/SqliteOwnedInventoryRepository.cpp', 285, 315, 'selected registry/cell/alias DDL literals; no SQL executed'),
    ('src/db/SqliteOwnedEquipmentTransaction.cpp', 35, 93, 'complete existing one-owner joint replace source'),
    ('src/db/SqliteOwnedEquipmentTransaction.cpp', 192, 231, 'complete joint observation source; durable read not issuer'),
    ('src/game/TaiwanOwnedBagItemMaterial.h', 8, 40, 'complete full25 declaration validation; syntax not provenance authentication'),
    ('src/game/SharedTaiwanOwnedBagMoveSource.cpp', 38, 121, 'selected existing same-owner custom full-material plan; not cross-owner rule'),
    ('src/protocol/RecoveredInventoryProjection.h', 10, 34, 'complete legacy projection retains prefix but uses opaque WORD0'),
    ('src/db/SqliteDatabase.cpp', 213, 225, 'borrowed common/native writer accessors; no population'),
    ('src/db/SqliteSupport.h', 84, 94, 'complete BEGIN IMMEDIATE/rollback/COMMIT source'),
]
cuts = []
for i, (rel, lo, hi, meaning) in enumerate(specs):
    lines = wholes[rel].splitlines(keepends=True)
    assert 1 <= lo <= hi <= len(lines), (rel, lo, hi, len(lines))
    b = b''.join(lines[lo - 1:hi])
    retained = 'cuts/%02d-%s-L%d-L%d.txt' % (i, Path(rel).name, lo, hi)
    put(retained, b)
    cuts.append(dict(actual_path=(S / rel).as_posix(), retained=retained, bytes=len(b), sha256=sha(b),
                     first_line=lo, last_line=hi, boundary=meaning, source_head=HEAD))
jout('source-cuts.json', cuts)
jout('typed-frontier.json', dict(
    verdict='Conditional storage design possible; source-qualified actual route integration blocked; no implementation authorized',
    existing_route='Actual Application native trade branch -> OwnedInstanceTradeService -> both2C -> SqliteOwnedInstanceTradeRepository::commit',
    existing_design='CUSTOM-0069 legacy custody; CUSTOM-0092 common coordination; full25 retention CUSTOM-0094 remains separate',
    missing_preconditions=[
        'Authentic same-event definition/acquisition/full25 common donor binding and two actual Session delivery receipts, not shape or source-label inference',
        'Genuine complete per-owner after1215 policy/source compatible with actual consumer/helper behavior; legacy20/defaultopaque projection is insufficient',
    ],
    source_action='Bind real pre-existing authoritative donor material and complete before populations at the actual both-confirm context; only then introduce one outer sameDB settlement participant',
    rejects=['new grant/mint/remint', 'partial stack/split/merge', 'PET or other-client aliases without qualified rules',
             'two independent owner commits', 'caller callback substitutes for issuer', 'postcommit observation minted as operation receipt',
             'fresh50/1215 inferred from replay', 'new unhosted factory'],
    authority_credit=0, native_route_credit=0, execution=False))

report = '''# Round358 actual two-owner common material settlement frontier

READONLY source audit at immutable published HEAD81566a8a7efb75e7ea768bb5f767e1e5f1ad9324. Twenty-three complete current source files and eighteen exact cuts retain the finite hosted trade/common-writer participants. Working digests are separate; future party edits to Application do not rewrite this immutable baseline. A35752/1141761 and I35756/3849652 individually verified unchanged. No SQL/API/native/parser/codec/runtime/build/test was executed; no tracked source was changed and no unused coordinator/factory was added.

## Actual route and usable transaction participant

Application.cpp1409..1416 supplies real trade peers from weak held Sessions, actual movement current_location and legacy owned_bag_projected readiness. Lines1459..1493 construct the hosted default-off CUSTOM0069 service against the actual Database's legacy instance repository. Lines4012..4033 route native trade requests and submit actual result deliveries. Service96..117 validates offers against captured legacy metadata and both2C; its context owns both old legacy snapshots and its real Repository::Plan. Repository183..246 simultaneously removes both sides' offers before explicit destination selection, retains complete opaque20 overlays and records each source/destination/quantity in transfers. This is a genuine existing two-owner participant and settlement, not a common inventory acquisition issuer.

Repository251..308 owns one IMMEDIATE transaction over changed legacy scalar/overlay rows, optional PET scope, wallets and unique CUSTOM0069 settlement receipt. prepare(next) runs BEFORE BEGIN and prebuilds both original service replies; final check runs inside the actual transaction after staged reads. Existing observer/callback behavior is therefore not automatically a pure common coordinator's source contract. A new common integration cannot call this public commit under another BEGIN or call it once per owner. The actual participant would need a private staged implementation under one lexical outer coordinator, while preserving the existing public legacy adapter and original plan/reply recipe. Callback exceptions before COMMIT must unwind/rollback every participant; after a successful durable COMMIT there is no SQL retry, rollback, postcommit mintage or second settlement.

## Permanent identity permits transfer, but current one-owner API does not

OwnedInventoryRepository stores stable id/definition_key/stackable/acquisition pair independently of location. SqliteOwnedInventoryRepository120..168 treats an ID missing from that ONE owner's expected population as a mint: lines139..145 INSERT its permanent global registry row. Thus donor deletion followed by receiver replace fails or remints and is not a transfer. DDL285..315 has globally unique cells.instance_id, permanent unique acquisition pair and aliases FK to the located instance. A legitimate two-owner transfer must retain every existing registry row unchanged, detach the affected aliases/cells on BOTH owners before reattachment, and reinsert only the same existing IDs at actual planned destinations in the same transaction. It must never invoke the one-owner mint loop for incoming IDs. Full before/after union identity conservation includes definition/acquisition/stackability, all untouched cells, all aliases and positive nonwrapping revisions. An explicit empty location is capacity; missing cells are not.

The current SqliteOwnedEquipmentTransaction35..93 is ONE owner's full inventory/native witness coordinator. Its actual sameconnection/account/character identities, private writer guards, full roots/pose/no-battle checks, exact staged readback, pure issuer fence and preCOMMIT immutable receipts are reusable requirements, not an existing two-owner method. observe_before192..217 is an owned consistent read of one existing complete tuple; observe_committed219..231 is explicitly CUSTOM0112 durable read, not operation or acquisition authority. Two separately observed tuples are not a simultaneous two-owner expected readset.

## Conditional concrete narrow design, not implemented authority

After the two missing source preconditions below are actually supplied, a bounded candidate can consume complete EXISTING old material for two distinct owners. Limit the first variant to whole singleton ordinary slots0..29, no partial stack/split/merge, no PET or unqualified second-client aliases. Each source item must have the real stable registry identity, original definition/acquisition binding, its genuine same-declaration item20/full25 aliases, and an already-qualified complete1215 witness under the exact native149c root/pose/actor. Both genuine actual private Session initialization/delivery receipts must remain ready/current throughout actual consent/both-confirm context; original current trade_peer's scalar projected flag alone is insufficient. Require exact legacy overlay20/key/count to match the bound common instance and the Plan transfers. Full25 shape validation alone never authenticates this binding or its source labels.

One lexical same-DB BEGIN IMMEDIATE must own both common inventory populations, both complete native1215 witnesses, legacy before/after overlays/scalars, both wallet changes and the existing unique trade settlement receipt. Before BEGIN, hold exact strong owners, complete old populations and preallocated immutable output/receipt material. Inside the transaction re-read both actual roots/pose/no-battle, full populations, settlement absence and exact plan. The actual source/rule check must be pure in-memory/private-receipt checking: no callback SQL reads/writes, sends, yields, event pumping, transaction changes or reader reentry. Use operation guards and fixed transaction/autocommit/write-count boundaries around all supplier/observer-sensitive segments, plus final complete exact readback of all participants and protected rows before COMMIT. Stage both-owner common relocation without touching permanent identity/acquisition rows; stage both complete native next witnesses and legacy plan with the actual same event. Allocate actual immutable two-owner operation receipt and all reply storage before the only COMMIT; return actual private committed values only after that COMMIT. Ordinary delivery failure afterwards retires actual held owners; it never retries the durable transfer. This is a storage/hosting plan, not a new recovered transfer rule.

Native witnesses remain per-owner root/pose/actor caches; an item's original acquisition travels unchanged while the OWNER's full1215 is not itself transferred as an item. A native row's prefix1..3 and inactive metadata are local existing bytes, not an item prefix that can be copied to a new owner. Any derived relocation/projection must have a separately qualified exact policy. Same-owner CUSTOM0094 retention is not original cross-owner eligibility or a universal native after-state supplier.

## Exact two missing preconditions and next source action

1. Authentic same-event common definition/acquisition/full25 donor binding plus BOTH actual Session delivery receipts. Current common definition_key is an opaque positive common ID; native historical396 observation does not bind it. A357's actual diagnostic writers are explicitly synthetic; neither a genuine-looking provenance string nor importing/reobserving their persisted20 establishes acquisition or an original full25. Existing normal-entry C24 host Application7591..7605 says both schemas/material must already exist and consumes that material; it does not supply trade's two-owner source. The nearest concrete action is to locate and retain the real producer/export that authored the donor registry+acquisition+paired aliases and two owner-bank delivery event BEFORE either common mint or this both-confirm callsite. Source data cannot be filled by the client2A selector/key/quantity, random settlement receipt, historical metadata or callback argument.

2. A genuine complete per-owner AFTER1215 policy source compatible with actual3B/41/helper effects. OwnedInstanceTradeService44..62 copies legacy overlay20 but falls back to key+zeros; RecoveredInventoryProjection29 always writes opaqueWORD0. Full25 material observe validates width/paired provenance but not source authenticity or helper compatibility. The legacy service projects30 slots, not complete50/cache/DA, so its reply cannot certify full1215. A concrete next trace is the original transfer result full25 issuer/helper compatibility and the actual native before/after row-cache writes for occupied and emptied destinations, including prefix1..3/inactive bytes and appearance. Until that source or an explicitly authorized qualified custom policy exists, no posttrade full1215 may be guessed from the legacy plan. Existing original metadata/DA/witness identity stays explicit and unchanged; no fresh-client/full50 restoration claim follows.

Within this finite selected source scope, storage feasibility is demonstrated and the integration seam is exact, but the two genuine inputs are not supplied by the hosted branch. No implementation is proposed now; no new source factory or acquisition/route completion credit is warranted. Both missing suppliers remain OPEN; this is not a global absence claim. Later358 party review is separate; no359 work starts here.
'''
put('REPORT.md', report.encode())
jout('capture-complete.json', dict(status='PASS', head=HEAD, whole_count=len(refs), cut_count=len(cuts),
    prior_member_count=108, prior_member_bytes=4991413, tracked_edits=False, product_execution=False,
    authority_credit=0, route_credit=0))
for ref in refs:
    assert (O / ref['retained']).read_bytes() == subprocess.check_output(
        ['git', 'show', HEAD + ':' + str(Path(ref['actual_path']).relative_to(S)).replace('\\', '/')], cwd=S)
members = []
for p in sorted(O.rglob('*')):
    if p.is_file() and p.name != 'SEAL.json':
        b = p.read_bytes()
        members.append(dict(path=p.relative_to(O).as_posix(), bytes=len(b), sha256=sha(b)))
total = sum(m['bytes'] for m in members)
assert isinstance(total, int)
jout('SEAL.json', dict(status='PASS', member_count=len(members), member_bytes=total, members=members))
for m in members:
    b = (O / m['path']).read_bytes()
    assert len(b) == m['bytes'] and sha(b) == m['sha256']
sb = (O / 'SEAL.json').read_bytes()
hb = Path(__file__).read_bytes()
assert b'\r' not in hb
print(json.dumps(dict(status='PASS', member_count=len(members), member_bytes=total,
    seal_bytes=len(sb), seal_sha256=sha(sb), helper_bytes=len(hb), helper_sha256=sha(hb))))
