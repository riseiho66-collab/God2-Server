# Town Quest To Indoor Battle Gate (2026-09-23)

This turn adds default-off CUSTOM-0028. The prior native-call observations
independently qualify a completed town guide reward, indoor transfer/save and
fresh-client reconnect (`native-town-indoor-relogin-20260921-03`), and an
isolated indoor diagnostic skill battle. They do not establish an original
quest-to-encounter trigger or native combat rule.

The new configuration gate permits the combination only in the isolated
loopback town database with the existing dual-map, quest and durable one-round
skill-battle fixture enabled. Application checks the bound character's saved
indoor position, stage-3 guide progress and pinned reward occupancy before
sending any diagnostic battle transition. No production setting changed, and
ordinary town/standalone battle modes retain their prior behavior.

At the initial implementation checkpoint, Release `god2-server` and
`god2-tests` built and the complete test suite passed, including positive
explicit opt-in and invalid-combination checks. The native combined run and
cold reconnect below provide the subsequent original-client evidence.

## Original-client combined run and cold reconnect

`tools/strike_lab/run_town_quest_battle.ps1` runs the owned native client
observer with the process-local Taiwan resource selector and existing pagefile
compatibility. It does not change the client executable or source database.
`apex.py --town-battle-after-quest` requires an isolated stage-3 indoor restore
at area2/scene15/x18/y12/revision55 and the explicit one-round durable skill
fixture. The ordinary town and standalone battle modes keep their prior gates.

`native-town-quest-battle-20260923-05` completed with
`NATIVE_SOCKET_BATTLE_RETURNED_TO_WORLD_LOOP`, error null. The original client
entered the socket-fed battle, selected and sent one native skill command,
consumed its terminal vitals and outcome panel, and naturally returned to its
world loop. Before battle, the observer also confirmed native indoor scene
state and all15 restored journal callbacks. The service reserved and settled battle1 once, with HP100/120,
MP42/80, resource revision2 and XP0. The diagnostic combat values remain
CUSTOM-0012, not recovered original balance. No physical input or visual
playability acceptance is claimed.

`native-town-quest-battle-reconnect-20260923-04` starts a fresh server and
client from a read-only backup of the post-battle database, with battle
transition disabled. It reports `NATIVE_CROSS_MAP_RECONNECT_RESTORED`, error
null. Native scene state is area2/scene15/indoor kind2 at18,12; all15 native
journal slot callbacks match the completed guide. No new battle occurs.

`tools/strike_lab/verify_town_quest_battle.py` checks SQLite integrity, native
result milestones, SHA256 of both backup sources, and every table on the three
databases. The original source hash remains
`6882b0e4c849c8d3e04b7176d4122a7121d278cb081396bae848f3f955b67596`.
Only battle reservation, settlement, XP0, resource and SQLite sequence tables
change from the source to the first run. Position, quest progress, receipt and
inventory slot5569/count1 compare equal row by row. All tables in the cold reconnect
copy equal the post-battle source. Verification result is PASS in
`native-town-quest-battle-reconnect-20260923-04/town-battle-verification.json`.

This closes the narrow combined diagnostic acceptance. Original encounter
admission, monster identity, combat formulas, reward balance, visual operation
and production readiness remain open. Current playability is conservatively
estimated at about30% as a work estimate: authenticated entry, town/indoor
movement, this isolated quest/battle chain and persistence have native-client
evidence, while general gameplay systems and unassisted normal play do not.

## Continuous indoor movement after battle

`native-town-quest-battle-move-20260923-02` runs the same qualified stage-3
source through one skill, terminal settlement and natural world return. The
runner then invokes three original client path requests on pinned indoor grid
cells: (18,12)->(19,12)->(18,12)->(19,12). Native ACKs `5d01`, `5d02`,
`5d03` advance the queue ring to `010304`; the client reaches the last cell
and idle motion state0. SQLite saves area2/scene15/19,12/revision58. The
failed first attempt `native-town-quest-battle-move-20260923-01` timed out
because the observer re-entered its already completed indoor restore check;
it did not save a movement. The corrected observer keeps that check before
battle and follows the movement path after battle.

`native-town-quest-battle-move-reconnect-20260923-01` starts a new server and
client from a read-only backup of the moved database with battle disabled. It
restores native indoor scene2/15/kind2 at19,12 and all15 completed journal
slots, with no further battle or movement. The extended verifier passes: the
only extra table changed relative to the prior battle-only result is
`recovered_positions`; resource, settlement, quest, reward, inventory and
schema rows agree. Every table in the moved cold-reconnect copy equals its
post-movement source. The original source SHA256 remains
`6882b0e4c849c8d3e04b7176d4122a7121d278cb081396bae848f3f955b67596`.
The report is `native-town-quest-battle-move-reconnect-20260923-01/`
`town-battle-movement-verification.json`.

This qualifies continuous native client movement after the isolated custom
battle and durable position restore. It does not establish the original
encounter trigger, combat balance, general indoor routes or physical visual
playability. The work estimate remains about30%; the added path is a narrow
diagnostic continuation rather than broad playable content.

## Same-connection town return after battle

`CUSTOM-0028` now has a separate default-off `return_after_battle` switch.
It requires the existing battle gate plus `scene_return_probe` and
`scene_return_commit`; other battle fixtures and automatic doorway mode remain
separate. The observer waits for the post-battle native send queue to drain,
then invokes the original client's map-item request function. This request is
a diagnostic native call, not physical UI item use. The server uses the
existing `CUSTOM-0024` qualified indoor-to-town map response and durable
position write. Run with `run_town_quest_battle.ps1 -PostBattleReturn`.

`native-town-battle-return-20260923-05` reports
`NATIVE_POST_BATTLE_DURABLE_TOWN_RETURN`, error null. On one original-client
connection, the completed stage-3 indoor save at18,12 passed the one-round
skill battle, outcome panel and natural world return, then queued native
map request `25c1150000`. The original scene receiver accepted area2/scene4/
kind0/110,70, loaded scene258 (`CityI1`) and reset the movement ring to
`010001`. Two projected guide NPCs were observed at1606/110,69 and
1607/112,70. The server logged `DIAGNOSTIC_RETURN_TOWN_COMMITTED` and saved
position revision56. SQLite integrity is OK. Compared with the read-only
source at `native-town-indoor-relogin-20260921-03`, only battle reservations,
settlements, experience, resources, position and SQLite sequence changed;
quest progress, receipt and inventory tables are equal. The source SHA256 is
`6882b0e4c849c8d3e04b7176d4122a7121d278cb081396bae848f3f955b67596`.
The repeatable `verify_town_quest_battle.py --return-run` comparison passes;
its report is `native-town-battle-return-20260923-05/town-battle-return-verification.json`.

Attempts `-01` and `-02` stopped before protocol execution after a runner
argument alignment error. `-03` reached the battle but found the client send
queue occupied at battle exit. `-04` reached the town scene receiver and
durable save but timed out because the observer had not rearmed its world
frame breakpoint for final NPC observation. Both observer issues were fixed
before `-05`. Release server and tests build, the full `god2-tests` suite
passes, and `apex.py` compiles. This remains a composed diagnostic path;
the original encounter trigger, physical map-item use, original combat
formula, visual playability and post-return cold reconnect are open. The
overall playability work estimate stays about30%.

## Same-connection movement-triggered doorway after battle

A separate default-off `door_after_battle` switch composes the existing
`CUSTOM-0028` stage-3 indoor battle gate with the source-linked `CUSTOM-0025`
indoor exit policy. It permits `door_routes` alongside the indoor restore
flags only for this isolated fixture. The competing diagnostic map-item
request handler is disabled in this mode. The original client issues eight
native path requests from18,12 through the pinned indoor grid to16,20;
the final committed move triggers the Lua doorway plan. C++ queues the
transition after the movement ACK, then validates the native context receipt
and saves the destination. Run with `run_town_quest_battle.ps1 -PostBattleDoor`.

`native-town-battle-door-20260923-01` reports
`NATIVE_POST_BATTLE_DOORWAY_TOWN_RETURN`, error null. The captured same-socket
wire sequence contains eight C2S2E path requests and S2C5D ACKs (`5d01`
through `5d08`), followed by S2C `610201000058018e00` and C2S
`1c01000000`. There is no post-battle map-item request. The original client
loads town area2/scene4/kind0 at86,71, resource scene258 (`CityI1`), movement
ring `010001`, and two town NPCs at1606/110,69 and1607/112,70. SQLite saves
revision64: eight moves from revision55 plus one transfer. Quest progress,
reward receipt and inventory are identical to the source. The repeatable
`verify_town_quest_battle.py --door-run` check validates source hash, all
database tables, decrypted wire hashes/checksums and ordering, battle
milestones, NPCs and saved position; it passes in
`native-town-battle-door-20260923-01/town-battle-door-verification.json`.

`native-town-battle-door-reconnect-20260923-03` starts fresh client and server
processes from a read-only backup of that final save. It reports
`NATIVE_DOOR_ROUNDTRIP_RECONNECT_RESTORED`, restores town86,71 and both guides,
replays all15 completed journal callbacks, and starts no battle. All SQLite
tables compare equal with the post-door source; the source hash in the backup
manifest matches the prior run. The extended verifier passes and writes
`native-town-battle-door-reconnect-20260923-03/town-battle-door-reconnect-verification.json`.
The first reconnect command stopped before protocol execution because the
town-progress observer needed its completed-conversation flags; the second
stopped at the saved-position allowlist. The final run adds an explicit
revision64 allowlist entry limited to post-battle doorway reconnect.

This is a stronger functional continuation than the diagnostic map call,
but the exit policy remains CUSTOM-0025 and the movement is invoked through
native functions by the observer rather than physical player input. Original
encounter timing, combat balance, visual interaction and broad gameplay
readiness remain open; the overall playability work estimate stays about30%.
