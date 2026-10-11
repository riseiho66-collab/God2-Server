# Current monster groups and placement join — 2026-09-27

## Result

**No complete native monster spawn/encounter record was recovered.** This pass qualifies the boundary between the local display namespace and the identity/position supplied by a world actor packet. It does not turn a display ordinal into a species ID, weighted spawn entry or location.

The 96 final EnyName groups divide into:

| Namespace | Groups | Visible records |
|---|---:|---:|
| Keys also present in current Map_City_Coordniate | 92 | 1,625 |
| Area 0, scene 0/2/3/13; no map catalog rows | 4 | 6,166 |
| Total | 96 | 7,791 |

Area-0 counts are respectively 2,115 / 816 / 2,070 / 1,165. The latter three are also used by the existing pet/alternate appearance lookup contract. They are not four newly discovered world regions. Matching the other 92 keys is a display-resource namespace join, not authorization to spawn every entry there.

## Source and current build

Read prior `native-monster-placement-audit-20260926.md`, `current-world-enemy-groups-20260919.md`, and current SpecialEnyInfo qualification. The older groups report contains historical references to retired archives; this pass did not read or use those archives. The prior asset/header scan was not repeated.

* Current God2.exe SHA256: `6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98`.
* Current `Data2/Patch/Comm/gamedata.csvZ`: `70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731`.
* Decoded source: `75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815`.
* Mapped native reference: `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.

All executed spans are checked against the current PE and pinned mapped reference. The new artifact also pins static world actor call/coordinate ranges. Addresses below are VA unless identified as RVA.

## Original source fields: no unconsumed placement columns

Source line 21695 is `EnyName,7931`; line 21696 is `EnyNameTotal,7815`. `0045A1A0` uses the latter total, then the nested area/group counts. The source contains 16 area declarations and 97 group occurrences. Repeated area 7 replaces its earlier descriptor pointer; 24 old records become invisible, leaving 96 groups / 7,791 lookup rows. The existing full original loader qualification established this behavior; the new tool does not claim to rerun that large loader.

All 7,815 rows have either six columns (4,706 rows) or ten (3,109 rows):

| Source column | Original 0045A1A0 use |
|---|---|
| 0 | Not read as the lookup key. All current labels happen to equal their one-based row ordinal. |
| 1 | Copy up to 15 name bytes to record+2; terminate record+17. |
| 2 | Low four source bits become record byte0 high nibble. No level/weight meaning established. |
| 3 | Source bit0 becomes record byte0 bit0. |
| 4 | Truncate to record byte1; full integer also selects the 5001..5003 component branch. |
| 5 | Low three bits become record byte0 bits1..3. |
| 6..9 | Only when column4 is 5001..5003 and column3 bit0 is set: parse `h/f/b/w` component strings into record+22/+20/+18/+24 pairs. |

There are no remaining numeric x/y, rectangle, probability, count, facing, timer or encounter-condition columns in this current six/ten-column envelope. Packed flags retain their verified bit behavior without inventing gameplay labels. A descriptor's row count is a table count; no random-weight operation occurs in these loaders/lookups.

`0045A000(byte area, WORD scene)` returns a three-DWORD descriptor `{scene,count,records_pointer}`. `0045A0A0(byte area, WORD scene, WORD ordinal)` checks area<17, nonzero ordinal, matching scene and ordinal<=count, then returns `records_pointer + 26*(ordinal-1)`. There is no map-cell argument, RNG, world x/y or spawn condition in either lookup.

## Exact map join and its limits

The artifact preserves all 96 groups, each first raw source record/line/index, and the unchanged matched Map_City_Coordniate row (including raw fields and source hash). It hashes only the corresponding existing MDL/MBD filename variants, without repeating the whole map audit or claiming to requalify model parsing.

Six matched catalog keys do not have a corresponding MDL/MBD file at the **literal catalog stem** tested here: `(5,40)`, `(8,2)`, `(8,13)`, `(8,14)`, `(8,15)`, `(15,30)`; all have catalog kind3. The artifact retains their exact MDT paths. Their fallback/alias resource resolution is not qualified in this lane, so the 92 catalog matches must not be described as 92 completed physical map joins. The other 86 groups have corresponding assets; 196 distinct physical MDL/MBD variants are hashed, including plain/Z variants.

Neither map catalog coordinates nor model-cell positions are joined to an EnyName row as a spawn. Existing 142-map decoding coverage does not provide the missing monster-instance relationship by itself.

## New native S2C71 identity-prefix execution

Original world dispatcher case71 begins at `0046A3B4`. Before `0046A3D4 -> 0045A0A0`:

* `WORD logical_packet+5 & 0x3F` supplies area.
* `WORD logical_packet+5 >> 6` supplies scene.
* `WORD logical_packet+19 >> 3` supplies the one-based ordinal.

The new oracle executes `0046A3B4..0046A3D9`, including the **full original lookup return**. It does not replace the lookup with a Python result. Source-backed descriptors are explicitly staged; the 26-byte payload arena remains unmapped, ensuring this prefix does not consume invented record contents.

**483 cases pass:** five per group (first, last, first with unrelated packet bytes FF, ordinal0, count+1), plus three absent/invalid keys. Every expected pointer is computed independently from the preserved source occurrence. Stack balance, native stop address and absence of packet mutation are required with non-optimizable checks. Diagnostic packets are not original-server captures.

This shows precisely what the client is given. The appearance area/scene in the packet need not be the player's current world scene; this prefix does not compare them. It cannot prove the original server selected a group because the player entered the matching catalog map.

## Actor position comes from a different packet field

Static current native chain: case71 increments the packet pointer to body+0 at `0046A3BF`; `0046A5B3` passes that body pointer to `004CB120` (`CPMonster::Appear` source assertion strings). The actor constructor reads:

* Instance key: low WORD of body DWORD+0.
* Direction: body DWORD+0 >>29.
* x: `(body DWORD+8 >>2) & 0x7FFF`.
* y: `body DWORD+8 >>17`.

Thus direction and world coordinates are supplied separately by the incoming actor body, not recovered from EnyName's six source columns. Body+8 is logical packet+9. The new oracle stops before actor allocation/resource construction, so this section is a static consumer trace, not full world71 acceptance.

Concrete remaining native edge: an original server source/capture must supply the selection and these actor-body fields. Continuing `004CB120` or its component-actor sibling `004CB720` can qualify installation behavior, but will not manufacture the missing input coordinates, weights or timing.

## SpecialEnyInfo is an override, not an encounter-region table

The current section is exactly:

```text
SpecialEnyInfo,1
1,IGS_SPECIAL,0,0,149,1
```

Source row 29626; section decoded offsets `[2781781,2781824)`, hash `c3d480f60ba45441c3dfc40fe2c61e420a9e79f32570a5b640f08b82652cc4ad`.

This pass re-executes full original `0045A560(1)` and `0045A120(base,1)` using the existing bounded CRT adapter. Allocation poison A5 produces exactly `02 95 00 00 00 00` followed by **20 untouched A5 bytes**. The lookup inherits the synthetic base name/high nibble into shared scratch; the last eight component bytes remain untouched A5. Those bytes cannot become zero-valued native coordinates or rules merely because another allocator normally clears memory. The tool preserves loader/lookup traces and labels the base record synthetic.

Existing `current-monster-variant-identity-20260920.md` separately proves the S2C1C normal versus alternate routing and selector bounds. No SpecialEnyInfo field supplies a map rectangle, probability or spawn timer.

## Reproduction and delivery

Tool: `tools/strike_lab/current_monster_group_placement_join_20260927.py`.

```powershell
python -m tools.strike_lab.current_monster_group_placement_join_20260927 --output artifacts/research/monster-group-placement-join-20260927/evidence.json
python -O -m tools.strike_lab.current_monster_group_placement_join_20260927 --output artifacts/research/monster-group-placement-join-20260927/evidence-optimized.json
```

Both PASS with byte-identical JSON SHA256:
`65fa33b6a1a632ac0ce586d66d165ade80b9cd35e84f998538fd6966c92ac8ac`.

No runtime, formal DB, client binary, UI or desktop changes. Runtime-eligible new spawn rows: **0**. The source identity/raw fields and packet lookup contracts are usable for validation; original monster-to-world assignments, exact positions/regions, direction and trigger/timing remain separate missing inputs.
