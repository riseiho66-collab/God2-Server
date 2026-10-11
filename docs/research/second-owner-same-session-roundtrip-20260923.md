# Second owned character, one-socket town↔indoor qualification

The existing default-off return fixture only admitted map-item requests from
indoor scene15. A completed-guide character at the qualified town entrance
could not enter the indoor scene and then use the same connection to return.
The map-response set was also never cleared after a committed transfer. An
isolated character3 on account3 reproduced the failure: login, world entry
and town projection succeeded, then a C2S25 at town110,70 closed the socket.

`src/core/Application.cpp` now selects the transfer direction from the bound
current scene under the same stage3, item5569, provenance, ownership and exact
coordinate checks. An accepted context receipt finishes the pending transfer,
invalidates the previous scene's NPC conversation, clears the scene projection
marker and allows the next map request. The connection cannot request another
transfer while one is pending. This keeps the return-only fixture usable from
its original indoor save while adding a complete two-direction diagnostic path.

The reproducible `artifacts/playtests/map-enable-20260923-01/setup.py` created
a separate stage3 account3/character3 fixture. `probe.py --roundtrip` ran the
original-format dual-socket sequence on port2596: town item request,
S2C61 indoor17,13, C2S1C context, indoor journal/inventory projection,
original-code-generated move to18,12 with S2C5D ACK, another item request,
S2C61 town110,70, exact context and fresh town NPC projection. SQLite saved
area2/scene4/110,70/revision56; stage3 and the map item remained unchanged.
The first rerun after the code fix stopped at an overly narrow probe assertion:
the valid indoor restore begins with S2CDB journal records and ends with S2C41
inventory. That assertion was corrected, then a fresh fixture in `roundtrip2`
passed `SECOND_OWNER_SAME_SESSION_ROUNDTRIP_SAVED`.

Release `diagnostic_door`, `config`, `recovered_movement_service` and
`recovered_quest_sync` pass 4/4. The captured native scene-transfer Python
suite passes 17/17. The persistent service was rebuilt and restored on
127.0.0.1:2592 as PID13260, but its configuration still has only the map
panel response enabled. The map item is meant to show a map; turning it into
a teleport on the user's service would replace that behavior. Door-based
travel and the movement-related visible black-screen outcome remain open.
