# Original client map item UI on a private desktop (2026-09-23)

The original client ran through Locale Emulator on a private Windows desktop,
using loopback port 2598 and a copied SQLite database. The persistent service
on port 2592 and the player's save were untouched. The isolated character was
already guide stage 3 with item 5569/count 1 in slot 0. The fixture moved that
character's copied save from indoor (2,15,16,19)/revision 83 to known town
(2,4,86,71)/revision 84; this is explicit setup, not a natural transfer.
The source and setup are recorded in
`artifacts/playtests/private-map-item-ui-20260923-01/fixture.json`.

The original client opened its inventory from the bottom toolbar and showed
the map item in slot 0. A single left-click showed its tooltip. Two synthetic
left-button down/up pairs did not use it. A targeted native Windows
`WM_LBUTTONDBLCLK` on that item reached the original client UI handler: the
server logged `DIAGNOSTIC_TOWN_MAP_CANDIDATE ... CUSTOM-0023 no_consumption`,
and the client displayed the full town map with labels, landmarks, and the
character marker. The map screenshot is
`artifacts/playtests/private-map-item-ui-20260923-01/item-dblmsg/window-1790173066859764600-03.png`.
This tests a real client UI event path, but the double-click was sent by the
private automation process rather than a human mouse.

The map closed on a left-click in its empty lower-left region. The inventory
then closed from its X button. A further world-ground click moved the character
to (2,4,88,71)/revision 86 in both rendered minimap and SQLite, with the
connection still active. Item 5569 remained count 1, matching the current
explicit non-consuming map policy; SQLite `quick_check` returned `ok`.
Screenshots for the tooltip, map closure, and post-map movement are in the
`item-click`, `map-close-click`, and `post-map-move` directories of the same
isolated playtest.

The persistent service already had `diagnostic_town.map_probe=true`; this run
adds original-client visual and continued-movement acceptance for that
existing connected feature. It does not establish official item consumption,
all map items, map travel, Windows 10 rendering, or general world completion.
Client-owned map art and labels remain Traditional, as expected for this
asset. No production configuration or binary was changed in this run.

## Current deployed EXE packet recheck, 2026-09-26

Run `artifacts/playtests/private-map-item-current-20260926-02/` used a fresh
SQLite backup of the pinned completed-guide save. The current deployed
`God2.exe` (SHA256
`6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98`)
ran directly on a private desktop as a disposable copy with only the startup
port immediate changed from 2592 to 2598. The first attempt used an invalid
fixture filename; the server rejected startup before login, and run 02 fixed
the isolated filename requirement.

The current client's inventory item double-click reached the original C2S25
producer and the server's `RecoveredInventoryItemRequest` branch. The log has
`DIAGNOSTIC_TOWN_MAP_CANDIDATE` on session 2. The owned item remained 5569/count
1/revision 2, position remained (2,4,88,71)/revision 86, the client window
stayed alive, and SQLite `quick_check=ok`. See run 02 `ui-result.json` and
`stdout.log`; the four focused CTests `town_guide_lua`,
`recovered_world_service`, `recovered_inventory`, and `current_world_records`
passed. This recheck proves current-build UI-to-C2S25/server acceptance and
the explicit no-consumption policy. Unlike the 2026-09-23 visual run, this
script made no screen capture, so current-build map rendering remains
unverified. The temporary EXE copy and private server were removed/stopped;
the deployed EXE hash, persistent port-2592 service, and player save remained
unchanged.
