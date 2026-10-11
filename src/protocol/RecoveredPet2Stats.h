#pragma once
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {
// Native FB receiver A52A0 and original petegg.romZ control bindings.
// A received pet instance is not an authoritative wild-monster definition.
struct RecoveredPet2Stats {
    static constexpr std::uint8_t opcode = 0xfb;
    static constexpr std::size_t logical_size = 73;
    // This standalone structural codec has no authority to grant or calculate
    // pet stats. Qualified owned snapshot replay/routing is separately enabled
    // by RecoveredPet2Lifecycle + RecoveredOwnedCompanions; these flags do not
    // describe that explicitly guarded lifecycle service.
    static constexpr bool runtime_emission_enabled = false;
    static constexpr bool runtime_mutation_enabled = false;
    using LogicalRecord = std::array<std::uint8_t, logical_size>;

    struct CombatValues {
        std::uint16_t physical_attack, physical_defense, magical_attack, magical_defense;
    };
    struct Attributes {
        std::uint16_t strength, constitution, intelligence, speed;
    };
    struct Elements {
        std::uint16_t metal, wood, water, fire, earth;
    };
    struct Vitals {
        std::uint16_t current_hp, maximum_hp, current_mp, maximum_mp;
    };
    struct CategorySelector {
        std::uint8_t group, index;
        bool display_valid() const noexcept { return group >= 1 && group <= 29; }
    };
    class Record {
    public:
        std::uint16_t metadata_key() const noexcept { return word(0); }
        std::uint8_t slot() const noexcept { return bytes_[3]; }
        // Original petegg panel control5 (level), 004A4288..004A42A9.
        // Preserve the full unsigned wire byte; this does not establish a cap.
        std::uint8_t level() const noexcept { return bytes_[4]; }
        // 004A41D7..004A4283: body+4/current and body+12/maximum;
        // HP uses bits0..13, MP uses bits14..24. Bits25..31 are unrelated.
        Vitals vitals() const noexcept {
            const auto current = dword(4), maximum = dword(12);
            return {static_cast<std::uint16_t>(current & 0x3fff),
                static_cast<std::uint16_t>(maximum & 0x3fff),
                static_cast<std::uint16_t>((current >> 14) & 0x7ff),
                static_cast<std::uint16_t>((maximum >> 14) & 0x7ff)};
        }
        // Original controls17/18: 星階 / 星等. These display nibbles do
        // not establish a mapping to Bahamut 普/頂/晚破/破頂 growth types.
        std::uint8_t star_rank() const noexcept { return bytes_[12] >> 4; }
        std::uint8_t star_rating() const noexcept { return bytes_[12] & 0xf; }
        // Original 004A4525 -> 0045C9E0/0045CA00 selects the 型態 name.
        // This is not the A/B/C/D grade used by the community growth tables.
        CategorySelector category_selector() const noexcept {
            return {bytes_[0x3d], static_cast<std::uint8_t>(bytes_[0x2d] & 0xf)};
        }
        // 004A4151..004A418A: FB body+8 low 24 bits, displayed by
        // 004A42D8..004A42F3 as raw * binary32(0.01), ProgramMsg 165 (%).
        // Upper eight bits belong to two other panel fields. This is neither
        // accumulated EXP nor an authoritative next-level EXP requirement.
        std::uint32_t progress_display_raw24() const noexcept {
            return std::uint32_t{bytes_[9]} | (std::uint32_t{bytes_[10]} << 8) |
                (std::uint32_t{bytes_[11]} << 16);
        }
        CombatValues combat_values() const noexcept {
            return {word(0x10), word(0x12), word(0x14), word(0x16)};
        }
        Attributes attributes() const noexcept {
            return {word(0x24), word(0x26), word(0x28), word(0x2a)};
        }
        Elements elements() const noexcept {
            return {word(0x18), word(0x1a), word(0x1c), word(0x1e), word(0x20)};
        }
        std::span<const std::uint8_t, 72> opaque_body() const noexcept {
            return std::span<const std::uint8_t, logical_size>(bytes_).subspan<1, 72>();
        }
    private:
        friend struct RecoveredPet2Stats;
        explicit Record(const LogicalRecord& bytes) noexcept : bytes_(bytes) {}
        std::uint16_t word(std::size_t body_offset) const noexcept {
            return static_cast<std::uint16_t>(bytes_[body_offset + 1] |
                (std::uint16_t{bytes_[body_offset + 2]} << 8));
        }
        std::uint32_t dword(std::size_t body_offset) const noexcept {
            return std::uint32_t{word(body_offset)} |
                (std::uint32_t{word(body_offset + 2)} << 16);
        }
        LogicalRecord bytes_;
    };

    // Structural parsing only. The caller must separately resolve the original
    // metadata key and establish instance ownership; unknown metadata is not valid
    // merely because the native outer range accepts its integer key.
    static std::optional<Record> parse_logical(std::span<const std::uint8_t> bytes) noexcept {
        if (bytes.size() != logical_size || bytes[0] != opcode ||
            bytes[3] < 42 || bytes[3] > 44) return std::nullopt;
        const auto key = static_cast<std::uint16_t>(bytes[1] | (std::uint16_t{bytes[2]} << 8));
        if (key < 0x6d61 || key >= 0x7f58) return std::nullopt;
        LogicalRecord owned;
        std::copy(bytes.begin(), bytes.end(), owned.begin());
        return Record(owned);
    }
    static LogicalRecord encode_logical(const Record& record) noexcept { return record.bytes_; }
};
}
