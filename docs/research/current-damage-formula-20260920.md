# Current received-result arithmetic, 2026-09-20

Recovered a new computation: **inbound battle-result WORDs accumulate into
per-target DWORDs, which the client applies to actor scalars using wrapping
addition, a sign-based zero floor, and a signed cap comparison**. This changes
actor storage, not just display geometry. An attack/defense-to-damage formula or
skill coefficient was not established. The findings below do not imply that no
such formula exists elsewhere in the client.

Only these new files were written under `C:/Users/risei/Desktop/God2/God2-Server`:

- `tools/strike_lab/current_damage_formula.py`
- `tests/research/test_current_damage_formula.py`
- `docs/research/current-damage-formula-20260920.md`

No optional artifact was written; the CLI prints executable evidence as JSON.
No existing/runtime/DB/CMake/shared files, archives, desktop, network or child
agents were used or changed. The requested recovery module and prior validation
document were read once. No target matrix was rerun.

## Executed dataflow

The starting clue was the known supplied-result consumers writing actor
`+DE8/+DEC/+DF0/+DF4`. A bounded cross-reference scan of mapped RVAs
`110000..131000` found arithmetic writers `128A70` and `128AC0`. Following their
callers backward reached result accumulators and the `83/0D` participant consumer.
The previous `86/0,1` copy/display path was not counted as a new proof.

The new receive test runs continuously from post-copy battle opcode dispatch
`114332` through `116AE0`, `117183 -> 12C520`, and returns to `1143A1`.
Fixtures supply a complete 15-byte logical record: opcode `83`, subtype `0D`,
source position 0, target-mask bit 1, nonzero WORD `+11=1`, and existing actor
action state `+239=1`, accumulator index `+2C4=0`. This is offline execution of
the inbound consumer, not a live server capture or a transport decoder test.

| Input/operation | Native proof |
| --- | --- |
| Logical record WORD `+9` | `12CB2D/12CB3A/12CB47` reads exactly two bytes and sign-extends them |
| Logical record BYTE `+13` | `12CB16`, table `12CCAC`, jump table `12CC98` select the arithmetic arm |
| Selectors 0..5 | `12CB31`: add signed WORD to source `+B60 + index*8`, modulo 2^32 |
| Selector 9 | `12CB3E`: same addition to source `+B64 + index*8` |
| Selector 20 decimal | `12CB4B`: replace first accumulator with the sign-extended WORD |
| Selectors 7,8 | No accumulator change; this branch does not read WORD `+9` |
| Result destination | Native stores packed target at source `+62E+index`; `12B8C4..12B8D9` decodes it and calls original `11E6E0` |
| Accumulator pointer | `12B8A1` computes source `+B60`; the first-entry prefix retains it at stack `+5C` |
| Actual scalar calls | `12BB91 -> 128A70` applies first DWORD; `12BBE5 -> 128AC0` applies second |

No multiplier, attack stat or defense stat is read by the executed accumulator
arithmetic. The amount originates in logical record `+9`; this proves its origin
at the client-consumer boundary, not how the sending side calculated it.

There are **three explicit execution stages**, not a fabricated continuous run:

1. The receive path above, through its original return to `1143A1`.
2. A separate function entry at `12B870`, stopping at `12B8DE` immediately after
   original target lookup. It derives the accumulator pointer and target from the
   receive-produced actor state; neither pointer is guessed as a helper return.
3. An independently declared post-formatting entry at `12BB84`, with `ESI` equal
   to the manager, `EDI` the target, and `[ESP+6C]` the accumulator pointer. The
   original code removes 16 stack bytes and calls both scalar helpers, stopping
   at `12BBEA` before display refresh. The intervening resource/formatting path
   is unexecuted. No formatter or other callee is replaced or made to return.

## Exact application arithmetic

For channel 0, `current = actor[DE8]`, `cap = actor[DF0]`; channel 1 uses
`DEC/DF4`. All storage is raw DWORDs. The supplied delta is a DWORD, potentially
an accumulation of sign-extended received WORDs.

```text
sum_bits = (current_bits + delta_bits) mod 2^32
if bit31(sum_bits) == 1:
    next_bits = 0
else if int32(sum_bits) > int32(cap_bits):
    next_bits = cap_bits
else:
    next_bits = sum_bits
```

Channel 0's ADD/JNS/CMP/JLE are `128A79/128A7F/128A93/128A95`; channel 1's are
`128AC9/128ACF/128AE3/128AE5`. This is not an overflow-safe saturating addition.
The negative-sum branch does not even read the cap. Cap storage is unchanged.
If the actor equals `[manager+2DC]`, the helper also writes `1` to
`manager+A89785C`; its broader notification semantics are not inferred.

| Counterfactual | Executed result |
| --- | --- |
| Current `100`, delta `-30`, cap `200` | `70` |
| Current `10`, delta `-30`, cap `200` | `0` |
| Current `100`, delta `100`, cap `150` | `150` |
| `7FFFFFFF + 1`, cap `7FFFFFFF` | `0`, because the wrapped result has its sign bit set |
| `FFFFFFFF + 2`, cap `100` | `1` |
| Current `0`, delta `1`, cap `FFFFFFFF` | `FFFFFFFF`, because the cap comparison is signed |

For source accumulators `(10,20)`, target scalars `(100,50)` and caps `(200,80)`,
received WORD `FFE2` (-30) gives target `(80,70)` with selector 0, `(110,40)` with
selector 9, and `(70,70)` with selector 20. Changing only the WORD to `FFE3`
changes selector-0 output to `(81,70)`. Sevenfold scaling, unsigned-WORD loading
and ordinary saturating addition all contradict executed counterexamples.

No floating-point operation, division or rounding step occurs in these arithmetic
paths. The zero floor/caps above apply to actor scalar updates; they do not prove
a minimum damage, damage cap, authoritative HP/MP label or resource-cost rule.
The missing damage-production edge is upstream of the received WORD: no verified
binding from attack/defense and selected skill to that amount was found in this
bounded trace. Resource/animation/formatting continuations are also not qualified.

## Source pins and checks

Only the mapped current image supplies native instructions/data:
`artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`.
SHA-256: `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
Base VA `400000`, file offset equals RVA; PE sections are not used.
All ranges below have exclusive ends; the CLI prints these hashes and the
executed packet-read RVAs/offsets for its examples.

| Slice | SHA-256 |
| --- | --- |
| `12CABA..12CB8E` accumulator | `2945bef0b4fa94b6562c96bbb5b99ebb7d513f4b0912144aee7d09f26677f35f` |
| `12CC98..12CCAC` jump targets | `d802b61a3f6a0c1b1c3cc83671e29ae7d42e8483c4ba17b454a0b1ac58bd3941` |
| `12CCAC..12CCC1` selector table | `0aca01dcf67145e8e1de93c8c6080932bb29a50bce915f6ff062a3842f5cad5d` |
| `12B870..12B8DE` application prefix | `a37a4fce8a91a6b975db285c798666a89446de924c4392360de7c439c940c9e1` |
| `12BB84..12BB98` first application | `8423886c57e27758b4b5564cc56664ca14814ab4b755cf6506a521fdd8a14bd7` |
| `12BBDA..12BBEA` second application | `eb7142db2b3d03e4f70ae6f1f441f64699075b281873617374d0ebf7f66b5d6d` |
| `128A70..128ABD` channel 0 | `ef45f0e76142a4a7924ae32a914f5bf2a60556c95b7f102e0db9da676695e01a` |
| `128AC0..128B0D` channel 1 | `5cda52d3024a4e2c1da4fb0d705a35b2e19fa5aba4bb3ec6106cc5b450494426` |

Actual commands from the server workspace:

```powershell
python -B -m unittest discover -s tests/research -p test_current_damage_formula.py -v
# Exit 0: 6 tests, 0.580 seconds, no skips.
python -B -m tools.strike_lab.current_damage_formula
# Exit 0: JSON with four executed examples, source hash, slice hashes and reads.
```

The suite checks 70 received-WORD/selector cases, 52 direct clamp cases, original
pointer/target derivation, both actual scalar calls under declared live-ins,
packet-value/selector counterfactuals and four actor-poison variants. It checks
whole actor snapshots, input preservation, exact accumulator writes, clamp data
reads, conditional flag writes, stops and stack cleanup. These are computational
and dataflow checks, not a system-coverage count. Image memory is read/execute;
closed native ranges and instruction budgets are enforced (5,000 receive, 512
application stage, 128 direct scalar). Unknown calls cannot return fake success.

Main review added exact integer-type checks on selector/channel arguments and
malformed-record/bounds regressions. The resulting seven-test suite independently
passes in0.553s; registered integration CTest also passes. This does not change
the received-result-only authority boundary above.
