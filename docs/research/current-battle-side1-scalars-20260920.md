# Current battle side1 scalar continuation, 2026-09-20

## Result and limits

The former subtype-0 side1 stop at `12D8C0` is extended through original
`109240`, `108CD0` (invalid-handle return only), `109200`, `12D840`, `108FC0`
and `108F50` calls wherever their actual gates allow native returns. Tests
start once at `114332` and return to the real dispatcher continuation `114482`.
The actor and display stay in the same emulated memory throughout; no game
callee, EAX return, instruction, return address, or program counter is patched
to bypass a call. Direct helper tests are explicitly separate entry fixtures.

Two complete paths are qualified:

1. An invalid actor display handle takes native no-work helper returns, then
   copies the two packet DWORDs to the side1 actor.
2. An existing display runs both setters and their original rectangle helpers
   with explicit **diagnostic inactive graphic records and absent resource
   handles**. The rectangle bytes change; this is **not visible rendering**.

Valid display creation stops at **`108D2C -> 01F040`**, before executing the
resource helper or copying any scalar. An actual rectangle resource stops at
**`01BE45 -> 025BA0`**, after the rectangle/actor/divisor writes described below.
No successful return is supplied at either frontier.

Synthetic values establish field semantics only. They do not recover original
monster HP, MP, stats, repertoire sources, or species identity. This work is
scalar copying and display arithmetic, not damage production or stat recovery.
It does not establish packet receipt, battle initialization, actor publication,
resource creation, or a visible battle. Subtype 1 side1 still returns without a
lookup or write.

## Authority and ownership

Only these files are owned by this sidecar:

- `tools/strike_lab/current_battle_side1_scalars.py`
- `tests/research/test_current_battle_side1_scalars.py`
- `docs/research/current-battle-side1-scalars-20260920.md`

Source bytes are exclusively
`artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`,
SHA-256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
All code addresses here are RVAs, `BASE=00400000`, RVA=file offset. Existing
`current_battle_entry.NativeRun` validates the whole-image hash for each VM;
code is mapped read/execute. The existing scalar module supplies its pin.
The tests also assert instruction witnesses and unchanged whole image bytes.

No production code, CMake/status, other research files, source inventories,
archives, Data scans, GUI, runtime, network, children, or bootstrap are used or
changed. `runtime_mutation_enabled=False` is a scope declaration. The native
emulation uses the already available local Unicorn dependency.

## Same-state binding and exact gates

Let `B` be the explicit battle snapshot, `T=B+144938`, `M=T+310`, and
`R=B+A9E9CB0`. The dispatcher gets the opcode from the supplied queue record
and the subtype from `R+1`; both records initially contain the same 17 bytes.
The preceding queue copy is a precondition, not newly qualified here.

| Step | Original operation and condition |
| --- | --- |
| `11723D` | Read position byte at `R+2`; quotient/remainder by 14. Side1 means positions 14..27. |
| `11736A/11736D` | Read raw DWORDs `R+5` and `R+9`. |
| `117375/11737F` | Read pointer `[B+83458]`, then its first DWORD. This owner value is an opaque input, not a monster identifier. |
| `117388` | Call `12D8C0(owner_value,1,slot,value9,value5)` with `ECX=T`. Only the slot's low byte is meaningful; upper pushed bits survive. |
| `12D8C6` | Require side argument low byte exactly 1; otherwise native `ret 14`. |
| `12D8DA` | Original `11E6E0(1,slot,0)` returns `[T+38+24*(14+slot)]`. |
| `11E6F5/11E6FE` | Lookup checks low-byte side `<2`, slot `<14`, selector `<6`. Invalid direct slot fixtures stop at assertion call `11E718 -> 002C70`. |
| `12D8E1` | Immediately dereference actor `E+1A`; **no null check**. Null lookup produces an actual unmapped WORD read at VA `0000001A`, not a benign return. |
| `12D8E7` | Unsigned WORD `E+1A >=1000` returns without scalar/display changes. Thus negative signed WORDs fail this gate too. |
| `12D8FA` | Pass raw WORD `E+1D8` to `109240`. It uses only the low WORD; `h>=1000` returns zero. |
| `109262` | For valid `h`, `D=M+1C+h*A7E0`; return 1 iff unsigned WORD `D+A79C <1000`. This is channel 0, not a separate existence flag. |
| `12D901/12D931` | If that check returned zero, enter `108CD0`. Invalid `h` returns natively (`108E63 ret 38`); valid `h` reaches the resource frontier. |
| `12D942` | `109200(h,1)` rejects unsigned low-WORD `h>=1000`; otherwise writes BYTE `D+2F=1` and calls `109280(D,1)`. |
| `12D956` | After real preceding returns, call `12D840(1,slot,value9,value5)`. It repeats the original slot lookup in the same state. |

All 14 side1 slots are exercised with other slots holding distinct poisoned
actors. Exactly the selected actor is changed; both original lookups read the
same slot address. Tests capture real call frames and assert the owner value,
slot, copied scalars, native continuation addresses, and final stack balance.
Direct low-byte side/slot and low-WORD handle alias cases are also checked.

## Exact scalar and display footprint

For an admitted nonnull actor, `12D840` reads WORD `E+1D8` and performs:

| Instruction | Write |
| --- | --- |
| `12D86C` | DWORD `E+DE8 = value9` |
| `12D875` | DWORD `E+DF0 = value5` |

All other actor bytes, including `E+DEC`, `E+DF4`, and `E+1A`, are preserved.
There is no side1 local-owner callback. Unlike its caller, direct `12D840`
checks for a null lookup and returns without a write.

If `E+1D8` is negative as a signed WORD, no display setter runs. If it is
nonnegative, even `1000..7FFF` calls both setters, whose own unsigned handle
checks reject it without display reads or writes. For valid `h` the order is:

1. `108FC0(h,value5,E+DF4)` writes DWORDs `D+A7A8` and `D+A7AC`, then calls
   `108E70`. Its real return is required before the next step.
2. `108F50(h,E+DE8,E+DEC)` writes DWORDs `D+A7B0` and `D+A7B4`, each followed
   by an additional write of its divisor if the supplied numerator is larger
   in an **unsigned** comparison. It calls `108E70` again.

Those four DWORDs and BYTE `D+2F` are the only display writes on the completed
existing-display path. Entire actor/display/graphic snapshots and all mapped
non-stack pages are compared, and the exact ordered write events (including
overwritten pre-clamp values) are asserted.

The admitted non-stack data-read footprint is narrow and width-checked:

| Object | Read offsets and widths |
| --- | --- |
| Queue record | `+0` BYTE |
| Copied record `R` | `+1,+2` BYTE; `+5,+9` DWORD |
| Battle / owner | `B+83458` DWORD pointer; owner `+0` DWORD |
| Actor lookup table | Selected `T+38+24*position` DWORD, twice on completed paths |
| Actor `E` | `+1A,+1D8` WORD; `+DE8,+DEC,+DF4` DWORD, subject to gates above |
| Display `D` | `+A79C,+A79E,+A7A0,+A7A2,+A7A4,+A7A6` WORD; `+A7A8,+A7AC,+A7B0,+A7B4` DWORD |
| Display manager `M` | `+4` DWORD graphics pointer |
| Graphic record `Q` | `+0` BYTE state; `+0E` WORD resource handle |
| Graphics manager `G` | `+4` DWORD resource owner, only before the real resource frontier |

Stack frame reads/writes and native image-table reads are recorded separately
from these object fields. Packet bytes 3..4 and 13..16 remain opaque and unread.
Missing display/graphic snapshots fail closed on the actual access; they do
not acquire zero/default successful returns.

## Diagnostic graphic returns and remaining boundaries

`109280` first checks channel 0 as unsigned `<1000`; if rejected, it returns
without checking other handles. On its enabled branch it considers graphic
handles at `D+A79C, +A79E, +A7A2, +A7A0` in that order. Each unsigned valid
handle calls `01B740(G+10+handle*290)`. The qualified diagnostic branch requires
the explicit graphic record's state BYTE to differ from 1 and executes the
original return at `01B817`. State 1 stops at `01B751`; its active resource and
child-graphic work is not qualified.

`108E70` separately uses **signed nonnegative** channel handles at `+A79C` and
`+A79E`. It multiplies the unsigned numerator by signed WORD width, divides by
the signed DWORD divisor, and uses original `149630` to truncate to a signed
64-bit integer. The rectangle receives its low DWORD. Channel 0 initializes
the rectangle to `(0,0,extent,signed_height)`; on this continuous two-channel
path channel 1 reuses that frame and replaces the extent. Both draws and both
setter stages are tested, including negative widths and high-bit divisors.
Zero divisors stop **before** `108ECD` or `108F23`, the actual unguarded divide.

Original `01BDC0` copies four DWORDs to graphic `Q+50,+54,+58,+5C`. For an
explicit unsigned `Q+0E >=1388` (5000), it returns at `01BE4D` without touching
a resource. These diagnostic returns let both scalar/display setters finish;
they establish rectangle state only, never rendering. For `Q+0E <1388`, the
same four rectangle writes occur, then execution stops before
`01BE45 -> 025BA0(resource,rectangle)`. Actor and divisors are already updated;
the later clamp setter has **not run**. The test asserts the partial write
order, rectangle, resource argument and resource-owner ECX.

Channel 1 handles `1000..7FFF` are skipped by visibility, yet the signed render
test calls `01BDC0`; its unsigned gate reaches assertion call `01BDDE ->
002C70`, where tests stop. Values `8000..FFFF` are skipped by both operations.
Consequently two negative display channels cannot be called an existing
display: the `109240` check would select creation.

For valid actor/display handles but absent channel 0, the original wrapper
calls `108CD0` with 14 arguments:

`(h, actor_word_1A, 3, sign_extend(owner_value.low16), 0x45, -1, 0x44, -30,
5, -30, 5, -30, 11, 0x1324)` (C-style numeric notation).

At the first creation call `108D2C`, ECX is `[M+4]` and the nine arguments for
`01F040` are `(actor_word_1A,3,sign_extend(owner_value.low16),0x44,-30,5,0x1325,1,0)`.
Only stack preparation has happened: no actor,
display, or graphic object write. All these arguments are asserted from the
actual native stack; the helper is never entered or supplied a return.

## Verification

Focused invocation (no bootstrap):

```text
python -B -m unittest discover -s tests/research -p "test_current_battle_*scalar*.py" -v
```

Result: **27 tests passed in 4.375 seconds** (19 sidecar, 8 existing scalar).
The sidecar contains 19 tests covering continuous slot binding, subtype 1,
native helper returns, null/gate/handle boundaries, opaque bytes, exact
footprints, raw DWORD copies, unsigned clamps, signed display arithmetic,
resource-frontier arguments, and stack/image preservation. The adjacent
existing scalar suite remains unchanged and is run alongside it. No shared
status or production integration is claimed; this sidecar is ready for close.
