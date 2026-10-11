# Regression sweep, 2026-09-21

Command: `ctest --test-dir build -C Release --output-on-failure`.
This sweep is incomplete. Of the original177 registered tests,143 completed:
141 passed and2 failed. It was deliberately stopped during
`current_battle_selector_population` (original144), after selector-windows
passed in185.64s. The remaining34 tests are not claimed passed: one interrupted,
33 not started. This was an explicit scope/time decision, not an observation
timeout, test completion, or evidence of a blocked goal.

The failures were `native_battle_transport` and `battle_transport_validation`.
Both still classified action02 as structurally unknown. Current parser support
is independently grounded by the captured revival opening02/0B batch; generic
combat authorization remains rejected outside the explicit opening policy.
Tests now recognize typed action02, preserve ordering/roundtrip checks and add
reserved-mask, target-count and truncation rejection. No production admission
rule was relaxed to make tests pass.

`current_revival_state` and `current_revival_live` were missing from CTest and
are now registered with research/revival/not-live-acceptance labels. After CMake
regeneration, all six selected tests passed in12.71s:

- battle_revival
- recovered_character_repository
- native_battle_transport
- battle_transport_validation
- current_revival_state
- current_revival_live

This does not constitute a complete179-test pass. Research boundary tests may
prove that a field/formula remains unknown; passing them does not recover that
field. Matrix generation refreshed its existing research outputs, not gameplay
data. No new fresh-client reconnect acceptance or production activation was
performed in this sweep. Revival recovery phase/lease handling remains open.
