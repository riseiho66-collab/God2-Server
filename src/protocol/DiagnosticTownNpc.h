#pragma once
#include <array>
#include <cstdint>
#include <stdexcept>

namespace god2 {
// CUSTOM-0020: native templates1606/1607 and appearance20; supplied test position,
// state1, direction0 and opaque zero fields are NOT recovered spawn policy.
struct DiagnosticTownNpc {
    struct Placement { std::uint32_t selector, x, y; };
    static constexpr std::array<Placement,2> guides{{{1606,110,69},{1607,112,70}}};
    static constexpr bool nearby(std::uint32_t target,std::uint32_t x,std::uint32_t y) {
        for(const auto& npc:guides)
            if(target==npc.selector && x>=npc.x-3 && x<=npc.x+3 && y>=npc.y-3 && y<=npc.y+3)
                return true;
        return false;
    }
    static std::array<std::uint8_t,21> logical(std::uint32_t selector,std::uint32_t x,std::uint32_t y) {
        if((selector!=1606 && selector!=1607) || x>=189 || y>=189)
            throw std::invalid_argument("Town NPC diagnostic outside qualified template/map bounds");
        std::array<std::uint8_t,21> record{0x72,0,0,0,0,20,0x60,0,0,1};
        record[1]=static_cast<std::uint8_t>(selector);
        record[2]=static_cast<std::uint8_t>(selector>>8);
        const auto position=(y<<17)|(x<<2);
        for(unsigned i=0;i<4;++i) record[17+i]=static_cast<std::uint8_t>(position>>(i*8));
        return record;
    }
};
}
