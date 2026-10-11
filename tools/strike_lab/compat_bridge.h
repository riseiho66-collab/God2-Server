#pragma once
#include <array>
#include <cstdint>
#include <cstring>

inline std::array<unsigned char,8> god2TimerBridge(std::uint32_t address,std::uint32_t target) {
    std::array<unsigned char,8> code{0x83,0xec,0x00,0xe9,0,0,0,0};
    const std::uint32_t relative=target-address-static_cast<std::uint32_t>(code.size());
    std::memcpy(code.data()+4,&relative,4);
    return code;
}
