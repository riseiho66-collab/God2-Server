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
// Native497140/497170/497230/4971B0 producers. Direction-qualified:
// C2S58 is the party preview answer; unrelated S2C58 carries saved vitals.
struct RecoveredParty {
    enum class Kind {Join,Answer,Kick,Leave};
    using Name=std::array<std::uint8_t,16>;
    struct Request {
        Kind kind;std::uint32_t self{},target{};std::uint8_t answer{},opaque{};Name name{};
        bool operator==(const Request&) const=default;
    };
    static constexpr std::size_t size(std::uint8_t opcode) noexcept {
        switch(opcode){case 0x6a:return 9;case 0x57:case 0x58:return 5;case 0x5a:return 19;default:return 0;}
    }
    static std::optional<Request> decode(std::span<const std::uint8_t> b) {
        if(b.empty() || !size(b[0]) || b.size()!=size(b[0]))return {};
        const auto dword=[&](unsigned at){return std::uint32_t{b[at]}|(std::uint32_t{b[at+1]}<<8)|
            (std::uint32_t{b[at+2]}<<16)|(std::uint32_t{b[at+3]}<<24);};
        if(b[0]==0x6a)return Request{Kind::Join,dword(1),dword(5)};
        if(b[0]==0x57)return Request{Kind::Kick,0,dword(1)};
        if(b[0]==0x58)return Request{Kind::Answer,0,std::uint32_t{b[1]}|(std::uint32_t{b[2]}<<8),b[3],b[4]};
        Request r{Kind::Leave,std::uint32_t{b[1]}|(std::uint32_t{b[2]}<<8)};
        std::copy_n(b.begin()+3,16,r.name.begin());return r;
    }
    static void word(std::vector<std::uint8_t>& b,std::uint16_t n){b.push_back(static_cast<std::uint8_t>(n));b.push_back(static_cast<std::uint8_t>(n>>8));}
    static void dword(std::vector<std::uint8_t>& b,std::uint32_t n){for(unsigned i=0;i<4;++i)b.push_back(static_cast<std::uint8_t>(n>>(8*i)));}
    static std::vector<std::uint8_t> encode(const Request& r) {
        std::vector<std::uint8_t> b;
        switch(r.kind) {
        case Kind::Join:b.push_back(0x6a);dword(b,r.self);dword(b,r.target);break;
        case Kind::Kick:b.push_back(0x57);dword(b,r.target);break;
        case Kind::Answer:
            if(r.target>0xffffu)throw std::invalid_argument("party answer ID exceeds native WORD");
            b.push_back(0x58);word(b,static_cast<std::uint16_t>(r.target));b.push_back(r.answer);b.push_back(r.opaque);break;
        case Kind::Leave:
            if(r.self>0xffffu)throw std::invalid_argument("party leave ID exceeds native WORD");
            b.push_back(0x5a);word(b,static_cast<std::uint16_t>(r.self));b.insert(b.end(),r.name.begin(),r.name.end());break;
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
