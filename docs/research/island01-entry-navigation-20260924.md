# Island01 approach to the next playable map (2026-09-24)

The current client map catalog identifies area 2/scene 0 as `Island01`, kind 1,
and area 2/scene 4 as `CityI1`, kind 0. The current EnyName catalog has 27
lookup entries for area 2/scene 0 and no group for scene 4. These entries are
enemy display identities, not a spawn table or combat statistics. Ordinary
encounters therefore need another qualified map and trigger; adding random
fights to the current town would lack source support.

`tools/strike_lab/island01_entry_navigation.py` pins the current client
`island01.mbd` and `Island01.mdlZ`, then reconstructs nine 63×63 static
navigation windows around the CityI1 asset placements in Island01. Each
window's independent Python projection matches the compiled C++
`recovered-outdoor-window --dump` output. The generated candidate is
`artifacts/world-atlas/island01-entry-2-0.json`.
The nine base block windows also match the pinned original x86 `47440..474E6`
projection in `test_island01_city_approach_matches_native_base_window`; that
targeted test passed. Model overlays have C++/Python agreement but have not
been tested through the full native scene-streaming path.

The nine windows provide 35,721 cell observations over 11,025 distinct
coordinates. Overlapping windows disagree at 212 coordinates; the artifact
records each conflict and requires a future server loader to reject those
cells. The point (477,209), also present in a CityI1 model placement, has
value 2 in all covering windows. That is an asset/navigation observation,
not a proven teleport target or permitted player spawn.

The current Island01 MDL contains 23 placements referencing CityI1, and the
CityI1 MDL contains 23 placements referencing its parent Island01. Both
coordinate lists are retained in the artifact without pairing them into a
route. At the western edge, static town cell (55,75) and Island01 cell
(477,209) both have value 2; this is a candidate boundary for the next
original-client transition capture. Asset references and matching cell values
alone do not identify the server's transfer trigger or arrival coordinate.

The isolated service can now load this export with the optional
`development.diagnostic_town.island_navigation` path, gated by source
consensus. Its importer combines all nine windows and treats all 212
contradictory cells as unavailable. The movement service supports durable
scene 0/kind 1 position, reconnect, step ACKs, and a qualified scene 4 to 0
transfer primitive. A targeted original x86 test confirms that the current
client's S2C61 prefix parses scene 0/kind 1 at (477,209). The full client
resource streaming path and portal trigger remain unqualified, so no live
route invokes this primitive. This code does not authorize enemy placement,
encounter probability or battle balance. The running 2592 service and its
database were not changed.

`recovered_island_entry_navigation`, `recovered_movement_service`, `config`,
`recovered_town_navigation`, and `diagnostic_door` CTest cases pass. A separate
`build-island-entry` Release server binary links successfully while the live
binary remains locked by the running service.

## Western parent boundary, original model-coordinate execution

The current CityI1 model has six west-edge placements referring explicitly to
`..\\Island01.mdt`; the Island01 model has six matching west-edge placements
referring to `cityI1\\cityI1.mdt`. The original x86 `49BB0` projection was
executed for each placement's pair 1 and pair 3. It yields town pair 1
`(55,75..80)` and pair 3 `(56,75..80)`, and Island01 pair 1
`(477,209..214)` and pair 3 `(476,209..214)`. Every pair 1 cell has static
value 2; every pair 3 cell has value 1 in all covering windows. The regression
is `test_current_island_boundary.py`. This is stronger source evidence for a
western transition than the raw placement anchors, but the exact client
trigger, pair-to-scene mapping and full resource load still require verification.

The movement service now also has an isolated scene 0 to scene 4 transfer
primitive. Its unit test crosses both directions, checks the exact S2C61
selector/kind/coordinates, committed SQLite positions, pending ACK rejection,
scene 0 reconnect and resumed town movement. No application route calls these
primitives on the live listener. A CUSTOM-0036 Lua policy and application route
are now available only with the opt-in `island_routes` setting, requiring the
island navigation export and excluding unqualified scene 0 player presence.
The six western model-point pairs determine its trigger/arrival coordinates.
Lua, config and movement unit tests pass, but original-client scene 0 resource
acceptance and an end-to-end socket route remain to be tested. The running
listener keeps `island_routes=false`.

Reproduce without UI or screenshots:

```powershell
python -B -m tools.strike_lab.island01_entry_navigation --client C:\Users\risei\Desktop\God2\God2 --executable build-town-visibility\tests\Release\recovered-outdoor-window.exe --output artifacts\world-atlas\island01-entry-2-0.json
python -B -m unittest discover -s tests/research -p test_current_outdoor_mbd.py -k island01 -v
```

## Current client crossing, 2026-09-26

The later isolated run `artifacts/playtests/private-island-current-20260926-02`
used the current unpacked client on a private desktop and a test-only SQLite
backup relocated from indoor scene 15 to town `(56,75)` revision 88. The
original client clicked toward the paired western boundary. The server
committed scene 0/kind 1 at `(476,209)` revision 90, then the client sent a
single batch: C2S `1C` payload `04 00 00 00` followed by C2S `2E` destination
`(475,209)`, sequence 1. The older pending-transfer gate allowed only `1C`
payload `04 00 01 00` and disconnected. Run01 used a different click that
did not move; neither run is claimed as successful arrival.

`diagnostic_island_arrival_receipt` now admits `04 00 00 00` only when the
default-off Island01 route is enabled, the session has an owned pending
transfer, and the saved destination is area 2/scene 0. Other door receipts and
battle-result contexts keep their existing gates. The ordinary movement
service validates and acknowledges the following `2E` after resetting the
destination ring. This is CUSTOM-0036 receipt policy over a client-observed
packet shape, not an original server encounter or teleport rule.

Fresh run `private-island-current-20260926-03` accepted the same one-click
crossing and combined `1C`+`2E` batch, then another original-client movement
record and later world ticks. The isolated position finished at scene 0
`(474,209)` revision 92; HP 0/120, MP 50/80, resource revision 2 and one prior
loss settlement were unchanged. The game process stayed alive during the
observation. `verify.py` checks packet order, saved position, resources,
ledger and SQLite integrity and prints `CURRENT_ISLAND_CONTEXT_MOVE_PASS`.
Four focused CTests pass. The test copy of the EXE was removed and the live
port-2592 server was untouched.

This qualifies one current-client town-to-Island01 packet transition and
movement continuation. It does not verify full rendered terrain, arbitrary
island traversal, reverse crossing, monster placement, encounter trigger,
combat statistics, drops or production activation.

`private-island-relogin-20260926-01` cloned the successful scene-0 save without
editing its position. A fresh original-client process logged into scene 0 at
`(474,209)` revision 92, received the saved HP-0 resource packet, then walked
to `(475,212)` revision 95. No additional battle settlement or resource write
occurred; the client stayed alive. Its `verify.py` prints
`CURRENT_ISLAND_RELOGIN_MOVE_PASS`. This closes the isolated cold-relogin and
movement part of this route, while rendered map quality and encounters remain
open.

Four further private desktop probes (`private-island-return-20260926-01` through
`-04`) used cloned scene-0 saves and the same current client to approach the
reverse boundary. The chosen screen clicks produced ordinary accepted C2S2E
movement only: `(475,212)->(475,214)`, then in separate clones either
`(475,214)->(469,211)` or `(475,214)->(470,224)`. No probe reached the
required `(476,209..214)->(477,same-y)` step or emitted a reverse S2C61/C2S1C
exchange. These runs establish continued movement and no server-side rejection
for those paths, but neither reverse transfer nor its context receipt is
current-client qualified. The fourth runner exited normally; the third runner's
console print hit the local cp950 encoding on a diagnostic log replacement
character after writing its result, with no game/session failure in that run.

## Isolated reverse crossing, 2026-09-26

The input helper scales coordinates against an 800×600 client viewport, so
out-of-range click coordinates from early probes do not qualify a portal.
`private-island-return-20260926-05` copied the prior island save and edited
only this private character's position to `(476,210)` revision 96. One in-range
client click at `(700,330)` reached `(477,213)` without crossing because the
CUSTOM-0036 Lua predicate required equal Y on the X-boundary step. In run 06,
the original client independently sent three one-step C2S2E movements:
`(476,210)->(476,211)->(476,212)->(477,213)`. This proves a diagonal final
step in the observed path, not a general original-server portal rule.

The default-off Lua return predicate now admits that one-step diagonal when
both Y values are within 209..214 and X moves exactly 476→477. Run 07 then
committed S2C61 scene 4 at `(56,79)` but the original client answered with
C2S1C payload `04 00 00 00`; the previous pending-transfer gate disconnected.
The receipt is now admitted only for the same account-owned pending transfer
that originated in scene 0 and saved a scene-4 destination. Other pending
town doors cannot use this extra receipt.

Fresh run `private-island-return-20260926-08` used the same test-only cloned
start. The original client walked across the island boundary, accepted the
scene-4 transfer, sent C2S1C `04 00 00 00`, stayed connected, received town
guide restoration, and walked from `(56,79)` to `(56,80)` revision 101.
HP 0/120, MP 50/80, resource revision 2 and the one prior battle settlement
were unchanged. Its `verify.py` checks ordered events, saved coordinates,
SQLite integrity and unchanged resources and prints
`CURRENT_ISLAND_RETURN_AND_TOWN_MOVE_PASS`. The same executable ran on a
private desktop and port 2598; the disposable EXE was removed and the live
port-2592 service was not altered. Rendering quality, natural traversal to
the boundary from farther inland, repeatable encounters, native portal policy
and production activation remain unverified.

`private-island-roundtrip-20260926-01` repeated the isolated test-only start
and then clicked the town's western boundary on the **same client connection**.
The client returned from island to town, moved to `(56,80)`, crossed back to
scene 0, sent the observed C2S1C `04 00 00 00` together with its first C2S2E
destination step `(475,214)` sequence 1, and continued to `(474,214)` revision
105. The server accepted both transfers and the game process remained alive.
Resources and the prior battle settlement stayed unchanged. Its verifier prints
`CURRENT_ISLAND_TOWN_ISLAND_ROUNDTRIP_PASS`. The exact source start `(476,210)`
was placed only in a cloned SQLite database; natural access to that boundary
from deeper island terrain is still open.

After tightening the pending gate so an island transfer cannot reuse the
indoor-door `04 00 01 00` receipt, `private-island-roundtrip-20260926-02`
repeated the same client loop against the rebuilt server. Its independent
verifier again prints `CURRENT_ISLAND_TOWN_ISLAND_ROUNDTRIP_PASS`.
