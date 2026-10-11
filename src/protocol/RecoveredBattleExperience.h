#pragma once
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {

// Current native consumer RVA 118BF0; display loads 118C6F..118CB6.
// A received display contract only, with no award or persistence authority.
struct RecoveredBattleExperience {
    static constexpr std::uint8_t opcode = 0x89;
    static constexpr std::size_t logical_size = 57;
    static constexpr bool runtime_emission_enabled = false;
    static constexpr bool runtime_mutation_enabled = false;
    using LogicalRecord = std::array<std::uint8_t, logical_size>;

    // Owning, lossless record. Only parsing can construct it: unknown bytes
    // have no defaults, and cannot be silently fabricated by an encoder.
    class Record {
    public:
        std::uint32_t character_received_exp_display() const noexcept { return u32(5); }
        std::uint32_t companion_received_exp_display() const noexcept { return u32(9); }
        std::uint32_t pet_received_exp_display() const noexcept { return u32(13); }
        std::uint32_t cave_received_exp_display() const noexcept { return u32(53); }
        std::uint32_t branch_selector() const noexcept { return u32(49); }

    private:
        friend struct RecoveredBattleExperience;
        explicit Record(const LogicalRecord& bytes) noexcept : bytes_(bytes) {}
        std::uint32_t u32(std::size_t at) const noexcept {
            return std::uint32_t{bytes_[at]} |
                (std::uint32_t{bytes_[at + 1]} << 8) |
                (std::uint32_t{bytes_[at + 2]} << 16) |
                (std::uint32_t{bytes_[at + 3]} << 24);
        }
        LogicalRecord bytes_;
    };

    // Exactly one logical record including opcode, without transport framing.
    // All DWORD bit patterns are retained, including unclassified selectors.
    static std::optional<Record> parse_logical(
        std::span<const std::uint8_t> logical) noexcept {
        if (logical.size() != logical_size || logical[0] != opcode)
            return std::nullopt;
        LogicalRecord bytes;
        std::copy(logical.begin(), logical.end(), bytes.begin());
        return Record(bytes);
    }

    static LogicalRecord encode_logical(const Record& record) noexcept {
        return record.bytes_;
    }
};
}
