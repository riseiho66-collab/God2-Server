# Skill formula evidence boundary, 2026-09-20

## Result and scope

Five new tests pass against pinned current-client bytes. The previously
static-only supplied-value linkage now has an executable regression through
`1173A0 -> 11E6E0 -> 12D970 -> 108FC0/108F50 -> 108E70`, returning normally.
Supplied actor DWORDs remain literal even when the display copy clamps them.
This establishes a consumer boundary, **not a recovered damage formula**.

Only these paths were added, relative to
`C:/Users/risei/Desktop/God2/God2-Server`:

- `tests/research/test_skill_formula_evidence_boundary.py`
- `docs/research/skill-formula-validation-20260920.md`

No runtime, CMake, status file, C++20/Lua/SQLite implementation or database was
changed. No desktop, game/server process, external server or child agent was
used. No retired archive content was opened. The existing current skill identity,
selection, target setup, recovery modules and native tests were read first.
Only `parse_skills` is reached from `recover_combat_skills`; its separate
archive-reading `build_catalog` is not called. No 4,480-target or 896-server-query
matrix was added or rerun.

## Pinned inputs

The three assets are under the current sibling client
`C:/Users/risei/Desktop/God2/God2`. The image is under the server workspace.
Every input is checked by SHA-256 before use; missing/changed inputs fail rather
than skip. Unicorn is the existing `artifacts/tooling/crypto-oracle-python`
dependency. Nothing is installed or downloaded.

| Input | SHA-256 |
| --- | --- |
| `Data2/Fight/Spg/cbspec2.bin` | `7676acd93f164d071f7681a3fe74de94d65892759dbf2e69e3c0f748423d2f51` |
| `Data2/Patch/Comm/gamedata.csvZ` | `70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731` |
| `Data2/Patch/Comm/ChangeDollEffect.csvZ` | `535a1c1a690e7f78be7d6e27cf8d212e89ed5230e5c7213c0e4fbe1d3a7d8ef1` |
| `artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin` | `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763` |

Mapped image base is `00400000`; addresses below are RVAs. Existing inventory
slice hashes also verify caller `1173A0..117472` and consumer `12D970..12D9E5`
(exclusive ends). These hashes are respectively
`6239c4b7175d313bda46166704cb7b507d3901c7d95706173cdc5b73a80daf80`
and `5d1ed07aaedeec218a3c890f68a59adf3fcf711998efbb6c3ed4d1a93546d261`.

## Concrete uncovered boundary

The prior `test_recover_combat_rules.py` executes display arithmetic and verifies
caller/consumer byte slices, but does not execute their connection. The new test
enters `1173A0` with a synthetic 13-byte buffer ending at a mapped page boundary.
It does not identify that buffer as a complete wire packet or assign an opcode.

For side zero, slot 13, with a non-null type-0 entity and actor handle zero:

| Native operation | Observed relationship |
| --- | --- |
| `1173F9`, `1173FC`, `117403`, `117404` | Loads buffer `+5/+9`; pushes `+5` before `+9` |
| `12D99C`, `12D9A5` | Actor `+DEC = buffer+9`; actor `+DF4 = buffer+5` |
| `12D9BE -> 108FC0` | Display divisors become `(actor+DF0, actor+DF4)` |
| `12D9DB -> 108F50` | Display numerators become unsigned minima of `(actor+DE8, actor+DEC)` and those divisors |

The test starts actor `+DE8=900`, `+DF0=100`. For buffer DWORDs `(+5,+9)=(5,900)`,
the four final actor DWORDs at `+DE8,+DEC,+DF0,+DF4` are `(900,900,100,5)`.
The four display DWORDs at `+A7A8,+A7AC,+A7B0,+A7B4` are `(100,5,100,5)`.
Thus display clamping does not overwrite the actor value `900` with `5`.
Neither value is labelled HP, MP, damage, hit chance or crit probability.

Five pairs cover ordinary values, zero and unsigned high-bit ordering:
`(5,900)`, `(0,1)`, `(1000,7)`, `(FFFFFFFF,80000000)` and
`(80000000,FFFFFFFF)`. Full actor/display snapshots, unchanged buffer, exact
non-stack write locations, call counts, return address and stack cleanup are
checked. Native code is read/execute only; every executed instruction must lie
inside the explicit seven function ranges. Each invocation has a 2,048-instruction
and one-second budget. No call or instruction is replaced.

Both display channel handles are signed `-1`, taking the original skip-drawing
branches. The caller's selected-position byte is `FF`, taking its original
skip-notification branch. Consequently this test executes neither pixel scaling
nor graphics; the existing display arithmetic tests cover scaling separately.
These are synthetic state choices, not claims about observed live client state.

Three early-return cases cover position 14 (side one), a null slot-13 entity,
and a negative actor display handle. The first two leave actor/display state
unchanged; the last still copies actor DWORDs but skips display updates. All
return `EAX=1`, so that return alone does not prove an actor update or cast success.

## Target values and promotion guard

One real definition is pinned independently: `(kind,id)=(0,40)`, file offset
`10CA`, length 110, record SHA-256
`fa4d53d4c8e4ef586944f64531dd09de1a57b0a494f31bb743d6105f6838ee8b`.
Its fields are `word_3e=0`, `reach_44=5`, `mode_45=14`. Executing original helper
`11EAD0` returns `EAX=7` and writes out-flag `0`, matching
`current_skill_target_setup.setup_parameters(14)`. Only that out-DWORD is written
outside the stack. This pins an opaque target setup value, not a sevenfold damage,
hit or crit modifier. The definition is not joined to a skill-book item by guess.
The existing target geometry matrices remain the coverage for target masks.

The new guard checks closed output key sets on all recovered skill descriptions,
nested description claims, card effects, selection records and native evidence.
All five rule records must retain `status=unknown`, null formula/coefficients and
`runtime_enabled=false`; server resource costs remain null. This catches new
multiplier/rate fields even when a top-level authority label is left unchanged.
Twelve negative controls modify deep copies in memory: damage/hit/crit multipliers
are injected into a nested description claim, definition `(0,40)`, display
evidence or the corresponding rule coefficients. Every injection is rejected.

This guards the recovery output contract. It does not execute C++/Lua consumers
or prove that arbitrary future runtime code cannot misuse a numeric value.
Source inspection below locates that runtime boundary without database mutation.

## Exact damage-resolution gap

- `tools/strike_lab/recover_combat_rules.py:199` classifies skill rows as
  descriptions; `:215` explicitly emits unknown server rules. The native path
  above consumes caller-supplied values. Their upstream computation and packet
  provenance are still absent from this evidence.
- `tools/strike_lab/recover_combat_skills.py:95` records description-only claims.
  `current_skill_identity` resolves record identity, and `current_skill_selection`
  changes bank state; neither supplies attack/defense arithmetic or cast authority.
- `src/game/NativeSkillTargeting.h:28` returns masks, saved masks, stored mode,
  opaque setup values and a kind gate. `:100` selects the setup pair from the mode
  table. `src/scripting/LuaEngine.cpp:213` evaluates that target result and `:214`
  builds a metadata table; there is no damage/hit/crit result in that API.
- `src/protocol/RecoveredSkillCommand.h:12` keeps runtime mutation disabled.
  `src/protocol/RecoveredWorldRecords.h:20` has no skill-command variant; its
  `:38` action parser accepts the basic/control command subset, not the separately
  recovered action `03/83` skill sequence. `src/core/Application.cpp:70` constructs
  recovered character handlers and `:106` wires movement; it does not install a
  `world_records` damage resolver. `src/net/Session.cpp:651` rejects non-movement,
  non-tick records without that callback. The battle-state gate at `:673` is not
  damage resolution. The separate fixture-style `src/handlers/BattleHandler.cpp:7`
  also remains a placeholder; it is not evidence for original gameplay.

Still required before claiming a server formula: authoritative attack/defense
inputs and their transformation, hit/evasion and crit decision rules/random
source, modifier order, element coefficients, rounding/caps/minimum damage, and
an established binding from selected skill to those computations. A display
consumer, selection flag, target distance, setup value or description percentage
does not fill those gaps. No damage formula was recovered by this deliverable.

## Actual verification

Working directory: `C:/Users/risei/Desktop/God2/God2-Server`.

```powershell
python -B -m unittest discover -s tests/research -p test_skill_formula_evidence_boundary.py -v
# Exit 0: 5 tests, 0.795s, OK; no skips.
python -B -m unittest discover -s tests/research -p test_recover_combat_rules.py -v
# Exit 0: 12 tests, 2.861s, OK; no skips.
python -B -m tools.strike_lab.recover_combat_rules --summary
# Exit 0: 381 books, 243 displayed MP costs, 1202 effects, 448 definitions,
# 9 native slices, 0 recovered server formulas; all five rules unknown.
```

Inventory checksum remains
`1036de62202d9d72f634ba49dd376a80485840b25bf1478751f15347b48de6fc`.
The existing read-only allowlist test passed, including exactly four permitted
current inputs. The new suite also runs directly with
`python -B tests/research/test_skill_formula_evidence_boundary.py -v` (the commands
above are the recorded executions). No native server build or DB-backed
application test was run. `git status --short --untracked-files=no` reported
`fatal: not a git repository`; change scope is the two explicit additions above,
not a claimed Git diff audit.
