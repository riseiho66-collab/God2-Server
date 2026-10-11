# Isolated Custom Test Combat

Authority: `CUSTOM_TEST_NOT_NATIVE`. These rules and monster stats are custom
test fixtures, NOT recovered GOD2 formulas. This TCP fixture client is NOT the
original GOD2 game client. Passing these tests does not establish native-client
combat compatibility or recovery of original damage, defense, or critical rules.

## Ownership and Isolation

- C++ owns sessions, turn validation, HP/MP mutation, RNG, and battle lifecycle.
- Lua defines the custom damage and MP-cost rules in `scripts/fixtures/combat.lua`.
- Explicit `development.fixture_battle=true` requires placeholder protocol,
  mock login, loopback binding, and a database named `fixture-combat.sqlite`.
- The supplied config uses `artifacts/fixture-combat/fixture-combat.sqlite`.
  Native catalogs and the normal database are not used as combat fixture data.
- Battle state is in memory; disconnect removes it. There are no XP, loot,
  native skill effects, or persistence claims.

## Custom Rules

Player: HP 120, MP 24, physical/magical attack 28/32, defense 8/6.
Monster: HP 100, MP 0, physical/magical attack 18/0, defense 10/8.

| Skill | Attack type | Power percent | MP cost |
| --- | --- | --- | --- |
| 1 | Physical | 100 | 0 |
| 2 | Magical | 150 | 8 |
| 3 | Physical | 200 | 20 |

Damage is `max(1, floor(attack * power / 100) - defense)`.
A roll below 1000 on the 0..9999 test roll is critical, multiplying damage by
150 percent with integer truncation. Defense is subtracted from damage; this
does not implement a defense-reduction debuff. Attacks do not miss in this fixture.

The player acts first. A surviving monster retaliates with skill 1. An accepted
turn commits MP cost, HP changes, RNG, and the next turn together. Invalid skill,
insufficient MP, stale turn/battle ID, and callback failure leave state unchanged.
Finished battles cannot accept more attacks. Flee returns the session to world state.

## Run

From the server project directory, use two terminals:

```powershell
.\build\Release\god2-server.exe --config config/fixture-combat.json
python tools/fixture_combat_client.py --port 17070 --username fixture_player
```

The fixture client supports `start`, `1`, `2`, `3`, `flee`, and `quit`.
Add `--autoplay` for an automated fight.

## Automated Acceptance

```powershell
python tools/fixture_combat_client.py --self-test --server build/Release/god2-server.exe --root .
ctest --test-dir build -C Release -R "^fixture_(battle|combat_lua|combat_tcp)$" --output-on-failure
```

The TCP self-test launches owned server processes on loopback ephemeral ports,
uses temporary databases, and stops those processes afterward. Its eight checks
cover independent logins, heavy attack, stale/insufficient-MP rejection without
mutation, victory, client isolation, flee/restart, malformed input, and disabled mode.
Domain and Lua tests additionally exercise failure rollback, critical boundaries,
loss, input bounds, script execution limits, and production-mode rejection.
