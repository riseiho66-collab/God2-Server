# Current Attack/Defense Producer Search, 2026-09-20

## Result And Scope

**Recovered actual wild-monster attack/defense tuples: 0. Actual wild-monster
values: 0. New combat-stat formulas: 0.** This is a bounded producer audit of
the previously identified character and owned-companion fields, not monster
stat recovery. Their exact four semantic labels belong to the separate label
investigation; no label is assigned here by borrowing card data.

New findings are initialization and row-management writes: an original `999`
constant to character `A+94`, broad zeroing, and opcode D9 row compaction and
clearing. These are not server rules, monster records, or growth formulas.
No new tools/tests are added for this negative combat-formula result. Only this
document is added; all existing code remains unchanged.

Notation: `R` is the character root, `A=R+90`, `U` is the owner, and
`[U+86888]=A`. This alias is established by existing native binding proof at
`81C81` and `E7CAB`, not inferred from equal-looking field offsets. An owned
companion row is `C_i=A+D8+i*3EC`, selected through `[A+D0]`. All offsets and
RVAs below are hexadecimal unless explicitly marked decimal. Body offsets
exclude the opcode; logical offsets include it.

## Confirmed Writers

| Object/range | Writer RVA | Source and operation | Qualification |
| --- | --- | --- | --- |
| `A+98/94/A0/9C`, DWORD | `E66BE/E66CD/E66DC/E66EB` | Opcode 2C body `2C/30/34/38`, respectively | Existing native packet-copy proof reused, not rerun |
| `C_i+38/3A/3C/3E`, WORD | `AA276/AA27E/AA286/AA28E` | Opcode 31 body `10/12/14/16`, respectively | Existing writer proof reused; signed byte body 0 selects matching row key |
| `R+90 .. R+4594` exclusive | `68326` | `rep stosd`, EAX=0, ECX=1141 | Newly executed; clears all four role fields and all owned rows |
| `R+124 = A+94` | `687E1` | `mov dword ptr [ebp+124],3E7` | Newly executed; literal decimal 999, initialization only |
| `R+90 .. R+4594` exclusive | `68904` | Same size zeroing on first-argument-null branch of 68160 | Newly executed; no 999 store on this branch |
| `R+168 .. R+4028` exclusive | `68148` | Zero 16 rows, FB0 DWORDs; also clear count/selection nearby | Existing same-VM reset proof reused |
| `C_i .. C_i+3EC` | `A9F04` | Copy next complete row to current row during removal | Newly executed D9 management branch; copies four fields unchanged |
| Last active row | `A9F83` | Clear FB DWORDs at `A+D8+(count-1)*3EC` | Newly executed |
| Row 15, `A+3BAC` | `A9FCB` | Clear FB DWORDs in the special index-15 removal branch | Newly executed |

The normal initializer `68160` receives R as its second argument: `681F6`
loads it into EBP. `65176/65183/65194` supply the embedded character root
`world+1539683C` to that function. `68315..68326` clears 4504 bytes before
the later `687E1` constant store. The constant instruction bytes are
`C7 85 24 01 00 00 E7 03 00 00`. It is not a table read or an arithmetic
derivation. The separate tested slices do not claim the intervening resource
and initialization calls have executed.

`68120` is called by `68827` during initialization and `6B3EB` in the world
opcode CF branch (branch entry `6B30E`, logical length 177 decimal). It resets
the owned-companion rows, not the four role DWORDs.

## Packet And Buffer Provenance

The world dispatcher calls `13420` at `68B24`, then `13650` at `68B47`, with
mode argument 1. `1365D` returns `connection+2CC4`; `68B4C` retains this logical
packet pointer in EBX. `68B61` dispatches through image table `6B5D4`.

| Opcode | Logical bytes, decimal | World dispatch/call | Destination and purpose |
| --- | --- | --- | --- |
| 2C | 61 | `69EDE`, call `69EE6 -> E6600` | Owner's character property block A, not a side-indexed battle actor |
| 31 | 29 | `69FA9`, call `69FB1 -> AA200` | Matching owned-companion row; four WORDs are logical offsets 11/13/15/17 hex |
| D2 | 21 | `6B2FC`, call `6B304 -> 9F540` | Owner's separate 20-byte addition block at `U+866BC` |
| D9 | 2 | `69F97`, call `69F9F -> A9E90` | Signed key at body 0; remove/compact an owned row, not supply new stats |

The battle-side packet forwarding routine `119370` calls `13420` at `119398`
and `13650` at `1193BD` with mode argument 2. It retains the same kind of
`connection+2CC4` logical-buffer pointer in ESI at `1193C2`; its owner is
`[battle+20]`. Its two-level dispatch (`1193DA/1193E0`, tables
`119A04/119908`) sends 2C to `11948A -> 11948F -> E6600`, and D2 to
`1194D2 -> 1194D7 -> 9F540`. Both increment the packet pointer past the opcode.
In this dispatch, 31 and D9 select the default `1198A1` branch. The existence
of battle-context forwarding does not turn the destination into a wild actor.

`9F549/9F554` copy five DWORDs from the D2 body into `U+866BC`; the first
four WORDs are at `+866BC/+866BE/+866C0/+866C2`. The prior consumer analysis
found zero-extended WORD additions at `A9C11/A9C38/A9C5F/A9C86` for selected
row keys 101..108 decimal. Those sums are formatting arguments, not writes
back into `C_i+38..3E`. This audit does not rerun or expand that UI path and
does not interpret it as a combat formula. The inspected exact-displacement
and LEA search found `9F549` as the concrete pointer-producing writer lead
for this addition block; arbitrary indirect aliases remain outside that claim.

## False Positives And Search Boundary

The static search covered mapped `.text` RVA `[1000,170000)`, first through
149000 and then its suffix. It included explicit memory-write operands for
the eight offsets, the role root aliases `124/128/12C/130`, first-row root
aliases `1A0/1A2/1A4/1A6`, overlapping smaller writes, x87 stores, LEA/pointer
adjustments, and direct callers of the identified producers. Function-entry
disassembly and object provenance were used for the listed conclusions.
Linear decoding also crosses jump tables: byte-pattern hits are not facts
about instructions, and matching offsets are not object identity.

Concrete exclusions:

- `15DFE/15E04/15E0A/15E16` are in `15CE0`, called with VA `5B49A8` by
  `12BE0/12BE5`. `12C19` indexes that same global by opcode*4. These are packet
  length table entries, not character properties.
- `A6039/A6079/A60BC/A60FC/A613C` perform bitfield packing, but their receiver
  comes from `U+232EBC`, for example `AC480 -> AC486 -> A6010`, not `[U+86888]`.
  `A6010` also follows its own `+DC` owner pointer and checks owner `+85A30`.
  Their masks and shifts must not be reported as an attack/defense formula.
- `FB121/FB13E/FB184/FB194` write floating accumulators at `+98/+9C` in
  `FB0D0`; its caller `FB290` traverses another manager's records beginning
  at `this+18`, with stride 268, not character roots or 3EC companion rows.
  These are not a demonstrated target-object producer.
- `D54D2/D5502/D551C..D554C` write owner-local `+3C/+3A/+3E` in an item/control
  path using owner `+85610` and `59A60`, not the selected companion row.

Within the object-proven paths above, no non-copy stat calculation writing the
four role DWORDs or four companion WORDs was established. This is NOT a
global claim that the client has no such calculation. Indirect/vtable calls,
general-purpose copies with aliases, other pointer bases, malformed-input
overwrites, and other actor types have not been exhaustively excluded.
The row append function AA040 supplies names/keys and selection; it does not
provide these four values on the inspected bounded valid-name path.

## Lightweight Native Checks

One inline `python -B` run reused `current_role_progression.NativeProbe` and
`current_battle_character_binding.NativeBattleCharacterBinding._run` on an
isolated VM. The pinned code stayed unchanged. No callee adapters, fake game
returns, source table records, UI calls, resource preload, or live processes
were used. Execution had allowlisted PCs/writes, a 30,000-instruction cap per
stage and a one-second timeout per stage. Total command time: 0.407 seconds,
exit 0, all assertions passed.

| Case | Native outcome |
| --- | --- |
| `68315 -> 68328`, poisoned root | Exactly 17,668 nonstack bytes zeroed; four role fields zero; end guard retained |
| Separate `687E1 -> 687EB` | Exactly one DWORD write of 999 to R+124; resulting staged role tuple `(999,0,0,0)` |
| `688D0 -> 68906`, ESI=0, explicit root argument | Four role fields zero; exactly 17,668-byte data clear, plus 23 bytes of prefix initialization |
| D9, two synthetic rows, delete key 1 | `69F97 -> AA012`; next row's synthetic `(111,122,133,144)` copied unchanged, count 1, last row cleared |
| D9, sixteen synthetic rows, delete key 16 | `69F97 -> AA012`; count 15, row 15 cleared, first row unchanged |

The D9 inputs are distinguishable test sentinels, NOT native-source stat values.
AA012 is the unexecuted refresh call; no successful UI return is assumed.
Only native initialization constants zero and 999 were observed as newly
verified intrinsic values. Neither contributes a wild-monster value or tuple.

## Source Identity And Remaining Edge

Mapped image: `artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`.
SHA-256: `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
Base is 400000; RVA equals mapped file offset. New executed interval hashes:

| RVA interval, end exclusive | SHA-256 |
| --- | --- |
| `68315..68328` | `57fa26c2f5a333d1d913a3577767afbb80393b7ecc05abec609efe8158f0bd3f` |
| `687E1..687EB` | `3de2dedd4c23a16e9847be1a5dec0080473deeefadf4589225b31f2e80733dc9` |
| `688D0..68906` | `583f4ac6c93b2884d319531bcf9f5bfbf9cc613873e00ecf4229da345cfc7bd1` |
| `69F97..69FA4` | `3ed6e48047341fa91707b3bdd387f0e397281f33d9ab932c3ca4eee200f81bb4` |
| `A9E90..AA012` | `fa6d9e41be7c9769b31fbbd4dfe2e1c201007d627bdcd60a9a54055f50558246` |

Reused current-tool hashes at execution time:

- `current_role_progression.py`: `2be3a9ae2d06f5500d0447911405820efa3bf3e473662904f5fb18dbf55c07a0`.
- `current_battle_character_binding.py`: `55a2efc3619dc2606c0e2a594a65a05fca167c96cc8e86ea48236b3839879f82`.
- Read-only packet-source reference `current_progression_source.py`:
  `bd5ae0347bb00fad3484e90570c12d847f7e0ee539f75d290a10206e6f8c26df`.

The concrete remaining edge is a source-backed writer into the actual wild
battle actor's four attack/defense fields, with that actor's identity and
offsets independently established. None of the role initializer, 2C, owned
row 31/D9, or D2 owner addition block establishes that edge. Do not transplant
their values to wild monsters or infer a server-side formula from formatting.
No runtime/schema/DB changes, no new child workers, and no background process
were started. The requested `send_input` tool was unavailable; findings were
reported in task commentary instead.
