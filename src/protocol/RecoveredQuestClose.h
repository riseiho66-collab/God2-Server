#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {
// Current C8350 -> C83A2 -> 132E0. Neither word is a proven gameplay ID.
struct RecoveredQuestClose {
    static constexpr std::uint8_t opcode = 0x86;
    static constexpr std::size_t logical_size = 5;
    struct Request {
        std::uint16_t source_low_word, this_high_word;
    };
    using LogicalRecord = std::array<std::uint8_t, logical_size>;

    // Diagnostic reconstruction only. The upper word is saved client-pointer
    // residue, not padding; callers must supply the observed value explicitly.
    static constexpr LogicalRecord encode(Request request) noexcept {
        return {opcode, static_cast<std::uint8_t>(request.source_low_word),
                static_cast<std::uint8_t>(request.source_low_word >> 8),
                static_cast<std::uint8_t>(request.this_high_word),
                static_cast<std::uint8_t>(request.this_high_word >> 8)};
    }
    static std::optional<Request> decode(std::span<const std::uint8_t> logical) noexcept {
        if(logical.size() != logical_size || logical[0] != opcode) return std::nullopt;
        return Request{
            static_cast<std::uint16_t>(logical[1] + 256u * logical[2]),
            static_cast<std::uint16_t>(logical[3] + 256u * logical[4])};
    }
};
}
