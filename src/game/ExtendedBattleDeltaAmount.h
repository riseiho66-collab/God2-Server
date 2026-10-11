#pragma once
#include <cstdint>
#include <limits>
#include <optional>

namespace god2 {
// Latest owner numeric extension, 2026-10-07. Exact signed64 HP-change/damage delta
// domain; no native damage formula, skill permission, settlement or wire opcode.
// Native short and authoritative extended value are separate representations.
struct ExtendedBattleDeltaAmount {
    std::int64_t value;
    std::uint64_t magnitude()const noexcept {
        // Avoid negating INT64_MIN in signed arithmetic.
        return value<0?std::uint64_t{0}-static_cast<std::uint64_t>(value):
                       static_cast<std::uint64_t>(value);
    }
    std::optional<std::int16_t> native_signed_short()const noexcept {
        if(value<std::numeric_limits<std::int16_t>::min()||
           value>std::numeric_limits<std::int16_t>::max())return std::nullopt;
        return static_cast<std::int16_t>(value);
    }
    std::optional<std::int32_t> native_signed_dword()const noexcept {
        if(value<std::numeric_limits<std::int32_t>::min()||
           value>std::numeric_limits<std::int32_t>::max())return std::nullopt;
        return static_cast<std::int32_t>(value);
    }
    bool operator==(const ExtendedBattleDeltaAmount&)const=default;
};
}
