# Current world UI resource at +0x214

## Validated answer

The original source is current client `Data2/Patch/FieldComm3.csvZ`,
decoded table/header name `FightCommon`, record key `RomIdx=2`, column 1
(zero-based). The literal setting is `\Data3\Flow\DTitleGui.ROM`.
The source's informational enum column is `ROM_DTITLEGUI,` (quoted CSV
field, including the comma). This is **not** an INI section/key/default or
a CString object. It is an indexed CSV record with an inline C string.

Concrete current asset:

`C:/Users/risei/Desktop/God2/God2/Data3/Flow/DTitleGui.ROMZ`

The native path passed toward `60A90` is:

`C:\Users\risei\Desktop\God2\God2\Data3\Flow\DTitleGui.ROM`

The original `29820` prefix prepares that same path plus `Z` as its first
`fopen(..., "rb")` argument. Both uncompressed source spellings
`FieldComm3.csv` and `DTitleGui.ROM` are absent in the current asset tree.
The compressed asset exists, is 10,310 bytes, and decodes to 30,310 bytes
beginning `IGSROM02\0\0\0\0ACTINDEX`.

CSV physical line 7, decoded byte range `[230, 292)`, contains the setting:

```csv
2,\Data3\Flow\DTitleGui.ROM,"ROM_DTITLEGUI,",//[original Big5 comment]
```

The comment placeholder above is explanatory, not the source's literal bytes.
The tool/tests retain and validate the complete original source bytes.
The literal path is supplied by this row; no hardcoded default path is
established. In an explicit counterfactual fixture deleting only this row,
the complete native reader still returns success (max ID remains 64), and
the new calloc-backed `+0x214` field remains empty. It does not substitute
`DTitleGui.ROM` or validate every ID's presence.

## Native provenance and layout

Addresses below are RVAs unless explicitly marked VA; image base is `400000`.
Original current mapped image:

`artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`

SHA-256: `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.

1. World initialization at `64A8A..64A90` calls `815C0` with
   `UI = world + A7F2F6C`.
2. `815C7` pushes the literal at VA `58F1A0`, `FieldComm3.csv`.
   `815CE` pushes VA `5847D8`, `\Data2\Patch\`.
   Original `12F550` resolves the directory; `815E6` formats `%s\%s`.
   The resulting CSV path contains a double separator before the filename,
   because the directory literal already ends in a separator.
3. `815F3` supplies capacity `0x41` (65). `815F5` supplies reader
   `UI+CFF74`, and `815FB` calls the complete original reader `54720`.
4. `54727 -> 51920` requests four columns; the original setter clamps
   its stored column capacity to five. `51960 -> 2530` opens the CSV;
   `519C0` parses its header and skips to physical data line 5.
5. `54766..5476C` allocates `calloc(0x108, 65)`.
   **Pointer writer `54776`: `[reader+121F0] = EAX`.**
   Each record has a 32-bit ID at `+0` and 260-byte inline path at `+4`.
6. `547A9 -> 51B30` parses column 0 as the record index.
   `547D6..547E3` writes the ID at `records + index*0x108`.
   `547F7` computes `records + index*0x108 + 4`.
   `54800 -> 51AE0` copies column 1; actual path byte writers are
   **`51B12` (`rep movsd`) and `51B19` (`rep movsb`)**.
   Observed writes cover exactly all 25 path bytes plus the terminating NUL.
7. Therefore:

```text
reader                     = UI + 0xCFF74
reader + 0x121F0            = UI + 0xE2164
                            = world + 0xA8D50D0
*[world + 0xA8D50D0]        = records allocation (65 * 0x108)
records + 0x214            = records + 2 * 0x108 + 4
                            = RomIdx 2 inline path
```

The reader's `+121E8` is a maximum parsed ID plus one, not proof that every
record is populated. Source array IDs are contiguous 0..64 in the pinned
current CSV. No other resource fields are catalogued in this lane.

The binary diagnostic at VA `589554` identifies original source provenance
as `Z:\FS2_CLIENT_SOURCE_SVN\TRUNK\SRC_OUTSIDE\SOURCE\src\csvlib\fightcsv.cpp`.
That is an embedded build-time source path, not an available recovered C++
source file; the proof here is original machine code plus current asset bytes.

## Consumer contract

`64CB6` loads the records pointer; `64CBC` adds `214`; `64CC1` pushes the
address itself. There is no load of a CString data pointer.

`64CC2` calls **RVA `12F550`**, VA `52F550`, not RVA `2F550`.
This helper caches `GetCurrentDirectoryA` and tests the path's first byte.
For a leading backslash it uses `%s%s` at VA `5847F8`; otherwise it uses
`%s\%s` at VA `585BC8`. The outer call `64CD2 -> 147AF7` uses **`%s`**
at VA `584954`, not `%s%s`.

The probe executes `64CB6..64CE1`, stopping immediately before `60A90`.
It observes the exact stack argument above. A wrapped 32-bit EBP alias
makes the existing UI reader field visible at the original world offset;
no world or renderer object is built.

Static loader/handle continuation in the same pinned original image:

- `60A90` uses the primary bank pointer at manager `+121F8` and signed
  16-bit next slot at `+121FC`; `60ACC` calls `29820(path, slot)`.
  It returns that primary slot through EDI and increments the slot counter.
  An optional second bank at `+BF808` is serviced separately. The wrapper
  does not propagate `29820`'s success/failure as its return value.
- `64CF2` stores the `60A90` return in ESI. `64D01` pushes it for the
  fourth argument of `1081C0` at `64D0D`.
- `64F3F` again pushes ESI as fourth argument of `1081C0` at `64F4B`
  (`this=world+39C`). This is a slot handle, not a ROM byte pointer.
  This sidecar does not assign it a guessed numeric value.
- Original `29820..298ED` is executed independently through first-open
  preparation, confirming the concrete `.ROMZ` candidate. The slot-zero
  input to this prefix is only a bounded filename probe, not a claim about
  the world's eventual allocated handle.

## Reproduction and limits

```powershell
python -m tools.strike_lab.current_world_ui_resource
python -m unittest discover -s tests/research -p test_current_world_ui_resource.py -v
```

Five tests pass: current source/asset identity; complete native reader and
observed byte writers; original resolver/consumer/ROM filename preparation;
missing-row behavior; pinned call targets and handle-push instructions.

The tool uses the existing bounded memory/CRT adapter methods without
constructing their indoor, world, ROM-bank, or renderer fixtures. It runs
original `1EC0` separately on both complete compressed sources and compares
the resulting bytes with the hash-pinned decoder output. It then executes
full `815C0 -> 54720`, including the original header/row parser and field
getter. All reads are from current source files; host files are never changed.

Explicit adaptation boundaries:

- Reader/UI storage is initially zero-filled, and the current-directory cache
  is initialized explicitly. Full live application/owner construction is not
  claimed.
- CSV file abstraction `2530/27B0` is adapted to a decoded read-only text
  stream with CRLF translation. Its native temporary-file open/lifecycle is
  not executed. This does not replace row selection, index math, path writes,
  or native decompression.
- CRT allocation, fgets, sscanf, sprintf, CWD lookup and temporary-file search
  have bounded adapters. No game reader/getter or path selector is substituted.
- `60A90` and full `29820`/ROM parser/rendering are not executed in this lane.
  ROM decompression and filename preparation are proven; successful bank
  insertion, handle lifetime, and display are the owner's next work.

There is **no unresolved source or writer for the +214 path**. The concrete
next native integration location is `64CE1 -> 60A90 -> 60ACC -> 29820`,
using this verified source and the owner's real bank/counter state. To remove
the independent CSV I/O adaptation, trace `51989 -> 2530` and its matching
`519B1 -> 27B0`; that concerns file lifecycle, not an unknown config key.
No UNKNOWN is treated as completed gameplay, and this display-only path
establishes no original authoritative server rule.

## Source hashes

| Source | SHA-256 |
| --- | --- |
| FieldComm3.csvZ | `197b0952d33bddb6f3682779208dd396fcecbe451c1b9dc68ec86209ed1a7e05` |
| Decoded CSV (3,753 bytes) | `2c76b311dfcfba4ceb2b23c0faf5011339365673bd01c8a4ed371fb174fd43ac` |
| DTitleGui.ROMZ | `aef52204cba53037a97658de390e916fd1d418040f92a6c95e3bd4e766470b92` |
| Decoded ROM | `8920aec8158d2fb82814d2a61e101ec4a35f1adfbdc208d249cb56702c99faf2` |

Only the requested new tool, test, and this document are authored. Existing,
shared, and runtime sources are not edited. Retired client assets or names
are not used as evidence or leads.
