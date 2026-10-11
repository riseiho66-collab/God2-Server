#pragma once
#include <array>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {
// Current c5d8... client: 4B6426 family dispatch; 4B4690 -> 4B4200.
// Received instance tooltip operands only. These are not a generation roll,
// item admission rule, equipped-character aggregate or battle calculation.
struct RecoveredArmorInstance {
    using Instance=std::array<std::uint8_t,20>;
    struct Operands {
        std::uint16_t physical_defense{},magical_defense{},force{},constitution{},intelligence{},speed{};
        bool operator==(const Operands&) const = default;
    };
    static bool armor_family(std::span<const std::uint8_t> bytes) noexcept {
        if(bytes.size()!=20)return false;
        const auto family=bytes[2]&63u;
        return family==2 || family==26;
    }
    // The native unpack function itself has no family/owner check. Keeping that
    // distinction permits exact native vectors without admitting an inventory item.
    static std::optional<Operands> unpack(std::span<const std::uint8_t> bytes) noexcept {
        if(bytes.size()!=20)return std::nullopt;
        const auto high=bytes[19];
        return Operands{
            static_cast<std::uint16_t>(bytes[7]+256u*((high>>4)&3)),
            static_cast<std::uint16_t>(bytes[12]+256u*(high>>6)),
            static_cast<std::uint16_t>(bytes[8]+256u*(high&1)),
            static_cast<std::uint16_t>(bytes[9]+256u*((high>>1)&1)),
            static_cast<std::uint16_t>(bytes[10]+256u*((high>>2)&1)),
            static_cast<std::uint16_t>(bytes[11]+256u*((high>>3)&1))};
    }
};
}
