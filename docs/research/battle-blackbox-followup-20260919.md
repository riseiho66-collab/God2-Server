# Battle request black-box follow-up, 2026-09-19

## Result and scope

Added bounded, native-seeded memory-safety and state-guard ordering verification
for the existing basic-attack request contract. No production parser defect was
demonstrated, so `src/protocol/RecoveredBattleCommand.h` is unchanged and
`runtime_mutation_enabled` remains false. No new protocol semantics, combat
formulas, rewards, gameplay mutation or state authorization were introduced.
C++20 core, Lua gameplay and SQLite ownership are unchanged.

Changed only:

- `tests/test_recovered_battle_command.cpp`
- `tests/research/test_current_battle_command.py`
- `docs/research/battle-blackbox-followup-20260919.md`

No skill, shared build/CMake, runtime, state or integration-summary files were
edited. The existing Python fixture built the C++ executable and object in its
private `god2-battle-test-*` temporary directory. Python ran with `-B` to suppress
bytecode writes.

## Evidence consulted

Read `gameplay-lanes-20260919.md`, `current-battle-command-20260919.md`,
`current-skill-command-20260919.md` and their relevant tests before editing.
Existing battle tests cover ordinary prefix truncation and selected malformed
fields; the skill guard-page suite does not call the basic-attack parser. The
new risks are actual inaccessible-page boundaries, cross-group cardinality
interactions and dereference ordering with an unreadable native target pointer.

Both legacy sources were consulted directly:

- XJZ: `artifacts/legacy-evidence/xjz-20260820/files/XJZ-Server-Cpp/server_implementation/cpp/xjz_combat_command_contracts.hpp`,
  SHA-256 `e25f8c5b8e89e6207b0185b640c6e5afd9b70a83251024813820695f26729ea3`.
  Its semantic session/actor service interfaces do not prove current wire state.
- Classic root:
  `C:/God2Evidence/classic-20260820/files/God2-Classic-Server-Formal-Handoff-20260820-020345/ServerSource/src/God2.ClassicServer.Protocol/`.
  Read `OfficialBattleCommandWire.cs`, SHA-256
  `06e147cac8ac7aed5df46fdbddd7cd114f0bccd13e2e9f22b11e6f86be4549c5`, and
  `PublicBetaCompatibilityBattleWireAdapter.cs`, SHA-256
  `764a29843fcdf884ede6eab9a1b3fe75527b52530dd22cdcf8d08c39bb6c00c3`.
  Its different-image Battle-state gate, third-mask interpretation and
  missing-target rejection are not copied into this current structural parser.

Current authority is the original native image at
`artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin`,
SHA-256 `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
The suite checks the complete image hash before executing RVA `0x118E50` through
`0x1191EE`, or the original early return. Real lookups and queue copier execute;
no code bytes or native callees are replaced.

## Added checks

The C++ fixture exposes `--guard-batch`, taking stdin lines containing an
acceptance flag and a hex record. Each candidate is copied first against the
leading guard and then against the trailing guard of an OS memory allocation.
Both outer pages are inaccessible, and the middle page is read-only during
parsing. Protection failures fail the test; a memory violation fails the child
process. Empty input is also placed directly at an inaccessible page, and a
default empty span is checked separately. Accepted fields are serialized by the
test and compared byte-for-byte with the input, including both opaque DWORDs
and the unwritten byte.

The external Python corpus has 26,623 candidates / 53,246 guarded parser calls:

- 15 original-builder seeds cover every split of fourteen distinct targets
  between the two groups, alternating side, context and stack poison.
- All 171 byte subspans of a native 17-byte seed, including empty spans, plus
  34 oversized lengths from 18 through 51 bytes, exercise physical span edges.
- All 256 substitutions at each of 17 offsets check field bounds and preserve
  opaque bytes. These 4,352 cases include all actor, side and action byte values.
- All 15 x 15 target-count pairs, rotated through 14 positions, cover totals
  0..28 and the 13/14/15 boundary across both masks. Expected acceptance uses
  the lengths of constructed target lists, not the C++ popcount expression.
  Each of the 3,150 base cases has six reserved-bit variants, producing 22,050
  mask cases. The mutations include unaligned byte/WORD boundaries.
- One final valid seed checks acceptance after the mixed corpus in the same
  process. Each accepted result must preserve every byte.

The native state test unmaps the target page at original function entry, after
the existing fixture has finished setting up memory:

- Counts 15 and INT_MAX, actor low bytes 15 and 255, inactive state and both
  modes zero return without target reads or queue calls; stack cleanup matches
  the original return convention.
- Counts INT_MIN, -1 and zero produce valid empty-mask records without target
  reads. Nonzero high-bit active/mode DWORDs and connected byte 255 exercise
  the native nonzero predicates; the context DWORD remains opaque and intact.
- Positive controls with count one fault with `UC_ERR_READ_UNMAPPED` for both
  connected and disconnected state. This confirms the fixture is effective
  and that disconnection gates queueing after target dereference; it is not an
  earlier pointer-validation guard. The faults occur inside Unicorn only.

These client memory predicates do not establish a server battle session,
participant ownership, turn permission, valid target existence or replay policy.
The parser has no authoritative-state input, so no guessed state checks were
added. Context aliasing remains indistinguishable from an ordinary opaque
context value, as documented in the original battle contract.

## Exact verification

Working directory: `C:/Users/risei/Desktop/God2/God2-Server`.

```text
python -B tests/research/test_current_battle_command.py -v CurrentBattleCommandTests.test_native_guards_and_signed_count_before_target_pointer_read CurrentBattleCommandTests.test_cpp_guarded_native_seed_mutations_and_combined_mask_limit
```

Result: exit 0; both new tests passed in 3.342 seconds. Output:

```text
Ran 2 tests in 3.342s
OK
Battle guard corpus: 26623 candidates, 53246 checks
```

The fixture compiled with MSVC `/std:c++20 /EHsc /W4 /WX` in the private
temporary directory; its existing C++ assertions also run before each command.
Only the two new Python tests were selected. The previously covered six battle
tests, skill suite, shared build and full CTest were not rerun.

This is offline original-code emulation plus a standalone C++ process, not live
client/server E2E or rendered gameplay acceptance. No UI automation, native
client launch, sockets or public connections were used. The Windows guard-page
implementation was executed; the analogous POSIX path was not executed. This
bounded corpus does not prove all possible byte strings or authorize combat.
