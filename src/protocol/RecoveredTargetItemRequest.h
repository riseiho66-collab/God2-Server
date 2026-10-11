#pragma once
#include <array>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {
// Native963C0 -> 96486 ->132E0. Target semantics require separate ownership proof.
struct RecoveredTargetItemRequest {
    struct Request {
        std::uint16_t raw_target, client_item_id;
        std::uint8_t raw_slot, raw_tail;
    };
    using LogicalRecord = std::array<std::uint8_t,7>;
    static constexpr LogicalRecord encode(Request value) noexcept {
        return {0x26,static_cast<std::uint8_t>(value.raw_target),
            static_cast<std::uint8_t>(value.raw_target>>8),
            static_cast<std::uint8_t>(value.client_item_id),
            static_cast<std::uint8_t>(value.client_item_id>>8),value.raw_slot,value.raw_tail};
    }
    static std::optional<Request> decode(std::span<const std::uint8_t> record) noexcept {
        if(record.size()!=7 || record[0]!=0x26) return std::nullopt;
        return Request{static_cast<std::uint16_t>(record[1]+256u*record[2]),
            static_cast<std::uint16_t>(record[3]+256u*record[4]),record[5],record[6]};
    }
    // raw_tail preserves a native uninitialized local byte. Never use as quantity.
};
}
