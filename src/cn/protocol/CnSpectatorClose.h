#pragma once
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace god2cn {
// Independent CN582f complete004A1DA0..004A1E16: qualified local windowclose
// calls00481440 with A3/body1 for UI mode1 or CB/body1 for mode2.
// LEA[EBP-1] points to the highest saved incomingECX byte. Preserve it;
// never substitute zero or interpret it as nonce/windowgeneration/ACK/rights.
struct CnSpectatorClose {
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
