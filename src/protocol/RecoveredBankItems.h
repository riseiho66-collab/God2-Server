#pragma once
#include "protocol/RecoveredInventoryProjection.h"
#include <array>
#include <cstdint>
#include <optional>
#include <span>
namespace god2 {
// Native4975F0/4976F0,4977B0/497880 and497510 producers.
//63/64 quantity is an amount;65's final1 accompanies whole-cell movement.
// Parsing preserves bytes and grants no item/ownership authority.
struct RecoveredBankItems {
    enum class Kind : std::uint8_t {Deposit=0x63,Withdraw=0x64,Move=0x65};
    struct Request {
        Kind kind{};std::uint16_t target{};
        std::uint8_t page{},source{},destination{},quantity{};
        bool operator==(const Request&) const=default;
    };
    static std::optional<Request> decode(std::span<const std::uint8_t> b) noexcept {
        if(b.size()!=7 || b[0]<0x63 || b[0]>0x65)return {};
        return Request{static_cast<Kind>(b[0]),static_cast<std::uint16_t>(b[1]|std::uint16_t{b[2]}<<8),b[3],b[4],b[5],b[6]};
    }
    static std::array<std::uint8_t,7> encode(const Request& r) noexcept {
        return {static_cast<std::uint8_t>(r.kind),static_cast<std::uint8_t>(r.target),
            static_cast<std::uint8_t>(r.target>>8),r.page,r.source,r.destination,r.quantity};
    }
    //471E50 copies quantity/slot plus all20 metadata bytes into page*50+slot.
    // Clearing by48 replaces inactive metadata too, unlike46mode12.
    static std::optional<std::array<std::uint8_t,29>> slot(std::uint8_t page,
        std::uint8_t index,std::uint8_t quantity,const RecoveredInventoryProjection::Metadata& metadata) noexcept {
        const auto item=static_cast<std::uint16_t>(metadata[0]|std::uint16_t{metadata[1]}<<8);
        if(page>=6 || index>=50 || quantity>127 || (quantity==0)!=(item==0))return {};
        std::array<std::uint8_t,29> b{};b[0]=0x48;b[1]=page;b[5]=quantity;b[6]=index;
        std::copy(metadata.begin(),metadata.end(),b.begin()+9);return b;
    }
};
}
