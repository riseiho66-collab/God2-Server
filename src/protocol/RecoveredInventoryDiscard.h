#pragma once
#include <array>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {
// Native497720 queues the four raw bytes supplied by49A330/4C9ED0:
// item WORD, bag slot BYTE, quantity BYTE. S2C27 is a different contract.
struct RecoveredInventoryDiscard {
    static constexpr std::uint8_t opcode=0x27;
    static constexpr std::size_t logical_size=5;
    struct Request {
        std::uint16_t item;
        std::uint8_t slot,quantity;
        bool operator==(const Request&) const = default;
    };
    static constexpr std::array<std::uint8_t,5> encode(Request r) {
        return {opcode,static_cast<std::uint8_t>(r.item),static_cast<std::uint8_t>(r.item>>8),r.slot,r.quantity};
    }
    static std::optional<Request> decode(std::span<const std::uint8_t> bytes) {
        if(bytes.size()!=logical_size || bytes[0]!=opcode)return std::nullopt;
        return Request{static_cast<std::uint16_t>(bytes[1]+256u*bytes[2]),bytes[3],bytes[4]};
    }
};
}
