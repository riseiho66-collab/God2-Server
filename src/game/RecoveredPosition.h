#pragma once
#include <cstdint>

namespace god2 {
// Server-authoritative persistence state, not a recovered wire structure.
struct RecoveredPosition {
    std::uint16_t area = 0;
    std::uint16_t scene = 0;
    std::uint16_t x = 0;
    std::uint16_t y = 0;
    std::uint64_t revision = 0;
    bool operator==(const RecoveredPosition&) const = default;
};
}
