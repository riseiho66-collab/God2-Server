#pragma once
#include <algorithm>
#include <array>
#include <cstdint>
#include <optional>
#include <span>
namespace god2 {
// Current aaf0:5127C0->5156E0->518E50(9,actor,0,B+44C).
// Native action9 emits targetcount0, hence both target WORDs are zero.
// logical4 and DWORD13..16 are unwritten stack residue, preserved verbatim.
// Pair positions are SERVER result operands, never incoming C35 targets.
struct RecoveredBattleRowSwapCommand {
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
        friend struct RecoveredBattleRowSwapCommand;
        explicit Request(Bytes raw):raw_(raw){}
        Bytes raw_;
    };
    static std::optional<Request> decode(std::span<const std::uint8_t> raw)noexcept {
        if(raw.size()!=logical_size||raw[0]!=0x35||raw[2]!=9||raw[1]>14||raw[3]>1||u32(raw,5)!=0)return {};
        Bytes owned;std::copy(raw.begin(),raw.end(),owned.begin());return Request(owned);
    }
    static Bytes encode(const Request& r)noexcept{return r.raw_;}
private:
    static std::uint32_t u32(std::span<const std::uint8_t> b,std::size_t p)noexcept {
        return std::uint32_t(b[p])|(std::uint32_t(b[p+1])<<8)|
            (std::uint32_t(b[p+2])<<16)|(std::uint32_t(b[p+3])<<24);
    }
};
}
