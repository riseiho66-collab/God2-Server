#pragma once
#include "protocol/ProtocolSpec.h"

namespace god2 {
class PacketDecoder {
public:
    explicit PacketDecoder(ProtocolSpec& spec) : spec_(spec) {}
    DecodeResult decode(Buffer& input, std::vector<Packet>& outPackets);
private:
    ProtocolSpec& spec_;
};
}
