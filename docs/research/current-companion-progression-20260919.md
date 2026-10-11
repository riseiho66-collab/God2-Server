# Current Companion Progression Consumer, 2026-09-19

## Bounded Result

**Growth/stat/upgrade/EXP rules remain OPEN.** New evidence establishes one
actual downstream consumer of the current original QualityStar table: original
WORD values become numeric display-format arguments, without stat scaling or
growth accumulation in the executed slices. The literal `+` in the format
string is text, not evidence of adding a bonus to a gameplay stat.

This deliverable adds only:

- `tools/strike_lab/current_companion_progression.py`
- `tests/research/test_current_companion_progression.py`
- `docs/research/current-companion-progression-20260919.md`

The prior recovery report/loader was read and reused as an input fixture; no
catalog extraction was repeated or expanded. No retired corpora, server rules,
shared files, current recovery files or CMake were changed. No runtime data,
custom rates, artifacts, live process calls or successful game-callee stubs
are emitted. The CLI prints research JSON to stdout only.

## Exact Source to Consumer

Image: `artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`.
SHA-256: `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
All addresses below are hexadecimal RVAs; image base is `00400000`.

Current source: `God2/Data2/Patch/Comm/NewCombatPet_QualityStar.csvZ`.
Compressed SHA-256:
`52b414716947b4982d74c7da4166f35f4dd1b8e2cba27265aa3f854a2ba8756e`.
Decoded SHA-256:
`fde6e5b716e710d39b1b706efabd1cfc9d58ef9fc353033d709b38b4bc1a5fbf`.
Physical lines 5 and 7 supply QualityValue and StarValue respectively.
JSON includes each original row's exact bytes, hash, physical line, decoded
offset and fields; no generated gameplay fixture supplies these values.

| Stage | Exact relationship | Evidence |
| --- | --- | --- |
| Existing row loader | `5CA92..5CAAF`, `5CAF2..5CB0F` populate WORD arrays through `table+FC2CC`, `table+FC2D0` | Reused original fixture with existing decimal CRT adapter |
| Quality pointer | `B7DCF -> 5CAC0`, load `[ECX+FC2CC]`, real `ret` | Newly executed |
| Star pointer | `B7DDC -> 5CB20`, load `[ECX+FC2D0]`; `B7DE1` saves EAX at `[ESP+10]` | Newly executed |
| Quality index | `B7E2D..B7E38` or `B7EF2..B7EFD`: `([EBX+0C] >> 20) & 15`, WORD read, zero extension | Newly executed for both branches |
| Quality sink | Six arguments staged before `B7E4D` or `B7F12 -> 147AF7` | Exact stack observed; call not executed |
| Star index | `B7F89..B7F98`: `([EBX+0C] >> 16) & 15`, WORD through saved Star pointer, zero extension | Newly executed in separate later slice |
| Star sink | Six arguments staged before `B7FAD -> 147AF7` | Exact stack observed; call not executed |

At each sink the six DWORDs are `(destination, format, label, index, suffix,
table_value)`. Quality format at `192A04` is `\n%s:%d (%s+%d) `; Star format
at `1929F4` is `%s:%d (%s+%d)`. The source value is passed unchanged as the
last `%d` argument. These bytes and direct-call targets are checked against
the pinned image. The formatter entry `147AF7..147B49` is static evidence only.

Examples from actual source rows: Quality indices 0, 1, 15 yield 0, 15, 390;
Star indices 0, 1, 15 yield 0, 30, 780. Neither the units nor a gameplay effect
follows from those numbers. No percent conversion, stat addition, level
transition, rounding or EXP threshold has been demonstrated.

## Native Arithmetic and Producer Boundary

The gate at `B7DB4..B7DC9` computes an integer sum of two bytes and admits
exactly sum 1; other sums branch to `B7FE8`. `EAX` is the already extracted
second byte; `[ESP+68] & FF` supplies the first. This is **flag arithmetic**,
not pet-stat arithmetic. Tests include `(0,0)`, `(0,1)`, `(1,0)`, `(1,1)`,
A5 poison combinations and `(255,255) -> 510`. Treating arbitrary nonzero
bytes as true would give incorrect behavior.

The gate inputs have a concrete static producer: call `B7A87 -> 5CA00` gets a
22-byte Category record, then `B7A8C..B7A99` copies it into stack local `+54`.
The local bytes `+68/+69` are Category record offsets 20/21, corresponding
to columns 7/8 in the already established native row layout. `B7DA4/B7DAD`
extracts the second byte before a string-copy tail; this preceding extraction
and the Category getter/copy are **not executed by this deliverable**.
N-byte initialization is not redefined here: prior evidence shows row slices
leave N destinations untouched. Synthetic gate cases are explicitly labeled,
and are not asserted to be fully initialized original Category instances.

The packed DWORD's precise next producer boundary is also recorded, without
claiming to have found its writer:

- `B5BE0` takes the packed-record pointer as its sixth argument;
  `B7817` reloads it from `[ESP+11AC]` into EBX in this path.
- One concrete caller is `87690`: `87691` loads its third argument into ESI;
  `876B8` pushes ESI as the sixth argument for call `876C9 -> B5BE0`.
- The next unresolved producer is the writer of that incoming record's DWORD
  at offset `0C`, including the source of bits 16-23. This caller relationship
  is static, not a recovered packet writer, stat producer or level formula.

No concrete deity XP progression lead was discovered in this bounded path.
`deity_xp_lead` is null; no wider deity research or tooltip inference was done.

## Execution and Validation

The 1,024 native comparison cases cover every independent pair of 16 Quality
and 16 Star indices, both gate-admitted display modes, and both zero and all-one
bits outside the selector mask (`FF00FFFF`). Cases are checked against the
exact source rows and exact native read PCs, addresses and WORD widths.

Synthetic addresses: table `03000000`, stack SP `03208000`, record `03300000`,
Quality array `03400000`, Star array `03400100`, owner `03500000`.
Input/code pages are native read-only/read-execute; consumer writes must stay
inside the bounded stack argument/local-pointer region. Every consumer segment
has a code allowlist, exact stop PC, 300-instruction limit and one-second limit.
Original getters must actually execute; null table pointers fault. A test
rejects entry into the unexecuted formatting call instead of returning success.

Message count is explicitly zero, so original branches stage null label/suffix
arguments. They are never passed to a running formatter. This establishes the
numeric argument dataflow, not successful rendering with absent strings.
Star execution is a separate bounded slice starting at `B7F6E` with declared
EAX=table and EDX=0, ESP restored to the slice boundary; it retains the Star
pointer written by the actual preceding getter path. No skipped formatter or
string copy is pretended to have run. Whole-function/UI execution is unproven.

JSON separates executed and static-only code ranges, hashes each exact interval,
and hashes the reused `recover_companion_growth.py` and `current_npc_resources.py`
dependencies. Only the existing `%d` decimal adapter at `1480B4` is used during
row setup; no CRT/game adapter is called during the new consumer slices.

Reproduce from `C:/Users/risei/Desktop/God2/God2-Server`:

```powershell
python -B -m unittest tests.research.test_current_companion_progression -v
python -B -m tools.strike_lab.current_companion_progression --client-root C:/Users/risei/Desktop/God2/God2 --native-image artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin
```

Validation: **7 tests passed, no skips, 19.627 seconds, exit 0**. The standalone
CLI also exited 0 and completed all 1,024 cases. Tests independently construct
the complete expected numeric/read-provenance sequence from the source rows
and compare its canonical digest to the native observations.

Canonical case-sequence SHA-256:
`1b8326a1711c6a674570ae8ab3cb7874875f00d60d81f15d640dfcd9373bf2a2`.
Raw Windows CLI stdout SHA-256 (including stdout newline translation):
`6e700a762ffe9e76e1bc116e8ddac17c60e53e34c48c644ed69395e51fc1f40d`.

Source line 5 is at decoded offset 136, raw-row SHA-256
`4732a01c8d51ab420c0c352c7f644f2835392115197276918636cc9c61420a09`.
Source line 7 is at decoded offset 205, raw-row SHA-256
`a973097d551e0d85d0a080f8ff1836593ea627a9194fddb7d63070c6fc1407ce`.
Reused recovery helper SHA-256:
`3d594fb337426647e2d8bd0772e04af37e132eb689b5846ab40f5ff9da8662e9`.
Reused decimal-adapter source SHA-256:
`6cff27ef65b7c11a71a87c7d9ea1d79c0ad9b163e6da66058507067aea3191d1`.

Existing integration build/core-test results are owned by main integration,
not rerun or attributed to this research deliverable. This closes only the
bounded source-to-display consumer investigation; gameplay rules stay OPEN.
