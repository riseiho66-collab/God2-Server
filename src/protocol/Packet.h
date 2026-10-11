#pragma once
#include <cstdint>
#include <vector>

namespace god2 {
struct Packet {
    uint16_t opcode = 0;
    std::vector<uint8_t> payload;
};
}
