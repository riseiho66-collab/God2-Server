# Current Defeat Closure

## Verified scope

The `recovered_battle_service` regression now covers a synthetic CUSTOM-0011
defeat through RecoveredWorldService, RecoveredBattleService and the existing
Lua combat rule. This is not native client defeat acceptance or native formula
recovery.

The isolated actor starts with HP4. Its attack leaves the enemy at HP82;
the existing diagnostic retaliation kills the actor. A throwing checkpoint
commit callback leaves both actors and revision unchanged. Retrying commits a
finished checkpoint at revision3, winner side1, player HP0. Restoring that
checkpoint preserves death. No further attack or diagnostic round rearm is
accepted. A foreign-context receipt is rejected; the configured synthetic
receipt permits one release to InWorld without another checkpoint commit.

Verification on 2026-09-21:

```
cmake --build build --config Release --target recovered-battle-service
ctest --test-dir build -C Release -R '^recovered_battle_service$' --output-on-failure
```

Build succeeded; 1/1 CTest passed. The injected callback is not a SQLite
failure-injection test. No production rules, saved accounts or client binaries
were changed.

## Initial observation gap (superseded by run below)

The current observer in tools/strike_lab/apex.py assumes victory:

- Skill settlement uses initial HP minus 12 per exchange without death clamp.
- Terminal settlement specifically requires enemy death with no retaliation.
- Role progress projection assumes the player survives all but the final round.
- Restore admission currently allows selected known living resource snapshots,
  not the HP4/MP56/revision20 post-supply battle save.

Do not label a defeat capture failure under these expectations as a client
protocol failure. Do not widen receipt masks on the basis of synthetic tests.

Next native experiment should use a read-only copy of
artifacts/runs/native-after-supply-battle-20260921-01/diagnostic-accounts.db
after verifying its HP4/MP56/revision20 baseline and empty slot revision4.
Add an explicitly isolated defeat observation path, retain all victory checks,
then capture the actual death animation, vitals, client receipt and result/world
transition. Match the observed receipt before qualifying its service policy.
Verify zero XP award and HP0 persistence across a fresh connection. Revival
location, HP restoration and penalties remain unqualified rules, not implied
by releasing the battle binding.

## Actual own-server defeat and fresh connection

`native-defeat-20260921-01` completed with
`NATIVE_SOCKET_DEFEAT_RETURNED_TO_WORLD_LOOP`, no observer error. The new
`--observe-socket-defeat` path is restricted to the saved HP4/MP56 baseline,
one encounter, terminal skill animation path, no supply, award, progression or
checkpoint resume. Existing victory checks remain unchanged outside this mode.

- One original skill command; MP56 -> 48 and enemy HP150 -> 96.
- Original client receives the retaliation update with player HP0.
- Both animation batches complete without timeout fallback.
- Captured packet0566 is `140035000b0000000001000000000000000000c9`,
  checksum-valid and matching the original sender plaintext. Existing service
  control policy accepts this receipt; no mask relaxation was required.
- Native result consumer accepts the zero-award 0x89 result, then cleanup
  returns to the same world role source with HP0/max120/MP48/max80.
- SQLite resources are HP0/MP48/revision21. Settlement5 has won=false and
  experience=0. Existing four settlements are unchanged; total XP remains500.
  Inventory and saved position are unchanged. Source HP4 save remains intact.

`native-defeat-relogin-20260921-01` uses a read-only backup of that result in a
fresh connection. It completes `NATIVE_SAVED_POSITION_RESTORED`; the native
resource update return holds HP0/max120/MP48/max80. Every SQLite table equals
the defeated source save, including resources and settlement ledger.

`tests/research/test_current_defeat_projection.py`: 3/3 saved-evidence tests
pass. Existing supply projection evidence: 9/9 pass. These tests inspect the
captured runs, not a fresh client launch on each test invocation.

This proves the bounded diagnostic defeat transport/state/persistence path,
not normal mouse interaction, visible HUD acceptance, native combat formulas,
revival, death penalties or arbitrary multiplayer death. The broad runner's
`world_accepted` remains false and is not reclassified. A dead character's next
allowed gameplay action and revival remain open work; no silent restoration
or production promotion has been added.
