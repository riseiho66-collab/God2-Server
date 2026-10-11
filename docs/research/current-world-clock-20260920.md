# Current Original World Clock, 2026-09-20

This sidecar qualifies the bounded clock prerequisite used by the actual
`C3080` UI routine. It does not qualify world/battle startup or rendering and
makes no monster numeric claim. No resource preload, database/C++ changes,
network, live client, retired archive, or replacement game return is used.

## Pin and Logical Packet

All game addresses below are RVAs, with base `400000` and RVA = file offset.
The sole game image is
`artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`,
3,174,400 bytes, SHA256
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
Every helper instance checks that hash. Every execution checks the original
instruction ranges against the bytes in the supplied VM; clock runs also check
the pinned IAT slot and float constant. No executable bytes are patched.

| Evidence | Original behavior |
| --- | --- |
| `68B50`, `68B52`, `68B61` | Read logical opcode from `[EBX]`, bound it by `FD`, dispatch through VA `46B5D4 + opcode*4`. |
| `6B63C = 6B5D4 + 1A*4` | DWORD `0046B022`: logical **S2C1A** case. |
| `1200..120F` | Length selector bounds its opcode by `FD`, dispatches through VA `401324 + opcode*4`. |
| `138C = 1324 + 1A*4` | DWORD `00401264`; `1264` is `B8 04 00 00 00 C3`, returning **4 bytes**. |
| `6B022..6B02F` | Increment EBX past opcode, set ECX to `EBP+A7F2F6C` (owner), push payload, call `C35F0` at `6B02A`. |
| `C363B` | Writer executes `ret 4`, returning to `6B02F` with the dispatch arm's original stack balance. |

The explicit logical input is exactly `[1A, b1, b2, b3]`. The three payload
fields are unsigned BYTEs, read individually at `C360B`, `C3615`, `C3623`.
There are no WORD or DWORD packet fields and no original hour/minute/second
range checks in this writer. Values `00..FF` are accepted for each payload
byte. Transport framing and other packet systems are outside this sidecar.
The helper validates the opcode/length and executes the original dispatch arm;
it does not claim to execute the outer packet dispatcher or length routine.

## Writer and Source Coordinates

`source = DWORD[owner+86888]` must already equal `character+90`. The helper
checks this binding and never manufactures it or initializes missing fields.

| Instruction RVA | Read/write | Width | Meaning |
| --- | --- | --- | --- |
| `C35F3` | Read VA `5707BC`, native indirect CALL | DWORD | Imported clock target; original CALL pushes its return address. |
| `C35F9`, `C362C` | Read `owner+86888` | DWORD | Same character-source pointer, read twice. |
| `C35FF` | Write `source+44AC = character+453C` | DWORD | Explicit external clock sample. |
| `C3605` | Read writer argument from stack | DWORD | Pointer to packet byte 1. |
| `C360B/C3615/C3623` | Read packet `+1/+2/+3` | BYTE each | Unsigned base-60 inputs. |
| `C3634` | Write `source+44B0 = character+4540` | DWORD | `6 * (3600*b1 + 60*b2 + b3)`. |

These two DWORDs are the entire non-stack write footprint. The eight bytes
start at **character+453C**, not character+44AC. `C35F0` completes without
refresh/UI calls. In particular there is no reason to fake a UI return to
finish this writer.

## Imported Clock Identity

The import is **WINMM!timeGetTime**, not GetTickCount. Evidence is specific to
this capture, not a name guessed from clock-like behavior:

- Image IAT RVA `1707BC` contains VA `74147860`.
- Preserved parallel name-thunk RVA `17F7BC` contains `17F8D6`; hint/name bytes
  at `17F8D8` spell `timeGetTime\0`. The surrounding names are `mmioOpenA`,
  `mmioRead`, `mmioDescend`, `mmioSeek`, then `timeBeginPeriod`. `WINMM.dll\0`
  is at `17FA48`.
- `native-master-01-native.log` in the same current capture output records
  `C:\WINDOWS\SysWOW64\winmm.dll` loaded at `74140000..74173000` (line 116;
  detailed module record starts at line 1299). Log SHA256:
  `ed9c73c2d372b500d3534caa40756254a8eb4a57a920ee017958a7a606611241`.
- Read-only export inspection of `C:\Windows\SysWOW64\winmm.dll` confirms
  `timeGetTime` RVA `7860`; `74140000+7860 = 74147860`. Its size is 195,912
  bytes, SHA256 `eefb711e78a3e2031ff2015d04471da7258945f40bce2dd54433f664c2d667bf`.
  Timestamp `C1DE18F1`, image size `33000`, checksum `38B21`, and version
  `10.0.26100.9278` agree with the captured module record. Adjacent export RVAs
  `168B0/168F0/16810/16950/8C10` also match the five surrounding IAT entries.
- The separate preserved `GetTickCount` name is at `17FC8E`, thunk `17F400`,
  corresponding IAT `170400 = 765EDBF0`. It is not the target of these calls.

The active PE import directory is the packed image's directory at `302FAC`;
it does not directly describe the restored `1707BC` slot. The module/export
cross-check is therefore part of the identity evidence, not just the parallel
name table. The helper/tests need only the pinned game image and Unicorn;
they neither load the Windows DLL nor query a live clock.

The adapter consumes one explicit unsigned DWORD `clock_ms` per run. It stops
emulation at the imported entry before any entry hooks or instructions run,
reads the native CALL's return address, supplies EAX, pops that one DWORD and
resumes the unchanged game caller. This is a zero-argument OS adapter, never a
game-function return replacement. A temporary RX page at the captured import
target is mapped only if absent and removed afterwards; an existing mapping
and existing host hooks remain intact. In particular an existing fixed-zero
host clock adapter is not invoked by this helper.

## Consumer Arithmetic and UI Boundary

`C3080` calls `C3640` at **C3119**, after its preceding UI creation work.
`read_clock` executes exactly `C3117 -> C3119 -> C3640`, with ESI = owner,
and follows the real call at `C36A1` into complete `C3710`. It also executes
the original x87-to-integer helper `149630..149656` called at `C3687`.
Earlier C3080 UI creation is not run by this sidecar.
The bounded execution explicitly stages an empty x87 stack and control word
`037F` (extended precision, nearest rounding); this is a harness environment,
not a claim about unexecuted client startup. The original conversion helper
still performs its own rounding-mode change. Caller x87 state is restored.

| RVA | Native arithmetic or access |
| --- | --- |
| `C3646` | DWORD read of `owner+86888`. A missing binding is rejected by the helper before executing the native null-source skip. |
| `C3657` | Native indirect call through VA `5707BC`, with explicit external `now`. |
| `C365D..C3679` | Compute `delta6 = (6*now - 6*timestamp) mod 2^32`; timestamp is a DWORD read at `C366C` from `source+44AC`. |
| `C3660`, `C3679`, `C367D` | Set the upper DWORD to zero, store delta6 as the low DWORD, load the resulting nonnegative 64-bit integer with `FILD`. |
| `C3681` | Read float32 bytes `6F 12 83 3A` at VA `571240`: exact value `8589935 / 8589934592`, approximately `0.0010000000474974513`. |
| `149630..149656` | Preserve x87 control word, set round-toward-zero, `FISTP` to 64 bits, return EDX:EAX, restore control word. This routine is executed, not stubbed. |
| `C3695`, `C369B` | DWORD read of `source+44B0`, then 32-bit addition: `total = (value + trunc(delta6 * float32_constant)) mod 2^32`. |
| `C3710..C374C` | Unsigned arithmetic: `minute = (total // 60) % 60`, `hour = (total // 3600) % 24`; write only one BYTE per output pointer, `ret 0C`. |
| `C372F`, `C374A` | BYTE stores to minute pointer (third argument), then hour pointer (second argument). Upper bytes of the output slots are untouched. |
| `C36A6`, `C36AA` | Read the stack output slots as DWORDs; returned sidecar results use their low bytes, matching subsequent native AND FF instructions. |

The arithmetic's multiplication/subtraction wraps **before** float conversion.
It is not unrestricted elapsed milliseconds multiplied by six, signed elapsed
arithmetic, or exact decimal division by 1000. For example, the explicit test
`timestamp=0, now=10000333, value=58` exposes float32 rounding at a displayed
minute boundary. Backward ticks use the original unsigned wrap behavior.

The exact stop is **C36AE**, before `mov cx, word [esi+232DA6]`, the first
UI-handle read after the arithmetic. The deferred UI formatting call is
**C36D1 -> 1077C0**, using owner+E2170, that WORD handle, control 2, and
`%02d:%02d` at VA `593094`. Neither the handle read nor the formatting call
executes. No result labels this prefix as a completed C3640/UI refresh.

## Reusable API and Trace

```python
from tools.strike_lab.current_world_clock import NativeWorldClock

clock = NativeWorldClock(native.vm, owner=owner, character=character_root,
                         sp=dedicated_sp, packet=dedicated_packet)
written = clock.write_clock(explicit_logical_1a, clock_ms=explicit_receive_ms)
observed = clock.read_clock(clock_ms=explicit_observation_ms)
# Or assert a separately qualified existing eight-byte source snapshot:
observed = clock.read_clock(clock_ms=explicit_observation_ms,
                            state=explicit_timestamp_value_bytes)
split = clock.split_clock(explicit_unsigned_dword)
```

All stages use the supplied, stopped VM. Do not call recursively inside an
active emulation hook. Existing memory mappings must provide the source pointer
slot and clock fields; there is no source object construction. Reserve dedicated
RW scratch `[sp-100,sp+100)` and four packet bytes, disjoint from the image,
character object, source-pointer slot and other live caller data. Input addresses
and spans are checked against 32-bit bounds, overlap and required permissions.
No full resource or character-object mapping is needed by the standalone tests.

Every native data read and write, including IAT, constants, call/return stack,
x87 spills and byte output slots, is guarded and recorded in `reads`/`writes`
as `(instruction_rva, absolute_address, width, value)`. `pcs` records every
executed game instruction. `clock_calls` records the OS identity, exact target,
supplied sample, return address and adapter's explicit stack read. Host staging
inputs are recorded as `packet` and `external_clock_ms`; host setup/restoration
is not misreported as original instruction activity. `last_trace` is retained
for failures as well. Each stage has a 512-instruction bound and at most two
one-second emulation intervals, with at most one OS sample consumed.

CPU context, including caller x87/SIMD state, and all scratch stack/packet bytes
are restored on success and failure. Native writes remain in the same VM.
`writer_returned` includes the actual eight-byte `state` receipt;
`before_ui_handle_read` includes the original arithmetic's `hours`/`minutes`.
No pending UI stack continuation survives restoration: main resumes its own
caller separately. On an interrupted writer, partial native stores can remain,
but the old receipt is invalidated and no new receipt is issued.

`read_clock` requires a successful writer receipt on this instance, or explicit
eight-byte state equal to existing VM memory. Merely having mapped/zero-filled
storage is insufficient. Explicit zero is valid input; absent packet, absent
external sample, absent state, changed state, wrong source pointer, invalid
widths, and values outside their unsigned bounds fail closed.

## Verification

Run from `God2-Server`:

```powershell
python -B -m unittest discover -s tests/research -p test_current_world_clock.py -v
```

The standalone test imports Unicorn from
`artifacts/tooling/crypto-oracle-python` (2.1.4). It maps the pinned image and
small poisoned fixture pages only. Thirteen tests cover exact dispatch/length
and import bytes, original writer footprints, unsigned payload extremes,
C3080's real call through C3640/C3710 and the original CRT conversion, tick
wrap, scaled-delta wrap, total wrap, float precision, splitter/day boundaries,
missing input and permission rejection, changed image/IAT/constant rejection,
same-VM composition, an existing host clock hook, and CPU/stack/packet
restoration after an interrupted writer. No resource-preload test is run.
