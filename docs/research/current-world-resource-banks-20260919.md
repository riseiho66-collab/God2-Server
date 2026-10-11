# Original world resource-bank lifecycle, 2026-09-19

## Scope

`tools/strike_lab/current_world_resource_banks.py` now executes original
60810/608D0 construction, 60A10 binding, 60B80 character-table reload,
60B10 checkpoints, 619D0 scene selection and full initial-scene 61AD0 cold
preload in the bounded offline VM.
The pinned image is `native-master-01-stable.bin`, SHA-256
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
Both legacy corpora were searched for these bank functions before current
instruction inspection; no reusable bank-lifecycle implementation was found.

The bank manager is now joined in place at WORLD+AA364B8 by
`NativeColdWorldActor`, which runs 681CF..68851 continuously, including the
previous 682F1..68315 gap. `NativeWorldScene` uses this cold actor by default.
The older `NativeWorldActor` remains a separately labelled slice-only
regression oracle. No live process, network or C++/Lua gameplay change was made.

## Actual native execution

- 60810 constructs the two descriptors; active bank starts at signed -1.
- 60A10 binds both real ROM-bank objects and executes full 637B0 twice:
  120 DrvDoll records per bank, including original row loop and file closure.
- 60B80 executes both 63BF0/51F20 HeroDoll loaders (918 records each),
  both 63260 Drv loaders (92 records each), and both 63F40/552C0 GodDoll
  loaders (221 source rows each). Native MFC map construction and insertion
  execute, rather than a prebuilt hash-map fixture.
- 619D0 distinguishes initial misses from later hits, rotates two banks,
  records WORD area/scene selectors and rebinds renderer pointers through
  1FDF0. Misses restore slot and allocator checkpoints through 2D9C0/28880.
- 60B10 saves both allocator and next-slot checkpoints through 2D9A0/288E0.
  Tests use actual 28740 allocations with explicitly seeded slot counts.
- 61AD0 executes 616A0/60C60 and four complete 5E850 catalog loads: 215 ENY
  and 319 NPC records in each bank. The initial enemy group is absent according
  to original 5A000; original 5AA70 supplies the NPC group for codes 21/2143.
  Native category normalization loads records 318/20/237 into slots 0/1/2,
  using npc2401/npc2721/npc2643 ROMZ sources. Native parser inputs are compared
  byte-for-byte with their pinned decoded sources; all file handles close.
- The joined actor then loads its five actual role/mount resources into slots
  3..7. Its mount handle changes from the earlier isolated fixture's slot 4
  to native slot 7. No slot value is injected into the original function.

The test source comparison covers all 918 HeroDoll records in both banks and
1836 real native hash lookups; all 120 accessory and 92 Drv records per bank;
and all 480 GodDoll cells per bank, including unused cells and original
gender-zero duplication. These are visual/resource definitions, not monster
combat stats or proof of implemented deity gameplay.

## Environment adapters and limits

CSV sources are pinned by raw/decoded SHA-256 in `CSV_SOURCES`. Each decoded
source is independently compared with native 1760/1EC0 decompression. The
virtual filesystem then exposes an explicitly read-only plain-CSV namespace:
native 2530 tries compressed input, receives absent, and reads the qualified
plain view. The compressed-file-to-temporary-file branch is NOT exercised.
CRLF translation matches the text-read view; original source bytes are retained.

Other adapters cover bounded allocation, fgets, signed decimal sscanf,
path formatting, current-directory input, existing CString helpers, critical
sections and rectangle operations. No internal game loader is replaced by a
success stub. Failed sscanf leaves the destination untouched; nonnumeric Drv
header text must not be treated as an integer or as a loader failure.
Surface RGB555, 4 MiB allocator capacity and object addresses are explicit
offline fixture inputs, not recovered live-device configuration.
GetTickCount is an explicit fixed-zero clock. Original 606D0 executes twice
and increments progress from 0 to 2, while its timed repaint branch at 60731
does not execute. This is not qualification of the live progress renderer.
Diagnostic vsprintf only accepts the observed no-format-arguments strings;
original 289B0 is itself a bare return, not an adapter success stub.

## Verification

Command:

```text
python -B -m unittest discover -s tests/research -p test_current_world_resource_banks.py -v
```

Earlier lifecycle run: **10/10 passed in 33.751 seconds**. The first run's checkpoint-count
assertion counted a constructor checkpoint as a new save; corrected the test
to measure the delta. Actual allocator/slot restoration already matched.

Expanded worker run: **15/15 passed in 54.106 seconds**, including full cold
preload, every ENY/NPC record path/category/cache in both banks, native ROM
metadata, progress and a same-scene hit with no extra loads. Main's joined
scene suite passed **8/8 in 99.872 seconds**: C++ 2A output, original decoder,
continuous cold actor, native CAN/HMD/ROM loading and grid/projection checks.

Remaining: later scene continuation after 10078F (music lookup/setup
F76E0/F7520 and camera/pool work including 46520/103C70), progress repaint,
device presentation and live client/server acceptance. The initial NPC source
mapping is separately established in
`initial-npc-preload-assets-20260919.md`; its category/ordinal normalization
must be retained, including the mandatory category-9 default.
