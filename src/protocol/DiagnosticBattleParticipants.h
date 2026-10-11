#pragma once
#include "protocol/RecoveredBattleBootstrap.h"
#include "protocol/RecoveredBattleExperience.h"
#include "protocol/RecoveredRoleProgress.h"
#include "protocol/RecoveredRoleLevel.h"
#include "protocol/RecoveredWorldEntry.h"
#include "game/Battle.h"
#include "game/ExtendedHealthAmount.h"

namespace god2 {
// CUSTOM-0013: synthetic level1/base10/max120/80, opaque zeros. No stat growth.
inline RecoveredRoleLevel::Bytes diagnostic_role_level_seed() {
    RecoveredRoleLevel::Bytes bytes{};bytes[0]=0x22;bytes[1]=1;
    for(const auto offset:{5,7,9,11}) bytes[offset]=10;
    bytes[17]=120;bytes[21]=80;
    return bytes;
}
// CUSTOM-0012: isolated empty companion and opaque zeros; 2500 is a display sentinel,
// not XP/threshold arithmetic. Never use this fixture as a production snapshot.
inline RecoveredRoleProgress::Bytes diagnostic_role_progress(std::uint64_t hp,std::uint32_t mp,std::uint16_t progress=2500) {
    const auto value=ExtendedHealthAmount::from(hp);
    if(!value)throw std::invalid_argument("Unrepresentable diagnostic role HP domain");
    const auto hp32=value->native_unsigned_dword();
    if(!hp32)throw std::invalid_argument("Diagnostic role HP needs a qualified extended profile");
    RecoveredRoleProgress::Bytes bytes{};bytes[0]=RecoveredRoleProgress::opcode;
    return RecoveredRoleProgress::encode(RecoveredRoleProgress::with_role(
        *RecoveredRoleProgress::parse(bytes),*hp32,mp,progress));
}
// CUSTOM-0012: selected GOD key1 and catalog kind0/1,entry1, not official ownership.
inline std::array<std::uint8_t,23> diagnostic_battle_skill_seed(std::uint8_t kind=0) {
    if(kind>1) throw std::invalid_argument("Unqualified diagnostic skill family");
    std::array<std::uint8_t,23> records{};
    records[0]=0x30;records[1]=0xff;
    records[19]=0x34;records[20]=1;records[22]=1;
    records[21]=kind;
    return records;
}
inline std::array<std::uint8_t,3> diagnostic_battle_skill_selectable(std::uint8_t kind=0) {
    if(kind>1) throw std::invalid_argument("Unqualified diagnostic selectable family");
    return {0x87,1,static_cast<std::uint8_t>(0x80|kind)};
}
// CUSTOM-0010: diagnostic opaque zeros; native86/1 writes friendly-side MP only.
inline RecoveredBattleVitals::Bytes diagnostic_battle_mp(
        std::uint8_t position,std::uint32_t current,std::uint32_t maximum) {
    if(position>=14 || current>maximum)
        throw std::invalid_argument("Unqualified diagnostic MP position or bounds");
    RecoveredBattleVitals::Bytes record{};
    record[0]=0x86;record[1]=1;record[2]=position;
    for(unsigned i=0;i<4;++i) {
        record[5+i]=static_cast<std::uint8_t>(maximum>>(8*i));
        record[9+i]=static_cast<std::uint8_t>(current>>(8*i));
    }
    return record;
}
// CUSTOM-0009: known basic-action route, explicit native target outcome mapping.
inline std::array<std::uint8_t,15> diagnostic_battle_basic_animation(
        std::uint8_t source,std::uint8_t target,std::uint64_t hp_loss,std::uint8_t group=0,bool target_alive=true) {
    if(source>=28 || target>=28 || source/14==target/14 || hp_loss>0x7fff)
        throw std::invalid_argument("Diagnostic animation exceeds qualified positions/display range");
    std::array<std::uint8_t,15> record{};
    record[0]=0x83;record[1]=1;record[2]=source;
    record[3]=group;
    const auto mask=1u<<(target%14);
    record[5+2*(target/14)]=static_cast<std::uint8_t>(mask);
    record[6+2*(target/14)]=static_cast<std::uint8_t>(mask>>8);
    // Native12B48E sign-extends this WORD and formats "HP %+d".
    const auto delta=static_cast<std::uint16_t>(-static_cast<std::int32_t>(hp_loss));
    record[9]=static_cast<std::uint8_t>(delta);
    record[10]=static_cast<std::uint8_t>(delta>>8);
    // Native12C000 table171610: index28 -> state0; index0 -> death state9.
    record[12]=target_alive ? 28 : 0;
    return record;
}
// CUSTOM-0012: explicit kind0/1,id1 fixture effect, not an official skill magnitude.
inline std::array<std::uint8_t,15> diagnostic_battle_skill_animation(
        std::uint8_t source,std::uint8_t target,std::uint64_t hp_loss,std::uint8_t group=0,bool target_alive=true,std::uint8_t kind=0) {
    if(kind>1) throw std::invalid_argument("Unqualified diagnostic skill result family");
    auto record=diagnostic_battle_basic_animation(source,target,hp_loss,group,target_alive);
    record[1]=3;
    record[11]=1;
    record[12]=kind;
    record[14]=target_alive ? 28 : 0;
    return record;
}
// CUSTOM-0011: zero-award diagnostic result; opaque fields deliberately zero.
inline RecoveredBattleExperience::LogicalRecord diagnostic_battle_zero_result() {
    RecoveredBattleExperience::LogicalRecord bytes{};
    bytes[0]=RecoveredBattleExperience::opcode;
    return RecoveredBattleExperience::encode_logical(*RecoveredBattleExperience::parse_logical(bytes));
}
// CUSTOM-0012: explicit test award; native118C6F reads only the display DWORD.
inline RecoveredBattleExperience::LogicalRecord diagnostic_battle_experience_result(std::uint64_t award) {
    if(award>0x7fffffff) throw std::invalid_argument("Diagnostic EXP exceeds signed display range");
    const auto displayed=static_cast<std::uint32_t>(award); // Only after exact bound; never wrap a wide award.
    auto bytes=diagnostic_battle_zero_result();
    for(unsigned i=0;i<4;++i) bytes[5+i]=static_cast<std::uint8_t>(displayed>>(8*i));
    return bytes;
}
// CUSTOM-0009: isolated socket diagnostic, never native stats or production balance.
inline std::vector<std::uint8_t> diagnostic_battle_participants(std::uint32_t initial_mp=50,std::uint64_t initial_hp=100,std::uint64_t enemy_hp=150) {
    if(initial_hp==0 || initial_hp>120) throw std::invalid_argument("Diagnostic initial HP outside living range");
    if(initial_mp>80) throw std::invalid_argument("Diagnostic initial MP exceeds maximum");
    if(!enemy_hp || enemy_hp>150) throw std::invalid_argument("Diagnostic enemy HP outside living range");
    using Bootstrap=RecoveredBattleBootstrap;
    const auto actor=[initial_mp,initial_hp,enemy_hp](std::uint8_t position) {
        RecoveredBattleIdentity::Bytes identity{};
        identity[0]=0x1c;identity[1]=position;
        identity[6]=4;identity[7]=1;identity[9]=1;
        RecoveredBattleVitals::Bytes hp{};
        hp[0]=0x86;hp[2]=position;
        hp[5]=position ? 150 : 120;hp[9]=static_cast<std::uint8_t>(position ? enemy_hp : initial_hp);
        auto mp=hp;mp[1]=1;mp[5]=80;mp[9]=static_cast<std::uint8_t>(initial_mp);
        return Bootstrap::Actor{*RecoveredBattleIdentity::parse_logical(identity),
            *RecoveredBattleVitals::parse_logical(hp),position ? std::nullopt : RecoveredBattleVitals::parse_logical(mp)};
    };
    const std::array actors{actor(0),actor(14)};
    RecoveredBattleVitalsBatch::Bytes bulk{};
    bulk[0]=0x88;bulk[5]=static_cast<std::uint8_t>(initial_hp);bulk[9]=static_cast<std::uint8_t>(initial_mp);
    std::array<std::uint8_t,17> grant{};
    grant[0]=0x86;grant[1]=5;grant[3]=1;
    auto logical=Bootstrap::ready_logical(0,0,actors,*RecoveredBattleVitalsBatch::parse_logical(bulk),grant);
    // Transition was already sent; participants are deferred until the lab timing cue.
    logical.erase(logical.begin(),logical.begin()+9);
    return logical;
}
// CUSTOM-0009: historical world appearance is diagnostic, not recovered profile projection.
inline std::vector<std::uint8_t> diagnostic_battle_player_participants(std::uint64_t identity,std::uint32_t initial_mp=50,std::uint64_t initial_hp=100,std::uint64_t enemy_hp=150) {
    if(identity==0 || identity>0x3fff)
        throw std::invalid_argument("Diagnostic player identity exceeds world identity range");
    auto logical=diagnostic_battle_participants(initial_mp,initial_hp,enemy_hp);
    logical[3]=static_cast<std::uint8_t>(identity);
    logical[4]=static_cast<std::uint8_t>(identity>>8);
    logical[6]=0x20;
    std::array<std::uint8_t,17> appearance{};
    appearance[0]=0x86;appearance[1]=4;appearance[3]=1;
    std::copy_n(RecoveredWorldEntry::historical_body.begin()+12,8,appearance.begin()+4);
    logical.insert(logical.begin(),appearance.begin(),appearance.end());
    return logical;
}
// CUSTOM-0009: same qualified two-actor appearance template, saved resources only.
// This constructs packets, not a reconnect lease or permission to replay an action.
inline std::vector<std::uint8_t> diagnostic_battle_resume_participants(std::uint64_t identity,const BattleSnapshot& state) {
    if(!state.id || !state.revision || state.victorious_side || state.state!=BattleState::Active || !state.actors[0] || !state.actors[14])
        throw std::invalid_argument("Resume bootstrap requires active diagnostic pair");
    for(std::size_t i=0;i<state.actors.size();++i)
        if(i!=0 && i!=14 && state.actors[i]) throw std::invalid_argument("Unqualified resume participant");
    const auto& player=*state.actors[0];const auto& enemy=*state.actors[14];
    if(player.position!=0 || enemy.position!=14 || player.controller!=identity || enemy.controller || player.max_hp!=120 || player.max_mp!=80 ||
       enemy.max_hp!=150 || enemy.mp || enemy.max_mp)
        throw std::invalid_argument("Resume bootstrap differs from diagnostic resource contract");
    return diagnostic_battle_player_participants(identity,player.mp,player.hp,enemy.hp);
}
}
