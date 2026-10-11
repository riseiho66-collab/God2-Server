#include "protocol/PacketReader.h"
#include "protocol/Endian.h"
#include <algorithm>
#include <bit>
#include <iomanip>
#include <limits>
#include <sstream>
#include <stdexcept>

namespace god2 {
void PacketReader::require(size_t count) const {
    if (count > remaining()) throw std::runtime_error("PacketReader: truncated payload at byte " + std::to_string(cursor_));
}
uint8_t PacketReader::read_u8() { require(1); return bytes_[cursor_++]; }
uint16_t PacketReader::read_u16() {
    require(2); auto value = load_u16_le(bytes_.data() + cursor_); cursor_ += 2; return value;
}
uint32_t PacketReader::read_u32() {
    require(4); auto value = load_u32_le(bytes_.data() + cursor_); cursor_ += 4; return value;
}
int32_t PacketReader::read_i32() { return std::bit_cast<int32_t>(read_u32()); }
float PacketReader::read_float() {
    static_assert(sizeof(float) == 4 && std::numeric_limits<float>::is_iec559);
    return std::bit_cast<float>(read_u32());
}
std::string PacketReader::read_string() {
    require(2);
    const auto length = load_u16_le(bytes_.data() + cursor_);
    require(static_cast<size_t>(length) + 2);
    cursor_ += 2;
    std::string value;
    if (length != 0) value.assign(reinterpret_cast<const char*>(bytes_.data() + cursor_), length);
    cursor_ += length;
    return value;
}
std::string PacketReader::read_fixed_string(size_t width) {
    require(width);
    if (width == 0) return {};
    const auto field = bytes_.subspan(cursor_, width);
    const auto end = std::find(field.begin(), field.end(), uint8_t{0});
    std::string value(field.begin(), end);
    cursor_ += width;
    return value;
}
std::vector<uint8_t> PacketReader::read_bytes(size_t count) {
    require(count);
    const auto field = bytes_.subspan(cursor_, count);
    std::vector<uint8_t> value(field.begin(), field.end());
    cursor_ += count;
    return value;
}
std::string PacketReader::hex_dump() const {
    std::ostringstream out;
    out << std::hex << std::setfill('0');
    for (size_t i = 0; i < bytes_.size(); ++i) {
        if (i != 0) out << ' ';
        out << std::setw(2) << static_cast<unsigned>(bytes_[i]);
    }
    return out.str();
}
}
