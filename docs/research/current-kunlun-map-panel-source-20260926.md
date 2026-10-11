# Current Kunlun map panel and pinned map item sources

Date: 2026-09-26. Scope: current client consumer/input edges and original display
sources for SPI 5569/5576. This report does not establish the original server's
C2S25 response policy, item ownership, consumption, grants or quest rules.
The owning server integration selects its own explicitly documented presentation
policy. No game process, desktop, live database or shared build was changed by
this investigation.

## Binary qualification

- Current `../God2/God2.exe` SHA256:
  `6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98`.
- Pinned mapped image:
  `artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`,
  SHA256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
- These current PE RVA ranges equal the mapped image bytes (end exclusive):

| RVA range | Range SHA256 |
|---|---|
| C3750..C3A70 | cc8fd77c6e07df277f533bb05b466fe68061bca07c5117cb89fa23d40130ac6d |
| C3F60..C4245 | 120947f010219864a66447526b50a4c15c0824c4ee8d80e303d6b4e1f3f6d90e |
| 105230..105390 | 90bf3ab5fe64a7e62d4df3d311ea7a4c8b75adeb81e573db1a331a14abf40563 |
| 18BAA8..18BC14 | 8053c25ea781372a948e2b356c88880446fb070f382dc75856c235ea08887c80 |
| 820A0..82300 | 86858297eafad4c616fd194feda929f98c39da7fc9551c046bd8273d2371d377 |

All code addresses below are RVA unless prefixed VA; image base is 0x400000.
Decompiler text is navigation evidence; conclusions were checked against the
mapped native instructions. Prior scope: `current-town-map-use-20260921.md` and
`native-kunlun-birthplace-evidence-20260926.md`.

## S2C3F opens an already selected scene panel

Logical record is exactly `[3F, byte1, byte2]`. Dispatcher 6B034 passes byte1 to
C3890. Byte2 is opaque to this consumer. There is no item ID or map ID here.

- Scene pointer is `DWORD(UI+8AA4C)`. It must be valid: a null pointer skips the
  first check but is dereferenced later by the original function.
- `scene+F4 & 3 == 3` emits message 0x32F.
- `DWORD(UI+232F58) != 0` or `WORD(scene+F0) == 0x1741` emits 0x369.
- Otherwise zero byte1 emits 0x330; nonzero byte1 calls C3840 and 1052E0 to
  open the existing large map panel `int16(UI+232DA8)`.
- Optional panel `int16(UI+232E56) >= 0` is hidden through 105230.

This consumer neither changes inventory nor selects map graphics. Therefore
adjacency of opcodes 25/3F cannot establish an original request/reply rule.

## Kunlun scene selects type47/action8

The static map metadata table starts at RVA18AC70, with 143 records of stride
0x34. A runtime scene's `DWORD(scene+1A0)` points to its metadata.

| Entry | Metadata RVA | WORD +20 / +22 / +24 | Source identity |
|---|---|---|---|
| Island03, area4/scene0 | 18BAA8 | 47 / 1 / 0 | 參天林 |
| CityI2, area4/scene3 | 18BBE0 | 47 / 7 / 8 | 崑崙仙界 |

Current gamedata CityI2 row is line21097, area4/kind0/scene3, path
`Island03\CityI2\Cityi2.mdt`, dimensions252x252. C3080 initially uses area-base
metadata for the panel. C3F60 looks up the current scene through 459D80, reads
mini-map type/action +20/+22, then looks up area/scene0. When large-action WORD
+24 differs, it selects the current scene metadata. At C4203 the path calls
105110(panel,47,8), then 1051B0(panel,0,0). Kunlun mini-map is action7 and the
large map is action8.

Original `Data3/Flow/Island03Map.ROMZ`:

- Compressed SHA256 `0dccbe5ac417213479a57b1e021a84dd02599742b7ef70628ee6a29592b28053`.
- Decoded SHA256 `5ac9b3f65cc6acb47f0efd3268ccb798837d9709c29b1f4096d511bf74c6966d`.
- Existing Omega decoder and `parse_rom(..., name_encoding='cp950')` recover
  10 actions. Action7: 崑崙仙界, metadata `(10007,0,400,300,1,1)`.
  Action8: 崑崙仙界大地圖, metadata `(10008,0,400,300,1,1)`.
- Action8 first44 header bytes:
  `1827000000000000900100002c0100000100000001000000b158b15ba550acc9a46aa661b9cf000000000000`.
  Runtime pointer fields following the static header are not source-byte pins.

These results identify the scene selection and actual asset header; this lane
did not execute the complete ROM bank loader or certify a live rendered panel.

## Read-only open state, close hit rectangle and native input

Let `W=UI+E2170` and `p=int16(UI+232DA8)`. Validate p before reading a node.

| Field | Native address / interpretation |
|---|---|
| Panel node | `W+818+p*2A08` |
| Open state | `WORD(node) & 20` |
| Renderer handle | `WORD(node+4)` |
| Renderer owner | `DWORD(W+8)` |
| Renderer object if handle<1000 | `owner+10+handle*290` |
| Control c | `W+8B8+p*2A08+c*64` (also node+A0+c*64; stride100 decimal) |
| Control absolute RECT | four int32 at control+10 |
| Hit-manager pointer | `DWORD(W+4)` = `DWORD(UI+E2174)` |
| Hit ID | signed WORD(control+8), valid 0..BFF |
| Hit entry | manager+hitID*18 |
| Active hit entry | DWORD(entry+0)==1 |
| Hit absolute RECT | four int32 at entry+4 |
| Hit state | DWORD(entry+14) |

All numerals in this table are hexadecimal. The original 418B80 allocator copies
the control absolute RECT into entry+4/+8/+C/+10. 418CD0 validates the signed ID
and active field before reading +14. At 104A27, the widget loop checks the
control enabled byte, reads signed WORD(control+8), takes manager from W+4, and
calls 418CD0. This allows independent read-only rectangle agreement checks.

C3080 creates **control0** using 106C70, resource type1F/action48, local bounds
(0,0,419,339). It spans the whole large panel; there is no independently created
close-button control in this path. Absolute bounds add node+18/+1C x/y.
The world input dispatcher VA4820A0 calls VA504620; when its panel result matches
UI+232DA8, it calls C37F0(control,event). C37F0 ignores the control argument and
closes through C3870/105230 whenever `(event & 3) != 0`. An event containing only
bit4 is insufficient. Do not infer physical button names solely from these bits.

1052E0 opens with low flags `(old & 3)|20`; 105230 closes with `(old & 3)|10`.
A bounded Unicorn run of the original functions, with inactive rendering
handleFFFF and no callback, produced:

```text
C3890(1)       -> panel flags0021
C37F0(0,0)    -> panel flags0021
C37F0(0,1)    -> panel flags0011
C3890(1)       -> panel flags0021
C37F0(0,2)    -> panel flags0011
```

No native callees were stubbed. This proves open/close state transitions under
the explicit synthetic state, not physical hit testing or loaded rendering.
The reproducible setup uses `test_current_inventory.CurrentInventoryTests`,
`consumer_vm()` and `call()`: pinned image as `h.image`, scene at
`PACKET_PAGE+100` (zero0x200bytes, WORD+F0=00C4), UI+8AA4C pointing there,
panel index0, UI+232E56=-1, zero node0x2A08bytes, node flags0011,
WORD(node+4)=FFFF and int32(node+28)=-1. Invoke the five calls above with this=UI.
Identity and resulting flags must be checked with explicit raises or unittest
checks, never Python assertions that disappear under `-O`.

## SPI source pins and inventory metadata boundary

Both rows come from `Data2/Patch/Comm/gamedata.csvZ`, SPI section (737 rows):

- Compressed SHA256 `70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731`.
- Decoded SHA256 `75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815`.
- RowDesc line3 SHA256 `ab84cb5beb35b1a0f753f657993d881673b3b59351049cdedf91c2f7fab79e34`.

| Item | Raw source name | Line / decoded offset | Resource / icon | Category / effect |
|---|---|---|---|---|
| 5569 | 金鰲島地區地圖 | 8236 / 617594 | Spi01069 / 55069 | 3 / 8428 |
| 5576 | 崑崙仙界地圖 | 8243 / 618386 | Spi01076 / 55076 | 0 / 8428 |

- Row5569 SHA256 `6aad4d59bbbd41192acfc375d538ca93f1c2e454975e44f57114e7aedbae172e`.
- Row5576 SHA256 `6877e19719a222a3ad7bf45d1f61526d7364eb3b822890f15845d6a8ca216404`.
- Raw numeric source columns14..25 for both: `1,0,0,0,1,1,1,1,1,0,0,0`.
  RowDesc names columns14..24; column25 has no supplied label and is retained
  without inventing one. Their bit grouping is F1/01; these source flags are
  **not** the inventory instance's 20 metadata bytes.

96390 validates backpack slot0..29 and UI+866E4==0. 963C0 finds an occupied
matching lowWORD item ID; the quotient55 path calls 96350, producing C2S25.
The direct wrapper's routing reads count and lowWORD item ID, not a nonzero
highWORD packed type. The full 9A330 double-click path also reads loaded item
definition+11A flags; bit0 set and bits2/3 clear select the relevant use path.
Original initializer97FE0 clears all50 inventory records of24bytes; scalar41
writes count and lowWORD ID, retaining the other bytes. This is a known fresh
baseline, not a proof that arbitrary existing5576 instance metadata is zero.
Do not derive a packed inventory type from source category0 or fabricate
20 metadata bytes from the SPI row. Full5576 loaded-definition/UI qualification
remains part of the parent lane's actual client test.

## Importer and strict read-only reader

- `tools/strike_lab/import_native_map_items.py` owns `SCHEMA`, `install(db)`,
  `pinned_records(client)` and `import_catalog(db,client)`.
- Tables: `native_map_item_sources` (one source) and `native_map_item_rows`
  (two original rows). Raw CP950 record/RowDesc bytes, line/offset/hash,
  compressed/decoded source hashes and parsed byte fields are retained.
- Every record is `SOURCE_DISPLAY_ONLY`. Source validity is not use authority.
- Source parsing/pinning precedes database mutation. Import uses one immediate
  transaction, exact-existing-catalog comparison, readback and integrity checks.
  Partial/foreign/corrupt catalogs reject without replacement; failures roll back.
- `src/db/NativeMapItemCatalog.{h,cpp}` borrows sqlite3*. `populated()` returns
  false only when both installed tables are empty. Missing schema or corruption
  throws `DatabaseError`. `contains(uint16_t)` qualifies the entire source and
  **both** rows before returning membership; unknown IDs return false only after
  qualification. `lookup()` additionally exposes pinned raw fields.
- One SELECT supplies a coherent read snapshot including counts. No SQL writes,
  DDL, transaction ownership or data repairs occur. It works with a read-only
  connection and inside an existing caller transaction. Complete raw-byte and
  scalar comparison to embedded pins rejects tampering even if hash labels stay
  unchanged. It does not require the separate native map catalog.

### Verification performed

Python tests, normal and optimized: **5 tests PASS** each. They cover real
source pins, idempotence/reopen, invalid compressed/decoded source, partial and
foreign rows, flag/source tampering, failed second insertion, altered readback,
rollback, existing transaction and preexisting schema preservation.

```powershell
python -m unittest discover -s tests/research -p test_import_native_map_items.py -v
python -O -m unittest discover -s tests/research -p test_import_native_map_items.py -v
```

C++ standalone: **267 checks PASS**, MSVC C++20 x64 `/W4 /MD /utf-8`, using
`src/db/NativeMapItemCatalog.cpp`, `tests/test_native_map_item_catalog.cpp`,
include paths `src`, `build/_deps/sqlite_src-src`, linked against
`build-town-visibility/Release/sqlite3.lib`. No shared CMake or runtime build
was edited. The executable takes exactly one explicit disposable imported DB
path, opens it read-only, and performs negative mutations in memory clones.
Tests cover every persisted column, wrong SQLite types, incomplete/orphan
catalogs, unknown-item lookup, tampering the other row, no-write checks and
existing read transactions. To run without touching a server database:

```python
from pathlib import Path
from contextlib import closing
import tempfile, sqlite3, subprocess
from tools.strike_lab.import_native_map_items import import_catalog
with tempfile.TemporaryDirectory(prefix='god2-map-reader-') as d:
    p = Path(d) / 'test.sqlite'
    with closing(sqlite3.connect(p)) as db:
        import_catalog(db, Path('../God2'))
    subprocess.run(['build/map-item-agent-check/native-map-item-catalog.exe',
                    str(p)], check=True)
```

Integration registration should keep this standalone main out of any globbed
unit-test binary and invoke it against a disposable imported fixture. Shared
migration26, CMake, server route, owned map policy and live client acceptance are
owned and reported separately by the parent integration lane.
