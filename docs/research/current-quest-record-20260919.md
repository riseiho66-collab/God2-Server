# Current packed quest record: bounded description references

The DB4/5 packed value now has an executable, source-backed **display**
interpretation. Low 16 bits select a one-based `Mission_data` row. High 16 bits
select a description: zero and one both select array element zero; otherwise
the index is high-word minus one. This does not establish quest acceptance,
completion, availability, rewards, NPC relationships, or a progression rule.

## Implementation and integration

`RecoveredQuestSync::descriptionReference(packedValue, descriptionCounts)` in
`src/protocol/RecoveredQuestSync.h` returns an optional `DescriptionReference`
with `missionIndex` (one-based) and `descriptionIndex` (zero-based). Supply the
counts from the matching current `Mission_data` catalog, indexed by mission ID
minus one. Empty/out-of-range mission references, zero description counts,
out-of-range description selectors, catalog lengths over 32767, and selected
row counts over 32767 return nullopt. The latter two checks bound the native
signed-word domain; they are not a claim that the native consumer is safe for
malformed catalogs.

This is an opt-in display-state validator. The existing raw decoder and encoder
still accept and retain all packed bits. Nullopt means no bounded description
reference, not an invalid or completed gameplay quest. In particular, packed
values `0x00000001` and `0x00010001` must remain distinct even though they both
display the first description. The helper neither normalizes them nor emits
an inferred state transition.

Changes are limited to:

- `src/protocol/RecoveredQuestSync.h`: bounded description resolver.
- `tests/test_recovered_quest_sync.cpp`: compile-time checks and batch fixture
  mode `--descriptions`, returning the reference plus a verbatim-value DB4 record.
- `tests/research/test_current_quest_record.py`: new pinned native comparisons.
- This document.

No shared registration was edited. Main can register
`python -B tests/research/test_current_quest_record.py -v` as an offline research
check. It builds the existing quest-only C++ fixture in `artifacts/quest-record`
with C++20 and warnings as errors. The existing CMake quest target already
compiles this fixture. Runtime use requires the matching catalog plus existing
World/session and authoritative-state gates; this lane enables no packet sends.

## Evidence searched first

Both existing legacy corpora were searched for mission/step, packed word and
consumer references before implementing the new behavior:

- Classic root:
  `C:/God2Evidence/classic-20260820/files/God2-Classic-Server-Formal-Handoff-20260820-020345/ServerSource`.
  `src/God2.ClassicServer.Protocol/OfficialMissionSlotSyncWire.cs` was read;
  SHA-256 `869fa1db13feea2d34278fac113985f19ca070ea1b7b61c234fd805a4d38291b`.
  It explicitly identifies a different three-byte DF build contract. Runtime
  objective handlers and imported mission-step material do not prove the
  current DB packed-word meaning.
- XJZ root:
  `artifacts/legacy-evidence/xjz-20260820/files/XJZ-Server-Cpp/server_implementation`.
  `evidence-quest-service-template-v0.md` was read;
  SHA-256 `6a81782ed8d137de13c08ce10b16793c8b757e81377cbe633ad401f5c6d697ff`.
  Its inferred names and reconstructed step/requirement relationships were not
  adopted. No authoritative reward rows or current packed-word rule were found
  in these searched references.

The three requested current quest documents, extractor, C++ codec/fixture,
and existing native quest harness were read. Previous tests stop at a closed
journal, without loading description arrays. This extension executes those
arrays' original consumers instead of repeating that closed-widget proof.

## Current source bytes

Mapped original x86 image, base `0x400000`, file offsets equal RVAs:
`artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`.
SHA-256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.

Current source: `../God2/Data2/Patch/Comm/Mission_data.csvZ`.
Source SHA-256 `659c8f38ffd9c34107969b449afd16488665a08970110910c9aed8448a0bb716`;
decoded SHA-256 `f57cb8d1a9426e2f797c9cdfea32beb07642415ae3e2bb30a8909373a1c0a5f0`.
The tests verify both and use the existing byte-preserving extractor. All 418
IDs are contiguous; all 2014 description rows have sequential STEP labels in
file order. Actual counts range from 1 through 29.

Examples, physical decoded lines and raw field hex:

- Line 4: ID `31`, name `5babb0c2eda5f4b0c85dabb0c2edc251bec9`, count `32`:
  mission 1 with two descriptions. Line 6 (second description) is
  `a662a7e4a8eca7bad649b6eeabe1a141b8d3a65ea568a7e4d25cbfcdb97c283131302f31313029a5e6ae74a446a149`.
- Line 2427: ID `343138`, name
  `5ba544bd75a5f4b0c85d20acc9adadb8d1b0a34949`, count `38`: mission 418,
  eight descriptions beginning at line 2428.

The names and descriptions remain original bytes; tests do not derive gameplay
meaning from their displayed language.

## Original instructions

| RVA | Exact bytes | Behavior |
| --- | --- | --- |
| `584AE` | `0fbfb42424100000` | Loader uses signed-word catalog count. |
| `584F1` | `8bd84b` | Parsed mission ID becomes zero-based row index. |
| `58533..58536` | `8d1c9bc1e303` | Row stride is 40 bytes. |
| `58575` | `66893c19` | Parsed STEP count stored as row's first word. |
| `58594` | `89441a24` | Description pointer-array address stored at row +36. |
| `585F6` | `8904b2` | Text pointer stored by sequential ESI read index. |
| `C9581` | `8b84be04210c00` | Reads full packed value from selected journal slot. |
| `C958A` | `81e1ffff0000c1e810740148` | Low word selects mission; high word decremented only if nonzero. |
| `C95AB..C95B3` | `3bd35b7f3b6685c97636` | Rejects mission above catalog count or zero. |
| `C95BE` | `8d4cd1d8` | Catalog address = base + 40 * (mission - 1). |
| `C95C6` | `0fbf113bc2731e` | Sign-extended description count, unsigned index comparison. |
| `C95D7` | `8b1481` | Reads actual description pointer at index *4. |
| `C95E1` | `e89a5f0400` | Passes pointer to original text renderer `10F580`. |
| `C95F2` | `6840465b00` | Invalid reference passes the empty string at RVA `1B4640`. |
| `C9304` | `25ffff0000c1e910740149` | Click consumer has the same split and zero/one alias. |
| `C933F` | `0fbf103bca7325` | Click consumer uses the same description bound. |
| `C9346` | `89beb82e2300` | Only a valid clicked reference updates selected packed value. |
| `C9356` | `8b0c88` | Click consumer reads selected description pointer. |

The loader parses a description STEP field and checks it, but stores using
sequential ESI at `585F6`; the test verifies current file order before building
the synthetic resource arrays. No hypothetical reordered catalog is treated as
proven. `Mission_data` dispatch to `584A0` and DB dispatch/storage at
`6B44E -> 854F0 -> C9670` are established in the preceding protocol document.

## Native verification

Executed from the server root on 2026-09-19:
`python -B tests/research/test_current_quest_record.py -v`.
Result: exit 0, `Ran 5 tests in 58.345s`, `OK`, including the standalone
C++20 warnings-as-errors build and the existing C++ fixture assertions.

New tests compile the C++ helper, then use its emitted DB4 bytes through the
real `68B61` dispatcher to `6B517`. The journal writer completes with balanced
stack. They then invoke original `C9550` from its entry, including its original
`10D310` list-selection helper, and stop at `10F580` before rendering. Synthetic
list entries are null, so the helper takes its normal no-selection path. No
instructions are patched and there are no stubs. Resource pointer arrays and
text bytes are read-only. Native pointer reads and renderer arguments are
observed, not substituted.

The staged lookup comparison covers 2855 packed values: every current description,
the zero selector and first out-of-range selector for each of 418 missions,
plus five mission/high-word boundary cases. Every valid renderer pointer must
reference exactly the expected staged text bytes. This historical test did not
execute the source loader and therefore did not establish that the staged
strings were its actual output. Every invalid case must
select the native empty string without reading a description-array pointer.
Raw packet values remain intact after the original consumer executes.

2026-09-27 correction: the full `4584A0` parser now executes against all418
definitions/2014 descriptions. Two source strings are truncated by the native
field tokenizer: mission60 description index9, 416 ->379 bytes; mission168
index2, 380 ->379. The raw source remains preserved in the formal catalog.
`test_current_quest_record.py` now stages actual parser output before testing
the journal consumers and adds both long-string DB4/5 cases. See
`current-quest-rule-frontier-20260927.md` for parser scope and source receipts.
This correction supplies no quest transition or reward authority.

The independent click slice runs `C92EA` through the renderer call with prepared
page/click registers for both DB4 and DB5 emitted records. It verifies first,
second, overflow and high-bit selectors, including mission 418's last
description. A valid reference writes the original packed value to selection;
an invalid one preserves the prior selection. Input dispatch and actual mouse
or window behavior are not claimed.

A malformed-catalog probe sets count word `0xFFFF` and puts the pointer array
at a mapped-page boundary. For selector 2, `C95C6` sign-extends the count to
`0xFFFFFFFF`; the unsigned branch accepts index 1, and `C95D7` faults on an
unmapped pointer read. The C++ validator rejects counts 0, `0x8000`, and
`0xFFFF` without losing the raw DB record. Tests also exercise the signed-word
catalog/count boundary 32767/32768. These synthetic cases describe parser
safety, not actual source catalog rows.

Execution is entirely offline. No client/server process, UI session, socket,
shared runtime, network, world, CMake, Lua or database changes were made. The
workspace has no Git metadata; no Git diff claim is made.

## Remaining unknowns

The upper word is proven to select presentation text in these two consumers;
its server-side update conditions remain unknown. Zero is not proven to mean
unaccepted, and a selector beyond the description count is not proven to mean
complete. Acceptance, completion, rewards, quest availability, ACTMIS/daily
joins, NPC links, persistence, and authoritative initial state remain unknown.
No full renderer, open-window flow or live end-to-end behavior was executed.
