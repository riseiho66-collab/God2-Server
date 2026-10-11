# Current battle scalar result, 2026-09-19

This qualifies two adjacent consumers of the already identified **17-byte S2C
logical opcode 0x86**: record discriminator **0** at `117230` and discriminator
**1** at `1173A0`. They copy transmitted scalars into entities, then optionally
set display divisors and clamp display numerators. They do not produce damage.
No HP/MP, attack, defense, skill coefficient or server formula names are assigned
to these raw fields.

## Ownership and authority

Only these new files belong to this continuation:

- `tools/strike_lab/current_battle_scalar_result.py`
- `tests/research/test_current_battle_scalar_result.py`
- `docs/research/current-battle-scalar-result-20260919.md`

The new suite reads only the current raw image as source data:
`artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`,
SHA-256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
It verifies the whole image before executing. All locations below are RVAs,
mapped at VA `00400000`, with RVA equal to image offset. The existing Unicorn
dependency is loaded from `artifacts/tooling/crypto-oracle-python`.

Starting pointers were the current discriminator-3 proof and the display spans
already recorded in `combat-rule-authority-20260919.md`. That document's wider
inventory builder and source tables are not used or executed. Every new native
claim is checked against current image bytes, using explicit synthetic records
and state. No retired corpus or historical lead is used. The render/control
chain through `126270/120AE0/120B90` is not revisited.

No shared files, runtime, CMake, formal headers, UI, game process, production DB
or subagents are involved. Main owns the discriminator-3 formal contract and
world integration. The model sets `runtime_mutation_enabled = False`; this is a
research scope declaration, not an enforcement mechanism.

## Dispatch and input layout

The tests start at actual queue dispatch `114332` with EBP pointing to the
original queue record and EDI pointing to its explicitly supplied mutable copy
at `R = B+A9E9CB0`. Both contain the same 17 bytes. The queue copy itself and
the preceding network receive are outside this suite. Native code remains
unchanged throughout all executed calls.

`114464` reads `B+A9E9CB1`, exactly `R+1`. Table `1146CC` selects `11447A`
for value 0, whose call at `11447D` enters `117230`. Table `1146D0` selects
`11449E` for value 1, whose call at `1144A1` enters `1173A0`. This discriminator
is a transmitted byte, not a skill kind, C2S action or independent state value.

| Logical offset | Width | Qualified use |
| --- | --- | --- |
| 0 | byte | 0x86, read from original queue record by dispatcher |
| 1 | byte | Discriminator 0 or 1 in the copied record |
| 2 | byte | Zero-extended position; quotient/remainder on division by 14 |
| 5 | DWORD LE | Second supplied scalar, copied to entity +DF0 or +DF4 |
| 9 | DWORD LE | First supplied scalar, copied to entity +DE8 or +DEC |
| 3..4, 13..16 | bytes | Unread/opaque in these qualified prefixes |

The model admits positions 0..27, local slots 0..13, explicit null pointers or
4096-byte entity snapshots, and explicit display fields. These are research
bounds, not a recovered server policy or a complete entity-size definition.
Neither original nor copied logical record is modified in these branches.

## Exact scalar writes

Let `T = B+144938`. Both side-0 parsers call original `11E6E0(0,slot,0)`
to obtain E, then their setter repeats the same original lookup. The type-0
pointer slot is `T+38+24*slot`. A null pointer returns without scalar writes.

| Discriminator | Loads / call | Setter writes in order |
| --- | --- | --- |
| 0 | `11729A` reads +5; `11729D` reads +9; `1172AB -> 12D840(0,slot,value9,value5)` | `12D86C`: DWORD value9 to E+DE8; `12D875`: DWORD value5 to E+DF0 |
| 1 | `1173F9` reads +5; `1173FC` reads +9; `11740A -> 12D970(0,slot,value9,value5)` | `12D99C`: DWORD value9 to E+DEC; `12D9A5`: DWORD value5 to E+DF4 |

These are unconditional DWORD copies after nonnull lookup, with no arithmetic,
signed conversion or damage interpretation. They occur even when signed WORD
`E+1A` is negative and even when the display handle is negative. The other two
entity scalar DWORDs retain their prior snapshot values.

The setter reads signed WORD `E+1D8`. If negative, it skips its display calls.
Otherwise both display helpers receive its low WORD; low-WORD values >=0x1000
return without accessing a display record. A high WORD in direct helper
arguments is ignored. Positive entity handles 0x1000..0x7FFF thus preserve the
entity copies but cause no display-state writes. Negative entity handles never
reach the display helpers in this receive path.

After the setter returns, a side-0 slot matching `B+51`, with signed WORD
`E+1A >= 0`, copies all four DWORDs `E+DE8, +DEC, +DF0, +DF4` to stack storage
and calls `0E71E0`. This is a separate forwarding boundary, not a gate on the
earlier scalar writes. Tests stop at the callee entry and check the payload,
ECX, caller-supplied context DWORD, low mode byte from `B+76`, and zero flag.
Nonlocal or negative-marker cases return to queue continuation `114482` or
`1144A6`, respectively. Upper unused argument bits are not normalized or named.

For side 1, discriminator 1 returns with no lookup and no mutation. Discriminator
0 loads the two packet DWORDs and an explicit fixture DWORD through
`[B+83458]`, then calls `12D8C0` at `117388`. Tests stop at `12D8C0` entry and
verify all argument bits (slot semantics use its low byte). No side-1 scalar
write or successful wrapper return is claimed.

## Display order and arithmetic

Set `M = T+310`, `h = low_WORD(handle)`, and
`D = M+1C+h*A7E0`, valid only for `h < 1000h`.

Both scalar setters perform the same sequence using the four current entity
DWORDs, including values preserved from the explicit snapshot:

1. `12D88E` / `12D9BE` calls `108FC0(h,E+DF0,E+DF4)`.
   It stores literal DWORD divisors at `D+A7A8`, then `D+A7AC`, and calls
   `108E70` at `108FF6`. It does not change display numerators first.
2. Only after that original renderer returns, `12D8AB` / `12D9DB` calls
   `108F50(h,E+DE8,E+DEC)`. For each channel it writes the supplied numerator,
   compares it to the stored divisor with unsigned `CMP/JBE`, and overwrites
   it with the divisor if larger. Channel 0 at `D+A7B0` is processed before
   channel 1 at `D+A7B4`. It calls `108E70` again at `108FA9`.

Thus final display numerators, when this sequence completes, are
`min_u32(E+DE8,E+DF0)` and `min_u32(E+DEC,E+DF4)`. The entity DWORDs themselves
are not clamped. A render during step 1 observes old display numerators with
new divisors. Tests compare the exact ordered writes, including the initial
above-limit write before its clamp overwrite.

`108E70` checks signed WORD channel handles at `D+A79C` then `D+A79E`.
With both negative, it returns normally, allowing the continuous native receive
path to execute both display helper calls and the subsequent parser logic.
With either channel enabled, this proof stops at the first real `01BDC0` call;
it never fabricates a renderer return to reach later code. Separate direct
clamp-helper invocations qualify its render boundary with explicit state.

Actual scaling for an enabled channel is:

```text
numerator = zero_extend_u32(D+A7B0 or D+A7B4)
width     = sign_extend_i16(D+A7A4)
divisor   = reinterpret_i32(D+A7A8 or D+A7AC)
x87: FILD qword(numerator), FIMUL dword(width), FIDIV dword(divisor)
signed_qword = truncate_toward_zero(x87 result), via original 149630
rectangle extent bits = low_DWORD(signed_qword)
```

Channel 0 executes this at `108EAB/108EC1/108ECD`, conversion call `108ED1`,
extent write `108EDA`, renderer call `108EE3`. Channel 1 uses
`108F0F/108F1F/108F23`, conversion call `108F27`, extent write `108F35`, renderer
call `108F39`. Both call original conversion helper `149630..149656`.
It saves the x87 control word, sets rounding-control bits to truncation with
`OR AH,0C`, performs QWORD `FISTP`, restores the old control word, and returns
the full result in EDX:EAX. There is no 32-bit product overflow before division;
the low-DWORD extent can wrap after conversion.

For example, a numerator 1, width 83 and divisor 3 yields extent 27. Negative
width or a high-bit raw divisor can produce a negative quotient, because the
scaling divisor is signed even though the preceding clamp comparison is
unsigned. Numerator 0xFFFFFFFF, width 32767, divisor 1 exceeds signed DWORD
range; the QWORD result and its low DWORD are verified separately.

The model is bounded to x87 extended precision and nonzero divisors for enabled
channels. Products fit exactly within 47 magnitude bits in this input domain;
the integer oracle computes truncation without Python floor-division mistakes
for negative results. Tests exercise all four incoming rounding-control modes
with extended precision and verify full conversion bits and restored control
words. Other precision-control settings are outside this model.

There is no recovered zero-divisor guard: separate native runs reach the actual
`FIDIV` instruction with a zero divisor, then stop before executing it. The
model rejects this enabled-channel case rather than inventing exception or
rendering policy. Zero divisors with both handles negative remain supported.

Channel 0 also initializes rectangle left/top to zero and height from signed
WORD `D+A7A6`. If channel 0 is disabled and channel 1 is the first enabled
channel, that prefix only writes the extent; the other rectangle DWORDs retain
the explicitly poisoned stack bytes. No initialized full rectangle or completed
two-channel rendering is claimed for that path.

## Verification and remaining boundaries

Run from `C:/Users/risei/Desktop/God2/God2-Server`:

```powershell
python -B -m unittest discover -s tests/research -p test_current_battle_scalar_result.py -v
```

Final rerun on 2026-09-19: **8 tests passed**, exit 0, 2.007 seconds. The suite has
4,842 continuous queue-prefix/model comparisons and 376 direct display-helper
invocations, totaling 5,218 native invocations. The 4,842 comprise 728
position/entity-gate cases, 686 scalar/handle cases, 100 enabled-render cases,
3,072 opaque-byte cases and 256 seeded snapshots. The 376 comprise 360
clamp/render cases, 14 direct handle cases and two zero-divisor boundary cases.
Coverage includes both discriminators, every position 0..27,
null/signed entity gates, local forwarding, scalar DWORD extremes, display
handle boundaries, all values of every opaque byte, 256 seeded snapshots,
unsigned clamps, signed display divisors, negative widths, truncation, QWORD
conversion and low-DWORD storage. Truncated, trailing-byte and concatenated records,
unsupported discriminators and invalid model state fail closed.

The image is read/execute. Every executed instruction must fit a closed allowed
range. External game callees cannot return fake success; instruction-count
exhaustion cannot count as completion. Hooks verify ordered non-stack writes,
record read widths/offsets and input preservation. Complete mapped fixture
pages are compared in queue-prefix tests, preserving all fields outside the
documented writes. Native stop addresses, local forwarding payloads, original
return addresses and direct-helper callee stack cleanup are checked. No code
is patched and no original helper is replaced. `-B` prevents bytecode writes.

Exact unqualified continuations are:

- `01BDC0`, called by `108EE3` or `108F39`: renderer boundary with computed
  extent supplied. The first divisor-triggered render can stop progress before
  the clamp. Disabled-channel fixtures reach the later clamp through genuine
  original returns; this does not establish successful visible rendering.
- `0E71E0`, called by `117309` or `11745E`: local scalar snapshot forwarding.
  Its body is not executed or assigned persistent-state semantics.
- `12D8C0`, called by `117388`: side-1 discriminator-0 wrapper. Its body and
  any subsequent `12D840` call are not qualified by this continuation.

The recovered arithmetic is display clamping, scaling and conversion of
supplied values. How those values were produced remains unknown, including
damage, attack/defense interaction, random rolls, skill coefficients, resource
deduction, HP mutation authority and rounding in a server combat calculation.
This local result must not be substituted for any missing original formula.
