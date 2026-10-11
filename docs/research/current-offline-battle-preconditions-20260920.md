# Current Offline Battle Text Preconditions, 2026-09-20

## Result

The reported `115C90 -> 1216C0 -> 11602A -> 12CCD0` frontier is consistent
with an initialized battle renderer but an **unbound embedded text owner**.
The precise missing native binding path is:

`111516 -> 11F920 -> 1081C0`, with text owner `T = M+310` and
battle manager `M = B+144938`, where `B = DWORD[world+A7E05EC]`.

All code addresses below are RVAs unless prefixed VA. Base is `400000`;
RVA equals file offset in the pinned mapped image:
`artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`,
SHA256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
The battle constructor is **RVA 1109D0 / VA 5109D0**, not RVA 109D0.

## Exact Null Receiver

`12CE24` selects `ECX=M+310`; `12CE2A` calls `108300`.
At `10839B`, the original function loads `ECX=[T+4]`, then calls `1F6F0`
at `1083A0`. `1F711` dereferences `[ECX+0C]`, the renderer's ROM bank.
Thus the null is **T+4**, not M+0C or the existing ROM-bank pointer.

Read-only checks of the supplied run's `battle-manager-before.bin` show:

| Field | Captured value | Meaning |
| --- | --- | --- |
| M+04 | 005E053C | Catalog binding, equal to captured B+28 |
| M+08 | 0FAEA020 | ROM bank |
| M+0C | 3764B020 | Battle renderer |
| M+14 | 09FDCB68 | Name registry |
| T+00, +04, +08, +0C | All zero | Text owner not bound |
| T+10 | FFFFFFFF | Text GUI resource not bound |

These addresses describe that process only. The supplied result reports zero
original numeric values recovered. A successful resource/participant stage
does not recover dual attack/defense or establish four base attributes.

## Original Initialization ABI

The normal caller in battle-session initializer `1112C0` executes:

```text
111505  mov eax,[B+A9DF744]       ; FightComm3 record 0 runtime handle
11150B  mov ecx,[B+04]           ; app+428 owner
11150E  mov edx,[B+0C]           ; app+42C display bridge
111511  push eax
111512  push ecx
111513  push edx
111514  mov ecx,M
111516  call 11F920
11151B  continuation
```

`1112E1/1112ED` bind those B fields from the real application;
`11149B..1114B7` load the record table and store its first runtime handle
at B+A9DF744. Consequently a bounded experimental invocation may use the
same real sources directly, without requiring a fabricated battle event:

```asm
; A = [world+A7E05C4]; B = [world+A7E05EC]; M = B+144938
; D = [A+42C]; P = [A+428]; F = [B+83458]; h0 = DWORD[F]
push h0
push P
push D
mov ecx, M
call 0051F920h
; Stop at our own return checkpoint. Callee removes all 12 argument bytes.
```

This is an **experimental bridge to an original initializer**, not execution
of the complete normal `1112C0` caller or proof of successful battle entry.
`11F920` returns with `RET 0C`; EAX is not a Boolean success contract.

Inside the wrapper, `11F940` calls `1081C0` with ECX=T and five arguments,
in declaration order:

`(D, DWORD[M+0C], P, h0, DWORD[M+04])`.

`1081C0` first executes original reset `1080A0`, then writes:
T+00=D, T+04=renderer, T+08=P, T+0C=catalog, T+10=h0.
It returns with `RET 14`. The wrapper also writes M+A7E0330=52 and
M+A7E0334=61. Do not replace these calls with pointer stores.

## Preconditions And Checkpoints

Before calling, verify real, readable bindings, not merely nonzero numbers:

- B+28 == M+04 == world+AA36480 == A+444 (the latter is an embedded address).
  Captured M+04 has this value, but its producer is not established by this
  slice: manager constructor `11F5E4` originally zeros M+04. Preserve and
  verify the existing binding; do not silently manufacture it on a new run.
- M+0C is the actual battle renderer; DWORD[renderer+0C] == M+08.
- D == DWORD[A+42C] == DWORD[world+A7E05DC];
  P == DWORD[A+428] == DWORD[world+A7E05C8]. Do not use the world renderer
  or the pixel-format/context argument from the battle constructor as P.
- F == DWORD[B+83458] is the loaded FightComm3 table, not an invented table.
  h0 is its first **runtime handle**, not an assumed zero or CSV index.
  Check h0 is nonnegative, within registry count DWORD[[M+14]+404], and
  names the loaded GUI ROM in bank M+08. Preserve the existing valid assets.
- Catalog signed WORD[C+B2C6C] must be at least 02EE, with readable table
  DWORD[C+B2C68] and valid NUL-terminated strings for IDs
  02E2, 02E6, 02E7, 02EE (table offsets B84, B94, B98, BB4).
  `1081EC..1082EB` copies these strings without a null-safe fallback.
- Use a fresh disposable process before its first diagnostic `115C90` call.
  `108300` marks a text slot occupied before the observed fault;
  do not retry a faulted invocation or reset an active text owner in place.

At the initializer return checkpoint check the five T bindings above. On the
subsequent original path, `10839B` must load the same renderer as M+0C;
at `1F711`, ECX must be that renderer, and DWORD[ECX+0C] the real bank.
This closes the observed null prerequisite only, not every later resource,
battle-session, or display requirement. No initialization was executed here.

The full normal initializer remains `ECX=B; push descriptor; call 5112C0h`,
`RET 4`, reached at caller `65836`, returning to `6583B`. It additionally
binds session owners, copies the event into B+48, creates battle UI, and sets
B+A9DF740/+744 and B+A9EA4C8, all later consumed by `115C90`.
Those event-dependent values are not supplied by this text-only recipe.

## Byte Guards And Constructor Scope

| RVA | Expected bytes | Boundary |
| --- | --- | --- |
| 6514E | E8 7D B8 0A 00 | World calls battle constructor 1109D0 |
| 110DED | E8 7E EB 00 00 | Constructor calls manager init 11F970 |
| 111516 | E8 05 E4 00 00 | Original caller of text wrapper |
| 11F940 | E8 7B 88 FE FF | Wrapper calls 1081C0 |
| 11F95A | C2 0C 00 | Wrapper stack cleanup |
| 1081C0 | 53 56 57 8B D9 E8 D6 FE FF FF | Text initializer and reset |
| 1082F0 | C2 14 00 | Text initializer stack cleanup |
| 10839B | 8B 4F 04 52 53 E8 4B 73 F1 FF | Loads T+4 and calls 1F6F0 |
| 1F711 | 8B 41 0C | Observed null dereference |
| 12CE24 | 8D 8D 10 03 00 00 E8 D1 B4 FD FF | Selects T and calls 108300 |

`64910` already constructs B with arguments
`([D+A8], [A+430], [D+AC], C)`; constructor `1109D0` returns B with RET 10.
Its `110DED -> 11F970` initializes M with
`([D+A8], [A+430], 02000000, 02000000, [D+AC])`, RET 14.
That creates both ROM/renderer pairs and calls `11FC40` to bind all
2*14*6 participant pointers. It also loads the FightComm3 records and calls
`120650` for each ROM. **Do not rerun this allocation/manager init** to fix
the text null; `11F970` explicitly asserts if M+08 already exists.

Verification: static hash/byte guards checked against the pinned image;
captured pre-call fields read from the supplied artifact. No new live run,
UI, network, fake native return, runner edit, or monster-stat substitution.
