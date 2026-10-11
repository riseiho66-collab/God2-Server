#pragma once
#include "game/BattleNumericProfile.h"
#include <cstdint>

namespace god2 {
// CUSTOM-0006: caller-selected physical/magical stats and explicit skill rules.
// No default skill IDs, monster attributes, or native formula claim.
struct CombatRuleInput {
    std::uint32_t attack, defense;
    std::uint32_t power_percent, defense_percent;
    std::uint32_t mp_cost, available_mp;
    std::uint32_t critical_chance_bp, critical_multiplier_percent, roll;
    BattleNumericProfile numeric_profile{BattleNumericProfile::LegacyCustom};
};
struct CombatRuleResult {
    std::uint64_t damage;
    std::uint32_t mp_cost;
    bool critical;
};
}
