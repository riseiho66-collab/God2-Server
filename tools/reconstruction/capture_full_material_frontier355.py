from pathlib import Path
import json,hashlib,subprocess
S=Path('C:/Users/risei/Desktop/God2/God2-Server');A=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261013')
O=A/'round355-full-material-authority-source';HEAD='b934e539e9d0cb279e2d6b58678afdb7b555dcf9'
P=A/'round354-tw-unconnected-authority-source'
sha=lambda b:hashlib.sha256(b).hexdigest()
def put(p,b):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f:f.write(b)
def js(p,v):put(p,(json.dumps(v,indent=2,ensure_ascii=False)+'\n').encode())
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=S).decode().strip()==HEAD
sp=P/'SEAL.json';raw=sp.read_bytes();assert sha(raw)=='0dc6b240971a4c41f3a2c6bada060408938d8acf5733626bff76d26303e74ca1'
prior=json.loads(raw);assert prior['member_count']==53 and prior['member_bytes']==1905110
seen=set();checked=[]
for r in prior['members']:
    p=P/r['path'];assert r['path'] not in seen and p.resolve().is_relative_to(P.resolve());seen.add(r['path'])
    b=p.read_bytes();assert len(b)==r['bytes'] and sha(b)==r['sha256'];checked.append(r)
assert len(seen)==53 and sum(r['bytes'] for r in checked)==1905110
put(O/'prior354.SEAL.json',raw)
js(O/'prior354-individual-verification.json',dict(root=P.as_posix(),seal_sha256=sha(raw),members=53,member_bytes=1905110,individual_members_verified=checked,prior_immutable=True))
paths=['src/core/Application.cpp','src/core/Config.h','src/core/SharedTaiwanNativeWorldHostPlan.h','src/core/SharedTaiwanNativeWorldHostPlan.cpp','src/db/SqliteDatabase.h','src/db/SqliteDatabase.cpp','src/db/OwnedInventoryRepository.h','src/db/SqliteOwnedInventoryRepository.h','src/db/SqliteOwnedInventoryRepository.cpp','src/db/NativeEquipmentSnapshotRepository.h','src/db/SqliteNativeEquipmentSnapshotRepository.h','src/db/SqliteNativeEquipmentSnapshotRepository.cpp','src/db/NativeWorldEntrySnapshotRepository.h','src/db/NativeItemDefinitionObservation.h','src/db/NativeMapItemCatalog.h','src/db/NativeMapItemCatalog.cpp','src/db/SqliteOwnedEquipmentTransaction.h','src/db/SqliteOwnedEquipmentTransaction.cpp','src/game/TaiwanOwnedBagItemMaterial.h','src/game/SharedTaiwanOwnedBagMoveSource.h','src/game/SharedTaiwanOwnedBagMoveSource.cpp','src/game/SharedTaiwanNativeMovementScene.h','src/game/SharedTaiwanNativeMovementScene.cpp','src/game/TaiwanNativeSceneResourceOwner.h','src/game/TaiwanNativeSceneResourceOwner.cpp','src/game/SharedTaiwanMovement.h','src/game/SharedTaiwanMovement.cpp','src/protocol/RecoveredNativeMovement.h','src/protocol/RecoveredMovement.h','src/handlers/RecoveredMovementService.h','src/handlers/RecoveredMovementService.cpp','src/handlers/OwnedTaiwanPkEntryPreparation.h','src/handlers/OwnedTaiwanPkRoomBackend.h','src/game/OwnedTaiwanPkAppearanceSource.h','tools/strike_lab/import_native_map_items.py']
refs=[];whole={}
for p in paths:
    b=subprocess.check_output(['git','show',HEAD+':'+p],cwd=S);dest=O/'published-source'/p;put(dest,b);whole[p]=b
    refs.append(dict(actual_path=(S/p).as_posix(),retained=dest.relative_to(O).as_posix(),bytes=len(b),sha256=sha(b),source_revision=HEAD,source_custody='immutable published HEAD; later root candidate excluded'))
js(O/'source-references.json',refs)
cuts=[('src/core/Application.cpp',7528,7585,'actual-already-hosted-normal-entry-material-custody'),('src/db/SqliteOwnedInventoryRepository.cpp',32,59,'owned-state-shape-not-definition-or-acquisition-authority'),('src/db/SqliteOwnedInventoryRepository.cpp',133,152,'actual-mint-before-cell-replacement'),('src/db/SqliteOwnedInventoryRepository.cpp',214,245,'historical-definition-observer-source'),('src/db/SqliteOwnedEquipmentTransaction.cpp',36,90,'actual-one-joint-replace-and-private-token'),('src/db/SqliteOwnedEquipmentTransaction.h',125,132,'consistent-read-token-not-original-issuer'),('src/game/SharedTaiwanOwnedBagMoveSource.cpp',249,281,'existing-normal-entry-full-before-and-real-commit'),('src/game/SharedTaiwanNativeMovementScene.h',70,87,'full5D-permit-mandatory-authority-contract'),('src/game/SharedTaiwanNativeMovementScene.cpp',224,240,'actual-full5D-authorization-consumer'),('src/game/TaiwanNativeSceneResourceOwner.cpp',156,180,'actual-forwarding-only-authority-adapter'),('src/handlers/RecoveredMovementService.cpp',522,540,'inherited-narrow-normal-movement-ACK-policy'),('src/db/SqliteDatabase.cpp',427,524,'complete-existing-PK-backend-constructor'),('src/handlers/OwnedTaiwanPkEntryPreparation.h',56,155,'actual-PK-pair-and-complete-material-read'),('src/game/OwnedTaiwanPkAppearanceSource.h',151,202,'actual-PK-full-entry-bank-actor-predicates'),('tools/strike_lab/import_native_map_items.py',74,87,'definition-display-import-not-instance-grant')]
cutrows=[]
for p,lo,hi,name in cuts:
    lines=whole[p].splitlines(keepends=True);assert 1<=lo<=hi<=len(lines),(p,len(lines),hi)
    b=b''.join(lines[lo-1:hi]);dest=O/'cuts'/(name+'.source');put(dest,b)
    cutrows.append(dict(source_path=p,first_line=lo,last_line=hi,retained=dest.relative_to(O).as_posix(),bytes=len(b),sha256=sha(b),scope='selected exact line cut; complete enclosing source retained'))
js(O/'exact-line-cuts.json',cutrows)

js(O/'typed-earliest-owner-gaps.json',dict(head=HEAD,host_only_connection_supported=False,already_hosted=dict(policy=['CUSTOM-0094','CUSTOM-0095'],actual_source='Application.cpp7528..7585',normal_C24='create_for_normal_entry_with_item_material_and_receipt',movement='move_committed_with_owned_material_and_receipt',same_connection=True,private_session_current_and_actual_mutation_receipt=True,no_initial_bank_created=True),gaps=[dict(priority=1,domain='initial common-owned material acquisition',earliest_boundary='SqliteOwnedInventoryRepository.cpp143 mint; required true issuer before calling joint replace',required_material=['same real acquisition event and authoritative entitlement','stable common definition binding independent of native WORD','globally unique stable instance ID and immutable acquisition receipt','genuine original full25 with countBYTE/slotBYTE/opaqueWORD/full20','two same-origin aliases matching entire full20 and full25 plus revisions','actual full50x24 cache including each unknown prefix1..3 and complete DA15','actual owner root/pose/actor bound to exact normal entry and current saved state'],qualified_existing=['real common root/account and positive durable pose','typed same-DB full stored observations/CAS/private actual-commit transport','historical396 native definition observations with exact source key/provenance'],not_qualified=['catalog observation to common definition mapping','display import to ownership/instance/acquisition','full25 shape or source digest syntax to actual issuer','50 zero rows or3B/41 replay to complete native1215 witness'],next_source='A real OriginalServer/native saved acquisition or already-saved common issuer declaration with complete event tuple before mint; actual client prefix8560D..F producer remains independent OPEN',implementation_now=False),dict(priority=2,domain='complete original S5D movement issuer',earliest_boundary='TaiwanNativeSceneResourceOwner::Input.authority / Scene::Authority::authorize(candidate)',required_material=['full original ACKBYTE','real pre-CAS timing/pending/sequence/reset/collision/permission ticket','actual same-owner publish after one durable common-position commit'],qualified_existing=['read_ack preserves any complete two-byte5D logical record','scene geometry/current/root/pose/actor and explicit supplied resource lifecycle','ResourceOwner adapter keeps supplied fullBYTE and callbacks unchanged'],not_qualified=['consumer byte store/pending pop to server permission/value formula','narrow normal ACKsequence echo to full native authority','type-valid permit to original issuer'],next_source='Original server C2S2E->S5D issuer with queue/pending/reset/timing and owner state, not another Authority adapter',implementation_now=False),dict(priority=3,domain='existing PK69/35 backend install',earliest_boundary='SqliteDatabase.cpp427..449 explicit constructor sources plus EntryPreparation117..123',required_material=['real common presence/visibility pair and both actual Sessions/privateWrittenINITs','same-root complete joint bank+DA+native2A appearance','selected trusted seed/basic coefficients/order/retry policy','genuine complete terminal WORLD return actor/resources/selection owner'],qualified_existing=['concrete AsyncRoomAuthority and paired storage/transport/scheduler','CUSTOM0106 adopts actual saved role/resource/auxiliary under explicit policy'],not_qualified=['native definition flags to actual battle profile','normal INIT alone to fake common lease/full appearance','default seed/coefficient or preparation-only return to playable complete route'],implementation_now=False)],new_full_routes=0,new_native_acceptance=0,whole_game_denominator=None))
policy_path='docs/custom-designs.json';policy=subprocess.check_output(['git','show',HEAD+':'+policy_path],cwd=S);assert len(json.loads(policy)['designs'])==135
js(O/'policy-custody.json',dict(actual_path=(S/policy_path).as_posix(),source_revision=HEAD,bytes=len(policy),sha256=sha(policy),custom_designs=135,unchanged_policy=True,no_new_CUSTOM_rule=True,default_config_retained=True,whole_native_movement_not_credited_from_inherited_normal_policy=True))
put(O/'REPORT.md',b'''# Round355 initial material and native5D authoritative supplier frontier

Published-source scope: b934e539e9d0cb279e2d6b58678afdb7b555dcf9. This finite
audit retains immutable whole source/cuts, not a later root permission candidate.
Relevant354 authority53/1905110 seal and every member are verified in place.
No tracked edits or product/API/SQL/native/parser/codec/compiler/build/tests/
runtime/import/deploy execution occurred. No unused factory is proposed.

Nearest concrete owner is the genuine acquisition issuer BEFORE line143 mint
in SqliteOwnedInventoryRepository, CUSTOM0092 (143 is a line, not CUSTOM0143).
OwnedInventoryInstance separates common definition/instance/immutable acquisition
from native aliases. valid32..59 checks domain, provenance syntax, ordering and
quantity, not external acquisition rights or definition binding. stage_replace
permanently registers new IDs and receipt uniqueness, so a fabricated tuple is
not repaired by a later correct CAS. Joint replace36..90 protects full before/
next/root/pose and returns a private actual token only after one COMMIT; it does
not generate initial entitlement, bytes or IDs. observe_committed explicitly
labels a consistent read as neither a grant nor proof of original writer call.

Main7528..7585 ALREADY installs real normal-entry full-material C24 and joint
movement custody with actual private Session/current checks, same accounts/
characters/connection, and original response/actual mutation token. The missing
step is not another hosting wrapper. Existing complete already-installed tuples
can enter this policy if qualified, but source-only PHASE1 cannot claim that
actual saves contain such material. No bank existence/read or production SQL
was performed. Initial common population needs a true same-event definition
binding+stable instance/acquisition and original full25 before that mint.

TaiwanOwnedBagItemMaterial requires two aliases from one genuine source: exact
full20 and full25 count/slot/opaqueWORD/full20. Positive source count is retained
independently; it is not manufactured from common quantity. Its explicit
CUSTOM0094 positive subset and relocation policy are not original eligibility.
NativeEquipmentSnapshot1215 is full50x24 cache INCLUDING unknown prefix1..3 plus
DA15, separate from incoming wire. 3B/41 or outward UI-save evidence does not
construct this witness or a fresh initial cache. Existing C24 consumes/moves
already-owned instances; it does not create an acquisition or default bank.

NativeItemDefinitionObservation retains historical70a4/75c3/parser149c full396
TWP/WPN/EQU/TEQ. token0 source key differs from metadataDWORD0/token5. These
are not common IDs, per-player instance20, original25 or acquisition. MapItem
Catalog/importer is SOURCE_DISPLAY_ONLY for two pinned rows; source flags are
not packed instance metadata or grants. Genuine current bank qualification
remains separate. PFD flags or formatter/count clamps cannot fill authority.

Independent original native5D owner is required at ResourceOwner Input.authority
and Scene::Authority::authorize. The actual adapter156..180 retains/forwards
that supplied Permit; no value formula is derived there. Scene accepts its
full two-byte logical5D, actual pre-CAS timing/sequence/reset/pending/permission
ticket and post-CAS authoritative publication. read_ack preserves the fullBYTE
but grants no semantics. The known native consumer stores byte and pops pending;
it cannot issue server authority. Existing normal movement522..540 echoes its
narrow request sequence under inherited custom validation; CUSTOM0095 custody
does not transform it into native5D. Next source is OriginalServer2E->5D state/
timing/pending/reset/permission/commit issuance, not an echo or another adapter.

PK is downstream of the same genuine full materials: concrete backend427..524
requires common presence/visibility, actual both-Session/private Written INIT
and peer resolvers, explicit trusted seed/four basic coefficients/order/retry.
EntryPreparation117..123 and Appearance151..202 require full matching joint
bank, DA, native2A, actor, pose and lease. Its actual stored-stat CUSTOM0106
policy is not an original formula. Full terminal return actor/resources/
selection remains a real supplier dependency. No seed/formula/lease defaults.

There is no supported host-only increment in this selected scope. The actionable
first missing predicate is a real same-event acquisition tuple before mint;
separate native5D requires its genuine fullBYTE ticket owner. Once an authentic
tuple is supplied, the existing actual Main routes already provide mutation/
CAS/receipt transport seams. A new sourcefactory transferring the same missing
evidence to a caller would add no authoritative route. CUSTOM fallback must be
separately authorized/labeled and cannot pretend the native bytes/rights exist.
All route/native acceptance credits0; whole-game denominator remains unknown.
''')
js(O/'manifest.json',dict(head=HEAD,whole_sources=len(paths),exact_selected_cuts=len(cuts),source_revision_explicit=True,prior354_members=53,prior354_bytes=1905110,proposal='No qualified host-only implementation; exact earliest acquisition owner and independent full5D owner required',tracked_edits=0,implementation_proposed=False,whole_route_credits=0,helper_failures=[],successful_helper='capture_full_material_frontier355.py',successful_runs=1,execution='static source/hash/git reads only'))
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=S).decode().strip()==HEAD
members=[]
for p in sorted(O.rglob('*')):
    if p.is_file():
        b=p.read_bytes();members.append(dict(path=p.relative_to(O).as_posix(),bytes=len(b),sha256=sha(b)))
js(O/'SEAL.json',dict(head=HEAD,member_count=len(members),member_bytes=sum(r['bytes'] for r in members),members=members))
for r in json.loads((O/'SEAL.json').read_bytes())['members']:
    b=(O/r['path']).read_bytes();assert len(b)==r['bytes'] and sha(b)==r['sha256']
helper=(O/'capture_full_material_frontier355.py').read_bytes();assert b'\r' not in helper
print(json.dumps(dict(head=HEAD,members=len(members),bytes=sum(r['bytes'] for r in members),seal_bytes=(O/'SEAL.json').stat().st_size,seal_sha256=sha((O/'SEAL.json').read_bytes()),helper_bytes=len(helper),helper_sha256=sha(helper))))
