#pragma once
#include <cstdint>

namespace god2 {
// CUSTOM-0021: proposed quest flow, not recovered server rules.
// Stages: 0 unstarted, 1 find Song, 2 return to Tu, 3 completed.
struct TownGuideInput {
    std::uint32_t stage{}, npc{};
};
struct TownGuidePlan {
    std::uint32_t text_key{}, confirmed_stage{}, journal_description{};
    bool requires_reward{};
    bool operator==(const TownGuidePlan&) const = default;
};
// A plan never changes state. The host must bind the pending conversation to
// its saved revision, then commit confirmation, journal and reward atomically.
}
