# Native basic action animation routing

Pinned mapped image SHA256:
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
Addresses are RVAs with image base400000. No live client or production change.

## Proven route

Original length helper15840 returns15 for each logical83 and84. Only83's basic
action branch is exercised here; equal length does not establish equal layout.
Original116AE0, with explicitly supplied existing-batch flag+A9DF6B8=1,
continues to116BB1 without the first-batch renderer cleanup. No cleanup helper
is stubbed or given a fake return. The existing-batch condition is a test
precondition, not a claim about real socket timing.

For diagnostic83 records with byte1=1:

- Byte2 supplies source position. Native division by14 yields side and slot.
- WORDs at+5/+7 are searched by real11E5E0 for the first set bit, side0 then
  side1, low slot first, considering14 slots per side.
- Empty masks fall back to the source side/slot in116C5F..116C75. This is not
  authorization for a server to accept an empty client attack request.
- Source positions28,29,255 reach the native diagnostic-log boundary116BF4;
  tests stop BEFORE the logger, not after an assumed successful rejection.
- Byte11==0B preserves the branch's default status selector1C; otherwise
  byte12 supplies that selector. Only the explicit zero selector is executed
  in these tests. Its original1169F0 callee is executed, not replaced.
- Call117183 invokes12C520 with record+1, source side/slot, target side/slot.

The extended test continues without skipping calls through12C520 and the real
11E6E0 actor lookups. Explicit diagnostic actors have allocated component0
storage and handles100..127. Their idle action buffers are initialized by the
original manager. Basic action reaches12A8D0 with arguments action1, source
side/slot, target side/slot, record byte3 (zero in this test), and zero.
Tests stop BEFORE12A8D0. They do not prove movement, hit animation, sound or
completion of the animation queue.

## Tests

`python -B -m unittest discover -s tests/research -p test_current_battle_action_animation.py -v`

Four tests pass:112 source/target endpoint combinations; three mask/fallback
cases; three invalid sources; three continuous manager-to-action-setup cases.
The image stays read/execute and instruction ranges are fail-closed. All
record bytes are explicit diagnostic inputs, not captured official replies.

## Remaining contract

Trace12A8D0's basic-action stores and subsequent queue consumer; establish the
remaining83 fields and84 result pairing, timing/sequence and completion88
ordering. Only then add a diagnostic server emitter and observe original
client animation state transitions. Current HP86 and current-cycle88 success
does not replace that work. Full rendered/normal-input acceptance, native
damage formulas and production balance remain unproven.

## Continuous basic-action setup extension

The fifth regression extends the same execution from116AE0 through the real
12C520 ->12A8D0 call and its return, stopping at the subsequent12B060 callee.
No callee return is fabricated and no intervening call is skipped. The
existing-batch precondition and explicit synthetic actor storage still apply.

For basic action1 with valid source and target renderer handles, original
12A8D0 performs these observed writes:

- Source+1E9=1, source+1EA=11hex, source+233=0.
- Source+235 preserves bits4..6; bit7 becomes target side and bits0..3 target
  slot. These are native packed target fields, not a server authority check.
- Source+277 copies target+277, then target+277 increments as a byte.
  The test uses distinct actors with initial counter11 and observes11/12.

The resumed manager then calls12B060 with source side/slot, target side/slot,
WORD[logical83+9], zero, BYTE[logical83+11], and constant22hex. Tests cover
result-word values0,18,7FFF,8000,FFFF in three direction/position pairs.
Only the lowWORD/lowBYTE of partial-register arguments are compared; upper
register garbage is not silently treated as zero or part of the wire field.
Status byte remains explicit zero in these cases. No signedness, damage or
critical meaning is inferred merely from this argument forwarding.

All five tests pass. The next unexecuted boundary is12B060, followed by the
manager's remaining effect/queue bookkeeping and the per-frame consumer.
Full animations and original-client live acceptance remain unverified.

## Signed display delta and isolated live attempt

The sixth regression executes the original12B3C2..12B4A1 formatter route,
stopping before147AF7. Native12B48E sign-extends the result WORD and passes
the string at VA59D968, `HP %+d`. Inputs0,18,7FFF,8000,FFEE,FFFF retain
their WORD in actor+286 and supply the corresponding signed formatter value.
This proves display signedness, not damage authority or an official formula.

The default-off diagnostic emitter now sends negative actual hp_loss at+9;
18 encodes as EE FF. Zero encodes00 00; maximum qualified32767 encodes01 80.
Loss above32767 rejects before commit rather than clamping. All other opaque
fields remain explicit CUSTOM-0009 zeros. C++ regression covers392 opposing
source/target combinations plus bounds. All six native research tests pass.

Runs `native-player-animation-20260921-01` and `-02` used superseded positive
display deltas. Run01 stopped after one exchange; run02 requested two and
ended HARD_TIMEOUT. Neither certifies animation completion.

Fresh run `native-player-animation-20260921-03` uses the rebuilt negative-delta
server, original client diagnostic function calls, loopback and isolated DB.
It also ends HARD_TIMEOUT after one exchange: enemy HP132, friendly HP88.
At events520/522 both actors eventually expose action1/stage11hex in their
animation state. No second exchange is observed. Correcting display signedness
therefore does not resolve the animation-enabled round completion stall.

Next trace must inspect the native per-frame queue consumer and completion
notification after action setup, including the still-unqualified83/84 timing
fields. Do not bypass readiness or label this normal-input/visual acceptance.
The diagnostic flag remains off by default and has no production promotion.

## Timeout state observation

Run04 has no animation timeout snapshot because the observer flag was not
forwarded. Run05 has invalid wide `poi` values and an incomplete read after
the WOW64 stack command changed effective debugger architecture. Neither is
valid evidence for terminal actor state. The observer now forwards the flag
and explicitly selects `.effmach x86` before read-only memory inspection.

Run `native-player-animation-20260921-06` repeats the two-exchange request and
ends HARD_TIMEOUT after only one HP exchange. Its valid timeout snapshot has
stage1, result_received0, manager_event0, control_sent1, bulk_seen1 and both
cycle counters0. Actors0/14 change from action1/stage11hex at retaliation
receipt to action1/stage09hex at timeout. Target-counter bytes are01/FF.
Thus the native action state does advance; complete animation, meaning of09,
and second-round readiness are not proved. A seventh regression preserves this
distinction and rejects treating the run as successful two-round acceptance.

The prior run03 timeout stack is in recv via119370, called by battle loop1158B1.
Current pinned native dispatch maps83/84/86/88 to1195B1, queue append11D4E0;
the separate114399 ->116AE0 route consumes the basic action. The next focused
trace is the action-stage09 consumer and queued88 delivery/control latch,
not a fabricated completion packet or forced latch reset.

## Native dispatch qualification and receipt correction

Bounded native execution confirms1290A8 dispatches stage09 to1292E9 (general
update), while stage11hex dispatches to1290CD (basic-action update). This does
not identify09 as a completed animation. Original114538 defers88 when the
current action-batch flag is nonzero, disabling queue processing; when zero
it reaches118A90. Two regressions exercise those exact branches without fake
callee returns.

Run07 snapshot: queue_gate1, queue_hold0, batch_ended1, actions_expected0,
actions_completedFFFFFFFF. Crucially its server log shows a later control
record rejected, followed by disconnect. Post-action plaintext capture0551
contains logical `35 00 0B 00 00 00 00 01 00 00 00 00 00 00 00 00 00`:
target masks are {0,1}. The no-animation diagnostic had required {1,0}.
This is direct evidence of a diagnostic server policy mismatch, not proof
that88 remained queued forever or that no control was generated.

CUSTOM-0010 now stores an exact expected control mask in trusted per-session
policy; Application selects {0,1} only with the animation diagnostic flag.
Default {1,0} remains unchanged. The receipt cannot perform damage and still
requires matching identity/context, a prior action and no previous receipt.
Focused C++ tests reject premature/wrong-mask/replayed receipts and verify
that accepting the observed mask changes no battle revision.

Fresh run `native-player-animation-20260921-08` succeeds with two HP exchanges
and animation emission enabled: enemy150->132->114, friendly100->88->76.
Result NATIVE_SOCKET_DIAGNOSTIC_RETALIATION_APPLIED. A tenth evidence regression
checks both exchanges. This proves the earlier receipt mismatch is repaired;
it does not prove second-animation completion, normal UI input, rendered
effects or production balance. Native manager code1294AF also contains a
10-second completion fallback; successful round advancement alone must not
be used to claim every animation finished naturally.

## Animation-enabled terminal and world return

Fresh run `native-player-animation-terminal-20260921-01` uses the corrected
receipt policy, diagnostic83 emission and isolated lethal power1000 percent.
It ends NATIVE_MOVEMENT_PATH_COMPLETED. Observed event order:

- Damage return512: enemy HP0.
- Zero-award outcome return542, result-panel return544.
- Battle-loop return546, post-battle world-loop entry548.
- Three native movement steps complete at18,12 with motion_state0.

Read-only SQLite verification finds exactly recovered_positions row
(character_id1,area2,scene15,x18,y12,revision3). Server log contains one
DIAGNOSTIC_FINISHED_BATTLE_RELEASED and no world-policy rejection.
The same terminal/movement assertion helper now covers both animation-disabled
and enabled runs. All11 player-appearance research tests pass; the10 focused
CTest battle/config entries also pass.

This qualifies diagnostic packet/state integration through terminal return and
position persistence. It does not qualify actual screen rendering, normal UI
input, natural completion versus the native10-second fallback, combat HP/MP
persistence, rewards, balance or production activation. These remain explicit
acceptance gaps; the broad playable-world objective is not complete.

## Natural completion versus timeout, and action grouping

A read-only breakpoint at1294B6 now records expected/completed action counts
and elapsed milliseconds before the native completion function. Bounded
129499..1294B6 tests prove that incomplete counts wait through10000ms and
advance at10001ms, while matching counts advance immediately. This does not
change client counters, time or control flow.

Run `native-player-animation-completion-20260921-01` repeats same-group
attack/retaliation: expected2, completed1, elapsed10021ms, timeout_fallback=true.
Earlier HP and world-return results remain valid for their narrow contracts,
but must not be represented as naturally completed animation evidence.

Native114389 compares logical83 byte3 to the current batch group. Equal groups
enter116AE0; different groups disable queue processing and defer the next
record. A bounded regression executes both branches. The diagnostic emitter
now uses group0 for player attack and group1 for hostile retaliation, keeping
all damage authority in the existing C++/Lua transaction.

Fresh run `native-player-animation-completion-20260921-02` observes two first-
round completion decisions: expected1/completed1 at1988ms and3025ms, neither
using timeout fallback. Both precede the second-round grant, and the second
HP exchange succeeds. This qualifies natural native batch completion for the
first attack/retaliation pair, not screen presentation or completion of the
second pair (the harness still stops at its HP receipt). The evidence test
retains both the failed simultaneous grouping and corrected sequential groups.

## Two complete native animation rounds

The observer now waits beyond the final HP receipt for all requested animation
batches. On the final completion decision it observes1294C7, after the real
129610 finalization call returns. A run using any native timeout fallback is
reported separately as NATIVE_SOCKET_ANIMATION_TIMEOUT_FALLBACK, not success.
No native instructions, time values, counters or finalization returns are
fabricated by this observer.

Run `native-player-animation-full-rounds-20260921-01` reaches
NATIVE_SOCKET_ANIMATION_ROUNDS_COMPLETED. Four successive native completion
decisions have expected1/completed1 and elapsed2027,2997,2041,3002ms; every
timeout_fallback is false. Sequences537,544,584,595 precede finalization-return
sequence596. The second HP exchange was observed before the final completion.
Server logs show one next-round grant and no world-policy rejection.

The fourteenth regression checks both rounds, all four completion counts,
absence of fallback, ordering through finalization return, and server policy
acceptance. This expands the native diagnostic acceptance beyond the earlier
HP-only endpoint. Actual on-screen presentation, normal UI input, final control
receipt after the fourth finalization, skill execution and broader gameplay
remain outside this run's proven scope. No production promotion is implied.
