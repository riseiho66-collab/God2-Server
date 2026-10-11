#include "core/HexDump.h"
namespace god2 {
std::string hex_dump(std::span<const std::uint8_t> bytes) {
    constexpr char digits[]="0123456789ABCDEF";
    std::string out; out.reserve(bytes.size()*3);
    for(auto b:bytes) { if(!out.empty()) out+=' '; out+=digits[b>>4]; out+=digits[b&15]; }
    return out;
}
}
