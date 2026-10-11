# Current world initialization: 2A return to 1C

Date: 2026-09-19. Pinned mapped image:
`artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`.
SHA-256: `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
Image base VA `400000`; file offsets equal RVAs. Addresses below are hexadecimal
RVAs unless labeled VA; lengths and counts are decimal.

This follows [the socket-topology note](current-login-character-socket-topology-20260919.md).
Scope starts at `65199`, after `64910` calls `68160` at `65194`, and ends at
the `1C` builder call `6552D` (plus its immediate flush boundary `65538`).
The 2A parser and server integration remain owned by the coordinating task.

## Result and minimum sequence

**No additional S2C receive waiter or packet-count prerequisite was found in
the inspected post-68160 path before 1C.** In particular, the calls with
arguments `1F` and `23` are **C2S builders**, not S2C waiters. Their replies
are not awaited before `1C`.

For the connected branch, the observed protocol prerequisite is the already
identified **one accepted S2C 2A**. After `68160` succeeds and local setup
returns, the exact final sequence on retained G is:

1. `654FF -> 13670(1)`: reset current logical receive-buffer length.
2. `65510 -> 961A0(1F,1) -> 157D0`: enqueue `1F 00`.
3. `6551B -> 961A0(23,1) -> 157D0`: enqueue `23 00`.
4. `6552D -> 157F0(world_output_id)`: enqueue `1C` plus four bytes.
5. `65538 -> 13370`: flush G.

Thus the additional inbound prerequisite count **after successful 68160 is
zero in this recovered sequence**, and there are two one-byte outbound
requests before `1C`. This is a protocol boundary result, not proof that
arbitrary 2A data or missing local resources can complete world initialization.

The original tail executes in Unicorn with an empty receive buffer, without
calling receive poll `13420` or receive pointer accessor `13650`. Its queued
bytes with local ID `1234` and configuration flag one are:

```text
1f 00 23 00 1c 34 12 01 00
```

## Actual call path

| Call site / instructions | Observed role |
| --- | --- |
| `65199..6519B` | Test `68160` result; zero branches to initialization failure `655BC` |
| `651E3/65226 -> 15B406`, `65200/65243 -> 61DB0`, `6521F/65262 -> 61E20` | Allocate, construct, bind two local objects |
| `6526F -> 5FEC0` | Reset local structure |
| `65323 -> 817C0` | Bind initializer context; context `+4` is G, later passed by `81A08..81A0E -> 96170` and stored at subobject `+86874` |
| `817C0 -> 81C20` at `81BB3` | Initialize subordinate UI/state structures; not a call to a network waiter |
| `65330 -> 1E680`, `65341 -> 2D9E0`, `6535F -> C3EA0` | Local resource/setup calls |
| `6539C -> C3F60`, `653BC -> C3C20`, `653E0 -> C3E30`, `653E9 -> 65E00` | Conditional local setup selected by populated world fields |
| `65411 -> FABB0`, `65418 -> F7380`, `65435 -> 100180` | Local initialization; `100180`'s network-object call at `10092B -> 15AB0` is literally `ret 8` in this image |
| `65462 -> 12DFC0`, `6548F -> 12EA90`, `654B2/654D5 -> CA680`, `654F2 -> 331A0` | Local object/resource binding |
| `654F7/654FF` | Load G from world `+A7E05E0`; call `13670(1)` |
| `65510/6551B` | The two concrete cases of `961A0`, decoded below |
| `65520/65526/6552D` | Load ID from world `+1539683C`, load G, call `157F0` |

Direct-call inspection was rooted at these actual initializer calls, stopping
at networking helpers; it did not enumerate the general world packet
dispatcher. No post-call path to a receive waiter was identified. This is
not an exhaustive proof about every resource failure, indirect callback,
or unrelated UI branch. Only the final `654F7..65538` tail is dynamically
executed here; the large setup routines are not emulated or stubbed into a
claim of whole-initializer success.

`961A0` uses byte selector table `9628C` and target table `96274`.
The **actual arguments** resolve as follows:

| Argument | Selected block | Behavior |
| --- | --- | --- |
| `1F,1` | `961BF`, nonzero second argument branches to `961F9` | Load G from `+86874`; `961FF` pushes opcode `1F`; `96201` calls `157D0` |
| `23,1` | `96209` | Load the same G; `9620F` pushes opcode `23`; `96211` calls `157D0` |

`157D0` stores a constant zero byte at `157DD`, supplies length one at
`157D9`, and calls enqueue `132E0` at `157E2`. It neither receives nor
flushes. Both original selector cases and the original enqueue routine
execute in the test; these are not replacement Python packet encoders.

## Lengths, consumption, and bounds

**Table `1324` is the S2C logical-size table.** It cannot supply C2S lengths
for numerically identical opcodes. This distinction matters here:

| Direction/opcode | Logical bytes | Body bytes | Evidence and prerequisite |
| --- | ---: | ---: | --- |
| S2C `2A` | 37 | 36 | `1324+4*2A = 13CC -> VA 4012A0`, returning `25` hex; one accepted packet is the preceding connected gate |
| C2S `1F` | 2 | 1 | `157D0`: opcode plus constant `00`; no inbound count required |
| C2S `23` | 2 | 1 | Same builder; no inbound count required |
| C2S `1C` | 5 | 4 | `15814` pushes four, `1582C` pushes `1C`; no additional inbound count required |
| S2C `1F` (not a gate here) | 125 | 124 | `13A0 -> VA 401306`, returning `7D` hex |
| S2C `23` (not a gate here) | 17 | 16 | `13B0 -> VA 40124C`, returning `11` hex |
| S2C `1C` (not a gate here) | 45 | 44 | `1394 -> VA 4012A6`, returning `2D` hex |

The original size-return instructions for all four S2C entries are executed
in the test. The C2S lengths are checked against actual queued bytes.

The preceding waiter `15690` accepts opcode `2A` at `156EC`, copies the
caller's 36 bytes at `15700..15716`, then consumes the current packet via
`1571A -> 13670(0)`. Other opcodes take `156F1..156FA`, consuming/discarding
the current packet and retrying, rather than retaining it for a later
handler. Empty polling is bounded by a 30000 ms timeout (`156C2`), with
100 ms sleeps (`156D2`); inactive G fails at entry. Consequently an earlier
`1F` or `23` sent in place of `2A` cannot satisfy that waiter.

The connected `68160` caller requires the low six bits of the payload field
at body offset 24 to be **1 through 16** (`681CF..681E5`); failure prevents
the successful return needed at `65199`. This merely records the prior
gate's established bound, without duplicating its parser or proposing a
new 2A fixture.

At the later `654FF` call, **argument one to `13670` is not a prerequisite
packet count**. `13678 -> 15B20` optionally logs that argument, then
`1367D` unconditionally writes zero to G `+2CC0`. It does not test an opcode,
poll for data, or drain the embedded transport. It invalidates any currently
assembled logical packet by clearing its length; its underlying bytes and
any later transport data are not cleared by this routine. The test executes
it with lengths 0, 1, 37, and 2560 and verifies this distinction.

The three C2S packets total nine logical bytes. Enqueue `132E0` checks
`existing_length + body_length + 1 <= 2560` at `132F0..132FA`, flushing first
if it would exceed that capacity. Therefore the queue order is established,
but one TCP write or one transport frame is not guaranteed. The test starts
with an empty outbound queue and stops before the final flush. G must remain
active for a later flush to represent a send; queue construction alone is
not wire evidence.

## 1C body and verification

The world output at `+1539683C` is the client-local ID derived with mask
`3FFF` upstream at `68629/68633`. Its expected range is 0..16383; this is not
a selected row or a recovered database character ID. The **builder itself
keeps the low 16 bits**, not the low 14 bits:

```text
body_u32_le = (argument & 0xffff) | (config_flag << 16)
config_flag = 1 iff WORD[VA 59DFD8] == 4 and WORD[VA 59DFDA] == 2
```

The original `131C10` helper executes, including both comparisons. Tests
cover the normal low-14-bit ID boundaries, values beyond that upstream
range to distinguish builder masking, and matching/nonmatching config
pairs. The original builder returns zero after enqueue (`15833`) and does
not itself flush.

Run:

```powershell
python tests/research/test_current_world_ready_builder.py -v
```

Result: **5 tests passed**, including the original 49 parameterized executions
and three additional complete queue/encoder executions. The pinned
SHA-256 is checked before execution. Code pages remain read/execute; only
the two required data pages are writable within the mapped image. Synthetic
stack, G, and sparse world fields are mapped separately. Logging is disabled
by setting its data pointer to zero. There are no API/transport stubs and no
assets, client process, UI, or live calls.

There is no separate "first next-wait acceptance" test because no such
waiter was recovered in this interval. The verified substitute is the
original tail reaching the flush boundary with **zero supplied incoming
packets**. No live world end-to-end, playable state, complete initializer
execution, or server integration acceptance is claimed.

## Coordinator Transport Follow-Up

The coordinating task extended the test through the actual flush/codec path:
`13370 -> 124D0 -> 10A90 -> 10960 -> 10670/10690`, stopping at `12501`
before its `send` call. Zero-seed key expansion executes at `10490`; encryption
is enabled through codec+8. The pinned `108F0` compression predicate returns
zero. With the empty starting queue, all nine logical bytes are serialized
in **one 12-byte transport frame**, not three mandatory 5/5/8-byte frames.
No socket API or desktop operation is invoked. The C++ initialization-tail
validator handles both this grouping and whole-record splits across frames,
and accepts arbitrary TCP fragmentation without interpreting read boundaries
as packet boundaries. The Python loopback tests feed the resulting original
code-generated 12-byte frame to the real C++ server.
