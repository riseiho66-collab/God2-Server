#pragma once
#include "game/BattleNumericProfile.h"
#include <cstdint>

namespace god2 {
// CUSTOM-0016: caller supplies separately qualified amounts, never client input.
struct SupplyInput {
    std::uint64_t hp{}, max_hp{};
    std::uint32_t mp{}, max_mp{};
    std::uint64_t restore_hp{};
    std::uint32_t restore_mp{};
    BattleNumericProfile numeric_profile{BattleNumericProfile::LegacyCustom};
};
struct SupplyResult {
    std::uint64_t hp{};
    std::uint32_t mp{};
    bool consume{};
    bool operator==(const SupplyResult&) const = default;
};
}
