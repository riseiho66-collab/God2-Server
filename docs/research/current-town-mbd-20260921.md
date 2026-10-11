# Current town MBD block qualification

Pinned current native image SHA256:
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
Town source `Data2/map/island01/CityI1/cityi1.mbd`, 233188 bytes, SHA256
`cf4a4f14f9e5377fa47b4f115d44b1fc90c5c9dff0e3e0f358d781ab8c1030ae`.
Decoded sibling `cityI1.mbdZ` is byte-identical. No retired archive is used.

## Native structure

- 3C280 reads MDT. 3CEF1 selects `.mdl` and calls 3D420 at 3CF2E.
- 3CF50 selects `.mbd` and calls 408E0 at 3CF9A.
- 408E0 reads 16 header bytes: eight-byte magic/version, two u32 block counts.
  It then reads width*height u32 file offsets, beginning at file offset 16.
- 40790 is the block reader. 407D5 indexes `offsets[y*width+x]`; zero returns
  failure without writing the destination. Nonzero seeks to that absolute file
  offset. 407F9..4080E reads destination width*height*8 bytes.
- 3D172..3D18A constructs a 21 by 21 destination with 441 eight-byte entries.
  The native loader has compatibility conversions; raw block bytes alone must
  not be treated as final navigation state.

Town has 9 by 9 block entries, 66 nonzero and 15 absent. Each present block is
3528 bytes. The directory ends at 340; present payloads occupy exactly the
remaining 232848 bytes. `MAPNUM 9 9` is not a 9 by 9 movement-cell grid.

## Implemented checks

`tools/strike_lab/outdoor_mbd.py` is a bounded, read-only MBD v1.2 extractor.
It validates dimensions, directory bounds, payload spans and partial overlap.
Identical offsets may alias the same block. Zero entries stay absent, not filled
with invented walkability. Its size/dimension limits are defensive importer
limits, not claimed native game limits. Cell meanings remain uninterpreted.

`tests/research/test_current_outdoor_mbd.py` runs original 40790 for all 81
town block indices, comparing all 66 payloads byte-for-byte and verifying that
15 absent blocks leave poisoned destination memory untouched. It checks return
values, stack cleanup and exactly 66 seek/read calls. Only CRT seek/read are
adapted to pinned bytes; the owner/header/destination objects are synthetic.
Input-bound tests reject truncated headers, directory and final block, zero or
oversized dimensions, out-of-bounds and partially overlapping offsets, and wrong
version. Both test methods passed in 1.244s.

## Remaining gate

This is not a full terrain load or passability verdict. Follow current consumers
of eight-byte cell fields and MDL overlays, then compare the composed navigation
with native queries before server movement uses it. Full town loading, graphics,
NPC placement and own-server live entry are still unaccepted. No production
config, client executable or player database changed.

## Native base navigation projection

Follow-up disassembly and execution qualify the base layer, not final collision:

- Manager 46FF0 selects kind 0 (outdoor) or kind 2 (indoor). Outdoor queries
  use the 63x63 bytes at manager+0x50 with local coordinates
  `(x-manager[0x103c]+21, y-manager[0x1040]+21)`. Outside the window returns 0.
  The original center-slot lookup 42B50(4) executes in the test.
- 47440..474E6 visits the 3x3 block-pointer array at manager+0xFDC.
  Each nonnull slot contributes 21x21 bytes. At 474B5..474BF the exact base
  projection is `(cell[7] >> 6) & 1`. Other cell bytes/bits do not affect this
  layer. Null slots are skipped: the destination's prior bytes remain unchanged.
- Code after 474E6 applies additional data. In particular 47641 calls 416B0
  for model data and 47666 can overwrite the projected cell with 0; later
  branches can write 2. These later layers are not executed by the base test.

`project_base_window` requires an explicit initial buffer; it never treats absent
blocks as passable or silently invents a native initialization policy. Tests
compare all 81 possible town-centered block neighborhoods against original
47440..474E6, including off-map and absent slots. A separate synthetic block
cycles all 256 final-byte values with the other seven bytes set to 0xFF, testing
bit isolation. Original 46FF0 queries check translated coordinates and four
outside-window boundaries. All four MBD test methods passed in 2.616s.

The next gate is native window initialization and the model/dynamic overlay
composition. A base flag of 1 is not yet a certified final movement allowance.

## Model Pass overlay qualification

Original 47440 has now also executed through its actual return in a synthetic
scene with prepopulated block/model lists. No function in this full builder path
is stubbed: 42B50, 33AF0 and 416B0 all execute current instructions. Rendering,
asset parsing and scene construction remain outside this test; the model records
are fixtures, not claimed town objects.

- 416B0 selects `model+0x4C+36*(frame&255)` (pointer, width, height) and returns
  the Pass byte at row*width+column. The builder only clears cells for value 0;
  1, 2 and 255 all preserve the base byte in this layer.
- With origin already translated into window coordinates, model row r/column c
  maps to `(x+c-floor(r/2), y+c+ceil(r/2))`. Writes are clipped to 0..62 on
  each axis. Translation uses the center block's block coordinates times 21,
  not the raw map width or the manager's scene number.
- The linked list order executes normally; repeated and overlapping fixtures
  agree with sequential Python projection. Both frame 0 and 1 are exercised.
- Fixtures set model+0x2C and +0x34 special-point selectors negative, disabling
  only those data-driven branches. The production algorithm is not patched.
  Special-point writes of value 2 therefore remain a separate unqualified layer.

`apply_model_pass` implements this bounded layer. Five native configurations
cover center placement, upper/left and lower/right clipping, multiple nodes and
overlap. Tests compare all 3969 bytes, original stack restoration and the
builder's final manager+0x10 flag. All six MBD test methods pass (2.694s).
Importer dimension/coordinate limits are defensive, not recovered game limits.

Remaining work: read actual town MDL model Pass frames and placements through
native parsers; determine special-point semantics and window initialization;
compose with dynamic occupants; connect qualified data to C++ movement and
perform current-client own-server acceptance. Synthetic overlay success does
not prove the town's final collision map or normal gameplay.

## Actual town MDL frames and placement fields

Pinned `CityI1/cityI1.mdlZ`: raw SHA256
`bb2b72c2cb368ad9e91046783e1c9638ef02318f589cf462f0c45bbfdce04618`;
decoded 47037 bytes, SHA256
`59fd88e12c232c89ae8cb73fed4058090e708f963fc9525ededfe157fccfebef`.
The complete bounded parser accounts for all bytes: 16 ROM references,
167 tiles, 167 models, 175 Pass frames (6516 cells), 37 placement groups and
362 placements. Names remain raw bytes; no lossy character decoding is used.

The existing MDL parser now offers `allow_parent_rom=True` for a single literal
`..\` prefix followed by a simple ROM filename. Default behavior is unchanged.
References remain data and are never opened. Tests reject deeper traversal,
drive paths, UNC and forward-slash variants. This is not a general path resolver.

`test_current_town_mdl.py` feeds every actual model's frame/Pass token section
into original 4CB26..4CE2B, comparing dimensions and all 6516 resulting bytes,
token exhaustion and allocation canaries. CRT token input and bounded allocation
use the existing indoor harness; layer/resource setup preceding the slice is
not executed. No rendering or full resource-load claim follows.

All 362 placement rows also pass the existing native_mdl_placement oracle:
original row argument flow and model lookup, independent 41FC0 initializer, and
separate frame/extra-field store islands. Model pointers are fixtures. The
container insertion at 38920, attached-map loading and whole-file native loader
are not executed. These results qualify field projection, not scene population.

All three town MDL tests pass (4.080s); the three existing MDL-focused binary
producer regressions also pass (0.264s). No formal database or live config was
modified. Remaining integration must assemble the real parsed placements and
special points into the window and verify native composition before promotion.

## Actual town window composition

All 81 town-centered neighborhoods now match original 47440 through its return,
byte-for-byte across each 63x63 window. Inputs combine actual MBD blocks with
actual MDL Pass buffers produced by the original parser and all relevant actual
placement fields. The independent projection includes special-point writes of 2:
476AF..4774C calls 49BB0, using signed division truncated toward zero, skips a
point when its x selector is negative, and clips writes to the window.

The test initializes four model point pairs to (-1,-1) before native parsing;
41DF0 then applies the real parsed pairs including duplicate suppression. This
initialization is an explicit fixture, not yet a qualified full constructor.
The expected composition reads the resulting canonical first two point pairs,
not raw values whose native setter might have rejected a duplicate.

Scene containers are still synthesized: original 33AF0 performs lookup over
prepopulated group headers, with placements linked in file order. Native
constructor/insertion order remains unqualified. Initial window bytes are
deliberately 0xA5, allowing skipped empty regions to remain visible rather than
silently treating them as walkable or blocked. The test does not establish the
live client's initialization policy, dynamic-actor collision or final map state.

The first run reached the prior 100000-instruction slice limit in the builder;
this larger test now has an explicit 2000000-instruction / 10-second per-window
limit and asserts exact return address and stack restoration. All four town MDL
tests passed in 14.162s. No live configuration or database has been promoted.

## Container order correction and model initialization

The previous file-order fixture is NOT the native insertion rule. 38920 creates
instances with 41F90/41FC0 and calls 425F0. At 42605..42623 that insertion
compares signed `instance[0x10] + model[4]` (pixel Y plus model height), advancing
while the new key is >= the existing key. Ascending order is stable for ties.
Thus actual town window composition above remains conditional on its supplied
list order until native model heights and insertion are integrated.

A new test executes original 424F0, 41F90, 41FC0 and 425F0 without substitutes
for ascending/descending, negative and tied keys. It verifies forward/backward
links, head/tail, counts and stable order after every insertion. Heights here
are explicit synthetic inputs, not recovered town heights. All 167 actual town
models have only their first layer populated; height derivation can focus on
the single-layer native tile/model path rather than inventing a sort key.

The town Pass parser harness now executes actual model constructor 41560
before parsing, instead of directly writing negative special points. It verifies
the four (-1,-1) pairs from native constructor output. This closes the model
special-point initialization fixture gap, not manager window initialization.
All five town MDL tests pass (19.729s). Remaining file-order windows must not be
promoted as final native collision evidence merely because they are green.

## Native-sized and native-sorted town composition

The town harness now executes 4A800..4A842 for each explicit nonzero tile size,
stopping before graphical-resource assertions. Source dimensions are supplied
from the parsed TileModel fields (the 4C420 -> 4A6F0 -> 4A800 argument path is
disassembled, not executed end-to-end). Actual 41A00 then calculates each
single-layer model's dimensions using the supplied layer offsets. All 167 town
models use only layer zero; other layer configurations are not generalized.

All 362 actual placement instances are constructed with 41F90/41FC0 and inserted
with original 425F0 into original 424F0 group headers. An independent stable
sort on pixel Y plus source-derived model height checks every resulting linked
list. Frames are set explicitly from the already qualified placement field.
The full native 47440 then composes all 81 town windows using those actual
native-sorted lists. The independent composition now uses the same qualified
sort rule, not file order. All five town MDL tests pass in 47.286s on the final
revision (an earlier concurrent run finished in 42.292s).

This supersedes the file-order limitation for these tested town windows. It
does not claim a complete MDL/ROM loader: graphics remain absent, block group
tables are prepared rather than allocated by 38920, and the full manager
initialization/window-reuse policy and dynamic blockers are still open. No
production configuration, character database or client executable changed.

## Constructor and sequential-window retention

Actual manager constructor 42A60 -> 462B0 and its native callees now execute
without service substitutes in the bounded test. With a distinct byte pattern
preloaded at manager+0x50, all 3969 bytes remain unchanged after return; block
pointers are zero and both origin fields are -21. Thus this constructor does
NOT establish a zero-filled navigation window. This does not prove whether the
live allocation was zeroed by some outer owner; no such claim is made.

The real-data town test now calls the native constructor and carries each prior
window into the next of the 81 tested centers instead of resetting the window
between centers. Original builder results continue to match the independent
base/model/special-point composition, including retention in absent slots. The
sequential-window test passed in 35.179s; all eight MBD tests passed in 2.688s.
This is a controlled sequence of supplied block slots, not execution of the
complete live cache replacement/streaming lifecycle.

Integration consequence: values retained from absent source blocks cannot be
promoted to authoritative map walkability. A server navigation representation
must track whether a cell was established by current source data and reject
unknown coverage; it must not interpret arbitrary retained bytes as native
terrain. Dynamic occupancy and actual scene streaming are still unaccepted.

## C++ static window component

`src/game/RecoveredOutdoorWindow.h` now reconstructs base blocks, sorted model
Pass overlays and special points in C++20. Its cell API returns optional bytes:
absent source coverage remains nullopt, not a native zero or a movement grant.
A proven overlay write can establish a known 0 or 2 over unknown coverage.
Coordinates are window-relative; callers must supply native-sorted placements.
The component does not sort, perform scene loading, infer dynamic blockers or
authorize movement. No CUSTOM gameplay rule is introduced by this representation.

The existing real-town test now also sends every one of the 81 windows to the
compiled `recovered-outdoor-window --dump` fixture and compares all 3969 known
values/unknown markers against the independent current-source reconstruction.
In the same run, native 47440 still verifies sequential retained-window behavior.
C++ deliberately does not preserve unproven stale bytes as authoritative data.
This three-way test passed in 37.784s. Both CTest recovered_outdoor_window and
the unchanged recovered_indoor_grid passed. The new target uses warnings as
errors; malformed block size is rejected and known/unknown boundaries are tested.

This is a server-side component, not yet an Application integration. The current
RecoveredMovementService remains bound to indoor area2/scene15, and no account,
saved position, live configuration or production map has been changed. Next:
bounded provenance-bearing town navigation import, authorized scene selection,
dynamic occupancy contract and own-server current-client entry/movement checks.

## Reproducible town navigation artifact

`python -B -m tools.strike_lab.town_navigation --client ../God2 --executable
build/tests/Release/recovered-outdoor-window.exe --output
artifacts/world-atlas/town-2-4.json` now exports the pinned town sources into
81 static windows. Each includes its block center, translated origin, 7938-character
cell encoding, known-cell count and SHA256 of that encoding. The header fixes
area2/scene4/kind0 and source paths/raw/decoded hashes. Unknown cells retain `??`.
Original client output paths are rejected; source identity or C++/Python mismatch
aborts before export. Dynamic occupancy and runtime validation remain false.

The exporter stable-sorts source placements by the qualified single-layer height
rule, canonicalizes the four model point pairs with native duplicate suppression,
then composes only the native-selected neighboring groups. All 167 canonical
point pairs are independently compared against native parser output; that native
Pass/model test passed in 10.078s. A fresh full export exactly matches the saved
artifact, with every window length/count/hash checked (1.168s).

This JSON is a static-navigation input candidate, not a formal database import
or runtime authorization. The existing movement service still requires an
explicit town loader and scene-binding change plus client acceptance tests.

## Qualified C++ artifact loader

`src/game/RecoveredTownNavigation.cpp` now loads the town artifact with a 2 MiB
read bound and Windows BCrypt SHA256 verification of the complete file against
`8d49e344225168507ff6e0565c4aed3f80da03113d7bdb51aec7618f84c74c70`.
It also checks the scene identity, window order/origins, cell encoding and counts.
The pin is intentionally byte-exact; a new export requires qualification before
updating it. Unsupported hashing backends fail closed.

Queries require an explicit block center and global coordinates. Unknown cells,
out-of-map coordinates and coordinates outside that center's 63x63 window return
nullopt. This API does not infer client streaming transitions or grant movement.

Release build and all three CTests (`recovered_town_navigation`,
`recovered_indoor_grid`, `recovered_outdoor_window`) passed. The loader test
checks all 321489 window positions: 236817 known and 84672 unknown/outside.
These are overlapping window queries, not distinct map-cell counts. Ten invalid
artifact inputs are rejected: missing, empty, truncated, oversized, altered cells,
area, runtime flag, occupancy flag, known-cell count and source metadata. Signed
integer extremes and both block-center axes are checked without overflow.
Mutated JSON cases prove rejection by the whole-file pin, not independent
coverage of each downstream structural check.

The movement-service inspection confirms it still hardcodes area2/scene15 for
saved-position validation, entry and durable commits. No accounts or production
bindings were changed. Town scene selection, streaming-center semantics, dynamic
occupancy and own-server current-client town movement remain unaccepted.

## Native streaming neighborhood precondition

The current image's 45AA0 path calls 412E0 at 45B4D before replacing the
outdoor window. 412E0 checks every directory entry in the candidate center's
3x3 neighborhood: negative/out-of-range coordinates or a zero directory entry
return false. This is a source-block availability check, not cell walkability.
On the successful path, 45BED/45BF6 store the center multiplied by 21 in
manager+103C/+1040, then 45D23 calls the static window builder 47440.
These caller observations are disassembly evidence; the complete streaming
function and graphics/resource calls have not been executed here.

`test_native_town_streaming_neighborhood_gate` executes original 412E0 for all
81 centers with the pinned town MBD directory and compares its result and stack
cleanup with an independent nine-entry check. Exactly 36 centers pass:
block x in [2,7] and block y in [2,7]. All nine outdoor MBD research tests pass
(3.930s). The synthetic owner supplies the real directory; no gate function is
stubbed. A reconstructed window at another center is NOT thereby an accepted
streaming destination. Do not use this gate to infer collision, spawn locations,
world-coordinate-to-center selection or a normal live transition timing rule.

## Native coordinate-to-center selector

Original 41350 divides each input coordinate by 21 with signed truncation
toward zero, then calls 414E0 to test the resulting center's complete 3x3
neighborhood. If unavailable, it tests the surrounding centers in ascending Y,
then ascending X order, returning the first complete neighborhood. If none is
available it returns zero without modifying the two output coordinates.
414E0 executes its own real directory/bounds checks in this test; no stubs.

`test_native_town_coordinate_center_selection` compares original 41350/414E0
with an independent selector for every 189x189 town coordinate plus 144 signed
and boundary pairs: 35865 cases, 28228 successful selections. Output bytes,
return value and stack cleanup all match. These are selector inputs, not a count
of passable world cells. All ten MBD tests passed in 4.603s. The exhaustive test
uses a 5000-instruction budget per pure native call and requires the actual
return address, avoiding Windows timer-thread overhead per invocation. The
initial timer-based run was intentionally stopped and is not a passing result.

Caller 459F0 passes (x,y-1) to 41350 at 45A36, then passes the selected block
coordinates to 45AA0 at 45A50. This wrapper relationship is disassembly evidence,
not full live caller acceptance. Selection has now been qualified independently;
actual trigger timing, block-cache replacement and movement integration remain.

## C++ center selection and v2 source coverage

The navigation exporter now emits schema v2 with 81 boolean `block_present`
entries directly from the pinned MBD directory. Static cell windows and their
unknown semantics are unchanged. The updated complete artifact SHA256 is
`536bf3d370b256ae38d175c665aabab595ddc9843704699f03d5c9529645684c`;
this supersedes the v1 pin above. The C++ loader requires v2 and validates the
presence array and dimensions before use.

`RecoveredTownNavigation::available_center` checks actual 3x3 source coverage;
`select_center` implements the qualified signed division and neighboring-center
search. It takes original 41350 coordinates, intentionally not applying the
caller-specific y-1 transformation or pretending to choose streaming timing.
The test executable exposes a batch center-query mode. All 35865 coordinate
cases now compare compiled C++, independent Python and original 41350/414E0
results. Ten MBD tests passed in 4.706s, Release build succeeded, and the three
navigation CTests passed. Extreme signed inputs are also rejected safely by
C++ queries. This adds usable server-core behavior but does not activate town
movement in Application or change any saved character positions.

## Movement-service diagnostic binding

`RecoveredMovementService` now has an explicit `TownDiagnostic` constructor
with a pinned navigation path, fixed qualified block center and supplied test
coordinates. The original indoor constructor and defaults remain unchanged.
Town preparation emits area2/scene4/kind0; saved-position checks and atomic
commits use scene4 consistently. Unknown/outside-window and zero cells are
rejected. Existing indoor saves cannot be silently moved into town and town
saves cannot be loaded through the indoor service.

This is laboratory wiring, not a recovered spawn or a new production movement
policy. Tests select adjacent nonzero current-source cells solely as fixtures;
no such placement is asserted as the native start location. The window center
is fixed explicitly rather than inventing an automatic streaming policy. The
existing adjacent-step/ring/transaction contract is reused for this diagnostic;
outdoor client movement and nonzero-cell acceptance still require live checks.

Release `god2-tests` build succeeded. Five targeted CTests passed: movement
service, position repository, movement codec, post-create selection and town
navigation. Added assertions cover invalid centers/placement, no indoor-save
teleport, scene/kind entry bytes, whole-batch rejection without persistence,
town movement commits, reconnect restoration and revision continuity. Tests use
an in-memory SQLite database; no real account was changed. Application still
uses the indoor constructor. Live town entry/movement, dynamic occupancy and
automatic window transitions remain pending, not accepted by these tests.

## Application opt-in and own-server TCP test

Development configuration now accepts a `diagnostic_town` object with integer
`center_x`, `center_y`, `x`, `y`. It requires recovered movement, loopback,
non-mock authentication and the dedicated filename `town-diagnostic-accounts.db`.
Centers are bounded 0..8 and coordinates 0..188 before narrowing; the navigation
loader/service additionally validates actual source coverage and the test cell.
Indoor battle-transition diagnostics cannot be combined with this mode. Existing
quest/world-resource diagnostics require a different isolated database filename
and therefore cannot accidentally reuse their indoor setup here.

Application now routes this explicit configuration to the town constructor.
Absent opt-in, existing behavior is unchanged. Logging identifies scene4/town
instead of incorrectly reporting the indoor scene15. No permanent configuration
or real account database was changed.

`test_town_application_entry_movement_and_reconnect` starts the newly built real
C++ server on loopback with a temporary dedicated database. It authenticates,
creates/selects a character, verifies area2/scene4/kind0 entry bytes, sends the
original-code-generated world-ready and movement frames, receives ACKs, checks
scene4 position revision1, reconnects and verifies restoration plus revision2.
The static fixture placement is selected from adjacent current-source nonzero
cells, not asserted to be an original spawn. The focused test passed in 2.804s.

Config and movement-service CTests passed. The complete ten-case movement-server
suite passed in 29.383s after correcting one obsolete assertion: Application now
installs `world_records`, so unsupported quest/item policies are rejected by that
handler (`Recovered world policy or response rejected`), not by the no-handler
branch. The existing zero-position-commit and zero-movement-ACK assertions remain.
This is real server/network/persistence evidence with a synthetic peer, not a
running original client's town rendering or movement acceptance. The autonomous
live runner still needs town-specific configuration/probe wiring.

## First isolated original-client town entry

`apex.py --town-entry-lab` now selects a fresh town-only database and an explicit
static test placement from pinned navigation window (3,3). It requires isolated
movement/world entry and rejects restore, indoor movement probes, battle, quest
and resource diagnostics. Existing runner behavior is unchanged without the flag.
The C++ artifact pin remains the authority for the selected navigation data.

Run `artifacts/runs/native-town-entry-20260921-01` completed with process exit0,
`result=NATIVE_WORLD_FRAMES_OBSERVED`, `error=null`, `connected=true` and
`world_accepted=false`. This used the original client in the guarded work copy,
the real C++ server and a fresh `town-diagnostic-accounts.db`; no saved character
was copied or moved. The native initializer 64910 returned EAX1, original world
loop655E0 ran, state3 dispatch was observed, and present/frame return sites
67BCA/67BD7 were observed at counters0,1,2. Server logs confirm the original
31/35/28 initializer tail, config_flag0.

Evidence is recorded in the run's result JSON, diagnostic configuration, native
log and server log. These runtime sites establish initialization and frame-path
execution, not a visually inspected town or playable movement. The first-frame
resource sample is all zero; no invented HP/MP state was supplied or certified.
Town movement probing, live cache/scene inspection, visual correctness and
gameplay resources remain open. Do not promote world_accepted on this result.

## Original-client town path round trip

`town_movement_path_page` invokes original 5024C0 with bounded town target
coordinates using full-width immediate arguments. It does not write actor
position or synthesize movement network bytes. The runner validates its observed
starting position/ring, then applies the same native ACK and completion checks
as the existing path probe. Town mode requires at least two steps to observe
post-animation idle, and still prohibits indoor battle/resource/restore paths.

Run `artifacts/runs/native-town-movement-20260921-01`, with `--town-entry-lab
--probe-movement-step --movement-steps 3`, completed with
`NATIVE_MOVEMENT_PATH_COMPLETED`, no error, and world_accepted=false. Starting
at (63,64), original path calls requested (64,64), (63,64), (64,64), all returning
EAX1. Native ACK handlers received 5D01/5D02/5D03, applied each sequence and
advanced the ring to 01/03/04. The observed final position was (64,64) and motion
state0. Read-only SQLite verification found exactly character1/area2/scene4/
x64/y64/revision3. Thus this short town path has current-client original routine,
wire, server commit, native ACK and coordinate/idle completion evidence.

Two permanent tests pass: thunk argument/bounds encoding and retained run
page/ACK/position/database consistency. The latter checks saved evidence, not a
fresh runtime on every test. This was an explicit native-function probe, not a
physical mouse click or a visual inspection. Longer paths, scene/window
transitions, multi-player visibility and complete gameplay remain unverified.

## Continuous 26-step native town path

The isolated runner supports `--town-east-path` with the town movement probe.
Each target is checked against the qualified fixed static window before invoking
the original path routine; blocked/unknown/outside targets abort. Expected live
positions advance one tile per step rather than alternating between two cells.
The saved result now records each town target as well as observed preconditions.

Run `native-town-east-path-20260921-01` used 26 steps and completed with
`NATIVE_MOVEMENT_PATH_COMPLETED`, no error and world_accepted=false. The original
client walked (63,64) through (89,64), crossing coordinate block boundary x84.
All 26 calls returned EAX1; every native ACK sequence1..26 was applied with the
expected ring advancement. Final observed ring is 01/1A/1B, position (89,64),
motion state0. Read-only retained-run regression checks the SQLite position as
character1/area2/scene4/x89/y64/revision26 and every step's code, target, starting
position and ACK. All three town runtime regression tests pass.

This extends current-client movement evidence beyond a two-cell oscillation.
The server deliberately still queries fixed center(3,3), which covers the whole
tested route. Crossing x84 does NOT by itself prove when/how the client streamed
its block cache; no cache-center observation was collected in this run. Automatic
server window selection, outside-window paths and full town traversal remain open.

## Live window observation: no tile-boundary rebuild

Town runs now observe original 47440 entry/return with read-only breakpoints.
The probe records manager origin, caller and stack, then compares every known
cell in the returned 3969-byte window against the corresponding pinned atlas
window; unknown source cells are not asserted. Invalid center, stack mismatch
or known-cell mismatch stops the experiment. Observation is capped at128 builds.

`native-town-streaming-20260921-01` repeated the26-step east path successfully,
with no error and world_accepted=false. Exactly one47440 invocation was observed:
initialization at center(3,3), origin(63,63), and zero known-cell mismatches.
There was no additional47440 call while walking from(63,64) to(89,64), despite
crossing x84. This directly contradicts using every21-tile coordinate boundary
as an automatic navigation-rebuild trigger. The fixed window still covers this
route. It does not rule out other cache operations or prove the actual later
rebuild threshold; those require further observation of the caller lifecycle.

All four retained town runtime tests pass, including all26 ACKs, per-step
preconditions, final idle/position/SQLite and this initial-window observation.
No new server automatic-center policy was introduced on this evidence.

## Camera state and the rebuild branch

Current-image disassembly of46520 shows a viewport test through46C90, followed
by an outdoor-kind check and manager+34 mode check (5,16,17) before its loading
branch.46C90 derives coverage from viewport/tile dimensions and converted camera
coordinates, with comparisons against -19 and40, not simply player x/21.
These are instruction observations, not yet a qualified complete streaming rule.
Caller101F90 also invokes459F0 with player(x,y+1);459F0 subtracts one before41350.
Thus the earlier wrapper y-1 observation must not be blindly applied to player
coordinates: at this caller the adjustments cancel. Other callers still need
their own input-contract verification.

Run `native-town-camera-state-20260921-01` observes manager kind/mode/origin and
world camera before each of26 eastward original path calls. It again completes
with no error and native ACK/idle/durable position agreement. All samples use
one manager with kind0, mode5, origin(63,63). Camera starts(-320,140) and advances
(40,-20) per step, while only the initial47440 build occurs. Therefore this
non-rebuild result is not explained by an ineligible map mode or frozen camera.
The remaining frontier is the viewport coverage threshold and actual loading
branch, not an assumed coordinate-block switch. Five retained runtime tests pass,
including per-step camera movement, stable origin and all26 native ACKs.

## Native detour, actual window rebuild and sequence wrap

`town_probe_route.east_detour` supplies a diagnostic cardinal itinerary using
only source01 cells in the fixed qualified window. It is a test-route planner,
not a replacement for the original client's path algorithm or a gameplay rule.
`--town-detour-path --movement-steps 43` invokes the original path routine for
each adjacent target from(63,64), around blocked(90,64), to(100,70). The observer
checks modulo40 queue tokens and still requires final idle/coordinate completion.

Run `native-town-detour-20260921-01` stopped at EVENT_BUDGET_END after27 complete
steps; no client error was reported and the run is retained as incomplete.
The diagnostic-only event bound was increased to4000 for this longer route.
Fresh run `native-town-detour-20260921-02` completed all43 steps with no error,
NATIVE_MOVEMENT_PATH_COMPLETED and world_accepted=false.

This run observed real47440 builds at centers(3,3) then(4,3), origins(63,63)
and(84,63). Both returned with zero known-cell mismatches against their pinned
static atlas windows. Thus an actual client navigation rebuild occurred, not
merely a coordinate boundary crossing. Step39 ACK5D27 advanced ring01/27/00;
step40 ACK5D00 advanced01/00/01; step43 ended01/03/04. Final native position is
(100,70), motion0, and saved scene4 position revision43 agrees. Seven retained
runtime/route tests pass, including every precondition, target, thunk and ACK.

The server still used its explicit fixed window(3,3), which also covers this
route. Client-side rebuild and source agreement are now observed, but automatic
server window selection and paths leaving that original window remain pending.

## Cross-window source agreement, not invented streaming

Comparing every known global coordinate across the36 source-complete windows
finds28224 covered coordinates, including377 conflicts (for example80,35 is00
in one view and01 in another). Therefore directly combining any nonzero view
would incorrectly hide native projection differences. This remains a recovery
gap, not permission to label a guessed global map native.

The C++ loader now offers `consistent_cell`:27847 coordinates retain their
agreed value,377 conflicting and7497 uncovered coordinates return nullopt.
The full189x189 domain is independently checked against all source-complete
window queries; integer bounds and a concrete conflict are tested.

An explicit default-off `TownDiagnostic.source_consensus` mode uses this gate
in the movement service, registered CUSTOM-0019. It is a conservative test
authority policy over native data, not native streaming recovery or production
approval. In-memory service tests prove adjacent accepted cells beyond the
original fixed window can commit scene4 positions, while fixed mode rejects
that placement and conflicting coordinates remain rejected. Three targeted
navigation/movement/persistence CTests pass. Application activation, original
client traversal beyond the initial window and conflict resolution remain open.

## Native path beyond the initial window

CUSTOM-0019 is now explicitly selectable through the isolated town config's
boolean `source_consensus`; default remains false. Configuration rejects
non-boolean values and retains the dedicated database/loopback requirements.
The runner's `--town-consensus-path` requires the town detour experiment and
plans only agreed01 cells to x110. Its Python agreement map is compared against
the compiled C++ query for all35721 map positions, not just the chosen route.

Run `native-town-cross-window-20260921-01` completed53 original-client path
calls from(63,64) to(110,70), beyond initial center(3,3) window's last x104.
Result is NATIVE_MOVEMENT_PATH_COMPLETED, error null, world_accepted false.
Retained regression verifies every precondition, target, thunk, modulo40 ACK,
final idle and scene4 persisted position revision53. All observed native window
builds match their atlas's known cells. Nine runtime/route regression tests pass;
config and movement-service CTests pass and both server/tests build successfully.

This proves this own-server original-client cross-window path under the explicit
conservative custom gate. It does not resolve377 conflicting coordinates, restore
official server movement authority, establish dynamic occupancy or qualify all
town destinations. No formal account database or default configuration changed.

## Town durability across server restart

The real-server loopback test now saves a non-default town coordinate at
revision3, exits the server context (stopping that process), and starts a new
server against the same temporary SQLite database with registration disabled.
It authenticates the existing account, verifies its existing character list,
checks that the world-entry frame restores scene4 and the saved coordinates,
then sends movement sequence1 and verifies revision4. Account/profile snapshots
are unchanged. Thus reconnect is no longer substituted for process-restart
durability in this test.

Both fixed-window and CUSTOM-0019 variants pass (8.800s for the two tests).
The source-agreement variant starts beyond x104 and verifies that reloading a
position outside the original center(3,3) window does not reset it or silently
fall back to indoor scene15. Placement is an explicitly selected test cell.
These tests use the real server, TCP and file-backed database with synthetic
peers; original-client cold restart at the saved cross-window location remains
unverified and is not claimed by this result.

## Original-client cold restore at the cross-window save

`--restore-town-database` now accepts only an owned run's dedicated town DB
containing the qualified character1/scene4/(110,70)/revision53 checkpoint.
The runner opens the source read-only, checks SQLite integrity, backs it up to
a new run DB and verifies the source SHA256 is unchanged. A restore manifest
records that evidence. Account registration is disabled; the original client
selects its existing character instead of running the creation probe.

Run `native-town-cold-restore-20260921-01` used a new original-client process and
new C++ server with that copied save. It completed with
NATIVE_TOWN_SAVED_POSITION_RESTORED, error null and character_count1. Native
world coordinates are(110,70), ring01/00/01. This fresh initialization selected
center(5,3), and the actual rebuilt navigation matches that atlas window with
zero known-cell mismatches. This differs from the previous walk's retained
center(4,3), reinforcing that center selection depends on lifecycle/state.

The permanent retained-run test verifies original source hash, registration off,
native coordinates/ring and source/target rows of every SQLite table. All rows
remain equal after this restore-only session. Ten town runtime/route tests pass.
Thus original-client cold restore at the saved cross-window location is now
observed. Moving again from the newly initialized center, visual inspection,
conflict resolution and full gameplay remain pending; world_accepted stays false.

## Movement after original-client cold restore

The restore probe now optionally continues into adjacent town path calls after
checking the restored native position and fresh ring exactly once. Its starting
coordinates come from the qualified save, not the default test spawn. Restore
still rejects the unrelated east/detour route modes and leaves source evidence
read-only. No packet bytes or actor coordinates are injected by this extension.

Run `native-town-resumed-movement-20260921-01` opens the qualified save in fresh
client/server processes, restores(110,70) with ring01/00/01, then executes original
path calls to(111,70),(110,70),(111,70). All calls return1, native ACKs5D01..03
advance the queue, and final observed position(111,70) is idle. SQLite retains
scene4 and advances revision53->56. Retained regression compares every other
table with the source and finds no changes; the source SHA256 also remains equal
to the pre-copy manifest. Eleven town runtime/route tests pass. The run result is
NATIVE_MOVEMENT_PATH_COMPLETED with no error; world_accepted remains false.

This closes the tested town save/restart/resume-movement path under CUSTOM-0019.
It does not certify conflicting terrain, physical UI, NPC/gameplay completeness
or production activation. Full playable-world acceptance is still incomplete.
