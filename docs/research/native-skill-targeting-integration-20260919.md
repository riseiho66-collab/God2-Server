# Native Skill Targeting In The Formal Server

## Qualified Scope

`src/game/NativeSkillTargeting.h` implements the original client helper semantics
proved in `current-skill-target-setup-20260919.md`: row distance, occupancy-adjusted
range masks, all byte-mode dispatch outcomes, kind3/id8..10 pointer-word expansion,
mode17 saved-mask writes and the valid 11EAD0 setup lookup. Its authority is the
current image SHA256
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.

This is client target setup, not server cast authorization. Target masks can
include empty slots in original modes, so no additional occupancy intersection,
alive/dead interpretation, ownership, cooldown, resource, damage or hit policy is
introduced. The code does not send a packet or mutate a player/battle instance.
The structural domain remains explicit: two sides, fourteen slots each, raw
DWORD masks, optional signed WORDs and original 110-byte definitions. A supplied
null entity pointer is not an invented zero-stat entity.

The `passes_kind_gate` field reports only the kind2/WORD0FF5 branch at115571.
It is not `cast_allowed`. Modes outside1..17 reproduce the zero-mask helper
outcome and expose no subsequent setup value/flag: the real next routine enters
an unqualified diagnostic, not a successful cast. No exceptional behavior is
converted into a successful gameplay result.

## C++ And Lua

`native_skill_target_setup(kind, definition_id, actor, state)` uses the same
database-backed callback already installed by Application for the448 imported
native definitions. Definition lookup is not a caller-provided arbitrary blob.
Missing valid keys return nil; invalid inputs and inconsistent returned record
identities throw. The raw record's key is checked against the requested key.

Every caller must supply the complete state; no current battle state is guessed:

```lua
local state = {
    masks = {side0_mask, side1_mask},
    saved_masks = {saved_side0_mask, saved_side1_mask},
    entity_words = words -- Exactly 28 signed WORDs or false for null pointers.
}
local setup = native_skill_target_setup(kind, definition_id, actor, state)
```

`actor` is0..13. Arrays must have exactly the named number of integer keys;
unknown state fields, sparse arrays, numeric strings, fractional/nonfinite
numbers and out-of-range values fail before database lookup. Explicit false,
not nil/true, represents an absent pointer. Table fields are accessed raw,
without metatable lookups filling missing state. No input table is mutated.

The owning result contains masks, saved_masks, stored_mode, passes_kind_gate,
setup_valid, source provenance and record_sha256. When setup_valid is true,
setup_value and setup_flag are also present. These neutral setup values are
not damage coefficients. Lifetime/reload and game-thread rules are inherited
from the existing Lua engine; snapshots do not borrow database memory.

## Verification

- `test_native_skill_targeting.cpp`: C++ bounds, malformed definition lengths,
  row-distance extremes, empty-mask nonempty outcomes, mode17 saved state,
  invalid-mode absence and kind gate. Its --batch path calls the real header.
- `test_native_skill_targeting.py`:14 tests including13 inherited native
  regressions and4,480 additional native-versus-C++ cases. The latter cover all
  256 mode bytes across4 actor positions and3 reaches, all448 real definitions
  at actors0/13, and512 deterministic randomized special-expansion states.
  Expected masks and saved state are read from original x86 writes; valid setup
  value/flag comes from actual11EAD0 execution. Original code remains unchanged.
- `test_native_skill_lua.cpp`: malformed selectors/state rejected before the
  provider, source mismatch, nil/missing records, provider errors, no input
  mutation, binary/provenance snapshots, success/failure reloads and affinity.
- `test_native_skill_application.py`: actual Release server migration, pinned
  source import and recovered-mode startup; all448 records and896 target-setup
  queries pass through SQLite/C++/Lua with complete source comparisons. Original
  account/catalog data remains unchanged. These tests use a temporary database.

Initial targeted CTest4/4 passed; native differential14/14 passed in13.902s.
Final Release build passed, followed by selected CTest48/48 in123.62s; the five
older artifact/gate/environment suites were excluded. A subsequent synthetic
Lua case exercises signed numeric entity words and special expansion directly;
its target and the all448 Application integration were rebuilt/retested.
This does not establish live original-client world entry, a complete battle
session or any original damage/multiplier formula. No production DB is changed
by this integration; the previous448-record catalog import remains authoritative.
