#pragma once
#include <cstdint>
#include <optional>
#include <span>
namespace god2 {
// Current496300 ->4132E0; logical21 plus one selector byte.
// UI controls20/21/22/23 select Con/Str/Int/Speed as2/3/1/4.
struct RecoveredAttributeAllocation {
    static constexpr std::uint8_t opcode=0x21;
    static constexpr std::size_t logical_size=2;
    struct Request { std::uint8_t selector; };
    static std::optional<Request> decode(std::span<const std::uint8_t> bytes) noexcept {
        if(bytes.size()!=logical_size || bytes[0]!=opcode || bytes[1]<1 || bytes[1]>4)return std::nullopt;
        return Request{bytes[1]};
    }
};
}
