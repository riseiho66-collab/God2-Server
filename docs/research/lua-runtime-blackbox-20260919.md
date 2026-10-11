# Lua Runtime Black-Box Verification, 2026-09-19

## Result and scope

The complete Lua suite passes against the current C++20 LuaEngine, LuaRegistry,
and ScriptBindings sources. Added public-API regression coverage did not reproduce
a runtime defect, so production scripting code was not changed.

This is server-internal runtime verification. It establishes no original-client
packet, gameplay rule, spawn placement, reward, or combat formula. Existing runtime
limits are tested as implementation contracts, not asserted as client evidence.
No real client, desktop control, server process, shared build, shared CMake file,
or gameplay script was changed or launched.

## Changed workspace paths

- `tests/test_lua.cpp`: adds callback/registration isolation and dialogue boundary
  tests, called by the existing `test_lua()` suite.
- `docs/research/lua-runtime-blackbox-20260919.md`: this report.

Lua fixtures are written only by the test's existing temporary Fixture helper and
removed on destruction. Existing source edits were retained. The supplied server
directory has no Git metadata, so this is an explicit changed-path inventory,
not a Git-generated diff.

## Added public-API checks

- Seven failing invocations cover quest accept/complete, AI spawn/update/death,
  and ordinary-error/infinite-loop GM commands. Tests require the expected error
  diagnostic, then run all six healthy quest/AI/GM entry points and observe the
  accumulated result through NPC dialogue after each failure.
- GM player and argument tables are copied snapshots; mutation in Lua preserves
  the host values and later calls see the original arguments. UINT64_MAX remains
  the exact decimal string at the Lua boundary.
- An event registers another handler and then raises an error. Later handlers
  still run; newly registered handlers start on the next dispatch in registration
  order. This also records that callback failure does not roll back its earlier
  Lua-local or registration side effects.
- Seven invalid staged registrations cover duplicate quest/AI/GM registrations,
  missing quest callbacks, invalid AI/event callbacks, and an empty GM name.
  Every rejected load preserves the live closure state and hides the NPC
  registered earlier in that failed staging VM. Reload succeeds without retaining
  the failed entry and resets the live callback state.
- Dialogue accepts exactly 16384 text bytes, 64 options, UINT32_MAX option IDs,
  and exactly 32768 serialized JSON bytes.
- Fourteen malformed dialogue cases cover oversized text/option text, 65 options,
  32769 serialized bytes, invalid UTF-8, JSON escaping expansion, fractional/named
  option indices, zero/overflow/fractional IDs, numeric text, and metatable-only
  text/option fields. Every rejection is followed by successful healthy dialogue.
- A counter verifies that validation does not invoke the supplied `__index`
  metamethod. Embedded NUL bytes survive the player snapshot and JSON round trip.

The same run also executes all pre-existing checks: sandbox and require errors,
cyclic require, duplicate and missing registrations, thread affinity, runtime and
syntax reload rollback, directory additions/deletions, ordinary NPC failure,
infinite loops, a caught hook error, nested/shared require instruction budgets,
post-timeout recovery, and hook/extra-space restoration. The restoration check is
an existing internal unit test; the new checks use the public engine API.

## Executed verification

A private harness lives at
`C:/Users/risei/AppData/Local/Temp/god2-lua-blackbox-20260919`.
Its only manually created files are `CMakeLists.txt` and `main.cpp`. Build output
and CTest logs are confined to its `build` subdirectory. It compiles the three
current scripting translation units, the full `tests/test_lua.cpp`, and a private
Lua library from the already downloaded dependency sources. It reads dependency
headers/sources under the shared build tree without configuring or building there.
The harness uses C++20, MSVC x64 Release, Lua 5.4.8, sol2 safety checks, and spdlog
headers; it does not link the full game server.

Commands executed:

```powershell
cmake -S C:/Users/risei/AppData/Local/Temp/god2-lua-blackbox-20260919 -B C:/Users/risei/AppData/Local/Temp/god2-lua-blackbox-20260919/build -G 'Visual Studio 17 2022' -A x64
cmake --build C:/Users/risei/AppData/Local/Temp/god2-lua-blackbox-20260919/build --config Release --target lua-blackbox --parallel 2
ctest --test-dir C:/Users/risei/AppData/Local/Temp/god2-lua-blackbox-20260919/build -C Release -R '^lua$' --output-on-failure
```

Initial run: 1/1 passed, 0.22 seconds. After adding the observable metamethod
counter and explicit standard-library includes, rebuilt and reran: 1/1 passed,
0.17 seconds (0.20 seconds total). CTest enforces the existing 30-second suite
timeout. Compilation emitted the toolchain's temporary-output warning MSB8029
and dependency-header UTF-8 escape warning C5321; no compilation errors occurred.

Main coordinator's combined build target is **god2-tests**, suite **lua**.
These shared-build commands were deliberately not executed in this lane:

```powershell
cmake --build C:/Users/risei/Desktop/God2/God2-Server/build --config Release --target god2-tests
ctest --test-dir C:/Users/risei/Desktop/God2/God2-Server/build -C Release -R '^lua$' --output-on-failure
```

## Remaining boundary

This VM supports bounded accidental-loop handling, not arbitrary hostile-script
containment. Its documented limits still apply: repeated deliberate catching of
hook errors can evade termination; allocation, parsing, native calls and VM
destruction are not instruction-metered; there is no memory or wall-clock quota.
Those destructive cases were not run. The 30-second CTest timeout bounds the test
process, not production script execution.

Host-provided player names and GM argument counts/lengths have no added quotas.
Authentication/GM authorization, input admission limits, and scheduling remain
host responsibilities; this lane introduces no guessed gameplay policies.
Callback failure isolation means later calls remain usable, not transactional
rollback of arbitrary Lua mutations. Failed top-level load/reload staging does
retain the previous VM, which is separately verified.

The coordinator subsequently built the shared Release god2-tests target and
reran CTest lua successfully (0.19 seconds), alongside recovered_skill_command.
Full-server gameplay integration remains outside these public-API tests.
No client-compatible quest effects, AI movement, inventory mutation, or battle
behavior is claimed by these generic runtime callback tests.
