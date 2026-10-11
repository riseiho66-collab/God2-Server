#pragma once
#include <array>
#include <cstdint>
#include <optional>
#include <span>
#include <string_view>
#include <vector>

namespace god2cn {
// 00471730 CAN v1.0: raw binary, not the compressed HMD resource wrapper.
class CnAreaDirectory {
public:
    struct Entry {
        std::array<std::uint8_t,64> native_record;
        std::uint8_t raw_kind() const noexcept { return native_record[0]; }
        std::optional<std::string_view> filename() const noexcept;
    };
    static CnAreaDirectory read(std::span<const std::uint8_t> bytes);
    // 0048F61A..0048F630: area index ->u16 table value ->64-byte entry.
    // Entry byte0 is retained; this consumer skips it without comparing kind.
    const Entry* lookup(std::uint16_t native_area_index) const noexcept;
    const auto& entries() const noexcept { return entries_; }
    const auto& area_indices() const noexcept { return area_indices_; }
    const auto& trailing_bytes() const noexcept { return trailing_; }
private:
    CnAreaDirectory()=default;
    std::vector<Entry> entries_;
    std::vector<std::uint16_t> area_indices_;
    std::vector<std::uint8_t> trailing_;
};
}
