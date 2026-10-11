# First map item use from an unsaved town spawn (2026-09-23)

CUSTOM-0031 lets a fresh character finish the isolated town guide and receive
item 5569 without walking. This left `recovered_positions` absent. The existing
CUSTOM-0024 map-item transfer required a saved position, so the earned item
could not take that character indoors until the player made an unrelated move.

CUSTOM-0032 uses the authenticated, world-ready movement binding as the current
town location for the item request. The existing guide-stage, owned item slot,
source hash, scene, coordinate, source consensus and destination navigation
checks remain. A dedicated initial indoor transfer accepts only the exact
configured unsaved scene4 spawn; its SQLite compare-and-swap requires no saved
row and creates scene15 at 17,13 with revision1. Existing saved-position
transfers retain their previous compare-and-swap path. A foreign owner,
unsupported destination, pending transfer, or concurrent position write is
rejected before a second transfer is committed.

The socket regression completes three native-format NPC conversations with no
position row, restarts the server, restores the quest and item, sends the
original-format C2S25 item5569 slot0 request, receives S2C61 to scene15 at
17,13, and accepts the C2S1C context receipt. A second cold restart loads the
committed indoor location. C++ movement tests check the first transfer packet,
first revision, foreign-owner and invalid-destination rejection, and repeat
refusal. This remains a default-off custom game rule. The test uses an original
client-format socket oracle; it does not establish rendered client acceptance.

The same socket regression now continues after the second cold restart: it
commits the first indoor step (position revision2), enters the isolated battle
on the next world tick, accepts the original-format C2S36 timer and C2S35
control/action records, receives the damage/animation and S2C89 result, and
commits one battle settlement. The release resets the client movement ring to
slot0, so the following C2S2E step uses slot1 and commits position revision3.
A third cold restart returns the owned item snapshot at the indoor position;
quest, item, position, resources, experience, reservation and settlement rows
match their pre-restart values. This verifies continuity of the default-off
diagnostic route on our socket peer. Actual current-client rendering and
playability of the whole route still require live validation.

## Original client fresh spawn gate

The isolated WinDbg runner now has `--town-fresh-spawn` through
`tools/strike_lab/run_fresh_town_client.ps1`. It creates a new account and
character against a new SQLite file and selects town scene 4 at 110,70 without
restoring a saved position. In `native-fresh-town-20260923-01`, the original
client created and selected character 1, entered its world loop, then sent a
valid single C2S `30/0` heartbeat before its normal `1F/23/1C` initializer
tail. The server rejected that sequence because its tail parser required `1F`
first. The raw packets are `c2s/REAL_C2S_0444.bin` and
`c2s/REAL_C2S_0449.bin`; the native plaintext capture decodes the latter as
`0c001f0023001c01000000ff`.

`RecoveredWorldReady` now accepts exactly one valid `30/0` frame before the
initializer, while retaining rejection of malformed or repeated early ticks.
The original client run `native-fresh-town-20260923-02` reached
`NATIVE_TOWN_GUIDES_ALLOCATED`, with native NPC pool identities and positions
1606 at 110,69 and 1607 at 112,70. Its isolated database has one newly created
`recovered_characters` row at slot 0, and zero `recovered_positions` rows.
`recovered_world_entry` passed, and the restored-save original-client regression
`native-town-reconnect-regression-20260923-01` still reached
`NATIVE_CROSS_MAP_RECONNECT_RESTORED`.

This validates new-character world entry and NPC allocation in the current
client's memory and socket path. It does not yet validate visible rendering,
new-character NPC dialogue, first map item use, or the full battle route in one
original-client session.

## One original-client session through settlement

The same isolated runner then advanced one gate at a time, always starting
with a newly created character and no saved position:

| Run | Native result | Durable check |
| --- | --- | --- |
| `native-fresh-town-quest-20260923-01` | `NATIVE_TOWN_QUEST_ACCEPTED` | guide stage 1 |
| `native-fresh-town-full-quest-20260923-01` | `NATIVE_TOWN_QUEST_THREE_STAGES_AND_REWARD_COMMITTED` | stage 3, item 5569 slot 0, no position row |
| `native-fresh-town-map-20260923-01` | `NATIVE_TOWN_MAP_CANDIDATE_PANEL_STATE_OBSERVED` | native item request and panel path |
| `native-fresh-town-indoor-20260923-01` | `NATIVE_TOWN_TO_INDOOR_DURABLE_RECEIVER_RETURNED` | scene 15 at 17,13, revision 1 |
| `native-fresh-town-indoor-move-20260923-01` | `NATIVE_TOWN_TO_INDOOR_AND_MOVEMENT_COMPLETED` | 18,12, revision 2 |
| `native-fresh-town-battle-20260923-01` | `NATIVE_SOCKET_BATTLE_RETURNED_TO_WORLD_LOOP` | one `battle_settlements` row, resources 100/120 HP and 42/80 MP |
| `native-fresh-town-postbattle-move-20260923-03` | `NATIVE_MOVEMENT_PATH_COMPLETED` | 19,12, revision 5; stage 3, item and settlement retained |

Each result is from the original client connected to our isolated C++ server.
The runner uses original client code paths with diagnostic native calls for
NPC requests, item use, movement and battle skill input; it does not prove
that a human can complete the same path through visible mouse and keyboard
controls. It also does not prove native gameplay balance: the guide, reward,
first unsaved transfer and battle settlement remain identified CUSTOM rules.

Cold restart from `native-fresh-town-battle-20260923-01` produced
`native-fresh-town-cold-reconnect-20260923-01` and restored the stage-3 indoor
save at 18,12. Cold restart from the moved battle save produced
`native-fresh-town-moved-reconnect-20260923-01` and restored 19,12. Both use
read-only SQLite backup into a new per-run database and reached
`NATIVE_CROSS_MAP_RECONNECT_RESTORED` in the original client. These results
close the prior socket-only gap for one end-to-end native-call session while
leaving visible UI playability and production activation as separate gates.

## External UI movement observation

`native-ui-town-click-20260923-01` restored an isolated saved town character
at 110,70 and waited without installing a native movement call page. During
that wait, the original client emitted decoded C2S `2E` records for 110,71 and
110,72 (`packet-decode-1217.json`, `packet-decode-1231.json`). The C++ server
saved 110,72 at revision 55, and the original client memory snapshot agreed
with that coordinate after returning to idle. The run result is
`NATIVE_UI_WORLD_MOVEMENT_SAVED`.

The runner did not log the external input source. Its historical result field
`input_origin=EXTERNAL_WINDOWS_SENDINPUT_NO_NATIVE_CALL_PAGE` asserted
`SendInput` without evidence; future runs now say
`EXTERNAL_INPUT_UNATTRIBUTED_NO_NATIVE_CALL_PAGE`. Windows screen control
failed to bind the rapidly changing game window during this run, so no
attributable automated click or visible screenshot was captured. This proves
an original-client external-input movement path with packet/save agreement,
not which specific device or actor initiated it, and not visible UI quality.

The resulting saved town row was then copied read-only into
`native-ui-town-move-reconnect-20260923-02`. The original client restored
position `(110,72)` from revision 55 with movement ring `010001`, and the
source database SHA-256 was unchanged. This connects the external-input
movement observation to a cold reconnect, but does not resolve input
attribution or the missing screenshot.
