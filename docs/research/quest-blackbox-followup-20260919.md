# Quest journal opaque slot encoding and replay follow-up

Lane A, 2026-09-19. One deliverable: a source-backed opaque single-slot
encoder with native black-box checks for catalog boundaries, malformed display
state, and replay side effects. No defect was demonstrated in the existing
decoder. No quest progression or rewards are inferred.

## Scope and contract

Changed paths only:

- `src/protocol/RecoveredQuestSync.h`
- `tests/test_recovered_quest_sync.cpp`
- `tests/research/test_current_quest_sync.py`
- `docs/research/quest-blackbox-followup-20260919.md`

`RecoveredQuestSync::encodeSlotLogical(uint32_t slot, uint32_t subtype,
uint32_t packedValue)` returns `optional<Record>`. It accepts slots 0..14 and
subtypes 4/5, validates before narrowing, preserves every packed-value bit,
and zeros ignored padding. The record remains 13 bytes: DB, subtype, three
padding bytes, little-endian u32 slot, little-endian u32 packed value.
`clearSlotLogical` delegates with packed value zero; empty-journal encoding
and strict decoding retain their contracts.

The caller must establish the authoritative value and World session gate.
This helper has no session reference, does not validate a gameplay state,
and is not registered for runtime emission. Out-of-catalog low words are
preserved as the native writer does; accepting bytes does not authorize use
of those values as quest definitions. The earlier current-quest document's
statement that no nonempty encoder is exposed describes the pre-follow-up API.

## Authority checked before implementation

Read `current-quest-protocol-20260919.md`, `quest-recovery-20260919.md`, and
the existing C++ and native quest tests first. Existing truncation, slot-bound,
clear replay, and subtype-alias tests already cover those risks; this change
adds three tests for the new contract rather than another fuzz sweep.

Both required legacy references were read and their hashes checked:

- XJZ: `artifacts/legacy-evidence/xjz-20260820/files/XJZ-Server-Cpp/server_implementation/evidence-quest-service-template-v0.md`;
  SHA-256 `6a81782ed8d137de13c08ce10b16793c8b757e81377cbe633ad401f5c6d697ff`.
  Its 418 templates and zero authoritative reward rows establish no new wire semantics.
- Classic: `C:/God2Evidence/classic-20260820/files/God2-Classic-Server-Formal-Handoff-20260820-020345/ServerSource/src/God2.ClassicServer.Protocol/OfficialMissionSlotSyncWire.cs`;
  SHA-256 `869fa1db13feea2d34278fac113985f19ca070ea1b7b61c234fd805a4d38291b`.
  Its three-byte DF contract is for another build and is not adopted here.

Authority is the original mapped x86 image
`artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`,
SHA-256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
The test checks this hash before execution. RVAs inspected directly:

- `8565B..85665` and `85693..856A6`: pass full slot/value dwords to `C9670`.
- `C9674..C9699`: unsigned slot bound, then complete dword storage.
- `C96BA..C96E8`: low-word catalog eligibility affects display page calculation,
  not whether the supplied dword is stored.
- `C9721..C9731`: signed page-word comparison; negative page values survive.
- `8566A..85681`: subtype 4, final slot, suppression flag read and consumption.
- `85696`, `856AD`: subtype 5 selects the value and calls refresh each time.

## New black-box observations

The C++ fixture exposes `--encode <decimal-u32-slot> <decimal-u32-subtype>
<decimal-u32-value>`. Successful encoding exits 0 with one hex record;
unsupported helper inputs exit 1 without output; malformed/out-of-u32 text
exits 2 without output. Native tests consume these emitted bytes, not a
Python reimplementation of the encoder.

- Full values `0x123401A2`, `0x123401A3`, `0xFFFF0000`, `0xFFFFFFFF`, and
  `0x80000001` are stored intact at slot 14 for both subtypes. With catalog
  count 418, low words 418 and 1 give three pages; 419, 0, and 65535 give one.
  Other slots and adjacent canaries remain unchanged.
- An initial invalid page count of -7 is recomputed. Current page 32767 is
  clamped to zero; current page -1 remains -1 under the original signed
  comparison. This documents native behavior, not a server-side repair rule.
- Replaying the same nonzero final-slot update preserves slot contents but
  is not side-effect-free. With suppression initially 1, subtype 4 refresh
  call totals after three updates are 0, 1, 2; subtype 5 totals are 1, 2, 3.
  A read-only instruction hook observes actual `C9170` entry, without stubs.
  The third update replaces the value, proving last-write behavior.
- Subtype 4 preserves selection and consumes suppression; subtype 5 selects
  each supplied value and preserves suppression. Neither deduplication nor
  gameplay transition semantics are added.

## Verification

From `C:/Users/risei/Desktop/God2/God2-Server`, exact command:

```powershell
python -B tests/research/test_current_quest_sync.py -v
```

Result: exit 0, `Ran 14 tests in 5.325s`, `OK`. Includes a private temporary
C++20 warnings-as-errors build, compile-time encoding assertions, standalone
decoder/encoder assertions, and pinned native dispatcher execution. The full
quest suite was run once because routing clear encoding through the new
helper introduces a regression risk to the existing clear contract.

All verification is offline: synthetic memory, closed/uncreated widget,
synthetic nonnull catalog pointer, no catalog row reads, no native client
process, no UI automation, no sockets/public connections, no transport or
live E2E claim. Runtime session gating and open-widget behavior remain untested.
C++20, Lua gameplay, and SQLite architecture are unchanged; no shared CMake,
state, summary, or build output was edited. The workspace has no Git metadata,
so no Git diff/status verification is claimed.
