# Current Critical-Formula Investigation

## Outcome

**Critical trigger and multiplier remain UNPROVED.** This batch recovered and
executed a concrete received-result arithmetic producer, plus a native RNG-to-
action-value chain. Neither may be installed as a critical gameplay rule.
This is a bounded computational/dataflow advance, not full critical-system
coverage, server authority, or proof that the client contains no critical formula.

Only the current pinned mapped image was executed:

- `artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`
- SHA256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`
- 3,174,400 bytes; base `00400000`; mapped file offset equals RVA. PE section
  offsets were not used. All addresses below are RVAs unless explicitly marked.

The JSON contains per-slice SHA256, explicit synthetic inputs, original
instruction counts, ordered non-stack reads/writes, stop RVAs, and trace hashes.
Read tuples are `(instruction_RVA, absolute_address, byte_count)`; writes append
the value. These are emulated original instructions, not live captures.

## Computational Advance

Let `R` be the explicit 14-byte action payload, `E` an existing type-0 actor,
`i = signed16(E.word[2C4])`, `d = signed16(R.word[8])`, and
`A/B = E.dword[B60/B64 + 8*i]` before execution. Tests enter original `12C520`
with `R.byte[0]=13`, `R.word[A]=2`, and `E.byte[239]=1` (existing collection,
not the initial clearing branch). Native `11E6E0` resolves the supplied actor.

Exact dataflow and order:

1. `12C5B6..12C5CC` dispatches the received action kind to `12CA2D`.
2. `12CA2D..12CAC4` reads `R.word[A]`; values 1/2/3 admit `12CAD0`.
   This harness executes value 2, not every admission branch.
3. `12CAD0/12CADB` loads the old index and sign-extends it. `12CADE/12CAE3`
   increments/stores the WORD counter BEFORE writing the old indexed entry.
4. `12CAEA/12CAEE` copies the received tag to `E.word[4D0+2*i]`.
   `12CAF6..12CB0B` updates its packed target byte at `E+62E+i`.
5. `12CB16` loads `R.byte[C]`. Tables `12CCAC` and `12CC98` select the
   following original arithmetic; these are numeric selectors, not named crit bits.

| Received type | Producer | Exact output |
|---|---|---|
| 0..5 | `12CB2D`, `12CB31` | `A' = (A + d) mod 2^32`; B unchanged |
| 9 | `12CB3A`, `12CB3E` | `B' = (B + d) mod 2^32`; A unchanged |
| 20 | `12CB47`, `12CB4B` | `A' = uint32(d)`; B unchanged |
| 7,8 | jump to `12CB6B` | Both unchanged in this prefix |
| 6,10..19 | `12CB54` | Diagnostic branch; stopped before its call |

No floating-point rounding occurs here: the input is signed 16-bit, the sum
wraps at 32 bits, and replacement sign-extends to 32 bits. There is no saturation
or multiplication in this producer. The counter and tag writes precede both
successful arithmetic and diagnostic stops; rejected selectors are NOT called
successful transactions. Counter live-ins tested are 0..3, not arbitrary safety
or capacity coverage. Execution stops before `12CB6B` or `12CB54`.

Examples actually executed: `FFFFFFFF + 1 -> 00000000`; `0 + FFFF -> FFFFFFFF`;
`7FFFFFFF + 7FFF -> 80007FFE`; replacement of any prior A by `8000 -> FFFF8000`.
Changing the initial accumulator changes the sum. A value that happens to be
twice a received amount is therefore not evidence of a critical multiplier.

This is an actual state-producing arithmetic path, **not a recovered critical
stat producer**. Binding these result slots to attacker/defender critical stats
or authoritative damage is still missing. No guessed stat names are attached.

## RNG Candidate

At `12A89D`, the current action setup calls `147D7F`. That routine first calls
OS/TLS helper `14E001`. Execution here explicitly starts at `147D84`, AFTER
that unexecuted helper, with a supplied TLS pointer and actual caller return
address `12A8A2` on the stack. Nothing is patched, and no callee return is stubbed.
From that boundary the native execution is continuous through the caller and
`12B060`, including both original actor lookups and original `1224A0`.

| RVA | Original operation |
|---|---|
| `147D84` | Read DWORD seed from TLS+14 |
| `147D87` | Multiply by `343FD` (214013), low 32 bits |
| `147D8D` | Add `269EC3` (2531011), low 32 bits |
| `147D93` | Store next seed back to TLS+14 |
| `147D98`, `147D9B` | Logical shift right 16, AND `7FFF` |
| `12A8A2..12A8A8` | CDQ; divisor 100; signed IDIV |
| `12A8B6`, `12A8C1` | Push remainder as value1, call `12B060` |
| `12B3CD/12B3D4` | Store WORD value1/value2 at actor+286/+288 |
| `12B48E..12B49C` | Sign-extend value1; prepare `HP %+d` formatter argument |

Exact recurrence: `s' = (214013*s + 2531011) mod 2^32`;
`r = (s' >> 16) & 32767`; `value1 = r % 100`. Since r is nonnegative,
IDIV truncation gives the usual nonnegative remainder. The original next-seed
write precedes the action WORD writes. The formatter is stopped before CALL.

This is **not evidence of a critical percentage roll**: this inspected chain
passes the remainder as an action amount, without a threshold comparison or
critical multiplication. Its pre-call setup is gated by `122380`, whose inspected
body tests point/rectangle selection against actor coordinates. We do not run
that point-selection prefix or claim a live combat event. The 49 explicit seeds
include carry/sign boundaries and seeds chosen by modular inversion to produce
outputs 0/1/49/50/98/99/100/101/199/200/32767. Each runs with zero/A5 actor padding.
The resulting read footprint touches only actor handle, +277, and action kind
in this chain, not a qualified critical stat. No probability distribution is inferred.

## Received Values And Flags

Existing `current_battle_result_fields.py` and its research document already
bind the S2C86 normalized DWORD to actor+DB8 through `12C409`, then to
`126270`. That proof was read, not rerun as new coverage. Inspected branches
test bits and select status/renderer operations; none has been independently
qualified as a critical-chance bit. In particular, do not rename bit 40,
01000000, or 02000000 to "critical" on this evidence.

New runs begin at `12C520`, execute original `12A8D0` state setup, and bind:

- Kind1: `12C612` reads type byte R+A; `12C615` reads WORD R+8;
  `12C631` calls the consumer with value2 zero and effect22.
- Kind4: `12C94F` reads type R+C; `12C952/12C956` read WORDs R+A/R+8;
  `12C96D` calls the consumer with effect22.
- `12A95F` really writes the action kind. `12B3CD/12B3D4` copy the value WORDs
  without multiplying. Numeric formatter arguments are signed extensions of
  these WORDs, including `8000 -> -32768` and `FFFF -> -1`.
- Types 6/7/8 instead select empty/defense/evasion text in these tested paths;
  the source WORD writes have already occurred. No type is named "critical".

These action runs exclude the packet-dispatch prefix and all formatter calls.
They prove received-payload binding at the native producer boundary, not a
new transport schema or upstream server calculation. Zero/A5 padding provides
an input counterfactual; it does not prove independence of all possible stats.

## Nearest Other Candidate

A bounded direct-call inspection of `147D7F` in `116000..12E000` found calls
at `11A908`, `12302F`, and `12A89D`. This is not a whole-image call graph.
`11A908` feeds remainder modulo10 into formatting. `12302F` writes remainder
modulo5 to actor+1E6, adjacent to floating multiplies at `123088/123093`.
Following those floating inputs upstream: `122B9E/122BA4/122BAF` pass
actor+DAC/+DA8/+256 as outputs to `2F570`, with manager coordinate-table inputs
and constant24. Their downstream integer products are passed to renderer
`1FC00` at `1230CB`. This is a static coordinate-dataflow candidate elimination,
not an executed reconstruction of `2F570` or a stat formula. Slice hashes pin
these inspected producer/consumer instructions in the JSON.

`recover_combat_rules.py` and existing combat-rule docs supply current skill
descriptions mentioning chance and 2x. Description data is not executable
proof: no qualified join from those skill records to a critical stat producer,
comparison, or multiply/round/store chain was recovered here. No archive,
network, UI, server, database, or shared runtime was touched.

## Reproduction

From `C:/Users/risei/Desktop/God2/God2-Server`:

```powershell
python -B -m tools.strike_lab.current_critical_formula --output artifacts/research/current-critical-formula-20260920.json
python -B -m unittest discover -s tests/research -p test_current_critical_formula.py -v
```

The deterministic CLI uses one VM and a 2,000-instruction bound per run. It
emits 98 RNG, 84 arithmetic, and 176 received-value counterfactuals: 358 total.
44 arithmetic runs stop at the diagnostic boundary, 40 before continuation.
The tests additionally run a five-step native RNG state chain, 20 initial-state
counterfactuals, independent byte-slice/table checks, corrupted-observation
checks for signedness/wrap/doubling/source loss, and a second full native report
for byte-for-byte determinism. They do not patch or mutate the original image.

Actual results on 2026-09-20: CLI exit 0, 358 cases, 0.621 seconds command wall
time; unittest exit 0, 8 tests in 0.707 seconds. Two CLI emissions had identical
SHA256 `6be2f1d46b06e2a32dd9385ee4aaef611ac395a7be86b2baa6a2aa1a4c1bfcb2`.
Timing is recorded here rather than in the deterministic JSON.

Only new files owned by this task:

- `tools/strike_lab/current_critical_formula.py`
- `tests/research/test_current_critical_formula.py`
- `docs/research/current-critical-formula-20260920.md`
- `artifacts/research/current-critical-formula-20260920.json`

Missing proof remains precise: native critical-stat identity and producer;
its source binding to attacker/defender/skill; the RNG threshold comparison;
critical output-bit semantics; multiplier, order, rounding and clamps; and
the authoritative transaction applying that result. This batch cannot honestly
supply an actual CRIT formula. No default rule is exported.
