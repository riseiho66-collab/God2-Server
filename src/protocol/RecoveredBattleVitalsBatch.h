#pragma once
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {
// Battle S2C88 -> 118A90 -> 12D360. Received current values, not base stats.
struct RecoveredBattleVitalsBatch {
    static constexpr std::size_t logical_size = 121;
    static constexpr std::size_t slots = 14;
    static constexpr bool runtime_emission_enabled = false;
    using Bytes = std::array<std::uint8_t, logical_size>;
    struct Vitals { std::uint32_t hp, mp; };
    class Record {
    public:
        std::optional<Vitals> at(std::size_t slot) const noexcept {
            if (slot >= slots) return std::nullopt;
            return Vitals{word(5 + slot * 8), word(9 + slot * 8)};
        }
    private:
        friend struct RecoveredBattleVitalsBatch;
        explicit Record(const Bytes& bytes) noexcept : bytes_(bytes) {}
        std::uint32_t word(std::size_t at) const noexcept {
            return std::uint32_t{bytes_[at]} | (std::uint32_t{bytes_[at + 1]} << 8) |
                   (std::uint32_t{bytes_[at + 2]} << 16) | (std::uint32_t{bytes_[at + 3]} << 24);
        }
        Bytes bytes_;
    };
    // Caller must establish battle direction/context and all fourteen actor
    // pointers. The native bulk writer dereferences missing slots unchecked.
    static std::optional<Record> parse_logical(std::span<const std::uint8_t> bytes) noexcept {
        if (bytes.size() != logical_size || bytes[0] != 0x88) return std::nullopt;
        Bytes owned;
        std::copy(bytes.begin(), bytes.end(), owned.begin());
        return Record(owned);
    }
    static Bytes encode_logical(const Record& record) noexcept { return record.bytes_; }
};
}
