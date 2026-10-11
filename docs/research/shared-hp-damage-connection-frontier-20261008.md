# Shared HP and damage connection dependencies, round157

This is a bounded source dependency investigation requested through the owner's
three-worker delegation. It adds research evidence, not an implemented numeric64
gameplay route. Round156's actual experience award64 changes remain separate.
No gameplay source, rule, database, native executable or web client is changed.
No build, test, SQL, process-memory inspection or native execution is performed.

The workers separately capture the actual resource storage/CAS chain, shared
Battle/Lua/checkpoint calculation chain, and per-recipient native packet/gateway
producers. Their source copies, hashes and actual reading ranges are retained in
`artifacts/integration/packet-connections-20261006/shared-hp-damage-connection-frontier-01`.
Those inventories are bounded searches; they do not prove all HP writers or all
client consumers have been found. Missing branches remain OPEN.

The storage worker found six mutation paths converging on
`SqliteRecoveredCharacterRepository::commit_resources_in_transaction` at674-701.
`load_resources` currently decodes HP/maxHP as uint32; migration version6 retains
DWORD CHECK constraints. The mandatory raw role maxHP equality at344-346 and
679-682 is a separate authority dependency, rather than permission to weaken a
guard. The original migration text stays immutable; a future change needs an
additive migration preserving saved rows and receipts.

The projection worker traced the actual diagnostic Battle Encode callback at
`Application.cpp:5380` to short hit presentation and DWORD absolute HP/bulk bodies,
then the battle service and Session response/queue/write path. The two-owner PK
projection remains a source candidate without the complete Application
RoomAuthority/result-queue binding. Existing CN scalar A/B headers are not a
hosted HP provider. The scoped src .cpp/.h symbol search did not find an extended
delta checked-method caller; that bounded absence is not a global unused claim.
The existing four web routes select native byte tunnels, not an extended profile.

The calculation worker located eight connected modification groups, including
actor/result types, signed loss/healing, preserved legacy DWORD arithmetic, exact
C++/Lua integer boundaries, existing formula gates, supply/revival, checkpoint
versioning and the staged service callbacks. The existing Lua supply input has a
MAX_INT32 compatibility gate; revival retains its 1m target maximum gate and
CUSTOM HP1/MP66 rule. The damage formula's floating division and bounded output
need exact intermediate treatment in a wide profile. No formula, balance cap,
eligibility or native rule was changed by this investigation.

## Root investigation: PK and guild resource dependencies

`SqliteOwnedPkRoomRepository::Input` stores two whole CharacterResources and
BattleActors. Its validation compares each actor to the saved resource readset,
the legacy role's DWORD maxima and the entry's `array<uint32_t,4>` resource view.
The current initial readset contains exact resource numbers, raw role and entry
bytes, canonical checkpoint and profile hash, under document version1. Merely
widening CharacterResources therefore neither qualifies a wide entry view nor
provides an extended role authority. A future extended profile must connect all
of those inputs and their checks together; narrowing to satisfy the old array
would lose the owner's authoritative values.

The checkpoint topology check masks HP/MP changes and compares the remaining
whole actors to the original two-owner input. Both `advance` and paired `settle`
encode/check canonical checkpoints and CAS exact prior checkpoint/revision.
Paired settlement additionally CASes the collected round and enqueues the two
exact views in the same transaction. These methods do not implement terminal
character_resources/role/EXP settlement or release both owner's locks. That
remaining terminal policy must not be described as completed HP persistence.

The existing guild audience maps carry whole CharacterResources, including
revision and design origin, for accepted and pending/offline members. The
succession and relations53 panel sources validate the whole resource values and
reload them when checking a publication. The conversation sources capture and
compare whole resources as well. These are resource read leases, not battle HP
writers or evidence of a native HP numeric64 packet. Widening shared state must
preserve whole-value lease comparisons and their actual owner/readset conditions;
replacing them with an HP-only or revision-only comparison is unnecessary.

Root reading ranges and copies are in `source/root-dependencies/`. No claim is
made that every guild path has the same callback behavior; the older draft and
relations53 are distinct existing implementations and remain unchanged.

## Implementation boundaries for the next source increment

1. Select explicit, separately versioned extended storage/checkpoint/wire
   profiles. Preserve version1 raw request/checkpoint identity and legacy replay.
   SQLite/Lua signed64 representability is not an owner-selected HP or damage
   gameplay maximum. The coin cap99999999999 applies only to coins.
2. Connect the absolute HP/maxHP domain and signed damage/healing delta to actual
   rule results, actors, mutation, resource load/CAS/write and recovery together.
   Preserve original DWORD bit-pattern arithmetic as the original native profile;
   its signed floor/cap semantics cannot be relabeled as ordinary wide math.
3. Connect exact integer Lua input/result conversion and intermediate arithmetic.
   Removing a bound without replacing a floating-point conversion is insufficient.
   Existing CUSTOM formulas and balance limits are not original CN authority.
4. Connect owned native role and entry projections before permitting large HP in
   those routes. Legacy short/DWORD producers must reject unrepresentable values
   before authoritative commit. Clipping, wrapping or splitting a hit cannot
   substitute for an explicitly qualified extended client profile.
5. Connect per-recipient TW/CN and web consumer/object/floating-text paths. The
   browser's native-byte tunnel inherits the selected native protocol; it does not
   widen native fields automatically. Peer web client files remain peer-owned.
6. Preserve account/character ownership, whole tuple/revision CAS, atomic readback,
   outbox/replay, death/win/loss outcomes, level behavior and frozen features.
   Add migration source rather than rewriting historical migration versions.

These are dependent implementation steps, not approval gates or changes to the
goal's scope. Whole-game source integration remains active. Comprehensive builds,
testing, repairs and release follow full source connection as the owner directed.
New packet values, phase bindings and completed bidirectional routes are0 for
this research round; the full-game denominator and completion percentage are
unknown.
