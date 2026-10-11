# Durable battle reservation groundwork

SQLite migration7 adds an EMPTY battle_reservations table: database-generated
AUTOINCREMENT identity, owned character foreign key, starting resource revision
and CUSTOM-0012 provenance. Unique(character_id,resource_revision) represents
one diagnostic reservation at that exact resource version. It is NOT an award
ledger, an active-battle exclusivity lock or an in-progress battle snapshot.

RecoveredCharacterRepository.reserve_battle runs BEGIN IMMEDIATE, checks the
account's ownership and complete expected resource snapshot, rejects missing,
stale or zero-HP resources, inserts only if the version has no reservation and
reads back the persisted ID. Same-version retries return the same ID; changed
resource versions receive distinct IDs. It never writes resources or rewards.
No runtime Application call or payout is enabled by this change.

Tests exercise empty migration, same-version retry through a new repository
object, foreign account, missing/stale/altered resource snapshot, insert-trigger
failure with rollback, new-version identity and zero-HP rejection. Existing
accounts, profiles and mock data remain unchanged. The rebuilt database,
character repository, movement and position/resource test suites pass.

Limits: tests currently use in-memory SQLite; disk close/reopen and concurrent
connections remain unqualified. Same-version reservation reuse is only admission
idempotency. A version change mid-battle does not grant permission to create a
second active battle: the future lifecycle layer must enforce active ownership.
Existing sessions still use their prior in-memory battle IDs until explicit
integration. Do not claim exactly-once awards from this table alone.

Next: persist the battle lifecycle and request identity through restart, then
commit final resources, eligible EXP and a unique payout record atomically.
Retries after payout must match the original settlement payload and cannot
reapply resources or EXP. Native monster awards and leveling rules remain open;
no production numerical rewards are introduced here.

## Disk reopen, contention and diagnostic integration

The new recovered-character repository test creates a real temporary SQLite
file, reserves a battle, closes all handles, then reopens and verifies the same
ID. After a resource version change, two independent initialized connections
start concurrent requests through std::async and a shared start gate. Both
return the same NEW ID, only two total reservation rows exist (one per version),
and both see unchanged HP/MP. After closing both handles, another reopen reads
the same committed identity. The suite passes10 consecutive repetitions. This
qualifies graceful reopen and this concurrent workload, not power-loss recovery.

Application now calls reserve_battle only in diagnostic_battle_resources after
validating/loading the existing resource row, and passes its result to the
Battle constructor instead of session.id(). Session bindings remain keyed by
session identity. Other modes are unchanged. A failed later initialization may
leave an unused reservation; lifecycle cleanup and active exclusivity are still
open. No payout is triggered by reservation creation.

Live native-player-durable-battle-id-20260921-01 completes three skill rounds,
five natural animation batches, return to world and movement. Disk holds one
reservation(id1,character1,starting revision1,CUSTOM-0012) and final resources
HP76/max120,MP26/max80,revision4. Ten resource evidence regressions pass.
This supersedes the earlier in-memory-only and no-Application-call limitations,
but not the missing atomic reward ledger or full battle recovery.
