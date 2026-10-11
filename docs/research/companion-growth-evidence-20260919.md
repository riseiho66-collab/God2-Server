# Current Original Companion Growth Evidence, 2026-09-19

## Outcome and Authority

Delivered a runnable, deterministic, source-hashed extraction of **current
original-client records only**, plus bounded execution of original table-row
consumers. Exact battle-pet/deity growth formulas have **not** been recovered.
Growth rate, base value, upgrade formula and experience thresholds are separate
unknown contracts for each family: `status: unknown`, `value: null`,
`runtime_eligible: false`. An explicit source `0` is retained as `0`; absent or
unproven values are never filled with zero.

Only these new files were written:

- `tools/strike_lab/recover_companion_growth.py`
- `tests/research/test_recover_companion_growth.py`
- `docs/research/companion-growth-evidence-20260919.md`

The owner's final current-original-only directive superseded the earlier request
to consult historical corpora. Those files are RETIRED even if physically
present. No further reads occurred after that directive. Prior observations of
historical hardcoded stat defaults and growth rules are rejected historical
context, not evidence or dependencies of this deliverable. Their values and
formulas are not imported. This work does not certify server-wide runtime data.

## Reproduction

Working directory: `C:/Users/risei/Desktop/God2/God2-Server`.

Exact tested suite command:

```powershell
python -B -m unittest tests.research.test_recover_companion_growth -v
```

Result: **16 tests passed in 17.914 seconds**, exit 0. No skipped tests.

Exact tested standalone native extraction command:

```powershell
python -B -m tools.strike_lab.recover_companion_growth --client-root C:/Users/risei/Desktop/God2/God2 --native-image artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin --summary
```

Result: exit 0, seven source files qualified, 4 title rows, 464 category rows,
and 32 quality/star scalar values verified through bounded native execution.
Canonical full-result JSON SHA-256:
`ec260501dad3bf02e856ce1eace5f358b3f41de19af8925d1803f6b9d1de56c9`.
This digest includes the native result and adapter hash, not just the summary.

Omitting `--native-image` requires only the current client root and the existing
Python extraction helpers. The suite also tested this read-only CLI invocation:

```powershell
python -B -m tools.strike_lab.recover_companion_growth --client-root C:/Users/risei/Desktop/God2/God2 --summary
```

Without `--summary`, full JSON is printed. Optional `--output PATH` writes it;
`--output PATH --check` rebuilds and compares without writing. Outputs inside the
client root or overwriting the native image are rejected. No JSON artifact was
written during this task. `-B` avoids bytecode writes.

## Source Records

Every source is checked against both its compressed and decoded SHA-256 before
extraction. Every retained record has its original bytes in hex, SHA-256,
one-based physical line, decoded byte offset, positional field bytes, and CP950
display text. LF splitting preserves CR and CR CR LF. Display decoding does not
repair undecodable bytes. The output contains both raw and decoded file sizes
and hashes. Source changes fail closed rather than silently receiving old claims.

All paths below are relative to `C:/Users/risei/Desktop/God2/God2`:

| File under `Data2/Patch/Comm/` | Compressed SHA-256 |
| --- | --- |
| `gamedata.csvZ` | `70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731` |
| `message.csvZ` | `5cd34cce66feae96d947cd45e32984765ce625673c0fb19c73cb63d7d9178598` |
| `NewCombatPet_Category.csvZ` | `80c2b7d366d2ef0264df78f20de1b20fa21e14f6592f56676b090f83ddc064c6` |
| `NewCombatPet_QualityStar.csvZ` | `52b414716947b4982d74c7da4166f35f4dd1b8e2cba27265aa3f854a2ba8756e` |
| `NewCombatPet_AllInnate.csvZ` | `1a33373f44cb768acbfdb23d635aaf9ff408cfa47e2c62924e324519e8c3dee1` |
| `NewCombatPet_Innate.csvZ` | `3a47e93cb43113fcd1bf679210caa8959e9db5b0e7778f3395dab70a4eae12df` |
| `PetDesignDesc.csvZ` | `1fbf0c5bba7408b92a72f7386924bf0dde9d1baf45bfaf2ed835565bc429eef6` |

GameData sections retained in full: ItemType 46, GOD 34, PET 147, COM 2070,
NCP 1165, GodLevel 4, FightPetSkill 254, NewFightPet2Skill 255, CategoryNum 16.
GOD rows have 6 fields, PET 30, COM 32, NCP 36. Numeric tails and empty fields
remain raw; no skill-unlock, stat, rate, or requirement semantics are assigned.
ItemType label rows are retained as source labels, with `runtime_subtype: null`.
PET is not promoted to battle-pet status from a historical name.

Auxiliary extraction retains complete files, including headers: 464 category
records, 144 innate definitions, 41 innate-pool records, 381 design options,
and two quality/star rows with 16 values each. These counts do not establish
runtime effects or a template-to-category/innate/skill relationship.

### GodLevel

GameData physical lines 21165-21168 are these exact title/code pairs:

| CP950 title bytes | Code |
| --- | --- |
| `a470a550a6ec` | `1` |
| `a5bfa550a6ec` | `2` |
| `b16aa550a6ec` | `3` |
| `bbf4a550a6ec` | `4` |

These are title strings and codes, not an EXP-threshold series. No rate, initial
stat, level cap or upgrade arithmetic follows from the section name.

### Category and Quality Data

`NewCombatPet_Category.csvZ` line 5 literally declares `CategoryDetailNum,469`.
Lines 6-469 contain **464** data rows, ordered as groups 1-29 and indices 0-15.
The extractor reports the mismatch explicitly. It neither repairs the declaration
nor invents five rows. This is a source observation, not proof of how the full
loader handles the count and EOF.

Every row has 12 columns. Column 10 is literally `Base100_Index37` in all 464
rows. No resolved base-stat table or coefficients for this token were recovered.
Columns 3-8 contain Y/N tokens; column 9 and column 11 are retained verbatim.
They are not promoted to probabilities, growth coefficients or eligibility rules.

`NewCombatPet_QualityStar.csvZ` has literal labels Lv0-Lv15 on line 3:

```text
QualityValue, line 5: 0,15,30,45,75,95,115,135,175,200,225,250,300,330,360,390
StarValue,    line 7: 0,30,60,90,150,190,230,270,350,400,450,500,600,660,720,780
```

These values are verified as table tokens and native WORD stores. Their use in
stat calculations, units, scaling and rounding remains unknown. No extrapolation
or formula is inferred from their numeric pattern.

### Text Only

The artifact separately labels every selected message/item record
`source_text_only`, `runtime_verified: false`, `runtime_eligible: false`:

- SystemMessage 845, 860, 861: deity cap-release and companion level-up notices.
- SystemMessage 1309-1316: A-D growth-curve descriptions, including auction forms.
- ProgramMsg 911 and 1051: growth-form and growth-allocation display prompts.
- SPI 6254: growth-curve identification item description, GameData line 8770.
- MIS02 16542, 16762, 16763: experience-item descriptions at lines 14330, 14548,
  14549, including textual excess-experience statements.

PetDesignDesc group 6, lines 136-146, also retains the source growth-allocation
display options. Textual stat bonuses, prices, curve labels, EXP amounts and
overflow wording are not runtime verification of any transaction or formula.

## Bounded Native Verification

Mapped current-client image:
`artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`.
SHA-256: `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
Image base is `00400000`; the following offsets are hexadecimal RVAs.

| Current source | Static dispatch call -> loader | Executed row interval, stop exclusive |
| --- | --- | --- |
| GodLevel | `566CD -> 5A880` | `5A8A4..5A8DD` |
| CategoryDetailNum | `56B01 -> 5C640` | `5C6A6..5C9B5` |
| QualityValue | `56B47 -> 5CA70` | `5CA92..5CAAF` |
| StarValue | `56B8D -> 5CAD0` | `5CAF2..5CB0F` |

String-address operands, tag bytes and relative calls are checked. These dispatch
references are **static evidence**; the dispatcher and complete loaders were
not executed. Each source row runs through original tokenizer `51BE0`, original
string/numeric accessors, and the corresponding row interval. Decoded native
inputs are independently hash-checked before any execution.

The existing `NativeNpcResources._crt` decimal adapter is reused solely for
CRT `%d` sscanf at `1480B4`, accepting only return caller `51BC9`.
Its resource/NPC constructor is not called. All tokenizer, accessor and row
instructions are unchanged. Adapter source SHA-256:
`6cff27ef65b7c11a71a87c7d9ea1d79c0ad9b163e6da66058507067aea3191d1`.
Unicorn is loaded from the existing `artifacts/tooling/crypto-oracle-python`.

Verified current-row contracts:

- GodLevel copies column 0 into `table + D2ACA + (code - 1)*94` for the four
  original codes 1-4. Unwritten bytes retain the supplied A5 poison.
- Category uses `(group - 1)*16 + index`, 22-byte stride, name at offset 0.
  A literal Y in columns 3-8 sets bytes 16-21 to 1. N does not write these
  bytes in this interval; supplied A5 survives. The WORD counter at
  `table + FC2C8` increments once per row. Column-access tracing confirms
  columns 0-8 only; columns 9-11, including `Base100_Index37`, are not read
  by this row interval. This is not a claim about all client consumers.
- QualityValue and StarValue store all 16 numeric columns as consecutive WORDs
  through pointers at `table + FC2CC` and `table + FC2D0`. The two following
  canary bytes remain A5.

Every row checks the exact stop PC, restored stack pointer, actual column
access set, allowed non-stack write ranges and complete relevant destination
bytes. Each invocation is limited to 50,000 instructions and one second.
Input memory is read-only during tokenization; code memory is read/execute only.
Synthetic pointers, counter, scratch and poison are explicit test conditions,
not claimed original gameplay defaults. No allocator, full file-loader/EOF path,
renderer, UI, packet consumer, battle simulation or live process executes.

Existing `current_companion_state` evidence was considered as context: its
S2C31 scalar projection does not prove the units or meanings of those fields.
This deliverable does not rerun historical packet fixtures or promote them to
growth evidence.

## Unresolved Dependencies

| Concept | Missing original evidence |
| --- | --- |
| Growth rate | Curve coefficients/definitions, units and selection consumer; resolution of Base100_Index37 |
| Base value | Initial HP/MP/core/derived stats and binding to actual templates/instances |
| Upgrade formula | Level transition arithmetic, automatic/manual allocation, rounding, caps and overflow behavior |
| EXP thresholds | Original required-EXP table or verified level-to-EXP arithmetic for each companion family |

Also unresolved: COM/NCP category bindings, template skill relationships,
quality/star contributions, innate effects, and authoritative update packets.
Neither source-text assertions nor successful table-row execution supplies these
dependencies. Original growth gameplay is therefore still blocked; the extractor
cannot be used as a substitute formula engine.

The suite verifies all retained records against original bytes, complete auxiliary
file reconstruction, hash rejection, declaration mismatch preservation, missing
versus explicit zero, malformed/truncated/extra rows, independent unknown
contracts, canonical serialization, output guards, and all bounded native rows.
No shared files, CMake, gameplay state, UI or live processes were changed. Baby,
egg and hatch behavior were not audited.
