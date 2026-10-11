#pragma once
#include "protocol/ProtocolSpec.h"

namespace god2 {
class PacketEncoder {
public:
    explicit PacketEncoder(ProtocolSpec& spec) : spec_(spec) {}
    std::vector<uint8_t> encode(const Packet& packet);
private:
    ProtocolSpec& spec_;
};
}
