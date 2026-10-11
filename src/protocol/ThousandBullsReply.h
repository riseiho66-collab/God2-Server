#pragma once
#include "game/ThousandBulls.h"
#include "protocol/RecoveredBattleBootstrap.h"
#include "protocol/RecoveredBattleVitals.h"
#include "protocol/RecoveredBattleVitalsBatch.h"
#include "protocol/RecoveredWorldFrame.h"

namespace god2 {
// CUSTOM-0059: ONE authoritative83/type3 total per target, never four copies
// of the action. The installed150 bridge presents the exact total in four
// phases. This preserves native14-target storage and charges MP exactly once.
inline std::vector<std::uint8_t> thousand_bulls_reply(const BattleSnapshot& state,
        const BattleActionResult& result,std::uint32_t cycle,bool finish_cycle=true) {
    ThousandBulls::validate_result(result);
    if(!state.actors[result.source])throw std::invalid_argument("ThousandBulls caster absent");
    std::vector<std::uint8_t> logical;
    const auto append_caster_mp=[&](std::uint8_t slot) {
        const auto& actor=*state.actors[slot];
        RecoveredBattleVitals::Bytes bytes{};bytes[0]=0x86;bytes[1]=1;bytes[2]=slot;
        const auto maximum=actor.max_mp,current=actor.mp;
        for(unsigned i=0;i<4;++i){bytes[5+i]=static_cast<std::uint8_t>(maximum>>(8*i));bytes[9+i]=static_cast<std::uint8_t>(current>>(8*i));}
        logical.insert(logical.end(),bytes.begin(),bytes.end());
    };
    if(result.source<14)append_caster_mp(result.source);
    for(const auto& hit:result.hits) {
        if(!state.actors[hit.target] || hit.hp_loss>0x7fff)
            throw std::invalid_argument("ThousandBulls native display range invalid");
        std::array<std::uint8_t,15> bytes{};bytes[0]=0x83;bytes[1]=3;bytes[2]=result.source;
        const auto mask=1u<<(hit.target%14);
        const unsigned offset=5+2*(hit.target/14);
        bytes[offset]=static_cast<std::uint8_t>(mask);bytes[offset+1]=static_cast<std::uint8_t>(mask>>8);
        const auto delta=static_cast<std::uint16_t>(-static_cast<std::int32_t>(hit.hp_loss));
        bytes[9]=static_cast<std::uint8_t>(delta);bytes[10]=static_cast<std::uint8_t>(delta>>8);
        bytes[11]=ThousandBulls::id;bytes[12]=ThousandBulls::kind;bytes[14]=state.actors[hit.target]->hp?28:0;
        logical.insert(logical.end(),bytes.begin(),bytes.end());
        // Native86 HP updates DE8 immediately, before the150 timeline, and
        // would apply final HP before our four83-derived visual deltas. Keep
        // the initial HP until those phases; native88 waits on action barrier.
    }
    if(finish_cycle){
        RecoveredBattleVitalsBatch::Bytes bytes{};bytes[0]=0x88;
        for(unsigned i=0;i<4;++i)bytes[1+i]=static_cast<std::uint8_t>(cycle>>(8*i));
        for(unsigned slot=0;slot<14;++slot)if(state.actors[slot]){
            const auto hp=RecoveredBattleBootstrap::native_hp_dword(state.actors[slot]->hp);
            for(unsigned i=0;i<4;++i){
                bytes[5+slot*8+i]=static_cast<std::uint8_t>(hp>>(8*i));
                bytes[9+slot*8+i]=static_cast<std::uint8_t>(state.actors[slot]->mp>>(8*i));
            }
        }
        logical.insert(logical.end(),bytes.begin(),bytes.end());
    }
    return RecoveredWorldFrame::encode(logical);
}
}
