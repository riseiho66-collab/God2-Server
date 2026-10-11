# Current monster/map placement join, 2026-09-27

## Result and boundary

**No original monster spawn or encounter region is qualified.** This audit adds
a complete source graph over the newly readable 142 current MDLs, plus 1,261
complete native destination-coordinate lookups. The graph resolves map-model
links; it does not supply monster identity, spawn conditions, population,
respawn timing, or encounter selection. No runtime, database, client binary,
desktop, or shared parser was changed.

This closes a narrower question than the older filename scans: whether model
type, the four special-point pairs, attachment strings, and placement fields
6/7 expose an identity-bearing monster marker. The inspected consumers use
these fields for animated tiles, navigation, and scene/model entry references.
That is positive evidence about those particular fields, not a claim that the
whole executable lacks an encounter system.

Read first: `native-monster-placement-audit-20260926.md`,
`current-monster-binary-producer-20260920.md`,
`current-mdl-zero-pass-20260927.md`, and the existing doorway/cursor findings in
`current-scene-transfer-20260921.md`. The latter already qualified one CityI1
grocery attachment. This report expands to every current MDL and exercises the
previously unqualified complete destination lookup chain.

## Source identity

| Input | SHA256 |
| --- | --- |
| Current `God2.exe` | `6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98` |
| Mapped native-master-01-stable.bin | `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763` |
| Earlier complete MDL qualification receipt | `79e3c1da56eef4db78b8b72b17865bb39fd9d739d02a4b7586cd14013f61f0f7` |
| Current compressed gamedata.csvZ | `70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731` |
| Fourteen CAN source identities, aggregate | `c01d4a963563a19822f4a9d52de31e630f960d15f879d99ccc04dd49ad7e9dbe` |

The tool pins all 142 MDL compressed/decoded hashes using that pinned receipt,
checks the exact current file set, retains complete byte consumption, and
records every CAN file/record hash. CAN aggregate is SHA256 of compact JSON of
sorted `(lowercase relative path, source SHA256)` pairs. Every inspected code
span must also equal the pinned native image. All addresses below are VAs;
subtract `0x400000` for RVAs.

## Whole-source results

| Observed field / graph | Result |
| --- | --- |
| Fully parsed MDLs / models / placements | 142 / 12,140 / 169,522 |
| TileModel raw numeric type | All 12,140 are decimal 23 (`0x17`) |
| Native low-nibble type / placed body types | `7`, all 169,522 placements |
| Models with at least one active entry pair | 720 |
| Distinct four-pair source values | 250; complete native constructor + four setters agree |
| Distinct active coordinate pairs | 129; complete native transform agrees |
| Pass cells | 128,888 zeros; 324,098 ones |
| Attachments | 1,256 `.mdt`; 363 `.hmd` |
| Additional placements with destination coordinates but no attachment | 7 |
| Saved source graph edges | 1,626 |
| Unique MDL destination-coordinate queries executed | 1,261 |
| Query results | 1,248 unique; 4 multiple matches; 9 absent |
| Verified monster spawns / encounter regions | 0 / 0 |

`0044C420` masks the raw TileModel type with `0xF`; the source's `0x10`
bit is therefore not a separate monster category on this branch. `00441EB0`
reads the body tile's type from `model+8 -> tile+14`. The assertion in
`00441EC0` calls type 7 `TileType_Action`; its call at `00441F08` enters
`0044A0F0`, which creates animation/render state through `0041AFE0` and
`0041E070`. These are animated map tiles; neither the word “Action” nor a ROM
animation index establishes a monster actor.

Placement field 9 is retained: values 0..5 occur
142,785 / 6,361 / 8,132 / 5,019 / 3,298 / 3,927 times. The prior placement
consumer proof stores it at instance+38 and forwards it in the rendering
chain. This audit does not assign a gameplay meaning to those six values.

## Proven coordinate binding, not a monster ID

`0044C980` calls `00441DF0` four times for ModelDat's eight integers.
The latter's own assertion names `Entry_LeftIn <= nEntryType < Entry_End`.
`00441560` initializes all four pairs to `(-1,-1)`; `00441DF0` accepts
`x=-1`, otherwise rejects a duplicate pair. All 250 real source combinations
were executed through these complete original functions; no source combination
hits the duplicate rejection. No synthetic return or game-callee stub is used.

`00448980` reads an attached CString, compares its last four bytes with `.hmd`
at `00587634` and `.mdt` at `005885E0`, then uses placement+1C/+20 when
the first is nonnegative. Those offsets are source fields 6/7. They enter:

1. `00448CF7 -> 0043F1C0(x,y)`.
2. `0043F1C0` divides each coordinate by 21, toward zero, to select a block.
3. `00433AF0` supplies that block's model-list container.
4. `00442990` walks `container+C`, following node+8, and compares
   **both node+14 == x and node+18 == y**. It returns the first exact match.
5. `00448980` reads the returned instance's model pointer at +2C, selects
   the requested entry pair at model+2C/+30+8*entry, calls `00449BB0`, and
   adds the returned instance's +14/+18 anchor.

Thus these two source numbers demonstrably participate in a destination-model
**coordinate** lookup. They are not interpreted as a monster template/instance
key by this consumer. The native transform is
`dx = px - trunc(py/2)`, `dy = px + trunc((py+1)/2)`.

The new oracle runs complete `0043F1C0 -> 00433AF0 -> 00442990` through
return on 1,261 source-derived queries. Block tables are explicitly
preallocated fixtures, so the allocation branch is not exercised. Lists retain
source order for testing; native insertion order is not qualified. Consequently
all duplicate matches are retained, even though the fixture returns the first.
The empty-list control also returns zero. All native boundaries, stack cleanup,
instruction budgets, and outputs are checked with explicit exceptions under
normal and optimized Python.

### Concrete reciprocal example

`Data2/map/island01/Island01.mdlZ`, placement 104, decoded offset 59451:

```
fields = [161,880,40,482,65,0,469,67,1,0]
attachment = Island01.mdt
record SHA = e866460565fdd88d3469e7378110a2afd568577af1bd956919cc2946fc7440b3
```

The CAN source maps this asset to area 2 / scene 0. Query `(469,67)` selects
placement 116, offset 59846, whose fields are
`[167,440,340,469,67,0,482,65,1,0]`; its attachment refers back to the same
asset. Destination record SHA is
`14879023c487d7ad312c051d7dad241dc2feb039dc554715ff446765a7f56360`.
Its four model pairs are `[1,16,-1,-1,0,17,-1,-1]`.
This is a source-bound reciprocal model connection. It does not establish a
world actor ID, a battle trigger, or permission to teleport through it.

## Interaction caller boundary

The raw entry resolver `00448DC0` calls `00448980` at `00448EF8` and
`00448F64`, after matching entry pair 0/1. However the bounded mapped-code
relative E8/E9 scan and full mapped-image literal-pointer scan find no caller
reference to `00448DC0`. That limits its current gameplay reachability claim;
it does not prove it is universally unreachable.

The actual caller chain already documented in the scene-transfer research is
rechecked against current machine bytes:

```
0046707C -> 00434210 -> 00449000
                         mode 0 -> 00449040 (entry pairs 0/1)
                         mode 2 -> 00449250 (entry pairs 2/3)
```

The caller tests the returned boolean, then calls `00483530(0x0E)` at
`0046708F`. `00483530` changes UI+232F36 and forwards to `0041A950`.
This is the previously established cursor selection path. No encounter packet
producer or monster identity lookup is introduced by these inspected branches.
This audit preserves that distinction rather than relabeling an entry cursor
as combat. The full cursor/renderer was not emulated here.

## Unresolved edges retained explicitly

- 363 HMD attachments map to CAN assets; several share 2..12 scene aliases.
  Their full HMD placement lists were not reopened in this bounded MDL audit.
  Asset equality alone must not choose one gameplay scene or spawn identity.
- Two MDT edges were not eligible for an MDL coordinate query: South001
  placement 11343 has literal destination `(-1,-1)`; Tong placement 8 refers
  to `Reborn/Reborn.mdt`, whose corresponding MDL is absent from the 142-source
  set. Neither is silently repaired.
- Four duplicate-coordinate queries are Cave02 `(64,69)`, North001 `(379,47)`,
  North002 `(324,313)`, and South003 `(527,136)`. The JSON retains all source
  matches and exact hashes. Nine absent queries likewise remain present.
- Full `00448980` loading, relative-path handling, caller reachability and
  final network transition selection remain separate work. Native execution
  here starts at its actual subordinate coordinate lookup, not its entry.
- A native spawn claim still requires a consumer connecting one of these
  map/region records to monster template/instance identity and encounter
  conditions. The qualified EnyName / combat-display identity path and this
  map-model graph remain unjoined. Numeric overlap is insufficient.

## Reproduction and artifacts

From God2-Server in PowerShell:

```powershell
$env:PYTHONPATH='artifacts/tooling/crypto-oracle-python'
python -m tools.strike_lab.current_monster_map_placement_join_20260927 --output artifacts/research/monster-map-placement-join-20260927/evidence.json
python -O -m tools.strike_lab.current_monster_map_placement_join_20260927 --output artifacts/research/monster-map-placement-join-20260927/optimized.json
```

Both runs pass. Receipts contain all 1,626 edges, 1,261 native query results,
target record hashes/fields, 250 original entry-set executions, 129 original
point transforms, CAN raw records/aliases, source identities, code spans and
disassembly. No client process is launched. These are offline source/native
consumer qualifications, not current-client gameplay acceptance.
