# Current existing-character selection contract

Source: `artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`.
Verified SHA-256: `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
Mapped x86-32 image, base VA `0x400000`; all code/table addresses below are
**RVAs**, equal to file offsets. States/opcodes/offsets are hexadecimal;
lengths and record strides are decimal. Static decoding plus synthetic Unicorn
execution only. No live client, UI, network, gameplay, production edits, or
post-create C160 analysis. Legacy serializers are not evidence for this contract.

## Result

**Selecting an existing ordinary saved record uses state `14`, not state `7`.
It does not send `18` and does not require S2C `18`.** On an already prepared
connection, the sequence is simply C2S `1A` -> S2C `02/result WORD=0` -> state 8.
When the second network object needs connection setup, the bounded sequence is:

```text
Previously obtained list: C2S A6 -> S2C 07; state 12 -> 4 -> 13
ordinary saved-record selection -> state 14 (RVA 5626)
  BD50(2), when object A is connected and object B is disconnected:
    B580 -> 13060 establishes B
    131C0 waits for S2C 01, payload byte == F6
    B910 -> 149C0 sends C2S 00 (172 payload bytes)
         -> 14A70 waits for S2C 1F (124 payload bytes)
  BA00 -> 14C50 sends C2S 1A (37 payload bytes)
       -> 14D20 waits for S2C 02, result WORD == 0
  565B/565F -> AFB0(8)
```

`F6` above is a **value inside opcode 01**, not an opcode to send. A frame
whose opcode is F6 is discarded by this greeting waiter. The greeting is
server-first on the newly established connection; the bounded setup does not
enqueue a request before waiting for it. Endpoint/network-object integration
belongs to the separate investigation. Here A/B mean only pointers at
`main+15E84` / `main+15E88`; no server-role names are inferred.

If both A and B have nonzero byte `+2CB8`, BD50 returns success without the
setup exchange; the synthetic test executes that real branch. If A is
disconnected, BD50 runs the existing reconnect helpers BA60/BB40/BB80 and
requires state 13 before its B setup attempt. Their earlier authentication
contract is outside this bound. Thus the table below does not claim every
selection always repeats all previous exchanges.

## Frames and parser offsets

Full lengths are for **one logical message in an uncompressed frame**, before
transport encryption. Let `F` be its first length byte, `P=F+2` the opcode,
and payload offset zero be `P+1=F+3`. Frame layout is
`u16le(total) | opcode | payload | checksum`; logical length excludes the
two length bytes and checksum. Batching/compression may change the outer size.

| Direction / opcode | Payload | Logical | Total wire | Source or consumer |
| --- | ---: | ---: | ---: | --- |
| C2S `A6` | 2 | 3 | 6 | Earlier list request at 147D0; low bytes of main+8F4/+B40 |
| S2C `07` | 74 | 75 | 78 | 148B9 copies P+1..P+74 into the raw list |
| S2C `01` | 1 | 2 | 5 | 13215 checks opcode; 13270 reads P+1=F+3; must equal F6 |
| C2S `00` | 172 | 173 | 176 | B97A supplies opcode 0 to 149C0; 14A49 supplies length AC |
| S2C `1F` | 124 | 125 | 128 | 14B1E/14B28 copies P+1..P+124 = F+3..F+126 |
| C2S `1A` | 37 | 38 | 41 | BA00 -> 14C50, described below |
| S2C `02` | 22 | 23 | 26 | 14E0B reads little-endian WORD P+1 = F+3..F+4 |
| C2S `18`, separate branch | 1 | 2 | 5 | BE80, argument low byte |
| S2C `18`, separate branch | **2** | **3** | **6** | 152C2 reads only P+1=F+3; P+2=F+4 is ignored here |

The raw list starts with a count byte and flags byte, followed by two
36-byte records. For selected signed WORD `s=main+178CE4`, the selection
token is `rawList[2 + 36*s + 19] & 7` (19 decimal = 13 hex). The list
parser's flags bit store is separate from the count. Selection does not
request A6 again or replace the list in BA00.

The 172-byte C2S 00 payload is the existing structure at `main+58C`. B910
copies 24 bytes from `(main+15E68)+8` to structure offset 0, copies 132
bytes from that source object+20 to structure offset 18, and sets structure
byte A6 to C8. B580 previously sets structure byte A8 to low8(main+8F4).
These are data-source facts, not authority to fabricate the remaining bytes.
S2C 1F's 124 bytes are copied into B910's temporary stack output; B910 then
tests the waiter's return, with no further interpretation of that copy before
return. This proves its completion contract, not domain semantics for 124 bytes.

C2S 1A payload offsets 0..15 and 16..31 are bounded copies from
`main+178CF6` and `main+178D0E`; offsets 15 and 31 are forcibly zero.
Payload offset 32 (F+35) is the selected record token, with values 4..7
normalized to zero; offset 33 (F+36) is constant 4. Payload 34..36
(F+37..F+39) have **no writer in this builder**. Do not assign random values
or claim a canonical exact full packet for those bytes. The code does not
copy the record's name into this 1A payload.

For S2C 02, success is the full WORD zero. Results 1 and 256 both take
the failure branch. Nonzero results use `(P[21]&7F)` = frame byte 23 as a
resource-message variant, then return the result WORD. BA00 maps zero to
true and nonzero to false. False returns state 1 via 56A6/56A8; true requests
state 8 via 565B/565F. Opcode 1E is also a failure path in 14D20. Other
opcodes, including 18 and 07, are consumed/discarded and waiting continues.
Local timeout is return D7. A disconnected object's early return is zero;
that shortcut is not evidence of a received successful reply.

Exact plaintext frame shapes (brackets denote supplied data, not literal bytes):

```text
S2C greeting:   05 00 01 f6 ec
C2S setup:     b0 00 00 [172 existing structure bytes] [checksum]
S2C setup OK:  80 00 1f [124 bytes] [checksum]
C2S selection: 29 00 1a [37 bytes as above] [checksum]
S2C result:    1a 00 02 [result lo] [result hi] [20 bytes] [checksum]
C2S separate:  05 00 18 [q] [0d+q modulo 256]
S2C separate:  06 00 18 [t] [u] [4a+t+u modulo 256]
```

Checksum is the sum of `(byte+3C)` for every preceding frame byte, modulo
256 (`1067F..10688`). Only the greeting's entire contents are fixed by this
bounded path. Unread fields in other frames have not been assigned defaults.

## State 7 is record removal

The switch entry at 5C14 maps state 7 to 5935; state 14 at 5C48 maps to
5626. State 7 either returns to state 4 (59B9), or enters state 19
(59D6). Its confirmed branch eventually requests state 1A at 9252/9256.
That state dispatches to 5A05, calls BD50(2), and then **C210**, not BA00.

C210 calls 152E0, which sends **C2S opcode 19**, payload 53 / logical 54 /
total 57. That request contains the two input buffers, the selected token,
and the selected record name; payload offset 33 is constant 4. Its waiter
accepts S2C 02, result WORD at P+1. On success C210 shifts later raw records
left in **36-byte units**, decrements the count byte, and resets selected WORD
to zero. This is concrete record-removal behavior, not an existing-record
entry handshake. The state-7 chain does not call BEB0/15210 or BA00.
State values 19/1A and packet opcodes 19/1A must not be conflated.

After successful removal, 5A61..5A67 calls 15730(2,4,1), which sends C2S
02 with one-byte payload 04 (total 5), then waits in 15180 for S2C 03
(logical 3 / total 6). It then runs the existing reconnect/BD50 path and
returns to state 4. This is cleanup of the removal operation, not a prerequisite
to selecting an unchanged saved record. No removal request is executed here.

## Where 18 is required

The only direct E8 call to BEB0 in the pinned image is C04B, inside BF30.
The main switch reaches BF30 from state **18** at 5840. This separate
branch calls C0B0 -> 14CF0 (C2S opcode **17**, 44-byte payload), waits for
its result, and calls BEB0 on success. It is not the state-14 selection path.

BEB0 sends `18` with `q=low8(WORD(main+15E34)+1)`, then calls 15210.
On a connected object, **that particular waiter requires S2C opcode 18**;
02/07/1F do not satisfy it. There is a 30000 timer bound, and timeout returns
1. The S2C length table requires logical length 3, even though the waiter
reads only one payload byte. A total-5 S2C 18 is therefore not the established
frame shape; the correct uncompressed total is **6**.

The first payload byte `t` is data, not a success/error code: 15210 stores
it to its output and returns zero irrespective of t. BEB0 replaces the low
three bits of byte 19 of the **last counted record** with `t&7`, preserving
the upper five bits, then sets selected WORD to the full zero-extended t.
The second payload byte u has no reader in this slice. No valid-domain meaning
or server default for t/u is inferred. BEB0's caller subsequently disconnects,
reconnects through BD50, and requests state 4; it does not call BA00 directly.
Disconnected 15210 also returns zero without reading a reply, so the mandatory
reply statement is specifically for its connected receive path.

## Exact instruction witnesses

All rows below are literal image bytes. Table-pointer rows contain VAs.

| RVA | Exact bytes | Interpretation |
| --- | --- | --- |
| `5C14` | `35 59 40 00` | State 7 -> 5935 |
| `5C48` | `26 56 40 00` | State 14 -> 5626 |
| `5C58` | `12 58 40 00` | State 18 -> 5812 |
| `5C5C` | `ea 59 40 00` | State 19 -> 59EA |
| `5C60` | `05 5a 40 00` | State 1A -> 5A05 |
| `5611` | `6a 14` | Ordinary record confirmation requests state 14 |
| `88C4` | `6a 14` | Second ordinary-record entry to state 14 |
| `5626` | `6a 02` | BD50 attempt count 2 |
| `562A` | `e8 21 67 00 00` | Call BD50 |
| `BD82` | `74 3b` | A disconnected -> BDBF reconnect path |
| `BD86` | `0f 85 e0 00 00 00` | Both connected -> skip B580 |
| `BDB3` | `e8 c8 f7 ff ff` | Connect/setup B580 |
| `B7CD` | `e8 8e 78 00 00` | Establish connection through 13060 |
| `B7EF` | `68 f6 00 00 00` | Expected greeting payload F6 |
| `B7F5` | `e8 c6 79 00 00` | Call greeting waiter 131C0 |
| `13215` | `80 38 01` | Required opcode 01 |
| `13270` | `8a 40 01` | Read P+1 |
| `13277` | `3a c1` | Compare greeting byte to F6 argument |
| `13279` | `74 53` | Match -> consume success |
| `B840` | `e8 cb 00 00 00` | Setup B910 |
| `B97A` | `50` | Push zero opcode (EAX zeroed at B959) |
| `B97B` | `e8 40 90 00 00` | C2S 00 builder 149C0 |
| `14A49` | `68 ac 00 00 00` | Payload 172 |
| `14A52` | `e8 89 e8 ff ff` | Enqueue |
| `B993` | `e8 d8 90 00 00` | Waiter 14A70 |
| `14ABD` | `83 e9 1e` | Check 1E failure opcode |
| `14AC2` | `49` | Then check 1F |
| `14AC3` | `74 55` | 1F -> copy success |
| `14B1E` | `8d 70 01` | Start copy P+1 |
| `14B21` | `b9 1f 00 00 00` | 31 dwords = 124 bytes |
| `14B28` | `f3 a5` | Copy |
| `5652` | `e8 a9 63 00 00` | Selection BA00 |
| `BA13` | `8a 54 81 15` | Record byte 19, after two-byte list header |
| `BA1D` | `83 e2 07` | Token low three bits |
| `BA2F` | `e8 1c 92 00 00` | Builder 14C50 |
| `14C8F` | `6a 25` | Payload 37 |
| `14C98` | `6a 1a` | Opcode 1A |
| `BA44` | `e8 d7 92 00 00` | Waiter 14D20 |
| `14D7C` | `83 e8 02` | Required result opcode 02 |
| `14E0B` | `66 8b 7a 01` | Result WORD P+1 |
| `14E12` | `0f 86 81 00 00 00` | Zero -> success consume |
| `14D8E` | `e8 dd e8 ff ff` | Discard unrelated opcode, including 18 |
| `565B` | `6a 08` | Selection success state 8 |
| `565F` | `e8 4c 59 00 00` | AFB0 state setter |
| `59D6` | `c7 85 ec 8c 17 00 19 00 00 00` | State 7 -> state 19 |
| `9252` | `6a 1a` | Confirmed removal requests state 1A |
| `5A48` | `e8 c3 67 00 00` | C210, not BA00 |
| `C248` | `e8 93 90 00 00` | Removal exchange 152E0 |
| `15315` | `6a 35` | Removal payload 53 |
| `15376` | `6a 19` | Removal opcode 19 |
| `C283` | `b9 09 00 00 00` | Shift nine dwords = 36-byte record |
| `C289` | `f3 a5` | Shift record |
| `C2B0` | `fe c8` | Decrement list count |
| `C2B5` | `66 c7 06 00 00` | Reset selected WORD |
| `5840` | `e8 eb 66 00 00` | State 18 -> BF30 |
| `C04B` | `e8 60 fe ff ff` | Separate BEB0 caller |
| `BEBE` | `e8 bd ff ff ff` | Send 18 via BE80 |
| `BEDB` | `e8 30 93 00 00` | Wait for 18 via 15210 |
| `15264` | `80 38 18` | Required reply opcode 18 |
| `15267` | `74 55` | 18 -> payload extraction |
| `1526D` | `e8 fe e3 ff ff` | Discard other opcode |
| `152C2` | `8a 40 01` | Read only first payload byte |
| `152C7` | `88 01` | Store output byte |
| `BF03` | `80 e2 07` | Replace only low three record bits |
| `BF10` | `66 89 86 e4 8c 17 00` | Selected WORD receives full t |
| `1384` | `dc 12 40 00` | S2C 18 length-table entry |
| `12DC` | `b8 03 00 00 00 c3` | Logical length 3 -> full length 6 |
| `13A0` | `06 13 40 00` | S2C 1F length-table entry |
| `1306` | `b8 7d 00 00 00 c3` | Logical length 125 -> full length 128 |

## Verification and limit

`python -B tests/research/test_current_existing_character_selection.py -v`
passes seven tests against the SHA-pinned original bytes. A separate byte
comparison verified all 69 instruction/table witnesses above; the fixed
greeting checksum was also checked.

- Execute state-14 BD50/BA00/builder/result waiter with both objects connected;
  observe exactly one C2S 1A and state-8 request, with and without an extra S2C 18.
- Pin state dispatch and S2C logical-length entries.
- Execute the result WORD branch for 0, 1, and 256.
- Execute greeting branches for opcode 01/F6, wrong value, and wrong opcode F6.
- Execute 1F success dispatch/copy and verify exactly 124 bytes with guards.
- Execute separate 18 dispatch/extraction and verify the second byte is ignored;
  opcode 02 takes the discard branch.
- Execute C210 success with selected record 0 or 1 and verify removal/count/index.

Queue, flush and timer services in the combined selection test are stubs;
the other tests stop before queue/resource calls. Inputs are deterministic
synthetic bytes, not captured sessions or server defaults. This proves the
bounded original-client branches and required frame shapes, not live transport,
authentication, endpoint routing, or gameplay readiness. The trace stops at
state 8; its existing-record return is already documented in the adjacent
next-action note and is not re-traced here.
