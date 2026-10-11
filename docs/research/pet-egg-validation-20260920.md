# Pet / Egg Evidence Boundary Validation, 2026-09-20

This focused regression joins existing current-native helpers at their declared
boundaries. It adds no gameplay rule, hatch result, server authority, runtime
change, database mutation, or CMake registration. Only these files are added:

- `tests/research/test_pet_egg_evidence_boundary.py`
- `docs/research/pet-egg-validation-20260920.md`

## Evidence and Execution

Client root: `C:/Users/risei/Desktop/God2/God2`.
Native image, relative to the server workspace:
`artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`.
Required SHA-256:
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.

The existing extractors hash-qualify current `Data2/Patch/Comm/gamedata.csvZ`
and the seven growth sources, including `NewCombatPet_QualityStar.csvZ`.
Gamedata SHA-256:
`70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731`.
QualityStar decoded SHA-256:
`fde6e5b716e710d39b1b706efabd1cfc9d58ef9fc353033d709b38b4bc1a5fbf`.

Fixtures use offline Unicorn execution of unchanged native instructions and a
read-only CLI subprocess. No desktop, client process, network, external server,
child agent, database, shared build, or evidence-output CLI option is used.
No retired archive contents are read. The initial broad filename inventory
listed archive paths; these are not inputs or evidence. Subsequent inspection
was restricted to the named tools, tests, and current research reports.

Existing fixture methods are reused by composition from
`test_current_pet_incubation_guard` and `test_current_companion_state`; their
test classes are not inherited/discovered. In particular, the historical
frame test and its historical record are not executed or used. The new S2C31
record is an explicitly synthetic byte probe.

## Additional Regressions and Findings

1. **Egg presence is not request eligibility or ownership.** Current source
   identities 9324, 9325, 9427, and 9433 are staged through the existing native
   S2C41 consumer at slot 45. The egg guard returns 1, whereas the general item
   request caller at RVA `96390` returns without appending any request. Complete
   fixture-region snapshots remain unchanged across guard/request execution.
   After S2C41 clears the inventory count and identity, the egg presence guard
   still returns 1. It validates its arguments and catalog presence, not
   possession. This does not establish an egg-specific request protocol.

2. **Catalog loss is not cached success.** In one fixture, the existing pointer
   for 9325 is retained, cleared, then restored. The guard changes from success
   to assertion line `58B` (hex), then back to success. Invalid slot 30 reaches
   line `57A` throughout. Pointer edits are synthetic host fixture setup;
   definition memory remains read-only to native code. The index points to
   exact current row bytes but is not produced by the original catalog loader.

3. **Copied instance bits retain display provenance.** Forty synthetic records
   cover both dispatches, slots 0/29/42/43, and five packed DWORD patterns.
   The observed DWORD copied at `98E2B` to store `+0C`, then at `87416` to UI
   record `+0C`, is supplied to the existing progression helper in both admitted
   modes (80 display cases). Quality bits 20..23 and Star bits 16..19 select
   literal WORDs from byte/hash-checked QualityStar rows. Tests verify exact
   write and table-read PCs, addresses, widths, and values. This composition
   passes an observed value between separate slices; intervening metadata/UI
   calls are not executed and their state preservation is not asserted.

4. **Rejected/intercepted updates do not prove a fresh instance.** After a
   successful nonzero UI copy, slots 50/255 stop at `98FBD` with no writes;
   slots 38/41 with auxiliary state 1 stop at `98E05` before an unexecuted call.
   Neither changes the earlier UI record. Negative signed selectors and missing
   event bit 0 also preserve it at the entry gate. Thus residual UI bytes are
   not evidence of a new accepted message. The packet helper re-poisons its
   store before each probe, so this test makes no claim about preserved store
   history. A null UI owner faults; restoring the owner and sending a different
   valid probe restores the expected copy. Interception is an execution boundary,
   not proof of permanent native rejection.

5. **S2C31 respects declared rows, not residual bytes.** A matching signed key
   in a second allocated row is invisible when the declared count is one.
   Changing the count to two exposes it to the original dispatcher/scalar
   consumer. A truncated declared second row is rejected by the Python
   projection without input mutation; the valid record still works afterward.
   The malformed state is not passed into native code, so this is not a claim
   of native memory safety or server validation. Positive execution stops
   before `AA2AF` refresh effects; no match executes to the dispatcher join.

6. **Valid syntax cannot replace qualified growth provenance.** Changing a
   QualityStar literal from 15 to 16 still passes structural parsing, but the
   native progression constructor rejects its decoded hash. Unchanged bytes
   subsequently produce the original display value 15.

7. **Serialization cannot silently promote tooltip claims.** All 55 serialized
   EGG/SPP entries retain an exact unknown-contract set with null values and
   `runtime_eligible=false`. Exact entry keys also catch an added hatch result
   or new top-level default. Tooltip hours remain 9324=1 and 9325=20; 9426
   exists without 9326. None supplies an outcome relation or authoritative timer.

8. **Native row verification cannot promote growth rules.** The CLI subprocess
   executes `recover_companion_growth --native-image ... --summary` without an
   output path. It must report bounded original row verification while retaining
   false gameplay/formula verification. For both battle pets and deities,
   growth rate, base value, upgrade formula, and EXP thresholds must remain
   unknown, null, ineligible, and accompanied by a missing-evidence description.

## Missing Native Evidence

- Egg-specific request and result handling, ownership/eligibility conditions,
  costs and inventory transaction behavior beyond the demonstrated guard.
- Timer start, clock units, online/offline progress, pause/reset/completion,
  and their binding to a real egg instance. Tooltip hours do not prove these.
- RNG/probability calculation, success/failure handling, and an observed
  egg-to-result distribution. No item-ID arithmetic or fabricated hatch result
  can fill this gap.
- The upstream construction of opcode `3B` message DWORD `+11` (hex), actual
  instance transitions, and their relation to server-side growth values.
- Original growth coefficients/units and consumers; initial-stat instance
  binding; level-transition arithmetic, rounding, caps and allocation; EXP
  tables or verified threshold arithmetic. Display arguments are insufficient.
- Full execution across the skipped metadata/UI calls, actual packet transport
  and live gameplay acceptance. These bounded probes do not close those gaps.

The tests lock the inspected research evidence boundaries. They do not certify
all server runtime consumers or provide a general schema validator for arbitrary
future claim fields.

## Commands and Results

Working directory: `C:/Users/risei/Desktop/God2/God2-Server`.

```powershell
python -B -m unittest discover -s tests/research -p test_pet_egg_evidence_boundary.py -v
```

Initial run: 8 tests, 7 passed, 1 error, exit 1, 16.141 seconds. The new state
fixture passed a `bytearray` to the existing Unicorn helper, whose `mem_write`
requires `bytes`. Only the new test was corrected to supply immutable bytes.
Final rerun: **8/8 passed, no skips, exit 0, 16.828 seconds**. The exact same
command was rerun after the fixture correction. No production helper changed.

The CLI black-box command executed inside the test is equivalent to:

```powershell
python -B -m tools.strike_lab.recover_companion_growth --client-root C:/Users/risei/Desktop/God2/God2 --native-image artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin --summary
```

Its output is captured in memory and checked; no artifact is written. The
initial and final runs confirmed exit 0 and all unknown-contract assertions.
`git status --short --untracked-files=normal` could not supply a diff because
this workspace is not a Git repository (exit 1). Only the two paths listed
above were patched; no shared runtime/status/build files were edited.
