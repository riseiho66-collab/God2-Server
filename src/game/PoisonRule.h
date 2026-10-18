#pragma once
#include <cstdint>
#include <optional>

namespace god2 {
// CUSTOM-0157: owner-directed current maximum HP /10, not recovered native
// tick timing, status acquisition, rounding, stacking or mutation authority.
struct PoisonShareInput {
    // Supply the actual current owned target snapshot, not initial/cast-time
    // maximum HP or current remaining HP. No client value may authorize this.
    std::uint64_t target_current_max_hp;
};
struct PoisonShareResult {
    static constexpr std::uint8_t denominator=10;
    std::uint64_t whole_hp;
    std::uint8_t remainder_tenths;
    // A quotient alone is not the damage when a fractional remainder exists.
    // Do not silently floor/ceil/min1 or accumulate it across future ticks.
    std::optional<std::uint64_t> exact_integer_hp() const noexcept {
        if(remainder_tenths!=0)return std::nullopt;
        return whole_hp;
    }
    bool operator==(const PoisonShareResult&) const=default;
};
}
