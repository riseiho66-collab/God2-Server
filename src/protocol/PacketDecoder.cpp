#include "protocol/PacketDecoder.h"

namespace god2 {
DecodeResult PacketDecoder::decode(Buffer& input, std::vector<Packet>& outPackets) {
    return spec_.try_decode(input, outPackets);
}
}
