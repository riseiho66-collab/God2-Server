# Current quest journal synchronization

Implemented one bounded current-client consumer: S2C `0xDB` journal slots,
subtypes 4 and 5. No request, quest rules, reward rules, DB or shared runtime
changes. All offsets below are RVAs into the mapped x86 image at base 0x400000,
with file offset equal to RVA:

`artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`

SHA-256: `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.

## Runtime API

Header: `src/protocol/RecoveredQuestSync.h`, namespace `god2`.

- `RecoveredQuestSync::emptyJournalLogical()` returns `std::array<uint8_t,195>`.
  It contains 15 consecutive 13-byte DB/subtype-4 slot writes, slots 0 through
  14, packed value zero. Feed the logical array to the parent's shared
  `RecoveredWorldFrame::encode`. No duplicated encryption implementation.
- `RecoveredQuestSync::decode(span<const uint8_t>)` returns
  `optional<SlotUpdate>` for exactly one S2C record; fields are `subtype`,
  `slot`, `packedValue`. This is not a C2S request decoder. Only subtypes 4/5
  and indices below 15 are accepted. Opaque packed values are preserved;
  successful decoding is not authorization for a quest transition.
- `RecoveredQuestSync::clearSlotLogical(uint32_t slot, uint32_t subtype)` returns
  `optional<Record>` (13 bytes). Only slots 0..14 and explicit subtype 4 or 5
  are accepted; packed value and ignored padding are zero. The caller must
  already establish an authoritative single-slot clear in World. Subtype 4
  preserves the selected packed value; subtype 5 clears that value and invokes
  refresh. Subtype 4 on slot 14 also consumes the batch suppression flag.
  Clearing a visible slot is not quest abandonment, completion or reward delivery.
  The subtype input is validated at full u32 width before narrowing to the wire
  byte, so invalid integer inputs such as 260/261 cannot alias subtypes 4/5.

Call the empty encoder only when authoritative data already establishes an
empty journal and the session is in World. It does not establish that a new
character should be empty, reset gameplay state, or synchronize daily/history
state. The codec has no session reference and does not enforce the World gate.

The first record is `db04000000000000000000000000`; the last is
`db040000000e0000000000000000`. Concatenated logical SHA-256:
`75d84ca2e004ad44dccd06f339418faad84c739671c0a8ace17c7d654841eb46`.

## Native evidence

| Evidence | Current instructions / interpretation |
| --- | --- |
| Length table `1324 + 4*DB` | Points to `1246`, returns 13. |
| World table `6B5D4 + 4*DB` | Points to `6B44E`, advances past opcode and calls `854F0`. |
| `854FD..85509` | Payload byte 0 selects a five-entry switch; subtype 4 -> `8565B`, subtype 5 -> `85693`. |
| `8565B..85665` | Passes payload dwords at +4 and +8 to `C9670`. |
| `C9670..C9699` | Unsigned slot <15 check, then writes value to UI+`C2104+4*slot`; invalid index reaches assertion at `C9688`. |
| Assertion at `1940A8` | `nMisIdx<15`, source path at `194028` ends in `pmnpc2.cpp`. |
| `C96BA..C96CB` | Low word zero skips the slot during page calculation. |
| `C96CD..C96D6` | Nonzero indices use resource+`D2AC4` with 40-byte stride. |
| `563E9..5642A`, `584C3` | `Mission_data` section dispatches to `584A0`, whose allocation is stored at resource+`D2AC4`. This establishes the journal connection independently of legacy labels. |
| `C96F1..C973A` | Recalculates pages (minimum one) and clamps current page. |
| `8566A..85681` | Subtype 4 slot 14 conditionally invokes journal open/refresh then clears UI+`232EB0`. |
| `85693..856AD` | Subtype 5 sets UI+`232EB8` before calling the slot writer (including before its index assertion), then invokes journal refresh if the writer returns. |

Record offsets: opcode at 0, subtype at 1, ignored bytes 2..4, little-endian
u32 slot at 5, opaque little-endian u32 value at 9. The encoder zeros ignored
bytes; the decoder accepts arbitrary values there because native quest branches
do not inspect them. This is parser-supported canonicalization, not a captured
server transcript. No nonempty encoder is exposed. No relationship to ACTMIS,
daily missions, prerequisites, rewards or completion conditions is inferred.

## Prior evidence search

Both requested corpora were searched before native analysis. No AGENTS.md was
found in repository ancestors or under the lane's src/tools/tests paths.

Classic root:
`C:/God2Evidence/classic-20260820/files/God2-Classic-Server-Formal-Handoff-20260820-020345/ServerSource`.
`src/God2.ClassicServer.Protocol/OfficialMissionSlotSyncWire.cs` SHA-256
`869fa1db13feea2d34278fac113985f19ca070ea1b7b61c234fd805a4d38291b`
labels DF as mission slots for a different build. Its label is not reusable:
in the pinned image DF -> `6918C` -> `F7980`; the adjacent DD list consumer
`F7A30` references `VEND_GOODS_DATA_SC` and `PMVendCar.cpp` at `19AC20/19AC90`.
The current DB mission-data linkage above is the basis of this implementation.

XJZ root:
`artifacts/legacy-evidence/xjz-20260820/files/XJZ-Server-Cpp/server_implementation`.
`evidence-quest-service-template-v0.md` SHA-256
`6a81782ed8d137de13c08ce10b16793c8b757e81377cbe633ad401f5c6d697ff`
describes 418 templates, 2014 steps, 169 requirements, zero authoritative
reward rows, and inferred names. Its repository contracts provide no proof of
this current wire layout; none of its inferred gameplay relationships are used.

## Verification and bounds

Run `python tests/research/test_current_quest_sync.py -v` from the server root.
The runner compiles `tests/test_recovered_quest_sync.cpp` in a private temporary
directory using C++20 and warnings-as-errors; it neither uses nor edits shared
CMake/build output. The C++ fixture supports `--dump` for the logical bootstrap.

Nine tests cover the C++ decoder, image/mission-loader evidence, native length,
all 15 C++-emitted records through the real `68B61` dispatcher and full slot
consumer, both final-slot suppression states, arbitrary opaque values and
padding, invalid indices, unknown subtypes and truncated native reads. The
single-slot extension adds 30 C++-emitted clear records (both subtypes across all
15 slots), preserving other populated slots, selected-value differences and
batch-flag differences. Sparse sequences clear slots 14, 10, 9, 5, 4 and 0,
including duplicate clears; native page counts are 3, 2, 2, 1, 1 and 1. Current
page 2 resets to zero when page count drops to 2. This is journal display state,
not a recovered quest progression formula.

Native runs use synthetic memory, 418 as the resource catalog bound, poisoned
initial journal slots, and a closed/uncreated journal widget (`UI+232E5A=-1`).
Packets end at a read-only mapped-page boundary. There are **no stubs**; valid
runs return to `6B517` with balanced stack. All 15 slot dwords become zero,
page becomes 0, page count becomes 1, and adjacent canaries remain unchanged.
Invalid indices 15, 255, 0x80000000 and 0xffffffff stop before the assertion
call, with no journal-array write. Subtype 5 has already changed the selected
packed value at that stop; subtype 4 has not. Neither assertion handling nor
continuation after that stop is claimed. The C++ decoder and clear encoder
reject these indices for both subtypes. Native truncations at every nonempty
prefix length 1..12 fault before slot/selection changes, with the packet ending
at an unmapped page. C++ rejects all lengths 0..12 and oversize records before
reading. Unsupported DB subtypes are rejected by the codec; other DB behavior
is outside this lane.

The single-slot fixtures initialize synthetic in-range catalog indices 1..15
and 418, with opaque upper words. They install a nonnull synthetic catalog
pointer; the closed-widget page calculation computes addresses but does not
read catalog rows. No mission definitions, completion conditions or catalog
row contents are fabricated. The original instruction range C96BA..C96E8
tests the low word against the catalog bound, then tracks the highest eligible
slot position rather than the number of occupied slots.

Lane D validation executed on 2026-09-19:
`python tests/research/test_current_quest_sync.py -v` passed all nine tests,
including a standalone C++20 warnings-as-errors build. The fixture's
`--dump-clears` mode emits all 30 records for native differential checks.
Both legacy files named above were reread before this native extension. No
shared CMake, runtime, session, network or Lua files were changed. The existing
`recovered-quest-sync` target already compiles the extended C++ fixture;
registration of any additional aggregate checks remains with the main lane.

This proves the bounded parser/bootstrap with a closed widget, not live client
acceptance, an open-window render, normal login placement of this burst, or an
authoritative initial quest state. No client launch, sockets, external service,
Lua gameplay, transport edits or runtime registration were performed.

## Internal subtype validation improvement (2026-09-19)

The former u8 encoder parameter narrowed wider integer arguments before the
body could validate them: 0x104 became 4 and 0x105 became 5, producing a clear
record despite an unsupported input. The parameter now accepts u32 and checks
for exactly 4 or 5 before casting to u8. Slot validation, the decoder, and the
emitted bytes for supported inputs are unchanged. This is an internal C++ input
validation fix; the wire subtype remains one byte. Callers must still validate
values outside the API's u32 domain before conversion.

Authority remains the pinned current image and its subtype switch at
854FD..85509, with the two quest consumers at 8565B/85693. The differing
selection effects, including subtype 5's selection write before the slot
assertion, make accidentally selecting a supported branch observable. No
meaning is assigned to larger integer subtypes. The Classic mission-slot codec
and XJZ quest-service evidence were reread as references only.

The quest-only fixture adds `--clear <decimal-u32-slot> <decimal-u32-subtype>`:
success emits one hex record and exits 0; encoder rejection exits 1 without
output; malformed numeric arguments exit 2. Inputs reach the public helper
without a test-side u8 cast. Black-box checks exercise 38 invalid pairs,
including high-bit aliases of both supported subtypes and invalid slot indices,
and require exit 1 with empty stdout/stderr. Thirty valid pairs must match the
existing native-tested clear records. Standalone assertions additionally reject
nine wide subtype values at every valid slot, with compile-time checks for
0x104 and 0x105.

Verification: `python -B tests/research/test_current_quest_sync.py -v` passed all
11 tests, including a private C++20 warnings-as-errors build and the existing
pinned native checks. Only the quest header, C++ fixture, Python quest test,
and this document were edited. No shared oracle, CMake, Lua, or runtime changes
were made. Rewards, eligibility, prerequisites, progression, completion,
persistence, authoritative initial state, and live/open-widget behavior remain
unproven; this fix establishes none of them.
