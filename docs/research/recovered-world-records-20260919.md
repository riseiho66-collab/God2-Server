# Current C2S World Records: Typed Transport Prerequisite

## Coordinator Integration Update

After this sidecar completed, main wired the ordered records into Session's
authenticated world-tail path and added exact native C2S86 support in
`RecoveredQuestClose.h`. Its five bytes preserve the source low word and saved
this-pointer high word from `C8350 -> C83A2 -> 132E0`. The variant now also
contains `RecoveredQuestClose::Request`; no mandatory 85/86 pairing is imposed.
See `current-quest-close-20260919.md` and `recovered-world-router-20260919.md`.

Main registered the standalone target and permanent cross-language regression
`tests/research/test_current_world_records.py`. It passes all 256 native85
tail records through the formal C++ batch decoder, rejects a truncated suffix,
and checks the four actual native action/close sequences. The two Python tests
passed in 0.271 seconds. The standalone test also checks all 65,536 selected
source/pointer-word pairs and exact five-byte86 bounds. No quest policy is
installed in Application; transport is not gameplay completion.

## Delivered scope

Two header-only C++20 codecs expose lossless, owning records from the current
client's independently grounded C2S producers. This is a typed transport
prerequisite, not original quest/gameplay implementation or live playable proof.
Only these four files are owned by this sidecar:

- `src/protocol/RecoveredQuestAction.h`
- `src/protocol/RecoveredWorldRecords.h`
- `tests/test_recovered_world_records.cpp`
- `docs/research/recovered-world-records-20260919.md`

No Session, Application, Lua, shared codec, CMake or persistence edits are made.
`RecoveredMovement` retains its public API and implementation. Session handler
integration and movement authorization belong to the coordinator's separate lane.
No descendants are used. Retired XJZ/Classic corpora supply neither authority nor
leads; historical provenance paragraphs in existing documents are excluded.

## Current authority

Current mapped image:
`artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`.
SHA256: `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
Image base is `0x400000`; addresses below are hexadecimal RVAs.

| C2S opcode | Logical bytes | Current producer and interpretation |
| --- | --- | --- |
| `2E` | 7 | `15790 -> 132E0`: two little-endian coordinate words, sequence byte, observed unwritten stack tail. Existing `RecoveredMovement::Request` is reused. |
| `30` | 2 | `11750 -> 132E0 -> 13370`: exactly `30 00`. A Tick is a record, not a count that loses ordering. |
| `25` | 5 | `96350 -> 132E0`: item word, raw slot, raw tail. Decoding delegates to `RecoveredInventoryItemRequest`. |
| `85` | 7 | `C8500 -> 97DC0 -> 132E0`: two opaque little-endian words, context byte, observed unwritten stack tail. |

These are producer-specific lengths, never entries imported from an S2C length
table. Opcode `35`, other C2S lanes and unqualified producers are not accepted.
Direction is a caller/session contract: bytes identical to a supported C2S record
cannot reveal their sender direction. Opposite-direction opcodes or competing
lengths do not gain acceptance through a shared dispatch table.

The quest source of truth is `tools/strike_lab/current_quest_action.py` and
`docs/research/current-quest-action-20260919.md`. Current movement, periodic and
inventory producer evidence is recorded in `tests/research/test_current_movement.py`,
`docs/research/current-periodic-tick-20260919.md` (current native evidence section),
and `docs/research/current-inventory-item-request-20260919.md` (current original-code
authority section). Envelope validation remains in `RecoveredWorldFrame`.

## Exact quest record

| Offset | Width | C++ field |
| --- | --- | --- |
| 0 | 1 | Opcode `85` |
| 1 | 2 | `request_word`, little endian, opaque |
| 3 | 2 | `reply_word`, little endian, opaque reply-or-choice word as received |
| 5 | 1 | `context_byte`, opaque |
| 6 | 1 | `opaque_tail`, preexisting stack byte copied by the producer |

Example current native output: `85 34 12 02 00 9a a5`. The last byte originates
at producer-entry `ESP-3`; it is not padding, quantity, a quest state or a default.
The decoder neither normalizes the reply high bit nor imports UI page/choice
gates. Every word and byte value is structurally representable, including `FFFF`;
structural acceptance does not establish reachability through every native UI path.

`encode(Request)` is diagnostic lossless reconstruction with explicitly supplied
fields. It does not invent a tail, enqueue a request or authorize gameplay.
There are no field initializers, default arguments, quest IDs, eligibility tests,
ACTMIS joins, rewards, consumption, persistence updates or inferred replies.

## Public API and atomic boundary

All types are in namespace `god2`:

```cpp
struct RecoveredQuestAction::Request {
    std::uint16_t request_word, reply_word;
    std::uint8_t context_byte, opaque_tail;
};
// RecoveredQuestAction static members:
// opcode = 0x85; logical_size = 7;
using LogicalRecord = std::array<std::uint8_t, 7>;
static std::optional<Request> decode(std::span<const std::uint8_t>) noexcept;
static constexpr LogicalRecord encode(Request) noexcept;

// RecoveredWorldRecords members:
struct Tick {};
using Record = std::variant<RecoveredMovement::Request, Tick,
                           RecoveredInventoryItemRequest::Request,
                           RecoveredQuestAction::Request>;
// max_logical_size = RecoveredWorldFrame::max_logical_size = 0xA00;
static std::optional<std::vector<Record>> decode(std::span<const std::uint8_t> logical);
static std::optional<std::vector<Record>> parse_frame(std::span<const std::uint8_t> wire);
```

`decode` requires an already validated envelope and rejects empty or oversized
logical batches. It preserves every record in encounter order, including repeated
Ticks. Unsupported opcodes, short records and nonzero tick bodies reject the whole
batch with `nullopt`; no partial output or callback is exposed. Results own all
fields and remain valid after the source buffer is changed or destroyed.

`parse_frame` first calls `RecoveredWorldFrame::decode`, which checks the exact
declared wire length, zero-seed transform/checksum and logical capacity. It then
applies the C2S grammar above. This API accepts exactly one complete frame; TCP
fragmentation/coalescing and session gates remain external. The checksum is the
existing native checksum, not cryptographic authentication.

The integration contract allows a mutually exclusive Session batch handler to
return `optional<vector<uint8_t>>`: `nullopt` rejects; an empty vector accepts
without a response. That is separate from this codec's result: an empty logical
batch is invalid. Application remains movement authority only until additional
original rules are recovered. Structural atomicity here does not replace the
caller's whole-batch authorization/transaction boundary for gameplay mutations.

## Standalone validation

Validated on 2026-09-19 using MSVC 19.44, `/std:c++20 /EHsc /W4 /WX
/permissive- /utf-8`, compiling only `tests/test_recovered_world_records.cpp`
with `src` on the include path. All assertions passed. Output/object files reside
in a private system temporary directory, outside shared build trees.

Coverage includes the native quest/tick fixtures, all 65,536 word pairs, all 256
opaque tails and context/slot/sequence bytes, all 24 record-kind permutations,
repeated records, every logical prefix (accepting only complete record boundaries),
every framed prefix, all unsupported opcode bytes, nonzero tick bodies 1..255,
competing lengths, explicit world rejection of `35`, malformed suffixes, every
even logical size through `0xA00`, the `0x9FF` boundary, complete oversized batches,
and a malformed final record at capacity. Checksum and length corruption,
extra/concatenated frames, input immutability, owning results and existing movement
API behavior are also checked. The checksum test does not claim to detect every
possible multibyte corruption.

Additional current-native validation passed:

- `python -B tests/research/test_current_quest_action.py -v`: 15/15 tests.
- 256 executions of pinned `NativeAction`, each with a different stack-tail byte,
  request word `0x1200 + tail`, incoming reply `0x8002` and context `tail ^ 0xA5`.
  The exact queued output was submitted to standalone `--quest` and `--logical`:
  512 process-level comparisons matched without normalization or byte loss.

The executable accepts `--quest HEX`, `--logical HEX` and `--frame HEX` for further
native-oracle comparisons. Successful CLI output is reconstructed logical hex;
malformed inputs fail with a nonzero exit status. Without arguments it runs all
standalone assertions. No native functions or replies are replaced by this test.

Example standalone build from the server root (PowerShell):

```powershell
Import-Module 'C:/Program Files/Microsoft Visual Studio/2022/Community/Common7/Tools/Microsoft.VisualStudio.DevShell.dll'
Enter-VsDevShell -VsInstallPath 'C:/Program Files/Microsoft Visual Studio/2022/Community' -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64'
$recordsBuild = Join-Path $env:TEMP ('god2-world-records-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $recordsBuild | Out-Null
cl /nologo /std:c++20 /EHsc /W4 /WX /permissive- /utf-8 /I src tests/test_recovered_world_records.cpp "/Fe:$recordsBuild/recovered-world-records.exe" "/Fo:$recordsBuild/recovered-world-records.obj"
if ($LASTEXITCODE -ne 0) { throw 'Compile failed' }
& "$recordsBuild/recovered-world-records.exe"
```

## Coordinator CMake handoff

The coordinator reports that Session's typed callback, integration tests and
CMake registration are now added in the main lane. Its shared build validation
remains separate from the standalone results above.

The shared test file uses `file(GLOB TEST_SOURCES ...)`. Registration requires
excluding the standalone main **before** `add_executable(god2-tests ...)`,
otherwise the glob introduces a duplicate main. Registration reference (not
applied by this sidecar):

```cmake
list(FILTER TEST_SOURCES EXCLUDE REGEX "/test_recovered_world_records\\.cpp$")
# Place the exclusion above add_executable(god2-tests ...).
add_executable(recovered-world-records test_recovered_world_records.cpp)
target_include_directories(recovered-world-records PRIVATE ${PROJECT_SOURCE_DIR}/src)
target_compile_features(recovered-world-records PRIVATE cxx_std_20)
if(MSVC)
  target_compile_options(recovered-world-records PRIVATE /W4 /WX /permissive- /utf-8)
else()
  target_compile_options(recovered-world-records PRIVATE -Wall -Wextra -Wpedantic -Werror)
endif()
add_test(NAME recovered_world_records COMMAND recovered-world-records)
set_tests_properties(recovered_world_records PROPERTIES TIMEOUT 10)
```

Original quest dispatch, request/reply/context meanings, server authorization,
acceptance/completion, item effects and live client acceptance remain unresolved.
No shared-runtime or CMake integration test is claimed by this standalone lane.
