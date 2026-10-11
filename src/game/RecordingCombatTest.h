#pragma once
#include "game/CombatRule.h"
namespace god2 {
// CUSTOM-0059 owner-requested recording fixture, never production balance.
struct RecordingCombatTest {
    static constexpr std::uint32_t hit=9999,monster_hp=99999;
    static CombatRuleResult rule(const CombatRuleInput& input) {
        // The isolated policy grants only basic/126/150. Only150 has four
        // presentation hits;126/native blade3 receives one result per target.
        const bool herd=input.power_percent==1000 && input.mp_cost==100;
        return {hit*(herd?4u:1u),input.mp_cost,false};
    }
};
}
