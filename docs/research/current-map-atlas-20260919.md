# Current Map Catalog And World Candidate Qualification

## Implemented Import

`tools/strike_lab/world_atlas.py` imports all 144 records in the current
`Data2/Patch/Comm/gamedata.csvZ` section `Map_City_Coordniate`. Run:

```powershell
python -B -m tools.strike_lab.world_atlas --client C:\Users\risei\Desktop\God2\God2 --output artifacts/world-atlas/current-maps.json --selector 2 15
```

The output is an idempotent source-derived atlas, not a report-only count.
Each row retains its source line, record hash, raw byte fields, area/scene/kind,
coordinate fields, dimensions, asset paths and present MDT alternatives with
raw/decoded hashes. Names remain original bytes; no encoding substitution.
MDL/MBD/MMB candidates carry presence/size, not verified decoding or rendering.
The one leading separator in the Umg MDT field is normalized only for the
filesystem audit under Data2/map; the original source field is retained.
Absolute/drive/UNC/traversal escapes are rejected. The tool cannot write its
output into the original client directory.

Source SHA-256:
`70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731`.
Decoded SHA-256:
`75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815`.

Counts: 144/144 imported, 134/144 have MDT at the exact normalized catalog path
(plain or Z). **Zero are live-render validated or loaded into the C++ gameplay
world by this importer.** No spawn, collision, NPC, monster or teleport records
are fabricated; absent semantics stay null. Catalog X/Y are not asserted to be
spawn positions, nor are all rows assumed to use the same coordinate meaning.

## Original Loader Qualification

Pinned current mapped image SHA-256:
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
All addresses below are hexadecimal RVAs; CSV columns are zero-based decimal.

Section dispatch `565EC -> 59A80` allocates 420-byte records. Original loader
and lookup `59D80` execute against all 144 current rows in
`tests/research/test_current_map_atlas.py`. The test supplies field buffers in
place of disk-line input, calloc storage, and CRT sscanf("%d"). Original
`51AE0/51B60/51B50/51BA0`, all record writes, masks, shifts, and lookups execute.
Code pages remain read/execute, the trailing allocation guard remains unchanged.

| Columns | In-memory record |
| --- | --- |
| 0,1,2 byte strings | +0,+10,+20 (16-byte fields) |
| 3 area, 5 scene | WORD +F0 = area low6 plus scene high10 |
| 4 kind, 6 X, 7 Y | DWORD +F4 = kind low2, X bits2..16, Y bits17..31 |
| 8,9,10 byte strings | +30,+70,+B0 (64-byte fields) |
| 11,12,13 | WORD +F8,+FA,+FC |
| 14..23 optional labels | Ten 16-byte fields starting +FE |

The oldreborn row's empty dimension fields become zero through the original
empty-value numeric path. They are not replaced with guessed dimensions.
For area2/scene0, Island01 MDT decodes to MAPNUM35x37; the catalog stores735x777.
That ratio alone is not a verified collision grid or universal coordinate rule.

## UI Catalog Is Not The Scene Index

The retained world candidate's area2/scene15 is **absent from all 144 current
rows**; original `59D80(2,15)` returns null after the original loader runs.
Area2 has scenes0,2,108,32,4,43. Its scene0 lookup succeeds, but that does not
authorize silently changing the selected spawn to scene0 or reinterpreting17,13
in another map. No map/position bits are changed in the production candidate.

Independently, the retained candidate's kind2 causes original initializer
`65364..65373` to jump to653EE, skipping the normal `C3F60`/`C3C20` map setup.
Original branch tests distinguish0/1/3 from2. This is a concrete reason the prior
scalar 2A parser test was insufficient to prove ordinary map entry. It does not
prove that no later special-mode/resource path can display anything, and does
not establish a replacement bootstrap policy.

**The scene lookup gap is now resolved, without modifying 2A.** Original
`100180` subsequently uses the area's scene0 catalog row to obtain a CAN index.
Current `Island01.can` scene15 selects record12 `indoor\\groceryl.hmd`.
The kind2 path goes through `6C5A0 -> 48300`, the indoor loader; it is not a
skipped terrain initialization. `groceryL.hmdZ` is present in the original
client. See `current-scene-resolution-20260919.md` and the original-code test
`test_current_scene_resolver.py` for the complete bounded qualification.
Thus absence from this 144-row UI catalog does **not** mean an invalid scene.
Live world acceptance and actual rendering remain unverified.

## Missing Exact MDT Paths

These are filesystem mismatches, not declarations that a whole map is lost:

| Area/scene | Catalog-relative MDT under Data2/map |
| --- | --- |
| 5/40 | South002/cityS04/cityS04.mdt |
| 8/2 | array/9tyr2/9tyr.mdt |
| 8/13 | array/array011/array011.mdt |
| 8/14 | array/array012/array012.mdt |
| 8/15 | array/array013/array013.mdt |
| 7/8 | tong/Reborn/Reborn.mdt |
| 15/7 | North004/Citywei01/Citywie01.mdt |
| 15/8 | North004/Citywei02/Citywie02.mdt |
| 15/9 | North004/Citywei03/Citywie03.mdt |
| 15/30 | North004/Mazewei06/Mazewei07.mdt |

No aliases, spelling fixes, fabricated files, or client modifications were
applied. Actual loader path construction/fallback must justify any later repair.

Verification after integration: Release build, 21 core CTest suites, and the
combined 107 Python regressions passed. The bounded appearance agent was closed.
No original-client live session or rendered map acceptance was performed.
