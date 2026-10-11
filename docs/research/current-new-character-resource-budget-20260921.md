# New-character resource gap and diagnostic budgets

Native birth HP/MP and growth are still unqualified. The existing
role-growth-evidence-20260919.md records the missing causal rules; the current
RecoveredCharacterService persists the native40-byte creation profile, not
authoritative birth resources. Do not promote diagnostic HP100/MP50/max120/80
into production starting values on the strength of successful packet handling.

Targeted external searches on2026-09-21 did not yield a build-matched starting
resource formula. Portal https://xjz.17173.com/class/class.htm and the related
class/4.htm give qualitative class advice, not starting HP/MP. These pages do
not establish the current Taiwan build's numerical rules. No external values
were imported. Unrelated games/fiction search results were excluded.

## Executed Lua encounter budgets

test_combat_rule_lua.cpp now runs six bounded diagnostic encounters using the
ACTUAL scripts/gameplay/combat.lua through LuaEngine.combat_damage. This is a
sequential resource-budget simulation, not Battle transaction tests, live
client combat, normal skill-selection input or proof of native formulas.

Inputs are existing CUSTOM-0012 nonterminal fixture values from Application:
player physical/magic attack31/40 and physical defense8; enemy HP150,
physical attack20, physical/magic defense13/6; skill power150%, cost8;
no criticals. Basic damage18, skill54, retaliation12. The simulation uses
player-first turns, suppresses retaliation after a lethal hit and chooses basic
when its skill-preferring test strategy has insufficient MP. That strategy is
test policy, not an automatic server fallback or reconstructed client AI.

| Initial HP/MP | Strategy | Turns | Final HP/MP | Outcome |
| --- | --- | --- | --- | --- |
| 100/50 | Basic | 9 | 4/50 | Win |
| 100/50 | Skill preferred | 3 | 76/26 | Win |
| 76/34 | Basic | 7 | 0/34 | Loss |
| 76/34 | Skill preferred | 3 | 52/10 | Win |
| 100/7 | Skill preferred | 9 | 4/7 | Win |
| 76/0 | Skill preferred | 7 | 0/0 | Loss |

Release combat-rule-lua build and executable pass, including768 existing
formula combinations, bounds and these six budgets. Passing means regression
agreement, NOT balance approval. The fixture exhibits a narrow basic survival
margin and substantial skill advantage. No cost, stat, starting value, Lua
formula or production database was changed.

Next acceptance must include an explicit native-backed or CUSTOM starting
policy, equipment/level bands, recovery availability, critical spikes and
multi-encounter attrition with live-client completion. Do not solve the missing
starting policy by silently reusing terminal1000%-power fixtures. No new
production initial-resource design has been approved by this report.
