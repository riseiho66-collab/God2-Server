#pragma once
#include <cstdint>
#include <vector>

namespace god2 {
// CUSTOM-0013: explicit cumulative thresholds, never native table defaults.
struct ProgressionInput {
    std::uint64_t total_experience{};
    std::vector<std::uint64_t> cumulative_thresholds;
    std::uint16_t unlocked_level{};
};
struct ProgressionResult {
    std::uint16_t level{}, progress_display{};
    bool operator==(const ProgressionResult&) const = default;
};
}
