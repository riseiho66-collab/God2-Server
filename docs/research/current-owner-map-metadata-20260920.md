# Current Owner Map Metadata

Same-VM source loader and map-panel metadata binding for the retained C3080
consumer. This bounded helper does not run battle preload, the world constructor,
the retained clock continuation, or the rest of C3080. All addresses below are
RVAs relative to `400000`, except explicitly marked VAs. RVA equals file offset.

## Integration

```python
from tools.strike_lab.current_owner_map_metadata import attach_and_load

# b.native is stopped, outside emu_start and its callbacks.
# b.owner_metadata is the existing NativeItemMetadata in this SAME VM.
metadata = attach_and_load(b.native, owner=0x30000000)
assert metadata.table == b.owner_metadata.TABLE
island = metadata.lookup(2, 0)
```

`owner+CFF70` must already point to the real existing table. The helper never
replaces that binding, item pointer arrays, RomMaps, or retained item records.
The table must have RW parser storage through `+2418`, and RW map slots
`+D2ABA..+D2ABF`; the six map slot bytes must initially be zero. Successful load
changes only those six bytes within the existing table. Temporary parser bytes
`+4..+2417` are restored even if loading fails. Native map records occupy a new
allocation, and their `+1A0` fields are written by original native code.

The host supplies `vm` and its existing `allocate(length)` fresh-allocation API.
Every allocation is checked against earlier VM mappings and the reserved main
owner, world bank, world renderer, battle, character, and main stack ranges.
There are no fixed new object addresses. Allocations are a private 64 KiB stack,
`D440`-byte LZ context, 2,783,008-byte decoded output plus 16 bytes, and
`144*1A4` catalog bytes. Their lifetime is the host VM's allocator lifetime.

Every execution saves/restores the complete Unicorn CPU context and private
stack, including failures. The pending stack at `657F000` is never used.
No second VM is constructed and no pre-existing hooks/virtual file handles are
removed or modified. Temporary BLOCK hooks implement qualified CRT services
before older CODE service hooks. Translation blocks are flushed on entry/exit
so previously translated CRT entries cannot bypass that ordering. No executable
bytes are patched. All temporary hooks are removed on failure as well as success.

Use `metadata.provenance`, `metadata.traces`, `metadata.load_trace`, and
`metadata.bind_trace` for receipts. `lookup(area, scene)` runs original `59D80`
and returns its actual record pointer, `+1A0` pointer, source row hash/line,
image metadata RVA, the `+20/+22` words, and native read/write/instruction trace.
Only explicit WORD selectors are accepted. Null native results remain null.
Repeated loading or a nonempty existing map slot is rejected, never overwritten.
An interrupted load may leave partial native map slots/records; it is not a
successful receipt and the helper cannot retry it as a fresh load.

## Reused Source Proof

The source validation, section parsing, bounds and span come directly from
`current_world_music.music_source()`, reusing the existing complete-source
[music proof](current-world-music-20260919.md). No client inventory was rerun.

| Source | SHA-256 |
| --- | --- |
| `artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin` | `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763` |
| `God2/Data2/Patch/Comm/gamedata.csvZ` | `70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731` |
| Complete decoded gamedata | `75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815` |
| Image bytes `18AC70..18C97B` (143 metadata entries) | `0a0d47e15ff9437d487cfe92aea569f2dd315ce49e1893576cb2eafea4f3072d` |

Original `1EC0` consumes all 719,032 compressed bytes and produces the complete
2,783,008-byte decoded source in the supplied VM. Its internal LZ ring is
initialized by that function; it does not read `1760` constructor fields.
This helper therefore calls the actual decoder directly without entering the
constructor/destructor's unrelated global temporary-file lifecycle.
CRT `1474AB/1474DC/14785C` only supply read-only bytes, with exact caller and
header-size checks. Complete native output is compared to the pinned decode.

The original output supplies `Map_City_Coordniate`, header line 21019,
144 records at lines 21020..21163 and decoded byte span `[2462531,2483449)`.
Original `51920(24)` sets the parser width. The dispatch island
`565AB..565F1`, including call `565EC -> 59A80`, executes the complete native
allocation, all 144 `51A90 -> 51BE0` row reads/tokenizations, field accessors,
record stores and normal `ret 4`. Only section selection/count/stream positioning
are explicit preparation; the top-level loader of unrelated sections is not run.

CRT calloc `147E23`, return `59AAD`, allocates exactly `(144,1A4)` through the
host allocator and provides its defined zero initialization. CRT fgets
`147A95`, return `51AB0`, performs CRLF-to-LF translation on each original row.
Each read receipt contains its exact decoded-source span, source line, SHA-256,
destination and caller. CRT sscanf `1480B4`, return `51BC9`, accepts only the
bounded source `%d` tokens. No row reader, tokenizer or game lookup is replaced.
Python source projections are used only for comparison, never record writes.

## Exact Schema And Binding

| Catalog location | Original meaning/source |
| --- | --- |
| table `+D2ABA` / `+D2ABC` | signed WORD count / record pointer |
| record stride `1A4` | original `59A80` calloc width |
| record `+00/+10/+20` | 16-byte strings, source columns 0/1/2 |
| record `+30/+70/+B0` | 64-byte paths, columns 8/9/10 |
| record `+F0` | WORD: area in low 6 bits, scene in upper 10 |
| record `+F4` | DWORD: kind in low 2 bits, catalog X in bits 2..16, Y in bits 17..31 |
| record `+F8/+FA/+FC` | layer width, layer height, layers per row, columns 11/12/13 |
| record `+FE..+19D` | ten 16-byte layer labels, columns 14..23 |
| record `+1A0` | image-owned map-panel metadata pointer, explicitly cleared by `59D55` |

The missing dependency is original `818DC -> 67EF0 -> 59E70`. The helper runs
the caller island `818D6..818E1` with a scratch descriptor whose `+20` is the
already bound table. Original `67EF0` iterates **143** entries of stride `34`
starting at VA **58AC70**. Original `59E70` compares the image entry's ASCII
name at `+00` to catalog `record+10`, through CRT case-insensitive comparison
`151DE0`, return `59E95`. Native store **59ECC** publishes the actual image
pointer into `record+1A0`; no metadata records are copied into another bank.

All 143 image names have unique matches in the 144-row source. The helper checks
this before running the binder, because the original unmatched-name branch
reads past the record array. Source row `(area=7,scene=3,oldreborn)` has no image
entry and correctly retains null `+1A0`. Every record field, zero padding,
native null initialization, and final pointer is checked against its source.

Example: `59D80(2,0)` finds Island01 and its `+1A0` is VA **58B804**.
Metadata `+20` is unsigned WORD **47** and `+22` is signed WORD **1**.
The image also contains the name/label and other bytes; no extra semantics
for unused fields are inferred. `59D80(2,15)` correctly returns null.

## Proven Consumer Frontier

The optional `probe_c3080(character=CHARACTER_ROOT)` is a diagnostic slice
using supplied character bytes; it does not qualify their packet producer or
consume the retained battle call. It executes these unchanged instructions:

| RVA | Observed dependency |
| --- | --- |
| `C328B` / `C328F` | WORD scene at character-root `+14`, WORD area at `+18` |
| `C3294` | actual table through owner `+CFF70` |
| `C32B6 -> 59D80` | `(area,scene)`, normal return `C32BB` |
| `C32C1` | actual result written to owner `+8AA4C` |
| `C32CD -> 59D80` | `(area,0)`, normal return `C32D2` |
| `C32DA` | read the area record's original `+1A0` pointer |

With diagnostic `(2,15)`, `(2,0)` and `(1,12)`, the exact reached stop is
**C32FD**, before that instruction executes. A missing area stops before the
native assertion branch **C32E2**, without fabricating a result or suppressing
an assertion return. The native owner cache write persists; CPU and stack do not.

Main can load while its original continuation is stopped at **C328B**, then
resume that SAME pending stack directly. Do not call the diagnostic probe first
when measuring the retained continuation's owner writes. Main still owns the
native world-packet production of character `+14/+18` and the retained clock
stage. Later C3080 needs its existing ESI=owner, EBX=character root, EBP=0,
EDI=owner+E2170, panel WORD `owner+232DA6`, character kind byte `+10` on the
null-current-row branch, and the later `owner+8688C` position source.

`C3307` or `C3354` reads the selected record's `+1A0`; `C3311/C3315` or
`C335E/C3362` reads its signed `+22` and unsigned `+20` words. The later call
`C332C` or `C3379 -> 105C20` receives `(panel,word20,4,word22,VA 5B7AA8)` with
ECX=EDI. Those UI calls, `C3343 -> C3B60`, subsequent map controls, the C3080
return and full battle initialization are outside this proof.

## Verification

```powershell
python -B -m unittest discover -s tests/research -p test_current_owner_map_metadata.py -v
```

**7/7 pass in 29.342 seconds.** A single full native decode is shared by the
tests. The lightweight fixture creates real `NativeItemMetadata`, loads and
retains MIS:4660, and attaches to that same bank. It checks all 144 lookups,
143 native pointer writes, exact consumer reads, null behavior, CPU/main-stack
preservation, unchanged item/RomMaps data and other table sections, unchanged
image bytes, reserved owner/bank/renderer/battle canaries, old CRT hook exclusion,
changed code/data/binding rejection, source failure, overlap rejection, repeat
rejection, and interrupted-lookup cleanup. No battle resource preload or shared
bootstrap test runs. Only this helper, its test, and this document are changed.
