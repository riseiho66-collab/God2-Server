# Current-client battle resource save

Run: `native-player-skill-resource-save-20260921-01`.

The runner now exposes `--diagnostic-battle-resources`, requiring isolated
database and diagnostic skill settlement. It forwards the default-off server
configuration; no production activation or balance approval is implied.

The original-client native probe completed `NATIVE_MOVEMENT_PATH_COMPLETED`.
After one terminal CUSTOM-0012 skill, the native actor held HP100, MP42,
maximum HP120 and maximum MP80. The enemy reached HP0. The client completed
the outcome/return-to-world path and three movement steps.

A separate read-only SQLite connection after runner termination observed:

- character_resources: character1, HP100/max120, MP42/max80, revision2,
  design CUSTOM-0012.
- recovered_positions: character1, area2, scene15, x18, y12, revision3.

Validation: the new test_current_battle_resource_persistence.py evidence
regression passed (1 test). CTest config, recovered_battle_service and
recovered_position_repository passed (3 tests).

Scope: disk save agrees with the live client after settlement. A fresh
server/client restoring these resources is NOT yet qualified. Normal UI input,
visual acceptance, world HUD restoration, native formulas and production
balance remain separate requirements. Existing RX native-function probes are
not physical desktop interaction. No official service was used.

## Fresh connection continuation

Run `native-player-skill-resource-restore-20260921-01` starts a new server and
client against a SQLite backup of the preceding run, opened read-only at its
source. Resource restoration rejects any source other than the verified
HP100/max120, MP42/max80, revision2 CUSTOM-0012 row and saved position fixture.
It does not accept arbitrary initial values merely to make the observer pass.

The new client consumed the battle bootstrap with HP100/MP42, sent one native
skill command, then held HP100/MP34. One animation batch completed 1/1 without
timeout fallback. Outcome and world return completed, with saved position18,12
and result `NATIVE_SAVED_POSITION_RESTORED`. The new database holds MP34,
revision3; the source remains MP42, revision2. The regression checks distinct
client PIDs, bootstrap/settlement order, native actor values and both databases.

This supersedes the earlier unqualified fresh-resource-restore note for this
specific diagnostic path. It does not qualify world HUD resources, damaged HP
restoration, resurrection, rewards, physical UI interaction or balance.

## Damaged HP continuation

`native-player-damaged-resource-save-20260921-01` completed two skill/retaliation
rounds through the current native client. Four animation batches completed 1/1
without timeout fallback. Native actor HP76/MP34 matched the disk resource row
at revision3, with maxima120/80 and CUSTOM-0012 provenance. No movement had
occurred, so the position table was empty.

The runner now accepts that exact second fixture as a resource restore source,
with an empty position table required. It obtains observer expectations from
the validated source before running; all other resource rows are rejected.
`native-player-damaged-resource-restore-20260921-01` opened a fresh server/client
against a backup: native bootstrap HP76/MP34, then one terminal skill produced
HP76/MP26 and storage revision4. One animation batch completed without timeout
fallback, and result was `NATIVE_SOCKET_BATTLE_RETURNED_TO_WORLD_LOOP`.
The source database remains HP76/MP34 revision3.

The resource evidence suite now passes three tests covering both source/restore
pairs; four CTests (config, bootstrap, battle service, position repository) pass.
This extends the earlier scope to positive damaged-HP battle restoration. It
does not qualify in-progress battle resume: the restored client starts a NEW
diagnostic encounter. World HUD, death/revival, crash recovery and formal
balance remain open.
