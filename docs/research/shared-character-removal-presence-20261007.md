# Common prepared/active character exclusion in native19 removal

PHASE1 source integration, not native rules or acceptance. No builds, tests,
native/server execution, database access, migration or deployment. Previous
catalog72 exception research is retained. Native levels/fields/curves remain
unchanged. Shared gameplay storage remains common, no new regional tables.

## Concrete source gap

`SharedWorldPresence::prepare` already reserves a common character and actor
before readiness; `activate` is later. Its `current`/`ready` views read common
root ownership. The removal transaction stages that root absent before its
BeforeCommit callback. Using current/ready to decide whether a live owner exists
would therefore hide precisely the reservation that should veto removal.
`RecoveredMovementService::character_active` also already includes prepared
legacy leases, and legacy `World::character_online` observes its actual players.
None of these sources was mandatory in the conditional19 operation's SQL gate.

## Additive source connection

`SharedWorldPresence::character_reserved(character)` is a raw registry read on
the same game owner. Every existing entry counts, before/after readiness and
even when its saved root no longer qualifies current(). It does not read SQL,
evict an actor, advance a generation or clean up an unqualified/stale entry.
Only the existing exact lease release removes that reservation.

`SharedCharacterRemovalPresence` binds this actual common registry, actual
legacy World and either the actual legacy movement service or an explicit
disabled host-configuration tag. No optional null/default registry substitutes
for those sources. Common registry and active legacy movement must use the same
repository. The added legacy getter is read-only object identity; its movement,
placement, readiness, transfer and cleanup behavior are unchanged. Reference
lifetimes belong to the actual host, and all calls stay on its serial game owner.
Activation of a formerly disabled legacy service requires rebinding before use.

The observer's unreserved(account,character) requires valid IDs, no common raw
reservation, no legacy world player and no actual legacy prepared/active movement
entry. This is saved-state integrity policy, not a recovered official deletion
permission, proof that all processes are idle, or an invented native reply.

The conditional19 source now requires that bound observer and matching common
repository. Its actual rule/CAS/replay Decision remains mandatory. BeforeErase
and BeforeCommit check actual occupancy both before and after the observing
Decision callback through the mandatory common `SharedCharacterRemoval::commit`
gate, so future TW/CN callers cannot omit it. BeforeCommit never derives absence
from a deleted root row.
After COMMIT/TW-CN offer invalidation, successful02 queue checks and whole queue
completion recheck occupancy alongside actual operation/ticket/deleted-ID state.
Nonzero source02 still performs no removal and can report an actual busy failure;
it does not need occupancy absence. No synthesized error code is added.

`SharedWorldPreparation::presence_registry()` exposes the exact registry retained
by that controller without changing preparation behavior. A complete deletion
source supplied by World composition must have the same registry as its declared
actual preparation source. The provider must use this getter and the same registry
as actual TW lifecycle; configuring unrelated registries cannot establish global
cross-version exclusion. The comparison rejects mismatched declared sources,
and does not introspect an arbitrary Selected callback or claim current hosting.

## Boundaries retained

Existing Application's TW reauthentication/native profile matching and its
CUSTOM-0083/0084 effective guild ownership policy are not imported as CN native
rules. Actual guild/online permission/replay receipts and complete native02/03
issuers remain open. Presence absence alone does not authorize deletion; shared
SQL/CAS still requires actual Decision and its current operation checks.
Durable crash/replay recovery and cross-process occupancy/invalidation remain
open. No guild retirement/member deletion semantics, save/history policy or
schema is invented. Existing SQL writer, World, Movement implementation and
Application source bodies stay byte-identical.
The frozen TW Application deletion body is not automatically routed through the
new common coordinator. Its explicit future adapter/hosting connection and
exclusion of CN reservations remain a separate gap; this round cannot claim
global TW-initiated deletion safety merely because the CN source uses the guard.

## Accounting

One concrete common occupancy observer added and one existing conditional19
transaction/queue chain strengthened. Three read-only binding/reservation
views added. No new opcode, owner chain, phase/source binding, complete
bidirectional route, formal hosting or acceptance. Counts stay CN71/53 and TW8/8
source associations, with31 conditional partial owner chains. Whole-game
phase/state/variant/indirect/deferred route denominator/percent remain null.
