#pragma once
#include "protocol/RecoveredInventoryProjection.h"
#include <cstdint>
#include <optional>

namespace god2 {
// Current client 4B6424 -> type8 table entry -> 4BA6F4..4BA763.
// Item16055 tooltip displays bits25..31 as remaining teleport uses, only1..10.
// This describes instance projection; it does not grant charges, choose a menu
// context/destination, charge money, or authorize inventory/position mutation.
struct RecoveredTeleportGem {
    using Metadata = RecoveredInventoryProjection::Metadata;
    static constexpr std::uint16_t item_id = 16055;
    static constexpr std::uint8_t instance_type = 8;
    static constexpr std::uint8_t maximum_displayed_charges = 10;

    static constexpr std::uint32_t header(const Metadata& bytes) noexcept {
        return std::uint32_t{bytes[0]} | (std::uint32_t{bytes[1]} << 8) |
            (std::uint32_t{bytes[2]} << 16) | (std::uint32_t{bytes[3]} << 24);
    }
    static constexpr bool matches(const Metadata& bytes) noexcept {
        const auto value=header(bytes);
        return (value & 0xffffu)==item_id && ((value >> 16) & 0x3fu)==instance_type;
    }
    static constexpr std::optional<std::uint8_t> displayed_charges(const Metadata& bytes) noexcept {
        if(!matches(bytes)) return std::nullopt;
        const auto count=static_cast<std::uint8_t>(header(bytes) >> 25);
        if(count==0 || count>maximum_displayed_charges) return std::nullopt;
        return count;
    }
    // Preserve every non-charge bit and every other instance byte. Zero means
    // the tooltip omits the count. Whether exhausted items are removed is a
    // separate authoritative rule; do not leave a usable zero-charge row.
    static constexpr std::optional<Metadata> with_charges(Metadata bytes,std::uint8_t count) noexcept {
        if(!matches(bytes) || count>maximum_displayed_charges) return std::nullopt;
        bytes[3]=static_cast<std::uint8_t>((bytes[3] & 1u) | (std::uint32_t{count} << 1));
        return bytes;
    }
};
}
