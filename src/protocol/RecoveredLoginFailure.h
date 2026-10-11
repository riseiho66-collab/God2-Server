#pragma once
#include "protocol/RecoveredZeroSeedKey.h"
#include <array>
#include <cstdint>

namespace god2 {
struct RecoveredLoginFailure {
    // Native login dispatcher 0x414325 consumes opcode 0x1e plus one result
    // byte. Result 3 maps through B010's table to SystemMessage 189:
    // account/password mismatch. The client need not wait for a TCP timeout.
    static constexpr std::array<std::uint8_t,5> password_mismatch() {
        return result(3);
    }
    // B010 default branch (result > 18) selects SystemMessage 185:
    // server/network connection error, not invalid credentials.
    static constexpr std::array<std::uint8_t,5> server_error() { return result(255); }
    static constexpr std::array<std::uint8_t,5> result(std::uint8_t code) {
        std::array<std::uint8_t,5> wire{5,0,0,0,0};
        const std::array<std::uint8_t,2> payload{0x1e,code};
        const auto checksum=static_cast<std::uint8_t>(5+4*0x3c+payload[0]+payload[1]);
        std::uint8_t previous=0;
        for(std::size_t i=0;i<3;++i) {
            const auto clear=i<2?payload[i]:checksum;
            wire[i+2]=static_cast<std::uint8_t>((clear^recovered_zero_seed_key[i])+previous-3);
            previous=clear;
        }
        return wire;
    }
};
}
