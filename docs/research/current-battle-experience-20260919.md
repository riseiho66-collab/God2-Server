# Current battle experience logical codec, 2026-09-19

## Delivery

Only these four files are owned by this change:

- `src/protocol/RecoveredBattleExperience.h`
- `tests/test_recovered_battle_experience.cpp`
- `tests/research/test_current_battle_experience.py`
- `docs/research/current-battle-experience-20260919.md`

`god2::RecoveredBattleExperience` is a header-only C++20 codec for exactly one
57-byte logical record, including opcode `0x89`. `parse_logical(span)` returns
`std::optional<Record>`; `encode_logical(const Record&)` returns an owning
`std::array<std::uint8_t, 57>`. There is no transport prefix, checksum, stream
splitting, or frame adapter in this contract.

The record owns every byte and exposes only read-only, proven field accessors.
It is not default constructible; only a successful parse can construct it.
Encoding copies the retained bytes, including every opaque byte. There are no
guessed defaults, field setters, award constructors, normalization, or allocation
in the codec. Empty, truncated, oversized, concatenated, and wrong-opcode records
are rejected before any field read. Unclassified selector values and every
32-bit field pattern are accepted structurally and preserved without claiming
that every pattern is meaningful to gameplay.

Both `runtime_emission_enabled` and `runtime_mutation_enabled` are false.
These constants express scope, not a runtime security mechanism. Nothing is
registered with a sender, dispatcher, session, database, or combat implementation.
No CMake or shared runtime file was edited, and no UI or live game process ran.

## Current-only authority

The prerequisite is `tools/strike_lab/recover_monster_experience.py`, its
`tests/research/test_recover_monster_experience.py` test, and
`docs/research/monster-experience-evidence-20260919.md`. The new tests use its
pin checks, message parsing, instruction spans, and bounded Unicorn adapters.
They do not call `build_evidence`, which would open additional current tables.

Exactly two source-data files are opened by the new suite:

| Source | SHA-256 |
| --- | --- |
| `C:/Users/risei/Desktop/God2/God2-Server/artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin` | `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763` |
| `C:/Users/risei/Desktop/God2/God2/Data2/Patch/Comm/message.csvZ` | `5cd34cce66feae96d947cd45e32984765ce625673c0fb19c73cb63d7d9178598` |

The decoded message data is also checked against SHA-256
`370bd6ed9b4892f57190fc7a8dab14061b3e844b0aa9d0171611a9cbab61b5f8`.
The mapped x86 image has base VA `0x400000`; its byte offsets equal RVAs.
Pins fail closed. No retired corpus is read or used, and no historical packet
fixture is borrowed. All test records are synthetic byte/bit-pattern probes,
not recovered awards or captured battle settlements.

The existing `build_fixture` compiler adapter from
`test_current_battle_command.py` is reused solely to compile the new standalone
test in a private temporary directory. Importing its current-image VM adapter
does not run its test setup or read another data source. Unicorn is loaded from
the existing `artifacts/tooling/crypto-oracle-python` dependency directory.

## Proven fields

Offsets include the opcode. All DWORD accessors return `std::uint32_t` assembled
explicitly as little endian; no packed struct, signed cast, or alignment
assumption is used.

| Offset | Width | Codec interpretation | Independent current consumer |
| --- | ---: | --- | --- |
| 0 | 1 | Opcode `0x89` | Size table entry RVA `0x1548`, handler `0x1240` returns 57 |
| 1 | 4 | Opaque bytes | No meaning promoted |
| 5 | 4 | `character_received_exp_display()` | Load `0x118C6F`, formatter call `0x118C82`, ProgramMsg 295 |
| 9 | 4 | `companion_received_exp_display()` | Load `0x118C87`, formatter call `0x118C9A`, ProgramMsg 296 |
| 13 | 4 | `pet_received_exp_display()` | Second load in block `0x118C9F`, first numeric argument to ProgramMsg 297 |
| 17 | 32 | Opaque bytes | The consumer examines these elsewhere; no reward/item semantics promoted |
| 49 | 4 | `branch_selector()` | Original entry load `0x118BF8`, unsigned comparison with 3 at `0x118BFB` |
| 53 | 4 | `cave_received_exp_display()` | First load in block `0x118C9F`, second numeric argument to ProgramMsg 297 |

Original receive dispatch `0x1193C4` reaches `0x1195CC`; queue dispatch
`0x114332` reaches `0x114582`. Their compressed map indices are 24 and 8.
The prerequisite evidence identifies the call to consumer `0x118BF0` at
`0x114597`. These are logical receive/display facts, not an award producer.

The native binding loop `0x11125F..0x1112A5` reads IDs from `0x19BE68` and
binds ProgramMsg 295/296/297 to globals `0x5B8B50/54/58`. The suite executes
this loop using the exact current CP950 message bytes in synthetic memory.

| ProgramMsg | Physical line | Numeric format | Exact row SHA-256 including CRLF |
| --- | ---: | --- | --- |
| 295, character received EXP | 2321 | `%d` | `a8bc3ae180944ce8e660cacbd5333ce7b912d211aed7c58dcaafeb0c04717de5` |
| 296, companion received EXP | 2322 | `%d` | `a3f584300bc9a554027f65bfe331360126e3149eb34fd532db6ded0f1f90f305` |
| 297, pet/cave EXP in that order | 2323 | `%d/%d` | `f03df3b71f22a057ce3bc1f593fe08fe0a89ec732c46f1165ef1be1fa47a0afc` |

The pet/cave names describe the two positions in the paired display label;
they do not establish a split formula. Character and companion are separate
recipient displays, never base/credited stages of one award.

For example, raw bits `0x80000000` remain unsigned `2147483648` in the codec;
the current signed `%d` convention represents those bits as `-2147483648`.
Likewise `0xFFFFFFFF` remains `4294967295`, with signed presentation `-1`.
Tests model that signed interpretation explicitly and verify the original
argument bits. They stop before calling the native formatter, so they do not
claim native text rendering was executed.

## Verification and limits

Run from `C:/Users/risei/Desktop/God2/God2-Server`:

```powershell
python -B -m unittest discover -s tests/research -p test_current_battle_experience.py -v
```

Result: **7 tests passed**, exit 0, 3.344 seconds. The suite compiled the new
C++ test with MSVC, C++20, `/W4 /WX`, and ran it successfully. Compiler outputs
were confined to a temporary directory that was cleaned up.

- 32,732 C++ guard-page checks cover every contiguous subspan, lengths 58..114,
  every value at every byte offset, and rotated unsigned DWORD boundaries.
  Inputs are read-only at both page edges with inaccessible neighboring pages.
  Accepted records undergo two full byte-for-byte parse/encode roundtrips.
  A separate check proves the parsed record survives mutation of its input.
- Black-box C++ rejection checks cover all 57 truncation lengths, all 255 wrong
  opcodes, trailing bytes, a concatenated record pair, and synthetic framing.
- Eighteen distinct multi-recipient records rotate zero, one, `0x12345678`,
  `0x7FFFFFFF`, `0x80000000`, and `0xFFFFFFFF`, with three opaque poison patterns.
  Both pre-encode and post-encode records feed original native field loads;
  the exact formatter stack arguments, format pointers, slots, and C++ decoded
  values are compared, including the ordering of both ProgramMsg 297 arguments.
- Each of the 36 opaque bytes is changed independently. The entire changed
  record roundtrips, and all four original recipient loads remain unchanged.
  Memory-read hooks verify exact native DWORD reads at 5, 9, 53, then 13.
  The record ends at an unmapped-page boundary in the native VM as well.
- Eight selector values, including 3, 4 and high-bit values, are compared to
  the original entry load and distinguished from the cave field at 53.
- Original size return, both dispatch slices, message binding, exact current
  text, row offsets/hashes, and signed display interpretation are checked.

Native execution uses bounded independent instruction segments, stopping at
formatter calls. No original game instructions are patched and no helpers are
replaced. Image pages are read/execute; only the message-global data page is
made writable. This does not execute a full receive queue copy, the conditional
display path from consumer entry, UI calls, or a live battle settlement.

Unknowns remain unknown: monster identities/base EXP, generation of the received
amounts, legal award range, persistent credited XP, level-difference penalties,
party splits, multipliers, rounding, overflow policy, growth, and every player,
pet, or companion level threshold. No runtime emission or mutation follows
from accepting a structurally valid record.

## Exact registration for main

Integration follow-up: main applied the exclusion, standalone module entry and
native suite below to `tests/CMakeLists.txt`. Release build passed. CTest passed
34/34 selected tests in 13.63 seconds, including this standalone codec and its
seven-test native suite. Five pre-existing artifact/gate/environment suites were
excluded. This is build/test integration only, not runtime packet emission.

The worker did not change build files. The existing `tests/CMakeLists.txt` glob will pick
up this standalone test's `main`, so the integrator must exclude it from
`TEST_SOURCES` before `add_executable(god2-tests ...)`:

```cmake
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_recovered_battle_experience\\.cpp$")
```

Add `battle-experience` to the existing standalone module loop:

```cmake
foreach(module quest-sync battle-command character-context skill-command battle-experience)
```

The existing loop then creates `recovered-battle-experience`, includes `src`,
requires C++20, enables warnings as errors, and registers CTest
`recovered_battle_experience` with timeout 10. No `god2_core` linkage or runtime
registration is needed. To register the native suite, add the following inside
the existing `if(Python3_Interpreter_FOUND)` block, outside its pefile gate:

```cmake
add_test(NAME current_battle_experience
  COMMAND ${Python3_EXECUTABLE} -B -m unittest discover
    -s ${CMAKE_CURRENT_SOURCE_DIR}/research
    -p test_current_battle_experience.py -v)
set_tests_properties(current_battle_experience PROPERTIES TIMEOUT 120)
```

The native suite requires the two pinned current files, the existing Unicorn
dependency, and a C++20 compiler; missing prerequisites fail instead of silently
skipping evidence checks. Standalone C++ checks require only the compiler and
the new header. These CMake additions are instructions for the integrator,
not changes applied by this task.
