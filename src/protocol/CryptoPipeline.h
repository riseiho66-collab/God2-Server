#pragma once
#include <cstdint>
#include <span>
#include <string_view>
#include <vector>

namespace god2 {
class CryptoPipeline {
public:
    explicit CryptoPipeline(std::string_view mode = "none");
    std::vector<uint8_t> encrypt(std::span<const uint8_t> bytes) const;
    std::vector<uint8_t> decrypt(std::span<const uint8_t> bytes) const;
};
}
