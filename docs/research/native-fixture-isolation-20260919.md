# Native Fixture Isolation, 2026-09-19

## Runtime policy

`Application.cpp` derives `fixture_mode` from
`config.protocol_mode == ProtocolMode::Fixture`. It passes that setting to
`LuaEngine` and initializes the mock `World` map 1 only in fixture mode. Every
recovered protocol mode, including the dual-connection application's character
listener, therefore starts without that mock map or the bundled sample hooks.

`LuaEngine` retains one constructor setting and publishes `GOD2_FIXTURE_MODE`
before scripts execute. Both initialization and every staged rebuild use the
same setting, including hot reload and transactional script loads. The existing
one-argument constructor defaults to fixture behavior for standalone fixture
callers, including the PLACEHOLDER network tests. Game-thread ownership, copied
Lua snapshots, instruction budgets and failed-reload rollback are unchanged.

The bundled `bootstrap.lua` loads `fixture_bootstrap.lua` only in fixture mode.
The latter also checks the flag and contains the existing NPC 1001, quest 2001,
AI 3001, sample lifecycle events and GM command imports, plus the previous
bootstrap's `server_start` event. No gameplay data or formulas were invented.

## Caller review and boundaries

`Config::load` still resolves the configured script root and bootstrap path.
`Application.cpp` still calls `load_script(config.bootstrap)` without replacing
custom paths. Custom scripts can inspect the runtime flag and register their own
hooks, including in recovered mode. This flag selects bundled content; it is
not a security restriction on arbitrary custom scripts. Explicit custom imports
of individual example modules, or an explicit `load_directory` over all scripts,
can still load those modules. The application uses neither mechanism.

`Session::Impl::read` processes recovered input through its recovered branch.
`Session::Impl::enqueue` already refuses fixture packets in recovered modes.
Recovered authentication, character services, world-entry callbacks, movement
binding and network framing do not require mock `World::initialize`. Their
registration, execution and teardown paths have not been changed. The empty
World remains available for the existing handler context and disconnect code.

The existing `RecoveredWorldStateCandidate::wire()` call in
`Session::Impl::accept_world_tail` still sends the historical scalar bootstrap
after the validated initialization tail. Its `2B / 2C / 24 / 39 / 22` prefix is
an unverified historical replay, not established selected-character attributes
or proven causal request replies. The warning in `Application.cpp` remains.
This change neither removes that frame nor promotes its scalars into gameplay
rules. See `current-world-scalar-bootstrap-20260919.md` for evidence and limits.

## Changed files

- `src/core/Application.cpp`: pass runtime policy and gate mock map initialization.
- `src/scripting/LuaEngine.h` and `.cpp`: retain the flag across VM construction.
- `scripts/bootstrap.lua`: select the bundled fixture entry by runtime flag.
- `scripts/fixture_bootstrap.lua`: retain the original sample imports and event.
- `tests/test_lua.cpp`: recovered, fixture, reload and custom-bootstrap regression checks.
- This report only; no shared documentation or CMake changes.

## Verification

Release build passed:

```text
cmake --build build --config Release --target god2-server god2-tests -j 2
```

All six selected CTest suites passed:

```text
ctest --test-dir build -C Release -R "^(lua|config|network|decoder|session_state|protocol_replay)$" --output-on-failure
```

The Lua tests load the actual default recovered-seed configuration and bootstrap,
then verify absence of example NPC, quest, AI and GM registrations before and
after reload. Missing callbacks must report unavailable registrations, not merely
throw from a registered callback. The custom-bootstrap test loads both bundled
entries with no sample modules present, retains its own NPC and lifecycle event,
checks the recovered flag on reload, and verifies rollback after a failed reload.
Existing example tests continue to exercise all fixture hooks, with explicit NPC,
quest, AI and GM assertions after reload.

The network suite exercises the existing PLACEHOLDER loopback workflow with an
in-memory database. No existing database or client was modified, and no live
client or recovered world end-to-end session was launched. Mock map gating was
reviewed in the application source and compiled; these Lua tests do not inspect
the application's World instance. No historical-scalar validity claim follows
from these tests. Subagent tools were unavailable in this session.
