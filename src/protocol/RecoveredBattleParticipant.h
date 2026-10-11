#pragma once

#include <algorithm>
#include <array>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {

// Bounded logical S2C83/subtype1 and S2C84 records. Existing-actor consumer
// evidence does not establish battle initialization or server authority.
struct RecoveredBattleParticipant {
    static constexpr std::size_t logical_size = 15;
    static constexpr bool runtime_emission_enabled = false;
    static constexpr bool runtime_mutation_enabled = false;
    using Bytes = std::array<std::uint8_t, logical_size>;

    class Record {
    public:
        std::uint8_t opcode() const noexcept { return bytes_[0]; }
        std::uint8_t position() const noexcept { return bytes_[is83() ? 2 : 5]; }
        std::uint8_t side() const noexcept { return position() / 14; }
        std::uint8_t slot() const noexcept { return position() % 14; }
        std::uint8_t marker() const noexcept { return bytes_[is83() ? 3 : 8]; }
        std::array<std::uint16_t, 2> target_masks() const noexcept {
            return {word(is83() ? 5 : 1), word(is83() ? 7 : 3)};
        }
        // Offsets include the opcode. Only demonstrated WORD/action BYTE
        // accesses are exposed; raw bits carry no inferred gameplay meaning.
        std::optional<std::uint16_t> raw_word_at(std::size_t offset) const noexcept {
            if (offset == 9 || (!is83() && (offset == 11 || offset == 13)))
                return word(offset);
            return std::nullopt;
        }
        std::optional<std::uint8_t> action_byte_at(std::size_t offset) const noexcept {
            if (is83() ? (offset == 11 || offset == 12) : (offset == 6 || offset == 7))
                return bytes_[offset];
            return std::nullopt;
        }
    private:
        friend struct RecoveredBattleParticipant;
        explicit Record(const Bytes& bytes) noexcept : bytes_(bytes) {}
        bool is83() const noexcept { return opcode() == 0x83; }
        std::uint16_t word(std::size_t offset) const noexcept {
            return static_cast<std::uint16_t>(bytes_[offset] |
                (std::uint16_t{bytes_[offset + 1]} << 8));
        }
        Bytes bytes_;
    };

    static std::optional<Record> parse_logical(std::span<const std::uint8_t> logical) noexcept {
        if (logical.size() != logical_size) return std::nullopt;
        if (logical[0] == 0x83) {
            if (logical[1] != 1 || logical[2] >= 28) return std::nullopt;
        } else if (logical[0] == 0x84) {
            if (logical[5] >= 28) return std::nullopt;
        } else {
            return std::nullopt;
        }
        Bytes bytes;
        std::copy(logical.begin(), logical.end(), bytes.begin());
        return Record(bytes);
    }
    static Bytes encode_logical(const Record& record) noexcept { return record.bytes_; }
};
}
