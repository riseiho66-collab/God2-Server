#pragma once
#include "protocol/RecoveredRemoteActor.h"
#include <stdexcept>
#include <vector>

namespace god2 {
// CUSTOM-0026: offline-qualified laboratory actor, never a persisted player.
struct DiagnosticRemoteActor {
    static std::vector<std::uint8_t> status(std::uint16_t value) {
        if(value!=1 && value && (value<0x100 || value>0x1000 || (value&(value-1))))
            throw std::invalid_argument("Remote status requires one qualified bit or clear");
        auto move=logical(1,0);
        move[5]=static_cast<std::uint8_t>(value);
        move[6]=static_cast<std::uint8_t>(value>>8);
        const std::uint32_t point=18u|(12u<<11);
        for(unsigned i=0;i<4;++i) move[9+i]=static_cast<std::uint8_t>(point>>(8*i));
        return move;
    }
    static std::vector<std::uint8_t> logical(unsigned stage,unsigned language) {
        if(stage>2 || language>1) throw std::invalid_argument("Remote actor diagnostic bounds");
        if(stage==2) return {0x73,7,0,0,0};
        if(stage==1) {
            RecoveredRemoteActorMove::LogicalRecord move{0x5e,7};
            const std::uint32_t point=19u|(12u<<11);
            for(unsigned i=0;i<4;++i) move[9+i]=static_cast<std::uint8_t>(point>>(8*i));
            return {move.begin(),move.end()};
        }
        RecoveredRemoteActor::LogicalRecord spawn{0x6f,7};
        spawn[4]=static_cast<std::uint8_t>(language<<1);
        const std::uint32_t point=2u|(18u<<2)|(12u<<17);
        for(unsigned i=0;i<4;++i) spawn[13+i]=static_cast<std::uint8_t>(point>>(8*i));
        constexpr std::array<std::uint8_t,8> components{1,0,1,0,1,0,0x81,0};
        std::copy(components.begin(),components.end(),spawn.begin()+21);
        constexpr char name[]="RemoteHero";
        std::copy(std::begin(name),std::end(name),spawn.begin()+29);
        return {spawn.begin(),spawn.end()};
    }
};
}
