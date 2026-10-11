# Current battle result fields, 2026-09-19

Identified S2C logical opcode **0x86**, native size **17 bytes**, and qualified
its **record discriminator 3** consumer. This lane normalizes and
copies transmitted result bits. It does not calculate attack, defense, or damage.
The original damage formula remains unknown. In particular, entity `+DB8` is
subsequently used for bit tests; naming it a damage amount would be unsupported.

## Owned files and authority

Only three new files belong to this task:

- `tools/strike_lab/current_battle_result_fields.py`
- `tests/research/test_current_battle_result_fields.py`
- `docs/research/current-battle-result-fields-20260919.md`

The only source-data file opened by the new test suite is
`artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`.
Its SHA-256 is
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
The whole image is checked before execution; a changed image fails the suite.
All addresses below are RVAs, mapped at VA `00400000`, with RVA equal to image
offset. Unicorn comes from `artifacts/tooling/crypto-oracle-python`.

The starting context was the current target-setup and command proofs:
`11EE90` constructs targets, while `118E50 -> 0132E0`, stopped at `1191EE`,
queues command identity. This task follows the current receive/queue dispatcher
into a result consumer. It does **not** establish a request/response pairing
between an individual command and a particular 0x86 record. No retired corpus,
historical opcode lead, captured old packet, or guessed formula supplies authority.

No runtime, CMake, world entry, shared helper, UI, game process, production DB,
or other task file was changed or exercised. There is no sender or integration;
the Python model has `runtime_mutation_enabled = False`. That constant records
scope, rather than providing a runtime enforcement mechanism.

## Opcode and execution route

| Location | Current instruction evidence |
| --- | --- |
| `001200..001215` | Native logical-size dispatch |
| `00153C` | Size table DWORD for 0x86 points to `00124C` |
| `00124C..001251` | Returns `0x11` (17 bytes) |
| `1193C4..1193E6` | Receive dispatch reads logical opcode at record +0 |
| `119A8A`, `119914` | 0x86 maps to index 3, then `1195B1` |
| `1195B1..1195C7` | Static receive arm gets size via `015840`, passes record and size to queue helper `11D4E0` |
| `114332..114357` | Battle queue dispatch reads the same logical opcode |
| `114321..11432D` | Sets EDI to `B+A9E9CB0`, destination of the queued-record copy |
| `1146C6`, `114648` | 0x86 maps to index 5, then `114464` |
| `114464..114479` | Reads byte `B+A9E9CB1`, which is copied record +1; dispatches values 0..6 |
| `1146D8` | State 3 table entry points to `1144AE` |
| `1144AE..1144B1` | Passes the logical record pointer to `117480`, ECX = B |

The size function, receive dispatch to `1195B1`, and copy-call argument prefix
`114321..11432D` execute independently in the tests. Neither queue copy is
executed. Each main comparison supplies identical original and copied records,
with EBP pointing to the original and EDI to `B+A9E9CB0`, then runs
continuously from `114332` through the original state dispatch, `117480`,
`12C3E0`, and the complete `11E6E0` lookup, stopping at `126270` before its first
instruction. Null/negative-entity paths instead return through the real parser
to `1144B6`. These are independent synthetic queue invocations, not a full
network receive or live settlement. Discriminator 3 is explicitly required at
record +1 and in the model's state; it is not identified with skill kind,
selected skill, or C2S action 3. The stored byte and record +1 are the same
memory location, not independent state variables.

## Proven input and writes

Let `R = B+A9E9CB0` be the 17-byte mutable record copy, `B` the battle object,
`T = B+144938`, and `E`
the type-0 entity selected by the lookup. Offsets below include the opcode.

| Logical field | Proven use in this state-3 branch |
| --- | --- |
| `+0`, byte | Opcode 0x86 in the queue dispatcher |
| `+1`, byte | Discriminator 3 selects `117480` through `114464` |
| `+2`, byte | Zero-extended position; side = position / 14, slot = position % 14 |
| `+3`, WORD LE | Copied to `E+278` after the entity gate |
| `+5`, DWORD LE | If bit 0 is set, overwrite the entire input DWORD with 1; otherwise preserve it |
| `+9..16` | No reads in this qualified branch; retained as opaque bytes |

The model admits positions 0..27 only, corresponding to two fourteen-slot
sides. This is an explicit research bound. It is not a claim that the native
parser rejects other bytes safely. The actual accessor has diagnostic paths
outside this domain; they are not executed or replaced by successful returns.

The precise writes, in order, are:

1. `1174B7` tests input byte `R+5` bit 0. If set, `1174C1` writes DWORD 1 at
   `R+5`. This occurs even when the later lookup is null or its gate fails.
2. When side is zero and slot equals byte `B+51`, `1174D1..1174D4` copies the
   normalized DWORD into `B+A9E9C74`. This also precedes the entity gate.
3. `1174EB` calls `12C3E0(side, slot, R+1)` on T. Its call at `12C3F1`
   executes `11E6E0(side, slot, 0)`. The actual type-0 pointer load is from
   `T+38+24*(side*14+slot)` at `11E75A`.
4. A null E returns. Otherwise `12C3FA` tests signed WORD `E+1A`; a negative
   value returns. No alive/HP/entity-identity meaning is assigned to this WORD.
5. `12C406..12C409` copies the normalized DWORD `R+5` to `E+DB8`.
   `12C40F..12C413` copies WORD `R+3` to `E+278`.
6. `12C41C` calls `126270(E)` with ECX = T. The tested primary prefix stops
   at that callee's entry, with the original return address `12C421` and E
   still on the original call stack.

For example, transmitted `0x80000003` becomes 1, while `0x80000002` remains
unchanged. This is bit-triggered normalization, not saturation, damage clamping,
an attack/defense calculation, or signed arithmetic on a damage amount.
The WORD is copied without scaling or interpretation. All other input/entity
bytes, and all other bytes on the mapped battle/context pages, remain intact
within this prefix. Downstream code can still change state after the stop.

`State` requires the dispatch state, local slot, previous cache DWORD and an
explicit 4096-byte selected entity snapshot (or None). `consume` returns the
updated record, side/slot, cache, entity snapshot and next-consumer location.
It does not access live memory or validate ownership, a turn, legal targets,
packet provenance, framing, or whether the supplied entity belongs to a battle.
The 4096-byte snapshot is a fixture bound, not a recovered complete entity size.

## Verification

Run from `C:/Users/risei/Desktop/God2/God2-Server`:

```powershell
python -B -m unittest discover -s tests/research -p test_current_battle_result_fields.py -v
```

Result on 2026-09-19: **8 tests passed**, exit 0. The suite makes
4,257 full model/native comparisons, plus size, copy-argument and dispatch checks:

- Every position 0..27 against every local slot 0..13.
- Zero, high-bit and all-one DWORD boundaries, all individual bits, and bit 0
  combined with every bit, crossed with WORD boundaries and both sides.
- Null pointers and signed entity markers -32768, -1, 0, 1, 32767; cache and
  input writes are checked even when the entity is not updated.
- Every byte value at each of the eight opaque offsets. Original queue-record
  placement alternates between the beginning and end of a page with unmapped
  neighbors. The mutable copy remains at its actual fixed battle-object offset;
  exact read/write hooks qualify that copy's bounds.
- 256 reproducible random raw records and complete entity snapshots.
- Model rejection of all truncations, trailing/concatenated/framed bytes,
  wrong opcodes/discriminators, positions outside the qualified domain and
  invalid state.
- A continuation on the unchanged native stack through `126283` to stop
  `126289`, proving that the next consumer loads the copied `E+DB8` DWORD.

Code pages are read/execute, and every executed instruction must fit wholly
inside closed allowlisted ranges. No game instruction is patched; no original
callee is stubbed. The hook rejects unexpected writes, including to the input
outside mutable `R+5..8`. The original queue record must remain unchanged.
It checks the exact ordered non-stack writes and exact record
read offsets/widths, as well as all five complete fixture pages. Unchanged input
bytes are therefore checked even though the original parser requires writable
input. Native stops and stack arguments are verified; exhausting the instruction
budget cannot count as completion. Python runs with `-B`, leaving no bytecode.

## Remaining consumer boundary

The next concrete consumer is **126270**, called at **12C41C**. Its signed
entity gate and DWORD load at **126283** are executed by the continuation test.
Static inspection beyond that test shows bit tests at `1262A0` (bits 1..5),
`1262C3` (0x40), `126379` (0x01000000), and `1263B9` (0x02000000). The first
unexecuted instruction after the continuation stop is `126289`; the next calls
on its 0x40 branches are `1262CB -> 120AE0` and `1262D9 -> 120B90`.
These are exact unqualified follow-up locations, not identified damage formulas.

No attack/defense formula, hit probability, random roll, skill coefficient,
rounding rule, damage production, or authoritative HP mutation was found in
the executed prefix. The other state-dependent consumers of opcode 0x86 remain
outside this model. This local negative result does not prove that the whole
client lacks damage arithmetic. Transmitted result storage must not be promoted
to an original damage formula or a server combat implementation. World entry
and any future integration remain with main.
