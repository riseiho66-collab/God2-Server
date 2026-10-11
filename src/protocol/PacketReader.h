#pragma once
#include <cstddef>
#include <cstdint>
#include <span>
#include <string>
#include <vector>

namespace god2 {
// Non-owning: the supplied bytes must outlive the reader and remain unchanged.
class PacketReader {
public:
    explicit PacketReader(std::span<const uint8_t> bytes) : bytes_(bytes) {}
    uint8_t read_u8();
    uint16_t read_u16();
    uint32_t read_u32();
    int32_t read_i32();
    float read_float();
    std::string read_string();
    std::string read_fixed_string(size_t width);
    std::vector<uint8_t> read_bytes(size_t count);
    [[nodiscard]] size_t remaining() const noexcept { return bytes_.size() - cursor_; }
    void reset_cursor() noexcept { cursor_ = 0; }
    [[nodiscard]] std::span<const uint8_t> bytes() const noexcept { return bytes_; }
    [[nodiscard]] std::string hex_dump() const;
private:
    void require(size_t count) const;
    std::span<const uint8_t> bytes_;
    size_t cursor_ = 0;
};
}
