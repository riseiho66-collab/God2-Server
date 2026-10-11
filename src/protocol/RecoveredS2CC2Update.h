#pragma once
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {
// S2C C2 is a three-byte WORLD UI refresh. Its native C2E20 method does not
// consume the two body bytes. It is not qualified as a C2S C2 response.
struct RecoveredS2CC2Update {
    static constexpr std::uint8_t opcode=0xc2;
    static constexpr std::size_t logical_size=3;
    using Record=std::array<std::uint8_t,logical_size>;
    static std::optional<Record> decode(std::span<const std::uint8_t> bytes) noexcept {
        if(bytes.size()!=logical_size || bytes[0]!=opcode)return {};
        Record out{};std::copy(bytes.begin(),bytes.end(),out.begin());return out;
    }
    static Record encode(std::array<std::uint8_t,2> opaque_body) noexcept {
        return {opcode,opaque_body[0],opaque_body[1]};
    }
};
}
