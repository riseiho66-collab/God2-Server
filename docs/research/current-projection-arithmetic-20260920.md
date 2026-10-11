# Unclassified Native Projection Arithmetic

Status: NATIVE_ISOLATED_ARITHMETIC_NOT_DAMAGE_FORMULA.

This investigation follows the 119E30 lead in the combat formula frontier.
The new executable proof is `tools/strike_lab/current_projection_arithmetic.py`.
It executes unchanged instructions in the current pinned image, starting at
RVA 11A08F and stopping before 11A10E. It does not execute the full function,
its entry/callers, string formatting, or an authoritative battle transaction.
Descriptor low nibbles 3/4 stop at 11A281 before the alternate arm executes.

Image SHA256: `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
Slice SHA256: `eab22c1e2a8535a23911dfbdc51d8e86a59b2c0d0692790721ba47e496cbdd77`.

## Actual Arithmetic

Descriptor is read from owner+A9EA505+32*row+8*column. Supplied K is read
from owner+A9EA508+32*row+8*column. The stack and registers are explicit
synthetic live-ins, not a captured current battle. Read-only source pages
prevent the executed instructions from modifying these inputs.

For the qualified arithmetic arm:

```text
D = mode != 0 ? low32(K * (descriptor >> 4)) : K
projected = int32(current) > int32(D) ? low32(current - D) : 0
```

The comparison is signed; multiplication/subtraction wrap at 32 bits. Thus
current100, K40000000h, descriptor21h, mode1 produces 80000064h, NOT ordinary
saturating damage. Current100, KFFFFFFFFh, descriptor11h produces101.
These synthetic overflow tests discriminate arithmetic; they are not valid
gameplay-value claims. Ordinary current100/K20/descriptor31h gives40 in
mode1 and80 in mode0; current50 gives0 in mode1.

Only stack+74 and the selected stack+9C+4*slot are written in this slice.
No attack/defense field is read and no actor HP is written here. The full
routine's inspected prefix copies actor+DE8 into this stack area in one mode;
its inspected tail formats strings and calls96990. Neither establishes that
the arithmetic is an authoritative damage generator.

## Checks

Four unittest methods pass. They include105 native arithmetic runs across
mode, multiplier and signed/overflow boundaries; three indexed-address runs;
four alternate-arm stops; plus rejected invalid synthetic inputs. Tests check
the native output, exact source read addresses, permitted write destinations,
unchanged inputs and a bounded native stop. There are no patched instructions,
fake callee returns, live network connections, or database writes.

```powershell
python -B -m unittest discover -s tests/research -p test_current_projection_arithmetic.py -v
python -B -m tools.strike_lab.current_projection_arithmetic
```

## Still Missing

### Newly Qualified Entry Gate

`current_projection_gate.py` executes unchanged instructions from 119E44 to
119E6E (admitted) or 11A973 (rejected). The preceding FF15 call at 119E3E uses
IAT VA5707BC; the pinned unpacked PE identifies it as winmm.dll/timeGetTime.
The OS call is not executed: EAX is an explicit synthetic clock-result live-in.

The native gate requires owner+A9EA4F0 to be nonzero and unsigned low32(now -
owner+A9EA598) >= 2000. Admitted execution writes now to +A9EA598 at119E68;
rejected execution writes nothing. Fifty-four native runs check count values
0/1/FFFFFFFF, three previous timestamps, six elapsed values and DWORD wrap.
Exact write sets, unchanged count and full input-image identities are checked.
Three unittest methods pass. This qualifies a time/count gate, not a natural
caller, populated descriptor producer, server charge event or damage formula.
Together with the separately proven text sink, it cautions against treating
the isolated multiply/subtract operation as per-attack damage authority.

Follow-up `current-projection-sink-20260920.md` qualifies continuous execution
from the synthetic tail through a native text-message routine to the opcode2F
encoder boundary. This does not join the arithmetic to live combat and does
not make the multiplication a recovered damage formula.

The input-producer side investigation did not find populated K values or a
nonzero count producer. Main independently inspected initialization at
110EF7..110F04: 43 DWORDs at owner+A9EA4F0 are zeroed. It also inspected the
nearby receive queue calls at1195BC/1195D7 and copy destinations at11D550,
11D555,11D569: the copies target a buffer pointer loaded from queue+4, not
the adjacent inline descriptor array. Dequeue at114321 supplies the separate
owner+A9E9CB0 destination. Executed native length lookup for the candidate
opcodes1C,38,83..89 yields a maximum121 bytes, shorter than the2112-byte gap
to the count. This narrows ordinary queue-copy provenance; it does NOT exclude
separate downstream handler writes, pointer aliases, or computed callers.

The read-only agent reported no direct E8/E9 caller or literal entry pointer
for119E30 in its bounded scans. That negative scan is not a reachability proof.
The count/time entry gates and the unqualified populated-input producer remain
unresolved. The agent was closed after reporting; no native formula was promoted.

A populated K/descriptor producer, reachable live entry, attack/defense/skill
binding, and authoritative result writeback remain necessary before this can
be promoted to any native gameplay formula. Custom fixture rules are unchanged.
