#pragma once
#include "game/ThousandBulls.h"
#include "protocol/DiagnosticShunyingFemaleDeity.h"
#include "protocol/ThousandBullsReply.h"
#include "game/RecordingCombatTest.h"
namespace god2 {
// CUSTOM-0059 session-only trial. Does not write learned skills or hotbars.
inline std::array<std::uint8_t,3> diagnostic_thousand_bulls_manual_selectable(){
    return {0x87,ThousandBulls::id,0x80};
}
inline std::array<std::uint8_t,4> diagnostic_thousand_bulls_manual_seed(){
    return {0x34,DiagnosticShunyingFemaleDeity::key,ThousandBulls::kind,ThousandBulls::id};
}
inline std::array<std::uint8_t,8> diagnostic_recording_skills(){
    return {0x34,DiagnosticShunyingFemaleDeity::key,0,ShunyingSanshazhan::id,
            0x34,DiagnosticShunyingFemaleDeity::key,0,ThousandBulls::id};
}
inline BattleActionResult diagnostic_recording_display(const BattleActionResult& result){
    auto display=result;
    for(auto& hit:display.hits)hit.hp_loss=RecordingCombatTest::hit;
    return display;
}
inline std::vector<std::uint8_t> diagnostic_recording_bulls_reply(const BattleSnapshot& state,
        const BattleActionResult& result,std::uint32_t cycle){
    // Explicit paired test-client contract: native signed16 cannot hold39996.
    // Send the per-hit9999 token; test-client config expands to four9999 hits.
    // Authoritative HP/death/cost are still settled once by the server.
    return thousand_bulls_reply(state,diagnostic_recording_display(result),cycle);
}
}
