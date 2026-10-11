# Socket-Fed Battle Transition

Run: `artifacts/runs/native-socket-battle-20260920-01`.
Result: `NATIVE_SOCKET_BATTLE_INITIALIZED`.

After actual own-server login/create/select/world initialization, the C++
world handler accepted a solitary native Tick and sent one encoded batch:
logical 82 with two zero DWORDs, followed by 121-byte logical 88 with zero
payload. These are CUSTOM-0009 diagnostic values, not recovered monster stats,
official encounter values or balanced gameplay defaults.

Original client PID 6800 / TID 14004 reached initializer VA 0x5112C0 from the
normal world-loop caller, return VA 0x46583B. Battle object was 754016288.
Entry ESP 1705948 became 1705956 on return, EAX=1. The debugger observed this
call/return; it did not redirect execution to the initializer. The existing
login diagnostic still invokes native UI command handlers as documented.

The diagnostic branch is default off, requires loopback, recovered movement
and a database named diagnostic-accounts.db. Harness supplies a unique isolated
run database. One batch is allowed per authenticated session and tracking is
removed on disconnect. No server-side InBattle binding, attack rules, actor
stats, rewards or production database modifications are performed.

This closes socket-fed original world-to-battle initializer return with this
specific diagnostic batch. It does not prove that 88 was consumed after return,
that participants render, that controls are enabled, or that a player can attack.
Next: continue the same live transition into battle dispatch with explicit
participant construction and qualified controls; never combine old offline
actor tests with this run into a fictitious playable-battle claim.

Verification: complete Release build; config, recovered_world_service,
recovered_battle_service and recovered_battle_bootstrap CTests passed. Live
artifact regression checks exact caller/return, ABI, process/thread and one
server emission. No official endpoint was contacted.

## Continuation: Timer36 Rejection Resolved, 88 Still Pending

Run `native-socket-vitals-20260920-01` continued past initializer return but
the server rejected a C2S frame. Private decoded fixture packet-0472 is
`0c00360000000001000000d7`: logical 36 followed by two raw DWORDs 0,1.
Native RVA 117B0 reads the timer object's network pointer, then at 117C3 queues
exactly eight bytes from object+84 with opcode36 and flushes at117D7.
11780 enables this timer path and 115D0 initializes its opcode field to36.
These are producer/layout findings, not an attack or encounter-ready contract.

RecoveredWorldRecords now preserves the eight opaque bytes as TimerNotification.
Ordinary world policy rejects this record. Only CUSTOM-0009 after its one-shot
transition accepts the exact observed payload 0,1 without mutating gameplay
state or inventing a response. Other values/states remain rejected.

Fresh run `native-socket-vitals-20260920-02` accepted two such notifications,
continued normal Tick traffic, and stopped cleanly at the bounded deadline.
The socket-fed 88 receiver did not fire. That result closes the Timer36
disconnect, NOT battle vitals consumption or playable battle. Next investigate
how live battle network input reaches its internal queue and start gate; the
older offline probe populated that queue explicitly and does not prove this.

## Socket Queue And 88 Receiver Closed With Deferred Timing

Run `native-socket-queue-20260920-01` observed the original battle dispatcher
running but did not observe forwarding of the early coalesced 88. This does
not by itself identify which initialization operation lost or bypassed it.

For run `native-socket-queue-20260920-02`, CUSTOM-0009 sent 82 alone, then sent
88 once on the first subsequent exact Timer36 payload 0,1. This is a diagnostic
timing experiment, NOT proof that Timer36 is an official battle-ready message.

Observed same-process/thread order: normal battle initializer return, native
network forward RVA1195B1 with opcode88, dispatcher RVA1140C0, receiver
RVA118A90, receiver return. Native input was exactly 88 plus 120 zero bytes.
ESP1705796 advanced to1705804, EAX1, counterFFFFFFFF became0. Result is
`NATIVE_SOCKET_BATTLE_VITALS_CONSUMED`; no queue or client state field was
patched. Previous claims of pending88 are superseded only for this deferred
diagnostic sequence, not for the early coalesced ordering.

Next gap: socket-fed explicit participants and control grants, then actual
outbound attack and server response. Zero vitals do not certify actor rendering,
combat balance, skill formulas, native stats or a playable encounter.

## Deferred Participants And Grant (2026-09-21)

The first participant attempt (`native-socket-participants-20260920-01`)
rejected Timer36 because a fresh client sent raw DWORDs 0,0x1F04667D instead of
0,1. This disproves the earlier constant-value restriction. The decoder still
retains eight opaque bytes; the diagnostic branch now admits them only after
its transition, without interpreting them as gameplay values. Normal world
policy remains unchanged and rejects unsupported notifications.

`native-socket-participants-20260921-01` completed with
`NATIVE_SOCKET_PARTICIPANTS_GRANTED`. Additional opt-in
diagnostic_battle_participants uses existing bootstrap/vitals codecs to send
two monster-catalog test identities at positions0/14, three scalar vitals,
bulk88, and grant86/5. It does not yet project the persisted player appearance.

Same-process ordered observations: native initializer return, both original
identity handlers, bulk88 return, grant handler and successful RET4 return.
Actual actor memory: friendly currentHP100,currentMP50,maxHP120,maxMP80;
enemy currentHP150,maxHP150 with MP fields unchanged at CDCDCDCD. Local
selectors become00FF and first-grant flag becomes1. These are synthetic test
vitals, not official monster data or approved balance. Enemy MP remains unset
because this diagnostic sends no enemy-MP field; never read its fill as a stat.

Config and bootstrap CTests pass, including participant flag dependency and
exact batch boundaries. Next acceptance is original attack emission and an
authoritative server result; rendered actors, mouse input, damage rules and
production promotion remain unverified.

## Original Attack Reaches The Socket

Run `native-socket-action-20260921-01` continues the same initialized, granted
client through its original RVA118E50 basic-action entry, using the existing
immutable diagnostic call page targeting position14. This is an explicit native
function call, not physical pointer-input acceptance. EAX1, original stack and
page integrity pass; control fields become [1,0,0], consuming the first grant.

The actual successful send and independently captured codec plaintext prove a
37-byte frame containing TWO 17-byte logical records: 35/01 followed by35/0B.
The basic attack has actor0, side0, masks[0,1], context0. Its final parameter
bytes contain unwritten native data and must not be treated as a gameplay ID.
Private packet-0496 artifacts preserve exact wire/plaintext and checksum result.

The server rejects the combined world batch because no authoritative battle is
bound and Control0B semantics remain unsupported. This is NOT damage acceptance
or a playable attack. Next qualify the native producer/consumer meaning of0B
and transaction boundary, then bind isolated C++ Battle plus Lua rules without
silently ignoring the control record or marking a fabricated result native.

## First Authoritative Diagnostic Damage Round Trip

`native-socket-damage-20260921-01` completed with
`NATIVE_SOCKET_DIAGNOSTIC_DAMAGE_APPLIED`. CUSTOM-0010 binds an in-memory
C++ Battle to the authenticated selected character before sending the grant.
The original client emits35/01 +35/0B. The existing RecoveredBattleService
validates actor/side/context/targets, calls Lua combat_damage, validates its
encoded reply before committing state, and sends86 HP update.

Actual original117230 entry receives target14,max150,current132; after RET4,
actor currentHP is132 and maxHP150. Friendly remains the synthetic fixture;
enemy MP is not qualified client data. This is real socket-fed client memory
update, not a native formula, visible animation or complete playable encounter.

Original local Control0B producer conditions were already documented in
current-battle-command-gate-20260919.md. The diagnostic now explicitly handles
one authorized completion notification, in the same batch or after the action,
without treating it as an official server turn advance. Duplicate/premature
control, replayed action and malformed response are rejected; response failure
does not commit HP or consume the diagnostic action receipt.

Production remains unchanged. Next: visible attack/result behavior, real
player identity projection, repeated round admission, monster retaliation,
victory/exit and persistence, plus custom balance qualification.

## Atomic Diagnostic Retaliation

Run `native-socket-retaliation-20260921-01` completed with
`NATIVE_SOCKET_DIAGNOSTIC_RETALIATION_APPLIED`. CUSTOM-0010 now optionally
stages a trusted server-controlled retaliation after the player's action.
Both Lua computations and both encoded replies complete before the bound
Battle snapshot/RNG is replaced. No extra client authority is granted.

Original HP receiver returns prove enemy150->132 then friendly100->88;
friendly MP50/maxHP120/maxMP80 remain unchanged. Both events occur in the
same initialized/granted/attacking client process and thread. Client fields
were read, not patched. The diagnostic still grants only one player action.

Tests inject a failure in retaliation encoding and verify neither HP nor
revision commits, then retry successfully. Duplicate actions are rejected;
a killed retaliator cannot act even if another enemy remains alive.
This does not qualify native initiative, official formulas, repeated rounds,
visual attack effects, encounter outcome or production balance.

## Trusted Diagnostic Rearm Preparation

RecoveredBattleService now exposes rearm_diagnostic only as a trusted C++
operation; no incoming packet invokes it. It requires the same session/account/
character, InBattle state, active battle, matching internal revision, living
actors and completed action/control receipts. Repeated or premature rearm is
rejected. The diagnostic socket route remains single-round until actual next
grant/attack is qualified; this change alone is NOT live multi-round acceptance.

Domain tests execute three explicitly reauthorized rounds: enemyHP100->82->64
->46 and friendlyHP100->88->76->64, with revisions1->3->5->7. They also test
stale revision, wrong account, missing control, duplicate rearm and finished
battle rejection. These test values differ from the live enemyHP150 fixture.

Known limitation: the native command context comes from battle+3C, not a proven
per-turn nonce. Identical attacks after a new grant cannot currently be proven
to be intentional input versus replay. Internal revision checks protect the
trusted operation but do not invent a wire-level replay guarantee.

## Actual Bounded Two-Round Diagnostic

Run `native-socket-two-rounds-20260921-01` records two complete sequences in
`socket_completed_rounds`, not just the single aggregate outcome label.
In the same client process/thread, original grant/action/HP receivers complete
twice: enemy HP150->132->114 and friendly HP100->88->76. Friendly MP remains50.
Application rearms once after the action/control receipts, sends current
friendly values in88 and another86/5 grant. Config accepts only1..2 rounds;
two requires diagnostic participants. No native turn policy or balance claim.

The first run's second `WORLD_ENTRY_CANDIDATE_SENT` line was a logging bug:
Session classified any40-byte outgoing buffer as world entry. The second-round
HP response has that length too. Write queue entries now carry explicit
world-entry provenance set only by the character-selection response path.
The original artifact is preserved; do not count its erroneous line as an
additional world transition. A fresh run must qualify the corrected logger.

Fresh run `native-socket-two-rounds-20260921-02` repeats both rounds with the
same cumulative HP values, exactly one world-entry log and one next-round
grant. The regression now targets this new artifact. Debug config,
session_state, session_battle_service and recovered_battle_service tests all
pass; the Python prefix/live evidence suites pass33 tests. No owned client,
debugger or server process remained after cleanup.

Regression checks require exactly two ordered grant/action/damage/retaliation
chains, receiver return PCs/stack, cumulative HP and one server rearm. These
remain native-function diagnostic actions, not normal UI or rendered battle
acceptance. Player projection, skill/result animation, outcome/exit,
persistence and balance qualification are still open.
