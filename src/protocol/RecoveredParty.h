#pragma once
#include <algorithm>
#include <array>
#include <cstdint>
#include <limits>
#include <optional>
#include <span>
#include <stdexcept>
#include <vector>
namespace god2 {
// Native497230 answer producer. Direction-qualified:
// C2S58 is the party preview answer; unrelated S2C58 carries saved vitals.
// C6A/497140 is cursor6 SUPPORT, not native party Join. It has a separate
// RecoveredSosSupportRequest type/owner. Existing Join below is INTERNAL
// CUSTOM-0062 consenting membership only; it has no native wire encoder.
// Cursor5 C57 team request likewise has its separate raw type. Kick below
// remains an INTERNAL custom party operation, not a qualified native command.
// C5A has distinct self/selected-member producers; its own raw exit type
// preserves that distinction. Join/Kick/Leave here are trusted INTERNAL input.
struct RecoveredParty {
    enum class Kind {Join,Answer,Kick,Leave};
    using Name=std::array<std::uint8_t,16>;
    struct Request {
        Kind kind;std::uint32_t self{},target{};std::uint8_t answer{},opaque{};Name name{};
        bool operator==(const Request&) const=default;
    };
    static constexpr std::size_t size(std::uint8_t opcode) noexcept {
        return opcode==0x58?5:0;
    }
    static std::optional<Request> decode(std::span<const std::uint8_t> b) {
        if(b.empty() || !size(b[0]) || b.size()!=size(b[0]))return {};
        if(b[0]==0x58)return Request{Kind::Answer,0,std::uint32_t{b[1]}|(std::uint32_t{b[2]}<<8),b[3],b[4]};
        return {};
    }
    static void word(std::vector<std::uint8_t>& b,std::uint16_t n){b.push_back(static_cast<std::uint8_t>(n));b.push_back(static_cast<std::uint8_t>(n>>8));}
    static void dword(std::vector<std::uint8_t>& b,std::uint32_t n){for(unsigned i=0;i<4;++i)b.push_back(static_cast<std::uint8_t>(n>>(8*i)));}
    static std::vector<std::uint8_t> encode(const Request& r) {
        std::vector<std::uint8_t> b;
        switch(r.kind) {
        case Kind::Join:throw std::invalid_argument("Internal CUSTOM party join has no qualified native wire encoder");
        case Kind::Kick:throw std::invalid_argument("Internal CUSTOM party kick has no qualified native wire encoder");
        case Kind::Answer:
            if(r.target>0xffffu)throw std::invalid_argument("party answer ID exceeds native WORD");
            b.push_back(0x58);word(b,static_cast<std::uint16_t>(r.target));b.push_back(r.answer);b.push_back(r.opaque);break;
        case Kind::Leave:throw std::invalid_argument("Internal CUSTOM leave has a separate self/member native exit type");
        }
        return b;
    }
    // 4EA8A0: name16,idWORD,professionBYTE,transferBYTE,HUD4,levelDWORD.
    static std::vector<std::uint8_t> preview(std::uint16_t id,const Name& name,
        std::uint8_t profession,std::uint8_t transfer,const std::array<std::uint8_t,4>& hud,std::uint32_t level) {
        std::vector<std::uint8_t> b{0x54};b.insert(b.end(),name.begin(),name.end());word(b,id);
        b.push_back(profession);b.push_back(transfer);b.insert(b.end(),hud.begin(),hud.end());dword(b,level);return b;
    }
    // 4E9BC0: idWORD,flagsBYTE,leaderBYTE,HUD4,name16. Self excluded from other roster.
    static std::vector<std::uint8_t> member(std::uint16_t id,const Name& name,
        bool leader,const std::array<std::uint8_t,4>& hud) {
        std::vector<std::uint8_t> b{0x55};word(b,id);b.push_back(0);b.push_back(leader?1:0);
        b.insert(b.end(),hud.begin(),hud.end());b.insert(b.end(),name.begin(),name.end());return b;
    }
    static std::vector<std::uint8_t> remove(std::uint16_t id,const Name& name) {
        std::vector<std::uint8_t> b{0x57};word(b,id);b.insert(b.end(),name.begin(),name.end());return b;
    }
    static std::vector<std::uint8_t> position(std::uint16_t id,std::uint16_t x,std::uint16_t y) {
        std::vector<std::uint8_t> b{0x56};word(b,id);word(b,x);word(b,y);return b;
    }
    static std::vector<std::uint8_t> vitals(std::uint16_t id,std::uint64_t hp,std::uint64_t maxhp,
        std::uint64_t mp,std::uint64_t maxmp) {
        // 4E9AD0 ->4E9990 reads HP at+4 and maximum HP at+12;
        // 4E9A30 reads MP at+8 and maximum MP at+16.
        constexpr auto native_max=std::numeric_limits<std::uint32_t>::max();
        if(hp>native_max || maxhp>native_max || mp>native_max || maxmp>native_max)
            throw std::invalid_argument("Party resources exceed native DWORD");
        std::vector<std::uint8_t> b{0x58};word(b,id);word(b,0);
        dword(b,static_cast<std::uint32_t>(hp));dword(b,static_cast<std::uint32_t>(mp));
        dword(b,static_cast<std::uint32_t>(maxhp));dword(b,static_cast<std::uint32_t>(maxmp));return b;
    }
};
}
