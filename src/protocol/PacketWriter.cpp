#include "protocol/PacketWriter.h"
#include <bit>
#include <limits>
#include <stdexcept>

namespace god2 {
void PacketWriter::write_u8(uint8_t value) { bytes_.push_back(value); }
void PacketWriter::write_u16(uint16_t value) {
    write_u8(static_cast<uint8_t>(value)); write_u8(static_cast<uint8_t>(value >> 8));
}
void PacketWriter::write_u32(uint32_t value) {
    for (unsigned shift = 0; shift < 32; shift += 8) write_u8(static_cast<uint8_t>(value >> shift));
}
void PacketWriter::write_i32(int32_t value) { write_u32(std::bit_cast<uint32_t>(value)); }
void PacketWriter::write_float(float value) {
    static_assert(sizeof(float) == 4 && std::numeric_limits<float>::is_iec559);
    write_u32(std::bit_cast<uint32_t>(value));
}
void PacketWriter::write_string(std::string_view value) {
    if (value.size() > 65535) throw std::runtime_error("PacketWriter: string exceeds uint16 length");
    // Copy before writing the prefix in case value aliases bytes_.
    const std::vector<uint8_t> copy(value.begin(), value.end());
    write_u16(static_cast<uint16_t>(copy.size()));
    write_bytes(copy);
}
void PacketWriter::write_fixed_string(std::string_view value, size_t width) {
    if (value.size() > width) throw std::runtime_error("PacketWriter: string exceeds fixed width");
    if (width > bytes_.max_size() - bytes_.size()) throw std::runtime_error("PacketWriter: fixed width too large");
    const std::vector<uint8_t> copy(value.begin(), value.end());
    write_bytes(copy);
    bytes_.insert(bytes_.end(), width - copy.size(), uint8_t{0});
}
void PacketWriter::write_bytes(std::span<const uint8_t> value) {
    if (value.empty()) return;
    const std::vector<uint8_t> copy(value.begin(), value.end());
    bytes_.insert(bytes_.end(), copy.begin(), copy.end());
}
}
