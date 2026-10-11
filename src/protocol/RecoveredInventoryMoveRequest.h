#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {
// Current client 00496610 -> 004132E0: opcode 24 and two slot bytes.
// UI callers 0049A330/0049EAB0 pass selected source then destination.
// This wire contract does not recover server swap/merge/equipment policy.
struct RecoveredInventoryMoveRequest {
    static constexpr std::uint8_t opcode = 0x24;
    static constexpr std::size_t logical_size = 3;
    struct Request {
        std::uint8_t source_slot;
        std::uint8_t destination_slot;
        bool operator==(const Request&) const = default;
    };
    using LogicalRecord = std::array<std::uint8_t, logical_size>;
    static constexpr LogicalRecord encode(Request request) noexcept {
        return {opcode, request.source_slot, request.destination_slot};
    }
    // Producer narrows both arguments to bytes without checking slot range.
    // Domain, ownership and modal/session authorization belong to the service.
    static std::optional<Request> decode(std::span<const std::uint8_t> logical) noexcept {
        if (logical.size() != logical_size || logical[0] != opcode) return std::nullopt;
        return Request{logical[1], logical[2]};
    }
};
}
