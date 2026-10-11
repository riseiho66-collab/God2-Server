#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {
// Current C2S producer RVA 97DC0 -> 132E0; this is not quest authorization.
struct RecoveredQuestAction {
    static constexpr std::uint8_t opcode = 0x85;
    static constexpr std::size_t logical_size = 7;

    struct Request {
        std::uint16_t request_word, reply_word;
        std::uint8_t context_byte, opaque_tail;
    };
    using LogicalRecord = std::array<std::uint8_t, logical_size>;

    // Diagnostic reconstruction only. The caller supplies the observed stack
    // tail explicitly; there is no canonical padding value or gameplay default.
    static constexpr LogicalRecord encode(Request request) noexcept {
        return {opcode, static_cast<std::uint8_t>(request.request_word),
                static_cast<std::uint8_t>(request.request_word >> 8),
                static_cast<std::uint8_t>(request.reply_word),
                static_cast<std::uint8_t>(request.reply_word >> 8),
                request.context_byte, request.opaque_tail};
    }

    // One logical record after transport validation. Preserve both opaque words
    // as received, including high bits; client UI gates are not server rules.
    static std::optional<Request> decode(
        std::span<const std::uint8_t> logical) noexcept {
        if (logical.size() != logical_size || logical[0] != opcode)
            return std::nullopt;
        return Request{
            static_cast<std::uint16_t>(logical[1] + 256u * logical[2]),
            static_cast<std::uint16_t>(logical[3] + 256u * logical[4]),
            logical[5], logical[6]};
    }
};
}
