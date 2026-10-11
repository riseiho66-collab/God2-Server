# Role Growth Evidence, 2026-09-19

## Result and Authority

Current-original-client-only extractor and tests. No original server role EXP
threshold table, level transition rule, HP/MP growth formula, or attribute
growth formula was established in this bounded audit. Unknown values are JSON
null with an explicit status and reason, never zero or a fabricated empty table.

The concrete native finding is a packet-fed WORD and an EXP percentage display
consumer. Its original instructions were executed offline for scalar writes,
display arithmetic and message lookup. This is not live-client acceptance or
original-server growth verification. Source text is not runtime proof.

The owner's latest directive retires all previously supplied legacy material.
Those files remain physically present, but are RETIRED and excluded from this
deliverable. No legacy roots, values, formulas, citations, hashes, or source
reads are required by the final extractor or tests. No retired files were
deleted or consulted after that directive.

Only these files were added for this task:

- `tools/strike_lab/recover_role_growth.py`
- `tests/research/test_recover_role_growth.py`
- `docs/research/role-growth-evidence-20260919.md`

C++20, Lua, CMake, existing recovery tools and shared documentation were not
edited. The tool reuses the existing CSVZ decoder and byte-record helpers;
it does not call their gameplay/content builders.

## Source Identity

Client root: `C:/Users/risei/Desktop/God2/God2`.
Server/research root: `C:/Users/risei/Desktop/God2/God2-Server`.
All seven client inputs are SHA-256 pinned. A mismatch or missing input fails
the build instead of silently emitting changed evidence or zero-valued rules.

| Client-relative source | Raw SHA-256 |
| --- | --- |
| `Data2/Patch/Comm/gamedata.csvZ` | `70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731` |
| `Data2/Patch/Comm/message.csvZ` | `5cd34cce66feae96d947cd45e32984765ce625673c0fb19c73cb63d7d9178598` |
| `God2Con.csvZ` | `8a498103d8a391ac80d49c16572c1140c485f3fcd48a8ec7798ce00cac9284fe` |
| `God2Con2.csvZ` | `576cda6b3a4712ac583141d0bc79feeddb565fbb9675cb2d99e654157e058fc7` |
| `Data2/Client.csvZ` | `7ba020c3963bbd20dfdca89f05cd2d9b08c16c0e796f43850dd46e1fc1fa4f93` |
| `Data/Patch/God.csvZ` | `fa6673ce89374d135d3109bb1381a1fb0755b18f898af3988f34e1995ad8af44` |
| `Data/Patch/Skill.csvZ` | `1dc049cb4ac19fd753c17af64932c40f4e833a1dac92a8d0d33a44529a9a7e16` |

Decoded gamedata: 2,783,008 bytes, SHA-256
`75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815`.
Decoded messages: 110,622 bytes, SHA-256
`370bd6ed9b4892f57190fc7a8dab14061b3e844b0aa9d0171611a9cbab61b5f8`.

The native input is the current captured mapped image, relative to the server:
`artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`.
Size 3,174,400 bytes; SHA-256
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
Image base is VA `00400000`. Native addresses below are hexadecimal RVAs,
equal to file offsets in this mapped image, not offsets in the packed EXE.

## Exact Static Rows

CSV line numbers are one-based physical LF lines. Offsets are zero-based
decimal offsets in decoded bytes. The extractor preserves CR/LF, raw record
hex, record hash, every positional field, and CP950 display strings. Display
decoding never replaces the authoritative bytes or assigns field semantics.

| Source / section / row | Line | Decoded offset | Actual evidence |
| --- | ---: | ---: | --- |
| gamedata / `InitSettingMacro,5` | 4 | 318 | Five initialization rows, not role growth |
| gamedata / `InitSettingMacro` third row | 7 | 379 | Four fields, including opaque trailing comment |
| gamedata / `GodLevel,4` | 21164 | 2483449 | Four name/value rows, not a role EXP curve |
| gamedata / first GodLevel row | 21165 | 2483461 | `a470a550a6ec2c310d0a` |
| gamedata / second GodLevel row | 21166 | 2483471 | `a5bfa550a6ec2c320d0a` |
| gamedata / third GodLevel row | 21167 | 2483481 | `b16aa550a6ec2c330d0a` |
| gamedata / fourth GodLevel row | 21168 | 2483491 | `bbf4a550a6ec2c340d0a` |
| message / SystemMessage 330 | 405 | 16736 | Attribute reset display text |
| message / SystemMessage 844 | 919 | 37272 | Character level-lock release display text |
| message / SystemMessage 1746 | 1821 | 81454 | EXP denial at a cap, display text only |
| message / ProgramMsg 162 | 2188 | 90220 | EXP percentage format with `%6.2f` |
| message / ProgramMsg 927 | 2953 | 106482 | Text mentioning level 224; not a role cap |

The artifact includes all nine opaque table rows and 29 selected message rows.
It also inventories lexical marker candidates in the seven inputs. These are
not guaranteed section boundaries or a proof that hidden tables do not exist.
Nothing treats GodLevel's four values, message 927's 224, or any displayed
item EXP award as a role progression threshold.

## Bounded Native Finding

Current dispatch table `6B5D4 + 4*22` contains VA `00469EF0`.
The dispatcher passes the body at logical record +1 to `E6B40`.
Length function `1258` returns 25 logical bytes including the opcode.

The original scalar prefix `E6B40..E6BD4` performs these stores. Body offsets
and widths are decimal; destination offsets are hexadecimal relative to the
actor pointer at `[UI+86888]`. The first refresh call at `E6BD4` is excluded.

| Body offset / width | Actor destination | Operation |
| --- | --- | --- |
| 0 / 1 | `+26` | Raw byte |
| 2 / 2 | `+90` | Raw WORD |
| 4, 6, 8, 10 / 2 each | `+78,+7C,+80,+84` | WORD zero-extended to DWORD |
| 12 / 2 | `+58` | Raw WORD later used for EXP percentage display |
| 16, 20 / 4 each | `+60,+68` | Raw DWORD |

Body bytes 1, 14 and 15 are not consumed by this tested prefix. Other actor
bytes remain unchanged. These stores do not compute level growth; positional
field names remain opaque except for the separately established display use.

Static inspection also identifies S2C `2B`: dispatch entry `6B680`, target
`69EB0`, scalar consumer `E6390`, and length function `127C` returning 21.
Its body WORD at offset 16 is stored at actor `+58` by `E63B8`. Its two other
scalar stores copy body DWORDs at 0 and 8 to actor `+5C` and `+64`.
The S2C2B prefix is retained as hashed bytes, not claimed as executed here.

Display consumer `E6C90` reads the unsigned WORD at actor `+58` at `E6CAF`.
The arithmetic prefix ends before the call at `E6CD1`. It multiplies by the
original float32 bytes `0ad7233c` at RVA `171204`, whose value is
`0.009999999776482582`, and stores a float32 result. This is display scaling,
not an EXP-to-level formula. The later conversion/formatting callees were not
executed. Static formatter arguments are retained through `E6D25`.

The separately executed `E6CE1..E6CFE` lookup checks the ProgramMsg count,
loads the pointer array at `messages+B2C68`, and reads offset `284` (decimal
644), i.e. index 161 / message ID 162. Its current source row is the EXP
percentage format above. This binds the WORD to a display use; it does not
establish the server's underlying EXP total, required EXP, or rounding policy.

Native regressions run unmodified instructions in Unicorn, bounded to 1,000
instructions and one second per slice, with exact stop-address checks. They
use synthetic machine operands solely to test stores and WORD boundaries.
No synthetic growth samples, positive gameplay formulas, or simulated server
rules are created. No native callees are stubbed or replaced.

## Native EXP Table and Remaining Semantics

No identifiable native role EXP table was extracted. Consequently there are
no source-backed role threshold rows to publish; `rows` is null, not an empty
table that could be mistaken for zero requirements. The report distinguishes:

| Requested evidence | Result | Specific missing link |
| --- | --- | --- |
| Single-level thresholds | Unknown | No next-level requirement lookup identified; inspected scalar paths receive a WORD |
| Cumulative thresholds | Unknown | No total-EXP accumulator, prefix-sum table or total-to-level consumer established |
| Level cap | Unknown | A WORD's range and message text do not establish a role cap |
| HP/MP growth | Unknown | Copying state fields does not establish how the server derives or increases them |
| Automatic/manual attribute points | Unknown | State fields and reset text do not prove per-level budgets |
| Birth stats, class/rebirth modifiers, rounding/overflow | Unknown | No original causal rule or server sample established |

The bounded investigation inspected the pinned packet/scalar/display spans
and selected static files. Before convergence, a numeric-candidate scan of
mapped `.rdata/.data` (`170000..2F9000`) looked for at least 24 strictly
increasing contiguous little-endian uint32, uint64 and float64 values at each
byte alignment. Value bounds were `[0,2^32)`, `[0,10^18)` and `[1,10^18)`
respectively. It did not establish any candidate's role-EXP identity.
That exploratory heuristic is not an extractor rule or an absence proof:
segmented, strided, compressed, dynamically generated and server-only tables
remain outside its conclusion. No candidate was polynomial-fitted, summed,
differenced, extrapolated, or promoted based on its numeric shape.

## Existing Runtime Defaults Encountered

These are current repository source observations, not original authority and
not runtime verification. They were reported without editing shared files:

- `src/game/Character.h:10`: level/job/map defaults of 1; HP 100, MP 50.
- `src/game/Character.h:11`: position defaults 100,100.
- `src/db/Migration.cpp:15`: default level 1; lines 17-18 default HP 100/MP 50;
  lines 19-21 default map 1 and position 100,100.
- `src/game/Monster.h:7`: default HP 100.

No original evidence for these placeholder defaults was established here.
This task does not claim they were exercised by the active recovered protocol.

## Reproduction and Verification

Working directory: `C:/Users/risei/Desktop/God2/God2-Server`.

```powershell
python -B -m tools.strike_lab.recover_role_growth --client-root C:/Users/risei/Desktop/God2/God2
python -B -m unittest discover -s tests/research -p test_recover_role_growth.py -v
```

The first command emits deterministic ASCII JSON to stdout. `--native-image`
can relocate the identical pinned capture. Optional `--output PATH` writes an
artifact; `--output PATH --check` compares it without modifying it. Source
overwrites are rejected. No fourth persistent artifact is required.

Result: **16 tests passed**. The tests include all source/row hashes and
offsets, exact opaque fields, null unknowns, no retired-source reads, source
drift rejection, malformed real-table mutations, deterministic output, CLI
comparison and source-overwrite rejection, plus the bounded native checks.
Native tests use the existing Unicorn installation under
`artifacts/tooling/crypto-oracle-python`; the extractor uses Python's standard
library and existing recovery helpers only.

Serialized artifact: 122,253 bytes; SHA-256
`0c839aa460912005092e3671db053069c9a14088008bd94205883358f322c5b3`.
Its `runtime_verified` and `runtime_eligible` flags remain false. There was no
live run, server integration, original-server verification, or C++ build.
