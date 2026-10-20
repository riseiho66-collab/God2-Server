#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>
namespace god2 {
// Current aaf0 TW cursor5 team.ani ->4835A0 selection4 ->481F70
// action-10 ->465FA0:4660DC ->497170 ->4132E0(57,body4).
// The first formal self argument is ignored. Whole target DWORD remains
// untrusted; this is not a native kick instruction or official admission rule.
struct RecoveredTeamRequest57 {
    static constexpr std::uint8_t opcode=0x57;
    static constexpr std::size_t logical_size=5;
    struct Request {std::uint32_t target;bool operator==(const Request&) const=default;};
    using Bytes=std::array<std::uint8_t,logical_size>;
    static std::optional<Request> decode(std::span<const std::uint8_t> raw) noexcept {
        if(raw.size()!=logical_size || raw[0]!=opcode)return {};
        return Request{std::uint32_t{raw[1]}|(std::uint32_t{raw[2]}<<8)|
            (std::uint32_t{raw[3]}<<16)|(std::uint32_t{raw[4]}<<24)};
    }
    static Bytes encode(Request request) noexcept {
        Bytes raw{};raw[0]=opcode;
        for(unsigned i=0;i<4;++i)raw[1+i]=static_cast<std::uint8_t>(request.target>>(i*8));
        return raw;
    }
};
}
