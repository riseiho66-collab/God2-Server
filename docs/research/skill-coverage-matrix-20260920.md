# Full current-definition target coverage matrix, 2026-09-20

## Measured result

**18,816 / 18,816 target cases passed**, with zero mismatches. The denominator
is the actual pinned source's **448 definitions x all 14 actor positions x 3
explicit states**. Every definition has 42 cases run and 42 passed. Every actor
has 1,344 cases; every state has 6,272. No definition or actor was sampled away.

This is target-helper coverage, not system coverage, cast authorization, live
gameplay verification or completion of skill damage formulas. The seven test
methods audit the matrix and its failure behavior; their count is not the
gameplay coverage denominator.

The prior 4,480-case differential matrix mixed synthetic cases with 896 cases
using original definitions at actors 0 and 13. This matrix has 18,816 cases using
original definitions at actors 0 through 13: 4.2 times that total case count and
21 times its original-definition case count. This comparison describes test
inputs, not a multiplier on code coverage or system completeness.

## Owned paths

Only these new paths were written under
`C:/Users/risei/Desktop/God2/God2-Server`:

- `tools/strike_lab/skill_coverage_matrix.py`
- `tests/research/test_skill_coverage_matrix.py`
- `docs/research/skill-coverage-matrix-20260920.md`
- `artifacts/research/skill-coverage-matrix-20260920.json`

Existing fixture, model, runtime, DB, CMake and status files were not edited.
No archives, subagents, desktop automation, database operations, external
servers or game/server processes were used. The only subprocess executed by the
matrix is the existing formal target test executable with `--batch`.

## Inputs and provenance

| Input | SHA-256 |
| --- | --- |
| Current sibling `God2/Data2/Fight/Spg/cbspec2.bin` | `7676acd93f164d071f7681a3fe74de94d65892759dbf2e69e3c0f748423d2f51` |
| `artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin` | `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763` |
| `build/tests/Release/native-skill-targeting.exe` | `3cd5de7c3df0a5261de10dfacfc3a9680899b733847c79aa1b484d8e2ec4a17c` |

The source is 112,660 bytes, version `1.03`. Its group headers contain
`[121,129,87,111]`, summing to 448 populated definitions. The runner discovers
these through the current identity decoder; tests independently enumerate group
counts, direct record offsets and raw identity bytes. The image is pinned before
execution. The executable hash is recorded and checked again after execution.
This validates that exact existing binary; no rebuild or claim of binary/source
build equivalence is made.

Each definition in the artifact has its `(kind,id)`, complete source SHA-256,
exact source offset, 110-byte record length and record SHA-256. Raw fields
`identifier`, `kind`, `word_3e`, `reach_44`, `mode_45` remain distinguishable from
results and from formula evidence.

## Three explicit states

All states have saved DWORD masks `(89ABCDEF,76543210)` to detect unintended
overwrite or loss of high bits. Actor positions are zero-based `0..13`.

| State | Current masks | Type-0 entity states, 28 slots |
| --- | --- | --- |
| `empty` | `(0000,0000)` | All pointers null |
| `full` | `(3FFF,3FFF)` | All pointers present; each signed WORD is zero |
| `sparse_signed` | `(2001,0420)` | `(null,-32768,-1,0,32767,null,-1)` repeated four times |

The sparse fixture distinguishes null pointers, negative WORDs and nonnegative
WORDs while leaving holes in the masks. These are explicit synthetic inputs;
the signed WORDs are not labelled HP, life state, damage or server authority.
The exact arrays are embedded in the JSON rather than hidden behind state names.

## Native and formal comparison

`NativeTargetOracle` composes an instance of the existing
`CurrentSkillTargetSetupTests` fixture and calls only its fixture methods. It
does not inherit a test suite, call test methods, invoke test discovery or run the
inherited selection suite. One native VM is reused for the whole matrix.

For each definition, original instructions at RVA `115571` are executed to the
known gate exits `11557F` or `11559A`. For each actor/state case,
`install_target` resets the snapshot and `target_invoke` runs original `11EE90`
with its complete helper calls. Both result masks and saved masks/stored mode
are read from native memory. Full context and battle snapshots are checked for
unintended changes using those actual outputs. No Python targeting formula is
used to manufacture expected output.

For modes 1 through 17, original `11EAD0` also supplies its return DWORD and out
flag. Mode zero is unqualified for that helper, so the artifact records `-1,-1`
for the omitted setup result. The target-mask helper still runs for these cases.
Closed code ranges, permitted write ranges, stop addresses and stack checks
come from the existing fixture. Each invocation has a 20,000-instruction cap;
the CLI checks its overall deadline between cases. No native instructions or
calls are patched or replaced.

The formal executable receives all 18,816 cases in one bounded batch. Each input
has 38 integers; `32768` represents a null entity pointer and cannot be confused
with a signed WORD value. The eight compared output fields are:

```text
mask_0 mask_1 saved_mask_0 saved_mask_1 stored_mode
setup_value setup_flag passes_kind_gate
```

Every case retains both eight-field result vectors, its actor/state key, actual
entity-lookup execution flag and comparison result. A wrong row count or malformed
batch fails. A mismatch records a failed case and makes the CLI exit nonzero.
The shared gate result is measured natively once per definition, then compared
with the formal result in every case.

## Coverage breakdown

| Recovered target dispatch category | Definitions | Cases run/pass |
| --- | ---: | ---: |
| Reachable rows | 362 | 15,204 / 15,204 |
| Row template 6 | 16 | 672 / 672 |
| Row template 7 | 4 | 168 / 168 |
| Row template 15 | 17 | 714 / 714 |
| Fixed mask `001F` | 4 | 168 / 168 |
| Fixed mask `0400` | 17 | 714 / 714 |
| Actor only | 20 | 840 / 840 |
| Actor only, save original masks | 1 | 42 / 42 |
| Clear masks | 7 | 294 / 294 |
| **Total** | **448** | **18,816 / 18,816** |

These categories classify the recovered mode dispatch; they are not a claim of
instruction-level branch coverage. Raw mode values remain in every definition.
No current definition uses the side-zero-only mode-12 category, so this matrix
does not claim coverage for it or for all possible synthetic mode bytes.

- 18,522 cases execute qualified native setup parameters.
- 294 cases belong to seven mode-zero definitions and leave setup unqualified.
- 84 definitions fail the native kind gate. Their 3,528 direct-helper cases remain
  included, explicitly without claiming the caller would permit those casts.
- 126 cases execute the special entity lookup for kind 3, IDs 8, 9 and 10.
- There are 448 native gate invocations, 18,816 target-helper invocations and
  18,522 setup invocations: 37,786 bounded native invocations in one VM.

## Formula evidence remains separate

| Authoritative server rule | Definitions verified | Definitions unverified |
| --- | ---: | ---: |
| Damage | 0 | 448 |
| Hit | 0 | 448 |
| Crit | 0 | 448 |
| Five-element coefficients | 0 | 448 |
| Resource cost | 0 | 448 |

All 2,240 definition/rule pairs remain unverified. Each definition's separate
`formula_evidence` block retains null authoritative formula and coefficients,
with runtime enablement false. Target reach, mode, masks, setup values and kind
gate results are never relabelled as damage/hit/crit multipliers or resource costs.
This matrix neither recovers nor evaluates a server formula. It cannot establish
ownership, resource sufficiency, deduction timing, damage randomness or cast
eligibility. The earlier bounded formula-evidence report remains separate.

## Actual commands, timing and reproducibility

Run from `C:/Users/risei/Desktop/God2/God2-Server`:

```powershell
python -B -m tools.strike_lab.skill_coverage_matrix --output artifacts/research/skill-coverage-matrix-20260920.json --timeout-seconds 300
python -B -m unittest discover -s tests/research -p test_skill_coverage_matrix.py -v
Get-FileHash -Algorithm SHA256 -LiteralPath artifacts/research/skill-coverage-matrix-20260920.json,build/tests/Release/native-skill-targeting.exe
```

The full native/formal matrix was run **once**, exit 0. Reported computation
time was **14.757224 seconds**, comprising **14.402542 seconds** for native cases
and **0.224793 seconds** for the formal batch, plus loading/validation overhead.
This timing excludes final JSON serialization and artifact writing. The formal
subprocess has a 30-second timeout, additionally bounded by the remaining matrix
deadline. The configured overall deadline was 300 seconds.

The audit suite passed **7 tests in 1.944 seconds**, exit 0, no skips. It consumes
the generated artifact and pinned source, not a second native matrix. It checks
every denominator/key and stored native/formal comparison, canonical JSON,
duplicate JSON object keys, omitted/duplicate definitions and cases, wrong actor
or state, inflated counts, and malformed formal batch output. A counterfactual
flips one formal result bit: retaining a green result is rejected; recording the
failure yields exactly 18,815 passes and one failure and rejects overall success.
Each of the five formula categories also has a coefficient-promotion rejection.

The generated artifact is **9,998,757 bytes**, SHA-256:
`9f990048131dc523e1d4d38ec9d35cfeaf4cbf941be894d1a7487b8a30510f0d`.
`Get-FileHash` independently matched this and the executable hash above.

The JSON contains no timestamp, elapsed timing or machine-specific absolute path.
Ordering, state inputs and serialization are fixed; the tests verify byte-for-byte
canonical serialization. Timings/progress go to stderr separately. With `--output`,
stdout contains the summary and report hash; without it, stdout contains the full
report. Output writes are restricted to the authorized artifact path. The suite
fails if the artifact is missing, incomplete or no longer matches the executable;
it does not silently skip or regenerate evidence.
