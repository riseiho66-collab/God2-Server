# Normal-entry movement and owned witness custody, round345

The default-off normal-entry whole-bag profile now uses one actual joint
transaction for ordinary movement and C24. A movement batch advances the
durable common position and the existing native equipment witness together,
instead of making the latter stale after legacy commit_position. No native
inventory bytes, acquisitions or inventory revision are regenerated.

## Concrete typed movement owner

RecoveredMovementService::move_committed_with_owned_material receives the real
Session, the actual SqliteOwnedEquipmentTransaction and copied/typed movement
requests. It accepts no arbitrary owner/current/commit callback. The existing
default move/move_committed APIs remain the legacy behavior; only the new
explicit source uses joint custody. Shared preparation retains the complete
sequence(slot+1)%40, per-axis step<=1 and existing navigation checks, ordered
displaced destinations and each original ACK byte recipe. The whole batch is
prepared before any storage write; it commits only final x/y once. Stationary
requests still advance the saved position revision, as the old path did.

The new owner captures the actual private normal initialization from the real
world-records TLS callback, its entry_written/current_on_game identity, exact
Session object/root/phase/battle epoch and the actor read from its actual2A.
CharacterSelected and InWorld are explicit ready phases, held unchanged for
the operation. Same repository, positive actual saved baseline, full existing
inventory/equipment/root/actor/position are required. Missing or stale material
does not fall back to the old position-only writer or a synthesized witness.

The opted operation rejects reentry and poisons nested legacy mutations or
removal of its active source. It retains an owned old Position snapshot and
re-finds the live entry across observers, rather than retaining a map iterator
through repository calls. Identity/state continuity is checked before writes.
The joint writer's Current executes only twice while position is still OLD;
its closure checks pure old active state and private Session receipt. It cannot
call current_location, load_position, callbacks, sends or SQL readers there.

SqliteOwnedEquipmentTransaction::move_position_from_current already provides
the actual single transaction over common position and native witness. The
source calls it once per full batch, including an unchanged final geometry.
Full current tuples/root/position/battle and bounded revisions are rechecked;
closed checks guard staged writes. All inventory identity/acquisition/aliases/
quantities/bytes/revision remain exact. Only common x/y/position revision and
native witness position/revision/provenance advance under CUSTOM-0095.
Immutable receipt allocation precedes its only COMMIT.

After COMMIT the old active.saved would make current_location falsely stale.
The source first checks the durable receipt, closed committed_current and
retained old active/identity, publishes the new saved/queue/geometry with
assignment, then checks fresh actual
current_location and committed_current before returning the prebuilt ACKs.
A failure after a durable commit throws; it never pretends to roll storage back,
retries the mutation or returns a success for a stale delivery.

## Actual Main connection and lifetime

The existing WholeBagMoveHost retains one strong same-Database transaction and
a pointer to the actual game-owned movement service. The C24 factory and the
dedicated RecoveredWorldService Movement callback share that transaction.
Movement returns the actual prebuilt ACK bytes unchanged; C24 retains full25
clear/material/final41 projection. A retired facade after either committed
source now throws rather than silently losing its result.

The final outer world_records wrapper sends the complete original batch with
any C24 or movement to that existing service before other typed callbacks or
observers. Existing service grammar admits movements with only ticks, or one
C24 with only ticks. C24+movement, duplicateC24, movement+chat/options/selection/
target/battle mixtures fail before either source writes. Idle-only and other
unrelated existing chat/control paths use the previous callback. This is a
bounded source admission; general mixed-run gameplay remains unresolved.

The same world.owned_whole_bag_moves.enabled option remains false by default.
Config load and programmatic Main share the validator. Separate legacy transfer,
door/scene/map/probe and diagnostic visibility/appearance experiment flags are
now excluded for this same-map source: their Tick handoffs and postmovement
publication need their own full material/lifecycle integration. Existing
inventory population/settlement exclusions and actual normal-entry/auth/dual/
navigation requirements remain. No configured option is enabled or schema run.

Listener/network captures retain only weak facades. Stop refuses new work before
drain; disconnect releases the C24 source before previous cleanup, and actual
movement removal invalidates the active opted operation. Revocation releases
service/binding before clearing movement pointer/transaction on the game owner,
before borrowed movement/Database destruction. Frozen default movement, chat,
authentication, native fonts/conversion, CN and fourWS source paths remain.

## Explicit scope and remaining work

This is material retention under CUSTOM-0095, not a fresh native afterstate
capture or recovered original server witness lifecycle. Full bank/root/actor
and pose must exist genuinely already; no grant, population/importer, defaults,
stale-position rebase, zero fill or alias invention is supplied. Initial raw50
cache and full25 acquisition remain open. Only current same-map movement is
covered; transfer and battle return lifecycle require separate source authority.

The inherited legacy ACK recipe is preserved. Full native5D authority, pending
queue/helper effects, all variants and original movement/game rules are not
newly qualified by an atomic storage connection. C24 still updates only two
rows; other48/freshclient state and native3B opaque effects remain unknown.

New Main joint-movement source branch1; opcode/format/parser/phase/full-route
credits0. TW156C2S/252S2C, world74=50partial/11control/13unconnected. CN156C2S,
280phase entries and253length entries remain separate scopes. Whole TW/game
denominator and completion percentage stay null. PHASE1 static source/hash/
custody only: no build/compiler/tests/runtime/native/API/CRT/VM/parser/codec/
gameDBSQL/migration/activation/deployment. Full TW-first/CN/fourWS/sharedcore/
common tables/common64/coin99999999999/qualifiedstack99/nativelevels/saves/
frozen/fonts/conversion goal remains active. Heavy evidence is external and
all original failure candidates and correction appendices are retained.
