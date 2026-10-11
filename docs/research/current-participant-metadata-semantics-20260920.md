# Current Participant Metadata Semantics, 2026-09-20

## Minimal Proven Result

The two 16-byte blocks in logical S2C1C have **branch-dependent semantics**.
Packet offsets below are decimal; metadata/actor offsets and RVAs are hex.

| Qualified branch | Packet -> metadata -> actor | Executed semantic |
| --- | --- | --- |
| variant WORD +5 = `2000` | +9..24 -> +E -> +DBE | NUL-terminated primary displayed name |
| variant WORD +5 = `2000` | +25..40 -> +1E -> +DCE | NUL-terminated secondary display text |
| normal enemy variant `0400` | +9..24 -> +E -> +DBE | Initially lookup coordinates: area BYTE +E and scene WORD +10; original consumer then overwrites actor+DBE with the selected EnyName name |
| normal enemy variant `0400` | +25..40 -> +1E -> +DCE | Not read by the executed normal-name island; no additional semantics promoted |

The secondary text setter is also used by the `Lv:` display path. Its precise
meaning as a player/monster **title system** is not proved, so the promoted
name is only "secondary display text." No appearance encoding or numeric
HP/MP/attribute meaning is promoted from these two blocks.

Main separately reports completed HP/MP semantics for the four 86 scalar
fields. This lane does not rerun that proof or contradict it: the 1C blocks
studied here are distinct from actor+DE8/+DEC/+DF0/+DF4. None of this lane's
consumer traces reads or writes those four fields, and it recovers no original
wild HP/MP values. No ROM work or complete constructor execution is required
for the bounded semantic results above.

## Static Xrefs First

Pinned image:
`artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`.
SHA256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
BASE `400000`; RVA equals mapped-image file offset.

The bounded Capstone operand scan covers only `110000..12F550` and finds 77
direct displacement **candidates** in DB0..DE7. Candidates are not automatic
type attribution: `115C23`'s DD4 displacement indexes ProgramMsg storage,
not actor metadata. Indirect metadata arguments are followed separately:

| RVA | Observed reference |
| --- | --- |
| `121A3F/121A4A` | Destination actor+DB0, 14 original DWORD copies |
| `12D19A/12D1A1` | Metadata+E passed to original `1097D0` |
| `12D1AD/12D1B4` | Metadata+1E passed to original `109E70` |
| `12D0C4/12D0C8/12D0D0` | Ordinal WORD +C, scene WORD +10, area BYTE +E |
| `12D12B/12D132` | Selected EnyName record+2 passed to `1097D0` |
| `12D142/12D151/12D15C` | EnyName NUL-terminated name copied to actor+DBE |
| `116577/116582/116593/11659A` | Later actor+DBE NUL scan and string copy |

JSON retains raw instruction bytes, RVAs, disassembly, bounded scan limits,
and hashes of all executed instruction spans.

## Original Execution and Provenance

The lightweight fixture reuses `MonsterSideInitializationProbe` with
`fight_rows_loaded=False`: existing descriptor helpers and a single original
EnyName row writer, without FightEny or ROM loads. Current gamedata source:

- `Data2/Patch/Comm/gamedata.csvZ`, SHA256
  `70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731`.
- Decoded SHA256
  `75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815`.
- Selected EnyName generation1/area1/scene0/ordinal1, source_record_index0;
  decoded offset **2500917**, line **21699**, row SHA256
  `34e14a591490fd9f6444f8776bcc7f0cc39699dfd78a13b2feb097c3636c5f32`.
- Name bytes `A454B84FC06E`, followed by native NUL; no invented name or stat
  is returned by a game-function stub.

All packet operands, initial actor bytes and display-record bindings are
explicit diagnostic fixtures. The source-backed name is distinguished from
these fixtures in the report.

For variant2000, the original entry runs continuously
**115C90 -> 116149 -> 116166**, including real slot lookup and all 14 metadata
stores at `11615C`. Both 16-byte packet blocks reach actor+DB0 through native
stores. The existing merge/copy is a prerequisite, not the novel semantic
claim. All 14 paired side0/side1 positions preserve the same metadata contents.

For normal0400, the merge stops at **115DF1**. A separately declared
**121A30..121A4C constructor-tail island** copies the exact native-produced
metadata to actor+DB0. This does not cross or claim to resolve the previous
ROM constructor dependency. The null-source branch also executes: it writes
actor+1EA=0 but leaves metadata untouched.

The consumer operand fixture points the metadata argument at actor+DB0.
This proves the semantics of those exact bytes; it does not assert that every
original caller passes an actor alias rather than a separate metadata buffer.

### Two Text Consumers

From **12CE4B**, original type dispatch selects **12D193** for the tested
metadata type4000 produced by packet variant2000. The real calls and real
returns of `1097D0` and `109E70` execute, ending **before 12D1B9**.

- `10980E/109851` scan primary text to NUL; `109864/10986B` copy it.
- `109EAE/109EF4` scan secondary text to NUL; `109F0A/109F11` copy it.
- Native padding is `max(0, floor((14-byte_length)/2))` ASCII spaces.
- Destinations are display base + `A7E0*handle +70` and `+81`, respectively.
- Original getter **109F20..109F71** reads the secondary slot back as a
  NUL-terminated string, executes its real return and supplies EAX=1.

This is actual string consumption and destination writes, not an inference
from DWORD transport copies. No CRT or game-function returns are adapted.
Valid display storage is explicitly supplied; no rendered UI is claimed.

### Normal Enemy Name

Original type dispatch instead reaches **12D02A** for normal0400. That level
display path remains separate from the explicitly entered name island
**12D0C4..12D15E**. The island executes original **12D0D9 -> 5A0A0**, verifies
the original identity pointer, calls the real primary text setter at
**12D132 -> 1097D0**, then scans and copies the real EnyName name to actor+DBE.

Its exact metadata reads are WORD+C at `12D0C4`, WORD+10 at `12D0C8`, BYTE+E
at `12D0D0`, and DWORD+4 at `12D0EA`. It does not read metadata+1E..+2D.
Only the name plus NUL is overwritten at actor+DBE; the rest of that block,
the entire second block, actor scalar fields and guards retain their previous
bytes. Changing every byte of the second block does not change this result.
The separate **116577..11659C** native consumer then reads that same actor
name back through its real NUL scan and copy.

## Guards and Remaining Local Boundaries

Tests use poison A5/3C/FF, lengths 0/1/6/14/15, embedded termination followed
by different padding, valid handles 0/1/4095, and real invalid-handle/inactive
record branches. A missing terminator stops at the attempted native scan
beyond the corresponding 16-byte field; it is an oracle bound, not a native
sanitizer. No overflow-derived adjacent-field semantics are inferred.

With the selected EnyName payload page deliberately unmapped, normal lookup
still computes its source pointer, but execution stops **before 10980E**, the
first unbacked name scan. With an absent scene, the real lookup returns null
and the native branch reaches **12D184** without any name write. These guards
run on both sides. The native metadata-copy null-pointer guard is separate.

Remaining local instructions are **12D1B9 onward** (following display
bindings), **12D15E onward** (category/color and subsequent display work),
the intervening normal level/display path before 12D0C4, and the prior full
constructor dependency at 1206E0. Packet variants outside 0400/2000 are not
promoted by this suite. No further ROM investigation is needed for this
delivery; no global absence of other numeric producers is asserted.

## Verification

```powershell
python -B tests/research/test_current_participant_metadata_semantics.py -v
python -B -m tools.strike_lab.current_participant_metadata_semantics
```

**Complete new suite: 10/10 passed in 2.776 seconds.** Tests permit file opens
only for the pinned image and exact current gamedata.csvZ. Native access logs
retain RVA, address, region/offset, width and bytes for every read/write.
Only the three requested new files were added; no existing file, CMake,
status, database, production code or shared bootstrap was changed.
