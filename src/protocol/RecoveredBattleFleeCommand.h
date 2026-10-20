#pragma once
#include <algorithm>
#include <array>
#include <cstdint>
#include <optional>
#include <span>
namespace god2 {
// Current aaf0:518E50 explicit action6 path. It clears14 target-scratch bytes,
// takes5156E0's actual current actor, forces count1 and constructs self masks.
// It preserves actor<=14 and sideflag=(A==0 && B!=0), context=B+3C.
// logical4 is an unwritten stack BYTE; action6 does not initialize the final
// DWORD13..16. Neither opaque region is zero, a result, a fee or permission.
// Format/producer-owned bytes only; actual Session/actor/grant and successful
// withdrawal/save/83-response/return ownership belong to the real room host.
struct RecoveredBattleFleeCommand {
    static constexpr std::size_t logical_size=17;
    using Bytes=std::array<std::uint8_t,logical_size>;
    class Request {
    public:
        std::uint8_t actor_position()const noexcept{return raw_[1];}
        std::uint8_t side_flag()const noexcept{return raw_[3];}
        std::uint8_t opaque4()const noexcept{return raw_[4];}
        std::uint32_t context()const noexcept{return u32(raw_,9);}
        std::uint32_t unwritten_tail_bits()const noexcept{return u32(raw_,13);}
        bool operator==(const Request&)const=default;
    private:
        friend struct RecoveredBattleFleeCommand;
        explicit Request(Bytes raw):raw_(raw){}
        Bytes raw_;
    };
    static std::optional<Request> decode(std::span<const std::uint8_t> raw)noexcept {
        if(raw.size()!=logical_size||raw[0]!=0x35||raw[2]!=6||raw[1]>14||raw[3]>1)return {};
        const auto actor=raw[1];
        const auto low=actor<14?static_cast<std::uint16_t>(1u<<actor):std::uint16_t{0};
        const auto high=actor==14?std::uint16_t{1}:std::uint16_t{0};
        if(u16(raw,5)!=low||u16(raw,7)!=high)return {};
        Bytes owned;std::copy(raw.begin(),raw.end(),owned.begin());return Request(owned);
    }
    static Bytes encode(const Request& request)noexcept{return request.raw_;}
private:
    static std::uint16_t u16(std::span<const std::uint8_t> b,std::size_t at)noexcept {
        return static_cast<std::uint16_t>(b[at]|(std::uint16_t{b[at+1]}<<8));
    }
    static std::uint32_t u32(std::span<const std::uint8_t> b,std::size_t at)noexcept {
        return std::uint32_t{u16(b,at)}|(std::uint32_t{u16(b,at+2)}<<16);
    }
};
}
