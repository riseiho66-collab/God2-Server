#pragma once
#include <algorithm>
#include <array>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {
// Native00497210 queues59 with the exact18 bytes supplied by004EA530.
// targetWORD is followed by name16; bytes after NUL retain native stack residue.
// The name is display context, never server ownership authority.
struct RecoveredPartyPositionQuery {
    static constexpr std::uint8_t opcode=0x59;
    static constexpr std::size_t logical_size=19;
    struct Request {
        std::uint16_t target{};
        std::array<std::uint8_t,16> name{};
        bool operator==(const Request&) const=default;
    };
    static std::array<std::uint8_t,logical_size> encode(const Request& request) noexcept {
        std::array<std::uint8_t,logical_size> wire{};
        wire[0]=opcode;wire[1]=static_cast<std::uint8_t>(request.target);
        wire[2]=static_cast<std::uint8_t>(request.target>>8);
        std::copy(request.name.begin(),request.name.end(),wire.begin()+3);return wire;
    }
    static std::optional<Request> decode(std::span<const std::uint8_t> wire) noexcept {
        if(wire.size()!=logical_size || wire[0]!=opcode)return {};
        Request value{static_cast<std::uint16_t>(wire[1]|(std::uint16_t{wire[2]}<<8))};
        std::copy_n(wire.begin()+3,16,value.name.begin());return value;
    }
};
}
