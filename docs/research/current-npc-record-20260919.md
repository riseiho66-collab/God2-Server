# Current native opcode 0x72 record contract

This lane recovers the logical record envelope, raw selector representation,
client selector bounds, and packed coordinate widths. The owning C++20 codec is
ready for explicit integration but is not runtime-enabled. No default NPC,
template, coordinate, world placement, or authoritative server rule is supplied.
Emulator results below are bounded native evidence, not live playable proof.

## Evidence source

Only `artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`
is loaded as evidence. Its size is 3,174,400 bytes and SHA256 is
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
Image base is `0x400000`; file offset equals RVA. All addresses below are RVAs.
The oracle verifies the whole image hash before execution and maps code read-only
and executable. It imports only the local Unicorn package, never earlier NPC
recovery fixtures or asset inventories. Earlier spawn-helper values were not used
to derive or constrain this contract.

## Exact logical envelope

| Logical offset | Width | Contract |
| --- | --- | --- |
| 0 | 1 byte | Opcode `0x72` (hexadecimal) |
| 1 | 4 bytes LE | Raw selector, retained without catalog filtering |
| 5 | 12 bytes | Opaque bytes, retained exactly |
| 17 | 4 bytes LE | Packed position, retained exactly |

For raw selector `S`, the primary half is `S & 0xffff` and the secondary half is
`S >> 16`. Neither is sign-extended. These are native catalog selectors, not a
recovered server entity-ID allocation policy.

For packed position `P`, `x = (P >> 2) & 0x7fff`, `y = P >> 17`, and the low two
bits are retained without interpretation. Both coordinates have the complete
unsigned representable range `0..32767`. This is an encoding bound, not proof
that every coordinate is legal on any particular map. The low bits are ignored
by the tested coordinate slices; they are not declared globally unused or zero.

`RecoveredNpcRecord::parse(span)` accepts exactly 21 bytes with opcode `0x72`.
It owns a copy of every byte, including unrecognized data. `encode()` returns an
independent 21-byte copy. There is no default constructor or template builder.
`setPosition(uint64_t,uint64_t)` rejects either value above 32767 without changing
the record; successful edits preserve bits 0..1 and every non-position byte.
`setRawSelector(uint64_t)` rejects values above `0xffffffff` without changing the
record. Successful selector edits affect only bytes 1..4. Parsing does not impose
catalog membership, resource readiness, map bounds, or spawn policy.

### Native length and assembly

1. `134C3` reads the queued opcode. `134C8 -> 15840 -> 1000 -> 1200`
   reaches the native length switch. The jump-table entry at `14EC`
   (`1324 + 4*72h`) is VA `40127C`.
2. `127C: B8 15 00 00 00 C3` returns 21. `134E2/134E6` counts the
   already-read opcode as byte one, so this is 21 logical bytes including opcode,
   not 21 payload bytes after it.
3. `13558` compares the buffered count with this length and `1355E` takes the
   complete branch when count is at least 21. The read loop at `13566..13590`
   calls `12520` once per byte and stops immediately on reaching 21.
4. `12520` uses the real empty check `10B50` and real copy/cursor update
   `10AF0`. The receive queue object is receiver `+758h`; its decoded data starts
   at receiver `+1368h`, end at `+1F68h`, cursor at `+1F6Ch`. Logical count and
   output start at receiver `+2CC0h` and `+2CC4h`.

Tests execute this assembly from `13497` with synthetic decoded queues of every
size 0..22. Sizes 0..20 stop at `135AF` after the real byte reader returns 1
(unavailable); counts and copied prefixes match exactly. Sizes 21 and 22 stop
at `13592` with exactly 21 bytes copied and consumed. With 22 available bytes,
byte 22 remains queued. The maximum observed path is 1,521 instructions.

The separate count-guard test probes buffered counts 0..22 after executing the
real callback. It observes that an already-set count of 22 also takes the native
complete branch. The new C++ API rejects a 22-byte span because it accepts one
exact record; it does not claim that native stream assembly rejects trailing
stream bytes. The downstream field-decoding slices have no independent length
check and must not be exposed directly to an unbounded input buffer.

### Native selector bounds

The primary dispatcher at `68B4C..68B68` reads byte zero and indexes table
`6B5D4`; entry `6B79C` is VA `46A68B`. At `6A691`, the handler reads the low
WORD at logical offset 1; `6A695` increments EBX so it points past the opcode.
`6A6C6` then reads the entire DWORD from that same selector offset.

The catalog pointer is `[world + AA36480h]`. Its WORD at `+121E8h` is read with
`movsx`, giving a signed maximum `M`. Each accepted row pointer is
`catalog + 121EAh + 94 * index`. The primary pointer is set to null when
`primary > M`; otherwise the computed pointer is stored at `[esp+14h]`.
There is no explicit nonzero-primary check.

The selected pointer at `[esp+24h]` uses the secondary half if it is nonzero and
`secondary <= M`. Otherwise the handler retries the primary half. If that primary
also exceeds `M`, execution leaves at `6B517`. Success stops at `6A72F`, before
dereferencing any row. The `JG` checks compare the zero-extended halves with the
sign-extended maximum. Consequently:

- `M = 0` accepts primary index zero in this bounded selection path.
- A negative `M` rejects both unsigned halves.
- A high half of zero falls back to the primary half.
- An out-of-range high half falls back to the primary half.
- An in-range nonzero high half can reach `6A72F` even with a null primary pointer.
  That observation does not establish safety or success of subsequent consumers.

Tests use seven signed maxima and eight boundary values for each selector half,
448 combinations total. Catalog rows are not materialized or stubbed: execution
stops before the selected row is read. The C++ codec preserves all combinations,
including those that this synthetic catalog state would reject.

### Native packed coordinates

`6AA81` passes EBX (logical record +1) to `CC380` at `6AA89`.
`CC3B0` reloads that record argument into EDI. In the new-entry scalar slice:

```text
CC676 mov eax,[edi+10h]     ; logical bytes 17..20
CC679 shr eax,2
CC67C and eax,7FFFh
CC681 mov [esi+10h],eax
CC684 mov eax,[edi+10h]
CC687 shr eax,11h
CC68D mov [esi+14h],eax
```

Execution stops at `CC690`, before the scene owner dereference. The same slice
also copies the low selector half to actor `+0` and extracts logical byte 9's high
three bits into actor `+8`. The latter remains opaque in the public codec; it is
not justification for choosing a direction, state, or resource.

The existing-entry slice `CC41A..CC447` uses the identical extraction and writes
both actor `+180h/+184h` and `+188h/+18Ch`. Static continuations at
`CC499..CC4B0` and `CC7D2..CC809` repeat those same coordinate operations.

The catalog-flag branch also reaches a different consumer: `6A9BC` passes the
same post-opcode EBX and `6A9C0` calls `CBD70`; `CBD74` reloads its record into
EBX. Its existing-entry slice `CBDEF..CBE1C` and new-entry slice
`CC04F..CC069` execute the identical 15+15-bit extraction. All four slices are
differentially checked against C++ on the same 644 position records.

No actor allocation, catalog-resource lookup, map conversion, renderer, or
branch-result function is replaced. These scalar slices start with explicit
synthetic register bindings and poison-filled actor memory. They do not pretend
to have reached that state through a successful whole-world initialization.

## Exact executable evidence

Ranges are half-open. The oracle prints hashes for all executed and static ranges
and validates direct call targets and both opcode jump-table entries. Selected
range hashes for independent comparison:

| RVA range | SHA256 |
| --- | --- |
| `127C..1282` | `e4f9f7041b372cb8bd7dda73eb33390a3fb3a11ea2164b2b6a465b11b2ea2188` |
| `13497..13592` | `33afb1e77f0dcc5056b416bf55d598eadd2dc7965ad362590848d42dab0f03e3` |
| `12520..12554` | `2863bec9edc037a510b90f8a0fdbbf53e9feaea66278534b4be749d2142cb08d` |
| `10AF0..10B4A` | `80a01dc72f5c72593d87311563bf6661115ec9bcd310eaeee6b2258ab57a2c0e` |
| `6A68B..6A72F` | `71758fbffc021c93651534b1a4b62e8ecfe4cc4ab38a6256919d76886b9d6840` |
| `CC621..CC690` | `e2aac96315e1a4408dc39ad9154f785885a983b5dcf2250bee1d7bc9ecb96982` |
| `CC41A..CC447` | `2b43c4598aa96eed157a59d13ebd99578d876f872e40dc241a4aa0972a002ce9` |

Every slice enforces instruction-address and memory-access ranges, an instruction
budget (160 normally, 2,500 for real logical assembly), and a one-second emulation
timeout. Unexpected calls, writes, stops, and faults fail the tests. Record input
is placed against an unmapped page; native scalar reads for every truncated size
0..20 fault at the observed opcode/selector/direction/position read rather than
silently receiving zero padding. Exact 21-byte inputs succeed; the last position
read is offset 17, width 4. Actor and receive buffers have checked canaries.

## Reproduction and validation

From `C:/Users/risei/Desktop/God2/God2-Server`:

```powershell
python -B tools/strike_lab/current_npc_record.py
python -B tests/research/test_current_npc_record.py -v
```

The first command prints the qualified image identity, native length result, and
range hashes. The second builds `tests/test_recovered_npc_record.cpp` directly
with a C++20 compiler in a private temporary directory and deletes the products
on completion. On this host it discovers MSVC using `vswhere`, imports
`vcvars64.bat`, and uses `/std:c++20 /EHsc /W4 /WX`. No CMake or shared build tree
is involved. Missing image, hash mismatch, missing compiler, unexpected native
access, or compilation failure is a test failure, never a skip.

The nine tests cover:

- Original receive assembly for all 23 available lengths 0..22, plus the native
  length callback and all 23 count-guard boundaries.
- Every truncation 0..20 at a guard page; exact final read extent at 21.
- 448 signed-count/unsigned-selector boundary combinations.
- 644 packed-position inputs on four original consumer slices: 324 Cartesian
  boundary/low-bit combinations, all 32 one-hot and 32 one-cold bit patterns,
  and 256 deterministic random DWORDs (seed `0x720919`).
- All 256 values at each of the 20 non-opcode offsets: 5,120 exact C++ round trips.
- 96 opaque-byte perturbations against the original scalar path.
- 144 C++ selector/position edits checked against native decoding and exact
  preservation; deterministic edit seed `0x7215`.
- C++ owning-copy behavior, lengths 0..64, every opcode byte, coordinates beyond
  15 bits, selector values beyond 32 bits, and no mutation on setter failure.

Final validation on 2026-09-19: the evidence command exited 0 with native length
21 and the pinned hash; the complete test command exited 0, `Ran 9 tests in
34.117s`, `OK`. The C++ fixture compiled under MSVC with warnings treated as
errors and its standalone checks passed. All started execution sessions finished.

## Remaining original boundary: open

The record contract is finite and testable. Original gameplay rules remain open;
opaque preservation is not a declaration that those rules have been recovered.

| Still open | Native evidence pursued and concrete continuation |
| --- | --- |
| Meaning and valid combinations of opaque bytes 5..16 and position bits 0..1 | Inspected the current handler and both actor consumers. Resource selection reads logical bytes 5/6 at `6A9DA..6AA06`; logical byte 9 is split at `CC635..CC676` and `CC773..CC78C`; bytes 5/6 high bits are transformed at `CC72A..CC748`. Continue at the actual callees `61580`, `61600`, `CAF60`, and `CAFE0`, and the catalog-flag branch `6A72F..6A9D5`. No omitted byte is labeled a mandatory zero. |
| Eligibility of a selector, catalog row, resource, or NPC template in the live world | Selection is proved only through `6A72F`, before the row dereference at that RVA. Continue through its row flags and the `6A9EF -> 61580` / `6AA06 -> 61600` lookups with current qualified state. Continue actor lookup `CC3BE -> CCF80` or `CBD93 -> CCF80` and actual pool construction at `CC5DB` / `CBFB6`. The synthetic maximum used by these tests is not a live catalog inventory. |
| Map/scene conversion, legal spawn coordinates, timing and persistence | Continue at `CC690` (other branch `CC069`) through `[owner+BC]` and the native map conversion call `CC6E9 -> 49330` (existing-entry `CC4F6 -> 49330`). Those are client scene/display paths. They do not provide original authoritative server placement or persistence rules. A qualified current original server producer/validator remains required; none is available as an input to this bounded lane. |
| Transport delivery and complete playable spawn | Real logical assembly starts after the outer transport gates at `13497`; next preceding work is `13420..13497`, including queue/connection status, and the decoded-queue producer `10AB0 -> 10A10`. No socket or encrypted transport is exercised. Scalar tests stop before map and rendering dependencies. Continue the original paths with current qualified state; no live-playable claim follows from this emulator suite. |

Only these five new owned files are delivered: `tools/strike_lab/current_npc_record.py`,
`tests/research/test_current_npc_record.py`, `src/protocol/RecoveredNpcRecord.h`,
`tests/test_recovered_npc_record.cpp`, and this note. Existing helpers, Session,
CMake, shared runtime, and client files are untouched. No UI automation or
delegated tasks were used.
