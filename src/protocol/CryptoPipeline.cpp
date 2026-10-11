#include "protocol/CryptoPipeline.h"
#include <stdexcept>
#include <string>

namespace god2 {
CryptoPipeline::CryptoPipeline(std::string_view mode) {
    if (mode != "none") throw std::runtime_error("Unsupported encryption: " + std::string(mode));
}
std::vector<uint8_t> CryptoPipeline::encrypt(std::span<const uint8_t> bytes) const { return {bytes.begin(), bytes.end()}; }
std::vector<uint8_t> CryptoPipeline::decrypt(std::span<const uint8_t> bytes) const { return {bytes.begin(), bytes.end()}; }
}
