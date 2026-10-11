# Current Monster Side Initialization, 2026-09-20

## Result and Battle-Start Question

The initial logical **1C participant record is 45 bytes**, and the qualified
normal-enemy path reads every byte at **+1..+44**. It contains a packet-supplied
displayed level, identity/variant/ordinal fields, two opaque 16-byte blocks, and
a DWORD flags field. These are not an established full HP/MP/attribute record.
No original official battle-start batch was captured or supplied in this work.
Consequently neither the number/order of initial messages nor whether that
batch also contains scalar updates is established. A TCP batch is not itself
one logical participant record. All injected packet values here are diagnostic.

**New continuous frontier:** original `115C90` now executes through the
previously unexecuted normal resource selection, path construction and
`115FC2 -> 120650` resource-name lookup prefix, stopping **before `1206E0`**.
Same original EnyName occurrence, same VM and actor pointer, paired side1/side0:

- Side1 selects source path `data2\fight\eny\eny5015.rom`.
- Side0 selects source path `data2\fight\eny1\eny1015.rom`.
- The 56-byte metadata buffer is identical on both sides.
- Neither run writes actor metadata or the four DWORDs `+DE8,+DEC,+DF0,+DF4`.
- Original numeric table bytes `16` and `0F` are consumed as routing flags and
  a resource selector. They are not combat statistics.

This is a constructor **prefix**, not completed initialization or recruitment.
The unexecuted remainder can still matter. No original wild numeric values are
recovered, and all requested field authority remains null.

## Exact Initial Packet Reads

Instruction addresses and actor/metadata offsets below are hexadecimal.
Packet offsets in this table are **decimal**, measured from logical opcode +0.
`M` is the native 56-byte stack metadata buffer, `entry_SP-16C`.

| Packet bytes | Native reads (RVA) | Executed destination/use |
| --- | --- | --- |
| +0 | None inside `115C90` | Opcode handled outside this entry; existing `12A6` length proof is reused |
| +1 BYTE | `115CA8` | Position divided by 14 to obtain side/local slot |
| +2 BYTE | `115D2F` | Displayed level in M+7, stored with packed DWORD at `115DD7` |
| +3..4 WORD | `115D10` | Identity word at M+0 via `115D23`; no source template-ID claim |
| +5..6 WORD | `115D19,115DF1,115E0E` | Variant/type bits, metadata packing and normal-bank routing; tested value `0400` |
| +7..8 WORD | `115DDB` | EnyName ordinal at M+C via `115DDF`, original lookup argument |
| +9..12 DWORD | `115D88` | M+E via `115D8D`; BYTE +9 reread at `115E02` as area, WORD +11 reread at `115DFA` as scene |
| +13..16 DWORD | `115D99` | M+12 via `115D9C` |
| +17..20 DWORD | `115DA0` | M+16 via `115DA3` |
| +21..24 DWORD | `115DA7` | M+1A via `115DAA` |
| +25..28 DWORD | `115DB1` | M+1E via `115DB4` |
| +29..32 DWORD | `115DB8` | M+22 via `115DBB` |
| +33..36 DWORD | `115DBF` | M+26 via `115DC2` |
| +37..40 DWORD | `115DC6` | M+2A via `115DC9` |
| +41..44 DWORD | `115D6B` | M+8 at `115D71`; if bit0 set, `115D77` replaces the entire value with 1 |

The two blocks +9..24 and +25..40 are copied as bytes. Apart from the explicit
area/scene interpretation, no full numeric-stat semantics are asserted. In
particular, reading four bytes with a DWORD instruction does not make them a
combat scalar. Flags tests use `0,1,FEFEFEFE,FFFFFFFF`, verifying normalization
without any actor scalar write. Level counterfactuals 0/255 change only M+7.

The actor lookup succeeds on the same actor address in both cases. Thus
`115CF9..115D08` first copies its prior metadata into M. Tests use poison rather
than silently zero-initializing this prior state, and compare the complete
actor allocation plus its trailing guard after each call. Later tests use the
actual native reset result instead of poison; the conclusion through this
frontier is the same.

## First Scalar Storage Writes

The existing initializer already qualified
`111424 -> 11FC40 -> 11FCA4 -> 11FDE0` for the battle arena. This work does not
claim that prerequisite as new. A lightweight, separate invocation of the
original single-record `11FDE0` makes its exact scalar write provenance visible:

| RVA | Effect |
| --- | --- |
| `11FDF2` | ECX=`3B3`, covering the `ECC`-byte actor |
| `11FDF7` | EAX=`CDCDCDCD`, immediate instruction constant |
| `11FDFE` | `REP STOSD` fills the actor, including DWORDs +DE8/+DEC/+DF0/+DF4 |
| `11FF12..11FF24` | Separate zero fill begins at +DF8; it does not cover those four DWORDs |
| `11FFC7,11FFD2` | Metadata +DB0..+DE7 is cleared, then its first WORD becomes FFFF |

Each of the four scalar fields receives exactly one reset write, from
`11FDFE`, value `CDCDCDCD`. That is a fill constant, not an initial monster
measurement. After reset, both new 1C runs preserve it through `1206E0`.
The reset and participant executions are explicitly separate stages, not a
continuous full battle entry.

For comparison only, the already-qualified subsequent logical **86** record is
17 bytes: subtype BYTE +1, position BYTE +2, supplied DWORDs +5 and +9.
Existing side0 evidence maps subtype0 +9 -> actor+DE8 (`12D86C`) and +5 ->
actor+DF0 (`12D875`); subtype1 +9 -> actor+DEC (`12D99C`) and +5 -> actor+DF4
(`12D9A5`). These are packet copies. The new suite does **not** rerun that
dispatcher, side-flip experiment, or role-property packet-copy proof. Whether
86 or other richer messages accompany initial 1C records in an official batch
remains a capture/sender-provenance question.

## New Source-to-Consumer Edge

The pinned image is
`artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`,
SHA256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
BASE=`400000`; all RVAs equal raw image file offsets.

Reuse: `_LookupFixture`, `pinned_catalog`, `NativeWorldActor._map_rw`, and the
established `NativeIndoorResources.cstring` layout helper. No full battle
resource object or graphics preload is constructed. Descriptor layout is
source-derived fixture data, not a new full EnyName loader claim.

The selected original identity is **EnyName generation1/area1/scene0/ordinal1,
source_record_index0**. Source is current `Data2/Patch/Comm/gamedata.csvZ`:
raw SHA256 `70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731`,
decoded SHA256 `75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815`.
Its original row is at decoded byte **2500917**, line **21699**, SHA256
`34e14a591490fd9f6444f8776bcc7f0cc39699dfd78a13b2feb097c3636c5f32`.

The already-qualified EnyName row writer is reused narrowly: execute original
`51BE0` tokenization and `5A2B4..5A516` for this one row, with the original
zero-allocation contract for its 26-byte record. No invented packed table
bytes are substituted. Decimal decoded source offsets:

| Source column (zero-based) | Offset / token | Original store |
| --- | --- | --- |
| 2 | 2500926 / `1` | `5A2E5`, record+0 high nibble |
| 3 | 2500928 / `0` | `5A2FD`, record+0 bit0 |
| 4 | 2500930 / `15` | `5A30A`, record+1 = 0F |
| 5 | 2500933 / `3` | `5A323`, record+0 bits1..3; final byte16 |

**Novel consumption:** `115E7F` reads record+0, selects non-appearance branch;
`115F2F` reads record+1. Native arithmetic at `115F3F/115F44` produces resource
index14 and auxiliary selector2. `115F81` computes
`B+40B9C + 92*(250*side + 14)`. The same record pointer is retained as identity
evidence on both runs; no name-based join is used.

That address corresponds exactly to the reader at B+2E9B0 bound by original
`110CDD..110CE4 -> 54210`, using literal `FightEny.csv` at `19C5B4`.
Current `Data2/Patch/FightEny.csvZ` raw SHA256:
`887f721a429aaa394d79787ccbd42d544cbcc53a878802cd5f8d010e55dc5a6a`;
decoded SHA256:
`30aa86a6001919289090f924bbde727eab5e100ff4db6d71406e60260ed22c40`.
Selected row15 is at decoded byte **2105**, line **55**, SHA256
`1ca4fa4da3bff379520bb5617240201c6289fe12316ad1572e1586ae5a2a249b`.

**New producer execution:** original `51BE0` and `54290..54478`, including
original `51AE0/51B50/51B60/51BA0`, populate both 92-byte resource records.
This is a single-row loader slice, not a complete `54210` file load.

| Source column | Decoded offset / token | Original writes |
| --- | --- | --- |
| 1 | 2110 / `15` | Native decrement/stride computes index14 |
| 4 | 2118 / `6015` | `5435B/54367`: side1/side0 WORD row+2 |
| 7 | 2180 / `1` | `54378/54385`: side1/side0 WORD row+4 |
| 5 | 2123 / `data2\fight\eny\eny5015.rom` | `543F2/543F9`: side1 path row+C |
| 6 | 2151 / `data2\fight\eny1\eny1015.rom` | `5446B/54472`: side0 path row+C |

The row+0 runtime handle and other untouched bytes retain poison. Nothing
pretends that a CSV number is a loaded ROM handle. During the participant run,
only row+C's path is consumed; row+2 and row+4 **are not yet read**. Those two
source numbers therefore do not initialize combat scalars in this trace.

## Exact Stop and Missing-Source Guard

For the complete supplied row fixture, one uninterrupted `115C90` invocation
executes `115F90 -> 12F550` path construction and `115FC2 -> 120650` up to
**1206E0**, bytes `8B 4D 08`, before loading `[manager+8]`. The next call is
**1206E5 -> 29820**, the unresolved ROM-bank load. The name registry is an
explicit empty fixture, so the native cache miss is real. No successful
resource handle or game-function return is supplied.

When FightEny producer output is omitted, both resource rows remain **unmapped**.
The same original entry reaches **12F57D** and stops before its first path byte
read (`CMP BYTE PTR [EAX],5C`), EAX=selected row+C. No path is formatted, no
`120650` call occurs, and no actor byte changes. This is an oracle guard before
an unavailable read, not a claim that the native game gracefully handles
missing resources.

CRT `strchr/memcpy/sscanf/sprintf` and two CString constructors use bounded
adapters at exact return sites. Only these library returns are adapted; no
game callee is replaced. Cached CWD `C:\Oracle` is an explicit diagnostic
environment input. Original native stores and adapter accesses have separate
trace markers. JSON retains all instruction visits and each memory access's
RVA, absolute address, region-relative offset, size and bytes, along with
source row offsets/hashes. CRLF -> LF translation is recorded.

Remaining unexecuted instructions include `115FC7` resource-handle store,
`115FCE` resource row+4 read and `115FED` metadata merge, `116000 -> 120000`,
`116025 -> 1216C0`, and metadata copy `121A30..121A4C`. The latter stays static;
this work does not jump across the missing ROM dependency to manufacture a
constructor result. Full post-resource scalar initialization is unresolved.

## Verification

```powershell
python -B tests/research/test_current_monster_side_initialization.py -v
python -B -m tools.strike_lab.current_monster_side_initialization
```

The focused suite covers exact packet/table reads and source stores, all 14
paired side positions with one actor pointer, poison A5/3C/FF, level and flags
counterfactuals, both missing-source guards, the already-qualified reset's first
scalar fills, instruction integrity, execution budgets and null authority.
Only the pinned image and two exact current CSVZ files may be opened by tests.
No original official numeric values, complete battle batch, full recruitment,
production integration, DB operation, GUI/network work, child workers, or
retired-source access is claimed or performed.

Verified: **8 tests passed in 2.724 seconds**. The module's stdout also parsed
as JSON successfully. Each supplied-source participant run executes 312
instruction visits, stopping at 1206E0. Source prerequisite stages execute
304/261/325/893 visits respectively (enemy parse/write, FightEny parse/write).
Only the three requested new tool/test/document files were edited. This
workspace has no Git repository metadata, so no Git diff/status claim is made.
