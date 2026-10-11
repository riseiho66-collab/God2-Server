#include "protocol/CompressionPipeline.h"
#include <stdexcept>
#include <string>

namespace god2 {
CompressionPipeline::CompressionPipeline(std::string_view mode) {
    if (mode != "none") throw std::runtime_error("Unsupported compression: " + std::string(mode));
}
std::vector<uint8_t> CompressionPipeline::compress(std::span<const uint8_t> bytes) const { return {bytes.begin(), bytes.end()}; }
std::vector<uint8_t> CompressionPipeline::decompress(std::span<const uint8_t> bytes) const { return {bytes.begin(), bytes.end()}; }
}
