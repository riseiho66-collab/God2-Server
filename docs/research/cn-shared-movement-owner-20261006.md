# CN adjacent movement to common stored position

Static source integration only. No build, Lua execution, tests, native/server
execution, production DB access or deployment. TW movement, saved accounts,
chat/IME and font/conversion behavior are unchanged.

## Imported native preparation

CnMovement, CnMapPassability, CnMovementRules and movement_rules.lua are imported
from the paused CN source using hashed raw snapshots. Only C++ include paths
change; Lua bytes are retained as scripts/cn/native_movement.lua. The source
covers ordinary adjacent coordinate direction00539150 and the nonzero raw-cell
neighbor filter00486B80. Passability snapshots preserve mode0 initialized63x63
window origins/chunks/ordered objects and mode2 selected mask composition.
Cell2 remains distinct. These recovered client predicates are not recovered
original server permissions, speed rules or complete path search.

C2S2E is a complete7-byte record: two LE16 destinations, ring write index<40,
and an uninitialized native stack byte. That byte is never a direction/flag,
must not be required zero, and is excluded from Lua/authoritative state.
S2C5D's complete2-byte consumer stores its byte for diagnostics and pops the
pending queue independently of its value. Native reset leaves an initial queue
entry(count1/write1); request index and ack byte cannot be equated automatically.
Initial/reset/duplicate/out-of-order contracts remain open.

## Actual common mutation path

SharedMovement binds the actual current committed world ticket, independently
verified account, offered common character ID and active SharedWorldPresence
lease. It reads the actual RecoveredCharacterRepository position, then requires
an actual WorldOwner scene snapshot with matching map keys, nonzero owner
revision, native mode0 or2 grid and actor direction. Missing assets/lifecycle
cannot be replaced by empty grids or an unrelated TW navigation file.

Native Lua prepares an adjacent step and raw destination cell. The mandatory
WorldOwner.authorize must establish actual permission, timing, battle/transfer
state and pending sequence and supply the complete native5D. No default owner,
permit, guessed ring reset/index echo or fabricated response is provided.
Authorization failure performs no position write.

The connection/actor/scene is rechecked after owner callbacks. The common
SharedWorldPresence.commit_owned_step invokes the existing repository's
transactional commit_position with exact expected map/coordinates/revision,
retaining the current map key rather than accepting one from a packet. The
shared SQLite recovered_positions CAS remains the single persisted position;
there is no CN database import or version table split. The real world owner
must then apply actor/direction/window lifecycle and per-recipient TW/CN
visibility before this connection queues the supplied5D.

The later dispatcher forwards complete homogeneous2E runs; mixed aggregates
and other records remain its responsibility. All record formats are checked
before the first per-step transaction, but authorization/publication is per
step. If a later step/publication/output fails, the connection and lease close;
an already committed authorized position remains saved. Do not undo a move
that peers could have observed. Reentry recovery must use current saved state.

## Scope and remaining ownership

The required WorldOwner implementation, native asset/collision/window lifecycle,
timing/sequence/reset authority, full5D byte supplier, remote movement formats
and broadcast, map transitions/battle paths, actual Application routing and TW
enrollment in the same common presence remain open. References supplied to the
controller must live through its connection and run on the same game owner.
Common movement source is conditional/unhosted, not a playable mixed world.

Original CN movement/passability function C/ASM/PE spans, import receipt,
source snapshots and prior ledger are sealed in cn-shared-movement-owner-01.
This adds an actual common CAS mutation path without executing it. Complete
bidirectional routes added0; whole-game route/variant denominator and percentage
remain unknown. Previous goal turn is progress (account success/owned disconnect
source), and its historical binding-count correction remains preserved.
