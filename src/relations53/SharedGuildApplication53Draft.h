#pragma once
#include "SharedGuildCoordinator53Draft.h"
#include "handlers/OwnedGuildPanelService.h"
#include "protocol/RecoveredWorldRecords.h"
#include "GuildAdmission53Application.h"
#include "game/LegacyWorldReply.h"
#include <exception>
#include <type_traits>
namespace god2 {
// PRIVATE actual Application ingress. Captures entire old frame before any
// prefix. No legacy52/50 mutator fallback and no alternative panel scheduler.
class SharedGuildApplication53Draft {
public:
    using Common=SharedGuildCoordinator53Draft;using Records=RecoveredWorldRecords;
    using Prefix=std::function<std::optional<std::vector<std::uint8_t>>(std::span<const Records::Record>)>;
    using CausalPrefix=std::function<std::optional<LegacyWorldReply>(std::span<const Records::Record>)>;
    using Audit=std::function<void(std::uint64_t,std::size_t,unsigned,bool)>;
    class Prepared final {
    public:
        bool recognizes(std::size_t index)const noexcept{return index<actions_.size()&&actions_[index].owned;}
        std::span<const Records::Record> records()const noexcept{return {records_.data(),records_.size()};}
        Prepared(const Prepared&)=delete;
        Prepared& operator=(const Prepared&)=delete;
    private:
        friend class SharedGuildApplication53Draft;
        Prepared()=default;
        struct Classified {unsigned opcode{};bool help{},choice{},owned{},consumed{};};
        const SharedGuildApplication53Draft* adapter_{};
        std::shared_ptr<const std::uint8_t> identity_;
        std::shared_ptr<Common> common_;
        std::shared_ptr<GuildAdmission53Application> admission_source_;
        std::shared_ptr<const std::uint8_t> admission_identity_;
        std::uint64_t session_{};
        std::vector<Records::Record> records_;
        std::vector<Classified> actions_;
        Common::Time now_;
        std::optional<GuildAdmission53Application::Captured> admission_;
        std::optional<Common::Panel::CacheEvidence> oldcache_;
        std::optional<Common::PendingPermit> oldpending_;
        std::vector<Common::NeighborIndexed> indexed_;
        std::vector<Common::Indexed> rawindexed_;
        Common::NeighborBatch members_;
        Common::PendingBatch pending_;
        Common::Batch relation_;
        std::optional<Common::NoticeAction> notice_;
        std::map<std::size_t,Common::Lifecycle> life_;
        std::set<unsigned> domains_;
        std::size_t next_{};
        bool mixed_{},help_safe_{},complete_{},rejected_{},cleanup_attempted_{},executing_{};
    };
    using Capture=std::shared_ptr<Prepared>;
    // UI attempts do not prove enqueue, Written, publication or client ACK.
    // None carries no affirmative result and does not promise rollback.
    enum class Effect {None,UiAttempted,MutationCommitted};
    struct Execution {bool recognized{};Effect effect{Effect::None};};
    bool owns(std::uint64_t session,const Records::Record& record)const{return opcode(record)||help(record)||(admission_&&admission_->recognizes(session,record));}
    SharedGuildApplication53Draft(std::shared_ptr<Common> common,Common::Neighboring::Original& original,Audit audit={})
      :common_(std::move(common)),original_(original),audit_(std::move(audit)){}
    void admission(std::shared_ptr<GuildAdmission53Application> value){auto identity=std::make_shared<const std::uint8_t>(0);admission_=std::move(value);admission_identity_=std::move(identity);}
    static bool help(const Records::Record& r){const auto npc=std::get_if<RecoveredNpcInteraction::Request>(&r);return npc&&OwnedGuildPanelService::custom_help_entry(*npc);}
    static unsigned opcode(const Records::Record& r){
        if(const auto q=std::get_if<RecoveredGuildLeadership::Request>(&r))return static_cast<unsigned>(q->action);
        if(std::holds_alternative<RecoveredGuildLeave::Request>(r))return 0x73;
        if(std::holds_alternative<RecoveredGuildDisband75::Request>(r))return 0x75;
        if(std::holds_alternative<RecoveredGuildAnnouncement::Request>(r))return 0x79;
        if(std::holds_alternative<RecoveredGuildMembership::Request>(r))return 0x6f;
        if(std::holds_alternative<native_relation_private::Action>(r))return 0x76;
        return 0;
    }
    bool handles(std::uint64_t session,std::span<const Records::Record> records)const{return std::any_of(records.begin(),records.end(),[&](const auto& r){return opcode(r)||help(r)||(admission_&&admission_->recognizes(session,r));});}
    std::optional<std::vector<std::uint8_t>> handle(std::uint64_t session,std::span<const Records::Record> records,const Prefix& prefix){
        return handle_impl<std::vector<std::uint8_t>>(session,records,prefix);
    }
    std::optional<LegacyWorldReply> handle_reply(std::uint64_t session,std::span<const Records::Record> records,const CausalPrefix& prefix){
        return handle_impl<LegacyWorldReply>(session,records,prefix);
    }
    Capture capture(std::uint64_t session,std::span<const Records::Record> records){
        const auto keep=common_;if(!keep||records.empty())return {};
        auto captured=Capture(new Prepared);auto& state=*captured;
        state.adapter_=this;state.identity_=identity_;state.common_=keep;state.admission_source_=admission_;state.admission_identity_=admission_identity_;state.session_=session;
        state.records_.assign(records.begin(),records.end());state.now_=OwnedGuildMembershipConversation::Clock::now();
        // Freeze dynamic admission choices before capture may revoke a mixed
        // dialogue and before any unrelated prefix can open a new one.
        for(const auto& record:state.records_){const auto op=opcode(record);const bool is_help=help(record);
            const bool choice=state.admission_source_&&state.admission_source_->recognizes(session,record);
            state.actions_.push_back({op,is_help,choice,bool(op||is_help||choice),false});
        }
        while(state.next_<state.actions_.size()&&!state.actions_[state.next_].owned)++state.next_;
        state.help_safe_=std::all_of(state.records_.begin(),state.records_.end(),[](const auto& r){return help(r)||std::holds_alternative<Records::Tick>(r)||std::holds_alternative<Records::TimerNotification>(r)||std::holds_alternative<Records::ContextNotification>(r)||std::holds_alternative<Records::ClientDiagnostic>(r)||std::holds_alternative<RecoveredGuildRoster::PanelReady>(r);});
        state.admission_=state.admission_source_?std::optional{state.admission_source_->capture(session,state.records_,state.now_)}:std::nullopt;
        state.oldcache_=keep->panel().cached(session);state.oldpending_=keep->pending_permit(session);
        for(std::size_t i=0;i<state.records_.size();++i){const auto op=state.actions_[i].opcode;if(!op)continue;std::vector<std::uint8_t> raw;
            const auto& record=state.records_[i];
            if(const auto q=std::get_if<RecoveredGuildLeadership::Request>(&record))raw={static_cast<std::uint8_t>(op),q->slot};
            else if(const auto q=std::get_if<RecoveredGuildLeave::Request>(&record))raw={0x73,q->slot};
            else if(const auto q=std::get_if<RecoveredGuildDisband75::Request>(&record))raw={0x75,q->slot};
            else if(const auto q=std::get_if<native_relation_private::Action>(&record)){const auto bytes=native_relation_private::encode76(*q);raw.assign(bytes.begin(),bytes.end());}
            else raw={static_cast<std::uint8_t>(op)};
            state.indexed_.push_back({i,raw});state.rawindexed_.push_back({i,raw});state.domains_.insert(op);
        }
        state.members_=keep->capture_neighbors_before_any_prefix(session,state.indexed_);
        if(state.members_.original&&(!state.oldcache_||state.members_.original->panel!=*state.oldcache_))state.members_.original.reset();
        state.pending_=keep->capture_pending73_before_any_prefix(session,state.indexed_,state.now_);
        if(state.pending_.original!=state.oldpending_)state.pending_.original.reset();
        state.relation_=keep->capture_before_any_prefix(session,state.rawindexed_);
        if(state.relation_.original&&(!state.oldcache_||state.relation_.original->panel!=*state.oldcache_))state.relation_.original.reset();
        state.notice_=keep->capture_announcement(session,state.now_);
        if(state.notice_&&(!state.oldcache_||state.notice_->original.panel!=*state.oldcache_))state.notice_.reset();
        for(std::size_t i=0;i<state.records_.size();++i)try{
            std::optional<Common::Lifecycle> plan;
            if(const auto q=std::get_if<RecoveredGuildDisband75::Request>(&state.records_[i]);q&&q->slot==0)plan=keep->capture_disband(session);
            if(const auto q=std::get_if<RecoveredGuildLeave::Request>(&state.records_[i]);q&&q->slot&&state.oldcache_){
                const auto& rows=state.oldcache_->previous.state.rows;if(q->slot<rows.size()){const auto& row=rows[q->slot];
                    const auto join=StoredGuildMembership{state.oldcache_->previous.state.leader.guild.id,state.oldcache_->previous.state.leader.guild.name_utf8,state.oldcache_->previous.state.leader.guild.revision,row.membership_revision};
                    plan=keep->capture_transfer(session,original_.identity(row.account_id,row.character_id),join);
                }
            }
            if(plan&&state.oldcache_&&plan->original.panel==*state.oldcache_)state.life_.emplace(i,*plan);
        }catch(...){}
        state.mixed_=state.domains_.size()>1;state.complete_=true;
        return captured;
    }
    Execution execute(std::uint64_t session,Capture& captured,std::size_t index){
        // No recapture here: all plans, choices and domain policy belong to the
        // complete original frame. Consume before any callback can reenter.
        // Retirement stops later records, but cannot undo or cancel side
        // callbacks already entered inside Common/admission. A native holder
        // still needs deeper continuation/custody fencing before activation.
        const auto held=captured;if(!owns_capture(session,held))return {};
        if(!valid(session,held)||held->executing_||index!=held->next_||!held->recognizes(index)||held->actions_[index].consumed){reject(session,captured);return {};}
        auto& state=*held;auto& action=state.actions_[index];action.consumed=true;
        ++state.next_;while(state.next_<state.actions_.size()&&!state.actions_[state.next_].owned)++state.next_;
        state.executing_=true;struct Reset {bool& flag;~Reset(){flag=false;}} reset{state.executing_};
        const auto keep=state.common_;const auto& record=state.records_[index];const auto op=action.opcode;
        try{
        if(action.help){bool committed=false;if(state.help_safe_){
            const auto context=keep->context(session);
            if(!valid(session,held)){auto retirement=held;reject(session,retirement);return {};}
            if(context){keep->sync(session,true);committed=true;}else if(state.admission_source_)committed=state.admission_source_->open_menu(session,state.now_);
        }return {!state.rejected_,committed?Effect::UiAttempted:Effect::None};}
        if(action.choice){const bool committed=state.admission_&&!state.mixed_&&state.admission_source_->choose(session,*state.admission_,record,OwnedGuildMembershipConversation::Clock::now());return {!state.rejected_,committed?Effect::UiAttempted:Effect::None};}
        bool committed=false;
        if(!state.mixed_){
            if(op==0x76)committed=keep->execute(state.relation_);
            else if(op==0x79){if(state.notice_)committed=bool(keep->execute(*state.notice_,std::get<RecoveredGuildAnnouncement::Request>(record),OwnedGuildMembershipConversation::Clock::now()));}
            else if(state.life_.contains(index))committed=keep->execute(state.life_.at(index));
            else if(op==0x73&&state.pending_.original){const auto at=std::find_if(state.pending_.actions.begin(),state.pending_.actions.end(),[&](const auto& row){return row.index==index;});if(at!=state.pending_.actions.end())committed=keep->execute_pending73_item(state.pending_,static_cast<std::size_t>(at-state.pending_.actions.begin()),OwnedGuildMembershipConversation::Clock::now());}
            else if(op==0x71||op==0x72||op==0x73){const auto at=std::find_if(state.members_.actions.begin(),state.members_.actions.end(),[&](const auto& row){return row.index==index;});if(at!=state.members_.actions.end())committed=keep->execute_neighbor_item(state.members_,static_cast<std::size_t>(at-state.members_.actions.begin()));}
            else if(op==0x6f&&state.admission_)committed=state.admission_source_->submit(session,*state.admission_,index,OwnedGuildMembershipConversation::Clock::now());
        }
        if(!committed){reject_actions(state);if(op==0x79&&state.records_.size()==1)keep->restore_announcement(session);}
        if(audit_)audit_(session,index,op,committed);
        return {!state.rejected_,committed?Effect::MutationCommitted:Effect::None};
        }catch(...){
            // No rollback is implied if an action already committed. A caught
            // callback/audit failure may not continue into another old plan.
            const auto failure=std::current_exception();state.rejected_=true;
            try{reject_actions(state);}catch(...){}std::rethrow_exception(failure);
        }
    }
    void reject(std::uint64_t session,Capture& captured){
        const auto held=captured;if(!owns_capture(session,held)||held->rejected_)return;held->rejected_=true;reject_actions(*held);
    }
    void retire(std::uint64_t session,Capture& captured){reject(session,captured);}
private:
    bool owns_capture(std::uint64_t session,const Capture& captured)const{return captured&&captured->complete_&&captured->adapter_==this&&captured->identity_==identity_&&captured->common_==common_&&captured->session_==session;}
    bool valid(std::uint64_t session,const Capture& captured)const{return owns_capture(session,captured)&&!captured->rejected_&&captured->admission_source_==admission_&&captured->admission_identity_==admission_identity_;}
    static void reject_actions(Prepared& state){
        if(state.cleanup_attempted_)return;state.cleanup_attempted_=true;std::exception_ptr failure;
        try{state.common_->reject_neighbor_batch(state.members_);}catch(...){failure=std::current_exception();}
        if(state.pending_.original)try{state.common_->deny_pending_exact(*state.pending_.original);}catch(...){if(!failure)failure=std::current_exception();}
        if(failure)std::rethrow_exception(failure);
    }
    template<class Reply,class PrefixCallback>
    std::optional<Reply> handle_impl(std::uint64_t session,std::span<const Records::Record> records,const PrefixCallback& prefix){
        if(!prefix)return {};auto captured=capture(session,records);if(!captured)return {};
        const auto original=captured->records();
        Reply response{std::vector<std::uint8_t>{}};std::size_t begin=0;
        const auto runprefix=[&](std::size_t end){
            if(end==begin)return true;
            // Session prefix custody is tied to the actual incoming record
            // occurrences. Prepared copies belong only to the action plans.
            auto result=prefix(records.subspan(begin,end-begin));if(!result)return false;
            if constexpr(std::is_same_v<Reply,LegacyWorldReply>)response.append(std::move(*result));
            else response.insert(response.end(),result->begin(),result->end());
            return true;
        };
        for(std::size_t i=0;i<original.size();++i){if(!captured->recognizes(i))continue;
            if(!runprefix(i)){reject(session,captured);return {};}
            begin=i+1;if(!execute(session,captured,i).recognized)return {};
        }
        if(!runprefix(original.size()))return {};return std::optional<Reply>{std::move(response)};
    }
private:std::shared_ptr<const std::uint8_t> identity_=std::make_shared<const std::uint8_t>(0);
    std::shared_ptr<Common> common_;Common::Neighboring::Original& original_;Audit audit_;
    std::shared_ptr<GuildAdmission53Application> admission_;
    std::shared_ptr<const std::uint8_t> admission_identity_;
};
}
