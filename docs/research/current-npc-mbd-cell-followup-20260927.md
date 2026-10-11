# NPC position lead: CityI2 MBD cell semantics

2026-09-27. This is a bounded current-client source follow-up, not a recovered
NPC placement table. No client, configuration, account or production DB changes.

## New evidence

The preceding inventory left CityI2 MBD cell bytes+2..+7 partly unidentified.
The reconstructed functions now give a concrete chain:

- `0043B360` removes a tile from a resource group and returns that group's
  ordinal through its output pointer. `0043B7DB..0043B83B` then decrements later
  same-type cell ordinals. Native execution verifies signed comparisons,
  type0/1/4, unrelated type2, disabled adjustment and mismatched types.
- `004381D0` returns signed cell WORD+4. Native `00438E50` and `00439030`
  forward it to `00449FD0` for tile drawing.
- Previously unexported `00438210..00438266` sets WORD+4, bounded by the tile
  manager's `+910` count. This routine is absent from the current
  `decompiled/functions.tsv`; a search of exported C alone would miss it.
  Its negative input behavior is recorded as native behavior, not promoted
  into a server validation policy.
- `0043FF50` writes the original `MAP v1.1` text format. Full native returns
  name the six source fields below. Only CRT `fprintf` is adapted to an
  in-memory receipt; original client instructions remain unmodified.

| Source cell field | Native writer name | Width |
|---|---|---|
| WORD+0 | TileIdx | signed16 |
| WORD+2 | LinkIdx | signed16 |
| WORD+4 | TileNum | signed16 |
| BYTE+6 low5 | PalNum | 5 bits |
| BYTE+7 low4 | SpriteNum | 4 bits |
| BYTE+7 bits4..5 | Pass | 2 bits |

The named `MAP v1.1` Pass field must not be conflated with the previously
qualified `00447440` base collision projection `(cell[7]>>6)&1`. This report
does not assign the remaining bits new gameplay meanings.

## Reproducible native checks

Tool: `tools/strike_lab/current_npc_mbd_cell_followup_20260927.py`.
Receipts: `artifacts/research/npc-mbd-cell-followup-20260927/evidence.json`
and `evidence-optimized.json`; normal/optimized receipts are byte-identical.

- 16 actual CityI2 source cells, with exact file offsets and raw bytes, pass
  the original getter and complete named writer (20 original output calls each).
- Four out-of-bounds getter cases, nine setter cases and 22 conditional group
  adjustment cases pass. Synthetic registers/objects are explicitly test
  scaffolding, not world NPC positions.
- Tested spans match both the pinned image
  `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`
  and current God2.exe
  `6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98`.
- Source CityI2 MBD is pinned to
  `eba7aa7ae1ddc0381c7fe30d452fa251345aa9310386948b5eaf080c37d78e59`.

## Placement boundary

These fields establish tile/resource indices, palette and sprite data; they
do not bind an NPC world instance, catalog selector, scene and facing.
No complete interactive NPC placement is qualified by this cell lead.
This conclusion is restricted to the tested fields and traced consumers,
not proof that every current-client byte has been interpreted.

Continue along NPC pool writers, other resource/configuration loaders and
the CityI2 MDL parser boundary. Do not reuse cell ordinals or SpriteNum as
NPC identities/facing, or convert any arbitrary matching WORD into a spawn.
