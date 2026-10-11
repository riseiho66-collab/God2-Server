# Player battle appearance prerequisites

## Scope

The current own-server diagnostic uses catalog monster identities for both
friendly slot 0 and hostile slot 14. It is not normal-player battle acceptance.
No production settings, formulas, account data or client binaries changed here.

Pinned mapped image SHA256:
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
Addresses below are RVAs (image base 400000).

## Live prerequisite observation

Run `artifacts/runs/native-battle-player-prerequisite-20260921-01` ended with
`NATIVE_SOCKET_PARTICIPANTS_GRANTED`. Read-only snapshots before native 115C90
in events 486/487 recorded both actor render handles at actor+1A as signed -1.
Both actor+DB0 metadata regions were FFFF followed by 54 zero bytes. The local
player identity at battle+48 was 1. These are initial states of this fixture,
not claims about every battle or every client build.

Static inspection of the 1C variant2000 branch at 116149 shows that it reads
the existing actor+1A handle, copies 56 metadata bytes and tests the handle at
116166. A -1 handle leads to logging and return0 at 1161B1. Merely changing the
fixture identity variant cannot create the missing renderer in this branch.
Metadata is written before the return; later consumers remain to be traced.

## Newly executed native edges

The original subtype dispatcher 114464 indexes table1146CC. Entry4 is1144C8,
which calls1177C0 with the record at battle+A9E9CB1 and ECX=battle.
The test now executes the outer logical86 switch at114332, this intact subtype
dispatch and call, and stops at1177C0. The original15840 length helper returns
17 for86. This does not by itself certify the transport frame or queue route.

The original1177C0 prefix extracts position from record+1, computing side as
position/14 and slot as position%14. Record+2 selects a mode:

- 0: branch11890B, not executed beyond its entry.
- 1 with WORD[record+C]==0: branch1182B9, not executed beyond its entry.
- 2: branch118A79, not executed beyond its entry.

All28 positions across these three modes pass bounded original instruction
execution. No native callee is replaced or given a fabricated return value.
Static inspection of1182B9 onward shows actor lookups for component types
0,3,2,1 and copies from record+3/+7 into temporary metadata. Resource creation,
component meanings and required values are not yet qualified.

Other static handle-store leads:121179 (calls1AFE0),121513 (calls2F510),
1219A0 (calls1AFE0). The124291 store belongs to a type5 component retrieved by
1241A0 and is not proof of the main player renderer. These leads must not be
turned into packet fields by guessing.

## Verification and next step

`python -B -m unittest discover -s tests/research -p test_current_battle_player_appearance.py -v`

Four tests pass: native subtype routing,84 position/mode cases,256 packed-byte
argument cases, and persisted live prerequisite evidence. The existing20 tests
in test_current_battle_entry.py also pass. This is not rendered, normal-input or production
acceptance. Next trace1182B9 through the real component creation calls, identify
the appearance input's authoritative character-data producer, then qualify the
outer subtype4 frame and test appearance-before-identity on our own server.
Keep CUSTOM participant stats and formulas isolated throughout.

## Main component creation arguments

Two additional independent instruction islands execute without replacing any
callee. They do NOT constitute continuous execution of the entire handler.

- 118527..118555 extracts record+3 low/high nibbles and record+4 low5 bits.
  The call54E50 receives side, an explicitly supplied diagnostic resource-family
  input, low nibble, component0, high nibble, and low5 bits. Register high bits
  are not assumed zero: the byte-sized arguments are compared as bytes.
- 118650..118672 passes the loaded resource handle from actor+24, side, slot,
  component0, record+4 high3 bits, and metadata to1216C0. All256 values of each
  packed byte are exercised (complementary pairs, not all65536 combinations).
- Static inspection of1216C0 shows its first WORD argument must be below200hex
  before actor lookup. This is a loaded resource index, not proof that monster
  identity or player identity may be substituted for it. Actual resource loading
  and renderer construction remain unexecuted by these new tests.

The existing world-appearance producer at68328 copies body+12..19 into the
character's4584..458B. That eight-byte layout is a candidate source to compare
against battle record+3..10, not yet a certified conversion. Current world
bootstrap still preserves unqualified historical resource-selector bits;
copying those would be an explicitly diagnostic experiment, not native profile
projection or production acceptance.

## Own-server appearance experiment

Default-off `diagnostic_battle_player_appearance` now requires the existing
isolated participant/transition gates (loopback, recovered movement and
diagnostic-accounts.db). CUSTOM-0009 records its provenance. It prepends one
17-byte86/4 record with position0/mode1 and copies historical world body12..19
to logical+4..11. Other bytes are explicit zero diagnostic fields. It changes
only the friendly1C identity to the session character ID and variant2000.
Original monster diagnostic output remains unchanged when the flag is off.

`native-player-appearance-20260921-01` reached
NATIVE_SOCKET_PARTICIPANTS_GRANTED. Before friendly1C, the original client's
actor handle was125 (previously -1); metadata+2E..35 contained
0180016001603100. Enemy handle remained -1 before its monster identity path.
The player identity matched local identity1; native grant returned1, and
friendly HP/MP storage was100/50 with maxima120/80. This establishes an actual
socket-driven component creation prerequisite, not visual acceptance.

`native-player-two-rounds-20260921-01` repeated that creation successfully but
ended EVENT_BUDGET_END. The native118E50 diagnostic call returned1, controls
remained010000000000000000000000, and no completed round/outcome was observed.
Server log ended after the bootstrap with no battle command handled. This is
NOT two-round success. The next frontier is the player command staging/sending
path, including118FBF onward; do not restore monster identity merely to obtain
a green battle result. No normal-input/rendered acceptance is claimed.

Verification: C++ server/bootstrap build, recovered_battle_bootstrap and config
CTest pass. Python regression retains both successful creation and the failed
two-round attempt, without reclassifying the latter. No production enablement,
balance approval, gameplay-formula recovery or saved-profile fidelity follows.

## Send-queue clarification

Run `native-player-two-rounds-20260921-02` added read-only observation at the
action return and increased the player-only event ceiling from1000 to4000.
It also ended EVENT_BUDGET_END, but exposed the earlier diagnosis as incomplete:
the action DID enter the native network queue (active1,17 logical bytes).
Its first13 bytes were35000100000000010000000000: actor0, basic1, side0,
enemy mask1, context0. The final DWORD is the documented unwritten parameter,
not an authentication token or a value to normalize in the client.
The same logical record appears in `crypto-private/tx-input-0500.plain.bin`.
Server logging shows session4 closed with `Recovered world policy or response
rejected` shortly afterward. Therefore this is not merely a missing native
send. The queued snapshot contains no control0B, but that alone is NOT proof
of the server rejection cause (the service supports split action/control).

Next: isolate the precise server admission or response-validation failure for
this recorded basic attack. Preserve the native bytes and existing ownership,
state and target checks; do not weaken them based on the symptom. This run
proves neither successful damage nor completed rounds.

## Admission fix and real player damage

The prior rejection was earlier than the attack: tx-input0490 in run02 contains
`35000b0000000000000000000000000000`, a standalone zero-mask control0B.
The admission-instrumented run `native-player-admission-20260921-01` confirms
InBattle state5, a sole record of variant index6 (ControlRequest), and policy
rejection before the basic attack. Thus the basic attack was not the rejected
record. Its standalone recorded bytes pass the C++ service, Lua and atomic
attack/retaliation test without changing the unwritten final DWORD.

Only CUSTOM-0009 player diagnostics may now admit that exact zero-field
pre-action control once per battle. It requires the existing session/account/
character/side/context binding, no previous action/control, and a sole record.
It returns no payload and changes no HP, MP, revision or round readiness.
Duplicate, wrong-context, mixed-batch and ordinary-policy cases are rejected.
It does not replace the post-action control receipt or relax target validation.

Fresh run `native-player-two-rounds-20260921-03` proves the resulting first
exchange on the original client: friendly is player variant2000 with a created
renderer; hostile HP150 ->132; friendly HP100 ->88. Both native117230 receivers
return and their actor storage matches. No policy rejection or disconnect
occurs during the observation window. The run ends HARD_TIMEOUT with exactly
one observed exchange, not two-round success. No next-round grant was logged.
The remaining frontier is the native post-action control/animation timeline;
do not weaken the required completion receipt simply to rearm the server.

Damage remains CUSTOM-0010 and diagnostic stats remain CUSTOM-0009. Native
rendered animation, normal input, production balance and original formulas are
not established by these memory/receiver checks. The existing output key
socket_completed_rounds denotes observed HP exchanges, not certified native
round completion; this run's absent next grant is retained in regression.

## Player two-exchange completion snapshot

Read-only run `native-player-control-gate-20260921-01` observed after retaliation:
result_received0, manager_event0, control_sent1, bulk_seen1, counter0,
completed_counter0, target_count1. Bounded execution of original115A59 with
this exact snapshot stops115ADD without calling118E50: the control_sent latch
is the rejecting predicate. Original88 tail518BC5 clears that latch.

CUSTOM-0009 now appends a current-cycle88 after the diagnostic retaliation's
HP result, encoded before the staged C++ transaction commits. It contains the
current trusted actor HP/MP and counter=granted diagnostic round-1. This is a
documented diagnostic ordering, NOT recovered official combat timing. No
client state is directly written. The existing required post-action receipt
still gates rearm; the initial zero-mask notice cannot satisfy it.

Fresh run `native-player-two-rounds-20260921-04` returns
NATIVE_SOCKET_DIAGNOSTIC_RETALIATION_APPLIED with two observed exchanges:
hostile HP132 then114, friendly HP88 then76. Native player variant2000 and
created handle are retained. Server logged exactly one next-round grant,
after handling the first exchange's control. No policy rejection was logged.
Python regressions retain all failed predecessors and this successful result.

This does not qualify83/84 action animations, normal input, player terminal
return-to-world, battle persistence, native damage formulas or production
balance. Those remain required work; the application stays default-off and
restricted to the isolated diagnostic database and loopback.

## Player terminal ordering and world return

Baseline `native-player-terminal-20260921-01` reached native outcome/cleanup
and world return, but the server retained Finished/InBattle while waiting for
the separate post-action receipt. The premature89 prevented that receipt's
normal control path. The subsequent world context record (variant index9)
was correctly rejected in battle state; the run ended HARD_TIMEOUT.

CUSTOM-0011 player diagnostics now stage terminal damage plus the current88
snapshot before commit, withholding89. Only after the authorized late control
has been accepted and release_finished_diagnostic succeeds is the preencoded
zero-award89 appended. Output capacity is reserved before server release.
The older non-player diagnostic remains unchanged. No new client opcode,
direct flag overwrite, reward mutation or relaxed completion test was added.

Fresh `native-player-terminal-20260921-02` returns NATIVE_MOVEMENT_PATH_COMPLETED:
enemy HP0 receiver sequence512; outcome527; outcome panel529; native battle
return546; world loop548; movement completion615. Three original path steps
and their ACKs finish at(18,12), motion_state0. Read-only SQLite confirms
recovered_positions row(1,2,15,18,12,3). Exactly one server battle release was
logged, with no policy rejection. Client identity remains player variant2000.

This proves the isolated player diagnostic death/outcome/world/movement path,
not normal UI input, full83/84 combat animations, persisted combat stats,
rewards, quests or production balance. Character/position persistence has
evidence; battle HP/MP persistence still does not. Regression retains the
failing predecessor and checks actual native sequence/state/DB evidence for
the successful run rather than only its result label.
