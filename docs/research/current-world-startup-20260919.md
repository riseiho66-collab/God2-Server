# Complete Native Startup And Scene Entry, 2026-09-19

## Result And Boundary

The offline lab now executes the original startup resource sequence continuously
from RVA `64CB6` to boundary `64FE2`, then the complete original scene-entry
function `100180` through its real `RET 8` epilogue. Four regression tests passed
in 237.660 seconds. No client code patch, forced scene branch, invented success
return, or replacement game callee was used to cross the prior effect-manager
binding failure.

This is NOT live current-client world acceptance. Unicorn supplies a bounded
process/device environment; the retained 36-byte indoor scene body is a fixture,
not authority for original start-area policy or character values. No new formal
world packet producer, gameplay formula or server response was established here.

## Current Inputs And Original Bindings

Image: `artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`,
SHA256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`,
base VA `400000`. Addresses below are RVAs unless explicitly identified as VM
addresses. Only current pinned client sources are inputs; retired corpora are not.

`current_world_startup_assets.py` qualifies all seven paths from the original
FieldComm3 table. `NativeWorldUIResource` executes that original reader; its
65 inline records of stride `108` are copied into a fresh lab allocation. These
records have inline strings, not pointers needing rebasing. The actual startup
uses that table pointer at `WORLD+A8D50D0`.

| FieldComm3 ID | Original asset | Startup load call |
| --- | --- | --- |
| 2 | Data3/Flow/DTitleGui.ROM | 64CE1 |
| 3 | Data3/Flow/StateEft.ROM | 64D5D |
| 10 | Data3/Fight/Gui/Eft2_8302.ROM | 64D97 |
| 12 | Data3/Flow/motion.ROM | 64DEB |
| 8 | Data3/Flow/gcall.ROM | 64E36 |
| 9 | Data3/Flow/speceff2.ROM | 64EAD |
| 46 | Data3/Flow/NameShadow.ROMZ | 64F16 |

The conditional speceff2 allocation runs on the native fresh-owner branch.
Both banks parse each original resource. Actual next/saved bank counts are seven;
the native checkpoint and both display bindings execute. Handles in the test
are allocator results, not guessed constants fed into game code. The native
effect-manager bind `10DC70` receives the actual gcall handle and renderer;
`10DC90` writes the original invalid-handle reset values. The original component
bind `FF3C0` also executes.

The additional secondary display is constructed by `107F30` at VM address
`WORLD+ABA32E0`. Its adjacent role-pool prefix is checked for unintended writes.
The existing native primary pool has 4096 records and 3072 rectangle slots.

## Explicit Lab Adaptations

- Shared bank helpers now expose `bank_capacity`, retaining the old 4 MiB
  default. This full-startup subclass requests 16 MiB per bank for the seven
  startup resources plus actor assets. This is not recovered memory policy.
- Device dimensions are explicit `800x600` fixture inputs. No real graphics
  device, presentation or rendered screenshot is claimed.
- Startup CRT `sprintf("%s", ...)` is admitted only at pinned startup return
  sites, with a bounded source. Actor-name CRT `sscanf("%s", ...)` is admitted
  only at four known return sites, with ASCII tokens up to 15 bytes. Unsupported
  formats and names fail closed. The adapter returns real assignment/EOF
  semantics; it does not replace the game name-processing functions.
- Startup has an explicit instruction/time budget and is not restarted from
  partially executed state. Fresh-start and single-scene guards reject reuse.

Initial failures were actual lab gaps: a missing `%s` CRT boundary, then the
unbound effect manager when only the title asset was loaded, and an unmapped
FieldComm3 pointer field while assembling the full startup environment. They
were fixed at their actual dependency locations before the successful run.

## Regression Evidence

```powershell
python -B -m unittest tests.research.test_current_world_startup -v
```

Four tests cover all fourteen bank parses, exact decoded sizes, native checkpoint,
both display bindings, owner and effect-manager construction, original handle
stores/reset, and the full scene function. The latter passes actual actor-label,
map, music and camera paths, returns to the call sentinel with `ESP=SP+12`, and
restores the SEH sentinel. The title record is allocated inside the real native
pool. The retained indoor fixture produces camera `(840,240)`; music resolution
runs and the actual absent-device branch returns `0`, not fabricated playback.
The observed final scene EAX was 17 and is not interpreted as a boolean result.

The seven-asset source suite was independently rerun: 6/6 in 36.022 seconds.
The next acceptance boundary is live original-client/formal-server world entry,
plus original authoritative scene/body construction. Neither is promoted by
these offline results.
