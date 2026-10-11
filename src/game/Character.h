#pragma once
#include <cstdint>
#include <string>

namespace god2 {
struct Character {
    std::uint64_t id = 0;
    std::uint64_t account_id = 0;
    std::string name;
    // CUSTOM-0003: unverified skeleton defaults, not recovered starting stats.
    std::uint32_t level = 1, job = 1, hp = 100, mp = 50, map_id = 1;
    std::int32_t x = 100, y = 100;
    std::string created_at;
};
}
