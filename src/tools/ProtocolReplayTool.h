#pragma once
#include "protocol/PacketDecoder.h"
#include <iosfwd>
#include <string_view>

namespace god2 {
struct ReplayResult {
    DecodeResult status;
    std::vector<Packet> packets;
    std::vector<size_t> lengths;
    size_t remaining_bytes = 0;
};
class ProtocolReplayTool {
public:
    explicit ProtocolReplayTool(ProtocolSpec& spec) : spec_(spec) {}
    static std::vector<uint8_t> parse_hex(std::string_view hex);
    ReplayResult replay_hex(std::string_view hex);
    static void print(const ReplayResult& result, std::ostream& out);
private:
    ProtocolSpec& spec_;
};
}
