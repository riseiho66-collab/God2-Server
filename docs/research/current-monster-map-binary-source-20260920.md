# Current Monster Map Binary Source, 2026-09-20

**No original wild-monster or BOSS numeric value was qualified.** This bounded
delivery newly qualifies the structure and native block-reader binding of one
current MBD/MBDZ pair. Its first cell WORD is used as a tile index. WORD+2 has
a conditional signed compare/decrement use, with field meaning still unknown;
no tile numbers become monster values. All 21
requested field-authority entries remain null, with zero verified monster/BOSS
records and runtime eligibility false.

## Selection And Prior Boundary

Read the existing current map-atlas, scene-resolution, indoor-resource and
monster-numeric-source proofs. The atlas records MDL/MBD/MMB presence only;
scene resolution covers CAN selection and the indoor HMD path. Neither covers
this outdoor MBD body or its reader. No prior identity, packet-scalar, category,
CSV inventory, or full resource-loader proof was rerun.

A bounded initial inspection used only Island01's four sibling candidates:

| Candidate | Actual decoded prefix | Selection evidence |
| --- | --- | --- |
| `island01.mbd`, `Island01.mbdZ` | `MBD v1.2`, DWORDs 35,37 | Binary index/payload candidate with native `.mbd` and MBD reader references |
| `Island01.mdlZ` | `MDL v1.6`, `ROMFILE 27` | ROM-list header; body not semantically qualified here |
| `Island01.mmbZ` | `BM`, 40-byte DIB header, 735x777, 8 bits/pixel | Bitmap header; no pixel/palette values promoted |

The selected source path is **MBD v1.2**. Only its plain/Z pair and the pinned
image are opened by the delivered sidecar. The initial MDL/MMB inspection is
selection evidence, not a family-wide exclusion of data. No other map payloads
or retired archives were examined.

## Pinned Sources

Current sibling client paths, relative to `God2`:

| Source | Bytes | SHA-256 |
| --- | ---: | --- |
| `Data2/map/island01/island01.mbd` | 3035748 | `b574654e5859e048ea0047c0de36b70addc5e90f2349b9796016ea6792f75f80` |
| `Data2/map/island01/Island01.mbdZ` | 735668 | `0edf2048eaf0964caa2c373d66b4c1e6129ebeca265c4a63326436c13e6e0a1f` |

The existing bounded `omega_assets.decode_csvz` expands MBDZ to exactly the
plain MBD bytes, with the plain hash above. Native decompression and native
plain-versus-Z selection were not executed. The two present inputs agree, so
neither alternative introduces a different payload in this representative.

Image: `artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`,
3174400 bytes, SHA-256
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
BASE is `400000`; all native addresses below are hexadecimal RVAs equal to
image file offsets. MBD offsets address decoded bytes; intervals are half-open.
The tool pins ten native spans by separate SHA-256 values in `SPANS`, and
reports their boundaries, hashes, literal operands and direct-call bytes.

## Structure And Native Use

| MBD byte region | Observed structure | Native binding |
| --- | --- | --- |
| `[0,10h)` | Eight-byte magic, u32 width35, u32 height37 | `408E0`; header fread call `40ACF`, 16 bytes into owner |
| `[10h,144Ch)` | 1295 little-endian u32 file offsets | `40B75..40BC9`: width*height, four bytes each; fread `40BA8` |
| `[144Ch,2E5264h)` | 859 blocks of 3528 bytes | `40790`: offset[y*width+x], seek, read grid-width*grid-height*8 |

There are 436 zero offsets. All nonzero offsets, in table order, exactly equal
`144Ch + k*DC8h` for k=0..858. The payload has 3030552 bytes; header, table and
blocks account for every byte with no overlap, gap, or trailing data. This is
structural coverage, not full semantic coverage. The parser deliberately accepts
only this packed v1.2 profile; rejection does not prove other MBD layouts invalid.

Concrete native chain:

- `3CF50` references `.mbd` at `187D1C`; `3CF9A -> 408E0` opens its reader.
- `408E0` validates the parsed MBD token against literal `18816C`. Its header
  and offset reads establish the index layout. This routine is statically
  inspected only; file open, timestamp handling and conversion are not executed.
- `3B712..3B726` sets both grid dimensions to 21 and allocates 441 elements
  of eight bytes. `3B7B1 -> 40790` reads one indexed block.
- `3B7C7` sign-extends cell WORD+0; `3B7CE -> 3B1B0` uses it to look up
  `owner+110h+index*4`, bounded by `owner+910h`. The lookup's diagnostic
  `nTileIdx<m_nTotalTile` at `187BE4`, referenced at `3B1CB`, identifies the
  namespace as tiles. It is not a monster identity lookup.
- `3D03F..3D062` dispatches the older v1.0/v1.1 conversion paths. The current
  header is v1.2; those conversion loops were not executed or treated as current
  cell semantics. Bytes+2..+7 have no qualified gameplay field meanings.
- The immediate block-reader caller has a real WORD+2 use in pinned span
  `[3B7DB,3B83B)`, SHA-256
  `27db4070519a6fd751c3b2ba7ef057e7ac5121e559ada0f4e57342fdaee79e99`.
  After `3B7B1 -> 40790`, `[esp+34h]` is the block buffer and `[esp+38h]`
  its width. `3B800..3B80D` and `3B81C..3B829` calculate the cell pointer.
  `3B810`/`3B82C` sign-extend WORD+2; `3B814`/`3B830` compare it with
  `[esp+10h]`. If the earlier caller guards permit this branch and the value
  is greater, `3B836` decrements it and `3B837` writes the WORD back. This is
  static operand evidence only, with no asserted field meaning or wild ownership.

Index-table SHA-256:
`da6107876d89fafbdcb2042afadef40f29879f4c74914fdeef4d7a469cc36d20`.
Pinned representative block results:

| Index (x,y) | MBD interval | Block SHA-256 |
| --- | --- | --- |
| 34 (34,0) | `[144Ch,2214h)` | `0462367625a2eedf9ad6eba746275657c085d38340969a4718c0d3cefa6e2e89` |
| 87 (17,2) | `[2FDCh,3DA4h)` | `44dfdbfdafa5c7da6886d446a7e2a2e34e991ff0bae29b8b90b5197b7a9b3171` |
| 1294 (34,36) | `[2E449Ch,2E5264h)` | `3a4d30f1ae6909a1ef1fa3f3073fc6894493096e6f7e1a887c39124f3da8b63e` |

Block87 begins `21 00 0B 00 32 00 00 80`. Only its first signed WORD is
qualified as tile index33. The remaining bytes are not HP, level, drop rate,
elemental values, or any other asserted monster field.

## Bounded Execution

Reuse `current_battle_entry.NativeRun` solely as the sparse instruction harness;
no battle/packet path executes. Original `40790..40829` runs with source-derived
header/index bytes, synthetic memory addresses and a virtual file handle.
Only CRT fseek (`1477A3`) and fread (`14785C`) returns are adapted: argument
checks enforce the original offset, SEEK_SET, 3528-byte size and count1 before
copying those exact source bytes into the original requested buffer.

Each present sample executes 53 instructions and returns1. Index0 executes34
instructions and returns0 without I/O; that means absent block, not a zero-valued
monster. Tests verify exact payload hashes, buffer guards and stack cleanup.
The image is read/execute-only; private buffers are read/write. Each execution
segment has a 200-instruction limit and rejects unexpected native control flow.
No native resource, tile, model, actor, display or owner preload runs.

The read boundary allows only the two fixed assets and image, rejects reparse
paths, validates sizes/hashes and bounds each input/expansion to4MiB. JSON goes
to stdout. There is no filesystem output, DB write, UI, runtime, network or
subagent work. No shared bootstrap, test aggregate, status or CMake file changed.

## Corrected Boundary And Unresolved Authority

**`37F4C -> 38790` is disqualified as a source-recovery target.** The earlier
recommendation was based on the callsite without verifying the callee body and
is withdrawn. The pinned image has a single `C3 RET` at `38790`, followed by
15 NOPs in `[38791,387A0)`. It has no cell operands or downstream calls and must
not be recommended for further reverse tracing. Span `[38790,387A0)` SHA-256:
`499f1f307c1cb989f968a6b7fcaec591e1828877223d0b0e7e8e8b76cde8c9ca`.
Both full and summary JSON retain this explicit disqualification.

The bounded correction inspects only this empty hook and the immediate caller
of the already-qualified block reader. The real WORD+2 operations above replace
the unsupported consumer claim. Their field meaning, the compared value's
provenance and remaining bytes+4..+7 are still unqualified. No further consumer
callee is nominated: `next_unexamined.call_rva` and `callee_rva` are null.

The unresolved byte region remains pinned block87 `[2FDCh,3DA4h)`, cell bytes
+2..+7 beginning **`[2FDEh,2FE4h)`**; its first WORD+2 is raw value11, without
an assigned gameplay meaning. No monster/BOSS numeric owner has been established.
This representative does not justify saying that other MBDs, MDLs, other
binaries, or the whole current client lack monster data.

## Verification

```powershell
python -B tests/research/test_current_monster_map_binary_source.py -v
python -B -m tools.strike_lab.current_monster_map_binary_source --summary
```

All nine focused tests pass. Coverage includes exact allowed reads, source-pair
equivalence, full byte accounting, native block reads and absent-block behavior,
static operand/call bindings, malformed offsets/sizes, changed-pin rejection,
the real WORD+2 operands, the empty-hook pin/disqualification in full and summary
JSON, null monster authority, and an unresolved next consumer. Synthetic
corruptions test rejection only and never supply gameplay values.

Changed paths are only this document,
`tools/strike_lab/current_monster_map_binary_source.py`, and
`tests/research/test_current_monster_map_binary_source.py`.
