#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {
// Pinned149c VA496550 -> queue append VA4132E0: key low WORD, source slot BYTE,
// and the third argument's low BYTE (4965D0 -> wire4965E9). The producer does
// not hardcode1. This codec supports the observed caller flag1 subset only;
// flag1 includes unequip and does not prove equip, quantity or destination.
// Historical category execution probes used old6bf, not149c acceptance.
// Structural decoding does not authorize item use or clear the client UI's
// pending state; those require the original reply contract.
struct RecoveredSelectionItemRequest {
    static constexpr std::uint8_t opcode = 0x28;
    static constexpr std::size_t logical_size = 5;

    struct Request {
        std::uint16_t client_item_id;
        std::uint8_t raw_slot;
    };

    using LogicalRecord = std::array<std::uint8_t, logical_size>;

    static constexpr LogicalRecord encode(Request request) noexcept {
        return {opcode, static_cast<std::uint8_t>(request.client_item_id),
                static_cast<std::uint8_t>(request.client_item_id >> 8),
                request.raw_slot, 1};
    }

    static std::optional<Request> decode(std::span<const std::uint8_t> logical) noexcept {
        if (logical.size() != logical_size || logical[0] != opcode || logical[4] != 1)
            return std::nullopt;
        return Request{static_cast<std::uint16_t>(logical[1] + 256u * logical[2]), logical[3]};
    }
};
}
