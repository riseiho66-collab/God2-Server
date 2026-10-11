#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {
// Current image producer RVA 96350 -> original queue append RVA 132E0.
// C2S only: this does not authorize item use or construct an S2C response.
struct RecoveredInventoryItemRequest {
    static constexpr std::uint8_t opcode = 0x25;
    static constexpr std::size_t logical_size = 5;

    struct Request {
        std::uint16_t client_item_id;
        std::uint8_t raw_slot;
        std::uint8_t raw_tail;
    };

    using LogicalRecord = std::array<std::uint8_t, logical_size>;

    // Lossless C2S record reconstruction, matching the native producer's bytes.
    // This does not apply its UI send gate, enqueue, or authorize an operation.
    static constexpr LogicalRecord encode(Request request) noexcept {
        return {opcode, static_cast<std::uint8_t>(request.client_item_id),
                static_cast<std::uint8_t>(request.client_item_id >> 8),
                request.raw_slot, request.raw_tail};
    }

    // One logical record after framing/integrity validation. The producer copies
    // the high byte of its first stack argument into raw_tail, not quantity.
    // It performs no ID/slot range validation; authorization belongs to a caller
    // with established ownership/state, not this lossless structural decoder.
    static std::optional<Request> decode(
        std::span<const std::uint8_t> logical) noexcept {
        if (logical.size() != logical_size || logical[0] != opcode)
            return std::nullopt;
        return Request{
            static_cast<std::uint16_t>(logical[1] + 256u * logical[2]),
            logical[3], logical[4]};
    }
};
}
