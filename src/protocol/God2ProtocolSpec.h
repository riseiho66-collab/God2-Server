#pragma once
#include "protocol/ProtocolSpec.h"
#include "protocol/CryptoPipeline.h"
#include "protocol/CompressionPipeline.h"

namespace god2 {
// PLACEHOLDER - waiting for real GOD2 reverse engineering result.
class God2ProtocolSpec final : public ProtocolSpec {
public:
    explicit God2ProtocolSpec(size_t max_packet_size = 65535,
        std::string_view encryption = "none", std::string_view compression = "none");
    size_t header_size() const override { return 4; }
    DecodeResult try_decode(Buffer& input, std::vector<Packet>& outPackets) override;
    std::vector<uint8_t> encode(const Packet& packet) override;
private:
    size_t max_packet_size_;
    CryptoPipeline crypto_;
    CompressionPipeline compression_;
};
}
