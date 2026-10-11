#pragma once
#include <cstdint>

namespace god2 {
// PLACEHOLDER - waiting for real GOD2 reverse engineering result.
// Little endian, length includes the four-byte header. Never serialize struct memory.
struct PacketHeader {
    uint16_t length = 0;
    uint16_t opcode = 0;
};
}
