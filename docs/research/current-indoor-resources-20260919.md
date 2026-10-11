# Current initial indoor resource loading

## Result

The original `48300` manager loader now executes through its normal return with
result 1, using actual initial-scene resources. This extends the prior scene
resolver's stop-at-48300 boundary. No native asset lookup, model allocation,
ROM parser, render-object allocator, navigation builder or projection routine
is replaced with a successful return.

This is a bounded in-memory current-code test, not a launched original client,
live graphics device, displayed world, server connection or full initializer.
Production 2A bytes, default flags, C++/Lua ownership and character data remain
unchanged. Prior real scene resolution remains area2/scene15/kind2/(17,13).

## Evidence

Mapped original image SHA256:
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
Image base 400000; all code addresses below are hexadecimal RVAs.

Both retained Classic source and XJZ implementation corpora were first searched
for 48300, groceryL, HMD v1.6 and groL.rom. No concrete current loader was found
in those searches. Existing current scene and indoor-navigation work supplies
the qualified filename and independent navigation comparison, not a fabricated
native model object.

Files under current `Data2/map/island01/indoor`:

| Source | SHA256 |
| --- | --- |
| groceryL.hmdZ | 42d769c0ff328db3e1e295e17208d0db7a0ff12608976f952dae800ff79c3c00 |
| groL.romZ | 20e5a8be548993e9d17cca9b2d9292b150f73b7907ed720256132ef4659bce6c |
| Decoded groL ROM, 365113 bytes | e76f5966c13b6a74ab9e084a6c0ff7385ca9f0939e5c9d5bb209d33f44c4ea9b |

## Original path executed

- `42A60 -> 462B0` constructs/initializes a real map-manager object.
- `48300` creates the indoor object through `362F0`, its ROM bank and real
  renderer pool through `1AA10`, then calls `37900` on the actual HMD path.
- `37900 -> 4D750` parses the whole HMD. `4D520 -> 4D350 -> 29820` loads the
  referenced ROMZ; original `1EC0` decompresses it and `2A1D0` parses it.
- Real tile/model creation and `4C6F0` model lookup execute. `37250` consumes
  placements, including base model and overlay; `36C30` builds navigation.
- Render-object/command paths include `421F0 -> 41EC0 -> 4A0F0 -> 1AFE0` and
  the real initialized surface-command pool. Returning nonnegative handles is
  not evidence that a graphics device displayed those commands.
- `48300` runs its final `43FB0`, `467F0`, `46840` paths and returns 1. Manager
  mode fields become 2 and 11 by original instructions, not injected answers.

All 961 navigation bytes equal the existing independent HMD/C++ grid. The base
10x30 pass model and 2x8 overlay at (2,8) match the source. The native model list
contains two actual model objects and one overlay node.

The native ROM bank has ACTINDEX 6974, one palette, two image buffers and two
actions. Both native image buffers, 780x580 and 138x125, match an independent
PCX RLE decode byte-for-byte; the palette matches the explicit RGB555 conversion.
The second image size is not the HMD tile-model box size (160x153); do not
replace image dimensions with those nominal model dimensions.

## Projection boundary found

With the loaded 31x31 indoor grid, `49330 -> 49B30` yields asset-space pixels:

```text
px = 40 * (x + y)
py = 20 * (30 - x + y)
```

Those anchors are on shared diamond edges. Original inverse classification
`493C0 -> 49950/499F0` maps the unadjusted anchor to (x,y-1), whereas the cell
interior at (px+40,py+20) maps back to (x,y). Both assertions pass for every one
of the 961 cells. Thus initial (17,13) has anchor (1200,520) and cell interior
(1240,540), in asset space. These are NOT screen click coordinates: viewport,
camera, window geometry, focus and live UI are not established here.

## Explicit environment and limits

`tools/strike_lab/current_indoor_resources.py` uses bounded virtual CRT file
I/O, allocations and token scanning, plus CString value operations. CString
allocations have oracle lifetime; the helper does not simulate MFC heap reuse.
No OS filesystem writes occur. The HMD is supplied as a decoded plain virtual
file, whose bytes independently match original `1EC0` decompression of the
pinned HMDZ. The native HMD temporary-file creation/reopen branch is not run.
The referenced ROMZ follows its actual compressed input path.

The test surface is explicitly RGB555 with a real `27400` reset of the
5000-entry command pool. There is no DirectDraw/window/device creation.
Single-thread critical-section, SetRect and IntersectRect adapters supply their
bounded API semantics; atexit callbacks are recorded, not executed. Pointer
identities are corroborated by the captured ntdll32/user32 module bases and the
matching local SysWOW64 exports. Native gameplay/resource routines are not API
adapters. Unknown file paths or native diagnostics fail the test.

Original code stays read/execute-only; only identified writable global pages
are enabled. Private heap pages are read/write, not executable. The low page
permits only original FS:[0] SEH load/store encodings, and any other null access
fails. Native execution has per-call instruction/time bounds, heap/file/string
bounds, exact stopping PC checks and stack-cleanup checks.

Tests also reject missing ROM and bad HMD identity, check all handles close,
critical sections balance, and the SEH chain restores to FFFFFFFF. These tests
do not claim that every malformed untrusted HMD is safe in the legacy client;
only pinned current assets are accepted by the helper's source boundary.

## Next integration

The qualified native scene object, model resources, render pool and projection
can now replace the previously unresolved scene dependency in an integrated
world/entity oracle. The retained NPC coordinates belong to a different scene;
do not spawn those NPCs in this grocery room to make a picture appear.
The remaining original-client initialization, owned appearance/resources,
camera/display and live transport acceptance must still be established.

## Integrated verification

Full Release build and 31 core CTest suites passed. The five unrelated research
aggregate suites excluded in the prior integration were not rerun here.

Parent ran the 6 new indoor tests, 4 source-backed appearance tests and 8
character-context tests: 18 passed. After heap execute protection and a tighter
instruction-only budget for tiny projection/accessor calls, parent reran the
6 indoor tests plus 20 existing scene-resolution, navigation, appearance and
character-selection tests: 26 passed in 11.476 seconds. These selections cover
38 distinct Python tests, not 44. No failed assertion was waived: the initial
anchor-as-center test was corrected to test the actually observed edge and
center behaviors separately across every cell.

Two agents completed source-backed appearance and 1F character-context work,
were reviewed and closed. The latter's standalone C++ decoder is registered in
CMake; its body remains opaque and does not populate gameplay state. See
`current-appearance-resources-20260919.md` and
`current-character-context-20260919.md` for exact limits.

Overall playable progress remains the previous rough 10% planning estimate,
not a measured acceptance ratio. No fresh original-client E2E or rendered world
was claimed by this batch. The full playable-server goal remains unfinished.
