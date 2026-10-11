#pragma once
#include "game/ExtendedHealthAmount.h"
#include <array>
#include <cstdint>
#include <stdexcept>

namespace god2 {
struct RecoveredRoleVitals {
    // Current 69F4D -> E71E0: logical24, HP/MP/maxHP/maxMP DWORDs.
    // Unlike a display-only update, HP loss can reduce companion HP.
    static std::array<std::uint8_t,17> encode(std::uint64_t hp,std::uint32_t mp,
                                             std::uint64_t max_hp,std::uint32_t max_mp) {
        if(!max_hp || hp>max_hp || mp>max_mp)
            throw std::invalid_argument("Invalid role resource bounds");
        const auto current=ExtendedHealthAmount::from(hp),maximum=ExtendedHealthAmount::from(max_hp);
        if(!current || !maximum)throw std::invalid_argument("Unrepresentable role HP domain");
        const auto current32=current->native_unsigned_dword(),maximum32=maximum->native_unsigned_dword();
        if(!current32 || !maximum32)throw std::invalid_argument("Role HP needs a qualified extended profile");
        std::array<std::uint8_t,17> result{};result[0]=0x24;
        const std::array values{*current32,mp,*maximum32,max_mp};
        for(unsigned field=0;field<4;++field)
            for(unsigned byte=0;byte<4;++byte)
                result[1+field*4+byte]=static_cast<std::uint8_t>(values[field]>>(8*byte));
        return result;
    }
};
}
