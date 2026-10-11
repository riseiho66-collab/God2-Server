#pragma once
#include <cstdint>
#include <string>

namespace god2 {
struct Account {
    std::uint64_t id = 0;
    std::string username;
    std::string password_hash;
    std::string created_at;
};
}
