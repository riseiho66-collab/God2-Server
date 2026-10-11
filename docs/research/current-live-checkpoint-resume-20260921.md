# Fresh-client checkpoint continuation accepted in isolated fixture

Source: native-player-pending-checkpoint-20260921-01, copied read-only.
Run: artifacts/runs/native-player-checkpoint-resume-20260921-02.
Result: NATIVE_MOVEMENT_PATH_COMPLETED, error null.

Correction to run01: the fresh client first local exchange emits control mask
{0,1}, not the former connection's second-exchange {1,0}. The resume policy
admits this only with diagnostic three-round retaliation, enemy default mask,
and binding at active revision3. At revision5 it retains that default; the
terminal revision6 friendly receipt is unchanged. Wrong-mask and replay tests
pass. No general mask permissiveness or saved RNG/reset changes were introduced.

The suspected counter change was NOT needed: existing bulk counters worked in
run02, whose skill command counters were0 then2. Do not infer universal counter
semantics from this fixture. This supersedes the proposed counter investigation
as an immediate blocker in current-resume-first-exchange-rejection-20260921.md.

Observed:
- Different client process restores HP88/MP42 and enemyHP96 at battle revision3.
- Two skills, five resource updates, three natural animation completions1/1;
  no animation timeout fallback (2416,3020,2485 milliseconds).
- Terminal battle revision6, winner0, enemyHP0, playerHP76/MP26; resources rev6.
- Exactly one settlement, XP250 CUSTOM-0012, native level1->2/progress1250.
- World movement completes; persisted position18,12 revision3.
- Original pending source remains active revision3, resource revision4, no award.

Build: god2-server and recovered-battle-service. Service test includes fresh
resume mask acceptance, wrong old-connection mask rejection and replay rejection.
Saved evidence regression additionally checks separate PID, restored resources,
remaining actions, animations, native level result, terminal DB and movement.

Scope: autonomous native debugger/probe against own loopback isolated server.
Not normal physical UI/visual acceptance; historical world_accepted classifier
still false. This is one qualified interruption point, not arbitrary mid-action
resume, distributed ownership or durable receipt queues. Gameplay stats/rewards
remain custom test values without production balance approval. Full playable
world goal remains incomplete.

## Continuity comparison

Read-only comparison against uninterrupted native-player-durable-checkpoint-
20260921-01 proves exact equality of all rows in battle_checkpoints (including
canonical RNG), character_resources, character_experience,
character_role_snapshots, battle_settlements (including transaction request),
and recovered_positions. Both paths contain one checkpoint and one settlement.
This compares independently executed native runs of the same explicit fixture;
it does not establish correctness for arbitrary encounter inputs.

The service regression now restores the actual CheckpointCommit output,
including the advanced RNG, rather than assembling a snapshot with fresh RNG.
Negative binding cases reject revision1, absent three-round policy, absent
single-action policy, absent retaliation and incompatible default target mask.
Saved-evidence suite now contains21 tests, not21 new runtime executions.
