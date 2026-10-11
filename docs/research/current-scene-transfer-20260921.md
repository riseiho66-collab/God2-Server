# Current Scene Transfer Prefix

Purpose: qualify the native relocation transport needed before attempting a
post-defeat return. This does NOT identify an official death destination,
restored HP, experience penalty or automatic resurrection rule.

Source: current pinned image SHA256
149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763.
No retired archive or external server is used.

Original length helper15840 reports9 logical bytes for S2C61. Dispatch at
68B4E uses the direct opcode-indexed table6B5D4: entry61 points69345.
6934D invokes814F0 (UI prelude, not executed in this qualification).
69352 increments the logical-record pointer, pushes1 and the body pointer,
then69358 invokes6BCC0. The original SEH prologue executes unchanged.

The bounded receiver prefix through6BD5D proves:

- Body+0 WORD: low6 bits copied to world+15396854; upper10 bits copied
  to world+15396850, matching the existing area/scene storage convention.
- Body+2 WORD is untouched by this prefix, not certified unused globally.
- Body+4 DWORD low2 bits copied to world+1539684C.
- If both saved selectors equal the incoming selectors AND bit16 of body+4
  is set, native code clears that bit IN THE MUTABLE PACKET and writes0
  to stack local+18. Otherwise the packet stays unchanged and local+18 is1.
- The prefix stops at original metadata lookup5AA70. No return value is faked.
  Disassembly at6BDD9 subsequently branches to6C33A when local+18 is0;
  the metadata/resource work between those points is not qualified here.

An independent original-code island6C33A..6C3C9 proves coordinate extraction:
world+224 = (body DWORD+4 >>2)&7FFF; world+228 = body DWORD+4 >>17.
Kind2 also prepares temporary X and Y+1 values. Other kinds are tested with an
explicit null auxiliary object, stopping before unqualified downstream code.
These are separate precondition executions, NOT one continuous scene change.

Important overlap: bit16 is also X bit14 in that coordinate encoding. The
same-scene branch clears it before coordinates are extracted. Do not add a
generic encoder that blindly ORs the flag without bounding/qualifying X, or
assume the incoming DWORD is immutable. This needs preservation in future
same-scene return tests.

Verification: test_current_scene_transfer.py passes3 tests, including96
selector/flag cases and40 coordinate-island cases. Raw area0/63 and scene1023
are arithmetic boundary inputs, not assertions that these maps exist.

Next: run the complete receiver with actual loaded scene resources in the
isolated own-server client, preserving current position and HP evidence.
Until then, no Application emission, server teleport handler, death recovery,
production balance or world acceptance is enabled by this evidence.

## Own-server complete receiver, subsequent qualification

CUSTOM-0024 now enables one same-position candidate only in the isolated town
map-probe configuration, completed guide save, character1 at110,70 in area2/
scene4. Native25 is only a diagnostic trigger, not an official map-item-to61
association. The response is61/02010000B8018D00: zero opaque WORD, kind0,
same selectors, same coordinates and bit16 set. No gameplay database write.

Run native-town-scene-transfer-20260921-01 proved receiver return but the server
then rejected the native1C followup and closed the socket. Its optimistic result
string must NOT be treated as successful round-trip acceptance. Run02 correctly
reports TOOL_ERROR for that rejection. Inspection found bootstrap retains
CharacterSelected after the initialization tail, whereas the first notice gate
required InWorld. Session already enforces tail completion before this route.

The corrected gate permits CharacterSelected or InWorld only with the explicit
scene probe and a pending sent candidate, character1, and exactly one context
payload01000000. It consumes the pending authorization once and removes it on
disconnect. No generic context routing or production relaxation was added.

Run native-town-scene-transfer-20260921-03 completed with error=null:

- Packet0413 S2C frame0C006102010000B8018D004A on socket2040.
- Receiver46BCC0 sequence415 ->46935D sequence418, EAX1, ESP+12.
- Actual body mutates02010000B8018D00 ->02010000B8018C00, confirming bit16 clear.
- Area2/scene4/kind0, position110,70 and inventory slot0 unchanged.
- Packet0421 C2S frame08001C01000000C9 on the same socket is accepted once.
- Sequence423 returns to original world frame467BD7 after the notice;
  no policy-rejection close in the server log.
- All21 SQLite tables equal the source completed-reward save, with equal schema.

The runtime regression verifies packet hashes/direction/checksum, same socket,
instruction order/ABI, server acceptance, and all-table equality. Five test
methods now include both original-code and saved-runtime evidence. Saved-run
checks do not launch a new client themselves. This qualifies the same-scene,
same-position path, NOT cross-scene loading, visible UI, death restoration,
production balance, arbitrary positions or full world acceptance. The broad
world_accepted flag remains false. The next step is a separately owned relocation
and saved-position contract, then a labeled death recovery rule.

## Durable relocation and next movement

CUSTOM-0024 adds an additional default-off scene_relocate option, dependent on
scene_probe. Application still requires the exact qualified character1 baseline
area2/scene4/110,70, then targets111,70. This is not a public destination command.

RecoveredMovementService now owns the two-phase change, rather than letting
Application overwrite a DB position behind its cached movement authority:

1. Verify ready session/account/character, no pending transfer, exact saved
   baseline, source-consensus town navigation and representable target.
2. Allocate/encode the frame, then CAS-commit the destination. Publish cached
   coordinates only after that commit. Mark the transfer pending.
3. Reject ordinary movement, repeated begin and battle-resume reset while
   pending. The exact previously qualified context notice invokes finish.
4. Revalidate the saved destination, reset connection slot0 and allow movement.
   A lost connection before finish restores the already committed destination
   through normal world entry, not an implicit return to old coordinates.

Unit coverage includes owner/bounds/navigation rejection, duplicate/foreign
receipt rejection, pending movement rejection, next step and reconnect before
receipt. Native original-code island6C414..6C443 calls103640 then1036B0 and
resets all40 tested prior ring indices to010001 with destination in slot0.

Run native-town-relocation-20260921-01 completes full native receiver and
accepted context; client position110,70 ->111,70, ring010001, SQLite revision54.
Run native-town-relocation-relogin-20260921-01 restores that save and completes
the existing NPC dialogue; its observer lacked a final explicit position read,
so it is not used alone as proof of rendered/restored destination.

Run native-town-relocation-move-20260921-01 stopped on a Python local struct
binding error in the observer, not a qualified gameplay outcome. After fixing
that observer, native-town-relocation-move-20260921-02 completes:

- Receiver transfers to111,70 and the server accepts one pending context.
- Original path function5024C0 then walks to112,70; no direct coordinate write.
- Native ACK5D01 advances ring010102; original world frame observes112,70 and
  motion state0. SQLite becomes area2/scene4/112,70/revision55.
- All other source database tables remain unchanged. Source save stays at
 110,70/revision53. Tests compare data read-only.

These native function probes are not physical-input or visible-UI acceptance.
Cross-scene loading, arbitrary destinations, multiplayer visibility, defeat
restoration and HP/penalty rules remain open. No production mode was enabled.

Fresh native-town-relocation-move-relogin-20260921-01 explicitly reads the final
world snapshot after restored NPC dialogue: area2/scene4/kind0/112,70 and fresh
ring010001. The client PID differs from the movement run; no transfer or movement
probe is executed on reconnect. All database tables and schema equal the
post-walk source save. This closes the bounded relocation -> next movement ->
durable reconnect path, without claiming broader world acceptance.

## Cross-scene transport and loaded collision data

At the time of the transport runs, the movement service used one map per instance. Do not
mutate its shared scene_ or navigation when one player changes map. A per-player
destination binding/registry and durable ownership handoff remain integration
work. To qualify transport first, scene_indoor_probe sends area2/scene15/kind2
at17,13 WITHOUT changing any save and forbids later non-tick gameplay (apart
from its one pending exact context receipt). It conflicts with scene_relocate.
This probe is not an enabled cross-map gameplay route.

Attempts are retained:

- native-town-indoor-transfer-20260921-01: receiver returns and notice accepted,
  but observation expires while incorrectly waiting for departed town NPCs.
- Run02: observer rejects UI scene ID, initially read with an incorrect DWORD
  width. Run03 corrects the WORD width and retains the actual mismatch evidence:
  UI+8AA4C still points to CityI1/258, while role scene is15/kind2.
- Existing original indoor loading evidence explains the distinction:
  test_current_world_scene.py proves59D80(2,15) returns null; indoor assets use
  CAN/HMD and the manager at [world+A7E05DC]+BC instead of the outdoor UI catalog.
  The live indoor object is manager+1030; grid pointer/width/height are at+8C.
  The observer now qualifies that actual grid rather than weakening the ID check.

native-town-indoor-transfer-20260921-04 passes the bounded transport criterion:

- S2C packet0411:0C0061C203000046001A0026, native6BCC0 entry413 and return414,
  EAX1, ESP+12; body unchanged (no same-scene bit was set).
- C2S packet0417:08001C01000000C9, same socket, accepted once.
- World frame419 reads area2/scene15/kind2/17,13, ring010001, inventory unchanged.
- Live manager indoor grid is31x31. Every one of961 cell bytes equals the
  existing current-native indoor-2-15 reconstruction. Retained CityI1 metadata
  is recorded separately and is NOT used as the active indoor-map identity.
- All21 DB tables and schema equal the town source save. No position, HP,
  quest, inventory or reward is committed by this transport-only experiment.

This is loaded collision/resource and receiver evidence, not a screenshot or
proof of visible scene rendering. Destination movement, multiplayer visibility,
durable cross-map reconnect and a death-recovery rule remain unimplemented.

## Per-character destination authority (service tests only)

RecoveredMovementService now optionally loads both pinned town and indoor
navigation without mutating either map when a character transfers. Each active
binding carries scene/kind, coordinates, movement ring and saved revision.
begin_indoor_transfer admits only an owned ready source-consensus town binding,
valid destination and exact source snapshot. It builds the qualified scene61
frame before committing the destination with repository CAS. Movement remains
blocked until finish_town_transfer validates the committed snapshot; reconnect
restores the destination even when the context receipt never arrived.

The recovered_movement_service test covers two independent characters, exact
native-qualified indoor logical bytes, invalid destination/ownership, duplicate
login, blocked movement while pending, separate movement rings, destination
movement persistence, fresh service restoration and rejection by town-only
navigation. External position changes before transfer and before its receipt
must reject stale operations without overwriting the newer save; reconnect
uses the newer authoritative destination. Reverse indoor-to-town transfer is
still rejected pending native qualification.

This is CUSTOM-0024 groundwork, not live cross-map acceptance. The original
Application transport-only indoor probe still leaves its database unchanged
and blocks subsequent gameplay. A separate default-off scene_indoor_transfer
option now requires scene_indoor_probe, source_consensus and an explicit
nonempty indoor_navigation path. It registers both maps and invokes the durable
transfer API for the existing isolated character1/110,70 -> indoor17,13 trigger.
Only its pending exact context receipt releases destination movement. Reconnect
in scene15 restores journal/inventory without spawning town NPCs; town-only
mode continues rejecting that save. No existing runtime config is changed.

Release server/tests build and config, recovered_movement_service,
recovered_position_repository and current_scene_transfer suites pass after
integration. Those tests do not execute the new Application crossing path.
Fresh client destination movement and cross-map reconnect remain required
before that path can be claimed complete. The runner does not yet expose the
new durable option at that point; the following attempt supersedes that tooling gap.

## First durable runtime attempt: startup language regression

The runner now exposes --town-scene-indoor-transfer, requiring the indoor probe
and town source-consensus mode. It writes explicit pinned indoor navigation and
checks the committed destination row independently after native receiver return.
The existing transport-only result remains distinct from durable acceptance.

Run native-town-indoor-durable-20260921-01 terminates REGRESSION / EXIT_PROCESS
before Winsock, login or any scene packet. Server startup succeeds. All21 DB
tables remain identical to the source; position is still2/4/110,70/revision53.
It is not evidence that the new transfer works or that the transfer failed.

Current Get-WinSystemLocale reports2052/zh-CN. Input loader events now request
gamedata-gb.csv and message-gb.csv, whereas successful indoor-transfer run04
requested gamedata.csv and message.csv. In the pinned image, original45578C
calls531C10 to select alternating language table pointers. 531C10 returns1
only for language WORDs at59DFD8=4 and59DFDA=2. Initializer531BC0 calls IAT
570394 then splits the returned language ID into low10 and high6 bits. The
import identity and complete startup failure chain remain to be qualified.
No system locale, source asset or client executable was changed for this run.
Next runtime work must resolve this process-local language/resource mismatch
before repeating the durable transfer; native destination movement/reconnect
remain pending. No physical UI or playability acceptance is claimed.

## Durable receiver accepted with explicit process-local resource language

Run native-town-indoor-durable-20260921-02 passes
NATIVE_TOWN_TO_INDOOR_DURABLE_RECEIVER_RETURNED, error null. The explicit
--taiwan-resource-locale compatibility option checks the exact original531C10
selector bytes at startup breakpoint6, records IAT570394 as
KERNEL32!GetSystemDefaultLangID, and changes only process-local language WORDs
59DFD8/59DFDA from4/2 to4/1. It does not patch executable instructions, fake an
API return, rename data, alter OS locale or change the original EXE on disk.
This intervention is retained in resource_locale_override and must not be
described as an unmodified-environment run. Unknown selector code or language
is rejected before writing. The override lasts only for the test process.

S2C packet0411 is0C0061C203000046001A0026. Original6BCC0 entry413 returns at414
with EAX1/ESP+12; C2S packet0417 is08001C01000000C9 on the same socket. Later
world frame419 reads area2/scene15/kind2/17,13 with ring010001. The live31x31
indoor grid matches all961 pinned navigation bytes. Application logs exactly
one durable commit and one accepted context, with no policy rejection.

Only recovered_positions changes: source1/2/4/110,70/revision53 becomes
1/2/15/17,13/revision54. All other20 tables are unchanged. The source database
is unchanged. A permanent captured-evidence regression verifies packet hashes,
checksums, direction/socket/order, receiver ABI, native grid, language
intervention and database isolation. current_scene_transfer passes.

This closes durable destination commit plus real native receiver/context
acceptance. Post-transfer movement, fresh-client cross-map reconnect and
physical rendered UI acceptance are still separate pending requirements.

## Cross-map followup movement

native-town-indoor-walk-20260921-01 extends the same explicit language-compatible
durable run with --town-scene-follow-move. After the native scene receiver and
accepted context, original5024C0 targets18,12. No direct coordinate write is
used. The original routine returns1, queues one step, receives S2C packet0426
05005D0153, and consumes ACK5D01 at event429. Later world frame430 confirms
area2/scene15/kind2/18,12, motion state0 and ring010102. The saved row is now
1/2/15/18,12/revision55, following the transfer's revision54. All other20 tables
equal the source town baseline. Result is
NATIVE_TOWN_TO_INDOOR_AND_MOVEMENT_COMPLETED with error null.

The captured-evidence regression checks native call bytes, step count, ACK hash
and checksum, ring, event order, saved revision and unrelated table equality.
Fresh-client cross-map reconnect and physical rendered UI acceptance remain
pending; this is not a claim of production readiness or an official map-item
transfer rule.

## Fresh-client cross-map reconnect

Run native-town-indoor-relogin-20260921-03 restores a read-only backup of the
post-walk indoor save into a new isolated database and launches a fresh client.
It reaches NATIVE_CROSS_MAP_RECONNECT_RESTORED with error null. No map-item,
scene-transfer or movement function probe executes on this reconnect. Final
state is2/15/kind2/18,12, ring010001, matching the revision55 saved destination.
All15 journal slots are consumed by the original restore reader, inventory
slot0 contains5569/count1, and no town NPC is present. All21 DB tables and their
schema equal the post-walk source, with no duplicated reward or position write.

Attempt01 expired because the observer waited for a dialogue-update record
instead of the existing journal_restore_returns. Attempt02 rejected an empty
outdoor catalog pointer. A direct indoor reconnect has no prior outdoor object;
current_scene_live now permits its absence only for qualified2/15/kind2 while
still requiring the independent indoor object and bounded collision grid.
Run03 verifies all961 grid bytes, not an invented outdoor catalog identity.
The explicit process-local Taiwan resource-language compatibility is retained.

This qualifies the bounded native-function-probe chain: town transfer -> indoor
movement -> durable save -> new client reconnect, including inventory/journal
restoration. Physical UI/visual acceptance, reverse transfer, arbitrary map
routes and production promotion are not implied.

## Return-route prefix qualification

Original prefix and independent post-resource coordinate islands now cover
the exact scene4 ->15 and15 ->4 transitions, with and without accidental bit16.
For the reverse candidate, logical bytes6102010000B8018C00 select area2/scene4,
kind0 and110,70. Cross-map prefix retains the payload and requests resource
reload. Setting the same-map reuse bit would instead decode X=16494, not110,
because that bit is only cleared when previous area/scene equal the target.
This is an original-code regression, not a full reverse receiver runtime pass.
It specifically rules out copying begin_town_transfer's same-map bit into a
future indoor-to-town response. The existing service still rejects reverse
transfer; no return route was enabled without full resource/receiver evidence.

## Isolated return transport route, awaiting native run

Application now has a separate default-off diagnostic_town.scene_return_probe.
It requires the existing explicit dual-map indoor-transfer configuration so it
can restore the qualified indoor save, but its response is transport-only:
character1 at area2/scene15/18,12 with completed guide progress and owned
item5569/count1 in slot0 may trigger exactly one candidate6102010000B8018C00.
The native25 association remains CUSTOM-0024 diagnostic policy, not official
map-item behavior. It does not call begin_transfer or mutate any saved position.
One pending exact native context receipt is admitted without finishing a
durable transfer; subsequent gameplay is blocked except ticks because the
server's movement binding intentionally remains indoors. No return movement or
production route is enabled. Config regression covers opt-in type/default and
dependency; the runner and fresh reverse receiver run are still pending.

## Reverse native receiver qualification

--town-scene-return-probe now exposes that isolated route. Fresh run
native-indoor-town-return-20260921-01 restores indoor18,12, invokes original
map-item request routine, then receives S2C packet0484
0C006102010000B8018C0049. Original6BCC0 entry486 returns489 with EAX1/ESP+12;
body remains02010000B8018C00. C2S packet0492 is08001C01000000C9 on the same
socket; the server accepts exactly one pending notice. Later world frame494
confirms2/4/kind0/110,70, ring010001, unchanged inventory, actual outdoor
catalog ID258 and CityI1 metadata at5814484. Result is
NATIVE_INDOOR_TO_TOWN_RECEIVER_RETURNED, error null.

All21 database tables and schema equal the indoor source. Explicit process
Taiwan resource compatibility remains recorded. The captured regression checks
direction/hash/checksum/socket/order, receiver ABI, loaded metadata and database
isolation. This qualifies the reverse receiver and loaded outdoor metadata,
not a screenshot, arbitrary town collision state or post-return movement.
Durable reverse position commit, re-spawning town NPCs, return movement and
reconnect remain integration work; the transport probe keeps them disabled.

## Durable reverse service and Application integration (not yet live)

RecoveredMovementService has an explicit begin_outdoor_return source15->4 API.
The shared encoder now receives the trusted source scene separately and sets
bit16 only for same-scene transfer; begin_town_transfer still requires source4.
Destination validation, pre-encoded response, CAS save commit, pending movement
block and exact saved-baseline receipt checks remain shared with the forward
route. Service tests verify the native-qualified return bytes, fresh town
movement sequence1, a second indoor/return cycle, disconnect before receipt,
fresh service restore and an unrelated indoor character's unchanged save.

Application adds default-off scene_return_commit requiring scene_return_probe.
Unlike the unchanged transport-only mode it invokes begin_outdoor_return and
finishes the binding on the pending context. Only after that context does it
clear the per-session guide projection marker so the next tick re-sends town
NPCs and the saved journal/inventory. Config tests require boolean opt-in and
all existing isolation dependencies. No existing runtime config is modified.
Release builds and targeted tests pass. Runner exposure and fresh native
durable return/NPC/movement/reconnect acceptance are still pending; this new
Application path is not certified by the earlier read-only-save native run.

## Durable return with town NPC projection

Fresh native-indoor-town-durable-20260921-01 uses explicit
--town-scene-return-commit and reaches NATIVE_DURABLE_RETURN_WITH_TOWN_NPCS,
error null. The original receiver accepts the same qualified return body;
after one exact pending context the next accepted world tick reprojects town
NPCs and saved journal/inventory. World frame564 observes1606 at110,69 and1607
at112,70, player2/4/kind0/110,70/ring010001. SQLite changes only position from
indoor18,12/revision55 to town110,70/revision56. Other20 tables equal the source,
including quest stage and reward receipts. No repeated reward is granted.

The captured regression checks receiver ABI/body, final map/position/ring,
NPC identities/coordinates, projection after context, unchanged item occupancy,
saved revision and unrelated tables. Explicit process-local language
compatibility remains. Return movement, fresh post-return reconnect, physical
UI and production acceptance remain pending.

## Return movement and fresh-client persistence

native-indoor-town-walk-20260921-01 reaches
NATIVE_DURABLE_RETURN_AND_MOVEMENT_COMPLETED. After the accepted return and
town NPC projection, original5024C0 walks110,70 ->111,70. Native ACK5D01 resets
the expected first-step ring to010102; idle world frame584 observes the town
destination and SQLite revision57. Only recovered_positions differs from the
indoor source; the other20 tables, including quest/reward/inventory, are equal.

native-indoor-town-walk-relogin-20260921-01 starts a new client PID from a
read-only database backup, without a scene or movement probe. It restores
2/4/kind0/111,70/ring010001 and completes the existing completed-quest dialogue.
World snapshot391 retains that destination and inventory. All21 tables and
schema equal the post-return-walk database, so reconnect does not replay
movement, rewards or transfer. The captured regression covers both runs.

The bounded forward+return chain now includes native receiver, movement,
durable position, NPC projection and fresh reconnect in both directions.
These are separate diagnostic runs using the explicitly documented item-use
trigger and process-local Taiwan resource compatibility. They do not establish
natural doorway triggering, repeated same-session round trips, multiplayer
visibility, physical UI, arbitrary-map support or production acceptance.

## Native doorway lead: current HMD model pairs

The next natural-trigger trace uses only the pinned current groceryL.hmdZ,
not retired teleports.json/Classic-derived catalogs. Its base ModelDat has
eight signed values [-1,-1,7,23,-1,-1,8,24]; the second model has eight -1s.
Original parser4CB26..4CE2B passes four pairs to41DF0, which writes model+2C
through+48. Existing navigation parser tests now verify these exact32 bytes
for both models after original execution, in addition to every grid byte.

A new original41DF0 test proves duplicate non-sentinel pairs are rejected
without mutation, while first coordinate -1 takes the disabled-pair write
branch (the second coordinate is preserved, not automatically forced to-1).
All six current_indoor_navigation unittest cases pass. This confirms source
bytes and native storage semantics, not activation or destination semantics.
The two active pairs must still be traced through the model-placement and
movement consumers before naming world door coordinates or emitting a natural
transition. No portal route, guessed coordinate or production row was added.

The original consumer36F30 reads model+2C/+30 indexed pairs, calls49BB0 and
adds the loaded object's+18/+1C anchor. Executing the complete consumer on the
originally parsed and grid-built groceryL object gives anchor20,0 and index1
->16,19, index3 ->16,20. A permanent native regression asserts both outputs;
all seven current_indoor_navigation unittest cases pass. No Python coordinate
formula substitutes for either native function in this check.

49520 wraps this consumer through manager+1030. A bounded raw direct-call scan
finds36F30 called at49537 but no E8 caller to49520 in inspected RVA1000..140000;
this is not evidence that the function is globally unused. Other pair readers
include49570 and448D2A/448D5C and must be qualified independently. The next useful
runtime probe is movement onto the two projected cells with packet/caller
observation; no server-side automatic transfer should be installed merely
because the coordinate projection is now known. Destination and activation
remain unproven.

## Live connection-cell walk: movement only in the observed window

native-indoor-door-walk-20260921-01 terminates successfully with
NATIVE_INDOOR_CONNECTION_CELLS_VISITED, error null. From a read-only backup of
the indoor18,12/revision55 save, original5024C0 is invoked eight times along
17,13 ->16,14 ->15,15 ->14,16 ->14,17 ->15,18 ->16,19 ->16,20.
These calls are explicit native-function probes, not physical UI input.
Both source-projected connection cells are reached on ordinary world frames.

After the restored-world snapshot, the captured packet artifacts contain exactly
eight C2S2E movement requests and eight S2C5D acknowledgments, with sequence
tokens1..8. Every original call returns1; every ACK updates the original ring
to [1,token,token+1]. Frame634 reaches16,20; frame657 remains there in
area2/scene15/kind2, ring010809. The observer requests approximately one second
of settling after arrival. No extra decoded transfer request or scene change
is observed in this bounded window. This does not prove a longer wait, another
interaction path, or additional original state could never trigger a doorway.

SQLite position alone changes to (1,2,15,16,20,63). The other20 tables and
schema match the source, including quest, rewards and inventory. The original
source remains at18,12/revision55. No map-item or scene-transfer probe executes,
and the server reports no policy rejection. A permanent captured regression
checks all16 wire/plain hashes, framing, direction, opcode, coordinates, tokens,
arrival ordering, native-call return, final state and database isolation.
All17 current_scene_transfer tests pass.

Next evidence target is the original connection-pair consumers and their
activation preconditions, rather than adding automatic server-side teleport at
these two coordinates. Destination mapping is still unproven. Physical UI,
natural doorway acceptance and production promotion remain outstanding.

## Original indoor exit classifier isolated

Current-image49250 requires manager+30 ==2, non-null manager+1030 and its
model pointer+30. It checks ONLY model pairs2/3 (+3C/+40 and+44/+48), projecting
through original49BB0 and adding indoor+18/+1C. A coordinate match writes
type2/type3 respectively and returns1; a miss returns0 without writing output.
The original49000 dispatcher selects49250 for manager kind2 (kind0 selects
49040). Current-image assertion text at58771C names the model index bounds
as nEntryType>=Entry_LeftIn && nEntryType<Entry_End; this supports entry-type
semantics but does not identify any destination map.

Executing both original49250 and49000 against the complete original-parser
groceryL object proves16,20 returns1/type3, while16,19,15,20 and18,12 return0
and leave the output sentinel unchanged. Direct49250 also rejects a non-indoor
manager kind or null indoor pointer without changing output. These are now
permanent tests; all8 current_indoor_navigation tests pass. This narrows the
previous two projected coordinates to one accepted indoor exit-classifier
coordinate for this source object, but is not live invocation evidence.

A bounded direct-call scan finds49000 invoked at43424C in a bridge wrapper
that first calls49450 to transform input coordinates and loads manager from
bridge+BC. The next trace is that wrapper and its callers. The earlier live
path probe did not instrument this classifier, so its movement-only result
cannot establish whether normal interaction reaches this path. No new server
teleport or destination inference has been installed.

## Screen-query caller is not a transfer producer

The bridge entry is34210, taking two screen coordinates, converting through
49450 and calling49000 with a stack-local entry-type output. Its sole raw E8
caller in the inspected code range is46707C. That caller requires local
[esp+40] ==-25, reads signed16 coordinates from input object+12000/+12002 and
tests the boolean result. Success calls483530 with0E. Original483530 updates
UI+232F36 and calls41A950 on UI+232EC0; this call path alone does not identify
a network request. The classification result's type2/3 is not propagated by
34210, which returns only the boolean. Therefore this reference is useful for
screen/interaction classification, not proof of a scene-transfer producer.

An added original-code test executes49330 projection,493C0 inverse, and the
complete34210 ->49450 ->49000 ->49250 chain for four cells and three camera
translations. Projected boundary pixels are not interior samples: the initial
test exposed an adjacent-cell result, so the fixture uses(+40,+20) pixel
samples and explicitly validates each through the original inverse. No
replacement coordinate formula or UI actuation is used. Exit16,20 alone
returns1; the neighboring/entry cells return0. Null bridge manager returns0.
All9 current_indoor_navigation tests pass after correcting the sample points.

The next producer investigation should follow movement/state completion or
interaction command dispatch, not treat the0E UI-state setter as an opcode.
The inspected502570 movement completion calls502210 after updating position
and setting motion state0; neither the observed screen-query chain nor this
bounded disassembly establishes the missing destination/transfer contract.

## Complete current-grid classifier coverage and movement-tail trace

The original49250 classifier has now executed for all961 coordinates of the
originally parsed31x31 groceryL navigation grid. Exactly one cell is accepted:
(16,20,type3), whose original collision byte is1. All960 rejected coordinates
leave the output sentinel unchanged. This is exhaustive for this object's
grid and this classifier, not for other assets, states or map transitions.
All10 current_indoor_navigation tests pass (19.037 seconds).

The bounded502570 movement-tail trace calls5029A0 for per-frame displacement,
updates the final world+224/+228 position, sets motion state0 and calls502210.
Inspected502210 handles animation/sprite state selection. Within5029A0,
446520 is dispatched by manager kind; its kind2 branch at44678D writes the
indoor camera+6C/+70 and calls4430B0. This distinguishes that branch from an
exit request. It does not prove the entire frame loop has no other producer.

Together with the live eight-step movement-only capture, these results leave
server-side transfer-on-movement as a plausible alternative to an additional
client exit opcode, but not a verified official rule. No destination is encoded
by the qualified49250 classifier. Continue investigating world command/queue
producers and native scene-connection metadata; do not wait indefinitely for
an unproven extra packet or label a chosen return destination native.

## Current town has an explicit grocery asset reference

Pinned CityI1/cityI1.mdlZ (town_navigation.MDL_SHA and MDL_DECODED_SHA)
placement80 at decoded offsets37213..37265 has record SHA256
c32b73ebf69f70817e16c7907d97deff921287c46a54b69cf82566082fbd5dd5,
block(4,2), fields[68,880,680,88,60,0,-1,-1,1,0], and an explicit attached
reference ..\indoor\groceryL.hmd. It is the only placement in this town MDL
with that reference. This is source-linked evidence, not a name-only external
join. Model68 carries pairs[-1,-1,4,12,-1,-1,4,13].

A new test loads those values through original41DF0 and executes original
448D4F..448D91, including49BB0 and the placed-object anchor additions.
Pair1 projects to town(86,70); pair3 projects to(86,71). This is a bounded
coordinate slice, not execution of the full model loader or a live transition.
The existing diagnostic return point110,70 is not replaced or relabeled native.

The pinned Island01.can file maps six scene slots[15,50,53,65,73,90] to the
same record12/indoor/groceryl.hmd. Thus the explicit MDL reference narrows the
asset but does not uniquely select scene15. The regression pins CAN identity,
the six aliases, MDL record hash/fields and both original projection results.
All11 current_indoor_navigation tests pass. Next qualification is the model
reference consumer and scene-instance resolution, followed by a fresh native
town-side approach; the asset link alone must not authorize a production route.

## Reusable explicit town asset-link evidence

tools/strike_lab/town_scene_links.py now exports all26 current CityI1 placement
references ending in.hmd to artifacts/world-atlas/current-town-asset-links.json.
It reuses the bounded current MDL/CAN parsers, pins compressed/decoded MDL and
CAN hashes, retains placement source offsets/hash, raw placement/model fields,
and every matching CAN scene alias. Output is forbidden inside the original
client; resolved source/reference paths must remain inside their allowed roots.
Every destination_scene remains null and route_verified false, even if a
reference has one scene candidate. Source linkage is not gameplay authority.
The deterministic regression checks all26 records and the six grocery aliases.

The inspected original48980 helper tests attached-path extensions against
literal.hmd at587634 and.mdt at5885E0. Its.hmd match writes output kind0 at
48A32..48A36; this is a local helper output, not network kind2 or a scene ID.
The helper's remaining path/coordinate processing must not be confused with
the original protocol selector. No original-network destination has been
recovered by this extension classification, and no production handler/data
was modified by the evidence exporter.

## Fresh native town-side grocery approach

native-town-grocery-approach-20260921-01 completes26 original5024C0 path calls
from restored town111,70 to86,71, with NATIVE_TOWN_GROCERY_APPROACH_COMPLETED,
error null. Original ACKs5D01..5D1A advance the ring to011A1B. Final world
event912 remains area2/scene4/kind0 at86,71 with reward slot5569 unchanged.
SQLite position advances revision57 ->83; the other20 tables and schema remain
equal to the read-only source. The server reports no policy rejection. The
fresh run still has world_accepted=false and is not physical UI acceptance.

The new --town-door-probe runner option restores the existing completed-town
workflow and reuses bounded native path/ACK observation; it cannot be combined
with item-map probes or indoor-door probes. The test itinerary uses26 ordinary
cardinal steps and is not an official route. Exact-point routing rejects
special/unknown cells instead of broadening the previous walkability policy.

Important distinction: source-consensus cell86,70 is02, whereas86,71 is01.
The actual entrance pair1 is therefore not yet approached by this run. The
native502B90 target check tests nonzero. Correction after inspecting
RecoveredMovementService::cell_available: the server also accepts known
nonzero cells; only the test itinerary planner restricts routes to01.
The previous claim that the server authorizer accepted only01 was incorrect.
Qualify the special-cell producer and
server response separately before changing authorization. Do not generalize
all02 cells to ordinary movement or claim the26-step run entered the shop.
Two added regressions cover exact-point routing and the full26-step captured
state/save progression. All25 current_town_runtime tests pass.

## Special entry cell accepts ordinary movement without map transition

--town-special-entry-probe extends the approach with one original5024C0 call
from86,71 to86,70, without any server-policy change. Run01 ends at the1000-event
budget after observing original return1 and ACK5D1B; it is not marked completed.
Run02 adds explicit idle-arrival plus one-second settling and terminates as
NATIVE_TOWN_SPECIAL_ENTRY_MOVEMENT_ACCEPTED, error null.

The fresh client sends0A002E560046001BC2CD, receives05005D1B6D, reaches86,70
in area2/scene4/kind0 with ring011B1C, and stays in that scene during the bounded
settle. The only other decoded post-approach message is the already-known
periodic C2S3000 when present; it is not a newly found exit opcode. SQLite
position is(1,2,4,86,70,84); other20 tables equal the preserved source. No
server rejection occurs. This confirms the existing nonzero-cell authorizer
already permits the native02 entrance cell, correcting the earlier mistaken
claim about server01-only handling. No collision relaxation was necessary.

A permanent regression checks request/ACK wire/plain hashes, checksums,
direction and exact body, native return/queue state, idle/final snapshots and
unrelated saved data. All26 current_town_runtime tests pass. Natural scene
change is still unproven: the explicit native movement call did not generate
an additional transfer request in this window, and no automatic scene response
was configured. Destination resolution and/or interaction-specific state remain
the next tasks; do not promote server-triggered teleport as an original rule.

## Explicit custom fallback proposal, not activated

CUSTOM-0025 separates unresolved scene-instance/trigger choices from the
source-linked coordinates. Lua diagnostic_door.plan proposes2/4/86,70 to
2/15/16,19 and2/15/16,20 to2/4/86,71 only after displacement. Pair selection,
movement trigger and arrival policy are custom test rules, not official
recovery. Arrival cells are deliberately not trigger cells.

LuaEngine::diagnostic_door passes a value snapshot, validates protocol bounds,
accepts nil for no proposal and rejects stationary proposals. It grants no
ownership, writes no state and is not called by Application. The host must
still prove committed position/revision, ready owned session, navigation and
pending receipt before using the existing C++ transfer service.

Release town-guide-lua build and CTest pass: bidirectional proposals,81 nearby
area/scene/cell combinations, stationary and return-arrival non-triggering,
invalid bounds and reload. This is not balance or live acceptance. Next is an
isolated host binding with ACK-before-transfer sequencing and fresh native
roundtrip/persistence verification; production activation remains prohibited.

The standalone diagnostic_door CTest now composes real Lua plans with real
RecoveredMovementService and an isolated in-memory SQLite repository for two
complete town->indoor->town cycles at the source-linked cells. It checks the
encoded transfer through RecoveredWorldFrame::decode against exact logical
61C203000042002600, committed destination, ownership rejection, pending-transfer
movement/battle-resume blocking, stale-source rejection, duplicate receipt
rejection and fresh service restoration. Arrival/stationary positions do not
propose another transfer. Initial test incorrectly compared an encoded wire
byte with a plaintext opcode; fixed to validate decoded content/checksum.
diagnostic_door, town_guide_lua and recovered_movement_service CTests pass.
This is service composition only: Application/tick sequencing and fresh-client
acceptance of the new16,19 arrival still need implementation/verification.

## Default-off Application doorway binding

development.diagnostic_town.door_routes now requires the existing isolated
loopback/dedicated database gate, consensus navigation, guide projection and
explicit indoor navigation; competing map/scene probes are rejected. It does
not require or activate the older map-item trigger. No existing run config was
modified. Lua still proposes only CUSTOM-0025 policy, C++ owns state/storage.

After an owned committed displaced move with a saved before-snapshot,
Application queues the proposal and returns its movement ACK. A subsequent
accepted world tick uses the exact saved source revision with the existing
begin_indoor_transfer/begin_outdoor_return service. During queued/pending
transfer other gameplay is refused. Exact pending01000000 context finishes the
transfer, clears the scene projection marker and lets the next tick restore
the appropriate NPC/journal/inventory projection. Disconnect clears proposals.
Destination scene is constrained to the registered4/15 pair before queuing.

This is implementation, not native-runtime certification: receiver acceptance
of16,19, same-session return/repeat, original NPC cleanup and fresh reconnect
must still be exercised. Original formulas and destination pairing remain
unproven; the custom rule stays explicitly labeled and production-disabled.

## Fresh original-client automatic entry accepted

native-town-auto-door-20260921-01 explicitly enables CUSTOM-0025 only in its
owned run configuration/database. It completes the26-step approach and special
entrance move, then reaches NATIVE_AUTOMATIC_GROCERY_ENTRY_ACCEPTED, error null.
The captured same-socket order is C2S2E560046001BC2, S2C5D1B, S2C61C203000042002600,
then C2S1C01000000. A later world frame is area2/scene15/kind2/16,19/ring010001,
with all961 original indoor grid bytes matching the pinned source and item5569
still occupying the same slot. Server context acceptance and indoor projection
both complete. No map-item request drives this transition.

The isolated save advances from town111,70/revision57 to indoor16,19/revision85
(27 movement commits plus one transfer); all other20 tables/schema equal the
read-only source. No policy rejection occurs. test_current_automatic_door.py
verifies wire/plain hashes/checksums, same-socket exact message ordering,
destination grid/position/ring, inventory preservation, unique transfer/context
and database isolation. It passes. The runner's event budget for this explicit
workflow is4000; historical default budgets are unchanged.

This qualifies original-client protocol/runtime acceptance of the custom
automatic entry, not official scene pairing, physical UI or whole-world
acceptance (world_accepted remains false). Next verify original exit movement
and automatic return on this same connection, followed by repeat/reconnect and
NPC cleanup/visibility. Existing production/runtime configs remain unchanged.

## Repeated doorway lifecycle defect and repair

native-town-auto-roundtrip-20260921-01 is a failed run, not an acceptance:
NATIVE_TOWN_SPECIAL_ENTRY_SERVER_REJECTED. Both entry and return emitted 61
and received the exact context notice. The subsequent town NPC projection
failed because DiagnosticQuestConversation still marked the previous scene's
NPCs as spawned (and retained an opened dialogue). The client had already
cleared its NPC pool indoors; the stale state was on the server.

CUSTOM-0025 now invalidates scene-local conversation availability after the
accepted transfer receipt. It consumes/cancels an old dialogue but retains its
request word, so the next dialogue advances rather than reusing an old token.
Owner/character mismatch cannot invalidate another binding. Projection remains
one-shot per scene. recovered_quest_sync tests four leave/respawn cycles,
unconsumed/consumed dialogues, stale confirmations and unauthorized cleanup.
Both recovered_quest_sync and diagnostic_door pass after rebuilding Release.

Run02 terminates with an observer NPC mismatch, not server rejection. Server
projection logging occurs before the native client has consumed the packet.
The observer now retains the last pending NPC snapshot and waits within the
existing30-second per-hop deadline for the exact pool contents; it does not
weaken the identity/coordinate check or mutate client NPC state.

Run03 (native-town-auto-roundtrip-20260921-03) passes two same-session roundtrips:
four movement/ACK/61/context chains, with native world snapshots1099,1378,1628,
1902 alternating indoor16,19 and town86,71. Each ring is010001. Indoor NPC pools
are empty; both town returns contain exactly1606/110,69 and1607/112,70. The
first movement ACK is5D1B; subsequent hops use5D01 after scene reset. Return
transfer logical bytes are610201000058018E00. All packet hashes/checksums and
same-socket ordering are covered by test_current_automatic_door.py.

The final isolated position is(1,2,4,86,71,91); all other20 tables and schema
remain identical to the read-only source at111,70/revision57. Two captured
regressions and five focused CTest suites pass. This is native-function and
protocol qualification for CUSTOM-0025, not official route recovery or physical
UI acceptance. Fresh reconnect from this final save and multiplayer remain
open; world_accepted remains false and production configs remain unchanged.

## Fresh reconnect after repeated doorway travel

native-town-door-reconnect-20260921-01 restores a read-only SQLite backup of
native-town-auto-roundtrip-20260921-03, without movement or door probes. The
runner now permits the captured town86,71/revision91 checkpoint and observes
its restored world before attempting a distance-invalid guide conversation.
It waits for the actual client journal, inventory and NPC projections, not
only the server send log.

Result: NATIVE_DOOR_ROUNDTRIP_RECONNECT_RESTORED, error null. Native world state
is area2/scene4/kind0/86,71/ring010001, CityI1 resource258. Both expected town
NPCs are present at their custom placements, all15 completed journal slots
are restored, and item5569 remains in slot0. All21 tables and schema match the
source database exactly, including position revision91, quest progress and
reward receipts. No movement_step or automatic_door_hops is recorded and no
door commit/policy rejection appears. test_current_automatic_door.py now has
three passing captured regressions (entry, repeat, reconnect).

This closes the bounded roundtrip-save reconnect check, not physical UI,
multiplayer or full-world acceptance. Historical LOGIN=false classifier flags
are not used as authority for this scoped native world result; world_accepted
remains false. No original-client files or production configs were changed.

## Two-owner interrupted-transfer composition

test_diagnostic_door.cpp now interleaves two different account/character
bindings in the same RecoveredMovementService and DiagnosticQuestConversation.
One character commits an indoor transfer without acknowledging it; the other
still moves in town and consumes its own dialogue. Wrong session/owner receipt
and conversation cleanup attempts are rejected. Removing the interrupted
session makes its old receipt and conversation confirmation unusable.

Rebinding the first character restores the committed indoor destination and
accepts the reset movement sequence1, while rejecting an old town movement and
an unsolicited scene receipt. A second disconnect during the outdoor return
also restores the committed town position. The other character's save and
consumed dialogue state remain unchanged, with its next request word1235.

Release diagnostic_door, recovered_movement_service and recovered_quest_sync
all pass. These are real C++/Lua/SQLite service-composition checks, not a native
two-client visibility, socket interruption or packet-loss acceptance test.
Current-client observer-spawn/movement/despawn protocol qualification remains
required before claiming multiplayer world completion.
