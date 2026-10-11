# Visibility Battle Pre-Action Recovery

## Scope

CUSTOM-0027 lifecycle integration uses existing CUSTOM-0012 persistence and
CUSTOM-0010/0011 diagnostic combat. No recovered damage formula or balance
approval is claimed. `diagnostic_visibility_checkpoint` is default-off and
requires the existing loopback-only durable visibility battle configuration.

The saved checkpoint must equal the initial diagnostic Battle checkpoint,
including actors, revision and RNG. This is deliberately not acceptance of
arbitrary mid-round snapshots. Existing non-checkpoint native evidence remains
unchanged; the native shared runner now exercises this flag with
`--checkpoint-battle --persist-battle --observe-battle`.

## Verified Server Behavior

- Initial checkpoint advances resource revision1 to2 once.
- Disconnect sends observer removal73; reconnect registers the owner again.
- Battle re-entry reuses the reservation, checkpoint and resources unchanged.
- Terminal settlement advances resources2 to3 with one settlement and zero XP.
- World refresh, movement persistence and observer departure still work.
- A canonical checkpoint with changed enemy physical attack is rejected, with
  no successful battle binding, resource overwrite or extra reservation.
- Injected settlement INSERT failure preserves the checkpoint and resources;
  no XP or settlement record is committed and no success response is emitted.

## Reproduction

```powershell
cmake --build build --config Release --target god2-server god2-tests
ctest --test-dir build -C Release -R "^config$" --output-on-failure
python -B -m unittest discover -s tests/research -p test_player_visibility_server.py -v
```

The Python suite runs real Application processes, authenticated synthetic TCP
peers and temporary SQLite databases. These tests are not original-client E2E.
At this initial synthetic stage native reconnect was still open. The subsequent
native acceptance below covers pre-action recovery only; disconnect during
action/receipt handling and general recovery remain open. No production flag
is enabled by this work.

## Native Normal-Path Acceptance

Run `native-shared-checkpoint-20260921-01` completed with two original clients
(PIDs9440 and18604) against the isolated own loopback server. Combatant returned
to the world, rebuilt the peer display and completed three original movement
steps. The observer saw Fight set/clear and the resulting movement. SQLite
contains one reservation, one zero-XP settlement, resources at revision3, a
finished checkpoint at battle revision2 and position18/12 at revision3.

`test_captured_native_checkpoint_battle_and_movement` checks both clients'
reports, frame hashes/checksums, display/movement samples and read-only database
state. This run did not disconnect during battle. Native recovery acceptance
was left for the separate disconnect run below.

## Native Pre-Action Disconnect Acceptance

`native-battle-reconnect-20260921-02` passes the full checkpoint battle command
above with `--post-battle-movement --checkpoint-reconnect` added. The owner
stops only its two test client process trees after the native action return
probe pauses before queued-action transmission. The archived checkpoint has
battle ID1, revision1, active state, resource revision2 and no settlement.

Fresh native processes then authenticate the same two characters against the
same server process/generation. Before releasing their battle barrier, the
runner checks exact equality of all checkpoint, resource, reservation and
settlement rows against the pre-disconnect snapshot. The resumed combatant
PID2248 and observer PID21148 complete battle, world repopulation and movement.
The terminal state contains one reservation and one settlement, not a second
battle. The captured regression checks fresh client identities, unchanged
server identity, native wire/display evidence and final database state.

Run01 is preserved as failed: capture/disconnect succeeded but the owner tried
to overwrite its immutable manifest. Run02 uses a separate recovery manifest.
This qualification restarts both clients, not the server. It does not qualify
arbitrary mid-action recovery, observer continuity while the owner reconnects,
or production combat balance.

## Post-Commit, Pre-Receipt Disconnect

`test_owned_terminal_disconnect_keeps_committed_settlement` extends the real
Application synthetic TCP suite. After receiving lethal damage, it withholds
the terminal control receipt, records the finished checkpoint (battle revision2,
resources revision3), disconnects and authenticates the same character again.
The first world tick registers the character with status0; movement succeeds.
All checkpoint, resource, reservation, XP and settlement rows must remain
identical to the committed pre-disconnect rows. This proves no duplicate write
on this bounded reconnect path, not outcome-panel replay in a native client.

The test's initial status assertion used body offset4; corrected to body offset6
(logical6F offset7), matching the existing encoder. No wire format changed.
The diagnostic encounter count is session-local; subsequent world ticks can
start another explicitly diagnostic encounter. This test does not assert that
the test runner's automatic encounters remain suppressed after reconnect.

Next native observation point is apex damage-return breakpoint439: expected
enemy HP is verified there, before the terminal/outcome breakpoint440. A native
post-commit disconnect run must independently establish that no terminal receipt
was transmitted and account for automatic diagnostic encounter admission.

## Native Post-Commit Disconnect Acceptance

`native-terminal-reconnect-20260921-01` passed using `--terminal-reconnect`
instead of `--checkpoint-reconnect`. At original damage-return breakpoint439,
enemy HP0 was observed and the probe remained paused while the owner captured
the committed state and stopped only its own client process trees. The first
client's captured C2S35 actions are exactly initial control0B and attack01;
hash/checksum verification confirms there is no subsequent terminal receipt.

Fresh clients PID3156 and8300 reconnect to the same server generation. This
diagnostic automatically starts a NEW encounter: battle1 remains finished at
resource revision3, while battle2 reserves that baseline and creates its active
checkpoint at resource revision4. Before releasing the second native action,
the runner proves battle1's full checkpoint and settlement rows are unchanged.
Battle2 finishes at resource revision5. There are precisely two settlements,
one per distinct battle, zero XP, and no replay of battle1. Both returning-world
display reconstruction and original movement/save complete normally.

The captured regression compares pre-disconnect, pre-second-action and final
database state, client/server generations and original frame evidence. The
45-test remote-actor/contract/identity suite passes. This is post-commit
disconnect durability, not replay of the missed outcome panel. Arbitrary
mid-round recovery, server restart in this combined mode, balance and production
activation remain open.

## First-Exchange Recovery Validation Foundation

The separate three-round skill diagnostic already has original-client evidence
in `native-player-pending-checkpoint-20260921-01` and
`native-player-checkpoint-resume-20260921-02`. This is not yet integrated with
the combined visibility battle. Its Application resume gate previously checked
the two actors and revision but not complete RNG equivalence.

`game/DiagnosticBattleRecovery.h` now validates that complete saved checkpoint
against the existing CUSTOM-0012 first skill plus retaliation, evaluated using
the current Lua rule and original diagnostic seed123. Replay is local to a
temporary Battle object: it neither sends packets nor changes stored resources.
Application calls this before binding the existing standalone resume path.
Changed controller, enemy attack, valid-but-different RNG state and revision
are rejected. This does not assert official math or qualify arbitrary snapshots.

Validation passed against the actual archived native checkpoint, opened read-only:

```powershell
build/tests/Release/battle-transaction.exe artifacts/runs/native-player-pending-checkpoint-20260921-01/diagnostic-accounts.db
ctest --test-dir build -C Release -R "^battle_transaction$" --output-on-failure
python -B -m unittest tests.research.test_current_battle_resource_persistence
```

Build and transaction tests pass, as do23 captured persistence regressions.
This is offline validation of original-run evidence, not a fresh native resume
run. Next integration must retain the existing skill/receipt phase contracts
while adding same-scene observer lifecycle; the one-round visibility fixture
remains unchanged and default-off.

## Combined Skill Recovery Integration

`diagnostic_visibility_skill_recovery` adds an explicit default-off combination:
visibility checkpoint + skill seed/settlement + three animated terminal rounds.
Missing persistence/skill dependencies are rejected. Existing one-round mode
still rejects unrelated skill flags and remains unchanged. The existing Lua
CUSTOM-0012 test rule is reused, not replaced or promoted as official math.

On a pending first-exchange checkpoint, Application validates the complete
checkpoint using DiagnosticBattleRecovery, projects saved actor vitals and
restores the already-qualified first-exchange receipt policy with two rounds
remaining. Other unsupported revisions remain rejected. Initial checkpoints
still require exact pre-action equality.

The new real-server synthetic TCP test disconnects before the first exchange
receipt: player88/120 HP,42/80 MP, enemy96 HP, resource revision3. After reconnect
the same reservation/checkpoint are unchanged. Two remaining skills finish at
player76/120 HP,26/80 MP, resource revision5 and battle revision6, with exactly
one zero-XP settlement. Observer title clears, world refresh and movement save
complete. Another test changes enemy attack and requires rejection without
overwriting persisted state. Native dual-client acceptance of this combined
skill mode remains pending; earlier standalone evidence is not a substitute.

## Combined Native Three-Skill Normal Path

`native-shared-skills-20260921-01` qualifies the uninterrupted combined mode:

```powershell
python tools/strike_lab/shared_visibility_run.py --run-id native-shared-skills-20260921-01 --timeout 300 --observe-battle --post-battle-movement --persist-battle --checkpoint-battle --skill-battle
```

Original client processes3304 and22784 share the same own-server world. The
combatant's original selection/command code emits three skill1 commands. Native
skill settlement, retaliation, terminal panel and world return complete; the
observer sees Fight set/clear and the three post-battle movement steps. Final
resources are76/120 HP,26/80 MP at revision5, checkpoint battle revision6 with
enemy HP0, and exactly one zero-XP settlement/reservation. Position is18/12,
revision3. Frame hashes/checksums, original skill command bytes, process reports,
world display samples and SQLite rows are covered by the captured regression.
The46-test remote actor/contract/identity suite passes.

The shared runner verifies manifest/config skill-mode agreement, and the first
original skill command waits for the observer's verified Fight sample before
transmission. Test synchronization is not production pacing. Shared skill
disconnect remains unqualified; this run does not replace the pending native
first-exchange reconnect test. Production and official formula claims remain off.

## Combined Native First-Exchange Recovery

The subsequent `native-skill-reconnect-20260921-03` adds `--skill-reconnect` to
the normal skill command. The original first client completes one skill and
retaliation with two natural animation completions, then pauses before the
next action. The owner captures battle revision3, resources88/120 HP and42/80 MP
at revision3, enemy96 HP, one reservation and no settlement, then closes only
its owned test clients.

Fresh original clients18612 and21636 reconnect to the same server generation.
Before releasing the new skill command, every saved checkpoint/resource/
reservation/settlement row equals the pre-disconnect snapshot. The original
client projects saved vitals and issues exactly two remaining skills. Final
world reconstruction and movement complete. Read-only comparison of the six
tables (checkpoint including RNG, resources, reservations, XP, settlements and
positions) is exactly equal to uninterrupted `native-shared-skills-20260921-01`.
The50-test remote actor, contract, identity and map-catalog suite passes.

Run01 failed because abrupt child termination left its diagnostic hotbar file.
The leftover matched that run's fixture hash and was archived, not discarded.
Shared skill fixtures are now parent-owned across both client generations and
are cleaned after owned children stop. Run02 captured the native459ED2 null read:
FIRST_BIND count0/table0 with no observed loader entry/return. It is retained
as an unresolved startup fault and has a dedicated captured regression; run03
success does not establish a fix. Original clients/accounts were not modified.

This qualifies this specific first exchange, not arbitrary skill/round states,
network retry replay, server restart, stable multiplayer production or official
damage formulas. Those remain outside this diagnostic acceptance.

## Native First-Exchange Server Restart

`native-skill-restart-20260921-01` uses the same isolated skill recovery flow
with the new default-off `--server-restart` option. It is accepted only with
`--skill-reconnect`. After the first native skill/retaliation, the runner stops
its owned clients and server, verifies the durable rows are unchanged, and
starts the same server executable/config against the same diagnostic database.
The old manifest remains immutable. The new manifest binds the new process
generation and actual listener ports before fresh clients attach.

Server PID18636/create_time1790001979.4138236 ended before the replacement
PID21328/create_time1790002013.9700034 started. Fresh native clients6116/11280
restored the first exchange, completed two remaining skills, observed Fight
clear, rebuilt the world actors and completed the three-step movement path.
Startup and pre-action recovery checks compare all checkpoint/resource/
reservation/settlement rows exactly; no test-side database writes restore them.

The captured regression compares the six final tables against uninterrupted
`native-shared-skills-20260921-01`, including checkpoint RNG. Both databases
match exactly: resources HP76/120 MP26/80 revision5, one reservation and one
settlement, checkpoint revision6, enemyHP0, and saved position18/12 revision3.
It also checks distinct server generations, unchanged config, two remaining
native skill commands, native packet checksums, lifecycle and hotbar cleanup.
The combined research suite passes54 tests; config and battle_transaction
CTest targets both pass.

This supersedes the server-restart gap above only for this exact first-exchange
diagnostic scenario. It does not qualify power-loss durability, a crash during
an SQL commit, arbitrary battle revisions, production balance or official
damage formulas. All gameplay remains default-off CUSTOM test behavior.
