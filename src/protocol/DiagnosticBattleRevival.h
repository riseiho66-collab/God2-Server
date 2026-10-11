#pragma once
#include "protocol/DiagnosticBattleParticipants.h"
#include "protocol/RecoveredWorldFrame.h"
#include "game/RevivalRecovery.h"
#include <limits>

namespace god2 {
// CUSTOM-0017: explicit diagnostic ownership, not native starter skill policy.
inline std::array<std::uint8_t,23> diagnostic_revival_skill_seed() {
    auto records=diagnostic_battle_skill_seed();
    records[21]=3;records[22]=8;
    return records;
}
// CUSTOM-0017: isolated three-actor setup. Ally appearance and batch ordering
// remain diagnostic candidates, not a live-qualified party bootstrap.
inline std::vector<std::uint8_t> diagnostic_revival_participants(
        std::uint64_t identity,const BattleSnapshot& state) {
    if(!identity || identity>0x3fff || !state.id || !state.revision ||
       state.state!=BattleState::Active || state.victorious_side)
        throw std::invalid_argument("Revival bootstrap requires active owned battle");
    for(unsigned slot=0;slot<28;++slot) {
        const bool expected=slot==0 || slot==1 || slot==14;
        if(bool(state.actors[slot])!=expected ||
           (expected && state.actors[slot]->position!=slot))
            throw std::invalid_argument("Revival bootstrap requires positions 0,1,14");
    }
    const auto& caster=*state.actors[0];
    if(caster.controller!=identity || !caster.hp || !state.actors[14]->hp)
        throw std::invalid_argument("Revival bootstrap requires living caster and enemy");
    const auto actor=[&](std::uint8_t slot) {
        const auto& value=*state.actors[slot];
        if(!value.max_hp || value.hp>value.max_hp || value.mp>value.max_mp ||
           (slot==14 && (value.controller || value.mp || value.max_mp)))
            throw std::invalid_argument("Invalid revival bootstrap resources");
        RecoveredBattleIdentity::Bytes name{};
        name[0]=0x1c;name[1]=slot;name[6]=4;name[7]=1;name[9]=1;
        if(slot==0) {
            name[3]=static_cast<std::uint8_t>(identity);
            name[4]=static_cast<std::uint8_t>(identity>>8);name[6]=0x20;
        }
        RecoveredBattleVitals::Bytes hp{};hp[0]=0x86;hp[2]=slot;
        const auto maximum=RecoveredBattleBootstrap::native_hp_dword(value.max_hp);
        const auto current=RecoveredBattleBootstrap::native_hp_dword(value.hp);
        for(unsigned i=0;i<4;++i) {
            hp[5+i]=static_cast<std::uint8_t>(maximum>>(8*i));
            hp[9+i]=static_cast<std::uint8_t>(current>>(8*i));
        }
        return RecoveredBattleBootstrap::Actor{*RecoveredBattleIdentity::parse_logical(name),
            *RecoveredBattleVitals::parse_logical(hp),slot<14 ?
            RecoveredBattleVitals::parse_logical(diagnostic_battle_mp(slot,value.mp,value.max_mp)) : std::nullopt};
    };
    const std::array actors{actor(0),actor(1),actor(14)};
    RecoveredBattleVitalsBatch::Bytes bulk{};bulk[0]=0x88;
    for(unsigned slot=0;slot<2;++slot) {
        const auto hp=RecoveredBattleBootstrap::native_hp_dword(state.actors[slot]->hp);
        for(unsigned i=0;i<4;++i) {
            bulk[5+slot*8+i]=static_cast<std::uint8_t>(hp>>(8*i));
            bulk[9+slot*8+i]=static_cast<std::uint8_t>(state.actors[slot]->mp>>(8*i));
        }
    }
    std::array<std::uint8_t,17> grant{};grant[0]=0x86;grant[1]=5;grant[3]=1;
    auto logical=RecoveredBattleBootstrap::ready_logical(0,0,actors,
        *RecoveredBattleVitalsBatch::parse_logical(bulk),grant);
    logical.erase(logical.begin(),logical.begin()+9);
    std::array<std::uint8_t,17> appearance{};
    appearance[0]=0x86;appearance[1]=4;appearance[3]=1;
    std::copy_n(RecoveredWorldEntry::historical_body.begin()+12,8,appearance.begin()+4);
    logical.insert(logical.begin(),appearance.begin(),appearance.end());
    return logical;
}
// CUSTOM-0017: receipt-complete continuation of the isolated revival battle.
// This projects state; it neither rearms the service nor authorizes a new action.
inline std::vector<std::uint8_t> diagnostic_revival_resume_participants(
        std::uint64_t identity,const RevivalRecovery& recovery) {
    if(recovery.version!=1 || !recovery.account || recovery.character!=identity ||
       !recovery.initial_control_received || !recovery.opening_received ||
       !recovery.action_received || !recovery.control_received || !recovery.opening_notice ||
       recovery.battle.snapshot.revision<4 ||
       recovery.battle.snapshot.revision>=std::numeric_limits<std::uint64_t>::max()-1)
        throw std::invalid_argument("Revival resume requires qualified receipt-complete phase");
    (void)Battle::restore(recovery.battle);
    const auto& enemy=recovery.battle.snapshot.actors[14];
    if(!enemy || !enemy->hp) throw std::invalid_argument("Revival resume requires living enemy");
    const std::array<BattleActor,3> expected{{
        {0,identity,100,120,14,80,31,40,8,10},
        {1,0,1,120,5,20,31,40,8,10},{14,0,enemy->hp,150,0,0,20,25,13,6}}};
    for(const auto& actor:expected)
        if(recovery.battle.snapshot.actors[actor.position]!=std::optional<BattleActor>{actor})
            throw std::invalid_argument("Revival resume differs from qualified three-actor snapshot");
    return diagnostic_revival_participants(identity,recovery.battle.snapshot);
}
// CUSTOM-0017: qualified operand layout, pending full native animation acceptance.
inline std::vector<std::uint8_t> diagnostic_revival_death_setup(
        std::uint64_t identity,Battle& battle,const Battle::Rule& rule) {
    const auto& initial=battle.inspect();
    if(!initial.actors[1] || initial.actors[1]->hp!=4 || initial.actors[1]->max_hp!=120)
        throw std::invalid_argument("Revival death setup requires living HP4 ally");
    auto staged=battle;
    auto logical=diagnostic_revival_participants(identity,initial);
    // Initial grant precedes actions, as in the qualified ordinary battle path.
    const auto damage=staged.act(0,initial.revision,{14,{1},false,100,100,0,0,150},rule,
        [](const BattleSnapshot& state,const BattleActionResult& result) {
            if(result.source!=14 || result.hits.size()!=1 || result.hits[0].target!=1 ||
               result.hits[0].hp_loss!=4 || state.actors[1]->hp || !state.actors[0]->hp ||
               state.state!=BattleState::Active)
                throw std::invalid_argument("Revival prelude did not produce isolated ally defeat");
            // First queued action uses group0; group1 is a subsequent exchange.
            const auto effect=diagnostic_battle_basic_animation(14,1,4,0,false);
            RecoveredBattleVitals::Bytes hp{};hp[0]=0x86;hp[2]=1;hp[5]=120;
            std::vector<std::uint8_t> bytes(effect.begin(),effect.end());
            bytes.insert(bytes.end(),hp.begin(),hp.end());
            return bytes;
        });
    logical.insert(logical.end(),damage.begin(),damage.end());
    // Match the qualified enemy-action tail: updated cycle snapshot after effects.
    RecoveredBattleVitalsBatch::Bytes settled{};settled[0]=0x88;
    for(unsigned slot=0;slot<2;++slot) {
        const auto hp=RecoveredBattleBootstrap::native_hp_dword(staged.inspect().actors[slot]->hp);
        for(unsigned i=0;i<4;++i) {
            settled[5+slot*8+i]=static_cast<std::uint8_t>(hp>>(8*i));
            settled[9+slot*8+i]=static_cast<std::uint8_t>(staged.inspect().actors[slot]->mp>>(8*i));
        }
    }
    logical.insert(logical.end(),settled.begin(),settled.end());
    battle=std::move(staged);
    return logical;
}

inline std::array<std::uint8_t,15> diagnostic_revival_effect(std::uint8_t source,std::uint8_t target) {
    if(source!=0 || target==0 || target>=14)
        throw std::invalid_argument("Revival probe requires source0 and friendly target1..13");
    std::array<std::uint8_t,15> result{0x83,3,source};
    const auto mask=1u<<target;
    result[5]=static_cast<std::uint8_t>(mask);result[6]=static_cast<std::uint8_t>(mask>>8);
    result[9]=1;result[11]=8;result[12]=3;result[14]=27;
    return result;
}
inline std::vector<std::uint8_t> diagnostic_revival_reply(
        const BattleSnapshot& state,const BattleRevivalResult& result) {
    if(result.source>=14 || result.target>=14 || result.hp_gain!=1 || result.mp_cost!=66 ||
       state.state!=BattleState::Active || !state.actors[result.source] || !state.actors[result.target] ||
       !state.actors[result.source]->hp || state.actors[result.target]->hp!=1)
        throw std::invalid_argument("Unqualified revival projection");
    const auto& caster=*state.actors[result.source];
    const auto& target=*state.actors[result.target];
    const auto mp=diagnostic_battle_mp(result.source,caster.mp,caster.max_mp);
    const auto effect=diagnostic_revival_effect(result.source,result.target);
    RecoveredBattleVitals::Bytes hp{};hp[0]=0x86;hp[2]=result.target;
    const auto maximum=RecoveredBattleBootstrap::native_hp_dword(target.max_hp);
    const auto current=RecoveredBattleBootstrap::native_hp_dword(target.hp);
    for(unsigned i=0;i<4;++i) {
        hp[5+i]=static_cast<std::uint8_t>(maximum>>(8*i));
        hp[9+i]=static_cast<std::uint8_t>(current>>(8*i));
    }
    std::vector<std::uint8_t> logical(mp.begin(),mp.end());
    logical.insert(logical.end(),effect.begin(),effect.end());
    logical.insert(logical.end(),hp.begin(),hp.end());
    // CUSTOM-0017: second diagnostic cycle; live acceptance remains explicit.
    RecoveredBattleVitalsBatch::Bytes bulk{};bulk[0]=0x88;bulk[1]=1;
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
}
