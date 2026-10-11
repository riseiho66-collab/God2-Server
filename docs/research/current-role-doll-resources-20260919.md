# Current RoleDoll uncached ROM loading

## Result

The original current-image `29820` uncached ROM loader returns normally for the
actual `r01w800.romz`, `r01f002.romz` and `r02f002.romz` files. Original code
decompresses their ROMZ bytes, allocates native ROM resources, parses their
images/palettes/actions, and populates previously empty bank slots.

This is an offline, in-memory loader result. It is not full renderer, complete
appearance, original-client E2E, world-entry or playability acceptance. No client
process, UI, authentication, network connection or host policy change occurred.
C++20 core/Lua gameplay and production serializers are untouched.

## Search and inputs

Read `current-appearance-resources-20260919.md`,
`current-indoor-resources-20260919.md`, and the pertinent existing helpers/tests
before implementation. Before native analysis, searched both retained roots:

- `C:/God2Evidence/classic-20260820/files/God2-Classic-Server-Formal-Handoff-20260820-020345/ServerSource`
- `artifacts/legacy-evidence/xjz-20260820/files/XJZ-Server-Cpp/server_implementation`

Search terms: `RoleDoll`, all three filenames, `29820`, `2a1d0`. Classic hits
were unrelated numeric/hash matches. XJZ `db-evidence-schema-v0.sql` retains
the real HeroDoll rows (including source lines 26, 92, 601 and 611), but the
bounded search found no current uncached loader implementation. The inspected
XJZ `evidence-gamedata-rom-map-v0.md` concerns item ROM mappings, not this loader.
These findings do not claim exhaustive inspection of either corpus.

Image: `artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`.
Image SHA-256:
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
All addresses below are hexadecimal RVAs relative to VA `400000`.

Actual asset directory: `C:/Users/risei/Desktop/God2/God2/Data2/Rom/RoleDoll`.

| File | Compressed bytes | Decoded bytes | ACTINDEX | Palettes | Images | Actions |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| r01w800.romz | 4216 | 7516 | 4201 | 8 | 1 | 19 |
| r01f002.romz | 14974 | 24237 | 4001 | 8 | 17 | 19 |
| r02f002.romz | 16210 | 25746 | 0 | 8 | 22 | 19 |

| File | SHA-256 of compressed source |
| --- | --- |
| r01w800.romz | `d64f1c25bc93fcedd4920347e70fc55d6385a5c188043ffcc3a96725c2d72440` |
| r01f002.romz | `0229239796e372609539121890ed4afa64cefe5d3d1b01adff58ca1ddab874d0` |
| r02f002.romz | `fe544837905075a6d46c2217f169a762edee63c04739f6e31a0e11b64c7c5120` |

| File | SHA-256 of decoded ROM |
| --- | --- |
| r01w800.romz | `53018d6aec69d67ba5611cbe307cc08ebe9920a3a127d9d77bc86662e7fd7071` |
| r01f002.romz | `9742ca3c81787acd58af2a5af943b1f2b7501ed80bf672be3a85cda64d9f77ba` |
| r02f002.romz | `5401efd34ab14c5215e3604ad2802bca7a47b79ac9af0c033649f85ff4ab4b5d` |

The helper verifies the image and all three source/decoded hashes before native
execution. Existing `omega_assets.decode_csvz` supplies an independent expected
byte sequence; it does not supply the native parser's input. At the original
`2A1D0` entry, an observation-only hook checks the entire buffer actually produced
by `1EC0` against that independent decode.

## Executed path and comparisons

- `2030` initializes the original temporary allocator. `29700` constructs a
  native ROM bank and `297E0` configures its pool with an explicit 4 MiB fixture
  capacity. The native bank has 512 records with stride `1514`; all begin with
  ACTINDEX `FFFFFFFF` and zero resource counts through original initialization.
- `2B180` binds an explicit RGB555 format fixture. No surface command pool,
  renderer pool, window, DirectDraw device or display is created.
- Each file is passed directly to complete `29820` using a distinct empty slot
  (0, 1, 2). Its compressed-input branch opens real pinned bytes through virtual
  CRT I/O, runs `1760/1EC0`, then calls complete `2A1D0`. Native `2D930 -> 28740`
  handles resource allocation. No native game/resource call returns a stubbed
  successful value.
- The return values are actual ACTINDEX values **4201, 4001, 0**, not fabricated
  resource handles and not the chosen slot numbers. In particular, zero is a
  valid result for this actual `r02f002` ROM. The other 509 records remain exactly
  equal to their pre-load bytes.
- All 24 palettes match source WORD values after the explicit RGB555 conversion
  (`value & 7FFF`). Original `2C090` loads 39 PCX images; an independent bounded
  PCX RLE decoder compares every pixel, retaining the actual width/height and
  handling source scanline stride separately.
- Original `2D250` loads the `r01w800` 1x1 16-bit `TGA_RWIF` image. Its pixel and
  row-offset bytes match the source, with native image type 1 and no palette-index
  pixel assumption. This format difference was observed in the actual assets.
- All 57 action headers and names, 306 `ACT_STEP` chunks (including each native
  step count), and 77 `ACT_POOL` records match source-backed data. `2A8F3..2A964`
  copies the first nine bytes of each 10-byte pool record; the last source byte
  is not asserted as a copied native field. All 77 source `ACTBLOCK` payloads
  are empty; their native pointers are non-null. No animation rules are inferred.

## Adapters and bounds

`current_role_doll_resources.py` reuses methods from the existing indoor helper
without running its initializer or editing it. Only the CRT allocation, read-only
file operations, string comparisons, existing fail-closed diagnostics and narrow
temporary-file-search adapter are installed. On the passing path the observed
services are fopen/fclose/getc/fgetc/fseek/fread/malloc/free and FindFirstFile.
Original code reaches the same temporary-file search caller at `297F`; the
virtual namespace has no temporary files, so FindFirstFile reports none. No host
filesystem search/write/delete is performed. Virtual CRT file IDs are adapter
bookkeeping, not ROM bank handles. Atexit recording is available but is not
called in the passing loader run.

Input files and independent decoded outputs are bounded to 1 MiB each. The
inherited allocation adapter limits an allocation to 16 MiB and total mapped
heap to 128 MiB. The original temporary allocator and ROM suballocator still
execute. Native calls have a 50-million-instruction/30-second bound, exact
return-PC checks and stack-cleanup checks. Private bank/stack/format/scratch/heap
pages are non-executable; original code stays read/execute-only except the three
identified writable global pages used by the existing helper. The low page
allows only opcode-checked original FS:[0] SEH operations.

Missing qualified files return actual fopen NULL. Original `29820` tries its
fallback and returns `FFFFFFFF` without entering the parser or changing the
bank record. Slot 512 is rejected by original code before any file open. Tests
also reject unknown filenames, reuse of a populated slot, source hash changes,
invalid/over-budget allocation requests and non-SEH low-page access. Successful
loads close every virtual file and restore the SEH chain to `FFFFFFFF`.
These are bounded fixture checks, not a general malformed-ROM safety claim.

## Exact residual gap

Follow-up: current-world-role-resources-20260919.md now executes world cache/path
wrappers, complete 61270 and the normal 2A component-consumer slice, including
the actual retained mounted candidate. current-preview-role-resources-20260919.md
executes preview 4B70/cache/FF450. The direct-loader scope below describes this
module; it is no longer the furthest qualified boundary of the combined work.

The test executes the real uncached loader **directly**. It does not execute the
world wrapper `63DE0`, its `526C0/526F0` table/cache checks and path construction,
or cache publication through `52680`. It does not execute preview `4B70/FF450`,
selector/action lookup `63780`, component setters, animation advancement,
layer composition or full renderer initialization/display. Thus actual loading
of the three previously isolated ROM dependencies is now qualified under an
explicit standalone bank capacity and RGB555 format, but the complete
HeroDoll-cache-to-character/render pipeline remains unqualified.

No further profile-to-2A field mappings, packets, coordinates, gameplay stats,
formulas or rules are promoted by this work. Full renderer and E2E acceptance
must not be inferred from these loader tests.

## Regression and ownership

Run from the server root:

```powershell
python -B tests/research/test_current_role_doll_resources.py -v
```

Executed result: **7 tests passed** (initial complete run: 0.843 seconds).
Only three new Lane A files were added: the helper, this document and the
focused regression. Existing appearance/indoor files, shared runtime/session/
network, and `tests/CMakeLists.txt` were not edited. Main retains CMake integration.
