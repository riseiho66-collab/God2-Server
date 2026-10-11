# Current skill target setup: bounded native proof

The qualified arithmetic is target-row distance, target-mask construction, and
setup-state assignment. No skill damage, damage multiplier, or damage coefficient
is calculated in the executed helpers. The original damage formula remains
unknown. Names such as `reach_44` describe observed use in this path only.

## Authority and scope

- Image: `artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`.
- Image SHA-256: `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
- Current source: sibling `God2/Data2/Fight/Spg/cbspec2.bin`.
- Source SHA-256: `7676acd93f164d071f7681a3fe74de94d65892759dbf2e69e3c0f748423d2f51`.
- All addresses below are image RVAs; execution maps the image at `00400000`.
- Evidence is current image bytes, the pinned source, and actual Unicorn x86
  execution. No retired archives/corpora or historical documents were consulted.

Only the new model, test, and this document belong to this work. The tests inherit
the current selection fixture and regressions; existing helpers remain unchanged.
No gameplay runtime, catalog integration, CMake, or other task files are modified.

## Postselection boundary

`1154E0` first calls `1156A0` to obtain the selected definition. This proof does
not execute the whole function: earlier UI/setup calls and intervening UI calls
are outside the bounded lane. It executes three independent original windows
with explicit registers, source records, and memory state:

| Window | Native behavior qualified | Stop |
| --- | --- | --- |
| `115571..11557D` | Kind 2 continues only when unsigned WORD `+3E == 0FF5`; other kinds continue | `11557F` or `11559A`, before either branch body |
| `1155BF..1155E4` plus complete callees | Actual source loads, `1156E0` actor accessor, and `CALL 11EE90` | `1155E9`, before the following UI call sequence |
| `1155F2..11564E` plus complete `11EAD0` | Actual mode load, `CALL` at `115614`, return storage and adjacent clears | `115650`, before `CALL 111E10` |

Let `B` be the battle object and `T = B + 144938`. The call at `1155E4` passes
`(B+434, zero_extend(byte +45), actor, zero_extend(byte +44), kind, id)` to
`T::11EE90`. The kind/id arguments have only their low bytes consumed. The actor
comes from `B+51`, or `B+52` when DWORD `B+A9E9C38` is zero and `B+A9E9C3C` is
nonzero. The accessor can retain upper EAX bits; the callee uses the actor byte.
Tests include nonzero upper bits in that mode state.

Of 448 populated definitions, 364 pass this single kind/WORD gate. Of the 87
kind-2 definitions, three have WORD `0FF5`. These counts do not establish learned
ownership, authorization, successful casting, or reachability through earlier
caller conditions. Tests deliberately invoke helpers for all source records,
including records diverted by the gate.

## Exact target arithmetic

`11ECA0(side, slot)` locates the first row containing `1 << slot` in the side's
four rows. The bounded domain is sides 0..1 and slots 0..13. DWORD masks at
`171BF8` are:

```text
row:   0     1     2     3     4     5     6     7
mask: 3000  0E00  01E0  001F  001F  01E0  0E00  3000
side:  0     0     0     0     1     1     1     1
```

The deepest fully executed arithmetic helper is `11ED00`, with both calls to
original `11ECA0` intact. If endpoints map to rows `a,b`, it returns:

```text
abs(b-a) - number of empty rows strictly between a and b
empty(r) means (input_masks[r // 4] & row_masks[r]) == 0
```

It does not test endpoint occupancy. Distinct rows yield at least one, even with
both masks zero. For side-0 slot 12 to side-1 slot 12 the result is 7 with full
masks and 1 with empty masks. This is occupancy-adjusted row distance, not damage.

`11EDA0` begins at `max(row_index(0, actor) - byte44, 0)`, scans backward from row
7 until `11ED00` is at most byte44, ORs the intervening row masks using original
`11EC70`, and intersects each output with its input mask. The native scan, lower
bound, and intersection are reproduced literally; a generic geometric radius
would not be an equivalent model. This proof covers its nonnull mask-pointer
call shape from `11EE90`, not every standalone argument accepted by `11EDA0`.

`11EE90` initially copies DWORD masks `T+2F4/+2F8` to stack locals and clears the
two output DWORDs. For kind 3 and ids 8..10 inclusive, it additionally walks all
28 slots through unchanged `11E6E0(side, slot, 0)`. A nonnull pointer whose signed
WORD at `+1A` is nonnegative adds that slot to the local mask. No meaning such as
HP, alive, or damage is assigned to that WORD. The source masks stay unchanged.

| Byte `+45` | Output behavior |
| --- | --- |
| 1..5, 13, 14, 16 | Complete `11EDA0` result |
| 6, 7, 15 | Row templates at `171C38`, `171C58`, `171C78`; current row plus conditional nearer/farther rows using `11ED00` and byte44 |
| 8 | Each side gets `001F` if its slot-0 row distance is at most byte44 |
| 9, 10 | Each side gets `0400` if its slot-4 row distance is at most byte44; preserve this exact test/output pairing |
| 11 | Side 0 gets `1 << actor`; side 1 is zero |
| 12 | `11EDA0` result with side 1 subsequently cleared |
| 17 | Executes `11EDA0`, then overwrites output with `(1 << actor, 0)` and copies original `T+2F4/+2F8` into `T+2FC/+300` |
| Other byte values | Both output DWORDs remain zero |

Every arm stores the mode DWORD at `T+304`. Modes 6/7/15 start with their actor-row
template. For actor rows 1..3, if distance to side-0 slot 12 is at most byte44,
all preceding templates are added; otherwise rows 2/3 add the immediately
preceding template when that distance is positive. A backward scan from row 7
then adds qualifying farther rows. These arms do not perform the final occupancy
intersection used by `11EDA0`. Neither do modes 8..11 or the overwritten mode-17
result. For example, mode 8 with reach 7 returns `(001F,001F)` from empty inputs.

## Setup lookup and writes

`11EAD0(mode, out)` reads `171BB0 + 4*mode`. For modes 1..17 the return values are:

```text
mode:   1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17
return: 1 2 3 4 1 1 1 1 1  1  1  1  2  7  1  3  2
```

The out DWORD is zero for 13/14/16, one otherwise. At the actual caller,
`B+45C` receives the return and `B+468` the out value. The executed caller window
also clears `B+43C..443`, `B+444..44B`, `B+44C..459`, and DWORD `B+460`.
Bytes `B+45A..45B` and DWORD `B+464` are preserved in that window.
The latter was assigned 3 earlier in the full caller, outside this execution.
The lookup values are setup metadata; there is no evidence they are damage
coefficients, multipliers, or target-count limits.

Seven current definitions have mode zero. `11EE90` clears output for zero;
`11EAD0` attempts diagnostic callee `002C70` for modes outside signed 1..17.
The harness fails closed there, without executing or replacing the diagnostic.
No successful continuation or out-of-range table-read behavior is claimed.

## Native verification

Run from the server repository:

```powershell
python -B -m unittest discover -s tests/research -p test_current_skill_target_setup.py -v
```

The suite has 13 tests: six new target-proof tests and seven inherited selection
regressions. Final verification on 2026-09-19: all 13 passed in 12.182 seconds.
The new tests include:

- 17,952 direct `11ED00` comparisons: all physical endpoint pairs with empty/full
  masks, and all row pairs across every one of 256 row-occupancy patterns.
- 9,520 mode/actor/reach/mask combinations, all 17 valid modes, high DWORD mask
  bits, byte reach boundaries, and dispatch-arm coverage checks.
- 420 kind/id/mode combinations testing special expansion boundaries and signed
  entity words, plus 512 deterministic randomized snapshots.
- All 448 source records through the native gate and direct mask helper, and
  through actual source-loading caller windows under three actor-accessor states.
- All valid setup modes, current-source setup windows, and diagnostic boundaries
  for 0, 18, 255, `FFFFFFFF`, and `80000000`.
- Exact constant-table assertions against the pinned image, complete context and
  output-page comparisons, adjacent preserved bytes, and checked input rejection.

The image is mapped read/execute. Instructions must fit completely within closed
allowlisted ranges; external game callees cannot return fake success. A separate
hook rejects native writes outside the stack and each invocation's declared
output fields. Direct helpers must reach the sentinel return with the exact
callee-cleaned stack size; caller windows must reach their named stop. An
instruction limit cannot silently count as completion. Fixtures are explicit
synthetic state using real source definitions, not captured live battle state.

## Damage unknown and next location

No attack/defense arithmetic, damage rounding, random damage roll, damage
coefficient application, or HP mutation occurs in these qualified paths. This
negative result is local to the executed helpers and bounded caller windows;
it does not establish that the client or the full skill workflow never computes
damage elsewhere.

The immediate unexecuted continuation is the call at `115650` to `111E10`.
The already inspected current bytes show target-mask/UI handling there, so it
must not be presented as an identified damage routine. Another concrete handoff
toward original calculation is the existing current command path at `118E50`:
it calls `1156A0` for the selected definition and queues its identity through
`0132E0`, with the existing bounded builder stopping at `1191EE`. Tracking that
identity into action/result consumers is the next calculation-oriented step.
This task does not trace those wider consumers or claim a verified damage RVA;
that work remains with the main lane. The target masks and setup lookup recovered
here must not be used as a substitute for the missing original damage formula.
