#pragma once
#include <cstdint>
#include <optional>

namespace god2 {
// CUSTOM-0157: owner-directed floor(current maximum HP /10). This is not
// recovered native tick timing, status acquisition, stacking or mutation authority.
struct PoisonShareInput {
    // Supply the actual current owned target snapshot, not initial/cast-time
    // maximum HP or current remaining HP. No client value may authorize this.
    std::uint64_t target_current_max_hp;
};
struct PoisonShareResult {
    static constexpr std::uint8_t denominator=10;
    std::uint64_t whole_hp;
    std::uint8_t remainder_tenths;
    // Owner clarification: discard the fractional part; 123 maximum HP costs
    // 12 HP. A maximum below10 therefore costs0, without an invented minimum.
    std::uint64_t damage_hp() const noexcept {return whole_hp;}
    // Exact mathematical divisibility is diagnostic only. The remainder is
    // never carried into another tick; damage uses damage_hp() above.
    std::optional<std::uint64_t> exact_integer_hp() const noexcept {
        if(remainder_tenths!=0)return std::nullopt;
        return whole_hp;
    }
    bool operator==(const PoisonShareResult&) const=default;
};
}
