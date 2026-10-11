#pragma once
#include "protocol/RecoveredZeroSeedKey.h"
#include <array>
#include <cstdint>

namespace god2 {
struct RecoveredCharacterBootstrap {
    // Current 14A70/14B28 copies 124 opaque bytes. Zero fill is a lab candidate,
    // not a recovered world schema or evidence of live client acceptance.
    static std::array<std::uint8_t,128> candidate() {
        std::array<std::uint8_t,128> wire{};
        wire[0]=128;
        const auto checksum=static_cast<std::uint8_t>(128+127*0x3c+0x1f);
        std::uint8_t previous=0;
        for(std::size_t i=0;i<126;++i) {
            const std::uint8_t plain=i==0?0x1f:i==125?checksum:0;
            wire[i+2]=static_cast<std::uint8_t>((recovered_zero_seed_key[i]^plain)+previous-3);
            previous=plain;
        }
        return wire;
    }
};
}
