#pragma once
#include "db/SqliteFruitQuestRepository.h"
#include "db/DbTypes.h"
#include "game/FruitVillageQuestRules.h"
#include "net/Session.h"
#include "protocol/RecoveredWorldRecords.h"
#include "protocol/RecoveredQuestDialogue.h"
#include "protocol/RecoveredQuestRewardNotice.h"
#include "protocol/RecoveredInventoryProjection.h"
#include <map>
#include <spdlog/spdlog.h>
namespace god2 {
// CUSTOM-0051. Transactional inferred collection rules; source-hint placement
// and direction zero are isolated opt-in data, not original spawn authority.
class RecoveredFruitQuests {
    struct Pending {
        std::uint32_t mission;std::uint16_t request;std::uint8_t context;std::optional<InferredQuestRules::Action> action;
        SqliteFruitQuestRepository::View expected;
    };
    SqliteFruitQuestRepository& repository_;
    std::map<std::uint64_t,Pending> pending_;
    std::map<std::uint64_t,std::uint32_t> sequence_;
public:
    explicit RecoveredFruitQuests(SqliteFruitQuestRepository& repository):repository_(repository){}
    void remove(std::uint64_t session){pending_.erase(session);sequence_.erase(session);}
    static bool material(std::uint16_t key){return key==5098 || key==5091 || key==3464;}
    static bool nearby(const FruitVillageQuestRules::Descriptor& d,const RecoveredPosition& p){
        return p.area==13 && p.scene==12 && p.x+3>=d.source_x && p.x<=d.source_x+3 &&
            p.y+3>=d.source_y && p.y<=d.source_y+3;
    }
    // An engaged empty result means the frame was rejected with no mutation.
    std::optional<std::vector<std::uint8_t>> handle(Session& session,
        std::span<const RecoveredWorldRecords::Record> records,const std::optional<RecoveredPosition>& position) {
        const RecoveredWorldRecords::Record* action=nullptr;bool relevant=false,mixed=false;
        for(const auto& r:records){
            const bool candidate=std::holds_alternative<RecoveredNpcInteraction::Request>(r) ||
                std::holds_alternative<RecoveredQuestAction::Request>(r) || std::holds_alternative<RecoveredQuestClose::Request>(r);
            if(candidate){relevant=true;if(action)mixed=true;action=&r;}
            else if(!std::holds_alternative<RecoveredWorldRecords::Tick>(r))mixed=true;
        }
        if(!relevant)return std::nullopt;
        const auto empty=[](){return std::optional<std::vector<std::uint8_t>>(std::vector<std::uint8_t>{});};
        if(mixed || !action || !position || !session.recovered_world_ready() || session.state()==SessionState::InBattle)return empty();
        if(std::holds_alternative<RecoveredQuestClose::Request>(*action)){pending_.erase(session.id());return empty();}
        if(const auto* npc=std::get_if<RecoveredNpcInteraction::Request>(action)){
            const FruitVillageQuestRules::Descriptor* d=nullptr;
            for(const auto& row:FruitVillageQuestRules::descriptors)if(row.npc_catalog==npc->raw_target)d=&row;
            if(!d || !nearby(*d,*position))return empty();
            auto view=repository_.load(session.account_id,session.character_id,d->mission_id);
            const auto rule=*FruitVillageQuestRules::rule(d->mission_id);
            std::uint32_t text=d->idle_before;std::optional<InferredQuestRules::Action> operation;
            const auto progress=view.snapshot.quests.find(d->mission_id);
            if(progress==view.snapshot.quests.end()){
                if(InferredQuestRules::plan_accept(rule,view.snapshot,view.snapshot.owner)){text=d->offer;operation=InferredQuestRules::Action::Accept;}
            } else if(progress->second.phase==InferredQuestRules::Phase::Completed)text=d->idle_after;
            else if(InferredQuestRules::plan_submit(rule,view.snapshot,view.snapshot.owner)){text=d->completion;operation=InferredQuestRules::Action::Submit;}
            else text=d->incomplete;
            auto& word=sequence_[session.id()];if(word>=255)return empty();++word;
            const auto logical=RecoveredQuestDialogue::mode1(d->npc_catalog,2,word,text,14600);
            if(!logical)throw DatabaseError("Fruit dialogue source selector rejected");
            auto wire=RecoveredWorldFrame::encode(*logical);
            pending_.insert_or_assign(session.id(),Pending{d->mission_id,d->npc_catalog,static_cast<std::uint8_t>(word),operation,std::move(view)});
            spdlog::info("FRUIT_QUEST_DIALOGUE character_id={} mission={} text={} request={} CUSTOM-0051",session.character_id,d->mission_id,text,word);
            return wire;
        }
        const auto& request=std::get<RecoveredQuestAction::Request>(*action);
        const auto found=pending_.find(session.id());
        if(found==pending_.end() || request.request_word!=found->second.request || request.reply_word!=2 || request.context_byte!=found->second.context)return empty();
        auto pending=found->second;pending_.erase(found);
        if(!nearby(*FruitVillageQuestRules::find(pending.mission),*position) || !pending.action)return empty();
        std::vector<std::uint8_t> wire;
        const auto prepare=[&](const SqliteFruitQuestRepository::Commit& c){
            auto logical=c.journal_logical;
            for(const auto& change:c.changed_bags){
                RecoveredInventoryProjection::Metadata metadata{};
                if(change.after.instance)metadata=*change.after.instance;
                else {metadata[0]=static_cast<std::uint8_t>(change.after.item);metadata[1]=static_cast<std::uint8_t>(change.after.item>>8);}
                const auto slot=RecoveredInventoryProjection::encode({change.slot,static_cast<std::uint8_t>(change.after.count),metadata});
                if(!slot)throw DatabaseError("Fruit bag projection rejected");logical.insert(logical.end(),slot->begin(),slot->end());
            }
            for(const auto [kind,amount]:{std::pair{RecoveredQuestRewardNotice::Kind::Experience,c.experience_delta},std::pair{RecoveredQuestRewardNotice::Kind::Reputation,c.reputation_delta}})
                if(amount){const auto notice=RecoveredQuestRewardNotice::logical(kind,amount);logical.insert(logical.end(),notice.begin(),notice.end());}
            wire=RecoveredWorldFrame::encode(logical);
        };
        if(*pending.action==InferredQuestRules::Action::Accept)repository_.accept(session.account_id,session.character_id,pending.mission,pending.expected,prepare);
        else repository_.submit(session.account_id,session.character_id,pending.mission,pending.expected,prepare);
        spdlog::info("FRUIT_QUEST_COMMITTED character_id={} mission={} action={} CUSTOM-0051",session.character_id,pending.mission,*pending.action==InferredQuestRules::Action::Accept?"accept":"submit");
        return wire;
    }
};
}
