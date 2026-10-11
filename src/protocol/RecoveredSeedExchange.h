#pragma once
#include <algorithm>
#include <array>
#include <cstdint>
#include <span>

namespace god2 {
// Lab-only zero-seed exchange verified with the original client. No login codec.
struct RecoveredSeedExchange {
    static constexpr std::array<std::uint8_t,19> hello() {
        std::array<std::uint8_t,19> frame{};
        frame[0]=19;
        unsigned checksum=0;
        for(std::size_t i=0;i+1<frame.size();++i) checksum+=frame[i]+0x3c;
        frame.back()=static_cast<std::uint8_t>(checksum);
        return frame;
    }
    static constexpr std::array<std::uint8_t,19> response{
        0x13,0x00,0xd6,0x0e,0xa4,0x6c,0xf2,0xf0,0x80,0x1a,
        0x6e,0x13,0x4f,0x91,0x41,0x48,0x7f,0x8d,0x6e};
    static bool accepts(std::span<const std::uint8_t> wire) {
        return wire.size()==response.size() && std::equal(wire.begin(),wire.end(),response.begin());
    }
};
}
