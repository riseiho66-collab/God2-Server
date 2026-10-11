# Recovered bounded battle participant codec

## Scope and provenance

`src/protocol/RecoveredBattleParticipant.h` adds a header-only production-library
codec following `RecoveredBattleResultFlags`. Its accepted logical records are
exactly 15 bytes: S2C `83` subtype `01`, or S2C `84`, with source position 0..27.
All other lengths, opcodes, source positions, and 83 subtypes are rejected.
In particular, subtype 3 remains outside this codec despite separate native
association-prefix evidence. These are codec bounds, not a claim that every
rejected record is rejected identically by the client.

Evidence comes from the existing
`tools/strike_lab/current_battle_participant.py` consumer and its current-image
tests, described in `current-battle-participant-20260920.md`. The original
image is pinned by the existing helper to SHA256
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
No older archive, live UI, external server, patched native instruction, or
invented callee return is used.

## Record contract

Offsets in this table are hexadecimal and include the opcode.

| Getter | 83 subtype 1 | 84 |
| --- | --- | --- |
| `opcode()` | BYTE +0 = 83 | BYTE +0 = 84 |
| `position()` | BYTE +2 | BYTE +5 |
| `side()`, `slot()` | position / 14, position % 14 | same |
| `target_masks()` | WORD +5, +7 | WORD +1, +3 |
| `marker()` | BYTE +3 | BYTE +8 |
| `raw_word_at(offset)` | WORD +9 | WORD +9, +B, +D |
| `action_byte_at(offset)` | BYTE +B, +C | BYTE +6, +7 |

WORDs are decoded little-endian. Offset getters return `std::nullopt` for
offsets outside these demonstrated sets, including out-of-range offsets.
No raw word is labeled damage or HP. Masks expose original bits; there is
no target-selection policy or normalization in the codec.

`Record` has a private constructor and owns its complete byte array.
`parse_logical` validates only the stated bounds, then copies every byte.
`encode_logical` returns an independent exact copy. In particular, 83 bytes
+4/+D/+E remain opaque, arbitrary values are accepted, and mask bits 14/15
are preserved. There are no invented padding, marker, action, metadata-key,
or raw-word constraints. No packet builder fabricates missing bytes.

Both `runtime_emission_enabled` and `runtime_mutation_enabled` remain false.
There are no Application, session, gameplay-policy, DB, allocation, or
battle-authority changes. A lossless logical codec does not prove transport
framing, initialized actors, resources, animation completion, or live success.

## Native differential validation

`tests/research/test_battle_participant_codec_validation.py` invokes the actual
C++ executable. It decodes its returned hex and feeds those returned bytes
into the unchanged original `consume` helper; it also executes the original
synthetic input with identical explicit snapshots as the reference.

The suite performs 75 paired comparisons (150 bounded native executions):

- All 28 source positions for each opcode, targeting the opposite side,
  with high mask bits set, varied markers, both source-active states, and
  nonzero opaque bytes on 83.
- Empty and high-only masks, including 83 source/target aliasing; gate reset,
  gate mismatch, and initial-phase stop boundaries for both opcodes.
- Four 83 raw WORD values: 0000, 7FFF, 8000, FFFF, continuously through the
  demonstrated actor WORD stores at +286/+288 to the formatting-call boundary.
- Both prebound 84 effect families and three 84 action-byte branches,
  including signed raw +B/+D arguments at the formatting boundaries.

Each pair compares the exact ordered native write trace (instruction RVA,
address, width, value), instruction visits, packet reads, action-manager reads,
full 0x1000-byte actor snapshots, full manager prefix, gate/output, and relevant
battle DWORDs. Continuations verify the supplied manager tail is unchanged.
Independent poisoned-actor expectations also check the demonstrated action,
ordinal, effect, and raw WORD stores. The loaded code image is compared with
the pinned original after each roundtripped run. Original packet-read guards
still reject reads beyond the supplied 15 bytes.

The original helper starts at RVA 114332 and stops before unqualified calls.
Default action stops remain 12C631/12C486. Continued cases end at the
demonstrated 147AF7 or 11DC00 call sites without executing those calls. Other
cases stop at their existing gate, phase, or assertion boundaries. No native
bootstrap or resource-production capability is added by this work.

## Integration and results

Owned files are only this document, the codec header,
`tests/test_recovered_battle_participant.cpp`, and the Python differential file.
Main owns CMake, native bootstrap, and status integration.

Requested CMake target: `recovered-battle-participant`, standalone source
`tests/test_recovered_battle_participant.cpp`, include directory `src`, C++20,
and the existing recovered-codec strict warning settings. Exclude the source
from the aggregate `god2-tests` glob. Requested CTest names are
`recovered_battle_participant` and `battle_participant_codec_validation`.
The Python suite defaults to `build/tests/Release/recovered-battle-participant.exe`;
`GOD2_BATTLE_PARTICIPANT_CODEC_TEST` can select another build's executable.

The executable runs its checks with no arguments, accepts one lowercase hex
record via `--roundtrip HEX`, and accepts newline-separated hex via `--batch`.
Accepted records print exact lowercase hex; rejected records print `reject`.
Malformed CLI hex or invalid command usage returns failure.

Validation completed before main's CMake build:

- MSVC C++20 compile with `/W4 /WX /permissive- /utf-8`: passed.
- Standalone C++ checks: passed. These include all source-byte values, all
  unsupported opcodes/subtypes, lengths 0..30, every value of every unrestricted
  byte independently, 1,024 random accepted records, offset getter bounds,
  inactive flags, and source/output ownership isolation.
- Python codec validation: 7 tests passed, including the 75 paired native cases,
  1,024 arbitrary accepted records, 1,279 rejected records, CLI roundtrips,
  and original native length lookups for both opcodes.
- Existing current participant proof: all 62 tests passed unchanged.

Main subsequently reported successful CMake configure and Release target build
with `/W4 /WX`. The Python codec suite was rerun against that CMake-built
`build/tests/Release/recovered-battle-participant.exe`: all 7 tests passed
in 6.020 seconds, including all 75 paired native comparisons. No additional
build or source change was needed for this final validation.

Commands from the server root:

```powershell
./build/tests/Release/recovered-battle-participant.exe
python -B -m unittest tests.research.test_battle_participant_codec_validation -v
python -B -m unittest tests.research.test_current_battle_participant -q
```
