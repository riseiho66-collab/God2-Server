#pragma once
#include <array>
#include <cstdint>
namespace god2 {
struct RecoveredServerList {
    // Opcode4 writes four bytes to UI entries[id]. UI requires word at entry+2 != 0.
    // Name/address come from the already loopback-restricted directory, not this packet.
    static constexpr std::array<std::uint8_t,8> one_entry() {
        constexpr std::array<std::uint8_t,5> payload{4,0,0,1,0};
        std::array<std::uint8_t,8> wire{8,0};
        std::uint8_t checksum=8+2*0x3c;
        for(auto b:payload) checksum=static_cast<std::uint8_t>(checksum+b+0x3c);
        std::uint8_t previous=0;
        for(std::size_t i=0;i<6;++i) {
            const auto clear=i<5?payload[i]:checksum;
            wire[i+2]=static_cast<std::uint8_t>(clear+previous-3);
            previous=clear;
        }
        return wire;
    }
};
}
