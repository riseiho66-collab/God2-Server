#pragma once
#include <cstdint>

namespace god2 {
inline uint16_t load_u16_le(const uint8_t* data) noexcept {
    return static_cast<uint16_t>(data[0] | (static_cast<uint16_t>(data[1]) << 8));
}
inline uint32_t load_u32_le(const uint8_t* data) noexcept {
    return static_cast<uint32_t>(data[0]) | (static_cast<uint32_t>(data[1]) << 8)
        | (static_cast<uint32_t>(data[2]) << 16) | (static_cast<uint32_t>(data[3]) << 24);
}
}
