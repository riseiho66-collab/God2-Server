# Persistent map panel plus natural doorway travel (2026-09-23)

The town map item now keeps its non-consuming S2C3F panel response while
default-off CUSTOM-0025 handles walking across the source-linked doorway.
`Config.cpp` permits `map_probe` with `door_routes` only when competing manual
scene-transfer probes remain disabled. After an accepted doorway context,
`Application.cpp` clears the per-scene map reply marker, so returning to town
does not permanently disable the map item. Quest, ownership, navigation and
transfer gates remain in their existing services.

The isolated character3/account3 `door-panel` probe on port2597 exercised:

- Original-format C2S25 map item → logical S2C `3f0100`.
- 26 original-code-generated town movements to the qualified cell86,70,
  with each S2C5D ACK checked.
- World tick → indoor S2C61 for area2/scene15/16,19, exact C2S1C context,
  and restored stage3 journal/item.
- Original-code-generated indoor move to16,20, then world tick → town
  S2C61 for area2/scene4/86,71, exact context and fresh guide projection.
- Another map item request → the same S2C3F panel response.

SQLite saved character3 at area2/scene4/86,71/revision82. Its stage3 quest
and item5569/count1 remained intact. A separate fresh server and dual-socket
reconnect restored that save and reopened the map panel without changing
position, quest, inventory or reward tables. The probe results are
`SECOND_OWNER_DOOR_PANEL_ROUNDTRIP_SAVED` and
`SECOND_OWNER_DOOR_PANEL_COLD_RECONNECT`.

The prior original-client native-function run for the same CUSTOM-0025 route
observed two roundtrips and scene resources, but physical player input and
visible rendering remain unverified. These rules are custom scene pairing,
not a recovered official server route.

The persistent service now enables `door_routes` and points
`indoor_navigation` to the pinned scene15 atlas. Parsed configuration
comparison confirms those are the only two changes. Its pre-activation
database and config are saved as `persistent-before-door.sqlite` and
`persistent-before-door.server-config.json` under
`artifacts/playtests/map-enable-20260923-01`; the SQLite backup SHA256 is
`e17e17fa4486d3791d1c760db33df906e88816eee942a59a4e1d322e62b07e5b`.
The service restarted as PID4332 on127.0.0.1:2592. Synthetic account login,
world entry and NPC dialogue passed after restart; SQLite `quick_check` is
`ok`, and both persistent character positions are unchanged.

The user's reported movement-triggered timer popup and black screen still
require visible acceptance. The current patch has only native-function
mechanical evidence. Neither this socket probe nor service startup proves
that the physical client can walk the path without that error.
