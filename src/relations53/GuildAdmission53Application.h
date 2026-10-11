#pragma once
#include "GuildJoinConversation53Runtime.h"
#include "SharedGuildCoordinator53Draft.h"
#include "handlers/OwnedGuildEntryService.h"
#include "handlers/OwnedGuildPanelService.h"
#include "protocol/RecoveredTrade.h"
#include "protocol/RecoveredWorldRecords.h"

namespace god2 {
// Native 7A menu ->85 choice ->8D prompt ->6F create/apply. The menu placement,
// lease, cost and capacity remain explicitly CUSTOM0078/83. GAME confined.
class GuildAdmission53Application:public std::enable_shared_from_this<GuildAdmission53Application> {
public:
    using Service=GuildJoinConversation53Service;using Runtime=GuildJoinConversation53Runtime;
    using Common=SharedGuildCoordinator53Draft;using Records=RecoveredWorldRecords;
    using Send=Common::Send;
    struct Captured {Runtime::Batch requests;std::optional<OwnedGuildEntryService::Lease> choice;};
    GuildAdmission53Application(std::shared_ptr<Common> common,Common::Neighboring& repo,
        Common::Neighboring::Original& original,Succession53ReaderDraft& effective,
        SqliteRecoveredCharacterRepository& profiles,Service::ActorReady ready,Service::ReadWallet wallet,Service::Rule rule)
      :common_(std::move(common)),entry_([this](auto id){return common_->owner(id);},
        [&original](const auto& owner)->std::optional<Common::Neighboring::Original::Identity>{
            if(original.pending(owner.account,owner.character))return {};
            return original.nonmember(owner.account,owner.character);
        }),
        service_(repo,original,effective,profiles,
            [this](auto id)->std::optional<Service::Interaction>{
                const auto at=interactions_.find(id);if(at==interactions_.end()||common_->owner(id)!=std::optional{at->second.owner})return {};return at->second;
            },std::move(ready),
            [this](const auto& leader,const auto& apps,const auto& actor){return common_->host().capture_membership(leader,apps,actor);},
            [this](const auto& audience){return common_->host().preflight(audience);},
            [this](const auto& audience){return common_->host().current(audience);},std::move(wallet),std::move(rule),
            [this](const auto& actor){return common_->host().capture_nonmember(actor);}),runtime_(service_){}
    bool recognizes(std::uint64_t session,const Records::Record& record)const{
        if(const auto q=std::get_if<RecoveredQuestAction::Request>(&record))return entry_.recognizes(session,*q);
        return entry_.pending(session)&&std::holds_alternative<RecoveredQuestClose::Request>(record);
    }
    Captured capture(std::uint64_t session,std::span<const Records::Record> records,Service::Time now){
        std::vector<Runtime::Indexed> raw;
        for(std::size_t i=0;i<records.size();++i)if(const auto q=std::get_if<RecoveredGuildMembership::Request>(&records[i])){
            const auto wire=RecoveredGuildMembership::encode_request(*q);if(wire)raw.push_back({i,{wire->begin(),wire->end()}});
        }
        const bool unrelated=std::any_of(records.begin(),records.end(),[&](const auto& record){
            if(recognizes(session,record)||std::holds_alternative<RecoveredGuildMembership::Request>(record))return false;
            if(const auto npc=std::get_if<RecoveredNpcInteraction::Request>(&record))return !OwnedGuildPanelService::custom_help_entry(*npc);
            return !std::holds_alternative<Records::Tick>(record)&&!std::holds_alternative<Records::TimerNotification>(record)&&
                !std::holds_alternative<Records::ContextNotification>(record)&&!std::holds_alternative<Records::ClientDiagnostic>(record)&&
                !std::holds_alternative<RecoveredGuildRoster::PanelReady>(record)&&!std::holds_alternative<Records::ClientOpaque74>(record)&&
                !std::holds_alternative<Records::ClientControl1F>(record)&&!std::holds_alternative<Records::ClientControl6D>(record)&&
                !std::holds_alternative<Records::ClientOptionsNotification>(record);
        });
        if(unrelated)invalidate(session);
        return {runtime_.capture_before_any_prefix(session,raw,now),entry_.prepare_choice(session,now)};
    }
    bool open_menu(std::uint64_t session,Service::Time now){
        if(common_->context(session))return false;
        const auto plan=entry_.prepare(session,now);if(!plan)return false;
        const auto weak=weak_from_this();common_->deliver(plan->lease.owner,{plan->logical.begin(),plan->logical.end()},
            [weak,plan=*plan](bool accepted){if(const auto self=weak.lock()){
                if(accepted)self->entry_.published(plan,OwnedGuildEntryService::Clock::now());
                else self->entry_.invalidate(plan.lease.owner.session);
            }});return true;
    }
    bool choose(std::uint64_t session,const Captured& captured,const Records::Record& record,Service::Time now){
        if(std::holds_alternative<RecoveredQuestClose::Request>(record)){invalidate(session);return true;}
        const auto action=std::get_if<RecoveredQuestAction::Request>(&record);if(!action||!captured.choice)return false;
        const auto choice=entry_.consume(*captured.choice,*action,now);if(!choice)return false;
        if(*choice==OwnedGuildEntryService::Choice::Exit){invalidate(session);return true;}
        service_.invalidate(session);
        interactions_.insert_or_assign(session,Service::Interaction{captured.choice->owner,0x087b,1,captured.choice->request});
        const auto opening=*choice==OwnedGuildEntryService::Choice::Create?service_.prepare_create(session,now):service_.prepare_join(session,now);
        if(!opening)return false;
        const auto weak=weak_from_this();common_->deliver(opening->interaction.owner,{opening->prompt.begin(),opening->prompt.end()},
            [weak,opening=*opening](bool accepted){if(const auto self=weak.lock()){
                if(accepted)self->service_.published(opening,Service::Conversation::Clock::now());
                else self->service_.invalidate(opening.interaction.owner.session);
            }});return true;
    }
    bool submit(std::uint64_t session,const Captured& captured,std::size_t index,Service::Time now){
        const auto at=std::find_if(captured.requests.actions.begin(),captured.requests.actions.end(),[&](const auto& item){return item.index==index;});
        if(at==captured.requests.actions.end())return false;
        const auto result=runtime_.execute(*at,now);if(!result)return false;
        if(const auto created=std::get_if<Common::Neighboring::Created53>(&*result)){
            const auto owner=common_->owner(session);if(owner)common_->deliver(*owner,RecoveredTrade::wallet(created->wallet.amount),[](bool){});
            common_->sync(session,false);
        }else{
            common_->sync(session,false);
        }
        // Accepted/pending roster reconciliation includes every connected target
        // owner captured before SQL; neither client names nor local slots supply IDs.
        if(at->plan)for(const auto& owner:at->plan->audience.connected)if(owner.session!=session)common_->sync(owner.session,false);
        return true;
    }
    void invalidate(std::uint64_t session){entry_.invalidate(session);service_.invalidate(session);interactions_.erase(session);}
    void disconnected(std::uint64_t session){invalidate(session);entry_.disconnect(session);}
private:
    std::shared_ptr<Common> common_;OwnedGuildEntryService entry_;
    std::map<std::uint64_t,Service::Interaction> interactions_;Service service_;Runtime runtime_;
};
}
