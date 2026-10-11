# Current Initial Scene Resolution

## Closed Gap

The retained 2A area2/scene15/kind2/(17,13) resolves to a real current indoor
asset. No replacement spawn, area, scene, kind, or coordinates are required
merely because scene15 has no `Map_City_Coordniate` UI row. Production 2A bytes
are unchanged. This closes asset selection, not live rendering/world acceptance.

Follow-up: `current-indoor-resources-20260919.md` executes the original indoor
manager loader through return using actual HMD/ROM/model data, and qualifies
the complete 31x31 projection/cell-center inverse in an offline test environment.
The older stop-at-48300 results below remain the original scope of this note.

All addresses below are hexadecimal RVAs of the pinned mapped current image:
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.

## Original Path

1. `1004F5 -> 6BB60` calls original `59D80(area,0)`, gets catalog MDT+ B0,
   prepends `\\Data2\\map`, and strips the last separator component.
2. `10050C -> 6BC00` uses the same **scene0** row and replaces its extension
   with `.can`. For area2 this is `Island01/Island01.can`.
3. `100524 -> 6C620 -> 44F70` reads that CAN into the map manager. Header is
   exactly eight bytes `CAN v1.0`; u32 file count; count*64-byte records;
   u32 scene count; count*u16 record indices. Scene count is bounded by the
   original 256 assertion. Manager file count is +126C, record pointers +1270;
   scene count +1068, scene indices +106C. Do not trust malformed native files:
   the import tool adds complete bounds/path checks, not just native assertions.
4. `10053E..10055D` selects the branch using actor kind. Kind2 follows
   `10069F..100747`: scene15 -> index12 -> record pointer+1, appends its path
   to the area directory, calls `6C5A0 -> 48300`. Other kinds use `6C520`.
5. Current record12 is tag01 plus `indoor\\groceryl.hmd`. **CAN tag01 is not
   network kind2**; do not copy the byte into a packet as a kind mapping.
6. The actual present compressed file is `Data2/map/island01/indoor/groceryL.hmdZ`.
   It decodes to HMD v1.6 with a `groL.rom` reference and model/pass data.
   Decompression and presence do not establish collision semantics or rendering.

`Island01.can`: 36 asset records, 130 scene slots, 2580 bytes, SHA-256
`f2b9ca9dc4dcebcd1c1c40de14ea63f1b2061993f644c49b9c7baca9ce2d2f97`.
`groceryL.hmdZ`: 329 bytes, SHA-256
`42d769c0ff328db3e1e295e17208d0db7a0ff12608976f952dae800ff79c3c00`.

## Executable Regression

`tests/research/test_current_scene_resolver.py` carries C++ 2A output through
the original decoder and actor projection harness, then runs original
`1004F5` through the call into `48300`. Original catalog row loading, lookup,
area directory/extension processing, full CAN loader, scene index selection,
kind branch and wrapper calls all execute. All 36 loaded records and 130 scene
indices are byte-compared against the actual CAN. Coordinates remain17,13.
Wrong CAN magic is independently rejected by the original loader.

Explicit service substitutes: CRT file I/O reads the exact pinned file into
native-requested destinations; malloc allocates bounded synthetic memory;
strcmp/strrchr/sprintf and CString primitives; working-directory expansion
retains the relative path; UI bounds refresh is stopped at its call boundary.
The prior actor projection harness still substitutes resource/appearance helpers.
No scene index, record pointer selection, branch outcome, or path value is
substituted. Code pages remain read/execute. Execution stops **before** the
indoor loader creates graphic resources. This is not a client process, screenshot,
native session, packet capture, playable-world proof, or collision test.

## Reusable Scene Import

`tools/strike_lab/world_scenes.py` now generates
`artifacts/world-atlas/current-scenes.json` from the current catalog's area-base
CAN files. It preserves all raw64-byte records, opaque tags, index mappings,
source offsets/hashes, and plain/Z asset alternatives. CLI:

```powershell
python -B -m tools.strike_lab.world_scenes --client ../God2 --output artifacts/world-atlas/current-scenes.json
```

Current counts: 14/14 area-base CAN files, 303 asset records, 613 scene slots;
287 records / 585 slots have an exact present asset variant. Repeated slots may
refer to one asset; these are not 613 distinct graphic files. The remaining
28 slots are recorded as absent, not substituted. Zero scenes are server-loaded
or runtime-render-validated by this importer. The 144 UI rows remain a separate
catalog, not overwritten by the scene index.

The parser checks bounded counts, exact sizes, terminated strings, record-index
bounds, path traversal/Windows aliases and resolved subtree containment. Output
inside the original client is rejected. `test_world_scenes.py` tests import,
determinism, negative bounds, and current2/15 provenance. Real symlink tests may
skip where Windows does not permit symlink creation; no elevation is requested.

## Legacy Cross-Check

`legacy-initial-scene-transition-20260919.md` found six saved legacy61 transition
fixtures and a persisted-location restore policy, but no causal official
initial2A->61 sequence. Those fixtures must not be appended merely to repair
the formerly apparent catalog mismatch. Both Classic and XJZ were checked;
the latter's relevant evidence tables contain no samples.

## Verification

Integrated run: 21 core CTest suites passed; 122 Python tests ran in81.998s,
119 passed and three OS-dependent symlink tests skipped (Windows privilege).
Both bounded agents completed and were closed. No C++/Lua production ownership
or bootstrap bytes changed. No original-client process, native gameplay session,
or rendered-world acceptance occurred in this iteration. Overall playable
progress remains the prior rough10% estimate, not a measured completion ratio.
