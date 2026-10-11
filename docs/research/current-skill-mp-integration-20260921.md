# Isolated skill MP response integration

## Evidence and scope

RecoveredBattleVitals already qualifies current native86 subtype1 through
1173A0: friendly-side MP uses maximum at logical+5 and current at+9. Hostile
MP does not have the same qualified actor-write path. This is a display/input
contract, not evidence for official skill cost or timing formulas.

Battle::act already checks ownership, living caster, targets and available MP;
it stages all target damage, deducts the configured cost once, then encodes
before committing state/RNG. RecoveredBattleService stages player action and
optional diagnostic retaliation together. The prior Application diagnostic
response emitted target HP only, with no dedicated caster MP record.

## Change

CUSTOM-0010 diagnostic_battle_mp encodes86/1 with explicit opaque zeros and
rejects positions14..27 or current greater than maximum. The isolated action
encoder emits exactly one such snapshot when result.mp_cost is nonzero,
before target HP records. Zero-cost basic attacks retain their existing wire
response. No production skill mapping, balancing or saved stats are changed.

## Verification

- Build: god2-server, recovered-battle-service, recovered-battle-bootstrap.
- CTest: recovered_battle_service, recovered_battle_bootstrap and
  recovered_battle_vitals pass.
- All14 supported friendly slots round-trip 32-bit MP123456/max654321.
- Hostile-side MP and current>maximum are rejected.
- Existing custom magical skill5 targets two enemies, deducts8 once from20,
  and returns one MP snapshot12/20 plus two HP records.
- A corrupted encoded skill reply leaves caster MP12, enemy HP48 and the
  battle revision unchanged; no partial damage/cost commits.

## Remaining work

Application's live diagnostic Policy.skills remains empty. The skill service
test uses synthetic requests and the existing custom Lua rule, not live native
skill selection. Qualify a current-client learned/selected skill, its original
producer, skill-specific action/effect reply and actual MP consumer in one
own-server run before claiming skill execution acceptance. Basic83 animations
must not be silently relabeled as skill effects. Original costs/formulas,
balance, combat-stat persistence and normal-input visual acceptance remain
separate open requirements.

## Fresh live prerequisites

Two fresh own-server runs `native-player-skill-prerequisite-20260921-01/02`
reach NATIVE_SOCKET_PARTICIPANTS_GRANTED. The observer only reads native
memory at the original grant return; it does not insert skills, alter selected
indices, fabricate a skill request or invoke unqualified skill functions.

Run02 reports current primary bank=-1, bank_count0, selected_index=-1 and
an empty bank list. Its upstream source also has current=-1 and row_count0.
This is direct evidence for this diagnostic fixture, not proof that the client
has no skill catalog or that all accounts lack learned skills.

Pinned original111667 reads battle+14;111677 adds90;111685 pushes this as the
selector initializer's seventh argument at1116A4 ->11BB80. The existing
current-character-binding proof qualifies source+CF/D4 -> selector+4/5 and
row pointers. Thus the empty live selector agrees with its empty upstream
actor-row source, rather than merely an unselected entry in a populated bank.

The next integration boundary is the existing native S2C30 actor-row producer
and S2C34 learned-skill writer before battle initialization, followed by the
qualified87/38 state/selection contracts and actual command producer. Existing
writer proofs stop before refresh and use explicit test rows; they do not
authorize assigning an official starter skill or mapping a fixture key to
the real character. Qualify those remaining branches before live emission.
A regression preserves the empty-source observation; no fake skill ownership
or direct client-memory patch was introduced.

## Low-key actor rows are metadata-backed

The next original branch is now executed in
tests/research/test_current_skill_source_low_keys.py. All198 combinations of
absolute keys1..99 and positive/negative signed packet keys run AA040 through
the real59A60 lookup and name copy, stopping BEFORE refresh AA1B5. This uses
explicit synthetic metadata names and a pointer table, not native-loaded
metadata or official owned skills. No game callee is stubbed.

For these keys, AA139..AA145 looks up item-metadata index2800+absolute_key
through UI+CFF70. The name comes from the returned record+8, not the supplied
packet name. The writer appends one row with that absolute WORD key. A negative
packet key selects the appended row via source+D0 and source+CF; a positive
key does not select it. Tests verify each name, key, row count and selection.

Inspection of the pinned current gamedata shows ItemType's2801..2899 range
tagged GOD and a GOD section containing34 rows. The generic item metadata
helper does not currently implement that section's loader/tag path (an
exploratory attempt correctly failed rather than returning invented data).
This range association is a resource-source lead, not proof of a player's
class, official starting ownership, or complete immortal gameplay semantics.
The previous phrase "actor rows" must not be silently interpreted as a
generic player skill book. Actual GOD metadata loading, refresh and ownership
projection remain prerequisites before using low-key rows in the live fixture.

## Runtime GOD metadata qualification

Fresh own-server run `native-player-god-metadata-20260921-01` reaches the
native participant grant and reads the real metadata owner via battle+20,
UI+CFF70. It inspects B2D40+4*key for keys2801..2834 and bounded name bytes at
each nonnull record+8. All34 pointers are present. Every observed name matches
column4 of the corresponding GOD row in the hash-pinned current gamedata.
The regression derives the expected keys/names from the parsed section rather
than hardcoding translations. This is live metadata lookup evidence without
injecting metadata pointers or bypassing its normal loader.

This supersedes any suggestion that the live fixture lacks GOD name metadata.
It does not qualify the untraced generic-parser branch, nor imply owned rows:
the same run still has source_row_count0 and no skill banks. The next actual
integration step remains an isolated explicit S2C30/34 ownership fixture and
the full original refresh path, with custom assignment provenance. Names and
catalog identities must not be mistaken for original skill assignments,
ability values, growth formulas or a completed playable skill system.

## Isolated live initialization chain

CUSTOM-0012 adds default-off diagnostic_battle_skill_seed, requiring the existing
player/participant/transition/loopback/isolated-DB gates. Before82 it sends the
explicit19-byte30 selected key-1 and4-byte34 key1/bank0/entry1. It does not
persist ownership, modify client tables directly or enable a server skill rule.
Current native metadata supplies the low-key name rather than guessed text.

Run `native-player-skill-seed-20260921-01` reaches participant grant after these
packets and native refresh: source current0/count1, selector current0/count1,
but battle bank entry_count0. Learned source and active battle skill population
must therefore remain distinct integration stages.

The server now additionally prepends `87 01 80` to the deferred participant
response after native battle initialization. Fresh run
`native-player-skill-seed-20260921-02` reaches participant grant and reads:

- source_row_count1, source_current0, first_source_learned_count1;
- bank_count1, current_bank0, bank0 entry_count1;
- first state WORD8001, actual pointed definition identity bytes0100;
- selected_index remains-1, raw bank state remains0.

This is real original-client packet processing through previously unexecuted
refresh paths, not an emulator-only result. The test verifies the two runs and
their distinct scope. Config/default and bootstrap CTests pass. The seed is an
explicit custom test assignment, not evidence for official starter ownership.
Original selection/cast, server skill authorization, cost and skill effects are
the next integration boundary; this result does not claim a cast or UI click.

## Fresh live hotbar boundary

Run `native-player-skill-hotbar-20260921-01` completed against the isolated
own server with result `NATIVE_SOCKET_PARTICIPANTS_GRANTED`, no harness error.
The same enabled entry WORD8001 exists, but selection remains -1. Read-only
native getter inputs show UI mode1, source row0, battle action mode1, and
all ten primary six-byte hotbar records equal FFFFFFFFFFFF. The alternate
60-byte table is zero. Thus populated skill ownership and battle availability
do not imply populated hotbar bindings in this fixture. This is a bounded
fresh runtime observation, not proof that manual skill selection is impossible.

The observer reads source row count as the native byte at +D4, and reads a
primary table only for source rows0..15. It neither writes bindings nor changes
the selected index. Existing full-entry offline selection qualification used
mode3 and populated bindings; this fresh mode1/empty-binding result explicitly
does not inherit that fixture's successful selection claim.

Next concrete source lead: pinned instructions AA98B write WORD2 at
UI+A3D54+6*(slot+10*source_row), with adjacent writes filling kind/id. The
surrounding producer, its trigger and state requirements remain to be traced
before attempting native binding/selection in the live fixture. Do not patch
the table to bypass this missing transition. Production remains unchanged.

## Hotbar producer conditions and local persistence

Pinned AA830 receives a three-byte body (row key, kind, entry ID), scans the
owned rows and matches the learned definition pointer. It sets the matched
learned-entry flag to3 at AA907, calls A9750, and for the selected row calls
A9510. Only after those refreshes does AA92A inspect UI+232EAC. A nonzero
flag permits writing `(WORD2, WORDkind, WORDid)` into the primary hotbar at
the matched learned-entry index; AA995 clears the flag. This inspected path
does not bound that learned index to ten. Do not enable it for arbitrary
learned lists without tracing the surrounding contract.

The flag is armed at84E14 only when the native event WORD equals0327.
`test_current_skill_hotbar_binding.py` executes that entry prefix in ten
event/prior-state fixtures and the independent post-refresh writer window
in320 row/slot/flag fixtures. Exact960-byte table comparison and recorded
write-address checks pass. All three tests pass. The tests stop before the
unqualified UI call or after the writer; they do not stub refreshes or claim
continuous execution of the complete AA830 handler.

Static current-image evidence also identifies a separate local persistence
route: format string VA585670 is `%s\\%s.hky`, directory VA58567C is `Save`,
with `wb`/`rb` strings at VA58234C/VA582350. AFFxx/B000x writes a60-byte
general table and960-byte primary table; B00B0 constructs the path and loads
local state. Full read layout, transformed character-name filename, call
timing and live loading remain unqualified. This is a concrete next route
for preparing isolated test hotkeys through the original loader, not grounds
to overwrite existing player files or inject binding memory.

## Native hotbar file loaded in fresh session

The read sequence at B01BE/B01CC/B01DD/B01F4/B0220/B024F requests
60,960,36,4,4,4 bytes (1068 total). Final settings destinations overlap at
+452E/+4530/+4532; the fixture is a labeled test preference, not a recovered
official default. B026F ORs38 into the first settings byte. The caller at
81A91 passes secondary actor source+B7 and stores the loader return at
UI+A3D14. Fresh run native-player-hotbar-loader-20260921-01 observes fopen
failure for the work-copy Save/CodexTrial.hky and still-empty primary table.

Default-off --diagnostic-battle-hotbar adds a CUSTOM-0012 file fixture with
exclusive creation, capture-work path restriction, input/final archives and
cleanup. A fresh run native-player-hotbar-loader-20260921-02 observes fopen
success and, at participant grant, primary bytes020000000100 followed by
54 FF bytes. Alternate slots remain FF. Selected index is still-1. The
original loader, not debugger memory writes, installed the binding. The
temporary file is absent after the completed run. Regression tests check
the two live observations, exact fixture size, exception cleanup and refusal
to overwrite existing player data. Native selection, mode transition, target
setup and casting remain next; this does not prove rendered UI acceptance.

## Full original selection in live client

Fresh own-server run `native-player-skill-select-20260921-01` completes with
`NATIVE_SOCKET_SKILL_SELECTED`. Opt-in --probe-socket-skill-select requires the
isolated hotbar fixture and excludes the basic-action probe. An immutable RX
thunk calls the full original1151A0 entry with slot0 and an eight-byte owned
stack context. The latter is necessary because115661->11F2A0 writes two target
counts at context+4. The thunk does not assign selection, mode or target masks.

Before entry, live selection is-1 and action mode1. After native return, the
stack is restored, RX bytes unchanged, selection0 and mode3. Target masks are
(1,1), setup DWORDs at45C are(1,0,3,1), and target counts are(1,1). This runs
the real mode-change, UI setup and target initialization callees that the
previous offline test deliberately stopped before. The temporary hotbar is
removed after completion. Six hotbar tests pass including the retained live
run, exact thunk bytes, selection transition and fixture preservation tests.

This is native-function invocation, not physical input or visual acceptance.
It does not send a skill command, consume MP, settle damage or certify a skill
formula. The next boundary is native command production from this selected
definition and independent server authorization/effect encoding.

## Live native skill command producer

Run `native-player-skill-command-20260921-01` completes full native selection
then calls118E50 with action3, actor0, explicit target14 and count1. The
default-off --probe-socket-skill-command requires the native selection probe.
Original calls return with restored stack and unchanged RX thunks. The native
queue contains exactly17 bytes: `3500030037000001000000000001000000`.
Controls become blocked1/first-grant0/second-grant0. This is native queue
production, not a flushed socket or server settlement claim.

The rebuilt C++ recovered-skill-command --decode-sequence accepts that record
as actor0, no continuation, side0, masks(0,1), context0, selection-ID byte1.
Byte4 is observed opaque stack value37, not a constant to impose on future
records. Unlike the old per-target offline fixture, this live selection has
468==1; its single-target output fits the existing structural subset. This
does not extend the parser to all aggregate/multi-target branches. Seven
hotbar/selection/command regressions pass; the CTest decoder suite also passes.

The command has not been authorized or settled by the server. No MP, damage,
formula or balance result follows from its successful construction. Next:
explicit isolated skill policy, actual socket dispatch, and separately native
MP/result consumers. Do not encode skill effects as basic attacks merely to
reuse the current diagnostic animation helper.

## Isolated server skill settlement and live scalar acceptance

Default-off diagnostic_battle_skill_settlement authorizes selection ID1 only
inside CUSTOM-0012 diagnostics. It requires seed/player/participant/loopback/
diagnostic database gates, one round, and rejects animation/terminal modes.
C++ policy supplies magical150%, defense100%, MP8 and zero critical chance;
existing labeled Lua combat arithmetic yields54 damage for attack40/defense6.
The C++ transaction validates and encodes MP/HP plus existing12-damage
retaliation before committing. No native formula or production balance claim.

Run native-player-skill-settlement-20260921-01 reached enemyHP96 and player
HP88/MP42 but ended HARD_TIMEOUT: the observer incorrectly monitored only
117230, missing separate MP entry1173A0. It remains a failed run. After
correcting the observer, fresh run native-player-skill-settlement-20260921-02
completes NATIVE_SOCKET_SKILL_VITALS_SETTLED with three original receiver
returns in order:

- MP record8601000000500000002A00000000000000: player100/42/max120/80.
- HP record86000E0000960000006000000000000000: enemyHP96/max150.
- HP record8600000000780000005800000000000000: player88/42/max120/80.

The original command is resumed through normal socket processing; this is no
longer queue-only evidence. The observer does not inject replies or mutate
actor values. Temporary hotbar cleanup completes. Config, battle service and
bootstrap CTests pass, as do eight hotbar/skill regressions including exact
wire scalars, native actor values and the retained failed-run boundary.

Still unqualified: skill animation/effects, normal physical selection/input,
rendered feedback, turn rearm after skill visuals, repeated casts through
insufficient MP, HP/MP persistence, and production balance. No basic83 action
is emitted as a substitute skill effect. Production configuration remains off.

## Distinct skill effect encoder qualification

`diagnostic_battle_skill_animation` now prepares a15-byte83/03 record with
kind0/id1 at offsets11/12, source and opposite-side target mask, action group,
and negative signed16 HP-loss display operand. It reuses the bounded envelope
construction but overwrites the action with3 and explicitly supplies identity;
it does not emit action1 as the skill. It is not activated in Application yet.

The C++ bootstrap executable's --diagnostic-skill-effect produces
830300000000000100CAFF01000000 for source0,target14,loss54. The native oracle
now accepts an explicit record plus matching target position and continuously
executes12C520 through12B619 with the actual cross-side target. The selected
catalog pointer and state3 are produced by original code, and the received
FFCA reaches the effect WORD store. Record identity/masks/amount must match;
malformed or mismatched input is rejected by the harness.

C++ tests cover all392 opposite-side position pairs, signed display bounds
and invalid positions; native amount tests retain all448 definitions and add
the exact C++ cross-side output. Six Python tests and bootstrap CTest pass.
The native fixture explicitly preloads the skill cache and stops at the store:
resource loading, fresh effect-state reset, animation completion and live
rendering still require verification. No coefficient/formula is recovered by
copying a received amount. Next: isolated server activation and original
resource/animation consumer observation, without weakening production gates.

## Live skill and retaliation action completion

Both default-off diagnostic_battle_skill_settlement and diagnostic_battle_animations
now enable83/03 for the MP-consuming player skill, group0, and83/01 for
retaliation, group1. Terminal/multiple-round skill modes remain rejected.
No change to normal production activation or the custom rule's provenance.

Fresh run native-player-skill-animation-20260921-01 completes with
NATIVE_SOCKET_SKILL_ANIMATIONS_COMPLETED. After the native selected-skill
command is flushed and the server replies, MP42 and enemyHP96 arrive, followed
by original animation batch completion expected1/completed1 at2410ms. The
source's native current-definition pointer resolves to bytes0100. Retaliation
then updates playerHP88 (MP stays42), and batch2 completes1/1 at3023ms. The
original finalization call returns after both batches and all three scalar
updates. Neither completion uses the10-second timeout fallback.

Nine hotbar/skill tests pass, with a new regression enforcing scalar/action
ordering, identity, both natural completion counters and finalization. Config,
battle service and bootstrap CTests pass. This supersedes the earlier
unqualified live-cache/playback boundary for this single fixture only; it does
not establish all skills' resource completeness or visual correctness. Normal
input, rendered effects, repeated/rearmed skill turns, insufficient-MP UX,
rewards/persistence and production balance remain open acceptance work.

## Two consecutive skill rounds in the same session

Skill diagnostics now permit the existing bounded two-round mode, but require
animations for more than one round. Server rearm code is unchanged: it waits
for an accepted completion notice and calls rearm_diagnostic on the existing
battle revision. No combatant reset or service rebind was introduced.

Fresh native-player-skill-two-rounds-20260921-01 completes with six original
scalar receiver returns and four natural1/1 animation completions at
2466/3026/1841/3186ms, all without timeout fallback. Round1 grant/command
sequences497/500 precede round2 grant/command564/567. Round2 grant follows
first-round animation completion549. MP50->42->34, enemyHP150->96->42 and
playerHP100->88->76 accumulate on the same live session. The server log has
exactly one DIAGNOSTIC_NEXT_ROUND_GRANTED and no rejected batch. Finalization
returns after batch4, and the temporary hotbar is removed.

The observer retains each grant, selection, command and three scalar updates
under socket_skill_rounds. Ten hotbar/skill regressions and config/battle-service
CTests pass. This qualifies two rounds of this fixture, not all skills,
unbounded encounters, insufficient-MP behavior, terminal rewards, persisted
HP/MP or production balance. Those acceptance items remain open.

## Insufficient-MP transaction boundary and native menu caveat

The C++ battle-service regression now tests availableMP0..8 against the
explicit custom fee8, including a combined skill+completion batch. For0..7,
the domain rejects before Lua or encoding callbacks; MP, both actors' HP and
revision remain unchanged. No completion receipt/rearm is admitted. A basic
attack still succeeds afterward, proving failed skill admission did not consume
the action. At8, one skill and one retaliation commit, MP becomes0, the receipt
is accepted and replay is rejected. The rebuilt battle-service CTest passes.
This is service/domain evidence, not live insufficient-MP recovery UX: domain
exceptions and the socket/session response remain to be qualified separately.

The actual pinned definition kind0/id1 has WORD+42=5 but BYTE+67=0. New
native-predicate regression executes A9070/A90D0 for MP0..8: both return false
for the unchanged record because the flag gate rejects first. An explicitly
counterfactual copy with flag1 isolates the >=5 threshold; it is not installed
in the client. An initial assertion expecting a nonzero native flag failed and
was corrected after inspecting the pinned bytes. Therefore do not claim that
native menus permit this skill atMP5..7, or equate these menu predicates with
the previously executed battle-hotbar entry1151A0. Context reachability and
ordinary input behavior remain distinct open checks.

Custom fee8 also differs from native display/cost field5; retain the mismatch
as a production blocker until the authoritative mapping and native cast
context are reconciled. No native client record or production setting changed.

## Real TCP insufficient-MP rejection is not recoverable yet

The extended session_battle_service CTest performs three actual loopback TCP
sessions atMP0/5/7 against the explicit fee8. Each establishes the existing
authenticated character/world handshake, then uses explicit test-only battle
admission. A fragmented native35/03 record must not reach game policy until
the final byte arrives. On complete input, the real Session -> world service
-> battle service path calls policy once, never reaches the result encoder,
and closes the connection. Battle revision1 and all HP/MP remain unchanged.
The rebuilt CTest passes in3.30s; this is a verified failure boundary, not
successful insufficient-MP gameplay handling or a native-client UX test.

Current source explains the disconnect: Battle::act throws invalid_argument
for the combined ownership/life/MP predicate; Session catches handler failures
and leaves accepted=false, then fails with Recovered world policy or response
rejected. Therefore the earlier domain-only ability to issue a basic attack
after rejection does not imply the connected player can do so.

Next required implementation must distinguish a recoverable resource refusal
from malformed, unauthorized and stale input without relaxing those checks.
Before claiming recovery, qualify the actual native-client message/control
sequence that restores its consumed grant and target mode, then exercise a
failed skill followed by a successful basic action on the SAME TCP connection.
Do not silently return success/empty bytes: native command production already
consumes the local grant, so keeping the socket alone would leave a stuck turn.

## Typed resource refusal prerequisite

Battle::act now raises InsufficientBattleMp(available,required) only after
source/controller/life and every target pass validation. It remains derived
from invalid_argument, preserving existing fail-closed callers until an
explicit recoverable response path is installed. Friendly, missing, duplicate
or dead targets must not be classified as a recoverable MP refusal merely
because the caster also lacks MP. Revision/parameter checks still precede it.

The service boundary regression checks exact available0..7/required8 values,
rejects friendly/missing targets as ordinary invalid_argument and rejects a
foreign client actor without admitting it as a resource refusal. No Lua or
encoder call occurs on these failures; existing transaction/retry assertions
remain. Rebuilt battle-service and actual TCP session-battle-service CTests
both pass. Session still disconnects on the typed exception; no claim of a
working network recovery, error message or restored client grant is made.

## Opt-in refusal callback: TCP evidence, not client acceptance

CUSTOM-0012 adds a default-empty diagnostic_mp_refusal policy callback,
permitted only with diagnostic_single_action. It handles only the initial
player's typed resource refusal after authorization and target checks, with
one action, one target and no initial/completion control in the batch. The
reply must pass existing framing/checksum validation before return. No staged
battle state, resource, revision or admission flag is committed on refusal.
Application does not enable this callback.

Actual loopback TCP regressions at MP0/5/7 use a synthetic peer and a candidate
MP snapshot plus grant reply. A subsequent basic action succeeds on the SAME
connection: enemy HP100->82, MP unchanged and revision1->2. The rejected skill
has no mutation. Existing no-callback tests still verify fail-closed behavior.
Additional domain tests reject non-diagnostic binding, mixed skill/completion
batches, empty or malformed replies and throwing encoders; failed replies do
not prevent a later valid domain-level basic action.

Both recovered_battle_service and session_battle_service CTests passed after
these changes (5.60 seconds total). This does not qualify original-client
control restoration, normal input, visible refusal UX or gameplay balance.
The owner requires documented balance validation AND current-client acceptance
against our own server before custom rules enter production. These gates remain
unfulfilled; the fee8/native-field5 discrepancy remains unresolved.

## Refusal regrant prerequisite: waiting latch is conditional

Reinspection of the SHA256-pinned current image confirms grant117590 calls
115670 and115740 after setting first grant at battle+A9E9C38. Both helpers
reach1121F0 only when battle+A9E9C28 is zero and battle+A9E9C64 is not -1.
Existing instruction tests identify the waiting-latch clear at11223B within
that rearm path. Do not equate setting first grant with clearing waiting.

The added test_refusal_regrant_helpers_can_return_with_wait_still_set executes
each complete helper from entry to return with explicit synthetic state:
first grant1, second0, waiting1, and (panel,counter)=(0,-1),(1,0),(1,1).
All six executions return with waiting still1 and never visit1121F0.
All13 current_battle_command_gate tests pass. This refines the existing gate
evidence; it does not prove the full grant handler fails or succeeds, because
later native UI/selection helpers have not been executed in these cases.

Next live refusal qualification must capture A9E9C28/A9E9C64 and waiting at
command completion and grant entry/return, then verify a second command through
the original producer on the same connection. Do not patch those fields or use
the synthetic TCP peer's success to assert that this client gate was satisfied.

## Live rearm snapshots and targeting limitation

Run native-player-skill-rearm-state-20260921-01 completed with
NATIVE_SOCKET_SKILL_ANIMATIONS_COMPLETED. Read-only snapshots show panel0,
counter0 at first command return and counter1 at second command return;
each command leaves waiting1 and both grants0. Second grant entry has
waiting1/panel0/counter1; its native return has waiting0/first grant1/second0.
This proves real regrant clearing in the successful-settlement path, NOT yet
the insufficient-MP refusal path. The temporary hotbar was removed after run.

Important acceptance gap: first selection reports target counts0101/masks1,1;
second selection reports counts0000 and both masks zero despite selected index0
and action mode3. The diagnostic producer receives explicit target14 and still
settles, so this cannot certify ordinary player targeting in the second round.
Preserve this observation in regression evidence and investigate the native
target-selection inputs before calling this repeated skill gameplay accepted.
No production promotion or balance approval follows from this run.

## Fixed living-target removal in diagnostic animation packets

Hardware write watches in native-player-skill-mask-writers-20260921-01 locate
both living-side masks being cleared by native129D9C (post-write PC529D9E).
This path requires animation state9 at129CD8, also zeroes actor HP at1299F5.
Pinned converter12C000 uses table171610: received index0 becomes state9,
index28 becomes state0. The previous opaque zero was therefore NOT neutral.

Native caller slices prove different logical offsets: basic83/01 byte12
(12C636 loads raw+0B); skill83/03 byte14 (12C865 loads raw+0D). An initial
byte14-only repair, surviving-targets-20260921-01, preserved the enemy but
not the player struck by basic retaliation. Retain this partial run as evidence.
The final encoder uses byte12 for basic, byte14 for skill, keeps skill bank0
at byte12, and chooses28 for positive authoritative post-hit HP or0 for zeroHP.
No runtime memory/state patch was used to preserve these masks.

Run native-player-skill-surviving-targets-20260921-02 completes both rounds:
both selections have masks1,1/counts0101, no mask write-watch hits, four1/1
animation completions without timeout fallback, and temporary hotbar cleanup.
The observer now rejects missing fixture targets before the explicit-target
command probe. Two native outcome tests cover caller offsets and table mapping;
C++ bootstrap covers live/lethal encoding and existing position/delta bounds.
An initial DWORD assertion was corrected to BYTE argument semantics because
native MOV AL retains unspecified high register bits; no code was patched.

This is native protocol-field recovery and a diagnostic server fix. It is not
original damage/balance recovery, physical-input acceptance, low-MP recovery,
or live verification of lethal combat/result/world return. Those remain open.

## Post-fix lethal basic battle, world return and fresh restore

Run native-player-outcome-fixed-terminal-20260921-01, using the rebuilt server
and corrected animation outcome encoder, returns NATIVE_MOVEMENT_PATH_COMPLETED.
The explicit diagnostic lethal basic attack takes enemy HP to0; native damage,
zero-award outcome, outcome-panel return, battle-loop return and world reentry
are observed at sequences514,545,547,549,551 respectively. Three original
movement requests complete with motion state0 at18,12. Read-only SQLite query
confirms recovered_positions=(character1,area2,scene15,x18,y12,revision3).

Run native-player-outcome-fixed-restore-20260921-01 starts a new server/client
session with a read-only SQLite backup of that isolated database, not reused
client memory. It receives the existing character and returns
NATIVE_SAVED_POSITION_RESTORED after native world-frame execution reads18,12.
The regression checks both session artifacts and the copied database row.

This closes post-fix regression of the existing lethal BASIC/zero-award path
and saved WORLD POSITION restore only. Skill-lethal handling, MP refusal,
combat resource persistence, actual rewards/EXP, balance, general quests and
normal player input/visual acceptance remain separate incomplete requirements.

## Isolated lethal skill closure

Terminal skill settlement is now permitted only with existing isolated skill
seed/player prerequisites, animations and a single terminal round. Config tests
reject terminal without animations and terminal with multiple rounds. This
CUSTOM-0012 fixture uses power1000% instead of150%, fee8, crit0; no production
balance or original-formula claim. The server uses post-hit HP to encode death.

Run native-player-skill-terminal-20260921-01 returns
NATIVE_MOVEMENT_PATH_COMPLETED. One native skill command yields exactly two
observed scalar settlements: playerHP100/MP42/max120/80, then enemyHP0/max150.
There is no retaliation or second MP debit. One skill animation retains native
definition0100 and completes1/1 without timeout; zero-award outcome, outcome
panel, battle cleanup and world reentry follow. Three movement requests save
character1/area2/scene15/x18/y12/revision3 in the isolated database.

This extends the prior basic terminal proof to this one diagnostic skill.
The observer requires the two-record order before arming outcome observation.
Regression evidence asserts one command, one debit, one animation and ordered
world return plus the SQLite position. Combat resource persistence, actual
rewards, low-MP refusal recovery, general skill coverage and balance remain open.

## Default-off Application low-MP fixture

development.diagnostic_battle_mp_refusal now installs the existing guarded
diagnostic_mp_refusal callback in Application only with skill settlement,
animations, one round and no terminal. Existing skill-seed/appearance/loopback/
isolated-database gates still apply. Initial Battle MP and both client scalar
and bulk MP are7, maximum80. The refused fee8 action returns actual MP and
first grant for actor0; it does not commit a hit, resource debit or turn advance.

Bootstrap tests cover initial MP0/7/8/50/80 and reject81, ensuring only the two
MP bytes change from the default packet sequence. Configuration tests reject
missing prerequisites, terminal and multiple rounds. Rebuilt server/tests and
config, recovered_battle_bootstrap, session_battle_service CTests pass.

This is prepared integration, NOT current-client refusal acceptance. The runner
still needs explicit refusal observation and same-connection basic retry before
the feature can be called usable. No production settings were changed.

## Current-client low-MP refusal and basic retry

The runner now accepts --diagnostic-battle-mp-refusal only with one animated
skill-settlement round and no terminal. It checks the initial MP7 bulk, observes
the actual native MP receiver returning unchanged HP100/MP7/max120/80, then
observes a new grant with waiting0/counter0 before invoking the original basic
command producer. No grant, MP, selection or waiting field is patched.

native-player-skill-mp-refusal-20260921-01 stopped with TOOL_ERROR because the
old observer still expected initial MP50. This was a fixture expectation error,
not client rejection, and is retained. After fixing that explicit expectation,
run02 returns NATIVE_SOCKET_ANIMATION_ROUNDS_COMPLETED. Original action3 is
followed by refusal/first grant, then action1; enemyHP150->132, retaliation
playerHP100->88, MP stays7, and two batches complete1/1 without timeout.
The temporary hotbar is removed. Regression checks the values and event order.

This qualifies this isolated recovery sequence through actual current-client
native functions, not physical player input or visible insufficient-MP text.
It does not certify official debit timing/fee, production balance, repeated
refusal/replay handling beyond existing service tests, or resource persistence.

## Whole-exchange persistence boundary prerequisite

RecoveredBattleService::bind accepts an optional Commit(before,after) callback.
It runs only after player and optional retaliation actions and ALL reply-frame
validation, immediately before the noexcept staged Battle move. A resource
refusal, rejected input or malformed reply never reaches this boundary. Storage
implementations must commit atomically and roll back before throwing; callbacks
must not reenter or send. Existing callers default to no persistence callback.

New domain regression injects malformed encoding (zero commit calls), then a
storage exception (revision1, HP100/MP20/enemyHP100 remain), then successful
retry (one complete exchange, revision3, HP88/MP12/enemyHP66). A replay cannot
commit again. Rebuilt server/domain/TCP tests pass. This is NOT actual SQLite
resource persistence: no repository schema or Application storage binding has
been added yet, and no restart durability or crash recovery is claimed.

## SQLite resource repository

Migration6 adds an empty character_resources table, referencing recovered
characters, with HP/MP/maxima range/type checks, positive signed64 revision
and explicit CUSTOM-0012 provenance. It creates no defaults or character rows.
The SQLite repository validates ownership on reads/writes, compares the entire
expected resource snapshot inside BEGIN IMMEDIATE, assigns the next revision,
checks affected rows and reads back exact values before commit. RAII rolls back
on write/readback failures; caller-supplied next revision is not authoritative.

Repository tests cover insert/load, combined HP/MP update, foreign-account
read/write, stale version, MP bounds, false native provenance, trigger-induced
readback corruption and retry after rollback. Existing profile/account/position
invariants remain checked. Database and both recovered character/position CTests
pass. No Application callback binding or fresh-client resource restore exists
yet; this supersedes only the missing SQLite-schema/repository part above.

## Battle service to real SQLite transaction integration test

The recovered_battle_service CTest now binds its Commit callback to the actual
SQLite repository, using all current migrations, an owned recovered character
and resource row. A real SQLite BEFORE UPDATE trigger raises ABORT on the
skill+retaliation exchange. Both database resources and bound Battle remain at
their pre-action state; removing the trigger permits retry. One successful
exchange saves HP88/MP12 at resource revision2, while Battle advances from1 to3.
Loading through a new repository object returns those values, and replay never
attempts another commit. The rebuilt test passes.

This database is in-memory: a new repository object is NOT a fresh connection
or process restart. No disk durability or current-client resource restoration
is claimed. Application binding and new-connection restore are still required.

## Default-off Application resource binding

development.diagnostic_battle_resources now requires skill settlement and its
existing isolated loopback/database prerequisites. The repository interface
exposes load/commit resources. At diagnostic admission Application reads owned
resources, seeds CUSTOM-0012 only when absent, rejects mismatched maxima120/80
or zeroHP, and uses saved HP/MP for both native bootstrap records and Battle.
It binds Commit to repository CAS, checking the old actor values/controller
against the captured saved row before committing the complete exchange.

HP bootstrap tests cover1/88/100/120, reject0/121 and verify scalar/bulk agreement.
Full build finished, then all six config/database/bootstrap/battle/repository/
TCP battle CTests passed. The earlier test invocation while compilation was
still running is not the final verification; the post-build run is authoritative.
This option has not yet been driven through the native runner, and no fresh
client or disk-restart resource acceptance is claimed. Production stays off.
