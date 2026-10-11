# Custom Combat Rules

CUSTOM-0006 is a designed fallback, not an original GOD2 formula. It is separate
from CUSTOM-0001's fixture-only skill table and does not change that fixture.

`LuaEngine::combat_damage(CombatRuleInput)` works with fixture mode disabled.
The caller explicitly selects attack/defense (physical or magical), skill power,
defense factor, MP cost, critical chance/multiplier and a server-generated roll.
There are no default monster stats, skill identities or hidden random draws.

`scripts/gameplay/combat.lua` calculates:

```text
base = max(1, floor(attack * power_percent / 100)
              - floor(defense * defense_percent / 100))
critical = roll < critical_chance_bp
damage = critical ? floor(base * critical_multiplier_percent / 100) : base
damage = min(1000000, damage)
```

All ranges and design rationale are registered in `custom-designs.json`.
MP availability is checked before invocation. Returned MP cost must equal the
explicit cost. Results are integer/type/range checked. The existing Lua thread,
sandbox and instruction-budget handling remain in force.

This is pure evaluation, NOT skill authorization. `game/Battle` now supplies
CUSTOM-0007's C++ controller/revision/target checks and atomic action mutation.
It stages all affected HP, charges MP once per action, prepares response bytes
through a pure callback, then commits HP/MP/revision/RNG together. Encoding or
rule failure leaves the entire battle unchanged. Stats/skills remain explicit.
Client animation, battle exit packets, XP/loot, persistence, turn scheduling and
live acceptance remain unimplemented here. No Application handler or database
import is enabled by this change. Controller zero is trusted server AI; a native
network adapter must never derive this identity directly from untrusted input.

## Verification (2026-09-20)

Release build passed. CTest selection `combat_rule_lua|^lua$|fixture_|native_skill_lua|native_catalog_lua`
passed 7/7. The new suite checks 768 attack/defense/power/factor/roll combinations
against an independent integer reference, ten invalid-input conditions, guaranteed
and zero-critical boundaries, exact available-MP cost and reload behavior with
fixture mode disabled. These checks certify the custom rule only, not original
balance or native-client battle acceptance.

The subsequent CUSTOM-0007 Release build and six selected CTests passed. Its
transaction test invokes the actual non-fixture Lua rule, exercises two-target
MP charging, explicit AI retaliation, physical/magical selection, clipped lethal
hits, finished-state rejection, invalid/stale/unauthorized requests, and late
rule/encoder failures. Retrying after each failure reproduces a fresh control
battle's exact RNG draws and response bytes. Diagnostic responses use recovered
86 records and the existing envelope with explicitly synthetic opaque fields.
This is not a captured or live-accepted combat response sequence.

## Native Command Adapter

CUSTOM-0008 (`handlers/RecoveredBattleService`) now binds an existing InBattle
session to an explicit Battle, input identity mapping, basic/skill policy and
pure reply encoder. It is compatible with RecoveredWorldService's battle callback.
Parsed basic and kind-0 skill records use server-selected formula parameters;
unknown skills, mixed commands, incomplete sequences, changed actor/side/context
and changed account/character bindings are rejected. Battle owns target/life/MP
checks. Every returned envelope is validated before the transaction commit.

Release build and seven focused CTests passed. The new adapter test uses actual
command parsing, RecoveredWorldService, non-fixture Lua and Battle, covering basic
damage, two-target skill MP charging, unauthorized requests, malformed response
rollback and binding removal. Its Session socket is unconnected and replies are
synthetic vital records: no TCP or original-client acceptance is claimed here.

Application still does not install this adapter. Native turn admission/replay
checks and action/result/exit sequence remain required before activation. The
internal Battle revision is not present in these C2S records and must not be
misrepresented as network replay protection. Control0B remains rejected rather
than guessed as a turn ACK. Bind does not send bootstrap or invent a state change.

The follow-up `session_battle_service` test passed over real loopback TCP after
Release compilation. It executes synthetic login/selection/tail, then explicitly
sets a test battle binding. Partial envelope and partial skill sequence do not
mutate state; final completion produces exactly one two-target action, one MP
charge and expected native-framed diagnostic vital bytes. A corrupt checksum
closes the session without a further revision. Original-client entry/turn/result
acceptance and production Application activation remain unproven.

Owner-supplied historical balance sources and adoption rules are tracked in
`research/external-balance-references.md`. Current arithmetic tests are not a
claim that CUSTOM-0006 is already balanced against those sources.
