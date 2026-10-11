# Current preview RoleDoll resource cache

## Result

Original preview `4B70` executes over the actual three pinned RoleDoll assets,
followed by native record-cache publication and complete `FF450`. The follow-up
also initializes the real `106C30` control table with original renderer-object
allocations and executes `9B66..9B97`, including `106C30 -> FF490`. No resource
handle or native gameplay helper return is fabricated. This is an offline
loader/cache/control/setter result, not complete preview initialization,
animation playback, displayed rendering or E2E acceptance.

| Source-backed HeroDoll record | Actual file | Preview cache slot | ROM ACTINDEX |
| --- | --- | ---: | ---: |
| r1h000 | r01w800.romz | 0 | 4201 |
| r1f002 | r01f002.romz | 1 | 4001 |
| r2f002 | r02f002.romz | 2 | 0 |
| r2h000 | r01w800.romz | 0, reused by filename | 4201 |

Slots above are observed in the stated load order in an initially empty cache;
they are not universal client slot assignments. `4B70` returns the filename
cache slot, whereas `29820` returns the loaded ROM's ACTINDEX. The actual
ACTINDEX zero in `r02f002` is accepted by the original nonnegative-success test.

## Source boundary

Before native work, searched both retained legacy roots for `4b70`, `ff450`
and `RoleDoll` in C++, headers, C# and Markdown (excluding sqlite3 files):

- `C:/God2Evidence/classic-20260820/files/God2-Classic-Server-Formal-Handoff-20260820-020345/ServerSource`
- `artifacts/legacy-evidence/xjz-20260820/files/XJZ-Server-Cpp/server_implementation`

No matches were found in that bounded search. The earlier RoleDoll lane's
broader search found XJZ SQL rows for these assets; no legacy implementation
was substituted for current native code. Read the current appearance, indoor,
RoleDoll helpers and pertinent tests/documents before implementation, including
the previous world-appearance document's explicit synthetic `106C30` limitation.

Pinned native image:
`artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`.
SHA-256: `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
All code addresses below are hexadecimal RVAs relative to VA `400000`.

Files under `C:/Users/risei/Desktop/God2/God2/Data2/Rom/RoleDoll`:

| File | Compressed SHA-256 |
| --- | --- |
| r01w800.romz | `d64f1c25bc93fcedd4920347e70fc55d6385a5c188043ffcc3a96725c2d72440` |
| r01f002.romz | `0229239796e372609539121890ed4afa64cefe5d3d1b01adff58ca1ddab874d0` |
| r02f002.romz | `fe544837905075a6d46c2217f169a762edee63c04739f6e31a0e11b64c7c5120` |

| File | Decoded SHA-256 |
| --- | --- |
| r01w800.romz | `53018d6aec69d67ba5611cbe307cc08ebe9920a3a127d9d77bc86662e7fd7071` |
| r01f002.romz | `9742ca3c81787acd58af2a5af943b1f2b7501ed80bf672be3a85cda64d9f77ba` |
| r02f002.romz | `5401efd34ab14c5215e3604ad2802bca7a47b79ac9af0c033649f85ff4ab4b5d` |

The existing RoleDoll helper checks these identities before native execution.
The existing `AppearanceResources` independently hash-pins and executes native
HeroDoll row loading and key lookup; four resulting 44-byte records are copied
unchanged into this fixture with their original cache WORD `FFFF`. Its updated
Drv loading remains available and unmodified. This test starts at a selected
record, not the world selector-to-action path; it does not infer action zero
or replace the newly qualified `63780` results with an assumed value.

## Executed native path

1. Native `40A9..410D` executes the preview filename-cache allocation and
   initialization. The slice's EBP and pushed size are supplied from the
   preceding `4031/4035` instructions. Original instructions create the cache
   object, allocate 22 zeroed 256-byte filename buffers through bounded calloc,
   and set count/base-count to zero and capacity to 22. No populated cache or
   resource handle is preinstalled.
2. The fixture binds the existing real native ROM bank to preview `+15E7C`.
   Its explicit 4 MiB pool and RGB555 format are inherited from the RoleDoll
   oracle. Native `FF370` initializes the component object at preview `+15E38`.
   The full preview initializer is not executed; its `4183` request is 10 MiB,
   so the smaller standalone fixture capacity is not claimed as that live setup.
3. Each original `9B00..9B66` continuation receives a native-produced record.
   `9B06` tests record `+1E`; an unloaded record traverses `12F550`, original
   sprintf path assembly, CString construction and complete `4B70`.
4. `4B70` searches its real filename entries using the bounded CRT
   case-insensitive comparison. A miss calls actual `29820` with the current
   count as slot, executing original `1EC0/2A1D0` and native pool allocation.
   The observation hook compares every native-decompressed byte with the
   independent pinned decode. All loaded bank counts agree with the prior
   RoleDoll result; all 509 unrelated bank records remain unchanged.
5. On success original `4C61..4CC0` copies the filename and increments count.
   Original `9B45` stores the returned slot in the HeroDoll record. `FF450`
   writes it at component-object `+4+6*component`. Tests verify all other
   source record bytes and unrelated component bytes remain unchanged.
6. A second head record with the same filename reaches `4B70` but reuses slot
   zero without opening/decompressing/loading again. Repeating a record whose
   `+1E` is already populated skips `4B70` entirely and reaches `FF450` directly.
   Uppercase filename requests also reuse all three native filename-cache slots.

Missing files return virtual fopen NULL. The native loader returns failure;
`4B70` does not increment its filename count, and `9B45/FF450` retain `FFFF`
as the record/component value. Restoring the pinned virtual bytes permits a
subsequent native retry to succeed. This is tested separately for all three
assets. The optional preview diagnostic-owner pointer is null in this fixture,
so the absent-resource message-display branch is not executed.

## Adapters and guards

The preview helper subclasses the existing RoleDoll helper read-only. Additional
adapters are bounded calloc, the existing bounded CString copy/construction/
destruction semantics, and GetCurrentDirectoryA returning an explicit virtual
`C:\RoleDollOracle` directory. Original `12F550` executes and caches that result;
no game path resolver is stubbed. Virtual fopen accepts only the three qualified
paths, with optional exact virtual-root prefix, and read-only binary mode.
No host directory or file is changed, and virtual CRT file IDs are distinct
from native resource/cache slots.

The CString allocations have bounded oracle lifetime, as documented by the
existing indoor helper; MFC reference counting and heap reuse are not proved.
The inherited per-allocation, total heap, source-size, instruction/time,
stack-cleanup, RX-code and opcode-checked SEH guards remain. A temporary exact
stop hook prevents cached translation blocks from crossing `410D` or `9B66`.
Only required current-directory data pages are additionally writable. Every
successful and missing-file test closes its virtual files and restores FS:[0].

## Follow-up: Native control table and FF490

Before follow-up native work, both legacy roots were searched for `106c30`,
`2808c`, `RomDesc` and `ACT_DATA` in C++, headers, C# and Markdown, with no
matches. Broad action/table terms produced unrelated battle and evidence-task
tables; none is substituted for this current preview path.

`106C30` is a renderer-object handle lookup, not a CSV animation-action lookup.
Its native backing table is `preview+2808C`; it returns the WORD at
`this + 8C2 + 2A08*window_selector + 64*control_selector` (hex offsets).
Native `104130 -> 104160 -> 1041A0` initializes all 128 window rows and all
106 controls per row. Every one of the 13,568 handle entries initially equals
`FFFF` through original writes. The regression checks every entry; it never
accepts zero-initialized memory as a successful handle.

The prerequisite is the actual preload slot 0, identified by current
`Data2/Patch/FlowComm.csvZ` row `0,FlowGui.ROM`. The file has 14 preload rows.
The preview initialization's `418D..41F3` references that CSV, then assembles
filenames under `data3/flow/` and passes them to `4B70`. This lane parses the
hash-pinned CSV with Python's CSV parser to establish the slot-0 filename; it
does not claim execution of the complete `54720` CSV loader or all 14 preloads.

| Source | SHA-256 |
| --- | --- |
| FlowComm.csvZ | `27a0660b158d0cfcfe6afd5a01fcae91f98732d0f73efdde953b9d98fbe717e1` |
| Decoded FlowComm CSV | `ca4c48dc8606081c420973772093848f18f51d3094972e2b500c6955658c053e` |
| Data3/Flow/FlowGui.ROMZ | `2ad797d15aa6daa6562652fb69d39c9e3dbbdc108965c230c199735c8e682503` |
| Decoded FlowGui ROM | `8612c3e4953c54d236eaae7c06d78200f0f6787ee05458bc4b004b1706cea215` |

The FlowGui source is 1,445,769 bytes, decoded 2,337,977 bytes. Native `4B70`
receives the actual `.ROM` spelling, original `29820` opens `.ROMZ`, and
original `1EC0/2A1D0` produces all 26 palettes, 76 images and 105 actions.
Every decompressed byte is compared independently before native parsing.
The fixture configures the ROM pool to the actual preview `4183` 10 MiB
request before this preload. Original `27400` and `1AA10` initialize the
surface command pool and renderer pool. No window/device or presentation occurs.
Original `18940` initializes the hit-region collection, also entirely in memory.

Original `C8D4..C95E` copies the image's rectangle tables, transforms them with
bounded CopyRect/OffsetRect adapters, and creates the preview window through
`104EA0 -> 104F50 -> 1AFE0`. The resulting free window index is written by
original `C97C` to preview `+178CD4`. In this initially empty fixture it is 0;
it is not an assumed universal window selector. Unrelated control creation
for controls 0..18 is skipped. The full original `CA33..CA9C` loop creates
controls 19..30 using `583908` image records and actual rectangle inputs.
Original `106C70 -> 1AFE0` allocates each renderer object, then `106D75` writes
its returned handle into the table. Observation-only hooks record both the
source-backed arguments and these actual writes; tests check their agreement.
The caller preserves upper EAX bits when loading some WORD arguments into AX;
the regression compares selectors/type values at their native WORD width.

The four component control selectors come directly from the image WORD table
at `583424`: **22, 23, 24, 25**. Their observed renderer handles are **5, 6, 7,
8** in this bounded allocation order; other preexisting controls would change
the handle numbers. The actual `CD51..CD5B` caller loads the window selector
from `+178CD4` as the argument to `99E0`. Accounting for its original prologue,
the same argument is `[ESP+130]` at `9B66`; its saved this is `[ESP+1C]`.
The fixture supplies those two stack values from the native-created object.
Complete `9B66..9B97` executes both the original table lookup and `FF490`.

With FlowGui occupying slot 0, real head/face ROMs occupy slots 1, 2, 3 in this
test's order. The head selects control 24/handle 7; both face records select
control 23/handle 6. Repeated assignments execute lookup/setter again while
preserving the cache and avoiding any new allocation or file load. Non-created
controls and window rows return native `FFFF`, and source tampering fails closed.

Additional adapters are only the indoor helper's established single-thread
locks/rectangle semantics plus CopyRect/OffsetRect. The control-table initializer
has explicit null optional window/font-owner bindings, a real hit collection,
and a real renderer backed by FlowGui; those bindings are not a recovered full
live environment. FlowGui input/output bounds are 4 MiB. Its larger original
decompression uses a dedicated 200-million-instruction/60-second budget; the
earlier 50-million instruction budget was reached and not treated as success.
All other calls retain the inherited budgets, source hashes, exact stop checks,
stack checks, memory protections and restored SEH/lock/file state.

## Previous table-only boundary

The new continuation stops at `9B97`, after `FF490`, with real ROM-slot and
renderer-object fields installed. Next `9B97..9BA6` consumes the source component
variant through `FFA20`; after all four components the original caller invokes
`FF8E0(6)` and `FFA60`. Actual animation still requires the complete four-component
loop, native `FF3C0` component-to-renderer binding at component `+28`, and the ensuing
original action/frame/timing and surface-command consumers. This lane has not
executed that sequence, full `99E0`, all FlowComm preloads/cache-reset lifecycle,
or a graphics device. `FF490` assigns a renderer-object handle; it does not by
itself demonstrate a moving character or action playback.

No world `63DE0`, `61270`, post-`68558` actor initialization or C++ variant work
is duplicated. No new profile-to-packet mapping or gameplay rule is promoted.

## Follow-up: original binding and frame consumers

The next bounded extension is `NativePreviewFrameResources`. Both legacy roots
were searched first for the binding/consumer addresses; neither supplied the
matching current native implementation. The pinned original image remains the
implementation evidence, with the same image/asset hashes recorded above.
Shared RoleDoll, appearance, indoor and world helpers remain read-only.

The actual preview initializer at `455A..456C` reads its renderer pointer from
preview `+15E80`, then calls `FF3C0` on preview `+15E38`. The fixture supplies
the already native-initialized renderer that backs the control table. Original
`FF3C0 -> FF420` resets all four slot/handle records to `FFFF`, then writes the
renderer binding at component `+28`. No return value or successful handle is
replaced. Original `CB7B..CB95 -> FFAD0` reads the position from image WORDs
`5837E0/5837E4`; no guessed coordinates or zero-filled position is used.

The profile fields are explicit zero-selector fixture inputs, not a claim about
live character state. Original `9A0E..9A26` and `9A2C..9A69` generate the local
component block `0000000000008000`. The cache-count reset at `9A26` is deliberately
omitted: complete FlowComm preload/base-count/reset lifetime is not established
by this fixture. The eight native-generated bytes are preserved across the
independently bounded component calls. Existing real-record and control-table
consumers still run through `9B97`; `9B97..9BA6 -> FFA20` now installs the variant.

The actual caller tail `9BBB..9BD5` executes `FF8E0(6)` and `FFA60` without
replacing either function. Action 6 is the literal in the original caller,
not the obsolete action-0 assumption or a fabricated action handle. Original
`1AE20` interprets it as a valid action-array index; the three ROMs' corresponding
`ACT_DATA` identifier is 1701. Original `1BF30 -> 1C360` selects real action,
step, pool, image and palette pointers, and updates the native surface-command
records. `FFA60/1E070` consume the selected palette variant.

The regression exercises `r01w800.romz`, `r01f002.romz`, and `r02f002.romz` using
the existing head/face records. It compares native action headers and every
consumed frame event against independently decoded `ACT_DATA/ACT_STEP/ACT_POOL`
chunks. Action 6 has **7, 7, and 6 steps**, respectively. Direct original
`1C360` calls consume every step and the wrap back to step zero. Tests also
check native duration/repeat fields, pool/image/palette pointers, and actual
surface-command image/palette bindings, without reloading or allocating during
stepping. Across the three selections the native tail makes five `1BF30` calls
(the retained head is also restarted) and 25 total `1C360` calls. Observation
hooks never modify native state. No additional service adapter is introduced.

Unqualified component keys/indices fail closed. A control's preexisting FlowGui
action is not accepted as an initialized RoleDoll action: direct stepping checks
the actual bank/action pointers first. Original file, stack, SEH and lock guards
remain active.

## Exact next boundary

This proves native action initialization, direct frame advancement/wrap, and
surface-command data for a **partial head/face preview**, not visible animation.
Body and weapon component records remain native `FFFF` sentinels; neither a full
four-component `99E0` invocation nor complete preview lifecycle is claimed.
The next timing boundary is original renderer tick `1C060`, including its
`149555` clock dependency and full active-object traversal. Direct `1C360`
stepping deliberately bypasses elapsed-time scheduling. Surface commands are
populated but rasterization/presentation and an actual display are not tested.
Full FlowComm preload/cache-reset semantics and the remaining native component
records must be integrated before claiming the complete preview path. These
are explicit remaining dependencies, not successful stubbed branches.

No UI, client launch, process inspection, authentication, network, policy change,
agent, shared-helper edit, world-scene work, or E2E/playability claim occurred.

## Verification and ownership

```powershell
python -B tests/research/test_current_preview_role_resources.py -v
```

Initial loader/cache run: **7 tests passed in 21.627 seconds**. Coverage includes
native cache initialization, uncached loading, both cache levels, native record
and component writes, uppercase hits, per-asset failure/retry and state guards.
Follow-up complete regression: **11 tests passed in 44.156 seconds**, including
all native table defaults, source-backed control allocations, real-selector
`106C30 -> FF490`, repeated assignment without reallocation, and FlowComm hash
rejection. No failed assertion was waived; the initial argument comparison was
corrected to match the callee's WORD reads rather than preserved upper EAX bits.
Binding/frame extension final rerun: **14 tests passed in 69.644 seconds**,
including original source-position setup and rejection of early stepping while
the renderer object still holds its preceding FlowGui action.
Only the three new preview-lane helper/test/document files are edited. Existing
helpers, other lanes, shared runtime/session/network and CMake are untouched.
