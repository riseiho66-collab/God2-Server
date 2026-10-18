#pragma once
#include "protocol/DiagnosticBattleParticipants.h"
#include "game/ShunyingSanshazhan.h"
#include "game/CharacterResources.h"
#include "protocol/DiagnosticShunyingFemaleDeity.h"

namespace god2 {
// Pinned native table571AA8: friendly slot2 has ground position(507,393).
inline constexpr std::uint8_t diagnostic_shunying_manual_slot=2;
// CUSTOM-0058: exclusively an isolated manual client trial. The 10000 HP,
// combat inputs and zero MP charge are test fixtures, not skill balance.
// The isolated client bridge consumes126, presents native blade3 (kind0/id8)
// hit timing and adds borrowed current-caster visual layers for extra targets.
inline std::vector<BattleActor> diagnostic_shunying_manual_actors(std::uint64_t owner,
        const CharacterResources* resources=nullptr,std::uint8_t friendly_slot=0,std::uint64_t monster_hp=10000) {
    if(!owner || owner>0x3fff) throw std::invalid_argument("Manual trial needs qualified owner");
    if(friendly_slot>=14) throw std::invalid_argument("Invalid manual friendly slot");
    std::vector<BattleActor> actors{{friendly_slot,owner,100,120,50,80,31,40,8,10}};
    if(resources) {
        const auto legacy=resources->legacy_vitals();
        if(!legacy)
            throw std::invalid_argument("Invalid test character resources");
        actors[0].hp=(*legacy)[0];actors[0].max_hp=(*legacy)[1];
        actors[0].mp=(*legacy)[2];actors[0].max_mp=(*legacy)[3];
        // Recording fixture only; native derived attack formula remains unqualified.
        actors[0].physical_attack=666;actors[0].magical_attack=666;
    }
    for(std::uint8_t pos=14;pos<28;++pos) actors.push_back({pos,0,monster_hp,monster_hp,0,0,20,25,13,6});
    return actors;
}
inline std::array<std::uint8_t,3> diagnostic_shunying_manual_selectable() {
    return {0x87,ShunyingSanshazhan::id,0x80};
}
inline std::vector<std::uint8_t> diagnostic_shunying_manual_seed() {
    const auto base=DiagnosticShunyingFemaleDeity::learned_trial_skills();
    std::vector<std::uint8_t> out(base.begin(),base.end());
    return out;
}
inline std::vector<std::uint8_t> diagnostic_shunying_manual_participants(std::uint64_t owner,
        const RecoveredWorldEntry::Body& current_appearance,const CharacterResources* resources=nullptr,
        std::uint8_t level=1,std::uint8_t friendly_slot=0,std::uint64_t monster_hp=10000) {
    const auto prepared=diagnostic_shunying_manual_actors(owner,resources,friendly_slot,monster_hp);
    std::vector<RecoveredBattleBootstrap::Actor> actors;
    for(const auto& actor:prepared) {
        RecoveredBattleIdentity::Bytes identity{};
        identity[0]=0x1c;identity[1]=actor.position;
        identity[6]=4;identity[7]=1;identity[9]=1;
        if(actor.position==friendly_slot) {
            identity[2]=level;
            identity[3]=static_cast<std::uint8_t>(owner);identity[4]=static_cast<std::uint8_t>(owner>>8);
            identity[6]=0x20;
        }
        RecoveredBattleVitals::Bytes hp{};hp[0]=0x86;hp[2]=actor.position;
        const auto maximum=RecoveredBattleBootstrap::native_hp_dword(actor.max_hp);
        const auto current=RecoveredBattleBootstrap::native_hp_dword(actor.hp);
        for(unsigned i=0;i<4;++i) {
            hp[5+i]=static_cast<std::uint8_t>(maximum>>(i*8));
            hp[9+i]=static_cast<std::uint8_t>(current>>(i*8));
        }
        std::optional<RecoveredBattleVitals::Record> mp;
        if(actor.position==friendly_slot) mp=RecoveredBattleVitals::parse_logical(diagnostic_battle_mp(friendly_slot,actor.mp,actor.max_mp));
        actors.push_back({*RecoveredBattleIdentity::parse_logical(identity),*RecoveredBattleVitals::parse_logical(hp),mp});
    }
    RecoveredBattleVitalsBatch::Bytes bulk{};bulk[0]=0x88;
    const auto friendly_hp=RecoveredBattleBootstrap::native_hp_dword(prepared[0].hp);
    for(unsigned i=0;i<4;++i) {
        bulk[5+friendly_slot*8+i]=static_cast<std::uint8_t>(friendly_hp>>(8*i));
        bulk[9+friendly_slot*8+i]=static_cast<std::uint8_t>(prepared[0].mp>>(8*i));
    }
    std::array<std::uint8_t,17> grant{};grant[0]=0x86;grant[1]=5;grant[3]=1;
    grant[4]=friendly_slot;
    auto logical=RecoveredBattleBootstrap::ready_logical(0,255u<<8,actors,*RecoveredBattleVitalsBatch::parse_logical(bulk),grant);
    logical.erase(logical.begin(),logical.begin()+9); // entry already sent
    std::array<std::uint8_t,17> appearance{};appearance[0]=0x86;appearance[1]=4;appearance[3]=1;
    appearance[2]=friendly_slot;
    std::copy_n(current_appearance.begin()+12,8,appearance.begin()+4);
    logical.insert(logical.begin(),appearance.begin(),appearance.end());
    // Native type4 attachment must be dressed after its owner1C exists, then
    // explicitly summoned. 83 is a native queue barrier before88/grant.
    const auto deity=DiagnosticShunyingFemaleDeity::battle_components(friendly_slot);
    logical.insert(logical.begin()+96,deity.begin(),deity.end());
    const auto summon=DiagnosticShunyingFemaleDeity::battle_summon(friendly_slot);
    logical.insert(logical.end()-138,summon.begin(),summon.end());
    return logical;
}
inline std::vector<std::uint8_t> diagnostic_shunying_manual_action_reply(
        const BattleSnapshot& state,const BattleActionResult& result,std::uint32_t cycle,bool skill) {
    if(result.source>=state.actors.size() || !state.actors[result.source])
        throw std::invalid_argument("Manual caster absent");
    if(skill) (void)ShunyingSanshazhan::visual_assignments(result); // validate, NOT render clones
    else if(result.hits.size()!=1) throw std::invalid_argument("Manual basic action needs one target");
    std::vector<std::uint8_t> logical;
    for(const auto& hit:result.hits) {
        if(hit.target>=state.actors.size() || !state.actors[hit.target])
            throw std::invalid_argument("Manual hit target absent");
        const auto& target=*state.actors[hit.target];
        auto animation=skill ?
            diagnostic_battle_skill_animation(result.source,hit.target,hit.hp_loss,0,target.hp>0,0) :
            diagnostic_battle_basic_animation(result.source,hit.target,hit.hp_loss,0,target.hp>0);
        if(skill) animation[11]=ShunyingSanshazhan::id; // client captures126 then uses native8 events
        logical.insert(logical.end(),animation.begin(),animation.end());
        // BASIC522FB0 and126/native8 both apply the signed amount on their
        // native hit. Keep resource projection guards without an eager HP86.
        (void)RecoveredBattleBootstrap::native_hp_dword(target.max_hp);
        (void)RecoveredBattleBootstrap::native_hp_dword(target.hp);
    }
    RecoveredBattleVitalsBatch::Bytes bulk{};bulk[0]=0x88;
    for(unsigned i=0;i<4;++i) bulk[1+i]=static_cast<std::uint8_t>(cycle>>(i*8));
    for(unsigned slot=0;slot<14;++slot) if(state.actors[slot]) {
        const auto hp=RecoveredBattleBootstrap::native_hp_dword(state.actors[slot]->hp);
        for(unsigned i=0;i<4;++i) {
            bulk[5+slot*8+i]=static_cast<std::uint8_t>(hp>>(8*i));
            bulk[9+slot*8+i]=static_cast<std::uint8_t>(state.actors[slot]->mp>>(8*i));
        }
    }
    logical.insert(logical.end(),bulk.begin(),bulk.end());
    return RecoveredWorldFrame::encode(logical);
}
inline std::vector<std::uint8_t> diagnostic_shunying_manual_reply(
        const BattleSnapshot& state,const BattleActionResult& result,std::uint32_t cycle) {
    return diagnostic_shunying_manual_action_reply(state,result,cycle,true);
}
inline std::vector<std::uint8_t> diagnostic_shunying_manual_basic_reply(
        const BattleSnapshot& state,const BattleActionResult& result,std::uint32_t cycle) {
    // A basic click consumes a turn too. Native88 clears its control latch;
    // the next86/5 still waits for the actual0B, just like custom skill casts.
    return diagnostic_shunying_manual_action_reply(state,result,cycle,false);
}
}
