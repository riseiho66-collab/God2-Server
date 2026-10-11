# Current-client parent routes — installed 2026-09-27

Release: `artifacts/releases/native-parent-routes-20260927-01`.
Installed candidate SHA256:
`a048c03fdec3b4dc48826dd4d1da06efa998b50775fbfe64904ae7b1c40b289c`.
Loopback listener remains127.0.0.1:2592, managed PID16468 at installation.
Code/config-only deployment preserved every live database table/schema/row,
the authoritative client and enabled multiplayer. No database replacement or
new player grants occurred. Both29-room configuration flags remain enabled.

## Connected routes and evidence

* Area2 CityI1 scene4 ↔ Island01 scene0:22 qualified original point pairs,
  44 directed routes. CUSTOM-0036 uses source point coordinates and explicit
  side/order join and movement activation; this is not recovered server authority.
* Area4 CityI2 scene3 point50,124 ↔ Island03 scene0 point318,363:2 directions.
  Coordinates and reciprocal source placements are native; second-pair activation
  and first-point landing choice remain explicitly CUSTOM-0053.

Lua proposes movement-triggered travel. C++ checks registered routes, account/
character binding, native coordinate/selector widths, source saved baseline,
destination navigation, pending transfer and durable revision CAS. S2C61 commits
the destination; only the session-owned C2S1C receipt reopens movement/presence.
Original context04000000 with its first destination2E is also validated after
the ring reset. No arbitrary context or unregistered destination is admitted.

Full source navigation is loaded for both parent maps: Island01 has1295 windows,
859 available centers and378819 covered cells; Island03 has1040 windows,
782 available centers and344862 covered cells. All6196 /87 conflicting cells
remain rejected. Native MDL/MBD/CAN source and complete export hashes are pinned.
Full navigation availability is not a claim that every map cell is walkable.

## Actual hidden-client acceptance

Final-candidate receipts:

* `artifacts/playtests/private-island01-presence-20260927-04/run-result.json`
* `artifacts/playtests/private-island03-presence-20260927-01/run-result.json`

Each test launches two owned current-client port-only copies on a hidden
desktop against a disposable database clone. Both endpoints, kind0→kind1→kind0,
same-scene names/renderers, remote movement, disconnect removal, fresh cold
login and fresh peer rejoin passed. Returning to the city removes the actor
from the remaining island peer. This does not test removal from a third city
peer at entry, and no screenshot/pixel appearance claim is made.

Island01's original client coalesced the receipt and first destination step:
source arrival476,209 followed by observed native/saved475,209; reverse arrival
56,75 followed by57,75. The harness accepts this only when the exact session's
pending-next-move marker and context-and-move acceptance match the native and
saved positions. It then separately moved to474,209 before cold login.
Island03 separately moved318,363→317,363, cold logged in there and returned
through318,363 to50,124. Neither test wrote client memory or changed the input
desktop. All owned clients/server processes closed; all source files and every
nonposition table stayed unchanged, including all positions except fixturechar4.

The first Island01 multiplayer cold login exposed a real projection defect:
`RecoveredPlayerPresence` rejected kind1. It now admits only current qualified
area2/4 scene0 kind1, retains the exact6F low bits and rejects other kind1/3.
Regression checks cover profile ownership, names, kind-preserving component/
position copies and two-player messages. A subsequent30ms click was missed;
150ms button sampling produced the original movement and receipt. The later
arrival assertion was corrected to validate the independently observed coalesced
step rather than incorrectly reporting a successful original transition as failure.

## Coverage and remaining scope

Service gates passed for76 room directions and46 parent directions:122/122.
Unique original-client point coverage is14/122 (11.5%):previous room10/76 plus
parent4/46 (8.7%). Repeated cold logins do not inflate directional coverage.
Logout/delete acceptance from the prior release remains separately documented.

All-world travel is incomplete. Teleport menus, other parent joins and conflicting
room resource joins remain open. A static consensus reachability check found no
path from configured Kunlun126,126 to parent50,124. Endpoint acceptance does
not establish that birth-to-exit journey. Follow-up source research executed the
original41350/414E0/46FF0 selector/getter on36 conflict observations and checked
five current/target-window selection variants. All still found no outdoor path;
the reachable component changed8251→8263 cells, not a connected exit. Therefore
global byte-consensus rejection alone does not explain the gap. Other original
exit mechanisms, including NPC/menu travel, remain to be recovered. No birth
coordinate, landing or conflicting cell was silently changed to manufacture
connectivity. See `kunlun-parent-window-reachability-20260927.json`.
