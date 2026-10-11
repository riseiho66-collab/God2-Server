#pragma once
#include "game/BattleNumericProfile.h"
#include <cstdint>
namespace god2 {
// CUSTOM-0017: isolated first-tier rule; source text is not runtime qualification.
struct RevivalInput {
    std::uint64_t target_max_hp;
    BattleNumericProfile numeric_profile{BattleNumericProfile::LegacyCustom};
};
struct RevivalResult {
    std::uint64_t hp;
    std::uint32_t mp_cost;
    bool operator==(const RevivalResult&) const = default;
};
}
