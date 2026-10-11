# Current create success: bounded next-action trace

Source: `artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`
SHA-256 verified: `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
Mapped image, base VA `0x400000`. Addresses below are **RVAs**;
file offsets equal RVAs. Capstone 5.0.7, x86-32, static inspection only.
No live client execution, UI, server/session/DB changes, or gameplay expansion.

## Answer

The current create path does **not** request a list refresh on success:

```text
state 0x1E -> D200 -> C160 -> C2S 1B (builder 14CC0)
  -> 15020 waits for S2C 02, result WORD == 0
  -> C2S 18 (builder BE80, one payload byte)
  -> BA00 -> C2S 1A (builder 14C50, 37 payload bytes)
  -> 14D20 waits for another S2C 02, result WORD == 0
  -> AFB0(8) -> state 8 -> return the existing selected list record
```

`A6 -> 07` belongs to the separate state `0x12` list-request path.
Serve the list in response to `A6`; an unsolicited `07` is not a required
create-success reply. Both result waiters consume/discard unrelated `07`
packets. There is no observed transition from this successful `D200` path
to state `0x12`, and no list rewrite in `C160`/`D200`/`BA00`.
This is a static client contract, not proof that an original server never
sent unsolicited packets elsewhere.

## Lengths and next builders

Lengths are decimal. Logical length includes opcode, excludes the outer
two-byte length and final checksum. Full lengths below assume one logical
message in an uncompressed frame; batching/compression can change wire size.

| C2S | Builder RVA | Payload | Logical | Full frame | Data source / timing |
| --- | --- | ---: | ---: | ---: | --- |
| `1B` | `14CC0` | 44 | 45 | 48 | Existing current create request |
| **`18`** | **`BE80`** | **1** | **2** | **5** | Immediate next request; `low8(WORD(main+15E34)+1)` |
| `1A` | `14C50` | 37 | 38 | 41 | Immediately after `18`, before another receive wait |
| `A6` | `147D0` | 2 | 3 | 6 | Separate state `12`; low bytes of `main+8F4`, `main+B40` |

For `18`, `D26E/D277` compute the increment in DX only: this does not
increment the stored WORD at `main+15E34`. `BE80` uses its low byte.
`18` and `1A` each call flush `13370`; there is no receive wait between them.
Both use network object `main+15E88`; `A6` here uses `main+15E84`.

`BA00` passes two buffers at `main+178CF6` and `main+178D0E` to `14C50`.
Its third argument is `rawList[2+36*selected+19]&7`, with raw list pointer
at `main+178CE0` and selected WORD at `main+178CE4`. Builder `14C50`
copies two 16-byte buffers, terminates their last bytes, places the selector
at payload 32 (values >=4 become 0), and constant 4 at payload 33.
Payload 34..36 have no writer in this builder. No domain meaning is assigned
to these fields here, and no synthetic defaults are established for that tail.

| RVA | Exact bytes | Evidence |
| --- | --- | --- |
| `C1C2` | `e8 f9 8a 00 00` | Call create builder `14CC0` |
| `14CD1` | `6a 2c` | Create payload length 44 |
| `14CD4` | `6a 1b` | Create opcode `1B` |
| `C1E7` | `e8 34 8e 00 00` | Call result waiter `15020` |
| `C1EC` | `66 89 06` | Store returned result WORD through caller pointer |
| `C1F2` | `66 85 c0` | Test result WORD |
| `C1F5` | `75 08` | Nonzero -> `C1FF`; zero returns EAX=0 at `C1F7` |
| `C1FF` | `25 ff ff 00 00` | Nonzero result returned zero-extended |
| `D217` | `e8 44 ef ff ff` | Call `C160` |
| `D21F` | `66 89 07` | Store result WORD in caller's output |
| `D222` | `74 4a` | Zero -> success at `D26E` |
| `D26E` | `66 8b 96 34 5e 01 00` | Read WORD at main+15E34 |
| `D277` | `66 42` | Increment DX |
| `D27A` | `e8 01 ec ff ff` | Call `BE80` |
| `BE80` | `8a 44 24 04` | Take argument's low byte |
| `BE87` | `6a 01` | Payload length 1 |
| `BE98` | `6a 18` | Opcode `18` |
| `BE9A` | `e8 41 74 00 00` | Enqueue through `132E0` |
| `BEA5` | `e8 c6 74 00 00` | Flush through `13370` |
| `D286` | `e8 75 e7 ff ff` | Call `BA00` |
| `BA2F` | `e8 1c 92 00 00` | Call builder `14C50` |
| `14C8F` | `6a 25` | Payload length 37 |
| `14C98` | `6a 1a` | Opcode `1A` |
| `14CA6` | `e8 35 e6 ff ff` | Enqueue through `132E0` |
| `14CAD` | `e8 be e6 ff ff` | Flush through `13370` |
| `BA44` | `e8 d7 92 00 00` | Wait through `14D20` |
| `BA49` | `f7 d8` | Start zero-result-to-true conversion (`neg eax`) |
| `BA4B` | `1b c0` | `sbb eax,eax` |
| `BA4E` | `40` | `inc eax`: waiter zero -> BA00 returns 1 |
| `D28D` | `74 d0` | BA00 false -> state-1 path `D25F` |
| `D28F` | `6a 08` | BA00 true -> request state 8 |
| `D293` | `e8 18 dd ff ff` | State setter `AFB0` |
| `13320` | `88 8c 13 c8 36 00 00` | Queue opcode byte |
| `1333F` | `45` | Add opcode to payload length |
| `109BF` | `8d 46 03` | Outer frame length = encoded logical bytes +3 |
| `109C4` | `66 89 03` | Store frame length WORD |
| `109DD` | `88 44 1e 02` | Append checksum after two-byte header and content |

## Exact state effects

The switch reads `main+178CEC` at `52AF`, then dispatches through the
VA table `405BF8` at `52BE` (`ff 24 85 f8 5b 40 00`).
These are data-table entries, not instructions:

| State | Table RVA | Exact bytes (VA target) | Handler RVA |
| --- | --- | --- | --- |
| `1` | `5BFC` | `0b 53 40 00` | `530B` |
| `4` | `5C08` | `7a 54 40 00` | `547A` |
| `8` | `5C18` | `76 5b 40 00` | `5B76` |
| `12` | `5C40` | `56 54 40 00` | `5456` |
| `1E` | `5C70` | `f6 58 40 00` | `58F6` |

State `1E` calls `D200` at `5924` (`e8 d7 78 00 00`), then returns to
the main loop. `AFB0` saves old state to `main+178CF0` at `AFF6`
(`89 86 f0 8c 17 00`) and writes the requested state to `main+178CEC`
at `AFFC` (`89 be ec 8c 17 00`). If old state is `0x0B`, both stores
are skipped (`AFF1: 83 f8 0b`, `AFF4: 74 0c`). Thus the ordinary
success path records previous state `1E` and current state `8`.

State 8 compares the signed selected WORD to the zero-extended list count
at `5B80` (`66 39 85 e4 8c 17 00`); `5B87: 7d 60` returns 0 if
selected >= count. There is no explicit negative-index guard here.
Otherwise it calls `4A30`, `4AD0`, `4990` with the existing main WORDs
at `+8F4`, `+B40`, `+178CE4`, respectively; computes the selected source
as `rawList+2+36*selected` at `5BCA/5BD2`; copies **40 bytes**, not 36,
to the outer caller's output; and returns 1. Exact copy witnesses:
`5BD2: 8d 74 8a 02`, `5BD6: b9 0a 00 00 00`, `5BDB: f3 a5`.
The 40-byte copy must not be interpreted as a 40-byte wire-list stride.
This trace stops at that return; it does not follow the outer caller.

## A6 requests 07; success does not refresh it

State `12` calls `B490` at `5458` (`e8 33 60 00 00`). `B490` passes
the existing raw list destination and null optional projection pointer,
then calls `147D0` at `B4CC` (`e8 ff 92 00 00`). This function sends
the request before entering the receive loop:

| RVA | Exact bytes | Evidence |
| --- | --- | --- |
| `147E3` | `6a 02` | A6 payload length 2 |
| `147EA` | `68 a6 00 00 00` | Opcode A6 |
| `147F9` | `e8 e2 ea ff ff` | Enqueue A6 |
| `14800` | `e8 6b eb ff ff` | Flush |
| `1483A` | `80 f9 07` | Expected reply opcode 07 |
| `1483D` | `74 7a` | 07 -> copy at `148B9` |
| `148BD` | `8d 70 01` | Copy starts after opcode |
| `148C0` | `b9 12 00 00 00` | 18 dwords |
| `148C7` | `f3 a5` | Copy 72 bytes |
| `148C9` | `66 a5` | Copy 2 more bytes: total 74 payload bytes |
| `14953` | `80 e1 01` | List header byte 1 low bit |
| `14956` | `88 8b 00 42 00 00` | Store bit to request network object's +4200 |
| `14966` | `33 c0` | Return success |

That reply is logical length 75 / uncompressed full frame 78.
`B490` returns true on receive success; `545F` branches to `5B61`,
which requests state 4 (`5B61: 6a 04`, `5B65: e8 46 54 00 00`).
Failure requests state 1 at `5465/5469`.

The create waiter only accepts `02`: `1507C: 83 e8 02`,
`1507F: 74 57`; every other opcode is consumed at `15085`
(`e8 e6 e5 ff ff`) and the loop resumes at `1508A: eb b3`.
The subsequent `1A` waiter recognizes `02` and `1E`, then discards
other opcodes at `14D8E` (`e8 dd e8 ff ff`), looping at `14D93: eb aa`.
Consequently an early `07` can be removed without updating the list.

## S2C 02 result and error semantics

For the established total-26 uncompressed `02` frame, the logical
opcode-plus-body length is 23 (`1234: b8 17 00 00 00 c3`). Let `P`
point to the opcode, i.e. full-frame offset 2. Result is unsigned
little-endian WORD `P+1` = **frame offsets 3..4**. It is not a byte.

| RVA | Exact bytes | Meaning |
| --- | --- | --- |
| `150D8` | `66 8b 7a 01` | Read full result WORD |
| `150DC` | `66 85 ff` | Test result |
| `150DF` | `0f 86 81 00 00 00` | Zero -> `15166` success consume |
| `1516A` | `e8 01 e5 ff ff` | Consume 02 |
| `15171` | `33 c0` | Return success 0 |
| `150EB` | `8a 42 15` | Nonzero: read P+21 = full-frame offset 23 |
| `150FE` | `24 7f` | Message variant = that byte & 0x7F |
| `1510E` | `3c 03` | Variant must be <3 for table lookup |
| `1511B` | `8d 0c 88` | Index arithmetic: 4*result + variant |
| `15124` | `8b 7c 88 f4` | Message pointer: table +16*result +4*variant -12 |
| `1514D` | `66 8b 72 01` | Reload exact server result WORD |
| `15153` | `e8 18 e5 ff ff` | Consume packet |
| `1515C` | `25 ff ff 00 00` | Return result zero-extended |

The lookup additionally requires result <= signed WORD at resource object
`+B2C64` (`150F1/15100/15107`) and result >0 (`15109/1510C`). Resource
object is `network+40D0`; pointer table is resource `+B2C60`. A valid
entry's NUL-terminated string is copied to the caller error buffer at
`1512C..1514B`. This is a numeric client-resource message lookup, not
server-supplied error text. The high bit of frame byte 23 is masked off
for this lookup; no independent meaning for that bit is established here.

On invalid range/variant the code sets EDI=0 at `1512A` (`33 ff`), then
performs `repne scasb` at `15131` (`f2 ae`). There is no safe fallback
string in this branch. Do not invent nonzero wire codes or assume every
16-bit nonzero value can be displayed safely. No duplicate-name, capacity,
validation, or other named server error mapping is established here.

`D200` handles all nonzero create results uniformly: if error text is
nonempty (`D224..D230`), it passes it to the message helper at `D257`;
then `D25F: 6a 01`, `D263: e8 48 dd ff ff` request state 1.
It does not send `18`/`1A` on this branch. State-1 setter `AFB0` also
calls `15730` with arguments `(2,0,1)` when `network+2CB8` is nonzero
(`AFCD..AFD2`), and `144F0` on the other network object (`AFE6`).
These cleanup calls are not followed beyond the bounded state setter.

The result waiter's timer uses 30000 (`1504C: 68 30 75 00 00`);
expiration produces **local return 0xC9** (`150B8: b8 c9 00 00 00`)
and a resource string. That is not evidence that the server should send
0xC9 for a particular create error. Also, `1502E` skips directly to the
zero-return tail when `network+2CB8` is zero: return 0 alone is not proof
that a success frame was received on a disconnected object.

The subsequent `14D20` waiter likewise treats `02/result=0` as success
(`14E0B/14E0F/14E12` -> `14E99` -> `14EA4`). Nonzero uses the same
message lookup and returns the WORD. Opcode `1E` is a separate failure
path (`14D85: 83 e8 1c`, `14D88: 74 57`); it clears network `+2CB8`
at `14DF9` and returns 1 at `14E01`. `BA00` converts waiter 0 to true,
all nonzero to false; `D200` then selects state 8 or state 1 respectively.

## Verification boundary

Pinned SHA-256 checked before inspection. All witness rows above are exact
image bytes; direct-call targets and switch entries were decoded from that
image. Automated comparison passed for 82 instruction witnesses and five
switch entries. Existing pinned `test_current_character_create_result.py` exercises
the result WORD branch with 0, 1, and 256 in synthetic memory, stopping
before resource lookup/queue mutation; both tests passed with `python -B`.
No claim of live network execution
or a tested end-to-end server flow is made by this note.
