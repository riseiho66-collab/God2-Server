#pragma once
#include <array>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {
// Current NPC pool branch 66E1B -> 96750 -> 132E0. Grammar, not authorization.
struct RecoveredNpcInteraction {
    static constexpr std::uint8_t opcode=0x37;
    static constexpr std::size_t logical_size=5;
    struct Request { std::uint32_t raw_target; };
    using LogicalRecord=std::array<std::uint8_t,logical_size>;
    static constexpr LogicalRecord encode(Request request) noexcept {
        return {opcode,static_cast<std::uint8_t>(request.raw_target),
            static_cast<std::uint8_t>(request.raw_target>>8),
            static_cast<std::uint8_t>(request.raw_target>>16),
            static_cast<std::uint8_t>(request.raw_target>>24)};
    }
    static std::optional<Request> decode(std::span<const std::uint8_t> logical) noexcept {
        if(logical.size()!=logical_size || logical[0]!=opcode) return std::nullopt;
        // Do not discard the high word: native producer retains the argument's bits.
        std::uint32_t target=0;
        for(unsigned i=0;i<4;++i) target|=std::uint32_t{logical[i+1]}<<(8*i);
        return Request{target};
    }
};
}
