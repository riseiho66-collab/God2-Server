#pragma once
#include "game/Battle.h"

namespace god2 {
// CUSTOM-0012: bounded replay of the explicit three-round test policy.
// This validates saved core state, not client reconnect receipt admission.
inline void validate_diagnostic_exchange(const BattleCheckpoint& saved,
        std::uint64_t character,unsigned completed_exchanges,const Battle::Rule& rule) {
    if(!character || !saved.snapshot.id || !rule ||
       completed_exchanges<1 || completed_exchanges>2)
        throw std::invalid_argument("Missing diagnostic recovery authority");
    const std::array<BattleActor,2> actors{{
        {0,character,100,120,50,80,31,40,8,10},
        {14,0,150,150,0,0,20,25,13,6}}};
    Battle expected(saved.snapshot.id,actors,123);
    // No wire transmission or persistence during deterministic validation.
    const Battle::Encode sink=[](const auto&,const auto&){return std::vector<std::uint8_t>{1};};
    for(unsigned exchange=0;exchange<completed_exchanges;++exchange) {
        expected.act(character,expected.inspect().revision,{0,{14},true,150,100,8,0,150},rule,sink);
        expected.act(0,expected.inspect().revision,{14,{0},false,100,100,0,0,150},rule,sink);
    }
    if(expected.checkpoint()!=saved)
        throw std::invalid_argument("Diagnostic exchange checkpoint differs");
}

inline void validate_diagnostic_first_exchange(const BattleCheckpoint& saved,
        std::uint64_t character,const Battle::Rule& rule) {
    validate_diagnostic_exchange(saved,character,1,rule);
}
}
