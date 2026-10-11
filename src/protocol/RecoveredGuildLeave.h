#pragma once
#include <cstdint>
#include <optional>
#include <span>
namespace god2 {
// Original/current 004EF6A0 -> modal4 -> 004EE560(4) -> 004EF6E0:
// C2S73 carries only the recipient-local native roster slot BYTE. It is NOT
// S2C73, a database character identity, or authorization to remove a member.
struct RecoveredGuildLeave {
    static constexpr std::uint8_t opcode=0x73;
    static constexpr std::size_t logical_size=2;
    struct Request {std::uint8_t slot;};
    static std::optional<Request> decode(std::span<const std::uint8_t> logical) noexcept {
        if(logical.size()!=logical_size || logical[0]!=opcode || logical[1]>=50)return {};
        return Request{logical[1]};
    }
};
}
