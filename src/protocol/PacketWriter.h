#pragma once
#include <cstddef>
#include <cstdint>
#include <span>
#include <string_view>
#include <vector>

namespace god2 {
class PacketWriter {
public:
    void write_u8(uint8_t value);
    void write_u16(uint16_t value);
    void write_u32(uint32_t value);
    void write_i32(int32_t value);
    void write_float(float value);
    void write_string(std::string_view value);
    void write_fixed_string(std::string_view value, size_t width);
    void write_bytes(std::span<const uint8_t> value);
    [[nodiscard]] const std::vector<uint8_t>& bytes() const noexcept { return bytes_; }
private:
    std::vector<uint8_t> bytes_;
};
}
