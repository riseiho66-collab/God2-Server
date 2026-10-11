# Current native battle participant consumption

## Bound and provenance

Only current `native-master-01-stable.bin` is evidence:
`artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`,
SHA256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
VA base `400000`; all instruction addresses below are RVA/file offsets, hex.
`B` is the explicit battle object and `M = B+144938` its embedded manager.
Packet offsets below are hex and include the opcode at offset zero.

`native_length(83)` and `native_length(84)` each execute the original length
lookup and return **15 decimal bytes**. This is not a transport codec proof.
The new harness starts once at the real post-copy opcode switch `114332`, with
the logical record at `B+A9E9CB0` and original dispatcher register/stack state.
It does not start/resume in a callee, patch instructions, or replace returns.
Every run hash-checks the image; code remains read/execute. Tests also compare
the complete loaded image after execution with the pinned original.

**Result: these qualified paths update existing type-0 entities. They do not
establish actor allocation, battle initialization, live entry, or authority.**
The supplied actor/resource snapshots are explicit test preconditions, not
claimed captured live state or manufactured return values.

## Dispatch and actor selection

`83`: case `11436B`, call `11439C -> 116AE0`.
`84`: case `1143DD`, call `114410 -> 116740`.
The dispatcher compares its existing gate against byte `+3` for 83 or `+8`
for 84. A gate of `-1` first stores that byte, then stops before the unqualified
reset call `114384/1143F6 -> 12AF90`. A nonmatching gate writes zero to
`B+A9EA4C4` and `B+A9DF6C0`, writes one to the caller output, and reaches
`1145C0` without entering either consumer.

Both consumers clear DWORD `B+A9E9C6C`. With phase DWORD `B+A9DF6B8 = 0`,
they set it to one and stop at `116B14/116771 -> 12AEE0`. The deeper tests
supply an already-started phase (`1`) before dispatcher execution.

| Field | 83 | 84 | Native interpretation proved here |
| --- | --- | --- | --- |
| Packed source | BYTE `+2` | BYTE `+5` | side = value / 14, slot = value % 14 |
| Target masks | WORD `+5`, WORD `+7` | WORD `+1`, WORD `+3` | side 0 then side 1; lowest set bit among bits 0..13 |
| Gate/marker | BYTE `+3` | BYTE `+8` | existing gate comparison; later `M+309` and source `+1E7` |

Valid packed sources are **0..27**, sides **0..1**, slots **0..13**. Values
28/255 stop before assertion `116C03/1168AF -> 2C70`; no assertion return
is fabricated. Mask bits 14/15 are ignored. An empty effective mask falls
back to the source for 83; 84 instead stops at `116917 -> 2C70`.
For 83 subtype 3, selector BYTE `+C == 2` also selects the source after the
mask scan (`116C4E..116C5B`); subsequent target use is outside that path's stop.

Original lookup `11E6E0` is executed, not modeled: type 0 reads
`[M+38 + 4*((side*14+slot)*6)]`. Fixtures install distinct poisoned actors
only at explicitly supplied positions and make all other slots null.
84 with a missing target really returns zero to `114415`. 83 subtype 1
with a missing source returns through `12C520`, then returns one to
`1143A1` **without creating anything**; that return alone is not success proof.

## 83 subtype 1: record to action state

BYTE `+1` selects the subtype. At `116C9C`, BYTE `+B != 0B` selects BYTE
`+C` for helper `1169F0`; otherwise its default is `1C`. For a local target
(side zero and slot equal to `B+51`), that helper can modify DWORD
`B+A9E9C74`. Both opcode tests with action byte 4 prove its bit-4 OR at
`116A3E` against nonzero prior flags.

`117183 -> 12C520` finds the source entity and copies BYTE `+3` to `M+309`.
When source BYTE `+239` is zero, original instructions reset these ranges:

- source WORD `+2C4 = 0`;
- source `[4D0,55C)` to `FF` (8C bytes);
- source `[B60,D90)` to zero (230 bytes);
- source `[55C,62E)` to zero (three 46-byte ranges).

Nonzero `+239` bypasses those resets. Through `12C60D -> 12A8D0`, original
type-0 lookups and handle checks lead to source `+1E7 = marker`,
`+1E9 = 1`, `+1EA = 11`, `+233 = 0`, and
`+235 = (old & 70) | targetSlot | (targetSide << 7)`.
The source receives target BYTE `+277`, then target `+277` increments,
including byte wrap and source/target aliasing. The tested entity WORD
`+1A` handles are already below unsigned `1000`; no binding is claimed.

**Default stop `12C631 -> 12B060`**, after its arguments have been pushed:
source side, source slot, target side, target slot, WORD packet `+9`, zero,
BYTE packet `+B`, constant `22`. BYTE/WORD loads leave upper register bits
live; tests check the actual argument widths, not invented zero-extension.
The default mode does not enter `12B060`; the opt-in continuation below
qualifies only its prefix, not resource/animation completion.

At this stop the observed record reads are `+0,+1,+2,+3` bytes, `+5` word,
`+9` word, `+B,+C` bytes for the first-side target test. Scanning side one
also reads WORD `+7`. Bytes `+4,+D,+E` are not read on this prefix; they are
not declared padding or assigned speculative meanings.

## 83 subtype 3: association before resource lookup

`116CF5` reads `M+20` but does not dereference it before this bound.
The source's pointer array starts at `+DF8`. Native code scans for a null
entry or one whose first two bytes match packet bytes `+B,+C`. Tests cover
an empty array, matching first entry, and a mismatching first entry followed
by an empty slot. They do not qualify an exhausted array's behavior.

At `116DC1`, it writes the selected source pointer-array slot to
`B+A924D12 + packet[+B]*110 + packet[+C]*28164` (multipliers decimal).
It then stops **before `116DF1 -> 5F490`**, with
`ECX=B+4BF4C`, arguments `(BYTE +C, BYTE +B)` in their native low widths.
That table lookup, pointer contents, later association initialization, and
selector/resource bounds are not qualified. No guessed resource result is
installed. Subtypes other than 1 and 3 are rejected by this bounded harness.

## 84: metadata, effect writes, action state

After target lookup, WORD packet `+9` is passed at `11696A -> 59A60` with
owner `[B+28]`. The original helper requires key `< 7F58` unsigned and reads
`[owner+B2D40+key*4]`. No snapshot supplied means stop before this call;
null metadata or an out-of-range key reaches assertion `116982 -> 2C70`.

At `11698C` the metadata WORD `+112` is sign-extended. Call
`1169A2 -> 116640` receives `[M+10]`, that signed value, and target `+1CC`.
The supplied `M+10` pointer is not dereferenced before the tested stops.
Effect zero natively writes `FFFF` to target WORDs `+1CC,+1CE,+1D0`.

For positive families 84/85 (decimal quotient by 100), `5E0B0` runs against
embedded owner `B+8345C` / `B+95650`: count at `+121E8`, records pointer at
`+121EC`, stride **214 hex**, index = effect % 100. Explicit count misses
also produce the three `FFFF` words, through the original return path.
Missing table state instead stops before `116671 -> 5E0B0`.

With a record present, its signed WORDs `+0,+2` gate resource preparation:

- negative WORD `+0`: stop **`11668A -> 12F550`**, before any target effect write;
- nonnegative `+0`, negative `+2`: first write `+0` to target `+1CC`, then
  stop **`1166C1 -> 12F550`**;
- both prebound: copy record WORDs `+0,+2,+6` to target `+1CC,+1CE,+1D0`.

`12F550` is the next unqualified resource-path/string helper, not a proved
loader. The later manager binding call `1166A1 -> 120650` is **not reached**.
Prebound values are explicitly supplied runtime-handle snapshots, not CSV
indices or fake loader returns. No origins/resource investigation is included.

The prebound/zero/miss paths continue through `12C430 -> 12A8D0`, writing
`M+309 = packet[+8]`; source `+1E7 = packet[+8]`, `+1E9 = 5`, `+1EA = 85`,
`+233 = 0`, and packed target `+235` preserving bits 4..6. Unlike the tested
83 subtype 1 path, this does not reset the large source ranges or increment
target `+277`. All 1000 hex bytes of both poisoned actors are checked.

**Default stop `12C486 -> 12B060`**. Pushed arguments: source side/slot, target
side/slot, WORD packet `+B`, WORD packet `+D`, BYTE packet `+6`, BYTE packet
`+7`. BYTE `+7` is also passed through `1169F0`. These are proven widths
and consumers, not speculative HP/damage/name/equipment meanings.

## Opt-in continuation through 12B060

The continuation preserves every old default boundary. `consume` accepts
optional `action_state` with **exactly** these two keys:

- `manager_tail`: exactly `150` hex raw bytes for `[M+A7FBC5C,M+A7FBDAC)`;
- `manager_0c`: an unsigned DWORD snapshot for `[M+C]`.

Unknown keys, absent fields, wrong byte lengths/types, and out-of-range DWORDs
are rejected. No other fixture API or shared file is changed. This state is
installed before the single original `114332` start; it does not substitute
for the native `12C631/12C486 -> 12B060` call. Earlier gate, phase, and resource
stops still apply. The supplied `[M+C]` resource owner remains **unmapped**.
The proven prefix forms addresses/arguments from it but never dereferences it.

`12B077` and `12B08C` call the original type-0 actor lookup again. A null actor
or invalid target WORD `+1A >= 1000` returns via actual `12B844 RET 20`, stopping
at the caller's `12C636/12C48B` before its unqualified suffix. The tested 84
invalid-target paths return without reading the new manager snapshot or
calling `1224A0`; reaching a caller return does not imply action success.

At `12B11D/12B12B`, native code reads two DWORDs at
`M+A7FBCCC + targetPackedPosition*8` and the following `+4`.
It passes source BYTE `+277` to **original `12B132 -> 1224A0`**. That helper
reads WORD `[VA59D198+index*2]`, using zero when its signed argument is below
one; it contains no upper-bound check. The tested byte indices 0/2/3 yield
signed values 0/-1/2 from the pinned image. Source `+277` is read **after**
the earlier caller-path entity writes, not from an independently resumed
fixture. For 83 subtype 1 this is the ordinal copied from the target.

`12B137` sign-extends that returned WORD. `12B140/14C/153` preserve the first
DWORD and calculate `secondDWORD + 15*signedWord` with 32-bit wrap. Tests use
distinct nonzero pairs for all 28 positions and exercise targets 0/13/27.
These are raw native values; no screen-space/unit or resource meaning is
invented. A 50-byte local buffer is initialized using original byte
`VA5B4640` (zero in the pinned image) followed by 49 native zero writes.

### 83 subtype 1: new actor words and signed formatting argument

Original instructions `12B3CD` / `12B3D4` write:

- source WORD `+286 = packet WORD +9`;
- source WORD `+288 = 0` (the existing 83 caller's next argument).

All other source/target bytes are compared with the complete previous-prefix
expectation. Tests cover packet words `0000`, `7FFF`, `8000`, `FFFF` and prove
that the write preserves raw WORD bits while the subsequent formatting
argument is sign-extended. No new direct packet offset is read inside this
callee; these are further consumers of the original caller's arguments.

For packet BYTE `+B = 9`, stop **`12B49C -> 147AF7`**, with pushed arguments
`(localBuffer, VA59D968, signExtend16(packet[+9]))`.
The original switch also proves BYTE `+B` values 6/7/8 select stops
`12B453/12B43A/12B421 -> 147AF7` with templates
`VA5B4640/VA59CE00/VA59CE48`, respectively. These tests still prove both
actor WORD writes, without simulating formatted output or executing a
formatting helper. No damage/health semantics are assigned to the WORD.

### 84: native cleanup or next setup call

For the existing fixture's packet BYTE `+7 = 4`, native comparisons choose
the path with no formatting call. This is an original branch, not a skipped
call. It reads source WORD `+2C2`:

- `< 1000`: stop **`12B36A -> 1B330`**, with native argument
  `[M+C] + handle*290 + 10` (all hex). Tests cover handles 7 and FFF.
  No cleanup return is invented and no handle is marked released.
- `>= 1000`: the original inactive-handle branch reaches
  **`12B397 -> 11DC00`**, `ECX=source+2C8`. Its six pushed arguments are
  `[M+C]`, WORD `[M+A7FBC5C]`, the first pair DWORD, the adjusted second
  DWORD, zero, WORD `[M+A7FBC60]`. Partial WORD loads leave upper register
  bits live; tests assert only the proven WORD widths for those two fields.

At both stops the poisoned source actor has **no additional writes beyond
the earlier 84 action prefix**. In particular, the later stores to `+286`,
`+288`, and `+2C2` after `11DC00` have not executed. Full target effect writes
from the earlier real consumer are retained, and the manager snapshot is
unchanged byte-for-byte.

Packet BYTE `+7 = 22` instead stops at **`12B1F3 -> 147AF7`**, passing signed
WORD packet `+B`. Value `24` stops at **`12B23B -> 147AF7`**, passing signed
WORDs packet `+B,+D` in that order; tests use `8000,FFFF` and prove DWORD
arguments `FFFF8000,FFFFFFFF`. These are formatting inputs, not inferred
gameplay meanings. None of these formatting calls is stubbed or executed.

## Verification and next needs

Run from repository root:

```powershell
python -B -m unittest tests.research.test_current_battle_participant -q
```

62 cases (the original 42 plus 20 continuation cases) pass. They cover
original byte witnesses, both native lengths, a single
continuous dispatcher start, entire-image immutability, full poisoned-actor
comparisons, side/slot limits, both mask sides, absent actors, gate/phase
boundaries, metadata bounds, signed effects, prebound handles, resource
misses, exact partial writes before unknown calls, opt-in input rejection,
real caller/helper execution, signed argument consumption, native inactive
and active handle branches, and exact raw manager reads. Packet read hooks
reject accesses beyond the 15 supplied logical bytes. Both extended opcode
tests recheck the complete original image after execution.

Current next needs: real `147AF7` for the formatting branches; real `1B330`
and its backing resource state for an active 84 handle; or real `11DC00`
with its owner/state for the inactive 84 path. `5F490` remains the separate
83 association boundary. Unbound effects still need real `12F550` and later
binding, not these snapshots as resource-production evidence. This task
ends at those explicit calls; no full battle, server authority, runtime
launch, or producer codec claim is made. Only the participant module, its
test, and this doc are changed; no initializer, resource integration, UI,
runtime, or CMake edits.
