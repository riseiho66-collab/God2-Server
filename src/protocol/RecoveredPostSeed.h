#pragma once
#include <array>
#include <cstdint>

namespace god2 {
struct RecoveredPostSeed {
    enum class State { Connected, SeedSent, SeedAccepted, PostSeedResponseSent };
    // PostSeedAccepted requires client-side evidence; the server cannot infer it from a write.
    // Runtime post-seed-contract-01: opcode 1 has length 2; expected byte is 0x53.
    // Zero-seed key[0..2] and initial feedback are zero. Header stays clear.
    static constexpr std::array<std::uint8_t,5> frame(std::uint8_t expected=0x53) {
        const std::array<std::uint8_t,2> payload{1,expected};
        std::array<std::uint8_t,5> wire{5,0,0,0,0};
        const auto checksum=static_cast<std::uint8_t>(5+4*0x3c+payload[0]+payload[1]);
        std::uint8_t previous=0;
        for(std::size_t i=0;i<3;++i) {
            const auto clear=i<2?payload[i]:checksum;
            wire[i+2]=static_cast<std::uint8_t>(clear+previous-3);
            previous=clear;
        }
        return wire;
    }
};
}
