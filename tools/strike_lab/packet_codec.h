#pragma once
#include <array>
#include <cstdint>
#include <span>

namespace god2_probe {
inline constexpr unsigned max_frame=258;
struct DecodedPacket {
    std::array<std::uint8_t,max_frame> plain{};
    int status=0;
};
inline DecodedPacket decode(std::span<const std::uint8_t> wire,
                           std::span<const std::uint8_t> key,unsigned feedback) {
    DecodedPacket result;
    if(wire.size()<4 || wire.size()>max_frame) { result.status=-1;return result; }
    if(key.size()!=256 || feedback>255) { result.status=-2;return result; }
    const unsigned length=wire[0]+256U*wire[1];
    if(length&0x8000U) { result.status=-3;return result; }
    if(length!=wire.size()) { result.status=-4;return result; }
    result.plain[0]=wire[0];result.plain[1]=wire[1];
    auto previous=static_cast<std::uint8_t>(feedback);
    for(unsigned i=0;i<length-2;++i) {
        const auto value=static_cast<std::uint8_t>(
            static_cast<std::uint8_t>(wire[i+2]+3-previous)^key[i]);
        result.plain[i+2]=value;previous=value;
    }
    std::uint8_t checksum=0;
    for(unsigned i=0;i<length-1;++i) checksum=static_cast<std::uint8_t>(checksum+result.plain[i]+0x3c);
    if(checksum!=result.plain[length-1]) { result.status=-5;return result; }
    result.status=static_cast<int>(length);
    return result;
}
}
