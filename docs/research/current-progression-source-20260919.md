# Current Progression Source: S2C31 Scalar Boundary

Gameplay progression remains **OPEN**. This deliverable validates an original
client receive-buffer writer, packed scalar source, percent conversion, and
horizontal bar geometry. It does not recover an authoritative original server
EXP requirement, level transition, or growth formula. An emulator is not live
playable proof; `runtime_verified` and `runtime_eligible` are false.

The existing current role and companion progression helpers/reports were read
first. Their GodLevel text, QualityStar formatting, role percent, and instance
copy results are not presented as new gameplay recovery. Historical portions
of existing reports were ignored. No retired archive or evidence corpus was
accessed, and none is a dependency of these new files.

## Owned Files and Authority

Only these three new files were added:

- `tools/strike_lab/current_progression_source.py`
- `tests/research/test_current_progression_source.py`
- `docs/research/current-progression-source-20260919.md`

Server root: `C:/Users/risei/Desktop/God2/God2-Server`.
Client root: `C:/Users/risei/Desktop/God2/God2`.
Native image: `artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`.
SHA256: `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
All native addresses below are hexadecimal RVAs, also mapped-file offsets;
VA = RVA + `400000`. Packet offsets are decimal and include the opcode.

The only other evidence file read by the CLI is the current client's
`Data2/Patch/Comm/message.csvZ`, SHA256
`5cd34cce66feae96d947cd45e32984765ce625673c0fb19c73cb63d7d9178598`.
Its decoded SHA256 is
`370bd6ed9b4892f57190fc7a8dab14061b3e844b0aa9d0171611a9cbab61b5f8`.
ProgramMsg 165 is physical line 2191, decoded offset 90275, exact row hex
`3136352c25362e3266a2480d0a`. Its format is `%6.2f` followed by CP950 bytes
`A248` (fullwidth percent sign). The existing `omega_assets.decode_csvz`
decoder is reused solely for this pinned file; no other recovery importer runs.

## Executed Source Contract

The upstream byte writer is newly executed, including the original opcode
length lookup. An already decoded byte queue is the explicit starting fixture;
its bytes are synthetic, not captured current-server traffic.

| Stage | Original instructions and observed contract |
| --- | --- |
| Logical assembly | Start `13497`, connection pending count zero, populated decoded queue |
| Opcode length | `134C8 -> 15840 -> 1000 -> 1200`; indirect read at `1324 + 4*31 = 13E8` reaches `12FA`, returns 29 |
| Byte source | `12520 -> 10AF0`, queue-relative `C10 + read_cursor` |
| Actual writer | `10B34` copies one byte into connection-relative `2CC4 + pending_count`; `10B40` advances queue cursor; `13586` stores the pending count |
| Complete / short | 29 available bytes reach `13592`; each tested availability 1..28 reaches `135BE`, retaining only those bytes and their count |
| Opcode dispatch | `68B4C..68B68` reads the assembled opcode and jumps via `6B5D4 + 4*31 = 6B698` to `69FA9` |
| Body consumer | `69FA9` advances past opcode; `69FB1` calls `AA200`; stop before `AA2AF` on a match |

Queue offsets above are relative to `connection+758`; the synthetic fixture's
queue bytes are therefore at `connection+1368`, write/read counters at
`connection+1F68/+1F6C`. All byte copies, cursor stores, and length/dispatch
table reads execute unchanged. Tests compare the exact writer PC, each byte's
address/value, the unfilled tail canary, and the assembled packet.

The buffered packet is passed directly to the native dispatch slice with its
actual assembled address. Buffer acquisition `68B3F -> 13650`, logging, and
the earlier socket checks are static boundaries, not emulated successful calls.
The separate dispatch slice declares EAX=assembled buffer and EBP such that
`EBP+A7F2F6C=UI`. This is not a whole receive-loop execution claim.

`AA200` searches existing WORD keys using a sign-extended packet byte 1.
Byte `80` matches key `FF80`, not `0080`; the first duplicate wins. These
properties were known from the prior scalar study and are regression checked
here without its historical fixtures. New source-to-percent evidence follows:

| Input | Exact store / downstream read |
| --- | --- |
| Packet bytes 25..26 | WORD read at `AA292`; `AND ECX,7FFF`; WORD store at `AA29C` to matched row `+28` |
| Same bytes 25..26 | Second WORD read at `AA2A0`; shift by 15 and mask; BYTE store at `AA2AC` to row `+5A` |
| Row `+28` | WORD read at `A9B92`, original call `A9B9C -> AA480` |
| Packet byte 2 | Copied to row `+02`; never read by the executed percent slices |

All other scalar stores are checked against a complete poisoned actor snapshot.
Packet bytes 13..16 and 27..28 remain unread by this scalar writer. Zero count
and missing key return to dispatch join `6B517` without actor mutation. The
two-row fixture limit is a harness bound, not an original ownership cap.

## Units, Widths and Bounds

`AA480` masks its DWORD argument to unsigned WORD, loads it as an integer,
multiplies by the pinned float32 at `171204` (hex `0AD7233C`, exact value
0.009999999776482582), and stores float32 at `AA4A8`. It then executes the
original `149630` helper, which saves/restores the x87 control word and
truncates to integer via a signed 64-bit temporary. The resulting integer is
staged for control `24` at `AA4C2 -> 1060F0`.

For this S2C31 writer, low15 is 0..32767, in nominal hundredths of a displayed
percent. This is not an absolute EXP count, nor a recovered EXP denominator.
The high bit is stored independently and has no influence on these percentage
arguments. Packet `FFFF` thus produces float32 327.66998291015625 and integer
327, not 655.35. `8000` produces zero with flag one. Changing the copied byte
at row `+02` across 0,1,127,128,255 leaves the percentage unchanged.

The separate `AA4C7..AA508` slice resolves the real ProgramMsg 165 format
through a synthetic pointer table, promotes the captured float32 to a double,
and stages the exact seven DWORD argument slots. The last two slots contain
the double, unchanged. No CRT formatter runs. `MOV AX/CX` only sets the low
16 bits of the panel argument; tests deliberately preserve/check the native
upper bits instead of claiming a clean DWORD panel ID.

The newly executed `10618A..106202` horizontal geometry slice has declared
live-ins after the unexecuted resource query `106185 -> 18C10`: EBX=0,
mode=0, control=24, and a synthetic inclusive rectangle. Its signed DWORD
percent input is clamped to zero below 0, to 1.0 at/above 100, or multiplied
by float32 `171328` (also `0AD7233C`) between 0 and 99. It multiplies the
inclusive width by that fraction and executes `149630` before staging the
drawing rectangle. It stops before drawing call `106202 -> 1EF00`.

There is no float32 intermediate store in the latter multiplication path.
At input 50 and width 100 the resulting truncated width is **49**, whereas
at input 100 it is 100. This is original display arithmetic, not XP rounding.
At input 327 the bar saturates, while the independent text argument still
represents approximately 327.67 percent. No gameplay clamp or level cap follows.

No actor bytes are modified by the executed percent/text/geometry slices.
The packet consumer's later selection and refresh calls at `AA2AF..AA2DB`,
resource lookup/validity checks before `10618A`, rendering and the vertical
bar mode remain unexecuted. No skipped callee is replaced with a success stub.

## Verification

From the server root, the exact commands are:

```powershell
python -B -m unittest tests.research.test_current_progression_source -v
python -B -m tools.strike_lab.current_progression_source --client-root C:/Users/risei/Desktop/God2/God2 --native-image artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin
```

Final test run: **9 tests passed, no skips, 12.973 seconds, exit 0**.
The CLI also exited 0, emitted 11 traced end-to-end fixture cases and the
exact bytes/SHA256 of all executed and static code spans. Its UTF-8 JSON with
LF line endings and one final newline has SHA256
`524d837f168d3a332c7a47f6e65926e789c67d53ab8c158752594b06bf0bc962`.
PowerShell captured CLI output in memory for summary/hash inspection; no
evidence output file was written.

Tests cover all partial lengths 1..28 and full 29, signed selector matching,
first duplicate/no match, complete actor snapshots, exact WORD/BYTE source
and destination provenance, all 15 independent low bits paired with both high
bit values, percent transition neighborhoods, float32/double bytes, opaque
packet bytes and other-scalar independence. Geometry tests cover integer inputs
0..327, signed extremes and -1, at widths 1,100,137 (993 cases), including
the native 49-pixel result. Negative tests reject source drift, malformed
logical records, unsupported harness inputs, instruction exhaustion and entry
into the unexecuted UI call.

Code pages are read/execute; packet, bank and UI pages are read-only. Code
allowlists and a write-range guard apply to every executed segment. Every
segment must reach an exact allowed stop within one second. The usual budget
is 2,048 instructions, with 4,096 for receive assembly (full case executes
2,089). The initial smaller receive budget correctly failed; it was increased
within an explicit finite cap. No test failure was treated as verification.
No UI automation, descendants/agents, server/client process, socket, build,
CMake, Session, shared runtime or existing helper modification was used.

## Unresolved Original Source and Next Location

The scalar's immediately upstream writer is now proved to be a copy from a
decoded incoming byte queue. The server's construction of logical WORD 25..26
is still unavailable in the examined current native slices. No original XP
requirement table or original growth arithmetic was recovered. The formatter's
unit and the bar's saturation are insufficient to reconstruct those rules.

The next concrete native evidence location is **`10ACB -> 10A10`**. Static
instructions at `10AB0..10AE4` pass the received frame, its size, output pointer
`ESI+C10`, and capacity `C00`; at return `10AD0` stores EAX as the decoded
queue length at `ESI+1810`, then clears the read cursor at `ESI+1814`.
Inside that next callee, `10A30 -> 106F0` is the conditional transform,
`10A39 -> 10750` checks the frame, and `10A62 -> 10820` handles its packed
branch; `10A7E/10A85` copy its unpacked branch. These are pinned static leads,
not executed transport proof in this deliverable.

Continuing there requires actual current frame operands/decoder state and
before/after role or companion state, or original current-server producer
code. Such samples can establish concrete transmitted values; they alone
would still not prove a universal level table. A requirement formula must be
tied to an original producer or actual authoritative data, not fitted from
these display scalars. Single-level/cumulative requirements, transitions,
level caps, HP/MP and attribute growth, point budgets, server scalar
construction, and the flag's gameplay meaning all remain **OPEN**, with null
values in machine-readable output. This bounded contract is validated;
original gameplay recovery is not complete.
