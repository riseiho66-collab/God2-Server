#pragma once
#include "game/ShunyingSanshazhan.h"
#include "protocol/RecoveredBattleBootstrap.h"
#include "protocol/RecoveredBattleVitals.h"
#include "protocol/RecoveredBattleVitalsBatch.h"
#include "protocol/RecoveredWorldFrame.h"

namespace god2 {
// CUSTOM-0058 presentation contract accepted with the installed client bridge:
// native83/type3 identifies126; bridge reuses native8 hit timing and appearance.
// Each target receives one authoritative hit. Visual clones own no game state.
inline std::vector<std::uint8_t> shunying_sanshazhan_reply(const BattleSnapshot& state,
        const BattleActionResult& result,std::uint32_t cycle,bool finish_cycle=true) {
    (void)ShunyingSanshazhan::visual_assignments(result);
    if(!state.actors[result.source]) throw std::invalid_argument("Shunying caster absent");
    std::vector<std::uint8_t> logical;
    const auto append_caster_mp=[&] {
        const auto& actor=*state.actors[result.source];
        RecoveredBattleVitals::Bytes bytes{};bytes[0]=0x86;bytes[1]=1;bytes[2]=result.source;
        const auto maximum=RecoveredBattleBootstrap::native_hp_dword(actor.max_mp);
        const auto current=RecoveredBattleBootstrap::native_hp_dword(actor.mp);
        for(unsigned i=0;i<4;++i) {
            bytes[5+i]=static_cast<std::uint8_t>(maximum>>(8*i));
            bytes[9+i]=static_cast<std::uint8_t>(current>>(8*i));
        }
        logical.insert(logical.end(),bytes.begin(),bytes.end());
    };
    // Native86/1 only accepts local friendly MP. Opposing actors still pay the
    // authoritative cost; do not forge an unqualified enemy MP display record.
    if(result.source<14) append_caster_mp();
    for(const auto& hit:result.hits) {
        if(!state.actors[hit.target] || hit.hp_loss>0x7fff)
            throw std::invalid_argument("Shunying target/display range invalid");
        // Retain the native resource representation checks even though an
        // eager absolute HP record would double-apply the deferred native8 hit.
        (void)RecoveredBattleBootstrap::native_hp_dword(state.actors[hit.target]->max_hp);
        (void)RecoveredBattleBootstrap::native_hp_dword(state.actors[hit.target]->hp);
        std::array<std::uint8_t,15> bytes{};
        bytes[0]=0x83;bytes[1]=3;bytes[2]=result.source;
        const auto mask=1u<<(hit.target%14);
        const auto offset=5+2*(hit.target/14);
        bytes[offset]=static_cast<std::uint8_t>(mask);bytes[offset+1]=static_cast<std::uint8_t>(mask>>8);
        const auto delta=static_cast<std::uint16_t>(-static_cast<std::int32_t>(hit.hp_loss));
        bytes[9]=static_cast<std::uint8_t>(delta);bytes[10]=static_cast<std::uint8_t>(delta>>8);
        bytes[11]=ShunyingSanshazhan::id;bytes[12]=ShunyingSanshazhan::kind;
        bytes[14]=state.actors[hit.target]->hp?28:0;
        logical.insert(logical.end(),bytes.begin(),bytes.end());
        // 86/0 is consumed before native8's524820 hit event applies WORD28A.
        // Keep the pre-hit client HP; the single83 delta owns that timed change.
    }
    if(finish_cycle) {
        RecoveredBattleVitalsBatch::Bytes bytes{};bytes[0]=0x88;
        for(unsigned i=0;i<4;++i) bytes[1+i]=static_cast<std::uint8_t>(cycle>>(8*i));
        for(unsigned slot=0;slot<14;++slot) if(state.actors[slot]) {
            const auto hp=RecoveredBattleBootstrap::native_hp_dword(state.actors[slot]->hp);
            for(unsigned i=0;i<4;++i) {
                bytes[5+slot*8+i]=static_cast<std::uint8_t>(hp>>(8*i));
                bytes[9+slot*8+i]=static_cast<std::uint8_t>(state.actors[slot]->mp>>(8*i));
            }
        }
        logical.insert(logical.end(),bytes.begin(),bytes.end());
    }
    return RecoveredWorldFrame::encode(logical);
}
}
