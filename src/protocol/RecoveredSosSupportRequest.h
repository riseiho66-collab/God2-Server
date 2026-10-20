#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>
namespace god2 {
// Current aaf0 TW: cursor6 support.ani ->4835A0 selection5 ->481F70
// action-11 ->465FA0:466057 ->497140 ->4132E0(C6A,body8).
// The two whole DWORDs are local actor identity and selected world actor.
// This is an untrusted support request, not party Join, watcher6E, a room
// capability, target membership proof or permission to replay an initial roster.
struct RecoveredSosSupportRequest {
    static constexpr std::uint8_t opcode=0x6a;
    static constexpr std::size_t logical_size=9;
    struct Request {
        std::uint32_t self,target;
        bool operator==(const Request&) const=default;
    };
    using Bytes=std::array<std::uint8_t,logical_size>;
    static std::optional<Request> decode(std::span<const std::uint8_t> raw) noexcept {
        if(raw.size()!=logical_size || raw[0]!=opcode)return {};
        const auto dword=[&](std::size_t at) {
            return std::uint32_t{raw[at]}|(std::uint32_t{raw[at+1]}<<8)|
                (std::uint32_t{raw[at+2]}<<16)|(std::uint32_t{raw[at+3]}<<24);
        };
        return Request{dword(1),dword(5)};
    }
    static Bytes encode(Request request) noexcept {
        Bytes raw{};raw[0]=opcode;
        for(unsigned i=0;i<4;++i){raw[1+i]=static_cast<std::uint8_t>(request.self>>(i*8));
            raw[5+i]=static_cast<std::uint8_t>(request.target>>(i*8));}
        return raw;
    }
};
}
