#pragma once
#include <cstdint>
#include <algorithm>
#include <array>
#include <optional>
#include <span>
namespace god2 {
// Current aaf0:512790 ->5156E0 ->518E50 action8. Body count1 is
// forced from the same current actor, masks name that actor only. The final
// DWORD is (battle+488==0), also saved to+48C; not HP, server acceptance,
// battle identity or an invitation token. Primary/secondary ownership and
// consumed native grant remain separate actual-owner obligations.
struct RecoveredSosBattleCommand {
    static constexpr std::size_t logical_size=17;
    using Bytes=std::array<std::uint8_t,logical_size>;
    class Request {
    public:
        std::uint8_t actor_position() const noexcept{return raw_[1];}
        std::uint8_t side_flag() const noexcept{return raw_[3];}
        std::uint8_t opaque4() const noexcept{return raw_[4];}
        std::uint32_t context() const noexcept{return u32(raw_,9);}
        std::uint32_t requested_flag() const noexcept{return u32(raw_,13);}
        bool operator==(const Request&) const=default;
    private:
        friend struct RecoveredSosBattleCommand;
        explicit Request(Bytes raw):raw_(raw){}
        Bytes raw_;
    };
    static std::optional<Request> decode(std::span<const std::uint8_t> raw) noexcept {
        if(raw.size()!=logical_size || raw[0]!=0x35 || raw[2]!=8 || raw[1]>14 || raw[3]>1 ||
           u32(raw,13)>1)return {};
        const auto actor=raw[1];
        const auto low=actor<14?static_cast<std::uint16_t>(1u<<actor):0;
        const auto high=actor==14?1u:0u;
        if(u16(raw,5)!=low || u16(raw,7)!=high)return {};
        Bytes owned;std::copy(raw.begin(),raw.end(),owned.begin());return Request(owned);
    }
    static Bytes encode(const Request& request) noexcept{return request.raw_;}
private:
    static std::uint16_t u16(std::span<const std::uint8_t> raw,std::size_t at) noexcept {
        return static_cast<std::uint16_t>(raw[at]|(std::uint16_t{raw[at+1]}<<8));
    }
    static std::uint32_t u32(std::span<const std::uint8_t> raw,std::size_t at) noexcept {
        return std::uint32_t{u16(raw,at)}|(std::uint32_t{u16(raw,at+2)}<<16);
    }
};
}
