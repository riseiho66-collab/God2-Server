# Current Revival Evidence

Scope: current Taiwan client, source-pinned descriptions and original metadata
lookup only. No retired archive, official server or production gameplay changes.

`tools/strike_lab/current_revival_evidence.py` extracts 11 item/book records with
raw bytes, hashes, source line and decoded offset into
`artifacts/research/current-revival-evidence-20260921.json`.

The four original A8E10 lookups were executed again using
NativeSkillBookBinding on 2026-09-21. Results agree with the existing full
catalog artifact `current-skill-book-binding-20260920.json`:

| Book | Native kind/id | Line | Description |
| --- | --- | --- | --- |
| 6808 | 3/8 | 9212 | Revival HP1; MP66; reach5; one target |
| 6809 | 3/9 | 9213 | Revival HP30%; MP111; reach6; one target |
| 6810 | 3/10 | 9214 | Revival HP full; MP222; reach7; one target |
| 6872 | 3/72 | 9272 | Active buff, 60 minutes, automatic revival on combat death, HP full |

Source hash and original image identity follow the binding report. These lookups
prove book/definition identity, not cast eligibility or execution. In particular
HP30% does not specify the basis, rounding or minimum HP. MP values here remain
source descriptions, not independently qualified debit timing.

Additional original descriptions distinguish automatic combat revival items
5518, 5542..5546 from the death-return XP protection item5539. Lv2 variants
describe HP full and MP restoration50; Lv3 variants describe HP full and MP
restoration1/3. Do not silently interpret restoration as assignment or infer a
percentage basis. Pet and character recipient rules must remain separate.

Pinned message.csvZ records1285/1286/1287 (physical lines1360..1362) explicitly
say the per-battle usage limit has been reached for three revival-item classes.
The original text establishes that a limit exists, not its numeric value,
counter grouping or reset rules. The exporter retains numeric_limit=null.
The message scan also found unrelated pet death and arena forced-return text;
neither establishes ordinary player defeat-return mechanics.

Verification:

```
python -B -m unittest discover -s tests/research -p test_current_revival_evidence.py
python -B -m tools.strike_lab.current_revival_evidence --output artifacts/research/current-revival-evidence-20260921.json
```

4 tests passed. All entries remain description_only and executable=false.

Next qualification: trace dead-target eligibility and the original selection/
command/animation path for kind3/id8, separately from ordinary defeat return.
The diagnostic duel currently finishes when its only friendly actor dies; a
living allied caster and a dead ally are needed to test combat revival without
inventing a self-cast after a finished battle. Ordinary defeat still needs a
return destination, restored HP and penalty policy; none are supplied by these
three active revival skill descriptions. Until qualified, do not turn the saved
HP0 outcome into automatic full healing or promote these records to server rules.

## Native targeting and live death field observation

The source definitions for kind3 IDs8/9/10 have mode1 and reach5/6/7.
Original RVA11EE90 invokes 11E6E0 and expands its temporary masks for nonnull
type0 entities whose signed WORD at +1A is nonnegative. It preserves existing
mask bits. It does not directly read HP and is not a dead-only eligibility check.

Added 4,704 cases (3 source definitions x 14 caster slots x 28 candidate slots x
4 pointer/WORD conditions) to the original-code target harness. Cases cover
null, -1, 0 and 32767, using sparse masks and independent expected bits.
Existing caster bits survive null/negative entity state; both sides can receive
expanded bits. An additional source kind3/id72 case does not take this expansion.
Full test_current_skill_target_setup suite: 15 tests passed, 19.964 seconds.

Own-server live run `native-defeat-20260921-02` again completed defeat, both
animations without fallback, result and world return. Read-only observation at
the original vitals consumer found the same player entity pointer and WORD+1A
value125 before (HP4) and after (HP0) lethal retaliation. Enemy WORD+1A was141.
These observations do not establish the WORD's full meaning, but disprove using
its sign alone as the death discriminator for this actor. The run does not cast
a revival skill and does not prove the final cast handler accepts a living or
dead target. Saved-evidence assertions live in test_current_defeat_projection.

Next trace belongs after broad mask setup: original final target selection and
command admission for kind3/id8 with a living caster plus dead ally. Keep this
separate from reviving the last defeated actor after battle termination.

## Original request builder and protocol integration

Original118E50 -> selection accessor ->132E0 emits revival request parameters
as DWORD 0x0308/0x0309/0x030A, not the selector-table index. Example with actor0,
target1, zero context and stack poisonA5:
`35 00 03 00 A5 02 00 00 00 00 00 00 00 08 03 00 00`.
The kind byte at logical offset14 was previously rejected by the kind0-only
RecoveredSkillCommand parser.

The parser now retains selection_kind_byte and admits the qualified kind3
IDs8..10 subset. Sequence identity includes kind, preventing a kind3/kind0
splice with the same ID. Other nonzero-kind requests remain rejected. Formal
world-record reconstruction preserves the kind byte rather than zeroing it.

The original-code builder test covers all three IDs, both selector paths and
five target lists (30 cases), including continuation, native queue output,
C++ parsing and world transport roundtrip. This executes a staged builder,
not ordinary UI target confirmation, HP eligibility or the post-queue cleanup.
The source defines these as single-target skills; structural multi-record
acceptance is not permission to cast them on multiple recipients.

RecoveredBattleService explicitly rejects nonzero kinds before its existing
kind0 policy lookup. A same-ID collision regression proves a revival8 request
cannot execute authorized attack8, debit MP or consume action admission.
This is protocol intake groundwork, NOT an enabled revival implementation.

Build succeeded for god2-server, recovered-world-records and
recovered-battle-service. Native skill command suite: 13 tests passed. CTest
recovered_world_records and recovered_battle_service: 2/2 passed. Rebuilding the
world-record fixture also exposed old missing opcode26 variant/reconstruction
and unsupported-opcode expectations from the supply addition; these were
updated to match the existing source contract, without changing supply behavior.

## HP-only restoration versus pending result state

New original vitals-consumer regression starts from HP0 and presentation bytes
entity+1EB=9, entity+232=9. Original86/0 dispatch copies HP1, HP36 and HP120
into actor and role resource storage without changing either presentation byte.
Thus an HP update alone does not clear these explicitly staged death states.
This stops at the existing role-update boundary, not a complete render loop.

The original secondary table at171610 maps packet index0 ->9, index27 ->89
(0x59), index28 ->0. Existing index28 is NOT sufficient to replace an already
latched9 in the skill-result path:

- 12C26E reads recipient+232; if it is9, ordinary secondary values preserve9
  in the source's pending result at +224+current_action_index.
- 12C27E explicitly permits secondary89 to reach12C298.
- 12C298 stores89 in recipient+232 and12C2A6 in the source's pending result.

A continuous original12C000 ->12C0C0 test stages a source at side0/slot0 with
current index1 pointing to side1/slot0. The recipient starts with +232=9,
+1EB=9 and HP0. Sending skill result secondary28 retains pending9; sending27
then changes recipient+232 and source+225 to89. Recipient+1EB stays9 and HP
stays0. No instructions, helper returns or client field writes are patched
during execution; the initial staged operands are explicit test inputs.

Tests: current_battle_outcome_mapping 3/3 and current_battle_vitals 6/6 passed.
This identifies a special pending-state transition candidate, NOT complete
revival animation acceptance. Index27 must not be promoted as a working revive
encoder until the subsequent animation consumes89, restores a usable actor,
and agrees with HP/resource updates in an own-server real-client experiment.
The current DiagnosticBattleParticipants helpers remain unchanged.

## Dedicated state89 handler prefix

The pending secondary state is consumed at128DA0/128DEC. State89 takes the
actual CALL128DF6 ->1267C0 instead of general126430. Original1267C0 first:

- clears entity+1DE;
- decodes entity+234 into side (bit7) and slot (low nibble);
- ORs that actor's bit back into manager+2F4/+2F8;
- assigns entity+DB8=0x10000000;
- calls129870 with entity, state0, force1, followed by120B90 and126270.

The new test_current_revival_state executes from128DEC through the real
CALL1267C0, stopping at129870 before animation/rendering. All28 positions
restore exactly the correct mask bit, preserve unrelated bits, and perform
only the three expected non-stack writes. HP remains0. Four non89 controls
instead stop at general126430 without these mutations. No callee return is
substituted; downstream rendering remains unexecuted.

The same suite sends an explicit candidate skill effect
`83 03 00 00 00 02 00 00 00 01 00 08 03 00 1B`
through original12C520 to12B621 with the source kind3/id8 definition. All13
non-source friendly positions are checked by varying the target mask. This
qualifies native effect-operand storage, not dead-target casting, animation,
resource mutation, or a server encoder. The amount1 is a diagnostic operand
consistent with first-tier text; no official timing/order is inferred.

Three new tests pass. Next requirement is a complete live battle containing a
living caster and a dead ally, with trusted owned-skill state and enough MP,
followed by this received effect, HP update and actual downstream animation.
The existing two-actor duel cannot test allied resurrection after its only
friendly actor has died; it must not be silently converted to a self-revival.

## Isolated authoritative transaction groundwork

CUSTOM-0017 now provides Battle::revive and LuaEngine::revival with a pure
scripts/gameplay/revival.lua projection. The first-tier test rule returns HP1
and MP cost66 based on book6808 text. Eligibility and commit timing remain
explicitly custom, not a recovered original formula or approved balance model.

C++ requires an active battle, matching controller/revision, living source and
one distinct dead same-side target. It validates bounded positive Lua outputs,
rejects insufficient MP, stages source MP/target HP/revision, calls the encoder,
then publishes only after a nonempty response. RNG, target MP, other actors and
outcome remain unchanged. This API does not revive an eliminated side or a
finished battle. Caller still must authorize owned skill identity and arrange
durable transaction commit around a staged Battle, as with existing attacks.

test_battle_revival uses a real Lua damage action to kill one ally while keeping
another alive. It covers both sides, MP65 rejection/MP66 exact exhaustion,
foreign controller/stale revision, living/missing/enemy/self/dead-source targets,
revision overflow, missing/throwing/invalid rule or encoder, all-state rollback,
one successful revision, duplicate rejection, unchanged RNG, checkpoint restore,
and a subsequent attack by the restored actor. Test encoder bytes are synthetic,
not a claim of native packet or UI acceptance. Lua reload is also checked.

Builds: battle-revival, god2-server, battle-transaction,
recovered-battle-service and supply-lua succeeded. CTest battle_revival,
battle_transaction, recovered_battle_service and supply_lua: 4/4 passed.
No Application wiring, revival packet encoder, database mutation or normal
kind3 skill dispatch has been enabled. This keeps protocol qualification,
custom domain behavior and pending live integration distinct.

## Explicit service binding and candidate reply

RecoveredBattleService now admits a trusted optional diagnostic_revival binding
with pure rule and encode callbacks. It requires single-action mode and forbids
automatic retaliation. This does not add an Application configuration or default
runtime activation. The previous blanket kind3 rejection remains for unbound
sessions; the opt-in admits only kind3/id8, one non-continuation record, matching
session actor/side/context and one bounded target bit. Mixed batches remain
rejected. Domain validation still rejects living/enemy/self/missing targets.

The service stages a Battle copy, validates every reply envelope before invoking
the existing commit/checkpoint callback, and only then publishes the snapshot
and action admission latch. Corrupt reply or a throwing commit leaves admission
and HP/MP unchanged. Existing receipt/rearm handling is reused as a diagnostic
contract only, not a claimed native revival-turn receipt qualification.

DiagnosticBattleRevival.h emits an isolated source0/ally1..13 candidate:
86/1 caster MP, 83 action3 kind3/id8 amount+1 secondary27, then86/0 ally HP1.
This order remains a test choice pending full live acceptance. Native skill
effect tests now consume bytes emitted by the compiled C++ encoder, not only
a handwritten fixture. All13 allied non-source effect-store positions pass;
the test stops before the subsequent animation, as previously documented.

Service tests include valid decoded C2S bytes, malformed reply rollback,
checkpoint callback failure/retry, actor/side/context/ID mismatches,
continuation/mixed-batch rejection, reply layout, duplicate rejection and
receipt-gated round readiness without false battle completion. No database
write is claimed by callback fault injection.

Builds passed: battle-revival, recovered-battle-service, god2-server.
CTest battle_revival, battle_transaction, recovered_battle_service and
recovered_world_records: 4/4. Native revival state suite: 3/3. Full own-server
client casting, allied participant setup, persistence and rendering remain open.

## Three-participant bootstrap preparation

`diagnostic_revival_participants(identity, snapshot)` now builds an isolated
375-byte logical batch for slots 0, 1 and 14: historical player appearance,
three identities with HP and friendly MP, matching 88 bulk values, then 86/5
grant to slot0. It rejects extra/missing/misindexed actors, invalid ownership,
finished battles, absent living caster/enemy and inconsistent resource bounds.
All resource DWORDs come from the supplied diagnostic snapshot; no save changes
or inventory/skill grants occur here. CUSTOM-0017 applies to this setup.

The allied slot uses the existing synthetic EnyName appearance template. Its
construction on the friendly side is a live-test candidate, not certified party
semantics. Zero HP in the bootstrap does not establish death animation state;
the live scenario must observe that separately, preferably via a lethal action
against an initially living ally. Existing two-participant bootstrap is unchanged.

Compiled test verifies actor record offsets, bulk HP/MP including zero-HP ally,
frame round trip and invalid snapshots. CTest battle_revival,
battle_transaction, recovered_battle_service and recovered_world_records: 4/4
passed; test_current_revival_state.py: 3/3 passed. Application activation,
kind3/id8 ownership/hotbar setup, live animation, durable commit and normal
client gameplay acceptance remain open. No playability percentage increase.

## Revival ownership and hotbar preparation

Compiled `battle-revival --seed` emits the existing diagnostic 19-byte S2C30
key-1 selected-row input followed by `34 01 03 08`. This is CUSTOM-0017 test
ownership, not an original starter skill assignment. The original low-key
lookup 59A60 and row append execute with an explicit synthetic name metadata
record; the real S2C34 writer then appends the pinned cbspec2 kind3/id8 pointer.
This test uses raw pinned catalog payload, not a native loader, and stops before
AA7BF refresh. The named-row-only helper correctly refused the low-key input;
the test now executes the low-key branch rather than bypassing its requirements.

Native hotbar entry 1151A0 reaches the selected-index write for kind3/id8 across
the existing qualified modes/rows and ten hotkey slots. Selector ownership is
explicit fixture input, so this is not a continuous ownership-to-cast proof.
The capture_work-only hotbar fixture has an opt-in revival identity; default
kind0/id1 bytes stay unchanged, exclusive file creation still preserves user
files, and cleanup retains an artifact. No launcher/client EXE was modified.

Verification: original learned-writer suite 13/13, skill-selection suite 9/9,
hotbar-binding suite 15/15. These counts include existing regressions, not 37
new gameplay features. Actual three-actor runtime wiring, client cast and full
revival rendering/persistence remain next; no E2E acceptance is claimed.

## Application diagnostic entry

`development.diagnostic_battle_revival` now explicitly connects the candidate
three-participant bootstrap, kind3/id8 seed, 87 selectable word8308 and Lua
revival service binding. Default is false. Config requires isolated loopback
battle transition/participants/player appearance, skill seed and animations;
it rejects damage-skill settlement, persisted resources, world resources,
terminal/repeated battles, MP-refusal and movement-trigger combinations.

The caster starts with test MP80; ally1 is an explicit synthetic zero-HP
checkpoint, enemy14 remains living. This checkpoint was not produced by an
observed lethal action. Battle constructor invariants remain intact: construct
living participants then explicitly restore the diagnostic dead-ally snapshot.
No automatic retaliation or persistent resource commit is attached. The
unchanged non-revival configuration retains its previous two-actor path.

After building god2-server and god2-tests, CTest config, application_startup and
battle_revival passed 3/3. This verifies compilation/config admission and existing
domain behavior, not Application runtime delivery to a native client. Runner
flag propagation, revival-aware observations and actual native acceptance remain
open. Ordinary startup smoke uses its existing fixture, not this new scenario.

## Own-server three-actor initialization observation

Run `native-revival-bootstrap-20260921-01` completed with
NATIVE_SOCKET_PARTICIPANTS_GRANTED, error null. The runner now propagates the
explicit revival flag and loads its isolated hotbar fixture. Action probes and
persistent-resource combinations are refused for this initialization-only mode.
Three actual S2C1C records reached the original consumer at slots0/1/14; actor
pointers were distinct. Native memory held caster HP100/MP80/max120/80 and ally
HP0/MP5/max120/20. Enemy HP150/max150 was observed; MP was uninitialized allocator
bytes, not native monster data and not a qualified MP projection.

The current client's skill source had one learned entry, selector word8308,
definition0803, and primary hotbar type2/kind3/id8. The native-loaded hotbar file
was unchanged at teardown. No cast was attempted and no revival response sent.

Important negative evidence: zero-HP ally presentation state was15, pending
state0, NOT death9. Thus initial HP0 cannot substitute for a real death/animation
transition. Next live scenario must establish that transition before claiming
89 restores it. Full visual/UI/world acceptance remains false/unqualified.
Saved-evidence tests test_current_revival_live.py pass3/3 and explicitly preserve
these limits. This is initialization acceptance, not full revival acceptance.

## Lethal-prelude experiment: animation gate still open

Application revival diagnostic now constructs a living HP4 ally and stages a
real C++ Battle::act with the existing custom Lua damage rule, enemy14 -> ally1.
`diagnostic_revival_death_setup` emits basic83 amount-4/death-index0 and86 HP0,
then publishes the staged battle only after encoding succeeds. The original
two-actor path is unchanged. This is not an official damage formula.

Two own-server runs `native-revival-death-20260921-01` and `-02` both ended
EVENT_BUDGET_END, not success. Run01 sent death before initial control grant:
at grant, ally HP0/pending9 but presentation15. The observed batch counter
remained expected0/completed-1, with no qualifying completion. Run02 moved
initial grant before the action, matching the ordinary initialization order;
at that earlier sampling point ally was HP4/pending0. It also produced no
qualifying animation completion. These samples are at different timeline points
and do not imply the second run failed to consume HP0 later.

Current emitter retains run02 ordering. The unresolved condition is activation
of the action/animation cycle for this unsolicited enemy opening, not encoding
HP0 or selecting the pending death index. Next trace must compare the normal
client turn-submit/receipt sequence against this prelude; do not patch native
state to claim success. No revival cast, persistent writes or native death
animation acceptance is claimed. Tests cover the staged lethal result/rollback
and preserve both failed experiments; C++ battle_revival passes.

## Cycle-snapshot closure: natural batch observed

Run03 used first-action group0 instead of the old second-exchange group1,
following original114389 marker comparison evidence; still EVENT_BUDGET_END.
Run04 also called the existing original118E50 basic-submit thunk. It returned
with waiting1 and the server accepted a damage response, but still HARD_TIMEOUT
without qualified animation completion. That diagnostic call was removed.

The qualified ordinary enemy-action path emits an updated88 after83/86. Adding
the same explicit cycle snapshot after the opening lethal action produced
`native-revival-death-20260921-05`: one natural batch, expected1/completed1,
2666ms, timeout_fallback=false. No basic-submit thunk was used in this run.
The emitter is now528 logical bytes: existing three-actor bootstrap/control,
group0 enemy lethal83/HP86, then settled88 retaining caster100/80 and ally0/5.
The new C++ test checks this order and batch values. Source formulas remain
CUSTOM, not original damage recovery.

At finalization return, ally HP0/MP5/max120/20 and pending9 were observed,
but presentation byte remained15. Thus this closes animation-batch activation,
NOT visual death pose or revival acceptance. Next work must follow recipient
presentation/89 handling and actual kind3/id8 casting without treating the
pending state as a rendered pose. Native animation regressions14/14 and C++
battle_revival passed; saved live suite covers the exact narrower outcome.

## First actual selection attempt: regrant boundary

The original action-call thunk now supports an explicit bounds-checked target
0..27 (default14 unchanged); revival uses allied slot1. No native instruction
was replaced, and no skill or control state was written into the client.

Run `native-revival-cast-20260921-01` naturally completed the lethal batch, then
called original1151A0 to select the native-loaded revival hotbar entry. It
returned selected_index=-1, battle_action_mode=FFFFFFFF, counts0000. The runner
stopped with TOOL_ERROR before any skill command was queued. This is a captured
negative result, not a cast or server settlement. It shows that selection at
animation finalization is too early/unauthorized after the mode clear; the
normal receipt/regrant path must be qualified before retrying. Do not force
the selected index or action mode to bypass that requirement.

The runner includes prospective native118E50 target1 and HP-receiver observation,
but neither was reached by this run. test_current_offline_battle_init.py passes
10 tests including target argument bounds/default preservation; the saved live
regression retains the failed selection and absence of a command/projection.

## Natural continuation exposes unsupported action2

`native-revival-receipt-20260921-01` resumes original finalization instead of
calling selection there, and waits for a new native grant. It ended
EVENT_BUDGET_END without a new grant. Its cpp-server.log reveals the earlier
disconnect: World frame contract rejected. Packet0519 has checksum-valid,
client-plaintext-matched37-byte frame containing two17-byte commands: action02
then action0B. Both use actor0/side0/context0 and friendly mask1. This packet
precedes the death-finalization observation, so it is NOT a post-animation ACK.
Earlier failure reports that emphasized only regrant were incomplete: the
transport grammar also rejected this naturally generated command batch.

RecoveredBattleCommand now gives action02 a distinct Action2Request type and
preserves its opaque fields. RecoveredWorldRecords appends that type without
changing existing variant indices. No defensive effects or authorization are
inferred; the battle service still rejects it until a separately qualified
opening policy is implemented. Thus parser repair alone does not fix the full
connection/cast sequence. Current task: move from the actual initial action2/
control batch through response/cycle completion and qualified regrant, not
pretend it arrived after animation.

The actual captured wire frame roundtrips through compiled recovered-world-records
to identical plaintext logical bytes; truncation, continuation rejection and
mutation tests pass. god2-server, battle-revival and recovered-battle-service
rebuilt. Live saved-evidence suite7/7; no renewed runtime cast success claimed.

## Exact opening admission and connection continuity

CUSTOM-0017 DiagnosticRevival.opening_notice opts into the one observed
action02/control0B pair. It requires authenticated bound owner/context, both
friendly masks1/0, zero opaque fields, prior zero-mask initial control,
revision2/dead ally1, no action/control already received and no prior opening.
It records only a once-only admission latch, returns an empty response, and
does not execute defense, spend resources, advance revision or mark the round
ready. Defaults reject it. Tests cover pre-initial refusal, wrong mask, exact
admission without mutation and duplicate refusal, followed by existing revival.

Run02 parsed the new type but world routing still refused it. Both world-batch
classification and session battle admission now route Action2Request to the
existing battle policy; other states and missing handlers remain rejected.
Run03 then retained its connection and accepted opening02/0B plus subsequent
ticks/timer36, with neither contract nor policy disconnect. It ended HARD_TIMEOUT
waiting for regrant, not gameplay success. Only the initial02/0B command pair
was captured after packet519; no later35 receipt was observed in this interval.
Do not assume that waiting longer guarantees a post-animation receipt. Next
step must qualify the opening-notice-to-regrant exchange, while keeping the
known early packet distinct from animation completion evidence.

## Native cast and resource projection accepted

The once-only opening admission now returns a candidate86/5 actor0 grant,
before publishing its admission latch; it still changes no battle resources
or revision and never executes an inferred action02 defense effect. The grant
is restricted to the explicit slot0/side0 revival diagnostic policy.

Run `native-revival-regrant-20260921-01` showed grant consumption before natural
lethal animation completion. Waiting for another grant then timed out; that
observation alone did not prove the early grant was cleared. Run02 inspected
post-animation controls and found first_grant1/waiting0 preserved. Original
1151A0 subsequently selected index0/mode3, original118E50 generated target1
kind3/id8 C2S35, and the real server accepted it and sent52 wire bytes.

Run02 result NATIVE_REVIVAL_HP_PROJECTION_OBSERVED, error null. Native receive
memory: caster HP100/MP14/max120/80, ally HP1/MP5/max120/20, pending state89.
Native command byte4 is unwritten scratch (2D in this run), not a parameter
that should be forced to zero. Sequence grant530 -> death532 -> select533 ->
command534 -> HP projection548 proves the observed order. No selection/control
state was patched in the client. Input used original-call thunks, not mouse UI.

This establishes one own-server diagnostic revival request and MP/HP projection,
NOT completed revival animation, next turn, persistence, production balance or
original server cast timing. Pending89 is not visual pose; presentation remained
15 at the HP receiver. Only the lethal prelude's one animation batch completed
before stopping. The next runtime step is full89 animation/cycle completion and
subsequent action. CUSTOM-0017 classification remains in force.

## Full native89 call and natural revival batch

The diagnostic revival reply now appends settled88 cycle1 after MP86/effect83/
HP86, making170 logical/173 wire bytes. This cycle number is explicit CUSTOM
test ordering, not recovered general turn numbering. Snapshot covers all
present friendly actors, including casterMP14 and revived allyHP1/MP5.

`native-revival-animation-20260921-01` completed both lethal and revival batches
without timeout. Run02 added1267C0 instrumentation but initially mistook ECX
(manager) for actor. Its recorded consumer state/vitals fields are INVALID as
actor evidence; retained raw log shows arg1=entity and arg2=59hex. No old
artifacts were overwritten. Run03 corrects this ABI and validates manager,
ally-slot1 pointer, argument89, and return stack+12.

Run03 result NATIVE_REVIVAL_ANIMATION_OBSERVED, error null. Two batches each
expected1/completed1,2628ms/2390ms,no fallback. The actual1267C0 call changed
manager masks(1,1)->(3,1), restoring ally1, and entity+1EA9->0 while preserving
HP1/MP5/max120/20. Consumer return precedes second batch completion/finalization.
This executes the real native call including its nested callees, not the
previous offline prefix stopped before129870.

Correction: the old JSON label presentation_state refers to byte+1EB, which
remained15. That byte alone is not evidence that an actor remains dead. The
observed death/reset byte in the complete consumer is +1EA. Raw old fields
remain unchanged for audit. This establishes native lifecycle/target-membership
restoration and natural batch completion, not physical UI screenshot acceptance,
next-turn action or persistent revival. Those remain open.

## Post-revival next round

Run `native-revival-next-turn-20260921-01` returns
`NATIVE_POST_REVIVAL_BASIC_DAMAGE_OBSERVED`, error null. The isolated revival
configuration now permits one or two rounds; all production/persistence gates
remain unchanged. The existing validated control-receipt/rearm path grants
round2 with bulk cycle2, after the revival response already used cycle1.

The lethal and revival batches completed naturally (2619/2424ms, each1/1,
no fallback). Revival finalization sequence556 precedes grant570, original
118E50 basic-command return571, HP-consumer entry584 and return585. Enemy HP
changes150->132; caster HP100/MP14 and revived ally HP1/MP5 remain unchanged.
Enemy MP remains unprojected and is not interpreted from memory sentinel bytes.
The server records exactly one second-round grant and one173-byte revival
reply, then accepts the basic action with35-byte response.

`tests/research/test_current_revival_live.py` pins this ordering and resource
preservation. Six targeted CTest cases pass, including configuration, revival,
world service and records. Damage18 is CUSTOM diagnostic output, not a recovered
official formula. This establishes caster action after revival, not the revived
ally's own turn, third animation completion, normal UI, durable revival or
production balance. `world_accepted` remains false.

## Followup animation stall and correction

`native-revival-next-animation-20260921-01` extends observation after the HP
receiver instead of stopping there. It times out with two completed batches,
followup damage present and connection continuing. The35-byte basic reply
contains effect/HP only: Application's settled88 branch depended on enemy
retaliation, which this revival diagnostic explicitly disables.

The isolated revival source0 Active branch now appends current cycle2 settled88
with both friendly actors' resources; no regrant or gameplay-state mutation is
added. Other battle branches retain their previous cycle calculation. This is
CUSTOM-0017 diagnostic scheduling, not a newly recovered universal cycle rule.

Fresh run `native-revival-next-animation-20260921-02` accepts156-byte reply and
returns `NATIVE_POST_REVIVAL_BASIC_ANIMATION_OBSERVED`. All three batches complete
1/1 without fallback (2637,2387,2073ms). Third completion586 follows HP return585,
then finalization returns587. Saved-evidence tests preserve both failure and
success. Subsequent control-receipt admission, revived actor taking its own
action, persistence and ordinary UI acceptance remain open.

## Followup control receipt

Run `native-revival-followup-receipt-20260921-01` deliberately continues after
third animation finalization. Packet0590 is20-byte plaintext
`140035000b0000010000000000000000000000c9`, checksum valid and matching the
native plaintext entry588 after finalization587. Formal frame decoding agrees.
The server accepts this single control record with empty reply, then continues
handling heartbeats and timer36. No third grant is issued: configured round
limit remains2. The bounded run ends HARD_TIMEOUT, not a general success code.

The saved-evidence test checks packet ordering and the server log after the
156-byte basic response. C++ service tests replay captured basic/receipt shape
against a restored post-revival snapshot, reject pre-action and duplicate
receipts plus wrong actor/side/mask/context, and prove receipt/rearm preserve
HP/MP/revision. This resolves receipt admission for this diagnostic sequence;
it does not qualify arbitrary multiplayer turns or revival persistence.

## Atomic checkpoint storage qualification

`test_revival_checkpoint_atomicity` in recovered-character repository tests
creates a fresh temporary SQLite database, reserves a battle, stores three
actors, applies lethal damage, then stages revival. It uses existing isolated
CUSTOM-0012 checkpoint policy and explicit CUSTOM-0017 arithmetic fixture;
no production data or owner saves are changed.

An injected SQLite trigger failure during checkpoint UPDATE proves the earlier
resource write rolls back with the document. Mismatched resource/actor values
and stale checkpoint replay are rejected. Closing/reopening the database keeps
the complete checkpoint, allyHP1/MP5, casterMP14 and battle revision3. Repeating
revival on the living target fails without mutating the restored state. No
settlement/reward row is created. Repository and revival CTest suites pass.

This is storage qualification, not live reconnect acceptance. Service Bound
action_received/control_received/initial_control_received/revival_opening_received
are not part of the stored battle checkpoint; Application's existing resume
path is a specific two-actor exchange and is not a three-actor revival restore.
Recovery must explicitly handle these protocol-phase differences before enabling
revival resume; do not remove existing configuration restrictions based on this
test alone.

The disk-reopen test additionally feeds the saved snapshot into the existing
three-actor participant encoder. It validates every record boundary in the
375-byte result, individual casterHP100/MP14, allyHP1/MP5, enemyHP150, matching
friendly bulk, caster grant and frame roundtrip. There is no83 action-effect
record or lethal prelude. Encoding leaves database resources/checkpoint and
in-memory state unchanged. Repository, revival and bootstrap CTest suites pass.
This validates the storage-to-packet projection; fresh native client consumption
and recovery-phase authorization are separate pending acceptance steps.

The same repository test now commits the successful transition through
RecoveredBattleService using the captured kind3/id8 logical request shape and
the actual Lua revival module, rather than directly calling the repository.
Its checkpoint callback compares the full before/after state against the domain
transition. Injected SQLite failure leaves both service memory and disk dead;
retry succeeds and returns the173-byte revival envelope only after commit.
Duplicate handling never reenters the callback. Disk reopen and projection
assertions therefore inspect the service-produced transaction. Repository and
revival CTest suites pass. This is an in-process integration test, not socket
reconnect or native UI acceptance.

## Explicit service phase recovery candidate

RecoveredBattleService now exposes trusted `checkpoint_revival` and
`restore_revival_phase` operations for the restricted revival diagnostic policy.
The envelope includes version, account/character, full BattleCheckpoint and
initial-control/opening/action/control flags. It is not a network record and
does not alter the version1 battle JSON or existing database rows.

Restore requires a fresh binding with identical full battle state and owner,
matching opening policy, and consistent flags. Wrong version/owner/revision,
control without action, opening without initial control, and restoring over an
already used binding are rejected before mutation. Tests reconstruct both
pending-receipt and receipt-complete phases: neither admits another action;
only the pending phase accepts its receipt, and explicit rearm permits the next
action. Five targeted suites pass (revival, repository, session battle service,
native revival state prefix and saved live evidence).

This is not yet a durable reconnect implementation. Phase serialization,
atomic phase/resource/checkpoint writes, exclusive session ownership and fresh
client bootstrap/receipt resynchronization remain necessary. No Application
route calls restore yet; existing resume restrictions remain intact.

## Canonical recovery envelope

`game/RevivalRecoveryCodec.h` now serializes the trusted revival envelope
with CUSTOM-0017/version1, account/character, canonical BattleCheckpoint string
and five strict boolean phase/policy fields. Decode limits input to64KiB and
nesting depth2; existing BattleCheckpoint validation independently bounds its
embedded document. It rejects wrong schema, types, owner, impossible flags and
noncanonical representation. Bare old battle snapshots are not recovery phases.

Both pending-receipt and receipt-complete tests now encode/decode before service
restore. Tests cover missing fields, nonboolean flags, invalid account types,
truncation, oversize, whitespace and owner/phase mismatch. Three targeted CTest
suites pass. No database migration, write route or live reconnect is enabled;
the next required integration is atomic phase plus resource/checkpoint storage.

## Atomic phase and resource storage

Migration12 adds nullable `battle_checkpoints.revival_document`; old rows remain
without phase, never inferred ready. The recovery value and codec now live in
the game layer. `commit_checkpoint` accepts an optional matching recovery value
and writes phase, battle document and resources in its existing transaction.
Loads validate canonical phase plus owner/full checkpoint identity. Active
updates cannot silently omit a previously stored phase. Terminal settlement
clears the now-invalid active phase in its transaction.

The actual C++/Lua revival integration test supplies the post-action/pending-
receipt phase from its checkpoint callback. Fault injection rolls all fields
back, reopening preserves the phase, mismatched owner and phase-dropping writes
are rejected. Terminal settlement and idempotent retry are tested. Five targeted
suites pass, followed by a successful repository rerun for terminal coverage.
Only temporary test databases were migrated, not owner saves.

Application does not yet supply recovery phases or activate revival resume.
Receipt-only/rearm transitions need atomic phase-only updates; exclusive new
session ownership and native fresh-client resynchronization remain open.

## Receipt-only durable phase transitions

`commit_revival_phase` now transactionally compares the full expected stored
checkpoint and resources, permits only pending-action to receipt-complete or
receipt-complete to rearmed, and changes only `revival_document`. It requires
active, unsettled, consistent state; no automatic phase creation for old rows.
Owner, battle, initial/opening policy and resource revision remain unchanged.

Tests reject skipping the receipt, changing battle revision, fabricating a
completed action from idle, and stale receipt/rearm retries. A SQLite trigger
failure preserves the pending document and resources. Another opened database
connection sees the committed ready phase. Rearm preserves HP/MP, battle/RNG
checkpoint and resource revision, and terminal settlement tests still pass.
Four targeted suites pass; server build succeeds. Wiring this API into service
receipt/rearm callbacks and live reconnect qualification are still pending.

## Service receipt and rearm transaction wiring

`set_revival_phase_commit` now attaches a single trusted callback to a qualified
revival binding with an action checkpoint callback. Receipt and rearm call it
before publishing in-memory flags. Exceptions leave the service phase unchanged.
Durable revival mode rejects mixed action/receipt batches, which have not been
qualified for this transaction path; default nonpersistent behavior is unchanged.

The disk-reopen integration test creates a new Session/service binding from the
saved envelope and processes the captured35/0B shape through this callback into
SQLite. Injected receipt/rearm UPDATE failures preserve memory and storage;
successful retries update both, and duplicate receipt never invokes storage.
Five targeted suites pass and the server is rebuilt. This is real handler/DB
integration with an in-process Session, not a socket reconnect or original-client
acceptance. Application still does not attach the new callback; live activation
and fresh-client handshake/phase resynchronization remain open.

## Own-server durable revival runtime

The isolated revival configuration now permits diagnostic_battle_resources.
Application requires a fresh character without saved resources, seeds80MP,
persists initial/death checkpoints, then binds action and phase-only callbacks.
Existing save restore inputs, world resources, terminal mode, and more than two
rounds remain excluded. No normal database or production mode is enabled.

Run `native-revival-durable-20260921-01` completes three natural batches1/1 with
no fallback (2634,2394,2041ms). Native followup resources are casterHP100/MP14,
allyHP1/MP5 and enemyHP132/max150. Read-only SQLite inspection agrees: character
resources revision5, battle revision4, recovery document contains the exact
battle document, and initial/opening/action/control flags are all true. No
settlement row exists. One173-byte revival reply, one156-byte attack response
and one second-round grant are recorded. Final heartbeat handling continues.

The runner deliberately observes to its limit and reports HARD_TIMEOUT; this
does not erase the specific completed evidence or certify world/reconnect
acceptance. A saved-evidence regression compares DB state to native vitals.
Config/revival/repository tests pass. Fresh-client reconnect remains untested.

## Saved-runtime resume projection admission

`diagnostic_revival_resume_participants` checks the qualified revision4,
receipt-complete envelope and exact three-actor diagnostic baseline before
emitting the existing375-byte state-only participant projection. It verifies
version, owner, phase flags, resources and actor template; it does not reset
phase or replay effects. This exact fixture gate is not a general restore policy.

The compiled `battle-revival --resume` test mode reads at most64KiB of canonical
phase JSON from stdin. The saved runtime DB recovery document passes, preserving
casterMP14, allyHP1 and enemyHP132. Clearing control-complete fails with no packet
output. Ten additional wrong-version/owner/phase/revision/resource cases fail.
Two targeted suites pass. The source DB is read-only; no new client connection
was launched for this admission test. Application restoration and native
new-session handshake still require implementation and runtime evidence.
