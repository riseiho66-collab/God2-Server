# Current login, character, and world socket boundary

Date: 2026-09-19. Static, bounded inspection of
`artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`.
SHA-256 verified:
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
Mapped image base VA `0x400000`; file offsets equal RVAs. All code addresses
below are hexadecimal **RVAs** unless explicitly marked VA. Capstone x86-32.
No original-client execution, UI interaction, runtime tooling, production
changes, or new packet fixtures were performed for this note.

## Conclusions

`main+15E84` and `main+15E88` are pointers to **separately allocated network
objects with independent TCP socket slots**, not aliases for one connection.
Call them L and G here, respectively; these labels describe the observed
roles, not recovered class names. L handles login and `A6/07`; G handles
`1B`, `18`, `1A` and is passed onward into the world object. A successful
connection on each object creates a separate `socket(AF_INET,SOCK_STREAM,6)`.
This does not require different server processes, hosts, or even ports.

The selected-character connection root performs a second connection/bootstrap,
expects `01/F6`, sends **C2S `00` with 172 account-structure bytes**, then
waits for S2C `1F` (or failure `1E`). There is explicit cross-connection
account-data reuse, but no recovered server-side database account ID or
authenticated handoff-token interpretation. Merely carrying `Session::account_id`
forward on L does not bind the independently accepted G connection.

The inspected recovered server's linear same-session path
`login -> A6/07 -> 1B -> 18/1A` contradicts the client's object/socket binding
for a connected character flow. An additional mismatch is missing endpoint
advertisement: the inspected server sends `04`, but not the `05/06` route
records consumed by the selected G connect path. Existing synthetic tests
on one socket do not qualify original-client topology.

After a successful state-8 return, the outer caller retains G and passes it
to world initialization. The next concrete world receive dependency found
is **S2C `2A`, 36 payload bytes**. A later identified C2S is `1C`, four
payload bytes, on G. This is a boundary trace, not a complete world protocol.

## Pre-login runtime anchor

**Break at RVA `4088` / VA `404088` before executing that instruction.**
Initializer `4010` has just bound both main-object fields. At this stop:

| Read-only expression | Meaning |
| --- | --- |
| `EBP` | Live main/login-selection object |
| `EAX` | Owner object passed to initializer |
| `[EBP+15E84] == [EAX+434]` | L network object |
| `[EBP+15E88] == [EAX+438]` | G network object |
| `[L+750]`, `[G+750]` | Independent socket HANDLE slots |
| byte `[L+2CB8]`, byte `[G+2CB8]` | High-level connected/active flags |

The instruction at `4088` is `8b 48 04` (`mov ecx,[eax+4]`), so EAX has
not yet been changed to `owner+444` by `4098`. Stores immediately preceding
the stop are `4076: mov [ebp+15E88],ecx` and
`4082: mov [ebp+15E84],ecx`.

The normal outer caller calls `4010` at `DF4D`, then calls the login/selection
routine `4DA0` at `DF87`. The other observed initializer call is `E1FC`,
before another `4DA0` call at `E224`. The first stop is therefore useful
before credentials are entered; repeated stops can belong to later re-entry.
Record the actual process/image identity, EBP/EAX, the four pointer values,
socket slots, and flags. On a fresh initialized, not-yet-connected object,
the socket sentinel is `FFFFFFFF`, and `+2CB8` is zero. Those equal sentinel
values do **not** mean the objects share a socket.

This anchor qualifies live object ownership without an auth action. It does
not itself prove two successful TCP connections, an endpoint, or packet flow.
No fresh launch or breakpoint result is claimed here; runtime work belongs
to the coordinating task.

## Allocation and actual socket roots

| RVA | Exact bytes | Evidence |
| --- | --- | --- |
| `DC69` | `68 04 42 00 00` | Allocate L object size `4204`; allocator call `DC6E` |
| `DC8B` | `e8 80 50 00 00` | L constructor `12D10` |
| `DCB0` | `89 85 34 04 00 00` | Save L to owner+434 |
| `DD43` | `68 04 42 00 00` | Separate G allocation; allocator call `DD48` |
| `DD65` | `e8 a6 4f 00 00` | G constructor `12D10` |
| `DD87` | `89 85 38 04 00 00` | Save G to owner+438 |
| `4070` | `8b 88 38 04 00 00` | Load owner+438 |
| `4076` | `89 8d 88 5e 01 00` | Store main+15E88 |
| `407C` | `8b 88 34 04 00 00` | Load owner+434 |
| `4082` | `89 8d 84 5e 01 00` | Store main+15E84 |
| `12D30` | `8d 8e 04 01 00 00` | Embedded transport at network+104 |
| `12D36` | `e8 e5 ed ff ff` | Transport constructor `11B20` |
| `11B29` | `c7 86 4c 06 00 00 ff ff ff ff` | Transport+64C = INVALID_SOCKET |
| `11D39` | `6a 06` | TCP protocol argument |
| `11D3B` | `6a 01` | SOCK_STREAM argument |
| `11D3F` | `6a 02` | AF_INET argument |
| `11D41` | `e8 58 20 13 00` | Call socket thunk `143D9E` |
| `11D49` | `89 83 4c 06 00 00` | Save returned HANDLE to this transport |
| `11E36` | `e8 3f 1f 13 00` | Call connect thunk `143D7A` |
| `11ECF` | `e8 d0 1e 13 00` | Close this transport's HANDLE |

Thus network+104+64C = **network+750**. The constructor also creates its
own transport codec at transport+654 and initializes network+2CB8 to zero
at `12D5F`. Common initializer `12E70` is called separately at `DCB6` and
`DD8D`; both receive owner+220 as their configuration/address input. The
literal `2710` at `DD6F` goes to helper `119B0` through `12E94..12EA0`;
it is **not a connect port**. The L log-name string is `GodAcnt.log`
(data RVA `184ACC`); labels set at network+40F0 are `L` and `G`.

Import identity was cross-checked against the existing
`artifacts/reports/native-wow64-20260919/modules/runtime-import-candidates.json`:
socket thunk `143D9E` jumps through VA `570834`, connect thunk `143D7A`
through VA `57084C`, closesocket thunk `143DA4` through VA `570830`.
Their pinned image pointers (`769CFBE0`, `769D77C0`, `769D0170`) match that
report's `ws2_32` exports. These process-specific API addresses are historical
evidence, not addresses to reuse in a new launch.

L's login root is `B010 -> 13E10` (`B0CE/B0D4` set ECX=L and call).
`13E40` selects L+104; `13E90` calls `11EE0`, which closes any previous
handle through `11EC0`, then calls `11D30` at `11EF4` with address string
at **VA `5B479C`** and literal port **`0A20` = 2592**. The address string
comes from initializer input through `11BB0 -> 11B60`; `11B7E..11B8D`
copies it into that global. No hostname/IP value is inferred here.
`11D30` resolves/formats the host, applies htons to the supplied port at
`11E10`, calls connect at `11E36`, and invokes post-connect setup `12690`
at `11E5F`. The static arguments, not an assumed loopback configuration,
establish this endpoint root.

G's selected-character root is `BD50 -> B580 -> 13060 -> 12440 -> 11D30`.
At `BD63..BD86`, L active and G inactive selects the call at `BDB3`; if
both are active it skips reconnecting. The retry/relogin branch can also
call `B580` at `BE61`. `B7C6/B7CD` explicitly use G for `13060`.
`13165` calls `12440` on G+104; `12443` closes that transport's old handle,
and `12454` calls `11D30` with the resolved address/port. Success sets G's
queue length to zero and its active flag to one at `13192/1319C`.
Flush `13370 -> 124D0` uses the same embedded transport and its HANDLE
(`133A8/133AE`, `124F9/12501`), closing the proof from builders to socket.

## Routing values: packets versus UI

The address lookup is shared table **VA `5B48A0`**, not a socket field.
`11A90` ignores ECX and returns `table[index]`. Accordingly, the apparent
L-to-G table copy in `B580` (`B5AF`, `B5CA`, `B5E3/B5E8`, 1804 bytes)
gets the same global entry for the same index. It is not a socket transfer.

`11BB0 -> 12740` initializes table groups/names from `Data3/config*.ini`
variants (literal strings at `185570`, `185584`, `18559C`, `1855B0`).
**Endpoint entries are subsequently cleared and populated by login packets.**
`13FEF` fetches each group; `13FFF..14020` clears 480 endpoint bytes per
subgroup before the `13E10` reply loop. The configuration alone is not
evidence of the eventual G connect destination.

Let P point at a decoded reply opcode; offsets in this paragraph are decimal.
The reply dispatcher at `14082/1408A` uses byte table `144D4` and target
table `144B8`. Its relevant entries are `04 -> 14234`, `05 -> 1426F`,
`06 -> 142D0`, `1D -> 14091`, and `0A -> 14386`.

| Input | Writer / consumer | Proven role |
| --- | --- | --- |
| S2C `04`, P+1 | `1425A/1425D` | Current group index for subsequent route records; `14252` resets endpoint counter to -1 |
| S2C `05`, P+1 | `14290/14292` | Subgroup index k; endpoint counter j increments at `14277`; route counter resets at `14283` |
| S2C `05`, P+1..8 | `142AE..142BB` | Copy 8 bytes to `T+260*k+30*j+C4` |
| S2C `06`, P+1..4 | `142D8`, `14302/14305` | Increment route counter r and copy to `T+260*k+30*j+CC+4*r` |
| UI WORD main+8F4 | e.g. writes `6E95`, `6F02`; read `B59B`, `B7BD` | Group/table index g; A6 uses only its low byte |
| UI WORD main+B40 | e.g. writes `7658`, `7688`; read `B7AF` | Subgroup index k; A6 uses only its low byte |
| raw `07` selected record byte 19 & 7 | `130A9/130B1`, `1232C..12333` | Select record by low-three-bit selector |
| matching raw `07` record byte 32 | `1235E` | Nonzero route-ID match against table entry+CC+4*r |

In the table formulas, T=`table[g]`; all constants/indices in the expressions
are hexadecimal except P offsets and explicitly named record-byte offsets.
For the chosen endpoint entry E=`T+260*k+30*j`, IPv4 octets are bytes
E+C6..C9, and port is the little-endian WORD E+CA. These therefore originate
from **S2C `05` P+3..6 and P+7..8**, respectively. `123BA..123E6` formats
the four octets using `%d.%d.%d.%d`; `123FF/1240F` returns the port.
If lookup `12310` returns zero, `130EC..13101` calls fallback `12250`, which
searches for a nonzero route entry and extracts the same endpoint fields.
No endpoint is recovered when neither search succeeds.

This distinguishes UI table selection, server-advertised routes, and the
`07` selector. In particular, `07` is not itself an IP/port redirect. S2C
size table `1324` confirms logical lengths 5 for `04/06`, 9 for `05`.
No concrete destination IP or G port is established by this static note.

## Account bridge and selected states

`B490` reads the two UI WORDs, uses L at `B4C4`, and calls `147D0` at
`B4CC`. It sends A6 with their low bytes, receives `07`, and retains the
74-byte raw list at main+178CE0. State `12` calls `B490` at `5458`; its
success branch `545F -> 5B61` requests state 4. On success, `B54F/B555`
load L/G, `B55D` reads L+4200, and `B568` writes G+4200. This is the low
bit of `07` payload byte 1 stored by `14953/14956`, not account identity.

Selected state `14` dispatches to `5626`, calls `BD50(2)` at `562A`, then
`BA00` at `5652`. This gives a concrete state-to-G-connect root without
walking all networking. The existing-character `18/1A` result semantics
are intentionally left to the separate assigned analysis.

After `13060` succeeds, `B7F5` calls `131C0` on G with expected byte F6
(`B7EF`). That waiter requires opcode `01` (`13215`), compares its next
byte to F6 (`13270..13279`), consumes it, then `B840` calls `B910`.
`B910` calls `149C0(0, account_structure)` at `B97B`; the zero argument
becomes opcode **00**, and `14A49/14A52` enqueue **AC = 172** payload bytes.
`14A59` flushes. `B993 -> 14A70` waits for `1F` or `1E`:
`14ABD/14AC2` distinguish them, `14B1E..14B28` copy 124 payload bytes for
`1F`, and `14B4F` clears G's active flag for `1E`.

The account structure is main+58C's pointee, supplied by the outer owner
(normal call passes owner+AC at `DF3D/DF44`, bound at `45A7`). Proven sources:

- `B010` copies the login input's 24-byte account and 132-byte password
  buffers into this structure (`B024/B047`), and separately saves them to
  owner+8 and owner+20 (`B066/B07F`), with forced terminating NULs.
- L sends the 172-byte structure as opcode `04` at `13F93..13FAB`.
  Login reply `1D` checks both strings at `141AC/141C4`, then replaces all
  172 bytes of the structure from the reply at `141D4..141DB`.
- Before G's `00`, `B910` restores the first 156 bytes from saved owner
  buffers (`B92D/B94B`) and sets structure byte A6 to C8 (`B95F`).
  `B5DD` sets byte A8 to the low byte of UI group index main+8F4.
  Other surviving tail fields can consequently originate in L's `1D` reply;
  they must not all be relabeled UI data, zeros, or a guessed session token.
- Builders at `C160`, `BE80`, and `BA00` explicitly use G; they do not move
  L's socket. `18`'s byte is `low8(WORD(main+15E34)+1)` on the D200 success
  branch. `1A` reads main+178CF6, main+178D0E, and raw selected byte 19 & 7.

**Bounded reachability limit:** current create submission `D200 -> C160`
does not call `BD50` or connect itself. Its direct state-9/1B/1C/A/1D/1E
setup/submit sequence has not been shown here to establish G on a cold
launch. Do not import the sibling `BF30 -> BD50 -> C0B0` (opcode 17)
preparation into opcode 1B. The allocation/socket distinction and G builder
binding are proven; a fresh successful cold-login-to-current-create path
still needs runtime qualification. Flush `13370` returns without sending
when +2CB8 is zero, so a builder call alone is not wire evidence.

## State 8 to the world boundary

State table entry `5C18` is VA `405B76`. Valid selection at `5B76` eventually
copies 40 bytes from `rawList+2+36*selected` at `5BD2..5BDB`, returns 1 at
`5BCD`, and returns to the outer `4DA0` caller. This preserves the earlier
note's distinction between a 36-byte wire stride and a 40-byte output copy.

The normal call is `DF87`, result check `DF8C/DF8F`. The outer code destroys
the selection object at `E034`, but retains owner+438. At `E0D6` it calls
world initializer **64910**. `649A6/649AC` bind the same owner+438 pointer
to **world+A7E05E0**; no third socket is created by this ownership handoff.
The companion L pointer is bound to world+A7E05E4 at `649B2/649B8`.
After successful world initialization, the outer call `E0ED -> 144F0` uses
L with flag zero; `145A1..145AC -> 11F10 -> 11EC0` closes L and clears its
active flag. It does not close G. Failure also takes L cleanup at `E13C`.

The next specific network dependency recovered within world initialization:

| RVA | Exact bytes | Meaning |
| --- | --- | --- |
| `65194` | `e8 c7 2f 00 00` | World initializer calls `68160` |
| `68193` | `8b 8b e0 05 7e 0a` | Use retained G |
| `681A0` | `6a 24` | Receive copy length 36 |
| `681A3` | `e8 e8 d4 fa ff` | Call waiter `15690` |
| `156EC` | `80 38 2a` | Wait for S2C 2A |
| `15700` | `8d 70 01` | Copy begins after opcode |
| `1570F` | `f3 a5` | Copy payload dwords |
| `1571A` | `e8 51 df ff ff` | Consume received packet |
| `12A0` | `b8 25 00 00 00` | 2A size-table target: logical length 37 |
| `65520` | `8b 85 3c 68 39 15` | Read populated world output DWORD |
| `6552D` | `e8 be 02 fb ff` | Pass it to `157F0` |
| `15814` | `6a 04` | C2S payload length 4 |
| `1582C` | `6a 1c` | C2S opcode 1C |
| `1582E` | `e8 ad da ff ff` | Enqueue through G |
| `65538` | `e8 33 de fa ff` | Flush G |

The 2A size-table entry is RVA `13CC` -> VA `4012A0`, confirming 36 payload
bytes, 37 logical bytes, or 40 bytes in a single uncompressed frame.
`15690` discards other queued opcodes and waits up to 30000 ms; it returns
failure when disconnected. Its caller uses the returned bytes, including
the low six bits of payload WORD at offset 24, checked as 1..16 at
`681CF..681E5`. This is not a license to fill 2A with synthetic zeros.

The later 1C payload is a little-endian DWORD:
`(world_output_DWORD & FFFF) | (return_value_of_131C10 << 16)`.
The world output DWORD is written by the packet-consuming routine at
`68633` after mask `3FFF` at `68629`; it is not the selected UI row or an
established database character ID. Helper `131C10` returns 1 only when
the WORDs at VA `59DFD8` and `59DFDA` equal 4 and 2, otherwise 0.
This establishes packet-derived output versus a local configuration flag
without assigning unsupported domain names. 1C has logical length 5,
single uncompressed full-frame length 8.

Scope limit: this is the identified world receive gate and later send,
not proof that every intervening resource/helper call is network-free or
that 1C is the first possible outbound packet in every world branch.
No world field schema, map choice, actor defaults, playable state, or
additional world packet implementation is proposed.

## Server implications and verification

Source was read only. At inspection, `src/net/Session.cpp` has per-socket
`C2S0002State`, processes A6 in `TerminalSent`, sets `PostSelectReceived`,
then expects a 48-byte 1B request on that same socket. Its next stage expects
18/1A on the same instance. `authenticate_recovered` binds `self->account_id`
from opcode 04; `character_operation` requires that per-instance account.
`src/protocol/RecoveredC2S0002.h::parse` explicitly rejects any opcode
other than 04, so it does not authenticate the G opcode-00 bridge.
`send_recovered_login` sends `1D`, `RecoveredServerList::one_entry()` (04),
and terminal `0A`; no 05/06 endpoint records occur in that inspected path.
The client clears route entries before accepting these login replies.

A single listener can still support multiple independently authenticated
connections. What is not supported by the current linear contract is
equating connection identity with account identity across L and G, or
expecting character packets to follow A6 on L. A compatible change needs
verified route advertisement and G bootstrap/account binding before
character operations; the exact server validation policy for the opaque
account tail remains unrecovered. No production changes were made here.

Verification: pinned SHA-256 checked on every disassembly invocation;
direct-call destinations, selected switch tables, socket API pointers,
and the exact-byte witness tables were checked against the pinned image.
No live authentication or topology acceptance test was run. The separate
existing-character result work and main runtime integration remain outside
this file's ownership.
