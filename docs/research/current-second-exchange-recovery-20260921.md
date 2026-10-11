# Second Exchange Recovery Validation

CUSTOM-0012 remains an isolated, explicit test combat policy, not a native
damage formula. DiagnosticBattleRecovery now accepts an explicit completed
exchange count of one or two. It replays the fixed initial actors, seed123,
skill and retaliation through the supplied rule and compares the entire
checkpoint, including RNG. Zero, terminal third exchange, and unbounded counts
are rejected. The existing first-exchange wrapper retains its exact boundary.
Default-off diagnostic_resume_checkpoint now also accepts the second boundary;
visibility and revival recovery do not inherit this expansion.

The second boundary is revision5, playerHP76/MP34 and enemyHP42. A saved state
after only the second skill is not this boundary. Regression rejects that
partial state, mismatched first/second boundaries, modified HP/MP/enemy HP,
defense, owner, revision and stale RNG. After codec round-trip and Battle::restore,
the terminal skill emits byte-identical wire to uninterrupted execution and
finishes with identical complete checkpoint, playerMP26 and winning side0.

## Native Interrupted Run And Fresh Restore

`native-second-exchange-pending-20260921-01` completes two native skill commands
and four natural animations with no fallback. The runner's new
`--stop-after-second-checkpoint` requires a fresh isolated single encounter and
checks active battle revision5/resource revision5, no settlement. It preserves
the database at player76/120HP,34/80MP and enemy42HP, level1 and no XP. This is
controlled interruption after animations, not proof of a saved client receipt.

Application checks owned role seed/revision/provenance, absent XP, matching
resource and checkpoint revisions, policy tag and absence of revival phase,
then replays all actors and RNG. It restores the existing battle ID, sends saved
participants, and sets the round budget to the final remaining action. No
resources are seeded and no new encounter is reserved.

`native-second-exchange-resume-20260921-01` is retained as failed evidence:
last skill commits and its animation completes, but the old friendly terminal
receipt policy rejects the client's enemy-mask control and closes the session.
Packet0552 has native plaintext/checksum agreement and logical bytes
`35000b0000000001000000000000000000`, masks0/1. This is the basis for the narrow
second-exchange policy exception, not a guessed reconnect control rule.

`native-second-exchange-resume-20260921-02` starts a fresh server/client using
a read-only backup of the pending database. Result NATIVE_MOVEMENT_PATH_COMPLETED,
error null: one skill, one natural animation, native EXP formatter250, native22
level1/progress0 to level2/progress1250, and movement to18,12/revision3. Final
resources76/120HP,26/80MP revision6; battle finished revision6; one ledger/XP250.
The original pending database still has revision5 and no XP/settlement.

All six compared gameplay tables equal the uninterrupted durable run and the
first-exchange resume run: checkpoint (including RNG), resources, XP, role,
settlement ledger and position. The newer revival_document schema column is
checked separately to be NULL, not silently omitted as arbitrary differing data.

Verification: Release server/service/tests build; five targeted CTest suites
pass (battle_transaction, recovered_battle_service, session_battle_service,
config, recovered_character_repository). Saved native resource evidence suite
passes25 tests. Unit cases reject wrong revision/policy combinations, receipt
replay and old-connection masks; original uninterrupted receipt behavior remains.

These are native function probes, not physical-input/visual gameplay acceptance.
General arbitrary-round/partial-action recovery, production balance and native
damage/growth formulas remain open. No production promotion is claimed.
