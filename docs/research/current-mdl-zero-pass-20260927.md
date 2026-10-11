# Current MDL zero-size Pass qualification — 2026-09-27

## Result

Qualified the original `0044C980` Pass-reading loop for zero width/height and
made the corresponding narrow parser correction. Current CityI2 model245
contains a real0×2 grid; the parser now retains its two empty physical rows,
then parses the next model without losing source bytes. That model is **荷花#a**,
with two static placements, not recovered NPC placement authority.

No server runtime, database, original EXE, desktop or collision projection was
changed. `outdoor_mbd.py` has no `parse_mdl`; the actual shared parser is
`current_monster_binary_producer.py::parse_mdl`. Its zero-dimension check and
empty-row handling changed. Following independent native string-copy proof,
the explicit `allow_parent_rom=True` analysis option also accepts the bounded
relative path syntax actually present. Default ROM grammar remains strict.

## Native execution and exact boundary

Tool: `tools/strike_lab/current_mdl_zero_pass_20260927.py`.
Current PE SHA256:
`6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98`.
The JSON records full-function/slice byte hashes. All addresses below are VA.

The oracle executes original instructions continuously from`0044CC84` to
`0044CD56`, the end of the Pass frame loop inside`0044C980`, including complete
`00441880` allocation/dimension update and every reached`00441730` cell setter.
It requires exact end EIP and restored slice ESP and bounds the instruction
count. **This is not a full0044C980 constructor/registration return.**

Only CRT boundaries are adapted: version-string comparison, bounded decimal
`fscanf`, and allocation. Game functions are never replaced. The stream adapter
preserves every byte position and implements whitespace-skipping decimal
conversion; native code decides how many reads and setters occur.

- `0044CCCB` reads width/height with`%d %d` for v1.6.
- `0044CCE0` calls`00441880(frame,width,height)` even for a zero dimension.
- `0044CCEB..0044CCED` skips all rows if height≤0.
- `0044CCF5..0044CCF7` skips cell reads/setters if width≤0, while the row index
  still advances to the positive height.
- Only the positive-inner-loop branch calls`fscanf %d` at`0044CD0B` and
  `00441730` at`0044CD1D`.
- `00441880` stores pointer/width/height/product at
  model+4C/+50/+54/+58+frame×24. If dimensions changed it requests width×height
  bytes. A0×0 request on the constructor's already0×0 state allocates nothing.
- The zero-byte allocator was tested with both null and nonnull adapter
  results. Native zero loops never dereference either result. These are
  explicit allocator boundary variants, not a claim about the live Windows
  allocator's chosen zero-byte pointer.
- `00441730` is reached only for valid positive cells; it writes the low byte
  at `buffer+y*width+x`. Forcing an invalid call would enter its assertion;
  the loader's zero path does not make that call.

Ten native cases pass: dimensions0×2,2×0,0×0,2×2 under both zero-allocation
variants; exact CityI2 source bytes; and a two-frame0×2→2×1 case with cells7/9.
The real CityI2 case consumes exactly the three numeric bytes`0 2`, performs
zero cell reads/setters, and leaves CRLF plus two empty rows before the next
model token246. The next native numeric read skips those whitespace bytes;
the two-frame case proves that behavior without substituting game control flow.

## Exact source and parser change

Source: `Data2/map/island03/cityi2/cityi2.mdlZ`.
Compressed SHA256:
`cb36dbf46adc611620e1bd7c9b0093955c846f33a849ebf88f6ce57f426813cc`.
Decoded SHA256:
`bed2f89dcdb30ed6d7b30c5625423f8bd007ca30eea32ec5406a7ebb7932dd5f`.

Physical lines5011..5015 are `Pass`, `0 2`, empty, empty, `246 0 0`.
The parser now accepts dimensions0..512. For each positive height it still
reads exactly one physical row; zero-width rows must contain only whitespace.
Nonempty zero-width rows reject rather than becoming the next model silently.
For zero height it consumes no cell row. Source offsets, region hashes, cell
budget, integer/count bounds, CRLF requirements and full-byte exhaustion remain.

Six negative cases reject: negative width, negative height, width513,
height513, nonempty zero-width row, and a missing required empty row.
The existing positive MDL structure/complete-region test and malformed source
test both pass. The parser is intentionally stricter than generic whitespace
`fscanf` about the source's physical row grammar.

The previous NPC-coordinate audit's deliberate assertion of parser failure is
updated to require qualified zero-grid/full-byte parsing. Its old report's
zero-grid blocker is historical and superseded by this result; its NPC
authority conclusion remains unchanged.

## Native ROM reference preservation and bounded analysis option

`0044D750` dispatches the ROMFILE section into`0044D520`. Its machine code at
`0044D57F` calls the CRT reader with exact`%s` format; the260-byte stack buffer
then feeds the base-directory/string concatenation sequence. `0044D5A5` calls
`0055AFCA`, whose`0055B00C` call reaches`0055AF26`. These call edges and the
actual format operand are checked against the pinned current image.

The tool executes the complete native`0055AF26 → 0055ABA2 → 0054A8C0` allocation
and string-copy path for **all634 unique ROM tokens** in the142 current MDLs.
Every concatenated result retains every source byte plus its NUL terminator,
including two-parent/subdirectory tokens, case, hyphens, and North001 physical
line7's literal`FM'.ROM` (`464d272e524f4d`). A synthetic directory prefix makes
this a copy test; the MFC pool allocator is adapted. Normal EIP/ESP return,
stored length and exact output are checked. This is not a full44D520 return,
asset-open test or proof that a referenced resource exists.

There is no basename-only grammar in this proven read/concatenate path. The
analysis parser's opt-in grammar therefore now permits0..2 leading`..\`, up
to4 ASCII directory components, and a bounded ASCII ROM basename; the actual
apostrophe filename is retained as data. It rejects absolute, drive, UNC,
interior-parent, excessive-parent/depth and260-byte-or-longer references.
Seven negative path cases and explicit-vs-default separation pass. The default
grammar is unchanged. No reference is normalized, opened or passed to a shell.

## All current Data2 MDL audit

Every `.mdl`/`.mdlZ` under current `Data2/map` was attempted:142 files. Each
source/decoded SHA is retained. Referenced ROM paths are never opened.

| Parser mode | Complete parses | Rejections |
|---|---:|---:|
|Strict default, unchanged|45|97|
|Qualified explicit `allow_parent_rom=True`|142|0|

Before the zero-grid correction the original explicit-parent run parsed65
files. Zero-grid support alone added CityI2, North001/CityIF01,
North001/MazeIF01, North001/MazeIF02 and north005/umg/UMG, reaching70. The native
path-preservation proof then qualified the bounded explicit path option, which
unlocked the other72. The final142-file set contains34 zero grids, including
1×0 and repeated animation frames across15 files. The complete set contains
12,140 model definitions and169,522 static placement records. All142 account
for all source bytes; these totals are not counts of NPCs or world entities.

The intermediate72 failures were the former **ROM reference grammar**, not
unrecognized model bodies. The pre-extension receipt is retained as
`path-before-change.json`. Examples preserved verbatim in the final native
copy receipts include:

- `..\..\Array\Array01\S31D.ROM`
- `..\..\Island02\flowernew03.ROM`
- `..\..\south001\W-G.ROM`

Every source body is now parsed under the explicit analysis option; there is
no remaining MDL grammar rejection in this inventory. This does not authorize
runtime asset loading or NPC spawning. The distinction from strict/default
behavior remains visible in the JSON rather than silently changing callers.

## New placements and NPC boundary

The newly parsed CityI2 zero-grid model245 references TileModel245, CP950
name bytes`b2fcaae12361` = 荷花#a, type23, ROM ordinal25, action10001.
Its ModelDat and placement fields are recorded losslessly in the JSON:

| Placement index | Block | Raw geometry pair | Raw grid pair | Remaining values |
|---|---|---:|---:|---|
|313|6,4|640,480|132,94|0,-1,-1,0,0|
|441|3,5|880,520|71,119|0,-1,-1,0,0|

No attached asset reference is present. A zero-sized Pass grid supplies no
cell values; this does not prove the model is noninteractive, traversable, an
NPC or a mission object. The separate map projection still requires its own
qualification and was not changed here.

Across all142 fully parsed files, ROM names containing`npc` still resolve only
to the existing CityI1`npcad.ROM` six佈告欄 definitions and three placements.
The newly accessible files add no such resource-name chain. This is a
bounded string/reference result; it is not proof that every NPC would have
`npc` in its resource name. No new field was identified as world-instance ID,
NPC template selector, server-facing direction, or quest authority. Complete
qualified NPC spawns remain0.

## Reproduction

```powershell
$env:PYTHONPATH='artifacts/tooling/crypto-oracle-python'
python -m tools.strike_lab.current_mdl_zero_pass_20260927 --output artifacts/research/mdl-zero-pass-20260927/evidence.json
python -O -m tools.strike_lab.current_mdl_zero_pass_20260927 --output artifacts/research/mdl-zero-pass-20260927/optimized.json
```

Both pass10 native Pass cases,634 native string copies,6 zero-grid negatives,
7 path negatives,142 complete parses under explicit mode, and34 zero grids.
The earlier NPC-coordinate tool also passes after its boundary update. No
original game loading/rendering, client process or production write is part
of these tests.
