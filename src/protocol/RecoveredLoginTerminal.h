#pragma once
#include "protocol/RecoveredZeroSeedKey.h"
#include <array>
#include <cstdint>
namespace god2 {
struct RecoveredLoginTerminal {
    static constexpr std::array<std::uint8_t,20> success() {
        std::array<std::uint8_t,20> wire{};wire[0]=20;
        const auto checksum=static_cast<std::uint8_t>(20+10+19*0x3c);
        std::uint8_t previous=0;
        for(std::size_t i=0;i<18;++i) {
            const std::uint8_t clear=i==0?10:i==17?checksum:0;
            wire[i+2]=static_cast<std::uint8_t>((clear^recovered_zero_seed_key[i])+previous-3);
            previous=clear;
        }
        return wire;
    }
};
}
