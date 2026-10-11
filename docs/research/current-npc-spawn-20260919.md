# Current S2C72 bounded recovery

`python -B tests/research/test_current_npc_spawn.py -v`: seven tests pass, including
private standalone C++20 compilation with warnings as errors. No shared build,
runtime registration, UI, game process, sockets or source-data changes.

## Provenance

- Current mapped image: `artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`,
  SHA256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
  All addresses below are RVAs, file offset = RVA, image base `0x400000`.
- Current `Data2/Patch/Comm/gamedata.csvZ`: SHA256
  `70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731`;
  decoded SHA256 `75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815`.
- Retained records, SQL and later Classic codec hashes are checked against
  `artifacts/world-atlas/npcs.json`; both full decoded frames retain valid checksums.
  `OfficialNpcReplicationWireCodec.cs` and the later adapter preserve the same
  21 logical bytes. Earlier unresolved protocol notes are not used as authority.

## Current data and instructions

Size table `1324 + 4*72` -> `127C` returns 21. Dispatch table `6B5D4 + 4*72`
-> `6A68B`. `56272..562B3` matches `NPCAppearData` and calls loader `570F0`.
Current section at line 115 has 4043 rows, maximum selector 6224, not 4043.
The loader tracks the maximum ID at resource+`121E8`; slots start at
resource+`121EA`, stride 94. Bounds use a signed WORD count and unsigned WORD ID,
with an inclusive upper bound. Zero passes this guard; that does not establish
that slot zero is usable. An in-range nonzero secondary WORD overrides the
primary record for branch selection; an invalid secondary falls back to primary.

| Primary | Source line | Loader slot+10 flags | Slot+12 resource | NPC.csvZ ordinal |
| --- | --- | --- | --- | --- |
| 3793 | 2401 | 4000 | 88 | 87, npc2788.ROM |
| 3954 | 2545 | 4000 | 82 | 81, npc2782.ROM |

The actual tokenizer `51BE0`, field accessors and loader `5711D..575FC` execute
on these current rows. Only CRT `sscanf("%d")` is substituted, strictly for the
four observed unsigned decimal inputs per row. Column 4 supplies bit 14;
column 2 in 5001..5003 would set bit 15, so neither retained row takes the
composite branch. `61580` executes the resource-byte decrement to ordinal 87/81.
NPC table bytes and source hashes are also checked against the atlas.

With opcode at logical byte 0: primary WORD +1, secondary WORD +3, resource byte
+5, resource type in low five bits of +6. `CC621..CC690` reads primary identity,
direction from +9 >> 5, and position DWORD +17 as x=(word>>2)&7FFF, y=word>>17.
`CC76F..CC78C` passes +9 & 1F to `CAFE0`; no gameplay meaning is assigned to
arbitrary values. Codec retains state 1, directions 5/4, selector high bits 3,
position low bits 0, reserved WORD 0 and opaque bytes `000000CF010000` exactly.
Only coordinates can change, bounded to 0..32767; selector accepts only 3793/3954.
The codec emits logical records, leaving transport and stream ownership to main.

## Native resource progression

Both retained corpora were searched first for 61510/5F190/5F200, table offsets,
and the two ROM names. Classic's NPC import and XJZ's template evidence provide
paths and fields, not a recovered live resource table. Current native code is
the authority below. `tools/strike_lab/current_npc_resources.py` is test-only.

For M=world+AA364B8, bank=DWORD[M+16CE18], Q=M+bank*AD610+3D5D4:
`60CC8..60CDE` selects Data2/Patch/NPC.csv with eight columns. Original
`5E85C..5E8B4` clears the table; `51BE0` and `5E9B0..5EBF7` process all 319 rows.
Q+244E0 becomes 319, Q+2ACCC becomes 10. Group zero at Q+2ACD0 is
base=0, last=88, count=89. Each 76-byte entry contains path[64], signed loaded
slot, action count, palette value, x/y offsets, category, and auxiliary WORD.
Ordinals 81/87 have action count 16, palette value 6, and zero remaining fields.
Both loaded-slot WORDs start at -1. Supplying the actual unloaded lookup result
to CC380 takes its real early return and leaves the natively initialized pool
empty. The dispatcher's separate missing-asset diagnostic path is unqualified.

`5F0E0 -> 5EEC0 -> 29820 -> 1EC0 -> 2A1D0` executes unchanged on the two
hash-pinned ROMZ files. The original LZSS output equals independently decoded
bytes (246947/263835 bytes). Native ROMs each contain ACTINDEX 2776, eight
palettes, 60 images, and 16 actions. Every native image matches an independent
PCX RLE decode; all palettes match the explicit RGB555 test environment.
Compressed and decoded SHA256 values are pinned in the helper's ASSETS table.

In an explicitly empty test bank, loading ordinal 81 then 87 assigns slots 0
then 1 via original `5EF89/5EF90`. These are load-order-dependent native slots,
not wire IDs or a claim about live-world slot numbers. Native cache hits do not
reopen files or increment the counter. `5F190` returns these real slots;
`5F200` returns the source-backed auxiliary value zero. Original `60DB3..60DCE`
propagates the resulting next-slot counter back to M+121FC.

Only CRT read-only file operations, malloc/free, decimal sscanf, and Win32
FindFirstFileA are adapted. The latter reports no virtual temporary files during
decompressor cleanup at 2940; it never searches/deletes host files. Native heap
initialization/allocation and ROM parsing execute. Allocations, input lengths,
instruction counts and time are bounded; unexpected native assertions fail.
The x86 oracle uses FS base zero: a guarded low page models only the SEH chain
at FS:[0], initialized to FFFFFFFF. Only original accesses at 2982A, 29831 and
29A9D are allowed, with exact instruction/access/width checks. The test checks
chain restoration and executes a non-SEH null load to prove it is rejected.

`CA680/FF3C0` initializes the real 256-slot entity pool. The original dispatcher,
`61580/61510/5F190`, `61600/5F200`, `CC380/CCF80/CD760` then execute through
`CC690`. They choose free slots and write (3954, resource 0, direction 4, 240,54)
and (3793, resource 1, direction 5, 65,61). Render handles remain -1.

## Scalar-only boundary

Stop RVA **CC690**, before scene projection. Scene and renderer pointers are
unmapped poison, not fabricated successful structures. Next reads are
ECX=[pool], ECX=[ECX+BC], then scene+30 and possibly scene+103C/+1040 before
`49330`. Recover a qualified current scene object/camera origin, then continue
through `CC6E9` and `CC74C -> CAF60 -> 1AFE0` with its real render manager.
This remains the boundary of the scalar/resource test. The coordinate-only
fixture below separately qualifies the type-2 indoor projection slice with a
native map object. No rendered visibility, live service behavior or historical
world-coordinate match is claimed. Archived area15/map7 is not initial
area2/scene15; do not spawn there.

## Lane B: NPC render-resource dependency

The NPC-only helper now optionally constructs its actual render manager through
`27400 -> 1AA10/1AD30`, bound to the already qualified NPC ROM bank. The shared
indoor helper was read but not changed. Both legacy roots were searched for
`npc2782`, `npc2788`, `CC690`, `CAF60`, `1AFE0`, `NPCAppearData` and the Classic
NPC codec before current-code work. Classic's `OfficialNpcReplicationWireCodec.cs`
retains profiles 3954/3793; XJZ's `evidence-gamedata-npc-appear-v0.md` preserves
raw appearance fields, not the current render-manager implementation. Native
addresses here refer to the same hash-pinned mapped image described above.

The new internal black-box test uses the standalone C++20 logical records,
native current CSV loading, original ROMZ loading and actual entity-pool scalar
writes. At CC690 it deliberately bypasses the unresolved projection block and
resumes at **CC72A**, stopping at **CC751**. Native `CAF60 -> 1AFE0 -> 1B290 ->
1B9C0` allocates the handles and command entries; `1AE20` selects the action,
`1E070` applies the palette and `1FD70` sets its native flag. No native routine
in this chain returns a substituted success value.

This isolated dependency test supplies zero render offsets explicitly and uses
the pixel fields zeroed by the original entity-pool initializer. These are test
inputs, not scene coordinates or a recovered camera. The scene pointer remains
unmapped poison. No indoor scene is loaded and no retained NPC is placed into
area2/scene15. Original CC690..CC72A has not been qualified by this new test.

In the explicit empty test bank, the two retained ROMs occupy resource slots
0/1. Their render handles and surface-command slots also become 0/1, chosen by
the original allocators. Tests compare the generated objects against the C++
record's direction (4/5), the real ROM action pointers, and palette 2 derived by
CC72A from the retained high bits 3. Both surface-command image/palette pointers
match the associated render object and loaded ROM. Original slot 512 rejection
returns FFFFFFFF and leaves the free-render-object count at 4094. These numbers
describe this initially empty test bank, not a live-world identity assignment.

Additional environment adapters are bounded `operator new`, single-thread
critical sections and `SetRect`; their API addresses match the existing indoor
oracle. Renderer constructor SEH access is permitted only at exact pinned
instructions 1AA17/1AA1E/1ABE3. Files close, lock depths balance and FS:[0]
restores to FFFFFFFF. The existing ROM pixel, CSV, selector, scalar, provenance
and non-SEH-null regressions remain passing.

Executed: `python -B tests/research/test_current_npc_spawn.py -v`, six tests
passed, including the private C++20 compile with warnings as errors. The focused
render-dependency test also passed again after explicitly setting its test
render offsets. No shared build or CMake files were modified; any Python-suite
CMake registration remains main's responsibility.

**Production status:** test-only NPC resource capability. No new production
registration, packet emission, Lua rules or placement data are enabled.
**Remaining boundary for this render test:** connect the scene/camera and NPC
resource/renderer lifecycles without transplanting retained coordinates. The
coordinate-only fixture below now covers the type-2 CC690..CC72A slice. After the isolated
CC751 stop, the state-dependent secondary render/resource path at
`CC78C -> CAFE0` remains unqualified. Device rendering, visibility, services,
transport acceptance and end-to-end playability are not established.

## Coordinate-only native scene dependency

`test_native_npc_coordinate_projection_on_loaded_indoor_map` reads the existing
indoor/world-scene helper contracts without changing them. It uses
`NativeIndoorResources.load_manager()` to execute `42A60 -> 48300 -> 37900`
against the hash-pinned `groceryl.hmdz` and `grol.romz` fixtures. The returned
map manager has native type 2 and an actual indoor object at manager+1030.
It uses the existing virtual read-only file, CRT/MFC, lock/rectangle and RGB555
environment adapters; projection and float conversion are never substituted.

Independent HMD parsing reproduces the atlas base and overlays. The HMD base
is **10x30**; the native constructed navigation grid is **31x31**, byte-for-byte
equal to the existing independently generated atlas grid. These dimensions are
different representations and must not be equated. The manager and all 961
navigation bytes remain unchanged after the projection cases.

Original `CA680/FF3C0` initializes the pool. An explicit test owner points to
the real map manager. Its NPC renderer/resource dependencies remain unmapped
poison. The test enters **CC621** with standalone C++20 coordinate-fixture
records and executes continuously through **CC690..CC72A**, stopping before
the render call. It does not run the dispatcher or NPC resource lookup in this
fixture, allocate a visible NPC, or claim a live camera binding.

Both retained selectors run 12 coordinate inputs each: (0,0), (1,0), (0,1),
(17,13), (30,0), (0,30), (30,30), (31,30), (30,31), (65,61), (240,54), and
(32767,32767). Observers require exactly `49330 -> 49B30 -> 149630 -> 149630`
for each case. Native type 2 selects zero map-origin offsets, not the outdoor
manager+103C/+1040 branch. For this native grid, original instructions produce
`(40*(x+y)+40, 20*(30-x+y)+20)`: `49B30` supplies the projection and
`CC6F6/CC6F9` add (40,20). Both actor floats and native integer stack results
match; the stack canary survives and both render handles remain -1. All seven
in-grid samples per selector also round-trip through original `493C0`.

The out-of-grid inputs still project. **Projection success is not a placement
or passability check.** Both historical retained positions are outside this
31x31 grid; the atlas placements remain runtime-ineligible. Those inputs are
arithmetic regression cases only, not NPC placements in area2/scene15.
Replacing the owner map pointer with unmapped poison faults at original
**CC69D**, before any projection helper or actor pixel write. No native success
is stubbed. Virtual files close, locks balance and the SEH chain restores.

Executed:
- `python -B tests/research/test_current_npc_spawn.py CurrentNpcSpawnTests.test_native_npc_coordinate_projection_on_loaded_indoor_map -v`: passed.
- `python -B tests/research/test_current_npc_spawn.py -v`: seven tests passed,
  including the private standalone C++20 compile with warnings as errors.

Changed only the NPC test and this document. No proven production defect was
found or production behavior changed. No shared helper, build, CMake, server
state, packet rules, Lua gameplay, asset source or placement data was modified.
No real client, desktop, graphics device or socket was used.

**Remaining boundary:** the native indoor projection dependency is qualified
as a coordinate-only slice. A single continuous NPC dispatcher/resource/scene/
renderer execution, correct historical scene identity, non-type-2 origin
behavior, the secondary `CAFE0` path and visible/live gameplay remain unqualified.
