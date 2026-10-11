# Revival Fresh-Connection Recovery

Scope: CUSTOM-0017, isolated own-server diagnostic only. Not production balance,
native formula recovery, ordinary UI acceptance, or full battle resumption.

## Admission and implementation

Application permits revival plus resume only with durable resources and one
diagnostic round. The lab makes a SQLite backup from a read-only source;
resource revision5, receipt-complete phase and the existing strict three-actor
projection gate are required. Normal resume restrictions remain unchanged.
Stored phase is restored after binding. Initial and death actions are not
replayed; the durable checkpoint and phase callbacks remain attached.

RecoveredBattleService explicitly arms one connection-local zero-mask control
notice after a trusted phase restore. It checks owner, actor, side, context,
reserved fields and exact single-record shape. The notice is consumed once,
without invoking persistence or changing battle flags/resources. Pending notice
blocks rearm and readiness; duplicate, mixed and mutated notices are rejected.

## Actual runtime evidence

- Source: artifacts/runs/native-revival-durable-20260921-01/diagnostic-accounts.db.
- restore-01: native three-actor projection succeeds, but initial 35/0B zero-mask
  notification is rejected and the connection closes. The early observer result
  NATIVE_REVIVAL_RESTORED_PARTICIPANTS is not connection acceptance.
- restore-02: new own-server run with the one-shot notice admission. Initial
  packet0323 plaintext `140035000b0000000000000000000000000000c8` is accepted
  with zero response bytes. Native actor0 has HP100/MP14/max120/80; actor1 has
  HP1/MP5/max120/20; actor14 has HP132/max150. Enemy MP is not qualified.
- Next native packet0347 is standalone action2:
  `14003500020000010000000000000000000000c0`. The service rejects it and closes
  the connection. Both packets match captured native plaintext and checksums.
- Observer now continues after projection. Run ends EVENT_BUDGET_END with no
  tool error; that result does NOT imply a healthy connection. Server rejection
  is authoritative. World acceptance stays false.
- Source and copy resources/checkpoint/phase compare equal after the attempt.

## Verification and next required work

The battle-revival unit test covers restored-phase notice admission, malformed
and duplicate records, unchanged recovery envelopes, and blocked premature
rearm. Saved-runtime suite now has16 tests, including the negative action2
result and read-only comparison of both databases.

Next: qualify the complete fresh-client action2/control opening sequence;
separate connection initialization from saved action receipts without silently
replaying revival or advancing combat. Then validate explicit rearm, a resumed
action, natural animation, subsequent receipt and atomic persistence using a
fresh client. None of those remaining steps is certified by this run.

## Follow-up: restore-03

The service now admits exactly one standalone action2 mask1/0 after consuming
the initial zero-mask notice. Actor/side/context/reserved fields must match.
It changes only the connection-local stage, with no combat/persistence callback
and no response payload. Until this opening arrives, rearm and readiness stay
blocked. Duplicate/mutated opening records remain rejected.

artifacts/runs/native-revival-restore-20260921-03 uses a new native client and a
fresh read-only-source SQLite backup. Both initial and opening notifications
are accepted. Subsequent heartbeats and timer36 continue without policy
rejection. The bounded45-second observation ends HARD_TIMEOUT, error null,
world_accepted false. No next-round grant is sent; resources and saved battle
phase remain equal to the source. A17th saved-runtime regression test checks
these facts alongside the earlier negative run, which remains preserved.

This closes the observed initialization disconnect, not full battle recovery.
Next required evidence is trusted rearm followed by a real resumed native
action, natural animation, receipt and atomic resource/checkpoint update.

## Follow-up: resumed action and durable receipt

Application now emits a86/5 grant after the accepted standalone opening in the
strict revision4 restore path. Trusted rearm commits cleared action/control
flags before exposing the response. The existing native-call observer invokes
the client's original basic-action function; this is not physical UI input.
The fresh client's first action is settled with bulk88 cycle0, not the old
connection's cycle2. Gameplay still uses the labeled custom diagnostic rule.

Runs artifacts/runs/native-revival-resume-action-20260921-01 and -02 both show
enemy HP132->114, caster100/14 and ally1/5 unchanged, and one natural1/1 animation
batch without timeout fallback. First run rejects the subsequent native receipt
`140035000b0000000001000000000000000000c9`: its mask is0/1 rather than1/0.
This negative evidence is retained. The service now admits that mask only in
the qualified restored OpeningConsumed state at battle revision5 with an action
pending; wrong-mask and duplicate receipt tests remain rejecting.

Second run accepts the receipt and continues heartbeats and timer36 without
policy rejection. SQLite has battle revision5, resource revision6, enemyHP114,
action/control true, and no settlement. No revival173-byte response is replayed;
exactly one rearm and one156-byte basic response occur. Run finishes its bounded
observation as HARD_TIMEOUT/error null; world acceptance remains false.

Four CTest suites pass: battle_revival, config, recovered_character_repository,
current_revival_live (18 saved-runtime test methods). These cover the observed
single resumed attack and persistence, not arbitrary battle recovery. The input
projection gate deliberately remains revision4 with the qualified actor values.
Repeat recovery from revision5, interruption during pending action, general
multi-round recovery, UI acceptance and multiplayer ownership remain unfinished.

## Repeat recovery from the next save

The input gate now accepts a receipt-complete continuation of the same isolated
three-actor archetype, using the saved living enemy HP and battle revision.
Owner, actor slots, max resources, player/ally state and diagnostic combat stats
are still checked. Battle::restore validates bounds; revisions below4 or near
uint64 overflow are rejected. Resource revision must equal battle revision+1.
The connection stores its restore revision and qualifies the post-action
receipt at that revision+1 rather than literal5. No native formula is inferred.

artifacts/runs/native-revival-repeat-resume-20260921-01 uses a read-only-source
backup of resume-action-02. Fresh native actor memory starts at enemyHP114,
then the next original-client basic command yields HP96. Caster100/14 and
ally1/5 remain unchanged. One natural animation completes, receipt is accepted,
heartbeats/timer36 continue, and SQLite stores battle revision6/resource
revision7 with action/control true and no settlement. Bounded HARD_TIMEOUT is
observation termination, not full world acceptance; world_accepted stays false.

Four targeted suites pass, with the saved-runtime test now checking all three
resumed-action runs, including the earlier rejected receipt. The service test
also exercises restoration from revisions4 and5 and duplicate/wrong receipts.
Pending-action crash recovery, terminal enemy death, arbitrary party/resource
states, continuous multi-round recovery and UI/multiplayer remain unfinished.

## Two continuous rounds after reconnection

The isolated resume limit now allows one or two rounds. New-connection settled
snapshot cycles use rounds_granted-1; the next-round snapshot uses
rounds_granted. This avoids importing the old connection's revival cycle into
the fresh client's animation state. Observer stores command, damage and
animation return per resumed round instead of losing the first observation.

artifacts/runs/native-revival-two-round-resume-20260921-01 restores the prior
HP96 save. Two consecutive original-client basic calls produce enemyHP78 then
60. Both native animations complete naturally1/1. Control receipts are0/1 for
the first resumed action, then1/0 for the next; existing phase-specific service
checks accept each and reject the swapped/duplicate forms in unit tests.
There is one reconnect rearm, one next-round grant and two156-byte responses.
SQLite ends at battle revision8/resource revision9, action/control true,
caster100/14, ally1/5, enemy60, no settlement. Heartbeats continue without policy
rejection until bounded HARD_TIMEOUT; error null and world_accepted false.

Four targeted suites pass; the saved-runtime suite now contains19 test methods.
This proves two nonterminal resumed rounds of this isolated custom battle,
not unlimited rounds, terminal settlement, arbitrary party recovery or UI and
multiplayer acceptance. Those remain open, along with native formula recovery.

## Terminal action, settlement and native world return

An explicit isolated resume+durable+terminal one-round configuration now permits
zero-award terminal testing. It reuses the existing CUSTOM-0011 power1000 lethal
test setting, not production damage balance. Fresh revival terminal mode and
unqualified XP awards remain rejected. Finished actions use settle_checkpoint
atomically instead of storing an invalid active revival phase. The terminal
receipt does not attempt to persist that removed phase; release still requires
the valid receipt and does not grant another action.

artifacts/runs/native-revival-terminal-resume-20260921-01 restores the prior
enemyHP60 checkpoint, receives a native basic command and projects HP0. A1/1
animation completes naturally in2026ms. The native outcome receiver marks its
result, the outcome-panel function returns, cleanup and battle-loop return
occur, then the original world loop is entered. Result is
NATIVE_SOCKET_BATTLE_RETURNED_TO_WORLD_LOOP, error null. Broad world_accepted
remains false: this is native-function/loop evidence, not visual UI acceptance.

SQLite contains finished battle revision9/resource revision10, phaseNULL,
caster100/14, enemy0 and exactly one zero-XP CUSTOM-0012 settlement. No rejected
packet is recorded and service release occurs once. Regression checks verify
the native event order, animation, final checkpoint/resources and settlement.
Service unit coverage verifies no release before final receipt, no extra phase
commit after terminal settlement, and rejection of duplicate receipt. Its
initial failure exposed an extra enemy in the test fixture; terminal fixture
now correctly contains only the three diagnostic actors. Four suites pass;
saved-runtime suite has20 test methods.

Still open: post-return movement and persisted world resources for this path,
terminal crash/relogin recovery, real rewards/loot, general party battles,
production balance, native formulas and multiplayer/UI acceptance.

## Post-terminal movement acceptance

artifacts/runs/native-revival-postbattle-move-20260921-01 repeats the terminal
restore with the existing post-battle native movement probe enabled. After
cleanup and original world-loop entry, three native path commands receive
ACK5D01,5D02,5D03. Native coordinates reach18,12, ring010304, motion_state0.
Result NATIVE_MOVEMENT_PATH_COMPLETED has error null. Server accepts exactly
three movement records after releasing battle, without policy rejection.

SQLite recovered_positions contains character1/area2/scene15/x18/y12/revision3.
Resources remain HP100/MP14/revision10, exactly one zero-award settlement
exists, and the finished checkpoint has phaseNULL. This shows movement does
not replay settlement or rewrite battle resources. Four targeted suites pass;
saved-runtime suite has21 methods. Physical UI acceptance, relogging with the
completed save and world resource display remain distinct unverified steps.

## Settled save: fresh world login

artifacts/runs/native-revival-settled-relogin-20260921-01 uses a read-only-source
SQLite backup of postbattle-move-01. A fresh native client logs into the own
server with world-resource projection enabled and battle transition/resume
disabled. No gameplay implementation change was required for this path.

Result NATIVE_SAVED_POSITION_RESTORED has error null. Native position bytes
are120000000c000000 (18,12); the native role resource receiver returns
64000000780000000e00000050000000 (HP100/max120, MP14/max80). These are
native-memory observations, not visual HUD acceptance.

Read-only comparisons prove position, resource, checkpoint and settlement rows
are identical before/after login. The existing single zero-award settlement
remains single, and no battle transition or release is replayed. Four targeted
suites pass, including22 saved-runtime test methods. Broad world_accepted stays
false. Crash windows, physical UI, native formula recovery, rewards/loot and
general multiplayer gameplay remain unfinished.
