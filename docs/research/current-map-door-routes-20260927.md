# Current map doorway routes, 2026-09-27

## Source boundary and measured denominator

The supplied current `Data2/map` contains 142 MDLZ sources. All 142 parse with
the strict current MDL v1.6 reader and contain 1,619 attached map-reference
placements. The retained survey is
`artifacts/world-atlas/current-map-reference-survey-20260927.json`.
These are static references, not 1,619 proven original server edges. Distinct
scenes sharing an HMD resource and paired parent references require separate
server edge qualification. The retired `teleports.json` corpus is not used.

The implemented town scope is CityI1, area2/scene4:

| Current source denominator | Prepared policy and navigation | Still excluded |
|---|---|---|
| 26 attached house references | 23 resource-matched scenes; 26 point pairs; 52 directed point routes | 3 resource mismatches |
| 23 town parent references and 23 inverse Island01 references | 22 paired boundary points; 44 directed point routes | One blocked original arrival cell |

This candidate offers 96 directed point routes across 24 distinct bidirectional
scene pairs (23 rooms and Island01). It does not restore every world map.
Current-client acceptance is measured separately from prepared routes and
unit/instruction execution. Before this round, only room15 and the western
Island01 scene pair had current-client transition evidence; this does not mean
every point in those scenes was physically accepted.

## Native fields and custom policy

Town model source `CityI1/cityI1.mdlZ` SHA256
`bb2b72c2cb368ad9e91046783e1c9638ef02318f589cf462f0c45bbfdce04618`,
decoded SHA256
`59fd88e12c232c89ae8cb73fed4058090e708f963fc9525ededfe157fccfebef`.
Island model source `Island01.mdlZ` SHA256
`cbdc0c946618a1bf4a9b2f221283a17fa58b1f49941b2ea336046851a2519d8d`.
Per-placement offsets/hashes, four model point pairs, exact attached resource,
CAN selector record offsets/hashes, and room HMD source identities are retained
in `town-doors-2.json` and `island01-all-boundaries-routes-2-0.json`.

Original `49BB0` uses signed32 arithmetic and signed division truncating toward
zero: `x = px - py/2`, `y = px + (py+1)/2`. The resulting outdoor point is added
to the exact placement anchor. Indoor points are added to the reconstructed
HMD base anchor: `side-1-width+(width&1),0`. No facing is introduced.
`tests/research/test_current_town_door_points.py` executes the original x86
projection for all nonnegative points in these town/parent/room scopes. It also
compares the actual current EXE SHA256
`6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98`
and its complete projection span with the retained mapped image. Both tests
passed. The mapped image identity remains
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.

The first direct service test found scene7's town point `(82,46)` has covering
window observations1/2. The byte-consensus gate correctly rejected it. A third
native test then executes the complete `46FF0` source-window getter and
`102BF0` straight-path consumer: byte0 truncates the path; bytes1 and2 both
produce the exact `(81,46)->(82,46)` two-node path. The native `41350/414E0`
selector chooses center `(3,2)` for all `(81/82,45..47)` tested coordinates,
whose original window value is2. A separate boolean-consensus predicate is now
used only for this exact point when scene7 is explicitly registered. It accepts
unanimous1/2 walkability and denies0/unknown. Existing byte-consensus behavior
and all other conflicting cells remain unchanged. Three native tests pass;
full A* streaming and physical scene7 entry remain separate acceptance work.

The points and resource references are native evidence. The interpretation as
movement triggers, paired arrival versus exit, and authoritative scene join are
CUSTOM-0052 for houses and CUSTOM-0036 for parent boundaries. CAN does not itself
encode server edge authority. The house policy joins the ordered attached house
records to scene5..30 only where resource names match. Its three excluded records
are TP_Nor_L versus scene10 god01, TP_Nor_R versus scene12 god01, and hotel01
versus scene22 hotel02. No filename alias or alternate destination is fabricated.

The parent policy groups original point pairs by outward direction and joins
matching ordered points to the inverse side: six west, eight east, nine south.
At the first east boundary, the original Island01 arrival `(543,207)` has
unanimous static navigation value0. That pair remains excluded. The other
22 pairs have original value2 triggers and value1 arrivals in every covering
window, as do their town endpoints. Broad parent triggers require movement
across the source point's inward coordinate, admitting one-cell diagonals.

## Runtime ownership and storage

`RecoveredMovementService::TownDiagnostic::indoor_scenes` explicitly installs
the 23-room bundle. Its full bytes are pinned to SHA256
`08ccfb33262913f97383da9abcc8bba58b2705e377fbbec004ee5cdfc35013c2`,
and all grids are reconstructed from their pass layers before use. The larger
Island01 bundle is separately pinned to SHA256
`475faae6162c5fb8c6dc8f2ca6d7b63dfa0e9bc27725d24d7e75eef2bcf43eb9`.
Its 24 windows cover21,168 distinct coordinates; all454 conflicting coordinates
are unavailable. The older nine-window loader contract remains available.

Lua proposes only the explicit configured routes. C++ validates navigation,
registered source/destination scene pairs, account/character ownership, pending
state, saved revision and wire coordinate limits. S2C61 is prepared before a
CAS position commit. During pending transfer, movement is rejected. The accepted
session-bound native C2S1C receipt resets the movement ring, then normal C2S2E
movement may resume. A disconnect before receipt restores the committed
destination on the next fresh login. No account, inventory, resource, companion,
quest, reward or production save is rewritten by bundle loading.

`begin_registered_door_transfer` is restricted to scene4 and a registered room.
Existing Island01 primitives remain restricted to scene4/scene0. Selection
menus `6D`/`99`/`A9` are separate native packet contracts; original teleport
costs, cooldowns and authoritative city destination coordinates remain open.

## Verification and activation status

The direct service test `diagnostic_door` now exercises all26 house point pairs
(52 directed transfers), lost-receipt indoor relogin, correct S2C61 selectors and
kind2, resumed exit movement, foreign receipt rejection and town reconnect. It
also exercises all22 eligible parent point pairs (44 directed transfers), saved
Island01 reconnect and reverse movement. These tests must be built/run against
the final candidate; they do not claim original-client acceptance.

Config/Application wiring and hidden current-client acceptance are performed by
the integrating main task. Promotion must retain the excluded source mismatches
and blocked coordinate, and record actual current-client results by scene/point.

## Current Kunlun room recovery

current_kunlun_doors_20260927.py reads only current CityI2 MDL and area4 CAN/HMD.
Six ordered references exactly match CAN scenes4..9 (konfu,gr01,gr02,gr03,gr04,hofu);
twelve complete point pairs establish 24 candidate directions. Source coordinates
and rebuilt room pass grids are native-derived; the ordinal selector join and
movement activation policy retain CUSTOM-0052. Generated bundle
kunlun-doors-4.json SHA256
9c3af8c338c2c26a5d5ee2156d0105cdf9d893666c656814aaae3973d7333f35.
The outside arrival points are unanimous01. konfu and hofu triggers contain
observations01/02 and need narrow native boolean consumer qualification before
server admission; their generated navigation eligibility is only static
unanimous nonzero evidence, not full current-client path acceptance.
The Island03 parent at placement63905 contains no first entry trigger point.
Its fields6/7 destination query anchor327,351 remains source-derived, but is
not a movement trigger or actor identity. Parent activation is unresolved pending
current click/action producer and reciprocal native placement query.

## Candidate integration and current-client boundary

The integrating task built the area-aware Kunlun registry with explicit source
kind (city4/3 kind0, room4/4..9 kind2), exact selector area4 and owned CAS.
The new service tests cover all12 pairs /24 directed transfers, cold room
restoration, pending movement rejection and foreign receipt refusal. Final
door/movement/config/world-service/repository gates passed after moving the
fixed252x252 navigation arrays to heap storage; Windows exception0xC00000FD
confirmed the previous multiple-service test stack overflow. Four original-code
research tests passed.

Live test `private-current-town-door-5-20260927-05` used the exact candidate
SHA256 `f77df42d65c7b59ac30c9c6074198089926b0db844a29a2e0ac856a626b3c22b`.
One native camera-derived click360,280 entered scene5, received context04000000,
and committed area2/scene5/11,12. Kind2 persisted through cold login. Entry
same-process raw state was identical except expected map fields. Cold owned
state matched; raw empty pet-row cache differences are retained in observations
and are not labeled renderer handles (originalA52A0 copies FB bodies). Source
DB has no owned pet rows, so no FB restoration applies to those caches.
Exit click440,320 emitted no2E; no return is claimed. Next actual test uses
source-walkable12,12 before exact exit11,13 and reads live native grid bytes.
No pixels/screenshots were examined, no user desktop was switched, and all
owned processes closed with source files unchanged.

Whole-current-map source graph:1261 executed coordinate-query edges;1248 have
unique target CAN and placement;1214 have unique source CAN;1094 have first
point pairs and165 only second pairs. Unique source/target joins have no cross
area edges. These are static joins, not implemented or client-accepted routes.
The current area4 parent pair has reciprocal anchors327,351 and53,121, points
Island03(318,363)02 andCityI2(50,124)01. Selected nine Island03 windows were
independently projected with Python and C++ and retained at
`island03-kunlun-entry-windows-4-0.json` SHA256
`5fd7e6189323bcf54853f487f778f3d9ba7bfcd5caf914d444f35305b5975c5a`.
Current click activation semantics and pending live transport remain unresolved.

### Accepted current-client room runs

Candidate `629e875615f2bd152a96c3dd3b70826199da818c5bc8d9a0f1657fdcb73f93e9`
passed town5 first pair, town7 first pair, and Kunlun4 first pair in the real
current client, each entrance + cold room login + exit and complete cleanup.
Town5 uses source-walkable12,12 before exit11,13 and waits for native actor
coordinates plus movement mode0; servercommit precedes original animation
completion. Room7's actual selected window is origin63,42 and original
82,46 trigger byte02, resolving the earlier covering-window01/02 discrepancy
for this route. Kunlun room4 restored kind2 despite sharing scene number4
with the area2 town kind0.

This round live point directions: town4/52, Kunlun2/24, Island01 zero new
point directions. Prior room15 and western Island01 receipts are separate.
Machine-readable receipt hashes and source preservation are retained in
`current-door-native-client-acceptance-20260927.json`. This is client protocol
and native scene/state acceptance; no screenshots/pixels were observed.

### Final candidate room validation

Candidate `4d9ac6a4830e3f31f8637c89ae07359e51b31cf7fa6a6a45a1153164c07b9aaf`
passed town9, town30, and repeated Kunlun4 first pairs: entrance, cold room
login, exit, unrelated native/database state preservation, source hashes,
and complete owned-process cleanup. Receipts are
`private-current-town-door-9-20260927-01`,
`private-current-town-door-30-20260927-01`, and
`private-current-kunlun-door-4-20260927-02` under `artifacts/playtests`.
All three used formal config baseline SHA256
`2a67f9ae6b4a09e9f0f6f80d5be897658a2780cefdc28281a1de7905d418879d`.
Unique live point directions now total town8/52 and Kunlun2/24; repeated
Kunlun4 does not increase the numerator. This final candidate specifically
has town4 and Kunlun2 live point directions in this agent's receipts.
The read-only harness now separates the path index from widget indices;
older receipts' `path_index` field was overwritten by a Python local variable
and is not authoritative. Their actor coordinates, movement mode, emitted
records, scene state, and preservation checks are unaffected.

### Formal room release

Own loopback2592 release `artifacts/releases/native-logout-doors-20260927-03`
installed final candidate4d9ac6... and enabled `all_door_routes` plus
`kunlun_door_routes`; `player_visibility` remains true. Verification records
PID34008 at install, unchanged current client and saved database, with no
database replacement. Connected room configuration comprises23 qualified
town scenes and6 Kunlun scenes,76 service-tested directed point routes.
The exact source coordinates and native scene protocol remain separate from
CUSTOM-0052 selector pairing and movement activation. Live unique point
coverage remains town8/52 and Kunlun2/24; enabling configuration does not
increase that numerator. Three mismatched town scenes and parent routes are
not enabled. CUSTOM-0053 remains source-prepared, with no runtime changes.

## Prepared whole Island03 source navigation (CUSTOM-0053 next phase)

Root explicitly deferred parent runtime changes until fixed logout/delete and
29-room release qualification. CUSTOM-0053 reserves the missing pair2 exit /
point0 landing fallback policy without claiming original activation.
`current_parent_windows_20260927.py --area4 --scene0 --point318363 --all-windows`
exports all1040 original MBD centers,782 available, extent420x1092. Full output
is8,422,055 bytes, SHA256
`64c42e064fab5196cb3c413b8d5c483e73de315407c529683683ef855a340841`.
Every exported window independently matches the source-derived Python and C++
projection. Available-window coverage has344862 cells,87 conflicting bytes
(including5 conflicts solely1/2),29589 unanimous nonzero cells. Conflicts and
uncovered cells stay separate; no global Boolean authority relaxation is
prepared. Original matched Island03 point318,363 is unanimous02, all eight
neighbor points are unanimous01. CityI2 point50,124 is unanimous01; nearby
50,123 /49,124 /50,125 are unanimous01. This is static source navigation,
not an implemented or original-client accepted parent route.

## CUSTOM-0053 parent candidate integration

Candidate SHA256 `85d42d3cfd1c3dd68632dd5ba6f773c159e21168377f2a3ca6b91faab151d444`
now connects area4 CityI2 scene3 kind0 point50,124 to Island03 scene0 kind1
point318,363 and back. Both source coordinates and mutual placement anchors
are exact current-native evidence. Secondpair2 activation and point0 landing
index are CUSTOM-0053 policy; original activation remains unrecovered.
Lua only proposes after displacement. C++ enforces the exact parent pair and
both points, owned ready lease, source saved read-set, CAS, destination nav,
coordinate widths, pending movement rejection, and area-aware selector/kind.
Cold saves restore scene0 kind1. Pending receipt4/0/0/0 admission is limited
to an owned pending parent destination; returning additionally requires the
source-scene0 marker. Live client qualification of that scope remains pending.

`development.diagnostic_town.kunlun_parent_routes=true` requires door routes,
source consensus, `kunlun_parent_navigation` pointing to the full pinned
Island03 artifact, and the existing area4/3 birthplace navigation. Multiplayer
location projection admits only the configured scene0 and uses kind1. Formal
service/config/database/client were not changed during this candidate work.

The same strict full-window loader also accepts the separately pinned
Island01 artifact `island01-full-navigation-2-0.json`, SHA256
`16a428a106eb2bc63f4996af51cf0cdbdb13ab02712d32664123832006920aa6`.
It has1295 windows/859 available centers/378819 covered cells/6196 rejected
conflicts. Existing9/24-window contracts remain available; choosing the full
file avoids misrepresenting the partial route windows as whole-map coverage.
No conflict is relaxed, including the eight Island01 conflicts solely1/2.
Configured Island01 multiplayer now passes Config and visibility location
guards; current-client multiplayer acceptance is still a separate test.

Six CTests pass: recovered_parent_route, diagnostic_door, config,
recovered_movement_service, recovered_world_service, recovered_position_repository.
Parent test proves2/2 service directions, exact points, source/destination
selectors and kinds, foreign owner/wrong landing/stale baseline rejection,
pending move rejection, lost-receipt island coldrestore, leave/reenter return,
city coldrestore, and disabled-registry save rejection. Current-client parent
coverage is0/2 at this checkpoint. Machine-readable scope is retained in
`current-parent-route-integration-20260927.json`; all-world completion is false.

Actual observer coldlogin first exposed an additional
`RecoveredPlayerPresence::from_world_entry` kind1 guard. Candidate
`a048c03fdec3b4dc48826dd4d1da06efa998b50775fbfe64904ae7b1c40b289c`
fixes that projection only for area2/4 scene0; other kind1 scenes and kind3
remain rejected. `recovered_visibility` passes with both source scene kinds,
native6F lowbits preservation through normal-component copy and reposition,
two-peer spawn records, and invalid area/scene/kind rejection. The original
`with_position` masks to retain low2bits, and normal-component copy does not
touch record13..16. No decoder/body rewrite was needed. Root owns actual
two-area retry; this checkpoint does not claim live parent directions.

### Actual Island03 parent acceptance

`artifacts/playtests/private-island03-presence-20260927-01/run-result.json`
accepted candidatea048c03... for both2/2 parent directions. Two original clients
coldlogin into separate city/island scenes; city50,123→50,124 enters
Island03 at318,363. Both peers receive names and original renderer actor
state, movement to317,363 updates the remote peer, island coldlogin restores
the same scene/kind/location, and reentering318,363 returns to city50,124.
Native entry and reverse context receipts both contain04000000. Unrelated
database rows/tables and pinned source files survive unchanged; all owned
clients close and input desktop stays unchanged. No pixels were captured.
CUSTOM-0053 is client-accepted, with formal promotion still false here.

`diagnostic_door` was separately rebuilt after changing its22 Island01 edge
pairs to full1295-window navigation: all44 directions pass in4.18s. Earlier
partial24-window44 direction acceptance is a separate historical gate; the
current test proves the configured full runtime artifact's strict cells.

One usable-condition limit remains explicit: static CityI2 byte-consensus
navigation has no cardinal or eight-neighbor path from126,126 to50,124,
despite both cells being01. The birth component has8251 cells. This isolated
client test starts near the parent and proves the local edge; it does not
prove a journey from that birthpoint. The retained source-only BFS artifact
is `kunlun-parent-static-reachability-20260927.json`. Do not fill this gap
with an invented landing or global conflict relaxation; active window and
full city connectivity need separate native qualification.

### Formal parent release and remaining birth-path scope

Root's code/config-only release `artifacts/releases/native-parent-routes-20260927-01`
installed candidatea048c03... on own loopback2592, PID16468 at install.
Verification confirms current client and saved database unchanged, both parent
flags enabled, fullIsland01 navigation selected, and29-room routes plus
`player_visibility` retained. CUSTOM-0036 and CUSTOM-0053 activation records
are formal-enabled. Combined parent coverage is46 service directions(44+2)
and4/46 current-client directions(2+2); all-world completion remains false.
Town receipt `private-island01-presence-20260927-04/run-result.json` also proves
two peers, remote names/native renderer/movement, coldlogin, scene isolation,
owned context plus coalesced first2E, data preservation and cleanup. The
initial native landing and later durable/native first step remain distinct.

Targeted source research in `kunlun-parent-window-reachability-20260927.json`
compares current-floor, target-floor, current original41350 selector,
target selector, and current-selector(y-1) BFS. All five still lack a
126,126→50,124 path; each reaches8263cells. This is12 more than strict
all-window byte consensus. Original41350/414E0 and46FF0 execute36 selected
observations across those12 conflict cells, retaining all covering-window
raw bytes and nearest blocked frontier. There is no complete shortest path
to deliver. Caller101F90 supplies player(y+1) to459F0, which subtracts1,
so this caller uses unadjusted playerY; other callers remain separate.
No runtime/global-conflict relaxation or changed birth/arrival coordinates
were introduced. A complete native city journey remains an open source and
streaming-timing/connectivity task after this accepted local parent release.
