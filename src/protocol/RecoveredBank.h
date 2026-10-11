#pragma once
#include <array>
#include <cstdint>
#include <optional>
#include <span>
#include <vector>
namespace god2 {
// Current 497390/497450 money producers, 496860 NPC-window close.
// Native grammar only. CUSTOM-0064 must establish owned bank access first.
struct RecoveredBank {
    enum class Kind { Deposit,Withdraw,Close };
    struct Request {
        Kind kind{};
        std::uint32_t amount{};
        std::uint16_t target{},opaque{},window_kind{};
        bool operator==(const Request&) const=default;
    };
    static constexpr std::size_t size(std::uint8_t opcode) noexcept {
        return opcode==0x39?5:(opcode==0x61 || opcode==0x62?9:0);
    }
    static std::optional<Request> decode(std::span<const std::uint8_t> b) noexcept {
        if(b.empty() || !size(b[0]) || b.size()!=size(b[0]))return {};
        const auto word=[&](std::size_t i){return static_cast<std::uint16_t>(b[i]|std::uint16_t{b[i+1]}<<8);};
        if(b[0]==0x39)return Request{Kind::Close,0,word(1),0,word(3)};
        std::uint32_t amount=0;for(unsigned n=0;n<4;++n)amount|=std::uint32_t{b[1+n]}<<(8*n);
        return Request{b[0]==0x61?Kind::Deposit:Kind::Withdraw,amount,word(5),word(7),0};
    }
    static std::vector<std::uint8_t> encode(const Request& r) {
        if(r.kind==Kind::Close)return {0x39,static_cast<std::uint8_t>(r.target),static_cast<std::uint8_t>(r.target>>8),
            static_cast<std::uint8_t>(r.window_kind),static_cast<std::uint8_t>(r.window_kind>>8)};
        return {static_cast<std::uint8_t>(r.kind==Kind::Deposit?0x61:0x62),
            static_cast<std::uint8_t>(r.amount),static_cast<std::uint8_t>(r.amount>>8),
            static_cast<std::uint8_t>(r.amount>>16),static_cast<std::uint8_t>(r.amount>>24),
            static_cast<std::uint8_t>(r.target),static_cast<std::uint8_t>(r.target>>8),
            static_cast<std::uint8_t>(r.opaque),static_cast<std::uint8_t>(r.opaque>>8)};
    }
    // 46 body+10 mode0 opens ordinary NPC bank; 47 body+0 is absolute money.
    static std::array<std::uint8_t,13> open(std::uint16_t target) noexcept {
        return {0x46,static_cast<std::uint8_t>(target),static_cast<std::uint8_t>(target>>8)};
    }
    static std::array<std::uint8_t,9> balance(std::uint32_t amount) noexcept {
        return {0x47,static_cast<std::uint8_t>(amount),static_cast<std::uint8_t>(amount>>8),
            static_cast<std::uint8_t>(amount>>16),static_cast<std::uint8_t>(amount>>24)};
    }
};
}
