#include "protocol/PacketEncoder.h"

namespace god2 {
std::vector<uint8_t> PacketEncoder::encode(const Packet& packet) { return spec_.encode(packet); }
}
