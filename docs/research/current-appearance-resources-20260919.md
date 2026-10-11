# Current Appearance Resource Dependency

## Result

**The documented C[33] component-1 derived lookup mismatch is reconciled by
the actual current HeroDoll table. No additional profile-to-2A field mapping
is promoted.** This is a resource-table/lookup result, not a loaded-ROM,
rendered-appearance or world-entry result. Existing appearance tests and the
production serializer are untouched.

Current native preview looks up `(0,2,0,0,0)` while the proposed completed
component block in world looks up `(C[33],2,0,0,0)`. For C[33] = 1 these are
different records, but their actual +0x2A bytes are both **2**:

| Source line (1-based) | Native key | File field | Byte +0x2A | Cache WORD +0x1E |
| --- | --- | --- | --- | --- |
| 26 | r1h000 | r01w800.romz | 2 | FFFF |
| 92 | r2h000 | r01w800.romz | 2 | FFFF |

Thus with source-backed selector-zero action and the create preview's zero component
resource indices, both original consumer paths request the same primary
component-1 record:

| C[33] | Primary key | Source line | Actual file |
| --- | --- | --- | --- |
| 0 | r1f002 | 601 | r01f002.romz |
| 1 | r2f002 | 611 | r02f002.romz |

The previous synthetic 2-versus-3 counterexample remains a valid warning about
unconditional reasoning; it does not describe these two pinned real records.
No synthetic successful resource handle is introduced here.

## Corpus Search First

Searched both retained roots before inspecting current assets/native code:

- `C:/God2Evidence/classic-20260820/files/God2-Classic-Server-Formal-Handoff-20260820-020345/ServerSource`
- `artifacts/legacy-evidence/xjz-20260820/files/XJZ-Server-Cpp/server_implementation`

Targeted searches: `52460`, `526c0`, `63c90`, `appearance`, `dollcsv`,
`r1h000`, `r2h000`, `r1h`, `r2h`, and HeroDoll/dollcsv filenames.
No direct lookup table or reconciliation was found in these searches.
Classic `src/God2.ClassicServer.Runtime/OfficialClientWorldProtocolFrames.cs`
contains historical appearance/world candidates rather than this current
native lookup relation. XJZ `evidence-account-character-runtime-v0.md`
describes appearance JSON and explicitly unfilled protocol samples, not a
source-backed current component mapping. This is a bounded search result,
not a claim that all legacy contents have been exhausted.

## Pinned Inputs

- Image: `artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`.
- Image SHA-256: `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
- Actual source: `C:/Users/risei/Desktop/God2/God2/Data2/Patch/HeroDoll.csvZ`.
- CSVZ SHA-256: `df2fa65e0b159b18303b2e135cacc690e0e02e4ea12560cacda3f0d8e6ae1359`.
- Decoded SHA-256: `0ba373ca45d0f4452f1d847fab5f5e194f00501f26a58f082c5352f71fe921c2`.
- Header: first data line 26; count 918; decoded length 37189 bytes.

Hashes are checked before native execution. CSVZ decompression uses existing
`omega_assets.decode_csvz` with a 1 MiB output bound, not the native file-open
or decompressor path. Latin-1 preserves source bytes; Python's CSV parser is
an independent comparison oracle, not the producer of native record fields.

## Executed Native Relation

All addresses are RVAs relative to VA 0x400000 in the pinned x86 image.

1. Preview initialization references `HeroDoll.csv` at 4225 and calls loader
   51F20 at 4261 with `this = preview + D8C`. World table setup references
   the same filename at 63C28 and calls 51F20 at 63C66 with `this = bank +
   12D78`. These call sites are identified by disassembly, not executed here.
2. For every actual source line, original tokenizer 51BE0 executes, followed
   by original loader row slice 5201C..521A2. Original 51AE0/51B60 read the
   token fields; original 51B50/51BA0 fetch field 5, and 5219E writes its low
   byte to record +2A. Row stride is 2C. File, key and cache initialization
   execute in this slice. All 918 resulting records are compared to source.
3. The bounded fixture constructs the native CMapStringToPtr container from
   those keys and native-produced record pointers. Its node/bucket layout is
   taken from 15A60C/15A6A6; allocation and insertion are not executed.
   Original 15A662 -> 15A60C hash/collision-chain/strcmp lookup executes for
   all 918 keys and must return the exact corresponding record address.
4. Original 52460 executes, including 52260's component/action transformation,
   format argument construction, native map lookup and missing-key branch.
   Original 52420 executes its +2A load and `<2`/addition behavior. The two
   head records return 2 plus the supplied extra value for all extras 0..31.
5. Original preview component-1 slice 9A90..9B00 executes against real table
   records. Its partial component block preserves component 2's still-zero
   binary nibble. The slice returns the actual primary record address.
6. Original world slice 61366..61399 executes with the final component block;
   it traverses 63780 and 63C90 -> 52420 -> 52460 -> native map lookup. The
   continuation 61399..613F1 executes the second 63780 and primary argument
   packing. Its five key arguments are
   submitted to original 52460 and must resolve to the preview's exact record.
   Both binary values and all 7 x 7 variant pairs pass: 98 combinations.

The initial regression supplied a zero action modifier. The follow-up below
removes that assumption by loading actual Drv records and executing both 63780
calls. The complete 61270 and complete preview are still not executed.

## Adapters And Guards

Only four library operations are adapted: decimal-only `sscanf` (1480B4),
ASCII `strlwr` (157F67), the exact `r%d%c%d%02d` CString format (158E89), and
scratch CString destruction (15AD35). Each validates its expected input.
No game lookup, resource record, cache success or ROM loader is stubbed.
CRT strchr, memcpy and strcmp execute original instructions.

The hash container has 1103 buckets and 918 distinct source-backed nodes.
Record storage becomes read-only after native loading. Code is read/execute
only. The low page permits only four opcode-checked FS:[0] SEH instructions
inside 52460; arbitrary null accesses fail. Each slice is limited to one
second/100000 instructions and must reach its exact stop. Call stack balance
is checked. Missing keys return native null; a missing derived lookup returns
native zero; an existing unloaded primary resource returns native FFFF.

## Exact Remaining Dependency

No C[33] nibble projection is yet qualified as a **complete** consumer/loaded
appearance mapping. This result closes just the previously isolated +2A
table-value discrepancy under the stated zero-action inputs.

- The original selector-to-action lookup 63780 depends on the real bank's
  WORD count at +121F6 and 32-byte records starting +121F8 (returned WORD
  at record +12 hex). The earlier +121FC/+0E description identified the same
  returned address, but not the actual record start. This table is now loaded
  as documented below. Complete mounted appearance remains outside proof.
- Every real HeroDoll record starts with cache WORD FFFF. Preview 9B06 tests
  that value and enters 9B0D..9B45: path construction and 4B70 resource loading
  before FF450. World 63DE0 -> 526C0 sees the same FFFF, branches at 63E28,
  then uses 526F0 and calls the real ROM loader 29820 at 63E8D, caching only
  after success via 52680 at 63EB1. The companion preview/world role-resource
  documents now execute these paths with real ROMs and native cache writes;
  no handle is forged to cross either path.
- Required file dependencies for this component are the real RoleDoll
  `r01w800.romz`, `r01f002.romz`, and `r02f002.romz`. The companion
  `current-role-doll-resources-20260919.md` now qualifies direct native loading
  of all three, with actual palettes/images/actions and bounded platform
  adapters. Follow-up `current-world-role-resources-20260919.md` executes world
  cache publication, path wrappers, complete 61270 and normal 2A component
  setters, including the actual retained mounted candidate. Preview wrappers
  and FF450 are covered by `current-preview-role-resources-20260919.md`.
  Complete animation/composition/rendering remains unqualified.

Therefore the two previously qualified variant-bit mappings remain the only
production-qualified mappings. No scene/NPC loader, shared runtime, CMake,
existing appearance test, UI, socket, authentication or live process is touched.

## Regression

From the server root:

```powershell
python -B tests/research/test_current_appearance_resources.py -v
```

Four tests cover all 918 native row records and native hash lookups, the two
real +2A values, 98 preview/world primary-key equivalences, 64 derived-value
checks, missing keys, unchanged unloaded caches and bounded API rejection.
Final run: **4 tests passed in 30.989 seconds**, including read-only record
storage and instruction-checked SEH guards.
This is offline original-code evidence, not current-client E2E acceptance.

## Follow-up: Actual Drv Action Table

Both legacy roots were searched for Drv.csv, DrvDoll, 63780 and 121F6.
Classic schema 462 and XJZ evidence-mount-auction-life-item-v0.md preserve mount
visual metadata, but not this current native loader. XJZ's visual evidence uses
a different source build (883 HeroDoll records versus the current 918); its
values are not substituted. Native 63260 references Data2/Patch/Drv.csv at
58A88C. This is the actual source for 63780, not adjacent DrvDoll loader 637B0.

Current Data2/Patch/Drv.csvZ hashes:

- Raw: 9af4b2ed4d5b007bfde12f2cff4e9895715903a8ffaf5a356aee011f3fb98f2e.
- Decoded: 72cd006c121a865e10b7d1e2c655895da16a5e760bad2c8d473bf5663996f6e0.

The header selects first data line 10. All 92 source rows, sequential indices
0..91, execute tokenizer 51BE0 and row loader 632C5..633E5. No resource load
or mount ownership is inferred. The source index is a label, while native
storage advances its own ordinal count. Source rows happen to agree exactly.
CSVZ decompression remains the bounded existing decoder; the complete file
opening/header-reading path is not executed.

Native record layout, relative to bank+121F8+32*ordinal:

| Offset (hex) | Source |
| --- | --- |
| 00..0F | Filename, including genuinely empty row 0 |
| 10 | Unloaded cache WORD FFFF |
| 12 | Column 2 action classification |
| 1E | Column 3 preload value |
| 16,18,1A,1C | Columns 4,5,6,7 |

Tests compare every source-backed field and call original 63780 for every
ordinal. Row 0 returns action 0; rows 1..91 all return action 2. Nonnegative
out-of-range selectors return native zero without changing records. Because
63780 uses a signed WORD comparison, the helper explicitly rejects negative
and high-bit selectors; it does not misreport the native routine as a general
bounds-safe parser.

The 98 preview/world comparisons now execute 61366..61399 followed by
61399..613F1, including both actual 63780 calls, with selector 0. World bank
HeroDoll pointers reference the already native-loaded records and native hash
lookup. No action return is supplied by the fixture. This qualifies the
zero-selector action dependency, not the entire mounted branch, historical
nonzero component indices, ROM cache or rendered appearance.

An exact temporary stop hook prevents cached Unicorn translation blocks from
crossing slice boundaries on repeated execution. Every call retains its
instruction/time budget and exact-PC assertion. Updated suite: 5 tests passed.
