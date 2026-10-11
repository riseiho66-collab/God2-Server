#pragma once
#include <algorithm>
#include <array>
#include <cstdint>
#include <cstddef>
#include <optional>
#include <span>

namespace god2 {
// Current Taiwan PE S2C2C -> 004E6600 -> 004E6710. Received snapshot only.
// The native formatter transforms modifier signs using the two mask WORDs.
// Preserve the raw wire snapshot; never reserialize transformed actor memory.
struct RecoveredRoleAuxiliary {
    static constexpr std::size_t logical_size = 61;
    using Logical = std::array<std::uint8_t, logical_size>;
    static std::optional<Logical> parse(std::span<const std::uint8_t> bytes) noexcept {
        if (bytes.size() != logical_size || bytes[0] != 0x2c) return std::nullopt;
        Logical owned{};
        std::copy(bytes.begin(), bytes.end(), owned.begin());
        return owned;
    }
    static Logical encode(const Logical& record) noexcept { return record; }
    static std::uint32_t physical_attack(const Logical& record) noexcept { return dword(record,49); }
    static std::uint32_t physical_defense(const Logical& record) noexcept { return dword(record,45); }
    static std::uint32_t magical_attack(const Logical& record) noexcept { return dword(record,57); }
    static std::uint32_t magical_defense(const Logical& record) noexcept { return dword(record,53); }
private:
    static std::uint32_t dword(const Logical& bytes, std::size_t offset) noexcept {
        return std::uint32_t{bytes[offset]} | (std::uint32_t{bytes[offset+1]} << 8) |
            (std::uint32_t{bytes[offset+2]} << 16) | (std::uint32_t{bytes[offset+3]} << 24);
    }
};
}
