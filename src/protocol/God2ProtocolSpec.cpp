#include "protocol/God2ProtocolSpec.h"
#include "protocol/Endian.h"
#include "protocol/PacketWriter.h"
#include <stdexcept>
#include <utility>

namespace god2 {
God2ProtocolSpec::God2ProtocolSpec(size_t max_packet_size, std::string_view encryption, std::string_view compression)
    : max_packet_size_(max_packet_size), crypto_(encryption), compression_(compression) {
    if (max_packet_size < header_size() || max_packet_size > 65535)
        throw std::runtime_error("Packet size limit must be between 4 and 65535");
}
DecodeResult God2ProtocolSpec::try_decode(Buffer& input, std::vector<Packet>& outPackets) {
    while (input.size() >= 2) {
        const auto bytes = input.data();
        const size_t length = load_u16_le(bytes.data());
        if (length < header_size()) return {false, "Packet length is smaller than header"};
        if (length > max_packet_size_) return {false, "Packet length exceeds configured maximum"};
        if (bytes.size() < length) break;
        const auto decrypted = crypto_.decrypt(bytes.subspan(header_size(), length - header_size()));
        auto payload = compression_.decompress(decrypted);
        outPackets.push_back(Packet{load_u16_le(bytes.data() + 2), std::move(payload)});
        input.consume(length);
    }
    return {};
}
std::vector<uint8_t> God2ProtocolSpec::encode(const Packet& packet) {
    if (packet.payload.size() > max_packet_size_ - header_size())
        throw std::runtime_error("Packet payload exceeds configured maximum");
    const auto compressed = compression_.compress(packet.payload);
    const auto payload = crypto_.encrypt(compressed);
    if (payload.size() > max_packet_size_ - header_size())
        throw std::runtime_error("Encoded payload exceeds configured maximum");
    PacketWriter writer;
    writer.write_u16(static_cast<uint16_t>(header_size() + payload.size()));
    writer.write_u16(packet.opcode);
    writer.write_bytes(payload);
    return writer.bytes();
}
}
