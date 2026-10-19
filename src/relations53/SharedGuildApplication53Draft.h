#pragma once
#include "SharedGuildCoordinator53Draft.h"
#include "handlers/OwnedGuildPanelService.h"
#include "protocol/RecoveredWorldRecords.h"
#include "GuildAdmission53Application.h"
#include "game/LegacyWorldReply.h"
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
    SharedGuildApplication53Draft(std::shared_ptr<Common> common,Common::Neighboring::Original& original,Audit audit={})
      :common_(std::move(common)),original_(original),audit_(std::move(audit)){}
    void admission(std::shared_ptr<GuildAdmission53Application> value){admission_=std::move(value);}
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
private:
    template<class Reply,class PrefixCallback>
    std::optional<Reply> handle_impl(std::uint64_t session,std::span<const Records::Record> records,const PrefixCallback& prefix){
        const auto keep=common_;if(!keep||!prefix||records.empty())return {};
        const auto now=OwnedGuildMembershipConversation::Clock::now();
        const auto admission=admission_?std::optional{admission_->capture(session,records,now)}:std::nullopt;
        const auto oldcache=keep->panel().cached(session);const auto oldpending=keep->pending_permit(session);
        std::vector<Common::NeighborIndexed> indexed;std::vector<Common::Indexed> rawindexed;
        for(std::size_t i=0;i<records.size();++i){const auto op=opcode(records[i]);if(!op)continue;std::vector<std::uint8_t> raw;
            if(const auto q=std::get_if<RecoveredGuildLeadership::Request>(&records[i]))raw={static_cast<std::uint8_t>(op),q->slot};
            else if(const auto leave_request=std::get_if<RecoveredGuildLeave::Request>(&records[i]))raw={0x73,leave_request->slot};
            else if(const auto disband_request=std::get_if<RecoveredGuildDisband75::Request>(&records[i]))raw={0x75,disband_request->slot};
            else if(const auto relation_request=std::get_if<native_relation_private::Action>(&records[i])){const auto b=native_relation_private::encode76(*relation_request);raw.assign(b.begin(),b.end());}
            else raw={static_cast<std::uint8_t>(op)};
            indexed.push_back({i,raw});rawindexed.push_back({i,raw});
        }
        auto members=keep->capture_neighbors_before_any_prefix(session,indexed);
        if(members.original&&(!oldcache||members.original->panel!=*oldcache))members.original.reset();
        auto pending=keep->capture_pending73_before_any_prefix(session,indexed,now);
        if(pending.original!=oldpending)pending.original.reset();
        auto relation=keep->capture_before_any_prefix(session,rawindexed);
        if(relation.original&&(!oldcache||relation.original->panel!=*oldcache))relation.original.reset();
        auto notice=keep->capture_announcement(session,now);
        if(notice&&(!oldcache||notice->original.panel!=*oldcache))notice.reset();
        std::map<std::size_t,Common::Lifecycle> life;
        for(std::size_t i=0;i<records.size();++i)try{
            std::optional<Common::Lifecycle> plan;
            if(const auto q=std::get_if<RecoveredGuildDisband75::Request>(&records[i]);q&&q->slot==0)plan=keep->capture_disband(session);
            if(const auto q=std::get_if<RecoveredGuildLeave::Request>(&records[i]);q&&q->slot&&oldcache){
                const auto& rows=oldcache->previous.state.rows;if(q->slot<rows.size()){const auto& row=rows[q->slot];
                    const auto join=StoredGuildMembership{oldcache->previous.state.leader.guild.id,oldcache->previous.state.leader.guild.name_utf8,oldcache->previous.state.leader.guild.revision,row.membership_revision};
                    plan=keep->capture_transfer(session,original_.identity(row.account_id,row.character_id),join);
                }
            }
            if(plan&&oldcache&&plan->original.panel==*oldcache)life.emplace(i,*plan);
        }catch(...){}
        // Mixed native domains are explicit fail-closed until their common
        // sequence policy is qualified; all capabilities above are still old.
        std::set<unsigned> domains;for(const auto& row:indexed)domains.insert(row.logical.front());
        const bool mixed=domains.size()>1;
        Reply response{std::vector<std::uint8_t>{}};std::size_t begin=0;
        const auto runprefix=[&](std::size_t end){
            if(end==begin)return true;
            auto result=prefix(records.subspan(begin,end-begin));if(!result)return false;
            if constexpr(std::is_same_v<Reply,LegacyWorldReply>)response.append(std::move(*result));
            else response.insert(response.end(),result->begin(),result->end());
            return true;
        };
        const bool help_safe=std::all_of(records.begin(),records.end(),[](const auto& r){return help(r)||std::holds_alternative<Records::Tick>(r)||std::holds_alternative<Records::TimerNotification>(r)||std::holds_alternative<Records::ContextNotification>(r)||std::holds_alternative<Records::ClientDiagnostic>(r)||std::holds_alternative<RecoveredGuildRoster::PanelReady>(r);});
        for(std::size_t i=0;i<records.size();++i){const auto op=opcode(records[i]);const bool choice=admission_&&admission_->recognizes(session,records[i]);if(!op&&!help(records[i])&&!choice)continue;
            if(!runprefix(i)){keep->reject_neighbor_batch(members);if(pending.original)keep->deny_pending_exact(*pending.original);return {};}
            begin=i+1;
            if(help(records[i])){if(help_safe){if(keep->context(session))keep->sync(session,true);else if(admission_)admission_->open_menu(session,now);}continue;}
            if(choice){if(admission&&!mixed)admission_->choose(session,*admission,records[i],OwnedGuildMembershipConversation::Clock::now());continue;}
            bool committed=false;
            if(!mixed){
                if(op==0x76)committed=keep->execute(relation);
                else if(op==0x79){if(notice)committed=bool(keep->execute(*notice,std::get<RecoveredGuildAnnouncement::Request>(records[i]),OwnedGuildMembershipConversation::Clock::now()));}
                else if(life.contains(i))committed=keep->execute(life.at(i));
                else if(op==0x73&&pending.original){const auto at=std::find_if(pending.actions.begin(),pending.actions.end(),[&](const auto& row){return row.index==i;});if(at!=pending.actions.end())committed=keep->execute_pending73_item(pending,static_cast<std::size_t>(at-pending.actions.begin()),OwnedGuildMembershipConversation::Clock::now());}
                else if(op==0x71||op==0x72||op==0x73){const auto at=std::find_if(members.actions.begin(),members.actions.end(),[&](const auto& row){return row.index==i;});if(at!=members.actions.end())committed=keep->execute_neighbor_item(members,static_cast<std::size_t>(at-members.actions.begin()));}
                else if(op==0x6f&&admission)committed=admission_->submit(session,*admission,i,OwnedGuildMembershipConversation::Clock::now());
            }
            if(!committed){keep->reject_neighbor_batch(members);if(pending.original)keep->deny_pending_exact(*pending.original);if(op==0x79&&records.size()==1)keep->restore_announcement(session);}
            if(audit_)audit_(session,i,op,committed);
        }
        if(!runprefix(records.size()))return {};return std::optional<Reply>{std::move(response)};
    }
private:std::shared_ptr<Common> common_;Common::Neighboring::Original& original_;Audit audit_;
    std::shared_ptr<GuildAdmission53Application> admission_;
};
}
