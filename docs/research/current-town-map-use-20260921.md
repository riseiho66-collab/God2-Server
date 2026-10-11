# Current town map use request

## Evidence and scope

Current mapped image SHA256:
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
The item5569 definition is the actual396-byte loaded record retained in
`native-town-map-item-catalog-20260921-01`, independently matched to the pinned
current gamedata SPI row by the town runtime regression. Flags at11A/11B are
F1/01. No retired archive values are used by this qualification.

## Original execution

New test `CurrentInventoryTests.test_native_owned_map_item_selects_c2s25`
executes original RVA96390 slot wrapper,963C0 inventory search,59A60 item
lookup,96350 producer and132E0 queue append with no substituted instructions
or callees. The synthetic inventory contains only the selected map; the real
loaded definition bytes are mapped into the native lookup table.

The slot wrapper accepts signed byte slots0..29 and a zero context+866E4 gate.
The resolver searches29 down to0 for a positive count with matching low item
word. Its low item ID /100 quotient55 branches directly to C2S25. For5569 the
result begins `25 C1 15 slot`; the final byte is an opaque inherited argument
byte, not evidence of quantity. Original producer96350 ignores the third
argument even though this resolver supplies literal1. No C2S28 call occurs.

Seven executions cover slots0,29,30,49,128,255 and nonzero gate. Accepted cases
append exactly5 bytes, preserve UI and definition memory and balance the stack;
rejected cases append nothing. This does not establish that all UI entry points
use the same slot bounds. Specifically this is the original slot wrapper, not
the full visual inventory event handler or physical double-click.

Static inspection of the inventory event path also finds flags read at9A595,
special-case checks and a25 call at9A6B9. That enclosing UI path was not executed
in this test and is not promoted to runtime evidence.

## Remaining work

This identifies a server-directed request on a proven native use path. It does
not establish the authoritative response that opens a map, whether use consumes
the item, map asset selection, or visible rendering. Keep the server inventory
unchanged until those response semantics are qualified; do not answer25 with
an invented success or assume S2C41 alone is a map-opening response.

Verification:
`python -B -m unittest discover -s tests/research -p test_current_inventory.py -k native_owned_map -v`
passes. This is a new offline original-code execution, not a fresh network run.

## Receiver candidate: S2C3F

Following the current image's PMMap.cpp assertion-string references found the
map interface family C3080..C4Axx. The world dispatch table at6B5D4 maps opcode
3F to6B034, which passes byte1 to C3890. Under its allowed scene/UI predicates,
nonzero byte1 calls C3840, which operates the panel referenced by UI+232DA8
through native1052E0 and optionally operates UI+232E56 through105230.
This is a candidate map-interface response, not yet proof of C2S25 association.

Crucial framing distinction: although this dispatch/consumer only reads byte1,
the original receive parser requires THREE logical bytes. The first attempted
two-byte test exhausted its buffer and entered the unavailable socket path.
Direct parser inspection found length3; the corrected regression executes
all256 byte1 values paired with distinct opaque byte2 values, consumes exactly
three bytes and leaves a two-byte incomplete3F tail buffered. Byte2 is not
assigned an invented meaning and must not be omitted.

The native dispatch and complete C3890/C3840/1052E0 path execute for byte1
values1,2,127,128,255. In explicit synthetic valid-scene/UI fixtures, node flags
change from0010 to0020, stack balances, and inventory bytes remain unchanged.
Resource IDs are explicitly inactive and the optional callback is absent;
no instructions, calls or branch results are stubbed. This does not exercise
rendering or establish visual meaning solely from the flag transition.

Four rejection-path executions stop BEFORE the native message renderer:
byte1 zero selects message330; scene flags low2bits=3 selects32F; scene ID1741
or nonzero UI+232F58 selects369. Those bounded slices leave UI memory unchanged;
the message renderer itself is not claimed executed. Scene pointer validity
is an existing native precondition, not a nullable contract for arbitrary input.

Tests `test_native_map_control_candidate_record_length`,
`test_native_map_control_candidate_dispatch`, and
`test_native_map_control_candidate_rejection_branches` pass. Next qualification
must observe a fresh own-server3F response in the resource-loaded client and
tie its actual panel to the intended map. No production sender, consumption
policy, map authorization or official request/response linkage was added.

## Fresh isolated candidate round trip

CUSTOM-0023 now gates an explicit experiment behind default-off
diagnostic_town.map_probe and the existing loopback/dedicated-town database
requirements. An already spawned, selected/in-world owned character in area2,
scene4 must have completed guide progress plus item5569/count1 in slot0. One
matching C2S25 per connection receives3F0100; no inventory or database mutation.
The opaque final zero and25-to3F association are custom test choices, not
official recovered server rules. Disconnect removes the once-per-session gate.

Run `native-town-map-candidate-20260921-01` reaches
NATIVE_TOWN_MAP_CANDIDATE_PANEL_STATE_OBSERVED with error null. A thunk invokes
original96390(slot0), preserving caller registers/flags, rather than physical
input. The native queue holds25C1150000. Retained crypto-private packet0401 is
C2S frame080025C1150000A7; packet0411 is S2C frame06003F010072 on the same socket.
Native C3890 receives1 and returns with the expected8-byte stack advancement.

Loaded panel1 has type47, resource handle11 and flags0011 before /0021 after;
the remaining48-byte node header bytes and inventory slot0 are unchanged.
A subsequent world frame is observed. Every saved database table equals the
completed-reward source. This closes the fresh transport and resource-loaded
panel-state gap, not visible image correctness, item consumption/authorization
semantics, native official association, or physical interaction acceptance.
world_accepted remains false. A retained round-trip regression checks packet
hashes, socket equality, ordered observations, node changes and all-table equality.

## Loaded panel to original bitmap

Fresh `native-town-map-resource-20260921-01` repeats the candidate round trip
with read-only scene metadata and render-object observation. Error is null.
The scene's metadata pointer is image RVA18B8D4 and exactly matches pinned
image bytes: CityI1, FengHua town, panel words47/5/7. Native C3080..C34E5 reads
the first and third words to create the large-map panel. Runtime panel1/type47
references render handle11; its non-null action header's first44 bytes exactly
match action7 in current Data3/Flow/Island01Map.ROMZ. The trailing runtime
pointer fields are not compared to on-disk bytes.

Asset raw SHA256:
`b4806bf65a45b3b07a9f8cb3e2c30a8c86579948154531b0f02ebd6e830064d3`.
Decoded SHA256:
`de22ae7038a1d03ad2ccd943e793ff46f7ba8312fb776033f8c4e680c52cc4b0`.
Existing structured ROM parser now accepts an explicit name_encoding keyword;
ASCII remains the default for earlier fixtures, CP950 is used for this asset.
Eight actions/images/palettes parse with original chunk bounds. Action7 is
named FengHua town large map; its numeric tuple is10070/0/400/300/1/1.
The400/300 values are action metadata, NOT the bitmap pixel dimensions.
Its ACT_POOL selects image7; ACT_STEP selects palette4. Decoded PCX is800x600.
Independent Pillow decode agrees with the existing decoder on every pixel.

Pixel SHA256: `00473a9a3a22c385af144d663e0f6ec1df2b21af9804ae836c8e5130df48ef07`.
Palette SHA256: `4d3d847d383e515cb552b3f569e4b3ac60e08f8340e12ce067a2dfd921e60540`.
Generated source-map-action7.png in the run directory was visually inspected:
it is the labeled town map with shop/landmark positions, not a blank asset.
This PNG is decoded source art, not a desktop capture or live framebuffer.
Twenty-two town regressions and four pre-existing ROM/UI binding tests pass.
The remaining visual acceptance gap is actual client composition/display,
and candidate item-to-map authorization/consumption is still CUSTOM-0023.
