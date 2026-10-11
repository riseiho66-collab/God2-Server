# Battle service checkpoint commit boundary

RecoveredBattleService has an optional CheckpointCommit callback receiving full
before/after BattleCheckpoint values, not only BattleSnapshot. Both snapshots are
prepared after validated action/retaliation encoding and before storage callback.
Successful callback is followed only by existing noexcept battle publication and
admission flags. Bind rejects enabling both Commit variants; callers must keep all
durable writes in one transaction and throw only before committing their storage.

The existing Application callback/API remains unchanged by default. This is a
service integration point, not an enabled client reconnect feature.

Real Lua + in-memory SQLite integration test:

- Seed owned character at HP88/MP12 and complete initial checkpoint.
- Native decoded skill command triggers skill and surviving enemy retaliation.
- Inject checkpoint insert failure after proposed resource update: memory battle,
  stored checkpoint, HP/MP and revision remain at baseline.
- Retry commits HP76/MP4, battle revision3 and full RNG state atomically.
- Independently restore the baseline core and execute the same two actions;
  resulting complete checkpoint equals the stored one, proving no failed-attempt
  RNG advance. A duplicate command cannot write again.
- Reject dual commit callbacks before binding; unchanged legacy persistence tests
  remain enabled.

Release server/service test builds and service test pass. Terminal storage still
requires a combined checkpoint/resource/XP/ledger transaction; current active-only
repository method intentionally rejects finished snapshots. Receipt-only updates,
policy snapshots, durable leases, client reconstruction and fresh-session acceptance
remain open. This does not certify native combat formulas or normal gameplay.
