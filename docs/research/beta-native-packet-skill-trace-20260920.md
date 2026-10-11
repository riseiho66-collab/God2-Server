# Beta Native Packet And Skill Trace

## Completed Scope

Executed the original beta ASPack stub in offline x86 emulation, restored an
analysis image, located beta-native battle dispatch and skill consumers, and
executed two scalar receivers. No game process, desktop interaction, external
server, production database, or current-client patch was involved.

The input SHA256 is
`1326af232a5280a5bf19cfadb434ba66b8b2b2753bd36097ada3ef66474c5cac`.
Output mapped image SHA256 is
`ef373960e2cf455916110f81eaff3935c1d950a46ff7de7b4ef562b01a56405f`.
Two completed unpack runs produced this same image hash.

Artifacts in `artifacts/research/beta-unpack-20260920/`:

- `beta-mapped.bin`: restored mapped image, base `0x400000`.
- `unpack.json`: stub API trace, section lengths, final handoff and hash.
- `packet-probe.json`: dispatch table and all diagnostic scalar results.

All code addresses below are beta hexadecimal RVAs, not current-client RVAs.
Image offsets equal RVAs. Actor offsets and packet offsets are explicitly
distinguished. The image has synthetic import addresses and is NOT a runnable PE.

## Unpacking Evidence

The original stub decompressed 1224704, 69632, 126976 and 35184 bytes in its four
operations. Its final block at VA `5C53BA` transferred to startup VA `50576A`
(RVA `10576A`), where execution stopped before application initialization.
The temporary RET probe at VA `401000` was explicitly excluded from completion.
Earlier instruction-budget stops are not treated as successful unpacking.

Only synthetic module/procedure lookup, allocation/free and protection services
are permitted. No imported network or application function executes on the host.
Synthetic import identities are analysis aids, not a repaired production IAT.

## Original Packet Paths

Socket receive callers at `45270`, `452AE`, `45329` reach thunk `101006` and
IAT `12C820` (WS2_32 ordinal 16). The receive loop `45250` reads the two-byte
wire length, handles its high flag bit, bounds length below `0xC00`, and calls
`45140` after accumulation. These framing observations are static, not a fresh
network capture or a completed beta crypto validation.

The battle dispatcher at `C6820` normalizes opcode by `-0x19`, uses byte-index
table `C6AE8` and target table `C6AAC`. Its nondefault cases are:

| Opcode | Case RVA | Direct receiver | Length-function return |
| --- | --- | --- | ---: |
| 19 | C6842 | C7F70 | 29 |
| 35 | C6982 | C96E0 | 2 |
| 80 | C6855 | C8CD0 | 17 |
| 81 | C68C7 | C8920 | 17 |
| 82 | C6933 | queue/control | 2 |
| 83 | C6948 | C9460 | 13 |
| 84 | C6958 | C9530 | 13 |
| 85 | C6968 | C9600 | 13 |
| 86 | C699C | C9940, pointer advanced by one | 11 |
| 87 | C6972 | C96C0 | 3 |
| 88 | C69D6 | CA240 | 121 |
| 89 | C6A20 | CA390 | 53 |
| 8D | C6992 | C9710 | 5 |
| DE | C69B2 | C9680 | 9 |

The original length function `1200` was executed for all 256 byte values.
These are its returned logical-size constants, not asserted encrypted wire sizes.
The dispatcher table was decoded statically, not fully exercised end to end.
Beta has a materially different opcode scheme from the current image; never
import these mappings into the current decoder unchanged.

## Executed Scalar Evidence

Executed original receivers `C9460` and `C9530`, original lookup `CF200`, and
setters `DDE80`/`DDF00` for positions 0..27: 56 cases passed.
Diagnostic values are synthetic markers, not recovered official monster values.

Packet offsets include the opcode:

- `83`: DWORD `+9` writes actor `+DBC`; DWORD `+5` writes actor `+DC4`.
- `84`: DWORD `+9` writes actor `+DC0`; DWORD `+5` writes actor `+DC8`.
- Positions 0..13 perform these assignments. Positions 14..27 return without
  those assignments through the actual native side test.

The lookup indexes 2 sides, 14 slots, 6 actor types. Renderer calls were excluded
using the native negative-render-handle branch; local UI synchronization was
excluded with a nonmatching local slot. The packet handlers, lookup and stores
were not replaced with modeled implementations.
These tests qualify copying supplied scalar values, not dual attack/defense
semantics, wild-monster base values, or a local damage calculation.

## Skill Evidence

Literal `data2\\fight\\spg\\cbspec2.bin` at `153A38` is referenced by PUSH at
`C33B7`; `C33B8` is its operand, not an instruction boundary. Call `C33DE`
reaches loader `DD9F0`. It opens the file, compares its first four bytes to
`1.03`, and reads `0x1B010` bytes into receiver object `+0x53E63A8`.
It does not check fread counts: its success return alone cannot certify input
completeness. The separate bounded source parser validates the actual envelope.

Record addressing in `DCFB8..DCFE1` and `CD0D2..CD0F3` independently confirms
108-byte records and `0x6C04` bank stride. These are beta-native instructions,
not assumptions from the modern 110-byte layout.

Static consumer evidence:

- `CC9C3` reads record WORD `+42`; `CC9CD` supplies the literal `%s MP=%d`
  at `154094`. This qualifies the displayed MP field, not deduction timing.
- `D6BE0` tests record WORDs `+4C..+54` for elemental-effect labels and
  `+56..+5C` for arm/body/intelligence/speed labels.
- Tests `D6CC1`, `D6CD8`, `D6CEF`, `D6D06` examine record `+5E/+60/+62/+64`
  and conditionally format physical attack/defense and magic attack/defense.
- These words are nonzero label gates in this consumer. The formatted amount
  is the separate function argument. `D634A` sign-extends actor WORD `+26C`
  and `D635A` passes it to `D6BE0`.
- `DBA59` stores an argument of `DB940` at actor `+26C + index*2`. One
  action-side call at `DD077` supplies a WORD read from action-record `+E`
  at `DD05C`. This is a supplied-effect-amount lead, not a formula.

No executed skill formatter/loader test is claimed by this report. Native
execution coverage here is the unpack stub, length function and two scalar paths.

## Verification And Remaining Frontier

```powershell
python -B -m tools.strike_lab.beta_unpack --source C:\Users\risei\Desktop\god2-test\god2.exe --output artifacts/research/beta-unpack-20260920
python -B -m tools.strike_lab.beta_packet_probe
python -B -m unittest discover -s tests/research -p test_beta_packet_probe.py -v
```

Three regression tests passed, including 256 native length evaluations and
56 original scalar-receiver cases. All helper agents were closed on completion.

Still unresolved: official wild-monster dual attack/defense values, full species
skill assignments, original damage/defense/critical formulas, MP debit timing,
and whether additional beta-only computations exist. Next narrow targets are
the beta action-record producer feeding `DD077` and consumers of the skill/stat
fields beyond display. Do not label this work complete native combat recovery.
