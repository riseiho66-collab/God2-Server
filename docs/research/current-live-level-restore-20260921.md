# Current-client saved level restoration

## Change

Existing default-off `diagnostic_world_resources` now reads the owned saved role
snapshot alongside resources. When present, validates CUSTOM-0013 provenance and
matching HP/MP maxima, then sends complete saved22 before resource24 on the first
accepted standalone world tick. No role seed, progression recomputation, award,
healing or storage mutation. Without a role snapshot, prior24-only behavior stays.
Loopback, non-mock, recovered movement and diagnostic database gates are unchanged.

## Evidence

Source: `artifacts/runs/native-player-level-snapshot-20260921-01/diagnostic-accounts.db`.
Restored run: `artifacts/runs/native-player-level-restore-20260921-01/run.json`.
The runner opens source SQLite read-only and backs up into a new isolated database.
Fresh server/client selected the existing character; no new character was created.
Result `NATIVE_SAVED_POSITION_RESTORED`, error null, character_count1.

Native E71E0 resource consumer entry/return captured the role object, showing:

- Level2 at actor26 and progress1250 at actor58, already present before24.
- Four base slots10 at actor78/7C/80/84, maxHP120/maxMP80.
- Complete resource consumer return HP76/max120/MP26/max80, no healing.
- World position18,12 restored from disk.

The saved evidence regression compares both databases for exact rows in role,
resources, XP, battle reservations, settlement ledger and positions. All unchanged:
XP250, role revision2, resource revision5, single settlement. Thus this login did
not award again or rebuild the role from default values. Native22 complete-consumer
qualification is in the preceding level snapshot run; this run captures its stored
field effects before/after24, not an additional E6B40 breakpoint trace.

Release build passed. Four targeted CTests and16 saved evidence tests passed.
The16 tests inspect recorded evidence, not16 fresh client executions.

## Limits

CUSTOM-0013 test values remain isolated, not native growth or balanced production
rules. The first world frame can precede resource synchronization. Normal UI/HUD
visual acceptance, companion behavior, production character initialization, policy
versioning and repeated normal encounters remain open. Historical world_accepted
classifier remains false. No claim that the entire game is playable follows from
this specific own-server restoration result.
