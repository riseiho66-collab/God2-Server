# Committed movement to native battle, isolated acceptance

Run: artifacts/runs/native-movement-encounter-20260921-01.
Result NATIVE_SOCKET_BATTLE_RETURNED_TO_WORLD_LOOP, error null.
CUSTOM-0014 remains diagnostic-only and default-off.

Runner now permits one explicit pre-battle native movement with the movement
encounter option. It records the ACK and continues, disabling further movement
injection. Restore and post-battle movement probes are currently incompatible
with this mode; existing modes retain their earlier guards.

Evidence: ACK5D01 applies at sequence473, advancing ring to010102. Battle
initializer entry follows at490. Three skills and five natural1/1 animations
complete without fallback. Native world-loop return at718 retains the exact
world object from movement. SQLite retains position18,12 revision1, resources
HP76/MP26 revision6, one settlement and XP250 (CUSTOM-0012).

This qualifies committed movement -> native ACK -> diagnostic82 entry ->
combat -> terminal settlement -> world-loop return. It does not qualify
post-battle movement, a second encounter, visual/physical UI, arbitrary zones,
official encounter frequency or native monster attributes. The server's
once-per-session entry and fresh-role seed restrictions still block ordinary
repeatable gameplay and must not be hidden by this result.

Regression: test_committed_movement_ack_precedes_encounter_and_world_return
in test_current_battle_resource_persistence.py, reads saved evidence only.

## Battle return movement: failed run01 and corrected run02

native-movement-encounter-return-20260921-01 reached world return but failed the
runner's expected ring: position18,12 was retained, native ring was010001 rather
than010102. This disproved uninterrupted queue numbering through battle.

RecoveredMovementService::resume_after_battle now validates ready session,
account, character and unchanged saved-position baseline, then resets only the
connection slot. Application calls it after successful finished-battle release;
it is not exposed as a client operation. No position/resource/reward write occurs.
Runner tracks total movement ordinal separately from post-battle queue sequence.

native-movement-encounter-return-20260921-02 ends NATIVE_MOVEMENT_PATH_COMPLETED.
Observed movement ACKs: ordinal1/sequence1 before battle, ordinal2/sequence1 and
ordinal3/sequence2 after battle. Final native position18,12, ring010203, idle0 at
sequence776. DB position revision3, resources76/26 revision6, one settlement.
This supersedes the prior post-battle-movement gap for this isolated scenario.
Second encounter and production/visual acceptance remain unverified.

Tests cover wrong owner and stale baseline refusal, resetting an advanced ring
while retaining saved position, and saved runtime evidence. Server/tests build,
movement and position repository CTests pass. Failed run01 remains preserved.
