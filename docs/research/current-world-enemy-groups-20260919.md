# Native world enemy resource groups

## Change

`NativeWorldActor` now executes the complete original EnyName loader at RVA
5A1A0, including nested area/scene allocation, original line reads, tokenization,
name copies and packed component fields. Only CRT fgets and calloc are adapted
to an immutable bounded source stream and zero-initialized VM memory. Game
loaders, lookups and row writers are not replaced by successful-return stubs.

Actor initialization now runs continuously from 681CF through 682F1. This
includes original NPC lookup 5AA70, enemy lookup 5A000 and preload-progress
calculation 607D0. The remaining skipped interval is 682F1..68315, containing
the cold resource-bank call 61AD0. The post-preload actor tail and following
scene loader remain their existing qualified native ranges.

## Sources

Both legacy corpora were searched first. Classic's
`tools/God2.GameplayContentRecovery/OfficialClientExtractor.cs` preserves
EnyNameTotal as name/encounter evidence without monster ID/stat promotion.
XJZ's `evidence-monster-client-v0.md` distinguishes visual/ROM records from
monster combat properties. Neither supplies this current native nested loader.

Current source is `Data2/Patch/Comm/gamedata.csvZ`, raw SHA-256
`70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731`,
decoded SHA-256
`75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815`.
The original mapped image remains SHA-256
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.

## Actual native table behavior

The source has 7815 records, 97 scene descriptors and 16 area declarations.
Area 7 appears twice. Original 5A21E/5A226 allocates and replaces that area's
descriptor pointer. It does not append or merge its earlier table. Consequently
96 scene groups / 7791 records are visible through the final lookup table;
24 earlier records remain allocated but are no longer selected by area lookup.

This is why rejecting every duplicate area was wrong for the actual source.
The first bounded implementation did reject it before native execution; it was
corrected to mirror the observed original pointer replacement. The source file
was not repaired or edited to make it conform to an assumed schema.

The outer `EnyName,7931` count differs from the consumed envelope. The original
loader actually uses the next `EnyNameTotal,7815` value and nested group sizes.
The adapter supplies exactly those rows and verifies complete consumption at
the following SpecialEnyInfo boundary. It does not reinterpret 7931 as a number
of monster definitions.

Visible records are 26 bytes: packed flag fields, a truncated resource byte,
16-byte name storage, and eight component bytes. 3109 entries take the original
5001..5003 component parsing branch. Tests compare flags, resource byte, displayed
name and component packing against source fields, plus original scene lookup
5A000 and record lookup 5A0A0 for first/last/invalid ordinals.

The retained initial scene (area 2, scene 15) has no EnyName descriptor. Its
separate NPCList descriptor contains two resource codes. This absence is now
the result of the actual loaded table and original lookup, not an empty fixture.
Other group-query cases cover area 2/scene 0, area 7/scene 13, area 9/scene 0 and
area 16/scene 9. Native progress sizing is compared with the actual combined
NPC/enemy count, including both-present and both-absent cases.

## Limits

This advances world-entry dependencies in offline original-code execution.
There is no new rendered world, client login or live client/server acceptance.
No monster spawn placement, combat attributes, HP/MP, skills, drop table or
drop probability is derived from resource byte/flags/name alone. Those are
separate required evidence contracts, as requested by the owner.

Source validation rejects unsupported area/scene ranges, record widths, numeric
bounds, component strings, NUL, truncation and missing envelope boundaries before
native allocation. Allocation and fgets calls accept only the inspected callers,
sizes and source handle. Temporary catalog file/column-width fields are restored
even when native execution fails. No host files or pagefile settings are modified.

## Verification

From the server root:

```powershell
python -B -c "import sys,unittest; sys.path.insert(0,'tests/research'); result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromNames(['test_current_world_actor','test_current_world_scene'])); sys.exit(not result.wasSuccessful())"
```

Final combined tree: 18/18 passed in 152.698 seconds (actor 11, scene 7).
This includes the new joined group-query range, full nested loader, source-bounds
negative cases and prior 49 C++ packet/actor profiles. No C++ production code or
Lua gameplay code changed in this world-loader follow-up; no live client was run.
