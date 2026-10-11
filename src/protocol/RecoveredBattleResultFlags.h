#pragma once

#include <algorithm>
#include <array>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {

// S2C 86/discriminator3 only. Not C2S86 dialogue close or a damage formula.
// Current 114332 -> 117480 -> 12C3E0; bounded before 126270.
struct RecoveredBattleResultFlags {
    static constexpr std::size_t logical_size = 17;
    static constexpr bool runtime_emission_enabled = false;
    static constexpr bool runtime_mutation_enabled = false;
    using Bytes = std::array<std::uint8_t, logical_size>;

    class Record {
    public:
        std::uint8_t position() const noexcept { return bytes_[2]; }
        std::uint8_t side() const noexcept { return position() / 14; }
        std::uint8_t slot() const noexcept { return position() % 14; }
        std::uint16_t raw_word() const noexcept {
            return static_cast<std::uint16_t>(bytes_[3] | (std::uint16_t{bytes_[4]} << 8));
        }
        std::uint32_t raw_flags() const noexcept {
            return std::uint32_t{bytes_[5]} | (std::uint32_t{bytes_[6]} << 8) |
                (std::uint32_t{bytes_[7]} << 16) | (std::uint32_t{bytes_[8]} << 24);
        }
        std::uint32_t normalized_flags() const noexcept {
            const auto flags = raw_flags();
            return flags & 1 ? 1 : flags;
        }
        std::span<const std::uint8_t, 8> opaque_tail() const noexcept {
            return std::span<const std::uint8_t, logical_size>(bytes_).subspan<9, 8>();
        }
    private:
        friend struct RecoveredBattleResultFlags;
        explicit Record(const Bytes& bytes) noexcept : bytes_(bytes) {}
        Bytes bytes_;
    };

    // Positions0..27 are the proved two-side helper domain, not a claim about
    // native rejection of other bytes. Preserve every accepted original byte.
    static std::optional<Record> parse_logical(std::span<const std::uint8_t> logical) noexcept {
        if (logical.size() != logical_size || logical[0] != 0x86 ||
            logical[1] != 3 || logical[2] >= 28) return std::nullopt;
        Bytes bytes;
        std::copy(logical.begin(), logical.end(), bytes.begin());
        return Record(bytes);
    }
    static Bytes encode_logical(const Record& record) noexcept { return record.bytes_; }
};
}
