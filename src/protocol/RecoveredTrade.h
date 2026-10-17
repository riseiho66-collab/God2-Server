#pragma once
#include <algorithm>
#include <array>
#include <cstdint>
#include <optional>
#include <limits>
#include <stdexcept>
#include <span>
#include <vector>

namespace god2 {
// Source projection failure, never a guessed native error packet.
class LegacyCoinProjectionError : public std::range_error {
public:
    using std::range_error::range_error;
};
// Current native player trade, not PK69/8A or bank61/62. Grammar only:
// 497250/497290/497A30/497A60 producers and 49D980..49DFF0 consumers.
// No client-provided target, item, quantity or money authorizes a mutation.
struct RecoveredTrade {
    enum class Kind { Open, OfferItem, OfferMoney, Confirm, Cancel };
    struct Request {
        Kind kind;
        std::uint16_t target{}, item{}, opaque{};
        std::uint8_t slot{}, quantity{}, control{};
        std::uint32_t money{};
        bool operator==(const Request&) const = default;
    };
    using Name = std::array<std::uint8_t,16>;
    using Item = std::array<std::uint8_t,24>;
    static constexpr std::size_t size(std::uint8_t opcode) noexcept {
        switch(opcode) {
        case 0x29:return 5;
        case 0x2a:return 7;
        case 0x2b:return 9;
        case 0x2c:case 0x2d:return 2;
        default:return 0;
        }
    }
    static std::optional<Request> decode(std::span<const std::uint8_t> b) noexcept {
        if(b.empty() || !size(b[0]) || b.size()!=size(b[0]))return {};
        const auto word=[&](std::size_t at) {
            return static_cast<std::uint16_t>(b[at] | (std::uint16_t{b[at+1]}<<8));
        };
        Request r{Kind::Open};
        switch(b[0]) {
        case 0x29:r.target=word(1);r.opaque=word(3);break;
        case 0x2a:r.kind=Kind::OfferItem;r.item=word(1);r.slot=b[3];r.quantity=b[4];r.target=word(5);break;
        case 0x2b:
            r.kind=Kind::OfferMoney;r.target=word(1);r.opaque=word(3);
            r.money=std::uint32_t{b[5]}|(std::uint32_t{b[6]}<<8)|
                (std::uint32_t{b[7]}<<16)|(std::uint32_t{b[8]}<<24);break;
        case 0x2c:r.kind=Kind::Confirm;r.control=b[1];break;
        case 0x2d:r.kind=Kind::Cancel;r.control=b[1];break;
        }
        return r;
    }
    static void word(std::vector<std::uint8_t>& b,std::uint16_t n) {
        b.push_back(static_cast<std::uint8_t>(n));b.push_back(static_cast<std::uint8_t>(n>>8));
    }
    static void dword(std::vector<std::uint8_t>& b,std::uint32_t n) {
        for(unsigned i=0;i<4;++i)b.push_back(static_cast<std::uint8_t>(n>>(8*i)));
    }
    static std::vector<std::uint8_t> encode(const Request& r) {
        std::vector<std::uint8_t> b;
        switch(r.kind) {
        case Kind::Open:b.push_back(0x29);word(b,r.target);word(b,r.opaque);break;
        case Kind::OfferItem:
            b.push_back(0x2a);word(b,r.item);b.push_back(r.slot);b.push_back(r.quantity);word(b,r.target);break;
        case Kind::OfferMoney:b.push_back(0x2b);word(b,r.target);word(b,r.opaque);dword(b,r.money);break;
        case Kind::Confirm:b={0x2c,r.control};break;
        case Kind::Cancel:b={0x2d,r.control};break;
        }
        return b;
    }
    // 4E ->49D980: raw name16 then peer WORD. Name conversion and termination
    // are the authority/projection caller's responsibility, as are reserved IDs.
    static std::vector<std::uint8_t> open(std::uint16_t peer,const Name& name) {
        std::vector<std::uint8_t> b{0x4e};b.insert(b.end(),name.begin(),name.end());word(b,peer);return b;
    }
    // 50 ->49DF10 copies all24 bytes; signed body+1 must be0..7. Preserve
    // count, reserved bytes and instance metadata; never invent item attributes.
    static std::optional<std::vector<std::uint8_t>> peer_item(const Item& item) {
        if(item[1]>=8)return {};
        std::vector<std::uint8_t> b{0x50};b.insert(b.end(),item.begin(),item.end());return b;
    }
    // 51 dispatcher reads a DWORD at logical+5, not logical+1. The leading
    // four body bytes are opaque. Keep them explicit for future native evidence.
    static std::vector<std::uint8_t> peer_money(std::uint32_t amount,
        const std::array<std::uint8_t,4>& opaque={}) {
        std::vector<std::uint8_t> b{0x51};b.insert(b.end(),opaque.begin(),opaque.end());dword(b,amount);return b;
    }
    // 53 WORD is peer confirmation, not successful settlement. Native nonzero
    // marks peer text and zero updates control9; do not equate it with commit.
    static std::vector<std::uint8_t> peer_confirmation(std::uint16_t value) {
        std::vector<std::uint8_t> b{0x53};word(b,value);return b;
    }
    // 27 ->498D70 is the absolute local purse DWORD, independent of role23.
    static bool wallet_amount_representable(std::uint64_t amount) noexcept {
        return amount<=static_cast<std::uint64_t>(std::numeric_limits<std::int32_t>::max());
    }
    static std::vector<std::uint8_t> wallet(std::uint64_t amount) {
        if(!wallet_amount_representable(amount))
            throw LegacyCoinProjectionError("Native purse requires a qualified extended coin profile");
        std::vector<std::uint8_t> b{0x27};dword(b,static_cast<std::uint32_t>(amount));return b;
    }
    // 4F restores locally escrowed money, clears item lists, then closes.
    // It does NOT restore inventory slots; the server must project them.
    // 52 only closes: caller must finish authoritative inventory/wallet sync.
    // Both have a native logical3 width although their WORD is not consumed.
    static std::vector<std::uint8_t> rollback_close(std::uint16_t opaque=0) {
        std::vector<std::uint8_t> b{0x4f};word(b,opaque);return b;
    }
    static std::vector<std::uint8_t> close_without_refund(std::uint16_t opaque=0) {
        std::vector<std::uint8_t> b{0x52};word(b,opaque);return b;
    }
};
}
