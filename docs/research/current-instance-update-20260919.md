# Current Instance Update Codec, 2026-09-19

## Scope and Authority

This deliverable adds a bounded C++20 owning codec for one exact 25-byte,
opcode-first logical `3B` record. It promotes the already established receive
layout into a lossless parser/encoder, with native differential checks at the
actual slot store. It adds no runtime registration, emission, mutation, data
defaults, or construction rule.

Read first: [goal acceptance](../GOAL_ACCEPTANCE.md),
[quest instance report](current-quest-instance-20260919.md), and
[companion instance report](current-companion-instance-20260919.md).
Those reports retain the underlying consumer interpretation and its conditions.
This work uses only their existing `current_quest_instance` and
`current_companion_instance` helpers, without new formula or display research.

Pinned original image, relative to repository root:
`artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`.
SHA-256: `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
Both helpers require this identity before executing original instructions.
All code addresses below are hexadecimal RVAs at image base `00400000`.

Exactly four owned files:

- `src/protocol/RecoveredInstanceUpdate.h`
- `tests/test_recovered_instance_update.cpp`
- `tests/research/test_current_instance_update.py`
- `docs/research/current-instance-update-20260919.md`

## Contract

`god2::RecoveredInstanceUpdate` follows `RecoveredBattleExperience`: its nested
`Record` has a private constructor and owns the complete input. Only
`parse_logical(span<const uint8_t>)` can create a record; failure returns
`nullopt`. `encode_logical(const Record&)` returns a separate 25-byte array.
Copying an already parsed record is allowed. There are no setters or builder.
Both `runtime_emission_enabled` and `runtime_mutation_enabled` are `false`.

| Logical offset | Width | Contract or read-only accessor |
| --- | --- | --- |
| 0 | 1 | Must be `3B` |
| 1 | 1 | Unclassified; preserved exactly |
| 2 | 1 | Native signed-byte slot, accepted 0..49; `slot()` returns `int8_t` |
| 3..4 | 2 | Unclassified; preserved exactly |
| 5..24 | 20 | `opaque_instance()` returns a const fixed-size span into the owned record |
| 5..6 | 2 | `low_word_lookup_key()`, little-endian raw lookup input |
| 7, bits 0..5 | 6 bits | `raw_category_bits()`, instance header bits 16..21 |
| 13..14 | 2 | `raw_instance_word8()`, little-endian instance WORD +8 |
| 17..20 | 4 | `raw_packed_dword_c()`, little-endian instance DWORD +0C |

Size is checked before any indexed read. The unsigned byte check `<50` is
exactly equivalent to the native signed-byte interval `[0,50)`: byte values
50..127 are too large, and 128..255 represent negative slots. Every other bit
pattern is accepted and retained. No alignment-dependent load or input write
occurs. The const instance span is valid only while its owning record lives.

The native length routine at `1258`, selected by `1324 + 4*3B`, returns 25.
The slot check is at `98DD8..98DE5`. `98E2B` copies five DWORDs from logical
offset 5 into `owner+85610+24*slot`; stop `98E2D` is immediately after the copy.
The codec does not expose the slot's four stride-padding bytes as packet data.

No accessor is named quest serial, Quality, or Star. The prior category-20
reader can interpret WORD +8 as an ACTMIS serial input only on its documented
category and caller path; this is not proof of serial validity or selection.
The packed DWORD's prior Quality/Star display interpretation likewise depends
on the proven companion consumer path. A raw incoming record does not certify
that path, instance eligibility, or a server-side construction rule. Raw
accessors therefore keep those contextual claims outside the codec. In
particular, a lookup key is not validated as an existing definition or item ID.

## Verification Design

The standalone C++ test has its own `main` and a `--batch` mode that invokes
the actual codec, returning encoded bytes and all scalar accessors. Python
compiles only this source into a temporary directory with C++20, optimization,
and warnings as errors. The test fails, without skipping, if compiler, pinned
image, or the existing Unicorn runtime is unavailable.

The standalone test performs **29,552 guarded checks**. Input is placed both
at the beginning and end of a read-only page between inaccessible pages. It
checks all contiguous subspans, lengths 26..50, every possible byte value at
each of the 25 positions, and all 160 individual instance bits at each of the
50 accepted slots. Accepted cases verify all accessors and two exact round
trips. Additional checks prove ownership after input changes, independent
encoder output, empty-span rejection, private construction, const instance
access, and disabled runtime flags. Checks remain active in optimized builds.

Python compares C++ results with bytes actually stored by original native code:

- All 256 slot-byte values through the quest primary dispatch and both
  companion dispatches, including every negative signed-byte representation.
- All 50 slots crossed with 36 packed-DWORD probes: zero, all ones, both
  alternating patterns, and every individual bit, including nibble boundaries.
- Header walking bits, all 64 raw categories with high header bits set,
  lookup-key boundaries, and WORD +8 walking bits and boundaries at slots 0/49.
- All 160 opaque-instance basis bits at slots 0/49, plus independent changes
  to each unclassified envelope byte through the quest helper.
- All four conditional-widget slots through both companion dispatches with
  auxiliary state 1, stopping before `961A0` at `98E05` with no store writes.
- Native length, malformed codec sizes/opcodes, image pin rejection, and
  unchanged original code bytes.

The matrix executes **7,931 bounded native dispatches**: 7,305 complete
20-byte stores, 618 slot rejections, and eight widget-call boundaries. It
compares the complete encoded logical input, complete stored instance, raw
accessor projections from the actual store, exact five-DWORD read/write
provenance, slot padding, neighbor poison, and unchanged logical input. The
companion adapter reconstructs its fixed envelope; tests assert exact equality
with the codec input before counting a differential result. Variable-envelope
probes use the quest helper, which accepts the complete logical record.

Helpers are reused without edits. The quest helper retains its 20,000-
instruction bound, exact endpoint, read-only page-end input and RX image.
The companion helper retains its instruction allowlist, 300-instruction and
one-second limits, bounded writes, exact endpoint and read-only input. DF is
explicitly clear and owner links are synthetic. All normal copy cases use
auxiliary state zero. No skipped call is replaced with a success stub.

## Reproduction and Results

From `C:/Users/risei/Desktop/God2/God2-Server`:

```powershell
python -B -m unittest discover -s tests/research -p test_current_instance_update.py -v
```

The suite uses the existing Unicorn installation under
`artifacts/tooling/crypto-oracle-python` through the companion helper. It builds
and runs the standalone guard-page executable as one of its eight tests.
Build output is confined to its automatically cleaned temporary directory.

Verified on Windows, 2026-09-19: **8 tests passed, no skips, 57.531 seconds,
exit 0**. The standalone executable compiled with MSVC C++20, `/O2 /W4 /WX
/permissive- /utf-8`, and reported `Guarded instance-update checks passed:
29552`. Both existing native helpers executed against the pinned image. No
shared CMake build, UI display chain, live client, or network was exercised.

## Exact Main-Lane Registration

No CMake or shared file is changed here. Before reconfiguring the shared test
target, the main task must exclude this standalone `main` from the existing
`TEST_SOURCES` glob in `tests/CMakeLists.txt`, before `add_executable(god2-tests ...)`:

```cmake
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_recovered_instance_update\\.cpp$")
```

Add `instance-update` to the existing standalone `foreach(module quest-sync
battle-command character-context skill-command battle-experience)` list. That
existing loop creates target `recovered-instance-update`, CTest test
`recovered_instance_update`, the src include path, C++20 mode, strict compiler
warnings and a 10-second timeout. No `god2_core` link is required.

Inside the existing `if(Python3_Interpreter_FOUND)` block, register:

```cmake
add_test(NAME current_instance_update
  COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
    -s ${CMAKE_CURRENT_SOURCE_DIR}/research -p test_current_instance_update.py -v)
set_tests_properties(current_instance_update PROPERTIES TIMEOUT 300)
```

Until the glob exclusion is made, a shared reconfigure would pick up a second
`main`. This delivery verifies the standalone sources directly; it does not
claim a shared CMake build or runtime integration.

## Remaining Boundaries

This is an exact logical-record codec and offline native store comparison.
It does not validate transport framing, decrypt input, emit a network record,
apply inventory or persistence updates, certify downstream lookup/UI success,
or establish live original-client acceptance. The native copy itself is not
an atomic length validator: the prior quest report shows truncated input can
write some DWORDs before faulting; the codec rejects incorrect length before
reading or copying any bytes.

Slots 38..41 remain structurally valid even when native widget state diverts
execution before the copy. Category-20 serial construction, packed-DWORD
construction, gameplay formulas, upgrades and normal UI reachability retain
their existing open boundaries. Original world display initialization is
owned by the main task and is outside these four files.
