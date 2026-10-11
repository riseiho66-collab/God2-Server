# Pet / Egg Whole-Source Coverage Matrix, 2026-09-20

This deliverable measures current source denominators and bounded native
behavior. It does not claim a complete pet gameplay system. Test-function
counts are not used as the gameplay coverage denominator.

Owned paths, relative to `C:/Users/risei/Desktop/God2/God2-Server`:

- `tools/strike_lab/pet_egg_coverage_matrix.py`
- `tests/research/test_pet_egg_coverage_matrix.py`
- `docs/research/pet-egg-coverage-matrix-20260920.md`
- `artifacts/research/pet-egg-coverage-matrix-20260920.json`

No existing file was edited for this task. No DB, CMake, shared runtime/status,
desktop, live client, external server, archive, or child-agent work was used.
The earlier eight-test deliverable is unchanged and is not counted here.

## Source Denominators

Inputs are the current sibling client `C:/Users/risei/Desktop/God2/God2` and the
existing qualified current-image capture:
`artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`.
The image SHA-256 is
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.

The report's `source_manifests` retains compressed/decoded SHA-256 and sizes for
all seven files qualified by `recover_companion_growth`. Its physical ledger
covers every decoded byte, retaining each physical row's 1-based line, exact
byte offset, length, and SHA-256. CR/CRLF/LF bytes are included in those hashes.
Growth groups reference those ledger lines; they do not silently count unrelated
rows in gamedata/message as proven growth behavior.

| Source file under Data2/Patch/Comm | Physical rows |
| --- | ---: |
| gamedata.csvZ | 29,672 |
| message.csvZ | 3,106 |
| NewCombatPet_Category.csvZ | 469 |
| NewCombatPet_QualityStar.csvZ | 7 |
| NewCombatPet_AllInnate.csvZ | 149 |
| NewCombatPet_Innate.csvZ | 45 |
| PetDesignDesc.csvZ | 386 |
| **Total physical rows** | **33,834** |

| Complete growth group | Data records |
| --- | ---: |
| ItemType | 46 |
| GOD | 34 |
| PET | 147 |
| COM | 2,070 |
| NCP | 1,165 |
| GodLevel | 4 |
| FightPetSkill | 254 |
| NewFightPet2Skill | 255 |
| CategoryNum | 16 |
| NewCombatPet_Category | 464 |
| NewCombatPet_AllInnate | 144 |
| NewCombatPet_Innate | 41 |
| PetDesignDesc | 381 |
| NewCombatPet_QualityStar | 2 |
| **Total growth data records** | **5,023** |

These are all records of the existing extractor's nine gamedata growth groups
and five auxiliary tables. The 17 selected text records used by that extractor
are reported separately with ledger references. All other physical rows in the
seven files remain accounted for, without inventing a semantic classification.
Category's literal declaration 469 and actual 464 data records are preserved;
the report does not create five missing records.

Native row loading is independently executed for **470 records**: four
GodLevel title rows, 464 Category rows, and two QualityStar rows containing
32 WORD values. Category consumption covers columns 0..8, not its opaque tail.
The other growth rows have source provenance, not native gameplay execution.

## Egg Definitions and Guard

Section parsing discovers **27 EGG + 28 SPP = 55 entries**. Every entry joins
uniquely to the current item extractor's **16,127-definition** denominator.
Qualification checks identity, section, source line, every raw field, and the
definition's newline-stripped row hash against the exact egg source bytes.
The two hash conventions are retained explicitly. Results: **55 joined, zero
unjoined**. Missing, ambiguous, or byte-mismatched joins produce explicit
`unjoined` reasons; their lookup pointers remain zero.

The original egg guard `D6C80 -> D6C40 -> 59A60` executes for every entry at
every byte slot 0..255: **14,080 cases**, with per-entry case/return/assertion
counts and observed lookup-read addresses/widths. Each qualified entry has
31 presence successes (0..29 and 45) and 225 slot assertions. There are also
110 pointer-removal/restoration cases, all 145 absent IDs within 9301..9500,
and four outside-range IDs. Assertion execution stops at `2C70`; it is not
converted into success. The whole lane preserves non-stack state.

This is a **source-qualified presence index**, not a reconstructed native
metadata structure. Pointers refer to exact source row bytes only after the
join; `59A60` reads the index pointer and does not dereference the row. A hook
fails the run if the source bytes are dereferenced as metadata. Native catalog
allocation/loading/layout remains explicitly unverified. No fabricated flag,
category, native item structure, or game-callee return is supplied.

Native presence still does not establish possession, egg-specific request
eligibility, inventory consumption, incubation, or a hatch transaction. Source
flags and tooltip claims are separately retained as source fields. Every egg
entry remains runtime-ineligible with null unproved rules.

## Instance and Display Matrix

The instance lane reuses one `NativeInstance` VM. For every slot 0..49 it runs
both native dispatches, auxiliary states 0 and 1, and 36 distinct DWORD patterns:
zero, all-one, alternating A5/5A, and each of the 32 basis bits. This gives
**7,200 in-store cases**. Slots 50..255 each run both dispatches and auxiliary
states with one additional mixed packed value: **824 rejection cases**.
Coverage is **8,024 instance cases**, with every coordinate and all 256 per-slot
counts retained, not only aggregate totals or hashes.

| Observed instance outcome | Count |
| --- | ---: |
| Native packet-to-store copy to stop 98E2D | 6,912 |
| Auxiliary-state interception before call at 98E05 | 288 |
| Invalid-slot rejection at 98FBD | 824 |
| Subsequent UI selection/copy to 87430 | 4,608 |
| Subsequent blocked UI selection at 873B3, prior UI preserved | 2,304 |
| Separate UI entry-gate cases | 212 |

Interception is a stop before an unexecuted call, not proof of permanent native
rejection. No UI selection is attempted for rejected/intercepted packet cases.
Each packet-only slice preserves the previous 24-byte UI record. Unlike the
existing `ui_copy` convenience method, the new small selection adapter retains
UI memory between cases and uses the existing guarded `run` to verify blocked
selection preserves it. Successful selections copy the exact source record,
adjacent fields, and packed DWORD; neighboring bytes remain unchanged.
The existing packet helper re-poisons slot storage each time. This is not a
claim about historical slot-store persistence.

The display lane reuses one `NativeProgression` VM and executes all **16 x 16
Quality/Star pairs x two modes x two unrelated-bit patterns = 1,024 cases**.
Every returned index/value and exact table-read PC/address/WORD width is checked
against current QualityStar rows 5 and 7. Sixteen display-gate cases distinguish
integer sum equal to one from truthiness or byte overflow. This is display
argument selection; formatting and intervening UI calls are not executed.

## Rules That Remain Unknown

`unknown_rules` keeps growth formula, EXP thresholds, hatch probability,
hatch-result distribution, incubation timer, and transaction rules null.
Both companion families retain the existing null growth-rate/base-value/
upgrade/EXP contracts. Native row verification retains false gameplay/formula
verification. An observed zero display WORD is not an unknown rule default.

Still missing: native item metadata loading; egg-specific request/result and
ownership/cost/consumption transaction paths; timer clock, start/pause/reset
and offline behavior; RNG and outcome distribution; construction of incoming
opcode 3B packed values; initial stats, growth coefficients, level arithmetic,
rounding/caps, and EXP thresholds. Whole-source accounting does not close these
native evidence gaps or prove complete gameplay.

## Bounds and Defect Checks

Egg and instance probes use 1,000/300 instruction limits, native-code
allowlists, exact stops, and 120-second lane deadlines. The new instance
subclass only changes execution scheduling; it retains the shared helper's
read/write hooks, copy checks, and canaries. Display and row helpers retain
their existing one-second per-call timeouts and instruction limits. The CLI
verification subprocess has a 300-second timeout. No shared helper was edited.

Tests check exact source and case identities, not only counts. Injected defects
include growth-row omission with adjusted totals, duplicate physical/egg rows,
corrupted joins, invalid-slot success, changed stale UI, duplicated display
pairs, wrong table values, and invented timer/probability/native-formula claims.
Additional native tests prove unjoined records receive no fabricated pointers
and the optimized runner still rejects unqualified code, writes and images.

## Reproduction and Results

Run from `C:/Users/risei/Desktop/God2/God2-Server`:

```powershell
python -B -m tools.strike_lab.pet_egg_coverage_matrix --output artifacts/research/pet-egg-coverage-matrix-20260920.json
python -B -m unittest discover -s tests/research -p test_pet_egg_coverage_matrix.py -v
```

Full matrix generation: **exit 0, 49.726 seconds**, 12,427,189 bytes.
Artifact SHA-256:
`4e8a7dfe731115773deedfa6d8db94059d21dace384d7078d3e404c52b4f062a`.
Test suite: **10/10 passed, no skips, exit 0, 53.415 seconds**, including full
matrix reexecution and byte-identical artifact verification. The ten test
functions check the enumerated source/native matrix and injected defects;
they are not a claim of ten gameplay features or complete system coverage.

The CLI test reruns the entire matrix with the following command and requires
byte-identical JSON; its duration is included in the suite time:

```powershell
python -B -m tools.strike_lab.pet_egg_coverage_matrix --output artifacts/research/pet-egg-coverage-matrix-20260920.json --check
```

The artifact excludes time, timestamps, and absolute workspace paths from its
content; elapsed time appears only in the CLI summary. An initial execution
using a watchdog thread per tiny egg/instance slice was stopped before artifact
creation (exit 1); the bounded scheduling adjustment above produced the complete
run. There was no result promotion or missing-case suppression to shorten it.
