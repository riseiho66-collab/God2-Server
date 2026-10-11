#pragma once

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {

// Current B910 -> 14A70 preselection reply only. Not a world/player schema.
// Transport decryption, checksum and record splitting precede this decoder.
struct RecoveredCharacterContext {
    static constexpr std::uint8_t opcode = 0x1f;
    static constexpr std::size_t body_size = 124;
    static constexpr std::size_t logical_size = body_size + 1;
    struct PreselectionReply {
        std::array<std::uint8_t, body_size> opaque_body;
    };

    // Success means exact record shape, NOT authorized state or playable world.
    // B910 discards this body; the alternate F930 caller does not. Do not reuse
    // this contract to infer fields, defaults or safe values for that caller.
    [[nodiscard]] static std::optional<PreselectionReply> decode_preselection_reply(
        std::span<const std::uint8_t> logical) noexcept {
        if (logical.size() != logical_size || logical[0] != opcode)
            return std::nullopt;
        PreselectionReply reply{};
        std::copy(logical.begin() + 1, logical.end(), reply.opaque_body.begin());
        return reply;
    }
};

} // namespace god2
