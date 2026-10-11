#pragma once
#include <cstdint>
namespace god2 {
// Placeholder content model; not a recovered GOD2 item schema.
struct Item {
    std::uint64_t id = 0;
    std::uint32_t template_id = 0;
    std::uint32_t quantity = 1;
};
}
