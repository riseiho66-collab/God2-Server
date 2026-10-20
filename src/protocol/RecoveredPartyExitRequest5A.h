#pragma once
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>
namespace god2 {
// Current aaf0 TW:4971B0 sends own PlayerData WORD/name+B7 as C5A/body18.
// Selected roster:4EA530 ->UI+AFEEC target WORD / AFEEE name16 ->4EF560
// modal11 ->483C80 case11 ->4EA510 sends SAME C5A/body18 from that buffer.
// The target can therefore be self or selected member, not necessarily self.
// Name bytes including post-NUL residue are display context, not authority.
// Actual party membership/leader/consent remain the explicit CUSTOM owner.
struct RecoveredPartyExitRequest5A {
    static constexpr std::uint8_t opcode=0x5a;
    static constexpr std::size_t logical_size=19;
    using Name=std::array<std::uint8_t,16>;
    struct Request {std::uint16_t target;Name name;bool operator==(const Request&) const=default;};
    using Bytes=std::array<std::uint8_t,logical_size>;
    static std::optional<Request> decode(std::span<const std::uint8_t> raw) noexcept {
        if(raw.size()!=logical_size || raw[0]!=opcode)return {};
        Request request{static_cast<std::uint16_t>(raw[1]|(std::uint16_t{raw[2]}<<8)),{}};
        std::copy_n(raw.begin()+3,16,request.name.begin());return request;
    }
    static Bytes encode(const Request& request) noexcept {
        Bytes raw{};raw[0]=opcode;raw[1]=static_cast<std::uint8_t>(request.target);
        raw[2]=static_cast<std::uint8_t>(request.target>>8);
        std::copy(request.name.begin(),request.name.end(),raw.begin()+3);return raw;
    }
};
}
