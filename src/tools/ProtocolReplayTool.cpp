#include "tools/ProtocolReplayTool.h"
#include "protocol/PacketReader.h"
#include <iomanip>
#include <ostream>
#include <sstream>
#include <stdexcept>

namespace god2 {
namespace {
int hex_digit(char c) {
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    return -1;
}
bool whitespace(char c) { return c == ' ' || c == '\t' || c == '\r' || c == '\n' || c == '\f' || c == '\v'; }
}
std::vector<uint8_t> ProtocolReplayTool::parse_hex(std::string_view hex) {
    std::vector<uint8_t> bytes;
    int high = -1;
    for (size_t i = 0; i < hex.size(); ++i) {
        const char c = hex[i];
        if (whitespace(c)) {
            if (high != -1) throw std::runtime_error("Incomplete hex byte at character " + std::to_string(i));
            continue;
        }
        const int digit = hex_digit(c);
        if (digit < 0) throw std::runtime_error("Invalid hex character at character " + std::to_string(i));
        if (high < 0) high = digit;
        else {
            bytes.push_back(static_cast<uint8_t>((high << 4) | digit));
            high = -1;
        }
    }
    if (high != -1) throw std::runtime_error("Incomplete final hex byte");
    return bytes;
}
ReplayResult ProtocolReplayTool::replay_hex(std::string_view hex) {
    ReplayResult result;
    try {
        const auto bytes = parse_hex(hex);
        Buffer input;
        input.append(bytes);
        PacketDecoder decoder(spec_);
        result.status = decoder.decode(input, result.packets);
        result.remaining_bytes = input.size();
        for (const auto& packet : result.packets)
            result.lengths.push_back(spec_.header_size() + packet.payload.size());
        if (result.status.ok && result.remaining_bytes != 0)
            result.status = {false, "Truncated final packet: " + std::to_string(result.remaining_bytes) + " buffered bytes"};
    } catch (const std::runtime_error& error) {
        result.status = {false, error.what()};
    }
    return result;
}
void ProtocolReplayTool::print(const ReplayResult& result, std::ostream& out) {
    // Format locally so replay cannot change the caller's stream flags.
    std::ostringstream text;
    for (size_t i = 0; i < result.packets.size(); ++i) {
        const auto& packet = result.packets[i];
        text << "length=" << std::dec << result.lengths.at(i)
             << " opcode=0x" << std::hex << std::setw(4) << std::setfill('0') << packet.opcode
             << " payload=" << PacketReader(packet.payload).hex_dump() << '\n';
    }
    if (!result.status.ok) text << "parse error: " << result.status.error << '\n';
    out << text.str();
}
}
