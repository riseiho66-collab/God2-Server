# Current Initial Indoor Navigation

## Implemented

`src/game/RecoveredIndoorGrid.h` implements the current indoor grid transform
and bounded raw-cell lookup in C++20. `tools/strike_lab/indoor_navigation.py`
parses a strict HMD v1.6 subset, resolves a scene through CAN, invokes the C++
grid implementation, and emits source-derived navigation data. Generated:
`artifacts/world-atlas/indoor-2-15.json`.

```powershell
python -B -m tools.strike_lab.indoor_navigation --client ../God2 --area 2 --scene 15 --grid-executable build/tests/Release/recovered-indoor-grid.exe --output artifacts/world-atlas/indoor-2-15.json
```

The data remains separate from the mock world and character persistence.
The subsequent opt-in movement service now loads it under
`config/recovered-movement.json`; see `current-movement-20260919.md` for that
integration and its limits. The original navigation qualification below does
not itself establish live-world acceptance or speed/gameplay rules.

## Current Evidence

Mapped image SHA-256:
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
Source `Data2/map/island01/indoor/groceryL.hmdZ`, SHA-256:
`42d769c0ff328db3e1e295e17208d0db7a0ff12608976f952dae800ff79c3c00`.
Area2/scene15 resolution is already qualified in
`current-scene-resolution-20260919.md`.

Both legacy corpora were searched first. Classic
`tools/God2.GameplayContentRecovery/ClientMapResourceInventory.cs` reads the
first HMD Pass dimensions but does not reconstruct this diamond grid and its
placement overlays. Its runtime's resource-dimension*21 map bounds cannot be
substituted for the current indoor transform. XJZ's inspected sources provide
catalog HMD references, not a qualified indoor navigation implementation.

Current HMD has two model grids: 10x30 background and 2x8 object. The second
placement's stored grid position is2,8; its160,160 fields are pixel positions,
not the navigation offset. Original loader records them in distinct fields.
The first Model row's stored20,0 is overwritten by the grid builder's computed
background anchor, which is20 for this asset.

## Original Algorithm

All addresses are hexadecimal RVAs; dimensions/positions below are decimal.

- `4CB26..4CE2B`: v1.6 ModelDat frame offsets, portal fields, Pass dimensions
  and per-cell bytes. Original `41880` allocates grids; `41730` writes cells.
- `37250`: placement count and six base fields / ten non-base fields forv1.6.
  Original `365D0`, `41F90`, `41FC0`, and `425F0` construct and link objects.
- `36C30`: computes side `2*max(width,ceil(height/2))+1`, initializes zeros,
  copies base cells, then applies every linked object's zero-valued mask.
- Anchor `side-1-width+(width&1)`. Base cell column c / row r maps to
  `(anchor+c-r/2, c+(r+1)/2)`.
- Overlay stored gx,gy maps to offset `(anchor+gx-gy/2, gx+(gy+1)/2)`;
  overlay c,r then adds `(c-r/2, c+(r+1)/2)`. Signed division truncates to zero.
  Only an overlay byte equal to zero erases the destination. Nonzero overlay
  bytes do not paint a new passable cell or replace a background byte.
- `416B0` reads model pass bytes. `36B60` reads the final grid and returns
  low byte0 for null/out-of-bounds. Do not interpret unspecified EAX high bits.

Result:31x31, 961 raw bytes, 101 nonzero cells. At17,13 the byte is1. All961
bytes match the current original builder. This establishes the raw navigation
representation, not a universal movement permission, speed, path, or collision
policy for all client states.

The C++ implementation refuses invalid dimensions/cell counts, excessive
placements, invalid coordinate ranges and out-of-grid projected overlays.
Native code asserts and skips out-of-grid writes; the importer deliberately
fails closed instead of claiming an incompletely represented asset is valid.
Failed rebuilds retain the prior complete grid. Raw byte values are preserved.

## Executable Qualification

`tests/research/test_current_indoor_navigation.py` reads the exact source tokens
and runs the original ModelDat navigation parser, placement loader, linked-list
construction, full grid builder, and bounded cell getter. No pass bytes, object
coordinate assignments, grid formula, overlay result, or getter outcome is
stubbed. The result is compared with the compiled C++ implementation, not a
second Python implementation of the transform. Synthetic odd/even dimensions,
row parities, negative placement division and overlay ordering are also compared.

Substitutes are explicit: bounded allocator/unused free, CRT fscanf/strcmp/
case-insensitive compare, CString destruction, and model-resource lookup.
The navigation parser starts after graphic-resource layer initialization;
the renderer reference only has a synthetic non-special type so no graphic
activation is performed. Pixel resources, animation rendering and input are
not executed. Current fixture frames are fully covered; strict subset parsing
rejects unsupported file versions/records/base frame arrangements.

The source importer preserves raw model metadata and rejects malformed values,
truncated grids, unsupported trailing sections, missing/divergent plain-Z
variants, source changes during import, and output into the original client.

## Next Protocol Boundary

`legacy-movement-contract-20260919.md` retains movement wire/plain fixtures:
M1 wire `0A0080B8D9C14BA69488` fully decodes under the legacy captured key to
`0A002E12000C0001FF72`, destination18,12, not the old4857,34399 XOR guess.
That legacy key is not the current zero-seed session key.

Initial current static checks locate builder `15790`: two WORD arguments and
one BYTE argument are written into a six-byte body queued with opcode2E through
`132E0`. The sixth body byte is **not initialized in this function**. Its legacy
valueFF must not automatically become a hard state/mount constraint. This
observation was subsequently qualified with original-builder execution and
caller/queue analysis in `current-movement-20260919.md`. Current S2C5D table target `692FA`
writes its byte to world+231, calls103700 and6CC00, then consumes the record.
That follow-up separates the qualified byte/queue contract from unverified live
rendering and gameplay behavior.

## Verification

Release build and22 core CTest suites passed. Five focused Python tests cover
current HMD native/C++ equivalence, raw synthetic grids, overlay signed math,
malformed input, and deterministic source-to-C++ asset compilation. The combined
scene/atlas/world-entry/navigation run executed29 tests in12.568s:26 passed,
three OS-dependent symlink checks skipped. Both agents
completed and were closed. No original client UI/session was launched and no
live world acceptance was claimed; overall playable progress remains the prior
rough10% estimate.
