#pragma once
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {

// Current native length RVA 1258; slot guard 98DD8; 20-byte store 98E2B.
// This logical receive contract gives no server-side construction authority.
struct RecoveredInstanceUpdate {
    static constexpr std::uint8_t opcode = 0x3b;
    static constexpr std::size_t logical_size = 25;
    static constexpr std::size_t instance_size = 20;
    static constexpr bool runtime_emission_enabled = false;
    static constexpr bool runtime_mutation_enabled = false;
    using LogicalRecord = std::array<std::uint8_t, logical_size>;

    struct DisplayCombatArguments {
        std::uint16_t physical_message_id;
        std::uint16_t magical_message_id;
        std::uint16_t physical;
        std::uint16_t magical;
    };

    struct DisplayRequirementReference {
        std::uint16_t actmis_serial;
    };

    // Parsing owns all bytes, including unclassified record bytes 1, 3 and 4.
    // No default constructor, field setters, or builder can invent an instance.
    class Record {
    public:
        std::int8_t slot() const noexcept {
            return static_cast<std::int8_t>(bytes_[2]); // Validated 0..49.
        }
        std::span<const std::uint8_t, instance_size> opaque_instance() const noexcept {
            return std::span<const std::uint8_t, logical_size>(bytes_)
                .subspan<5, instance_size>();
        }
        std::uint8_t raw_category_bits() const noexcept {
            return static_cast<std::uint8_t>(bytes_[7] & 0x3f);
        }
        std::uint16_t low_word_lookup_key() const noexcept { return u16(5); }
        std::uint16_t raw_instance_word8() const noexcept { return u16(13); }
        // Native B6424/B9F9A: category20 selects ACTMIS using instance+8.
        // This is not a mission ID or turn-in authority. Catalog bounds belong
        // to the source-qualified lookup; preserve even zero/unknown serials.
        std::optional<DisplayRequirementReference> display_requirement_reference() const noexcept {
            if (raw_category_bits() != 20) return std::nullopt;
            return DisplayRequirementReference{raw_instance_word8()};
        }
        std::uint32_t raw_packed_dword_c() const noexcept {
            return std::uint32_t{u16(17)} | (std::uint32_t{u16(19)} << 16);
        }

        // B6424 type dispatch and B45B0/B4690 arguments to B4200.
        // These are formatter inputs, not final displayed or battle values.
        // No species identity, equipment authority or stat formula is implied.
        std::optional<DisplayCombatArguments> display_combat_arguments() const noexcept {
            const auto category = raw_category_bits();
            const bool attack = category == 1 || category == 25;
            if (!attack && category != 2 && category != 26) return std::nullopt;
            return DisplayCombatArguments{
                static_cast<std::uint16_t>(attack ? 520 : 521),
                static_cast<std::uint16_t>(attack ? 522 : 523),
                static_cast<std::uint16_t>(bytes_[12] + 256u * ((bytes_[24] >> 4) & 3u)),
                static_cast<std::uint16_t>(bytes_[17] + 256u * ((bytes_[24] >> 6) & 3u))};
        }

    private:
        friend struct RecoveredInstanceUpdate;
        explicit Record(const LogicalRecord& bytes) noexcept : bytes_(bytes) {}
        std::uint16_t u16(std::size_t at) const noexcept {
            return static_cast<std::uint16_t>(std::uint16_t{bytes_[at]} |
                (std::uint16_t{bytes_[at + 1]} << 8));
        }
        LogicalRecord bytes_;
    };

    // Exact opcode-first logical record, without framing. The native signed
    // byte interval [0,50) is exactly the unsigned byte interval [0,49].
    static std::optional<Record> parse_logical(
        std::span<const std::uint8_t> logical) noexcept {
        if (logical.size() != logical_size || logical[0] != opcode || logical[2] >= 50)
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
