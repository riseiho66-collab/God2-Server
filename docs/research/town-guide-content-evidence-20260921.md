# Town Guide Content Evidence

## Current source

Mission_data.csvZ SHA256
659c8f38ffd9c34107969b449afd16488665a08970110910c9aed8448a0bb716:
mission1, source definition line4, description lines5/6, two descriptions.
The first describes speaking to Tu Di Song at110/110, then visiting Song Di Tu
near the weapon shop116/62. The second describes returning to Tu at110/110.
Names below are matched using their exact CP950 bytes in the regression.
These are presentation text coordinates, not verified spawn coordinates.

gamedata.csvZ SHA256
70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731:
NPCAppearData contains4043 definitions. Source lines739/740 contain unique
exact-name definitions1606/1607, both appearance20, remaining fields0,1,0,0,0,0.
This establishes the appearance definitions matching the text names, not their
live spawn identity, position, mission assignment or server script.

## External cross-check

Owner-supplied Bahamut wiki:
https://wiki2.gamer.com.tw/wiki.php?n=8591%3A%E6%A5%93%E8%8F%AF%E9%8E%AE
retrieved2026-09-21. It describes the same three-contact sequence and reports
reputation+1 plus a Jin Ao Island map. It gives111/111 and118/66, unlike the
current client's110/110 and116/62. Its build is unspecified. Rewards and
coordinates are community reference claims, not pinned current native rules.
Do not overwrite current source coordinates or grant these rewards as verified.

## Next qualification

Use current native appearance loader/runtime catalog to qualify1606/1607 and
appearance20 before constructing an owned-server spawn experiment. Resolve
the current Feng Hua town map, navigation and actual spawn placement separately.
Mission1/description selectors supply UI text only. Acceptance, revisit,
completion, reward item identity, reputation transport and persistence require
their own evidence or an explicitly labeled custom design. The current531
diagnostic NPC is not either of these NPC definitions and must not be relabeled.

## Live Catalog Qualification

native-town-guide-catalog-20260921-01 extends the existing read-only observer
to1606/1607 and resource ordinal19. Both native94-byte templates contain the
exact CP950 names from the current source, flags0x4000 and appearance20 at
offsets0x10/0x12. Initial NPC pools remain empty. The existing isolated531
conversation/cancellation completes without error; the target NPCs are not
spawned or substituted by this experiment.

Current resource ordinal19 identifies data2/rom/npc/npc2720.ROM, action count16,
palette6, loaded slot-1. This is an unloaded resource in the observed scene,
not evidence of a missing file or a failed loader. Native appearance20 loading
and spawn consumption must be qualified before visual/world activation.
The source and saved-live regression both pass. This narrows the next work to
the original resource-loading path, not an assumed name/appearance mapping.

## Original Loader Qualification

Current npc2720.ROMZ is403358 bytes, SHA256
bd9ce48fd0b23226858e4efe2a0b3bb42ab37c26314297bbc0f9af2a81b47d8d.
Decoded519564 bytes SHA256
ed12b235fd24d7961f7ed8766180c3e56456d5acf71c57a86b92297bd25e2836.
The bounded NativeNpcResources oracle now permits pinned ordinal19.

Original5F0E0 ->5EEC0 ->29820 ->1EC0 ->2A1D0 loads this asset, changing
lookup fromFFFFFFFF toslot0 in an explicitly empty test bank. The original
counter advances once. Independent PCX RLE comparison verifies all80 image
buffers and8 palettes; all decoded bytes are consumed. A repeated native load
keeps counter1 and opens no second file. No native function return is stubbed.
Existing CRT/file/allocator adapters and RGB555 test surface remain explicit.

First attempt exhausted the default bounded emulator allowance. An opt-in
threefold allowance completes; original defaults remain unchanged for other
tests. The existing pixel checker expected60 images from older assets; only
its per-resource expected count was parameterized, not pixel verification.
The focused loader test passes. This proves offline asset loading/cache, not
live scene preload,72-triggered loading, rendered sprites or physical selection.

## Live Original Loader

native-town-resource-load-20260921-01 invokes original45F0E0 with the observed
active table, group0 and ordinal19, on the guarded client's world-frame thread.
The diagnostic thunk preserves caller registers/flags and checks stack return.
The resource's loaded slot changes from-1 to nonnegative. Other observed
resources, NPC templates and both actor pools remain unchanged; a later world
frame returns. Result NATIVE_TOWN_RESOURCE_LOADED has no error.

No game function body, client file or resource slot is patched. The call itself
is explicit instrumentation, not a normal scene-preload event. This qualifies
the real process's loader/environment, not automatic72 handling, sprite display
or quest gameplay. The next experiment must establish the normal caller path
or clearly label any server/client compatibility mechanism as custom.

## Correct Scene Resource Group

Current pinned map catalog row21082 identifies CityI1 / Feng Hua town as
area2, scene4, kind0 (MDT Island01/CityI1/cityi1.mdt). The configured native
map table independently contains the same tuple and raw source row.
Current NPCList rows beginning4229 supply46 resource codes for2/4, including
20 exactly once. Initial diagnostic scene2/15 instead contains only21,2143.
Thus absence of ordinal19 from that diagnostic scene's loaded bank is
consistent with its actual group and does not establish a broken resource.

Source regression checks both groups and the pinned map record. The native
5AA70 lookup test checks scene4/count46 and the exact category0/code20 pair
stored by the original group loader. This identifies the normal scene input
to qualify next: enter2/4 and observe native preload, instead of silently
inserting a loader call into the production client. Neither resource grouping
nor map identity determines the NPCs' precise spawn positions.

## Natural Town Preload Observed

Run `native-town-natural-npc-preload-20260921-01` restores the qualified town
save at(110,70) in fresh original-client/server processes. It uses only the
read-only NPC observer and does NOT enable `probe_town_guide_resource` or install
the explicit resource-loading thunk used in the earlier indoor experiment.
After normal town initialization, ordinal19 `data2/rom/npc/npc2720.ROM` has
loaded_slot11, action_count16 and palette6. Templates1606/1607 retain flags4000
and appearance20. Both256-entry NPC pools are empty. The run returns
NATIVE_TOWN_SAVED_POSITION_RESTORED with no error.

The retained runtime regression checks the loaded slot is nonnegative, exact
resource identity and template properties, empty pools and absence of the
explicit loader-probe result fields. Twelve town runtime/route tests pass.
This establishes natural resource availability in the actual scene2/4 without
patching a resource slot or requesting an extra native loader call. It does not
prove either NPC has spawned, is visible, uses the text coordinates, accepts a
conversation or grants a quest. The next step is current S2C72 spawn qualification
with these templates and separately labeled placement/policy evidence.

## Compiled Town Spawn Parser Qualification

`DiagnosticTownNpc` now emits the bounded21-byte candidate for1606/1607.
`CUSTOM-0020` records the explicit test-only positions, state1, direction0,
selector-high3 and zero opaque fields; no Application activation or database
promotion occurs. Templates and appearance20 remain independently native.

Built `diagnostic-town-npc` in Release and ran
`python -B -m unittest discover -s tests/research -p test_current_town_npc_spawn.py -v`:
all3 tests passed. The test pins current image and raw/decoded gamedata hashes,
executes the native CSV tokenizer/template loader, and feeds the compiled C++
record through6A68B..6A9EF. Both native template pointer outputs select the
expected94-byte record;61580..615AB converts appearance20 to ordinal19.
The existing decimal sscanf platform adapter is retained; no asset lookup or
entity-allocation result is manufactured.

Separately, CC621..CC690 reads both identities and all five coordinate pairs
(0,0), (188,188), (110,110), (116,62), (110,70) exactly. A deliberate asset-slot
sentinel limits this to scalar decoding, not successful resource binding.
Seven malformed/out-of-range CLI cases reject without emitting a packet.
The new suite borrows current-image helper methods only; it does not run the
old suite setup, load a legacy placement atlas or read retired archives.

Remaining: own-server S2C72 live allocation, scene projection/render integration,
normal NPC request/reply, quest state and persistence. Text coordinate samples
remain test inputs, not recovered authoritative spawn locations. The isolated
helper is not a production gameplay or balance approval.

## Live Town Guide Allocation

Subsequent run `native-town-guides-spawn-20260921-01` enables the new default-off
`diagnostic_town.spawn_guides` in a dedicated loopback database cloned from the
qualified town save. Original client and server start afresh, restore the
character, and receive both21-byte72 records in one encoded world frame on an
accepted standalone tick. Application verifies the owned saved town position
and sends only once per session. Disconnect removes its transient send marker.

Result `NATIVE_TOWN_GUIDES_ALLOCATED`, error null: read-only pool observations
contain1606 at(110,69) and1607 at(112,70), followed by a world-frame return.
Resource ordinal19 is naturally loaded; no extra loader probe is installed.
These positions are arbitrary nearby diagnostic inputs under CUSTOM-0020, not
the mission text's coordinates and not native authoritative placements.

The retained regression requires exact identities/coordinates, one server send,
no policy rejection, no explicit resource probe, unchanged source database hash
and equal contents of every table before/after the isolated session. Config
tests cover default-off, explicit enable and rejecting non-boolean enable.
This closes allocation/coordinate acceptance only. Visible sprites, normal NPC
interaction and persistent quest gameplay remain open; world_accepted remains
false. No production balance promotion is implied.

## Both Town Guides Complete Native Conversation Transport

Fresh isolated runs `native-town-guide-dialogue-1606-20260921-01` and
`native-town-guide-dialogue-1607-20260921-01` both return
`NATIVE_TOWN_NPC_CONVERSATION_CONFIRMED`, error null. Each executes the native
96750 request function for its observed actor, sends37 naturally on the game
socket, receives the server's7A response through the original dialogue parser,
executes native C8500 confirmation and sends85 on that same socket. Server
confirmation acceptance precedes a subsequent world frame. No direct packet
injection replaces native client serialization. The probe does bypass physical
selection/clicking, so this is not a visual or player-operated UI acceptance.

CUSTOM-0020 now binds the completed-world session/account/character before
spawning. `open_town_npc` checks the spawned flag, exact1606/1607 target, saved
area2/scene4 and per-axis3 distance from the same placements used by the codec.
The distance authorization is custom server policy. Dialogue key3/count14600,
request1234/reply2/context9a are retained diagnostic values, not an established
native text/NPC/quest mapping. Town confirmation consumes the conversation
without borrowing the indoor journal mutation. Cancel/reopen retains existing
generation checks; successful confirmation remains terminal in this diagnostic.

Release `recovered-quest-sync` passes both targets'162 distance cases plus
ownership, invalid target/high-word, scene, replay, cancellation and removal
checks. All14 town runtime tests pass, including archived wire/plain hashes,
opcode identification, exact target37 and85 fields, native queue/stack checks,
strict event order and one server acceptance per message. Every database table
matches the qualified baseline in both runs and the baseline hash is unchanged.

Next required gameplay work is native text/quest binding, versioned persistent
progress and rewards with complete original-client acceptance. Neither these
round trips nor the arbitrary dialogue count as completing the introductory
quest or demonstrating visible NPC interaction.

## Native Guide Text and Multi-Page Consumer

Current `Data2/Patch/Comm/NPCMission01.csvZ`, SHA256
`1ff497204b5cf77cbbccffdf1836d7aeee30e46980ac1e85d8d0a08a0a4bcda7`,
contains the directly relevant source text below. Keys are actual declared
NPCMissionMessage IDs, not inferred offsets in the file. Lines896..903:

| Key | Source text content | CP950 byte length |
| --- | --- | --- |
| 894 | Town/island introduction; asks player to find Song near weapon shop | 900 |
| 895 | Reminder to find Song | 120 |
| 896 | Return/completion speech; promises a map | 678 |
| 897 | Reminder concerning the given map | 116 |
| 898 | Song asks player to speak to Tu first | 72 |
| 899 | Song's introduction to town surroundings | 740 |
| 900 | Song asks player to return to Tu | 34 |
| 901 | Closing greeting | 44 |

Read-only observation now bounds each selected live C string to4096 bytes and
requires NUL termination. All eight complete strings match the pinned decoded
source byte-for-byte in two fresh processes. This verifies live key/content
identity. Textual map promises do not establish item ID, count, reputation
changes, reward transaction or server stage predicates.

Town test responses now select894 for1606 and899 for1607. That association is
an explicit CUSTOM-0020 representative sample, not an official stage selector.
The previous arbitrary key3 remains historical test evidence and remains used
by the independent indoor diagnostic. No quest-state mutation was added.

First run `native-town-guide-source-text-1606-20260921-01` is retained as a
failed probe: C8500 returns without emitting a packet on page0 of7. Original
C8510..C852B checks the last-page/selection conditions; it is not next-page.
The pinned C85B0 event dispatcher uses button3/event1 to call C8750, followed
by C8700 selection reset and C8920 redraw. The owned probe now reads page state
to choose that native handler before the last page, or C8500 on the last page.
It never writes the page index/count. Caller registers/flags and stack are
preserved; each nonfinal return must advance exactly through the recorded page
sequence, have no queued packet, and remain within a64-page diagnostic bound.

Successful fresh runs:
- `native-town-guide-source-text-1606-20260921-02`: text894,7 pages,6 next-page returns.
- `native-town-guide-source-text-1607-20260921-01`: text899,5 pages,4 next-page returns.

Both finish `NATIVE_TOWN_NPC_CONVERSATION_CONFIRMED`, error null. Final85 is
emitted only after native page advancement, accepted once by the server, and
followed by a world frame. Fifteen town regressions pass, including current
image/hash and next-button branch evidence, exact probe bytes, source/live text,
page sequencing, stack, wire/plain hashes and equality of every saved DB table.
Still no physical click, screenshot/visible UI, official stage policy, journal
progress, map grant or reputation claim. Next: staged gameplay and persistent
quest acceptance without relabeling these text references as server authority.

## Staged Lua Proposal, Not Yet Activated

CUSTOM-0021 adds `LuaEngine::town_guide` and `gameplay/town_guide.lua` as a pure
rule boundary. Native text IDs894..901 and mission1 descriptions1/2 are reused;
stage selection and confirmation policy are explicitly custom. The API returns
only a proposed text key, confirmed stage, journal description and reward
requirement. It has no live actor handle, database connection or grant callback.

The staged route is0/unstarted ->1/find Song ->2/return to Tu ->3/completed,
with confirmations at1606,1607,1606 respectively. Wrong-order/repeated contacts
return source reminder text without advancing. Reaching3 requires a reward
transaction; `requires_reward` is not a receipt or evidence of a grant. A caller
must bind the proposal to a saved revision and conversation, authorize the
confirmed actor, and atomically commit the durable stage, journal and reward.
Cancellation discards a proposal. It must never write a completed stage solely
because the source dialogue promises an item.

Release `town_guide_lua` passes all8 combinations,729 six-contact traces
(either NPC confirmation or cancellation/no commit), unsupported inputs and
reload. The test checks at most one reward proposal per simulated trace; no
real reward, transaction, storage or client run is performed by that test.
C++ rejects out-of-range inputs/results, decreasing/skipped stages, inconsistent
journal descriptions and a completed transition without reward requirement.

Application does not call this API yet. CUSTOM-0020's isolated native dialogue
experiment is unchanged. Persisted/versioned quest state, optimistic revision
checks, exact-once reward settlement, native journal updates, reconnect and
client acceptance remain required before production activation.

## Incomplete Progress Persistence

Migration16 adds an empty `diagnostic_town_guide_progress` table without
rewriting prior schemas or populating progress. Each row stores owned character,
stage1/2, matching journal description1/2, positive revision, pinned current
NPCMission01 SHA256 and CUSTOM-0021. Missing row means unstarted; it is not an
implicit acceptance. The existing CUSTOM-0018 journal stays independent.

Repository load checks ownership, field bounds and exact provenance. Commit
accepts only absent->stage1 or stage1->stage2. It checks the expected snapshot
inside the SQLite transaction, uses revision-qualified update, verifies the
written row and commits stage/description/revision together. Stage3 is rejected
by both API and schema until reward settlement exists; a future schema/API
extension must provide that transaction, not silently treat2 as completed.

Tests now combine actual Lua proposals with bound conversation confirmation
callbacks: cancelled acceptance leaves no row; new request generation commits1;
an injected AFTER UPDATE failure leaves both progress and confirmation retryable;
retry commits2 and subsequent confirmation replay is denied. A second DB
connection's stale snapshot cannot overwrite the newer stage. Reopening the
database retains2/description2/revision2. Wrong owner, duplicate/skipped stages,
completed stage, inconsistent description, wrong source and revision overflow
are rejected. Existing accounts and display journal remain unchanged.

`database`, `recovered_character_repository`, `recovered_position_repository`
and `town_guide_lua` pass in Release. Tests use private temporary databases, not
the formal database or archived runtime evidence. Application has not activated
quest-stage writes yet. Next integration still needs a pending conversation
bound to its saved revision, native journal projection/restoration and original
client confirmation/reconnect; final completion needs atomic qualified rewards.

## Live First Acceptance and Journal Projection

Default-off `diagnostic_town.quest_progress` requires the isolated town guide
spawn configuration. On native37, Application reads owned saved progress and
uses Lua to construct a pending plan with its snapshot and target NPC. The
existing conversation binding supplies session/account/character and request
generation. Reward-required plans are rejected before opening. On native85,
position/range and saved revision are rechecked; commit precedes native DB
projection. Cancellation/disconnect remove pending data. The client request's
opaque byte never supplies a stage, reward or version.

Run `native-town-quest-accept-20260921-01` clones the qualified town baseline,
applies migration16 and imports pinned current quest descriptions into that
owned run DB. Fresh original-client/server processes complete1606 request,
text894 seven-page dialogue and85 confirmation. Result NATIVE_TOWN_QUEST_ACCEPTED,
error null. Saved row is character1/stage1/description1/revision1/CUSTOM-0021
with the pinned text source. Native C9670 receives slot0/value0x10001 and its
return writes that value while preserving the other14 slots; a subsequent
world-frame return is observed.

Sixteen town regressions pass. The live acceptance test checks same-socket
request/confirmation, six native next-page returns, exact native journal
arguments/stack/state/event order, one server acceptance and the durable row.
All baseline tables are unchanged except explicitly allowed schema migration
and native description/source imports; the only new gameplay table contains
the single expected progress row. Baseline file SHA256 is unchanged. Config,
repository and Lua CTest suites also pass.

This is isolated custom acceptance policy using native dialogue/journal
transport. It is not official quest-stage recovery, physical UI verification,
full task completion or production balance approval. Remaining: restore the
owned journal after reconnect, allow subsequent bound conversations safely,
qualify stage2 and implement atomic qualified rewards before final completion.

## Reconnect and Same-Connection Second Stage

Town progress mode now reconstructs the dedicated diagnostic journal from the
owned saved stage on the first accepted world tick. It emits the already
qualified15-record native batch, with slot0 referencing the saved description.
This diagnostic owns the entire test journal; shared production slot allocation
is not implemented. Saved stage and revision are not rewritten by restoration.

`native-town-quest-reconnect-visit-20260921-01` clones the prior accepted save.
Fresh original client/server processes restore all15 slots, slot0=0x10001,
before requesting1607. Native text899's5 pages complete,85 is accepted, and
stage2/description2/revision2 is saved. C9670 then consumes slot0=0x20001 and a
world frame follows. Result NATIVE_TOWN_QUEST_VISIT_COMMITTED, error null.
The retained regression proves restore-before-request ordering, second update,
the exact saved row, baseline hash unchanged and every other DB table unchanged.

An explicit `allow_followup` operation now permits another town progress
conversation only after an owned confirmation has successfully committed.
This does not make ordinary diagnostic conversations reusable automatically.
Old confirmations stay consumed; opening the next conversation assigns the
next request word without wrap. Tests cover missing/open/unconfirmed state,
wrong ownership, duplicate rearm, prior-word rejection and cancellation.

`native-town-quest-chain-20260921-01` starts from the original unstarted town
baseline and completes both contacts without disconnecting. Native requests
target1606 then1607;85 request words are1234 then1235, all four C2S messages use
the same socket. Texts894/899 have7/5 pages. Both journal consumers return,
there are exactly two progress commits and one NPC spawn send, and the durable
row is stage2/description2/revision2. Position remains110,70/revision53; the
independent CUSTOM-0018 journal remains empty. Result
NATIVE_TOWN_QUEST_TWO_STAGES_COMMITTED, error null.

Eighteen retained town regression tests and the Release conversation executable
pass. These runs close first acceptance, second contact and reconnect continuity
for the isolated custom flow. They do not close final return/reward settlement,
physical NPC selection, visible UI acceptance or overall world acceptance.

## Current Map Item Identity

Pinned gamedata.csvZ SPI section (737 definitions), source line8236, contains
item5569 / Spi01069 / icon55069. Exact current CP950 name is the Jin Ao Island
regional map; the descriptions identify a map item and regional terrain map.
This is a concrete candidate matching dialogue896's map promise, not evidence
of an authoritative quest reward mapping or quantity.

The existing offline NativeItemMetadata helper's36 first-match tags do not
contain SPI. An exploratory parse therefore failed at tag lookup before
executing a row parser. No fallback selector was invented and the helper's
qualified section list was not broadened. Original59301..59326 confirms the
bounded tag scan; resolving SPI dispatch/fallback is still separate work.

Fresh run `native-town-map-item-catalog-20260921-01` adds read-only observation
of the actual native item index at resource+B2D40+4*5569 and its non-null396-byte
record. Source name, all six description strings, raw price fields100/10,
effect-image field8428, icon55069 and flag bits match the loaded record exactly.
Strings begin at8, then46+38*i; the initial regression's36-byte assumption was
corrected against actual record offsets. Raw price fields are not proof of
server shop/economy behavior. Observed resource group106/action68 may be rebound
runtime slots; they are not asserted as source identifiers. The isolated
offline RomMaps helper returns41 for55069, so no equality is assumed between
these different stages of resource resolution.

The run completes the existing native town dialogue with no error. Nineteen
town regressions pass, including pinned file/unique section row and exact live
field comparison. No item was granted, no inventory packet was emitted for5569,
and map-use behavior is not qualified by this read-only observation. Next reward
work must establish owned slot availability, atomic completion/grant, duplicate
receipt protection and native inventory/resource acceptance. Count/reputation
remain official-rule gaps or require separately documented custom policy.

## Atomic reward repository qualification

CUSTOM-0022 introduces an isolated one-map/no-XP/no-currency/no-reputation
completion policy. This is not an official reward claim or balance approval.
Migration17 preserves existing progress and adds a unique reward receipt.
The repository requires stage2, an owned revision-matched explicitly empty
inventory row, pinned item source and no unresolved battle. It commits stage3,
one item5569 and the receipt in one transaction. Missing inventory is not empty.
Completed progress cannot load without matching receipt provenance; ordinary
incomplete-progress commits still cannot complete the quest.

Release server and tests build successfully. Five targeted CTest suites pass
(database, recovered_character_repository, recovered_position_repository,
town_guide_lua, config). Added cases cover missing/occupied/out-of-range slots,
wrong owner/source, stale revisions, overflow, injected receipt-insert failure
rolling back both progress and item, retry, stale peer and replay rejection,
disk reopen, corrupt/missing receipt, and migration16 saved-progress preservation.
Migration is also checked for no automatic inventory/reward creation and intact
foreign keys. Nineteen retained town runtime regressions pass; those replay
archived evidence, not a fresh reward run.

Application reward activation, authoritative empty-slot initialization, native
5569 inventory projection and reconnect acceptance remain pending. No existing
player database was intentionally migrated during these temporary-database tests.

## Native reward projection and completed reconnect

The isolated town route now binds the persisted empty slot0 snapshot when
opening reward dialogue896. Confirmation checks the same owned conversation,
saved position and progress, calls the atomic transaction, then sends native
journal DB slot0 clear plus inventory41 item5569/count1. Completed reconnect
restores15 cleared journal slots and current inventory occupancy, not another
grant. The runtime route deliberately supports slot0 only; no production
inventory allocator or missing-row-as-empty assumption was introduced.

For the explicit CUSTOM-0022 test, SQLite backup copied
`native-town-quest-reconnect-visit-20260921-01/town-diagnostic-accounts.db` into
`native-town-reward-empty-fixture-20260921-01/town-diagnostic-accounts.db`.
Only that new fixture received an empty CUSTOM-0015 slot0/revision1 with the
pinned gamedata source. Original source SHA256 remained
`f38013c16bc1e7722c012c3b0063eba9a6585a25f1d300e319974c80d371d7f4`.
This is an explicitly constructed test precondition, not recovered starting loot.

Fresh run `native-town-quest-reward-20260921-01` completes with error null and
`NATIVE_TOWN_QUEST_REWARD_OCCUPANCY_OBSERVED`. Original-client inventory24-byte
slot record becomes `01000000c115000000000000000000000000000000000000` after
journal clear and a subsequent world frame. Durable stage3/description0/revision3,
slot0/item5569/count1/revision2 and one matching CUSTOM-0022 receipt are present.

Fresh run `native-town-quest-reward-reconnect-20260921-01` clones that completed
database and reaches `NATIVE_TOWN_COMPLETED_QUEST_RESTORED` with error null.
The original client consumes all15 empty journal slots, restores item5569 and
confirms the completed NPC dialogue. All tables equal the completed baseline:
no new receipt, item, revision or account mutation. Twenty retained town tests
and five targeted CTest suites pass. This is live native-call/occupancy evidence,
not physical UI, visible icon, map activation, general quest balance or full-world
acceptance; world_accepted remains false.

## Full three-stage quest on one connection

The runner's explicit --town-quest-reward-chain extends --town-quest-chain to
three stages without changing the older two-stage default. It archives both
prior conversations, advances target1606 ->1607 ->1606, checks cleared final
journal and original-client item5569 occupancy before declaring the result.

Fixture `native-town-full-chain-fixture-20260921-01` is a SQLite backup of the
unstarted cross-window town baseline. Only the copy receives explicit empty
slot0/revision1/CUSTOM-0015. Original baseline SHA256 remains
`e5d6c6c50335f6ea36fb88250e9ca9761cbd97e320f94f7c24e51a79e2aa481b`.
No existing progress is seeded; migrations16/17 and the current quest catalog
are applied by the runner as in the preceding town experiments.

Fresh `native-town-full-quest-chain-20260921-01` reaches
NATIVE_TOWN_QUEST_THREE_STAGES_AND_REWARD_COMMITTED with error null. All three
native37/7A/85 exchanges use the same socket; request words1234/1235/1236 and
7/5/7 pages remain distinct. Journal projections are10001,20001,0 in order.
Three successful commits end at stage3/description0/revision3 with one
item5569/count1/slot revision2 and one matching receipt. Server log has exactly
one reward marker. Every unrelated baseline table is unchanged; allowed changes
are migration history, pinned quest catalog/source import and the inventory,
plus the newly created progress/receipt tables. Twenty-three retained town
regressions pass, including ordering, socket identity and persistence checks.

This proves the connected diagnostic quest state machine end-to-end through
native calls and original packet consumers, not physical player input, original
NPC coordinates, production inventory initialization or official reward policy.
CUSTOM-0020/0021/0022 remain explicit; no full-world acceptance promotion.

## Full Quest Followed By Reward Map Use

`native-town-chain-map-20260921-02` combines the existing full reward chain and
CUSTOM-0023 map-use probe on the same original-client connection. The runner
records `town_reward_chain_completed` after the third journal/reward receipt,
then continues into original96390(slot0) and natural transport instead of
stopping at the quest milestone. The two-stage chain still cannot request this
combination; scene-transfer combinations are explicitly rejected.

Original client PID19444 completes all three NPC conversations, then queues
25C1150000 at sequence491 after the reward milestone485. The own-server reply
3F0100 reaches the original panel consumer, changing flags11->21, and a native
world frame follows at510. Request/reply hashes and checksum are verified;
both use the same socket as all three quest confirmations. Inventory remains
item5569/count1/revision2, progress is stage3/revision3 and one reward receipt
exists. All gameplay database tables match the earlier full-chain baseline.
Migration version/name/SQL also match; independent application timestamps are
not gameplay state and are compared separately by exclusion of that field.

The first invocation stopped at argument validation because --movement-lab was
omitted; no client run was claimed. The first database comparison detected only
the independent migration timestamps; the corrected scoped comparison and all
27 town runtime tests pass. Earlier evidence is unchanged.

This extends the native-call E2E path from accepting the test quest through
using its reward. It does not prove physical clicks, visible bitmap correctness,
official reward/25-to3F association, all quests or production balance. Existing
CUSTOM-0020/0021/0022/0023 remain default-off; world_accepted remains false.

Additional verification: the broader current_protocol_coverage suite refuses
startup because its pinned formal-route snapshot for src/net/Session.cpp no
longer matches. This turn did not edit that file and did not update its hash
to bypass the audit. The27 town runtime tests still pass; broad protocol
coverage requires a separate source review before its snapshot can be renewed.

## Full-Chain Reward Cold Restore And Reuse

`native-town-chain-map-restore-20260921-01` starts a new owned server/client
from a read-only SQLite backup of native-town-chain-map-20260921-02, without
seeding progress or inventory. New client18500 receives15 empty journal slots,
retains the completed quest's map5569/count1, confirms the completed dialogue
and uses the map. Original25C1150000 and response3F0100 have retained wire/plain
hashes and valid checksum on the conversation's socket. The native panel goes
11->21 without changing slot bytes and a subsequent world frame is observed.

All database tables, including migration history, equal the completed source;
no new reward marker appears. The source database SHA256 remains
514a3e4cd044c8b191ff40d7b6f26d934b6e0a70a60aaeecd6b7e70c70a6eb13.
The28-test retained town suite passes with the new process identity, native
journal/slot observations, packet validation and exact all-table comparison.
No original account/save was altered and no synthetic starting reward added.

This closes cold restore/reuse for the same connected diagnostic quest chain,
not arbitrary quests, physical UI input or production promotion. CUSTOM reward
and map-response policies remain labeled and default-off.
