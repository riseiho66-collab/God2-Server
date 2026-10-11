#pragma once
#include <cstdint>
#include <span>
#include <string_view>
#include <vector>

namespace god2 {
class CompressionPipeline {
public:
    explicit CompressionPipeline(std::string_view mode = "none");
    std::vector<uint8_t> compress(std::span<const uint8_t> bytes) const;
    std::vector<uint8_t> decompress(std::span<const uint8_t> bytes) const;
};
}
