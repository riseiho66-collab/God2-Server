# Battle transport continuation, 2026-09-19

Owner priority: connect actual combat, not merely decode records. This change
removes the proven basic-attack input gap, but does NOT complete a battle.

## Action0B continuation, 2026-09-20

### Bounded skill staging follow-up

Session now withholds a batch ending in a kind-0 skill continuation until a
matching terminal record arrives, including across frames and TCP reads. No
prefix callback occurs while that sequence is incomplete. Its records must
share actor, side, context and selection byte using the same predicate as the
offline sequence codec; opaque byte3 and target order/duplicates are preserved.
Non-skill interruption and a14th continuation are rejected. Fourteen records
ending in a terminal remain accepted. Full available input is still structurally
validated before policy is invoked. Records remain typed, ordered records, not
authorized casts or damage results.

Pending staging is session-owned, capped at8192 total held records, cleared on
close/failure and subject to a fixed five-second steady-clock deadline. These
are conservative transport protections, not recovered gameplay constants.
Continued arrivals do not extend that deadline. Already-completed sequences
held in a preceding batch prefix do not reset it when rechecked. Finishing the
pending sequence clears the deadline; a new pending sequence gets a new one.
Leaving InBattle is checked on further input and again before the game callback.
Battle epoch/turn identity and replay protection remain unimplemented: leaving
and re-entering the same state alone is NOT sufficient identity protection.

Socket tests now exercise split two-frame sequences, header drift, interleaved
ticks, incomplete sequence overflow, nonbattle transitions, a fixed deadline
despite additional continuations, the native14-record maximum and sequential
casts. Invalid pending input includes an otherwise-valid movement prefix to
prove no partial callback. The timeout case also includes an already-complete
skill prefix to guard against accidental deadline renewal during rescanning.

Application still has no battle policy, original damage/cost formulas or live
client battle acceptance. The previous raw-record-only state below is chronology;
the coverage audit now reports runtime_sequence_assembly=true, while retaining
TRANSPORT_ROUTE and application_policy_installed=false.

Verification: native skill/coverage tests25/25 pass; the broader staged-session
CTest5/5 passes before final timer cleanup. The final Release build passes and
dedicated session_skill_sequence/network/dispatcher/world-record tests4/4 pass
in15.39s (sequence suite14.61s). Final source-pin coverage13/13 also passes.
The new sequence suite is separately registered so future checks need not rerun
unrelated handshake/movement cases. Completion explicitly cancels the old
staging timer before restoring normal idle policy, including when idle policy
is held. This is not a live current-client battle acceptance result.

### Skill record transport follow-up

The world grammar now also carries `RecoveredSkillCommand::Record` for the
already-qualified kind-0 action03/83 subset. The existing codec is reused;
skill records cannot alias basic attacks or control requests. Session includes
them in the batch-wide InBattle gate and forwards owning typed records to the
optional game-executor callback. The movement-only Application still rejects
them, with no partial movement commit. No casts or damage were enabled.

This is RAW RECORD transport, not sequence assembly: a continuation can arrive
in another frame/read and is not an independently authorized cast. The future
Application battle policy must buffer a bounded session-owned sequence, reject
interruptions/timeouts/replays, call `parse_sequence`, and establish caster,
target, resource and turn authority before mutation. There is no such policy
installed today. Synthetic test callbacks only verify transport; their replies
are not original combat outcomes. Unknown actions/malformed fields still fail
the whole available batch.

Added coverage exercises both actions through every nonempty TCP split,
coalescing, nonbattle states, pre-world-tail rejection, bad checksums, policy
failure and movement-only rejection. The native builder also generates lengths
1..14, checked byte-for-byte through the formal world decoder, including atomic
rejection of truncated suffixes. The C++ batch fixture covers byte mutations
and retains skill continuation flags and opaque storage without normalization.
The expanded four-action socket suite exceeded its old90-second test timeout;
its test-only limit is now180 seconds. Runtime timeouts are unchanged.

The dated action1/0B-only conclusions below are retained as chronology. The
coverage audit now classifies skills as TRANSPORT_ROUTE, explicitly with
runtime_sequence_assembly=false and application_policy_installed=false.

Verification after integration: Release god2-server and test targets build;
focused CTest5/5 passes in123.16s (expanded Session111.34s). The new native
skill-to-world sequence test passes for all14 lengths, and protocol coverage
audit13/13 passes after inspecting/re-pinning the changed Session and world
grammar. No current-client battle E2E, database mutation or formula was claimed.

The formal parser now has a distinct `ControlRequest` wrapping the lossless
common fields. `parse_control_logical` accepts exactly action0B; the existing
basic parser still accepts exactly action1. This follows current producer
115AD8 -> 118E50 -> 132E0, not a guessed control acknowledgement. The native
action0B branch bypasses the action1 grant gate; it does not establish server
turn advancement or any authoritative control meaning.

WorldRecords preserves both types in order. Session requires InBattle for
either type before any batch callback. The default movement-only Application
still rejects both. No gameplay callback, synthetic success reply, state
transition, damage/default formula or configured DB mutation was added.

Native integration now has six tests, including428 action0B combinations and
the original90 basic-attack cases. It covers all15 actor positions, four mode
combinations, poisoned opaque bytes, context DWORD extremes, both target masks,
empty/full masks, a maximum-size batch, truncation and skill/continuation
rejection. These execute current native code and compare to the formal C++
parser; they are not live-client battles. The Session regression now runs its
split/state/policy suite independently for each action. Coverage audit13/13
passes and classifies both routes as TRANSPORT_ROUTE only.
Final main verification: Release build succeeds and focused CTest11/11 passes
in98.28s. Session's two-action socket suite passes in70.27s; the native transport
six-test suite passes again in11.48s. Full original-client E2E remains untested.

The older action1-only verification below is chronology.

## Formal route

`RecoveredWorldRecords` now owns a `RecoveredBattleCommand::BasicAttackRequest`
variant. The current 17-byte C2S35/action1 parser is reused without changing
its native-qualified subset or interpreting opaque fields. Apart from the
new distinct action0B path, other actions including skill continuations remain
unsupported by this dispatcher.

The real Session socket path validates authenticated character/world-tail
state, complete recovered envelopes and the entire available logical batch.
It then posts owning records to the serial game executor. If any record is a
basic attack, `SessionState::InBattle` is required before invoking any handler.
This is a conservative server safety gate, not recovered turn/actor authority.
An attack in an invalid state prevents prefix operations from reaching policy.

The existing optional `world_records` callback owns actual battle/participant,
target, replay and transaction validation. A null result or exception rejects;
nonempty responses must be valid recovered frames. The default movement-only
Application still rejects combat before movement can commit. No automatic
transition to InBattle, original battle initialization, damage, deduction,
reward, persistence or fixture BattleHandler fallback was added.

## Verification

- Real C++ Session loopback tests pass all19 nonempty wire split positions,
  coalesced attacks, preserved fields, five nonbattle-state gates, pre-tail
  rejection, malformed checksums/actions, policy rejection/exception and
  movement-only rejection. Synthetic responses and participant state are
  test-only, NOT an original encounter or damage result.
- 90 unchanged original-builder executions produce C2S35 records that survive
  the formal typed decoder byte-for-byte. Original missing-selection guard
  emits no skill record; a produced skill record cannot alias a basic attack.
- Independent verifier added3 black-box tests /27 cases for combined target
  limits, unsupported actions in mixed batches and maximum envelope bounds.
- Targeted CTest4/4, native-builder integration2/2 and independent verifier3/3
  passed. Protocol coverage audit13/13 passes with the source changes pinned.
- Final Release build and selected CTest54/54 pass in160.51s; the five older
  artifact/gate/environment suites are excluded, as in the preceding round.

The native source is the current mapped image with SHA256
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
No retired corpus supplies this route. No configured DB was changed.

## Completion remains open

Battle entry/participant construction, native turn progression, authoritative
original damage/resource formulas, outcome records and battle exit must still
be recovered and wired into Application's C++/Lua gameplay path. Original
client E2E acceptance of a complete battle has not been demonstrated. The
coverage status is TRANSPORT_ROUTE, not RUNTIME_ROUTE or CLIENT_ACCEPTED.
