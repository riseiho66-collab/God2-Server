# Current Monster Binary Producer, 2026-09-20

**No identity-bound original monster/BOSS statistic was recovered.** This lane
qualifies two current RTB representatives through the original binary reader,
and one current MDLZ through complete structural accounting plus bounded native
placement consumers. The qualified uses are animation/render resources and map
models/placements. None supplies a monster ID and a requested numeric field
together. All 18 requested field-authority entries remain null, verified wild
and BOSS records remain zero, and runtime eligibility remains false.

This is a bounded two-family result, not proof that every RTB/MDL, every field,
or the whole current client lacks monster data. No third family is nominated.

## Selection And Read Boundary

Read the current manifest check, map-binary-source, combat-stats, inventory,
numeric-sources, auxiliary-sources, and relevant indoor-resource research first.
The manifest's 73 CSVZ/BIN result, transformation-card proof, EnyName inventory,
skill binary, and Island01 MBD block reader were not rerun. The corrected empty
MBD hook at RVA 38790 was not used as a lead.

RTB was selected because its binary consumer remained unresolved in the prior
inventory and it occurs in current battle resources. Selection started with the
pinned image's `rtbv1.0` reference and reader, not a stat-like filename. After
its render dataflow was established, the second and final family was MDL: its
`.mdl` path construction leads to an actual map-model reader, with the Island01
body previously only inspected at its prefix. HMD's existing indoor proof was
consulted, not repeated. MMB and MDT were not expanded as additional families.

The delivered sidecar opens exactly these four files, checks size/SHA256,
rejects reparse paths, and emits JSON only to stdout:

| Current input | Bytes | SHA256 |
| --- | ---: | --- |
| `God2/Data2/Fight/Spg/spg9001.rtb` | 1558 | `f5846a76370cd14ce1f260153bf377db5e1c24fa1fd4311318037721c309fd15` |
| `God2/Data3/fight/spg/spg9184.rtb` | 2330 | `860681bce02d0c57aaf634ace5332f3a4f28861113d98a95cd69896b6d111af2` |
| `God2/Data2/map/island01/Island01.mdlZ` | 106825 | `cbdc0c946618a1bf4a9b2f221283a17fa58b1f49941b2ea336046851a2519d8d` |
| Pinned mapped image | 3174400 | `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763` |

Image path, relative to God2-Server:
`artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`.
BASE is hexadecimal `400000`; every native address below is a hexadecimal RVA
equal to image file offset. Asset intervals below are decimal and half-open.
The tool pins 23 native spans, 29 direct calls and 12 literal operands.

Only the named current resource bodies and image were examined. The bounded
RTB filename listing was limited to current Fight and Data3; it was not used as
semantic evidence. No retired input, Save/log/account/config body, catalog CSV,
DB, live client, network, desktop UI, or child agent was accessed. Image source
path strings are diagnostic bytes, not paths opened on the host.

The parent-provided identity constraint is retained: no name-only or
source_label-only join. This lane does not recalculate pinned_catalog or join
any resource number to its 7791 visible keys. A future promotion requires actual
native monster identity, or the qualified composite key plus version and
consumer evidence; name/art/label coincidence is insufficient.

## RTB Reader And Producer

Native path preparation at `2E211..2E25E` copies a requested resource path,
changes its final character to `b` at `2E24C`, and calls **`2E259 -> 2F330`**.
The call tries the binary form before the text fallback at `2E292 -> 2E2E0`.
This proves binary selection behavior for that caller. It does not prove that
the high-level current startup selected either representative in a live run.

`2F330` opens `rb` at `2F35D -> 14716F`, reads 14 bytes at `2F37D -> 14785C`,
and compares `rtbv1.0` against RVA `187120`. The native structure is:

| File region | Width/use | Native binding |
| --- | --- | --- |
| `[0,8)` | `rtbv1.0` plus NUL | `2F385..2F3B9` |
| `[8,10)` | signed WORD object count | owner-record `+2`, store `2F3D8` |
| `[10,12)` | signed WORD frames per object | owner-record `+4`, store `2F3CF` |
| `[12,14)` | two raw flag bytes | owner-record `+C/+D`, `2F3C4/2F3C7`; meanings unqualified |
| `[14,14+52*N)` | N records of 52 bytes | `2F422 -> fread(size=34h,count=N)` |
| Remaining bytes | N consecutive arrays, F records of 12 bytes each | `2F48B -> fread(size=Ch,count=F)` |

The selected owner-record address is `manager+A1040h+slot*110h`. The slot is a
resource-cache slot, not a monster identifier. Original `2D930 -> 28740` provides
the allocations. For each object, file DWORD `+30h` is overwritten with its new
frame-buffer pointer at `2F47E`; the serialized pointer value is never an ID or
a recovered stat. All other first 48 object bytes are copied unchanged.

The symmetric native writer **`2F1F0`** is statically pinned only. Its fwrite
calls `2F2B3`, `2F2C4`, and `2F2E5` write respectively the 14-byte header,
52-byte object records, and 12-byte frame records. It is **never executed** and
no host or virtual output file is created. `2F1B1 -> 2F1F0` appears in the text
fallback producer; no external RTG file was read.

Exact source accounting:

| Source | Object table | Frame arrays | End |
| --- | --- | --- | ---: |
| Data2 spg9001 | `[14,118)`, 2 objects | `[118,838)`, `[838,1558)`, 60 frames each | 1558 |
| Data3 spg9184 | `[14,170)`, 3 objects | `[170,890)`, `[890,1610)`, `[1610,2330)` | 2330 |

No gaps, overlaps or trailing bytes remain in either observed profile. Full
JSON retains per-object raw bytes/hashes, exact source offsets, serialized
pointers, and frame-array hashes. All five frame arrays have SHA256
`d9f1513643ee22af9d6f7373c68c08eef5e43bb12ea62314c78aaddfece9e599`.
Each representative frame selected for execution is
`000000000000803f02000000`, not an HP/MP/stat vector.

Concrete downstream dataflow:

- `2F7EA..2F829`: object WORD+0 goes through **`2F81D -> 1AE20`**, a resource
  lookup; the result overwrites object WORD+2. `2FCE9 -> 1AFE0` creates an action
  resource. No EnyName or monster-attribute join is established here.
- `30839..30864`: object pointer comes from the reader's table; `3084D` divides
  playback frame by signed owner-record WORD+4. Remainder times 12 selects the
  frame through object DWORD+30h. This is a frame index, not monster level.
- Frame signed WORD+0/+2 are read at `309A1/3099D`; **`309D8 -> 1DBC0`** receives
  those movement deltas and an action-object pointer. `1DBD6/1DBDA` add them to
  action WORD+12h/+14h; its primary display call is `1DBEE -> 26F40`.
- Frame DWORD+4 flows at **`309EC -> 1DF60 -> 26FE0`**, where the original x87
  load/store writes a display record's `+12E8h+handle*200` float.
- The same in-memory frame field is produced by the text fallback's
  `Transparency:` branch, literal `186F98`, `2ED93..2EE40`: parsed float at +4
  is clamped/inverted (`1-transparency` within the bounded range). This static
  producer supports render opacity, not a combat percentage. The RTB reader
  copies that already-stored float without applying this conversion again.
- Frame byte+8 is tested against 2 at `30887`, selecting show/move/scalar versus
  hide paths. The text fallback's `visible_anim:` branch uses that same field
  at `2EE45..2EEC3`. Bytes+9..+11 remain unqualified, not silently called padding.

This establishes render consumers for the qualified fields. Object metadata
not enumerated above and the header flags retain unknown semantics. The narrow
exclusion is that these qualified render fields are not original wild stats;
it is not an exhaustive all-consumer or family-wide exclusion.

## MDL Structure And Consumers

`3CEF1` selects `.mdl`, then **`3CF2E -> 3D420`** opens its resource and validates
MDL/version. **`3D587 -> 4D750`** parses the model catalog; **`3D5C6 -> 3EE20`**
reads the following placements. Both are real current image consumers.

The chosen MDLZ is compressed non-CSV input. Its decoded payload is **text**,
not a hidden fixed-width binary stat table. Existing bounded decompression
produces 389290 bytes, SHA256
`88349e73e0baa95ca773dc54641a23d1baa19dbef25b3313866980ccbde6fce2`.
This format distinction is explicit; numeric tokens are not labelled stats.

| Decoded interval | Structure | Native consumer |
| --- | --- | --- |
| `[0,10)` | `MDL v1.6` with CRLF | `3D4AE..3D579` |
| `[10,350)` | ROMFILE 27, then 27 resource paths | `4D7DA -> 4D520` |
| `[350,8692)` | TileModel 266; name token plus five integers | `4D8E5 -> 4C420`, scanf format at `188A58` |
| `[8692,56006)` | ModelDat 266 | `4D95E -> 4C980` |
| `[56006,389290)` | Model marker; 601 block groups, 9875 placements | `3EE20` |

Every source byte belongs to exactly one region. Full JSON retains hashes for
all regions and offsets/hashes for all placements; row hashes include CRLF.
Referenced ROM/MDT/HMD paths are preserved as data and never followed.

Each observed ModelDat consists of three layer triples, a frame-count plus two
integers per frame, eight further integers, `Pass`, then one width/height and
byte grid per frame. The file contains 10292 pass cells. Native `4CA09` reads
each layer triple; `4CA1F -> 4C050` looks up the TileModel. Frame-offset stores
are `4CB7B/4CB7E`; the eight further integers reach `4CC1B -> 41DF0`; pass-grid
dimensions reach `4CCE0 -> 41880`, and cells reach `4CD1D -> 41730`. The parser
checks references and bounds but does not invent gameplay meanings for the
eight extra integers. The existing indoor research is prior evidence for this
shared grid machinery, not a new full loader execution in this lane.

Each placement group begins with three integers `(block_x,block_y,count)`.
`3EE68` and `3F151` parse group headers. For v1.6 the row has six integers,
three further integers, an optional string when the ninth integer is 1, then
one final integer. Thus the actual profile has 10 or 11 tokens, not an
unconditionally fixed ten-column row. There are **81 attached strings**.
719 placements have a nonzero last integer; it is not assumed to be an element,
level, capture flag or monster category.

Zero-based placement numeric-column binding:

| Column | Native use |
| --- | --- |
| 0 | **`3EF35 -> 4C6F0`** indexes the ModelDat pointer array; diagnostic at `188A6C` names `nModelDatIdx`/`m_nTotalModelDat` |
| 1..4 | Four position arguments at `3EF3A..3EF6A`; `38986 -> 41FC0` stores instance `+C,+10,+14,+18` |
| 5 | `3EF7A` stores instance `+30`; frame-index consumer `4215A..4216D` selects model frame offsets with 36-byte stride |
| 6,7 | `3EFF1/3EFFD` store instance `+1C/+20`; full destination/transition semantics unqualified here |
| 8 | `3EFFB/3F000` tests optional attached-string branch; `3F027` reads string, `3F041 -> 37540` assigns instance `+34` |
| 9 | `3F082` stores instance `+38`; `42223/42242 -> 42246 -> 41EC0 -> 4A0F0` passes it into action-tile creation |

`41EC0` checks `pTile->GetTileType()==TileType_Action`, literal `188344`.
This qualifies a render use of column9, without assigning its complete meaning
or saying every placement takes this particular consumer. Instance `+2C` is the
ModelDat pointer, not a monster record. Neither tile, model nor action IDs may
be joined to monster numeric authority on the basis of equal integers.

## Execution Limits And Tests

The sidecar reuses only `current_battle_entry.NativeRun` and `decode_csvz`.
There is no heavyweight resource preload or catalog initialization.

RTB `2F330..2F50D` executes through return with the original `2D930/28740` pool
allocators using an explicitly prepared private slab. Only CRT fopen/fread/
fclose are adapted. The adapters enforce mode, handle, read sizes/counts and
source boundaries; every source byte is copied into the actual native-requested
destination. Return slot0, stack cleanup, allocation consumption, record bytes,
pointer replacement, all frame bytes and buffer guards are checked. The two
loads execute 713 and 980 instructions, respectively, and close their virtual
handles. The cache slot0, path, handle, manager and pool addresses are fixtures.

Frame tests reuse those native-loaded records. Four playback positions per
object (0,1,59,61) exercise original modulo selection, for 20 source-backed
probes. Movement stops **before** 1DBC0; the independent scalar island executes
original 1DF60/26FE0 through its store. No successful movement return is supplied.
The zero movement in the chosen source frames is supplemented by an explicitly
synthetic signed-WORD/float counterfactual; it proves mapping only and is never
included as source data or monster authority.

MDL parsing accounts for the whole source outside the VM. Three representative
placement rows at decoded offsets **56021, 222722 and 389257** execute the
original row argument flow with a bounded CRT fscanf adapter, two version
comparisons, and original 4C6F0 lookup, stopping before 38920. Model pointers
are deliberately marked fixtures: native model/ROM loading is not executed.
Each row takes 69 instructions. Independent 41FC0 initializer and additional
store islands execute 11 and 14 instructions with source-derived locals.
Neither the placement constructor/container insertion nor attached-string
assignment is simulated as a successful native call. The latter is static
evidence only. Additional tests use actual attached/nonzero-column9 rows.

All original code pages remain read/execute-only. Private state is read/write.
Instruction ranges/stops are allowlisted and each execution segment is bounded
to at most 20000 instructions; no unknown callee runs. The four accepted inputs
total 3285113 raw bytes, each/decoded input bounded to 4 MiB. Parsers additionally
bound counts, rows, references, frames and aggregate pass cells. Rejections are
analysis-profile checks, not a security claim about the legacy native loaders.

```powershell
python -B tests/research/test_current_monster_binary_producer.py -v
python -B -m tools.strike_lab.current_monster_binary_producer --summary
# Without --summary, full structure/provenance JSON is stdout-only.
```

**10/10 focused tests pass** (0.716 seconds on the first completed run).
They cover the exact read-only four-input boundary, pins/calls/literals, complete
RTB reads and pointer replacement, original frame/render flow, a signed numeric
counterfactual, malformed structures, complete MDL accounting and references,
conditional attachments, native ModelDat lookup/stores, and null authority in
both full and summary reports. No unrelated suites or full catalog regression
were run. No child/background/test process remains; all command invocations
completed, and no original client was launched.

## Deliverables And Unknowns

Only these lane-owned files were created:

- `docs/research/current-monster-binary-producer-20260920.md`
- `tools/strike_lab/current_monster_binary_producer.py`
- `tests/research/test_current_monster_binary_producer.py`

No shared research, bootstrap, status, build configuration, production database,
runtime code or desktop artifact changed. No standalone report file was written.

Unresolved: every requested monster level/HP/MP/four-attribute/attack/defense/
element/EXP/capture value; monster ownership of these resource files; other
RTB object-field/header meanings and frame bytes+9..+11; complete MDL extra-field
semantics; every other file/consumer outside this explicit scope. There is no
qualified numeric producer RVA for wild monsters. The exact native edges above
are resource producers/consumers, not proposed substitutes for that missing
authority. Further work needs a new justified source/identity producer, not
another pass over these counts or a filename/name/label join.
