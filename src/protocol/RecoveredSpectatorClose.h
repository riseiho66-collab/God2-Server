#pragma once
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {
// TW149c complete00478C40 helper retained187: qualified local windowclose
// sends A3 in UI mode1 or CB in mode2, each with one opaque body byte.
// That byte is the highest saved incomingECX byte, not a nonce or UI epoch.
// A close input establishes neither battle rights nor a paired server ACK.
struct RecoveredSpectatorClose {
    static constexpr std::size_t logical_size=2;
    struct Request {
        std::uint8_t opcode{};
        std::uint8_t opaque{};
        bool operator==(const Request&) const=default;
    };
    static std::optional<Request> decode(std::span<const std::uint8_t> bytes) noexcept {
        if(bytes.size()!=logical_size || (bytes[0]!=0xa3 && bytes[0]!=0xcb))return {};
        return Request{bytes[0],bytes[1]};
    }
};
}
