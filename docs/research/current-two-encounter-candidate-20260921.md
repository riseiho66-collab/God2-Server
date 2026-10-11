# Two-encounter Application candidate

CUSTOM-0014, default-off extension: diagnostic_encounter_limit defaults1 and
accepts only integer1..2. Limit2 additionally requires movement trigger, level
snapshot, terminal three rounds, progress span200 and award250. Resume remains
incompatible. Existing loopback and diagnostic DB isolation apply.

The session stores number of transitions started. First terminal release plus
the qualified post-battle context notification permits clearing the old entry
and participant guards only if below the limit. Movement readiness is reset;
another committed displacement is required. The limit itself prevents a third
entry. Disconnect removes session counters.

Second initialization checks role2/progress1250/revision2, XP250, resources
HP76/MP26/revision6 and expected design IDs, plus no pending checkpoint. It
does not call the fresh-role seed. Existing reserve_battle creates a new owned
battle reservation; seed checkpoint and settlement use existing transactions.
This remains a deliberately narrow two-battle diagnostic, not arbitrary role
growth or encounter balance. Each independent battle retains the existing
explicit seed123 test policy; this is not production randomness.

Build/config tests cover default limit, valid two, missing lifecycle flags and
invalid types/ranges. No new two-encounter live run has been executed. The native
runner still keeps one battle's aggregate state; it must archive each completed
battle and arm fresh observation before this mode can be qualified. Do not
interpret configuration acceptance as repeated client gameplay acceptance.

## Evidence rollover preparation

tools/strike_lab/encounter_evidence.py adds a bounded first-to-second evidence
archive operation, tested against the actual completed movement/return run.
It requires terminal vitals, world return with matching owner and correct order,
three commands, five natural completions, native level1->2/progress1250,
EXP formatter250 and progress return. All copied battle fields are allocated
before removing live observation fields; world/login/movement context survives.
Second rollover is rejected. Missing, failed or contradictory evidence leaves
the input unchanged. It neither writes client state nor changes the database.

Two tests (including seven negative subcases) pass. The helper is not yet wired
into the live runner; no two-encounter runtime claim follows from these tests.
Next integration must rearm battle observation after the first role/progress
update, set second resource baseline76/26 and totalXP250, preserve movement
ordinal while resetting connection sequence, and validate second terminal state.

## Live runner integration and two failed runs

Runner now wires bounded encounter count, archives first battle after native
role/progress consumption, rearms battle probes and expects second initial
HP76/MP26, XP250. Both failed runs remain preserved.

native-two-encounters-20260921-01: second entry resends skill seed and client
emits9A diagnostic (packet0768), naming CPM enu GodUpdateSkillUp/career0/skill1
at pmgod2.cpp1825, before Timer36 packet0775. The server grammar rejects9A.
The rejection must not be misattributed to Timer36 or the crypto checksum.
Application now sends the initial skill seed only on the first encounter.

native-two-encounters-20260921-02: second entry successfully initializes, stored
battle2 is active revision1 and resource revision7 retains76/26. Client's initial
35/0B packet0791 carries target masks{1,0}, unlike the first entry's{0,0}.
Current initial-control policy rejects it before the subsequently emitted skill.
Exactly one settlement remains; battle1 is finished revision6. Run ends
EVENT_BUDGET_END, NOT completed two-encounter acceptance.

Next qualify a narrowly scoped repeated-entry initial-control policy, preserving
owner/context checks and rejecting premature/repeated notices outside that phase.
No generic mask acceptance or diagnostic9A ignoring was introduced. Evidence
regression records the known failure and unchanged first-battle reward/resources.

## Run03: two battles and subsequent movement accepted

diagnostic_second_encounter_entry is trusted, default-off policy requiring
initial-control/single-action mode, active revision1 and no checkpoint-resume
policy. Only its initial notice accepts mask1/0; first entry remains0/0.
Owner/context/unwritten-field and single-notice checks remain. Tests reject
wrong context, wrong first-entry mask, duplicate initial and treating that
initial notice as the later action receipt. Notice changes no battle state.

native-two-encounters-20260921-03 ends NATIVE_MOVEMENT_PATH_COMPLETED, error null.
Each independently observed encounter contains3 skills,5 natural1/1 animation
completions and native EXP formatter250. First level snapshots1/0 ->2/1250;
second2/1250 ->2/7500. First battle's world return precedes second initialization.
After second return, movement reaches18,12 and idle0. DB contains distinct IDs1/2,
both finished revision6, two settlements, XP500, resourcesHP52/MP2 revision10,
position18,12 revision3. No reseed/heal or repeated award observed.

Build and recovered_battle_service CTest pass; test_encounter_evidence now covers
both prior failure and successful run. This supersedes live-pending statements
above for the exact two-encounter fixture only. Normal UI/render acceptance,
general encounters, recovery beyond the qualified checkpoint, replenishment,
defeat and production balance remain open. Full playable-world goal incomplete.

## Fresh login after two encounters

native-two-encounters-relogin-20260921-01 uses a read-only SQLite backup of
run03, a new client process and world-resource restore only (no new combat,
resource seeding or award mode). Result NATIVE_SAVED_POSITION_RESTORED with
error null and one owned character. Native role memory after resource handler
returns contains HP52/max120, MP2/max80, level2/progress7500 and base attributes
10/10/10/10. Restored position18,12 matches the saved position.

Exact source/target row comparisons pass for role snapshots, resources, XP,
checkpoints including RNG, reservations, settlement ledger and positions.
Reauthentication does not heal, reseed, reaward or alter these gameplay tables.
test_encounter_evidence now contains5 tests, including fresh PID, native field
consumption and unchanged DB comparisons. This is current-client native probe
acceptance, not physical UI acceptance or proof of every reconnect scenario.
