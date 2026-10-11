#pragma once
#include "protocol/RecoveredPkRelativeView.h"
#include "protocol/RecoveredWorldRecords.h"
#include "game/Battle.h"
#include <map>
namespace god2 {
// CUSTOM-0086 native35 selection -> owned explicit server policy -> canonical
// action. Format/selection bridge only; caller owns Session/turn authorization.
// No default skills, damage formula, player stats or selected-byte grants.
struct RecoveredPkCommandSelection {
    enum class TargetMode { OneOpponent, Sequence, AllLivingOpponents };
    struct Skill {
        BattleAction parameters;
        TargetMode target_mode;
        std::uint8_t target_limit;
    };
    struct Policy {
        std::uint8_t client_actor,client_side;
        std::uint32_t context;
        BattleAction basic;
        std::map<std::uint16_t,Skill> owned_attack_skills;
    };
    struct Selected {BattleAction action;std::optional<std::uint16_t> skill_key;};
    static std::optional<Selected> select(const BattleSnapshot& state,std::uint8_t viewer,
        const Policy& policy,std::span<const RecoveredWorldRecords::Record> records){
        if(viewer>1||policy.client_actor!=0||policy.client_side>1||state.state!=BattleState::Active||
           !state.actors[14*viewer]||!state.actors[14*viewer]->hp||records.empty())return {};
        const auto source=static_cast<std::uint8_t>(14*viewer);
        std::optional<Selected> selected;
        std::optional<RecoveredSkillCommand::Record> first;
        const Skill* skill_policy=nullptr;
        std::size_t count=0;
        bool continuation=false;
        const auto owned_header=[&](const auto& r){
            return r.actor_position==policy.client_actor&&r.side_flag==policy.client_side&&r.context_storage==policy.context;
        };
        const auto targets=[&](std::array<std::uint16_t,2> local)->bool{
            if(((local[0]|local[1])&0xc000)||!selected)return false;
            const auto canonical=RecoveredPkRelativeView::masks(local,viewer);
            for(unsigned side=0;side<2;++side)for(unsigned slot=0;slot<14;++slot)if(canonical[side]&(1u<<slot)){
                const auto target=static_cast<std::uint8_t>(14*side+slot);
                if(side==viewer||!state.actors[target]||!state.actors[target]->hp||
                   std::find(selected->action.targets.begin(),selected->action.targets.end(),target)!=selected->action.targets.end())return false;
                selected->action.targets.push_back(target);
            }
            return true;
        };
        for(const auto& record:records){
            if(std::holds_alternative<RecoveredWorldRecords::Tick>(record)){
                if(continuation)return {};continue;
            }
            if(const auto* basic=std::get_if<RecoveredBattleCommand::BasicAttackRequest>(&record)){
                if(selected||!owned_header(*basic))return {};
                selected=Selected{policy.basic,{}};selected->action.source=source;selected->action.targets.clear();
                if(!targets(basic->target_masks)||selected->action.targets.size()!=1)return {};
                continue;
            }
            const auto* skill=std::get_if<RecoveredSkillCommand::Record>(&record);
            // Kind3 healing/revival is a separate operation; never run it as
            // a damaging attack. Kind2 dependent grammar is still unresolved.
            if(!skill||skill->selection_kind_byte>1||!skill->selection_id_byte||!owned_header(*skill)||
               ++count>RecoveredSkillCommand::max_sequence_records)return {};
            const auto key=static_cast<std::uint16_t>((std::uint16_t{skill->selection_kind_byte}<<8)|skill->selection_id_byte);
            if(!first){
                if(selected)return {};
                const auto at=policy.owned_attack_skills.find(key);
                if(at==policy.owned_attack_skills.end()||!at->second.target_limit||at->second.target_limit>14)return {};
                if(at->second.target_mode!=TargetMode::OneOpponent&&at->second.target_mode!=TargetMode::Sequence&&
                   at->second.target_mode!=TargetMode::AllLivingOpponents)return {};
                skill_policy=&at->second;first=*skill;
                selected=Selected{skill_policy->parameters,key};selected->action.source=source;selected->action.targets.clear();
            }else if(!continuation||!RecoveredSkillCommand::same_sequence(*first,*skill))return {};
            if(skill_policy->target_mode==TargetMode::AllLivingOpponents){
                // The current native parser scopes this full14-bit producer
                // grammar to owned CUSTOM0/150. Do not widen arbitrary skills.
                if(key!=150||count!=1||skill->continuation||skill->target_masks!=std::array<std::uint16_t,2>{0,0x3fff})return {};
                for(unsigned slot=14*(1-viewer);slot<14*(2-viewer);++slot)
                    if(state.actors[slot]&&state.actors[slot]->hp)selected->action.targets.push_back(static_cast<std::uint8_t>(slot));
                if(selected->action.targets.empty())return {};
            }else{
                const auto before=selected->action.targets.size();
                if(!targets(skill->target_masks)||selected->action.targets.size()!=before+1)return {};
                if(skill_policy->target_mode==TargetMode::OneOpponent&&(count!=1||skill->continuation))return {};
            }
            if(selected->action.targets.size()>skill_policy->target_limit)return {};
            continuation=skill->continuation;
        }
        // A final continuation or mixed/control records do not form an action.
        // The ordered dispatcher must process genuine0B/action2 separately;
        // no receipt, turn advance, timeout defense or terminal meaning guessed.
        if(!selected||continuation||selected->action.targets.empty())return {};
        return selected;
    }
};
}
