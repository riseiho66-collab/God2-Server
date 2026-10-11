#pragma once
#include "game/ExtendedHealthAmount.h"
#include <array>
#include <cstdint>
#include <string>

namespace god2 {
struct CharacterResources {
    std::uint64_t hp, max_hp;
    std::uint32_t mp, max_mp;
    std::uint64_t revision;
    std::string design_id; // Explicit provenance; never inferred from native packets.
    bool valid_health() const noexcept {
        return max_hp && hp<=max_hp && ExtendedHealthAmount::from(hp) && ExtendedHealthAmount::from(max_hp);
    }
    // Existing legacy Battle/Supply/PK inputs need explicit admission before
    // narrowing. This is a value projection, never an owner/profile permission.
    std::optional<std::array<std::uint32_t,4>> legacy_vitals() const noexcept {
        const auto current=ExtendedHealthAmount::from(hp),maximum=ExtendedHealthAmount::from(max_hp);
        if(!current || !maximum || !max_hp || hp>max_hp || mp>max_mp)return std::nullopt;
        const auto current32=current->native_unsigned_dword(),maximum32=maximum->native_unsigned_dword();
        if(!current32 || !maximum32)return std::nullopt;
        return std::array<std::uint32_t,4>{*current32,*maximum32,mp,max_mp};
    }
    bool operator==(const CharacterResources&) const = default;
};
}
