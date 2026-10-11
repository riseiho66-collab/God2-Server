# Full Native Battle Initialization In An Isolated Client

## Result And Scope

`artifacts/runs/offline-battle-init-20260920-01`, PID2004/TID14248, executes
original1112C0 through RET4 with EAX1. Observed ordered checkpoints are1112C0,
11132F (owner bindings),11151B (original text initializer returned) and the
RX diagnostic thunk's return trap. No helper return or battle pointer is patched.

The fresh client is the original-hash, guarded offline working copy. The mode
`--probe-native-battle-init` is exclusive with constructor/loop modes, requires
local-world entry and stays off by default. It calls the original initializer
using existing application/world/owner/catalog pointers. Descriptor layout is
backed by the executed655E0 producer test. The event context is explicitly
0x3EC zero bytes in an immutable RX lab page, not a captured official event.
Normal world transition leading to this call is not executed by the probe.

## Checked State

World268574752 owns battle716189728. Original111326 binds battle+14 to
world+1539683C=624658524. The pointer is checked at the binding checkpoint and
after return. EntryESP1709460 is restored exactly; the call entry has ESP-8.
Final actor selectors+51/+52 areFF/FF, counter A9E9C64 isFFFFFFFF, and
wait/first-grant/second-grant/0B-latch fields are zero. The entire diagnostic
code/descriptor/event page remains byte-identical on return.

The existing entry/timer interventions are restored, the executable disk hash
is unchanged, and no transport boundary event occurred. PID2004 was confirmed
absent after the bounded runner exited. The probe does not create a listener,
send to an official endpoint, modify production databases or recover stats.

## Reproduction And Remaining Work

```powershell
python -B -m tools.strike_lab.current_offline_client_run --run-id battle-init-NEW --timeout 90 --enter-local-world --probe-native-battle-init
python -m unittest tests.research.test_current_offline_battle_init tests.research.test_current_offline_monster_live -v
```

Tests inspect descriptor ABI, diagnostic bounds, live stage PCs/thread/stack,
role binding, control reset and restoration. The earlier standalone88 failure
was an incomplete-initialization diagnostic, not evidence of a malformed88.
This run closes full1112C0 return with zero diagnostic event only. It has not
yet continued to88, normal actor creation, player input or actual server traffic.
The next live test must keep this initialized process and validate88 there;
do not combine evidence from different processes into a claimed E2E run.

## Same-Process Initialized88 Receiver

Run `offline-initialized-vitals-20260920-01` (PID11124/TID8988) now executes
the full1112C0 initializer, then invokes118A90 on the same battle object in
the same process. `--probe-native-battle-init --probe-native-vitals` enables
this opt-in sequence; the initializer-only mode remains available unchanged.
No separate monster/text-only initializer is run in this mode.

Observed ordered receiver checkpoints:118A90 ->12D360 ->116AC0 ->lab return.
Original118A90 returnsEAX1 and restores entryESP1709460. Its local role pointer
matches the one originally bound by1112C0. All168 actor pointers are captured
after initialization and remain identical before the receiver call.

The121-byte diagnostic88 carries currentHP1000+i and currentMP50+i for14
side0/type0 slots, with other bytes zero. These values are supplied by this
test, not recovered stats, balances or a network capture. Before the call,
all inspected current/max fields contain native initialization fillCDCDCDCD.
Afterward exactly those14 currentHP/MP pairs match the input; every maximum
and all14 enemy-side current/max pairs are unchanged. Original cleanup returns
normally. The immutable input is re-read and checked; controls before/after
are stored as raw hashed snapshots.

The process exited; PID11124 was confirmed absent. Entry/timer interventions
were restored, disk executable unchanged, no transport boundary was hit.
Thirteen live-probe regression tests pass, including same PID/TID/order,
PC/stack checks, actor ownership, exact updates, unchanged maxima/enemies and
snapshot hashes. This supersedes the missing standalone receiver return, but
NOT the requirements for a socket-fed dispatcher, actual displayed participants,
player attack, combat formulas, balanced custom rules or own-server E2E.

```powershell
python -B -m tools.strike_lab.current_offline_client_run --run-id initialized-vitals-NEW --timeout 90 --enter-local-world --probe-native-battle-init --probe-native-vitals
```

## Native Queue And Battle Loop To Dispatch Return

Run `offline-battle-dispatch-20260920-01`, PID17584/TID18220, extends the same
initializer sequence with the original11D4E0 queue writer and115770 battle
loop. The lab supplies only the explicit121-byte diagnostic88 and a writable
stack byte for the loop's output argument. No battle state/grant/queue index
is directly overwritten by the observer. Normal115770 startup sets the
dispatch-enabling state; original1140C0 performs its own animation scan,
queue peek, opcode dispatch,118A90 receiver, cleanup and final return.

Ordered native checkpoints after initialization:
11D4E0 ->115770 ->1140C0 ->118A90 ->12D360 ->116AC0 ->115A51.
The final checkpoint is the caller after1140C0's RET8, not115770's return.
DispatchESP1709344 becomes1709356, exactly+12. The original5120-byte ring
changes from read/write0/0 to0/121, then back to0/0 with pointer and capacity
unchanged. Exactly14 friendly currentHP/MP pairs change; enemy values and
all maxima remain unchanged. Diagnostic input is checked immutable.

Run01's historical field `queue_write_eax` actually records EAX at loop entry,
after the lab loaded the115770 target. It is not the writer's Boolean result.
The source now names that observation `loop_entry_eax`; writer success is
established here by native queue contents/indices and eventual consumption,
not by the mislabeled scalar. Existing raw evidence is not rewritten.

Fourteen regression tests pass. Entry/timer interventions restore, disk EXE
is unchanged, no transport boundary is hit, and PID17584 is absent after exit.
This supersedes the missing live outer dispatcher return in the earlier scope.
It does not prove socket delivery, visible combatants, continued battle frames,
automatic0B flushing, ordinary attack/skill grants, actual damage, or gameplay.
The process is intentionally stopped after the first qualified dispatch return.

```powershell
python -B -m tools.strike_lab.current_offline_client_run --run-id battle-dispatch-NEW --timeout 90 --enter-local-world --probe-native-battle-init --probe-native-vitals --probe-native-battle-loop
```

## Two Resource-Backed Participants Through Original Dispatch

`offline-battle-actors-20260920-01` (PID16412/TID recorded in raw events) uses
the additional opt-in `--probe-native-battle-actors`. It prepends the existing
two45-byte diagnostic1C identities (positions0/14, generation1/area1/scene0/
ordinal1, variant0400) before88. The native queue contains211 bytes and the
unchanged original battle loop dispatches the records, then returns from its
first1140C0 invocation with the queue empty. No observer invokes115C90 directly
or manually creates renderer handles in this mode.

At118A90 entry, before88 has executed, the actual actors at slots0 and14 have
native WORD1A handles124 and136. CompleteECC-byte actor snapshots are saved
with hashes. The test checks that their vital fields match the separately
captured pre88 baseline. Native1C initialization changes some vitals, so the
bulk writer comparison deliberately uses this new baseline, not pre1C fill.
After88, all14 side0 currentHP/MP pairs match the explicit diagnostic values;
all maxima and all enemy-side vitals remain unchanged from the pre88 baseline.

These raw1000+i/50+i test values are parser probes, not balance-approved stats;
in particular1C's side0 initial maxima may still be1. This is not a valid
gameplay stat assignment and must not be promoted to production. Identity
selectors/resource handles are also not proof of species combat attributes.

Fifteen live-probe regressions pass. Entry/timer interventions restore, the
disk EXE is unchanged, no transport boundary event occurs, and PID16412 was
confirmed absent. The evidence now includes nonempty native resource-backed
participants under full initialization and dispatch. It does not verify actual
rendered frames, attacks, animation outcomes, authoritative formulas or socket
delivery. Next runtime checks must use valid isolated vitals and verify the
ordinary control grant/attack path before any production integration.

## Bounded Diagnostic Vitals Through Scalar And Bulk Updates

`offline-battle-actors-vitals-20260920-01` (PID18360/TID9068) repeats full
initialization and original queue/loop dispatch with a262-byte sequence:
two45-byte1C identities, three17-byte86 scalar records, then121-byte88.
The scalar records set friendly slot0 HP maximum120/current100, friendly
slot0 MP maximum80/current50, and enemy slot14 HP maximum150/current150.
At the real118A90 entry, before88, the captured fields already equal these
values. The bulk update retains friendly slot0 current100/50 and writes0/0
to the other13 friendly slots. Maxima and all enemy vital fields are preserved.
Enemy MP remains CDCDCDCD; it is unknown, not a recovered zero or usable stat.
Unoccupied slots' maxima remain uninitialized and are not gameplay values.

The original queue progresses0/0 ->0/262 ->0/0, with the same pointer and
capacity. Actual resource handles remain valid; hashed ECC-byte snapshots
match the pre88 field observations. Dispatch returns at115A51 with ESP+12.
Entry and timer interventions restore, the disk executable is unchanged,
no transport boundary was hit, and PID18360 was confirmed absent afterward.
Sixteen focused live-probe regressions pass, including the new sequence and
exact scalar/bulk effects. These tests replay assertions on recorded live
evidence; running the unit suite does not launch another client session.

The historical report's `stat_update_records_supplied` incorrectly says1:
it counted only88, omitting the three86 records. Source accounting now reports4
in participant mode and1 otherwise; the immutable original report is retained.

These bounded numbers are isolated diagnostic inputs, not native monster
attributes and not balance-approved custom production data. This qualifies
the combined native receive sequence, not a socket-fed battle, rendered combat,
an attack outcome, damage formulas or E2E acceptance. The next outstanding
runtime boundary is ordinary86/5 control grant and the actual attack path.

## First Control Grant In The Actual Process

`offline-battle-grant-20260920-01`, PID6344/TID17552, adds an explicit
`--probe-native-battle-grant` option requiring the participant loop. Its279-byte
queue inserts17-byte86/5 (flags1, actor0, other fields zero) after scalar vitals
and before88. The unmodified dispatcher reaches117590 and the original
1177B5 RET4 with the same ESP and EAX1, then enters118A90 and completes the
existing bulk-update/dispatch checks. No observer writes grant or actor fields.
At grant return, waiting/first/second are0/1/0 and actor selectors are0/FF.
The queue returns to empty, interventions restore, no transport boundary is
hit, disk bytes remain unchanged, and PID6344 was confirmed absent.

Important remaining precondition: A9E9C64 remains FFFFFFFF. The previously
qualified115670/115740 guards therefore prevent ordinary attack rearm despite
the successful first grant. This run proves a full live grant receiver return,
not active attack controls, successful action transmission or an attack result.
The timestamp import executes on the existing native/compatibility runtime
path, but this run does not separately breakpoint the OS API entry. The next
trace target is the native producer of the counter; do not patch the sentinel.
The grant is an explicit diagnostic sequence, not a recovered server turn policy.

## Bulk Before Grant: Native Counter And Rearm

The pinned image has direct writes to A9E9C64 in1117EE (initial sentinel)
and118AD2/118BB8 (88 receiver). Existing bulk receiver tests independently
cover the record DWORD at offset1 and the conditional counter update.
The runtime probe now orders1C/scalar86, then88, then86/5; it never writes
the counter itself. All numbers and ordering remain diagnostic test inputs.

Run `offline-battle-grant-20260920-02` stopped with a tool validation error:
the first dispatch returns after88, leaving the17-byte grant queued. This
was an observer expectation error, not an observed client crash. The observer
now records that boundary and lets the original115770 loop continue into its
next1140C0 call, rather than invoking a receiver directly or changing indices.

Run `offline-battle-grant-20260920-03` (PID13692) succeeds. Ring indices move
0/279 ->262/279 ->0/0. After the first dispatch, the next native dispatch calls
117590, enters1121F0 with ECX equal to the battle object and counter0, returns
from117590 at1177B5 with original ESP/EAX1, then returns to115A51. The recorded
grant remains waiting/first/second0/1/0 with actor0/FF. Final HP/MP checks still
pass. Entry/timer changes restore, executable bytes are unchanged, no transport
boundary was hit, and PID13692 was confirmed absent after the run.

This supersedes the missing live first-rearm call and sentinel blocker. It is
not proof that a visible attack button works, that an action packet reaches
our server, or that a combat result is accepted. Those remain next acceptance
boundaries. No production turn policy, monster stat or formula is promoted.

## C++ Construction Path For Initial Readiness

`RecoveredBattleBootstrap::ready_logical` now appends supplied88 and86/5 to
the existing typed82/1C/scalar86 sequence under CUSTOM-0005. It rejects the
FFFFFFFF counter sentinel, inconsistent bulk/current values, missing friendly
MP, nonzero current vitals for absent slots, unsupported grant flags and absent
grant actors. It supplies no gameplay values, preserves opaque input bytes and
does not activate Application routing. The existing bootstrap API is unchanged.
Focused C++ tests cover ordering, framing roundtrip and malformed inputs.
This is a server-side construction capability, not a new live network test:
the complete82-prefixed C++ sequence still needs current-client own-server
acceptance before production emission.

## Disconnected Native Basic Action

`--probe-native-battle-action` is an explicit diagnostic call after the complete
grant sequence. It requires a disconnected native transport object and uses
118E50 with action1, actor0, one target14 on an immutable lab page. It does not
click UI, establish a connection, set connectivity, or grant itself permission.

Run `offline-battle-action-20260920-01` had a tool expectation error: it waited
for132E0, but native disconnected branches skip enqueue. The client returned;
the observer classified this as an unexpected stage. PID17828 was absent after
cleanup. Run02 instead observes1191EE before cleanup and the real final return.
PID10248 reaches118E50 ->1191EE ->lab return with EAX1 and restored ESP, and
waiting/first/second change0/1/0 ->1/0/0 through native code. No helper return
or grant value is substituted. The captured16-byte stack body, prefixed by the
statically proven35 opcode, is `3500010000000001000000000001000000`.
The C++ recovered-battle-command decoder accepts actor0, first-control side0,
friendly mask0, enemy mask1 and context0. Opaque bytes remain opaque; their
observed values are not new protocol constants. No actual wire packet exists
in this disconnected experiment, despite the report field `logical_hex`.

Entry/timer interventions restore, disk bytes are unchanged, no transport API
boundary is hit, and PID10248 was confirmed absent. Regression tests preserve
the stack/return/control evidence and decode the captured body using C++.
This closes the live native builder/cleanup gap with diagnostic arguments,
not UI selection, socket delivery, server admission, combat result or E2E.

## Captured Body Replayed Through The C++ TCP Session

The `session_battle_service` CTest now reads the completed run02 report above
and frames its `action_probe.logical_hex` without regenerating attack fields.
A synthetic loopback peer completes the existing selection/tail exchange,
then receives explicit test-only InBattle admission and a bound diagnostic
battle. Its authorization policy matches native actor0/side0/context0.
The actual Session frame/parser, world routing, RecoveredBattleService,
Lua combat rule and transactional Battle process the replay. A frame missing
its last byte causes no mutation or reply. Completing it causes one revision
increment and one framed86 HP reply, enemy HP100 ->82, friendly MP20 unchanged.
The peer verifies the exact response over its real loopback TCP connection.

Build `god2-tests` and CTest `session_battle_service` pass. The18 damage is an
existing CUSTOM test formula/value, not recovered damage or approved balance.
This adds server-side TCP admission/result evidence for the observed native
body. It does NOT establish that the original client sent a wire packet,
accepted this result, entered battle through production Application, or used
a validated turn/replay policy. The offline report remains explicitly offline;
the TCP replay remains explicitly synthetic, with no production activation.

## Actual Network Prefix Recheck

Run `native-network-recheck-20260920-01` launches the original working-copy
client and existing C++ dual-listener world-entry candidate using apex's
zero-UI prefix mode, MODE_COMPAT and the scoped pagefile-capacity adapter.
The server listens on127.0.0.1:2592 and independent character port54780.
It subsequently drains/stops cleanly. Client PID9676 is absent after completion.

Authoritative milestones: graphics, string tables, Winsock and memory-warning
check passed; socket-created/connect-attempted/connected/first-TX/first-RX,
login, character-screen and world are all false. Last observed network event
is WSAStartup, caller RVA11C82. No packet artifact is produced. The bounded
observer terminates with HARD_TIMEOUT; this is not evidence of a connect failure
or client crash, since no connect attempt was observed. Compatibility restore
reports hr0/written4. The existing runner stops its owned processes at the end
of its configured experiment; no user-operated login was requested.

This fresh real-client result takes precedence over any inference of current
connected playability from offline battle or synthetic TCP tests. The next
network prerequisite is binding and executing the normal login-entry action
without bypassing its protocol/state checks. Increasing the timeout alone
does not establish that prerequisite. The complete native-client battle path
remains unqualified; neither protocol codecs nor this failed prefix promote
custom data/formulas or Application battle routing.

## Normal Login Loop Entry Located

Source review confirms zero-ui-prefix disables enter-game/test-login actions.
The old timeout alone could not identify where normal startup was waiting.
The new opt-in `--observe-login-entry` requires zero-UI mode and observes404DA0
without rewriting client state. It verifies return PC40DF8C and that ECX is
the application-owned pointer at EBP+43C before reading two login state fields.

Fresh run `native-login-entry-20260920-01` reaches that breakpoint naturally:
PID9628/TID6588, application5E00F8, login object0B3F0020, current/previous state
0/0. The pinned DF87 call targets4DA0. Five raw call arguments are recorded;
their meaning is not inferred. Result NATIVE_LOGIN_LOOP_ENTRY_OBSERVED is an
intentional observation stop, not timeout, authentication or a network failure.
Compatibility restore succeeds; PID9628 and listeners2592/54826 are absent
after completion. No connect/send was observed. The regression checks the
original call bytes, runtime event, ownership-check result and scope boundary.
Next: trace the state0 login event/command consumer on this owned object,
not an arbitrary synthetic global or a forced authenticated-state transition.

## Native Menu Command Before Authentication

Pinned code50F5 compares the active handle with login+178CC2 and510A calls
6400 with the native event arguments. Handler6400 takes command3/flags1
through6425 -> AFB0(1), rather than the cancel/state11 branch. This transition
is pre-authentication; it is not a success reply or a recovered credential.

`--probe-login-command` requires the login-entry observation. After checking
the application-owned object, it resumes normal initialization to4F2B, verifies
state0/EBP ownership, and invokes6400 through a bounded immutable owned page.
The arguments are explicit diagnostic event values, not desktop input. It
stops at the function's real return without resuming the login loop afterward.

`native-login-command-20260920-01` returns NATIVE_LOGIN_MENU_COMMAND_RETURNED:
current/previous state1/0, EAX1, restored ESP1706940. Native AFB0 performs the
state mutation; the observer does not write it. Compatibility restoration
succeeds, the owned client is absent and port2592 is no longer listening after
completion. No connect or transmission is certified. Tests cover the thunk,
same-process sequence and prelogin-only outcome. Next boundary is state1's
normal panel initialization and credential-submit consumer, retaining actual
authentication and loopback restrictions.

## Original Loop Completes Login Panel Initialization

`--probe-login-panel` requires the preceding command probe. After its native
return it rejoins the interrupted4F2B loop, without assigning the next state.
The pinned jump-table entry1 targets530B; call5320 invokes67C0. Checkpoints at
5325 and5336 verify the same login object, a nonnegative handle at178CC4 and
the native state1 ->14 transition. No credential fields are inspected or set.

`native-login-panel-20260920-01` (PID9704/TID16596) reaches both checkpoints:
state1/14, handle2, result NATIVE_LOGIN_PANEL_READY. This qualifies native
panel initialization and return to the input-wait state, not a screenshot,
credential submission or authentication. Compatibility restoration succeeds;
the client and port2592 listener are absent after completion. Three focused
login-entry regressions pass, retaining the no-connect/no-TX boundary.

## Native Test Login Reaches Accepted Server List

`--probe-login-submit` requires the panel probe, C++ loopback server, network
capture and explicit public lab-case A. Native50EC90 populates the two existing
text controls, then68E0(command5, flags1) reads them through6A10/6A90 and takes
the original state15 transition. The observer resumes the normal loop, retaining
all socket/codec/authentication handling. Only existing public synthetic test
credentials are supplied; no personal credentials or success flags are written.

`native-login-submit-20260920-01` (PID12248/TID14488) connects and transmits.
The actual C++ service verifies/binds account1 and sends29, routes/list and0A.
Client events then establish, in order: S2C0003 consumed, terminal handler
return EAX0, login state2/previousF, and server-list UI ready with count1,
selected0, enabled0=1 and directory_count1. These are actual native events,
not just server send logs. Four focused regressions pass, including this chain.

The observer continues waiting after the list and ends HARD_TIMEOUT. The old
login-terminal/server-list summaries still report unverified/regression; they
are retained as historical classifier outputs and do not override the recorded
handler/state/list events. Their full golden comparison is not the acceptance
criterion for the newly instrumented path. Do not infer selection confirmation,
second character connection, world entry or combat from this evidence.
Server shutdown is clean, compatibility restoration succeeds and PID12248 is
absent. The next actionable boundary is normal server-list confirmation.

## Two Native Confirmations And Real Six-Byte Request

`--probe-server-confirm` requires the submit probe and own-server dual mode.
It waits for the original list initializer/display to return at53A8 in state16,
then calls7040(command6, flags1). Original7010 validates its list and enters
state3; the observer changes no selection/state. Run01 qualified this return,
but no second connection occurred. Pinned state3 code initializes another panel
through7A10 and enters state17. The probe now waits at540B, checks its handle,
and calls7AA0(command6, flags1), whose native7A70 guard enters state18.

Run `native-server-confirm-20260920-02` (PID9424) qualifies both original
returns with unchanged ESP: first EAX0/state3, second EAX1/state18, selection0
and second-panel handle4. Continuing the original loop produces an actual
six-byte C2S request. C++ Session logs POST_SERVER_SELECT_C2S_ACCEPTED and
queues/sends the account-owned78-byte opcode7 character-list candidate.
These are not synthetic TCP peer events. The run ends at its observation
deadline afterward; client acceptance of that list remains unqualified here.
Five focused regressions pass. Server shutdown is clean, compatibility restore
succeeds and PID9424 is absent. Neither a second connection nor character/world
entry is claimed. Next: observe the original opcode7 consumer and selection.

## Actual Empty Character List Consumed

Run `native-character-list-20260920-01` (PID12804) reaches148B9 with the real
75-byte logical07, copies its74-byte body exactly to the original output,
returns from13670 consumption at14963, then completes RET18 with EAX0 and
ESP equal to slice-entry ESP+48. Converted output is null in this actual call.
Result is NATIVE_CHARACTER_LIST_CONSUMER_RETURNED; the body count byte is0.
Nonzero unused row bytes do not establish a character when count is zero.
The next required user flow is creation, not existing-character selection.

Six focused regressions pass, covering the actual body, copy, consume/return
order and ABI. Compatibility restoration succeeds and PID12804 is absent.
No rendered-character screen, second connection or world entry is inferred.
For subsequent probe runs, execution_summary reports these native-probe results
separately instead of printing the older golden-prefix classifier as the only
outcome. Old reports are unchanged. The login thunk source hash is now included
in new run provenance. Authentication/selection and world remain distinct gates.

## Empty List Continues To Native Creation Initialization

Opt-in `--observe-character-create` requires the full native confirmation path.
After the verified opcode7 return, it resumes without writing login state or
character fields. Pinned B490 success takes 5B61 -> AFB0(4); empty count and
netA+4200 !=1 take 554A/8740 -> state5. Region0 takes 56C5/9590, which initializes
the draft and creation panel, then the original loop assigns state21.

Run `native-create-panel-20260920-01` reaches 4056DB in PID13996/TID4224,
state21, panel handle6. Its 40-byte draft is recorded as native initialization,
not persisted character data or a recovered gameplay formula. The same thread
previously consumed and returned from the actual own-server empty list.
Result NATIVE_CHARACTER_CREATE_PANEL_READY; compatibility restoration succeeds.
Post-run checks find PID13996 and listeners2592/64760 absent. This run does not
contain the server's clean-shutdown log marker, so graceful server shutdown is
not certified. Seven focused login regressions pass. This is a native initialization checkpoint,
not visual acceptance, creation submission, world entry or playable combat.
Next boundary: original creation controls/submit and own-server persistence.

Execution summary now checks the actual list body/copy/return evidence rather
than requiring a terminal result string, so downstream observation does not
incorrectly erase an already completed list-consumption milestone.

## Real Creation Submission Reveals Opcode17 Contract Gap

`--probe-character-create` calls original97A0(command17,flags1) from state21.
Its native return enters state6; the untouched loop initializes A560 and state23.
The native text setter50EC90 at login+152A8 supplies public diagnostic name
CodexTrial. Original A870(command17,flags1) performs AD30/AD70 name checks and
enters state24. No success flag or draft-attribute override is written.

Run01 reached the second connect but exposed the observer's fixed endpoint
filename. Run02 passed that point and exposed its fixed post-seed filename.
Both artifacts retain TOOL_ERROR, not acceptance. Endpoint/seed records now
have per-run sequence numbers. Only port2592 and the live owned C++ process's
advertised loopback character listener are permitted; external destinations
remain refused. Old one-shot login breakpoints are not rearmed for seed2.

Run `native-create-submit-20260920-03` (PID3344) completes both native commands
with unchanged stack, connects/authenticates session2 against our own server,
and sends a real48-byte request. Packet0251 is checksum-valid, agrees with the
client's pre-encode plaintext, and has opcode0x17 (23), payload44, constant4
at payload40. It is NOT the existing opcode0x1B (27) contract.
Pinned BF30 calls C0B0 ->14CF0 (push17 at14D04), then waits via14EB0.
The existing C160 ->14CC0 (push1B) instead waits via15020. Those response paths
must be qualified separately before persistence is wired into this live flow.

The C++ service rejects the request with Character-create contract rejected;
no creation commit is certified. The observer finishes EVENT_BUDGET_END, not
world acceptance. PID3344 is absent and compatibility restoration succeeded.
Next: qualify14EB0 response and post-create continuation, then add the actual
17 contract to the authoritative service with live regression coverage.

## Opcode17 Creation Persists; Post-Create Sequence Still Open

Pinned14EB0 dispatch selects opcode2 at14F16;14F72 reads the result WORD.
Zero takes15000/13670 consumption and returns EAX0 at1500B. The separate
15020 consumer used by1B remains unchanged. Unicorn branch tests cover
0,1,256,65535 for17 and the prior1B cases; they do not certify live rendering.
The C++ request parser now accepts17 or1B with identical length/checksum/body
constant constraints and records the actual opcode. Success remains gated on
the existing authoritative repository commit, never sent merely for parsing.

Run `native-create-submit-20260920-04` (PID4496) authenticates both connections,
accepts opcode23/48 bytes and commits character1 for account1. Read-only SQLite
inspection after shutdown finds recovered_characters row id1/account1/slot0,
name_bytes CodexTrial and40-byte profile, created2026-09-20 14:56:58 UTC.
This diagnostic character is retained; future tests must not assume the account
is empty or delete it merely to repeat the previous creation probe.

Live packets251,263,267 are respectively17,18,30, with native plaintext match
and checksum pass. Packet263 is050018010e. No following1A frame is established;
the service reports Post-create selection prefix rejected and the observation
ends EVENT_BUDGET_END. Next investigate the18 request/response wait before1A,
and distinguish disconnect30 from a malformed selection. World entry remains
unverified. Compatibility restoration succeeds. Nine targeted CTests pass,
including character_create, repository, session_state and battle/skill sessions.

## Post-Create18 Is A Request/Reply Boundary, Not Immediate1A

Pinned BEB0 calls BE80 with WORD(login+15E34)+1. BE80 sends opcode18 plus one
payload byte. BEB0 then calls15210 and blocks for a reply. The receive length
table at1384 points4012DC, which returns3 logical bytes: S2C18 must be6 bytes
on wire, unlike the5-byte C2S18 request. Consumer15264 filters opcode18;
152BE..152C7 copies logical byte1 to its output. It consumes queue0 exactly
once and returns EAX0 with RET8. Logical byte2 is not read by this consumer;
its original meaning remains unknown, not a recovered constant.

New pinned-instruction regressions execute that exact slice for token0/1/7/255
and tail0/255, check one-byte-only output, queue invocation, return and stack.
They prove no token range validation in this slice; server must still derive
the response token from the committed, account-owned row rather than echo the
request byte (the observed request is1, but persisted row slot is0).

The current Session CharacterCreateCommitted branch expects concatenated18+1A
without replying18. That historical D26E path is not the observed BF30 flow.
After18 success, native BF30 C054..C099 closes/re-authenticates the connection
through15730/144F0/BD50 and sets state4. Thus sending1A immediately or promoting
the session to WorldEntrySent would bypass the actual continuation. Next patch
must distinguish request17 from1B, acknowledge the owned slot, and observe the
native refresh/list path before attempting selection. Keep CodexTrial intact.
Fourteen focused Python tests pass. This is static/synthetic reply qualification;
no S2C18 has yet been sent in a live run, and world acceptance remains open.

## Owned Slot Acknowledgement Implemented For17

Session now retains which create opcode committed. Only17 takes the bounded
five-byte18 request/reply path;1B retains the historical18+1A parser. Fragmented
requests wait until complete and validate checksum/opcode. On the serial game
executor, created_slot(account,committed_id) queries persisted profiles, rejects
missing/foreign/invalid identities, and returns a slot below2. It does not use
the request's context byte as the returned slot. Network-strand serialization
then queues logical18/slot/0 (six wire bytes), clears the input and awaits the
observed30/0 disconnect. The reply's last logical byte remains an explicitly
unverified zero candidate because15210 does not read it. No world frame,
selection callback or character binding is triggered by this acknowledgement.

Application connects the handler under existing recovered-character-creation
configuration; no ordinary/custom combat mode is enabled. The synthetic TCP
session regression tests fragmented18, repository-token0 despite request1,
no premature character selection, and graceful30/0 close. Service tests cover
foreign/missing/zero identities. Live-client acknowledgement acceptance is still
pending: CodexTrial is retained in the existing database, so the old empty-account
creation probe must not simply be rerun against it. Use an isolated diagnostic
database/account for a fresh create cycle, or follow the existing-character path.
Build succeeds. Four focused CTests pass (session_state87.55s, character_create,
recovered_character_repository, post_create_select); the latter was rebuilt and
rerun after adding the created_slot ownership assertions. Fourteen focused
Python regressions pass. These results are not a live S2C18 acceptance claim.

## Live18 Acknowledgement Accepted By Original Consumer

`--isolated-database` creates a per-run server config and fresh SQLite database,
preserving the existing recovered-accounts.db and CodexTrial. Lua bootstrap/root
are resolved to absolute existing paths because generated config location changes
relative-path resolution. Run01 failed at server startup due to that path issue;
it is retained as TOOL_ERROR and did not launch the client.

Run `native-create-ack-20260920-02` (PID3480) authenticates, creates its isolated
CodexTrial, and receives logical180000. Observer checkpoints4152BE/4152D0/40BEE0
prove the original consumer copied slot0, consumed the packet and returned EAX0
with ESP=entry+20 on the same thread. Result NATIVE_CREATE_SLOT_ACK_RETURNED.
Read-only SQLite verification finds isolated id1/account1/slot0/CodexTrial.
Compatibility restoration succeeds. This qualifies actual client acceptance of
the six-byte reply, not the unknown final byte's original semantics. The observer
stops at the verified return before BEB0 continues; refresh/selection/world are
not yet certified. Next allow that same natural continuation without writing
client state. Fifteen focused Python regressions pass.

## Native Refresh Returns The Persisted Character To Selection

Run native-create-refresh-20260920-01 disproves the earlier assumption that
successful18 ends with30/0. The actual successful C064 call is15730(2,0,1),
sending05000200f7, and waits in15180 for opcode03. The03 length-table entry also
returns3 logical bytes. Session now queues logical03/0/0 then drains/ends this
character connection. The unused03 tail bytes are zero candidates, not original
semantics. Its synthetic TCP test now verifies the02 request and03 reply before
close; the earlier30 shutdown expectation is superseded by this live evidence.

Run02 progresses through third-connection authentication but reaches the old350
event observation limit. Optional --observe-created-refresh now has1000 events
while retaining the wall-clock deadline. Run03 (PID17228/TID13936) reaches
C099 in state4, then557E in state19 with valid selection panel8. Both snapshots
contain74-byte character list count1/name CodexTrial. The own C++ server sends
that populated list on session3, then authenticates session4's independent
character connection. Result NATIVE_CREATED_SELECTION_READY; no selection
command or world entry has yet been accepted. Compatibility restore succeeds.

Residual: old login session1 receives native0A with public lab account bytes and
is rejected by the current independent-character-operation guard. The subsequent
native reconnect/list succeeds despite this; do not describe the whole refresh
protocol as error-free. Preserve this explicit logout/refresh request gap.

## Original Character Confirmation Returns Success To Application

--probe-character-select requires the observed creation/refresh chain. The
selection table at88E8 maps command10 to8865: it validates the current name
path and enters20 through AFB0. The probe validates selected index against the
actual populated list, calls87B0(command10,flags1), checks immutable thunk,
unchanged ESP/EAX1/state20, then resumes the normal loop at557E. It neither
assigns the selected slot nor writes the login/world state.

Run native-character-select-20260920-01 (PID10004/TID6800) confirms slot0.
Own-server session4 binds character1 and queues opcode2 success and the40-byte
opcode2A world candidate. The original4DA0 loop returns to40DF8C with EAX1 and
ESP restored by RET14. Result NATIVE_CHARACTER_SELECTION_RETURNED. The probe
stops before the application executes the world-entry continuation. Thus this
qualifies actual selection success, not world rendering, movement or combat.
Compatibility restoration succeeds. Next observe application/world initialization
and its real network consumers; the old-session0A gap remains separately open.

## Original World Initializer And Network Tail Succeed

--observe-world-entry resumes from the verified40DF8C selection return without
altering the original application branch. It observes constructor4643B0, then
initializer464910 and its return40E0DB. No offline-world-entry bridge is used.
Run native-world-entry-20260920-01 (PID3100/TID14600) reaches all three with the
same world object268603424, initializer EAX1, and ESP restored by28 bytes
(return plus six arguments). Original initialization also sends the real network
tail: own C++ session4 logs WORLD_INITIALIZER_TAIL_ACCEPTED opcodes31,35,28,
config_flag0. Result NATIVE_WORLD_INITIALIZER_SUCCEEDED. Compatibility restoration
succeeds and the owned client is absent afterward.

The probe intentionally stops before E0ED/655E0 world-loop continuation. These
facts certify native initialization and tail acceptance, not a rendered playable
world, movement, combat, content completeness, or recovered gameplay formulas.
The old-session0A rejection remains. Next observe original world-loop execution
and validate world interaction against our own server; do not relabel this result
as the full goal's acceptance. Eighteen focused Python regressions pass.

## World Loop Reached; Scene And Post-Initializer Handling Open

--observe-world-loop resumes the real E0DB return and observes655E0 plus the
first eight655638 dispatches if reached, retaining the existing observation
deadline/budget. Run native-world-loop-20260920-01 (PID16004/TID9808) enters
655E0 fromE0FD and dispatches state3 once. Pinned table65A14+12 targets65644,
which calls67860; no subsequent world-state transition is recorded. The run
ends EVENT_BUDGET_END, not playable-world success. Compatibility restore succeeds.

Own session4 accepts the initialization tail, then closes with Post-initializer
world contract not implemented. This run uses recovered-world-entry.json, which
does not enable recovered_movement. Application installs world_ready/world_records
only when that movement service exists. The existing recovered-movement.json
enables the indoor2/15 navigation artifact and position service, but that config
has not yet been qualified with this actual native login/create/select chain.
Next inspect scene inputs and that navigation artifact, then test the existing
world handler in an isolated database rather than claiming world-state acceptance
or bypassing scene loading. Nineteen focused Python regressions pass.

## Isolated World Handler Keeps Native Periodic Traffic Accepted

--movement-lab selects the existing recovered-movement.json only when isolated
database and recovered world entry are requested. Navigation path is resolved
absolutely in the generated config. Production configs are unchanged. Existing
service checks pinned indoor2/15 grid reconstruction, account/character ownership,
step/sequence constraints and position persistence; movement balance is not
promoted by this test.

Run native-world-movement-20260920-01 (PID14912) initializes successfully and
enters the original world loop. Actual logical30/0 packets recur about every5s;
the C++ world handler accepts multiple single-record batches rather than rejecting
the post-initializer contract. Observation reaches HARD_TIMEOUT at its normal
deadline; no live movement command or rendered-world acceptance is established.
Compatibility restoration succeeds. State3 is the observed outer loop branch,
not by itself proof of a stalled loader:67860 can remain active internally while
periodic traffic continues. Earlier descriptions of this state as necessarily
blocked must not be used as a diagnosis. The timeout WoW stack is inconclusive.
Next observe67860 internal scene/input/render checkpoints and native movement
producer; preserve the distinction between periodic traffic and actual movement.
Twenty focused Python regressions pass.

## Original World Frame Iterations Observed

--observe-world-frames adds read-only checkpoints at67BCA after32A20 and67BD7
after32F60 inside the original67860 loop. Run native-world-frames-20260920-01
(PID3904) reaches the ordered pair three times on one thread with unchanged
stack and world frame counter0,1,2. This directly corrects any prior assumption
that remaining in outer state3 implies scene-loading failure. Original inner
frame processing is active. Result NATIVE_WORLD_FRAMES_OBSERVED; compatibility
restoration succeeds and owned PID is absent after the bounded run.

No framebuffer pixels, visual scene contents, movement input, movement ACK or
position persistence are certified by these call-return checkpoints. The renderer
return values are not interpreted as graphics API success. Next use the actual
world object's native movement producer and verify its network/position effects.
Twenty-one focused Python regressions pass; full playable-world goal remains open.
