#pragma once
#include "EffectiveGuildAdmissionServiceDraft.h"
namespace god2 {
// PRIVATE CUSTOM policy; original native71/72/75 grammars unchanged.
class EffectiveGuildGovernanceServiceDraft {
public:
    using Repository=EffectiveGuildAdmissionRepositoryDraft;using Panel=OwnedGuildSuccessionServiceDraft;
    enum class Action {Appoint,RemoveOffice,Disband};
    struct Plan {Panel::Publication publication;Action action;std::uint8_t slot;Repository::Original::Identity target;StoredGuildMembership join;bool operator==(const Plan&)const=default;};
    using Ready=EffectiveGuildAdmissionServiceDraft::Readiness;
    EffectiveGuildGovernanceServiceDraft(Repository& repo,Panel& panel,Ready ready):repository_(repo),panel_(panel),ready_(std::move(ready)){}
    std::optional<Plan> prepare_before_prefix(const Panel::Publication& pub,std::span<const std::uint8_t> logical)const{
        try{const auto& state=pub.state;const auto session=state.recipient.session;
            if(logical.size()!=2 || logical[1]>=state.rows.size() || panel_.publication(session)!=std::optional{pub} || !ready_ || !ready_(state) ||
                state.leader.owner.account_id!=state.recipient.account || state.leader.owner.character_id!=state.recipient.character)return {};
            const auto slot=logical[1];const auto& row=state.rows[slot];if(!row.membership_revision)return {};
            const auto role=Repository::Succession::effective_display_role(state.leader,row);Action action;
            if(logical[0]==0x71 && slot && role==1)action=Action::Appoint;
            else if(logical[0]==0x72 && slot && role==2)action=Action::RemoveOffice;
            else if(logical[0]==0x75 && !slot && role==3 && row.character_id==state.recipient.character)action=Action::Disband;
            else return {};
            if(panel_.publication(session)!=std::optional{pub})return {};
            auto target=row;target.membership_revision=0;return Plan{pub,action,slot,target,{state.leader.guild.id,state.leader.guild.name_utf8,state.leader.guild.revision,row.membership_revision}};
        }catch(...){return {};}
    }
    bool execute(const Plan& plan){const auto& state=plan.publication.state;const auto session=state.recipient.session;
        try{if(panel_.publication(session)!=std::optional{plan.publication})return false;
            const std::array<std::uint8_t,2> logical{plan.action==Action::Appoint?std::uint8_t{0x71}:plan.action==Action::RemoveOffice?std::uint8_t{0x72}:std::uint8_t{0x75},plan.slot};
            if(prepare_before_prefix(plan.publication,logical)!=std::optional{plan}){panel_.invalidate_exact(plan.publication);return false;}
            panel_.invalidate_exact(plan.publication);consumed_.insert_or_assign(session,plan);
            const auto retained_cache=panel_.cached(session);if(!retained_cache || !retained_cache->consumed || retained_cache->previous!=plan.publication)throw DatabaseError("Missing consumed governance lifecycle cache");
            const auto proof=[&]{const auto at=consumed_.find(session);const auto cache=panel_.cached(session);
                if(at==consumed_.end() || at->second!=plan || !cache || cache!=retained_cache || !ready_ || !ready_(state))throw DatabaseError("Governance immutable consumed world lease changed");
                const auto final_cache=panel_.cached(session);if(!final_cache || final_cache!=retained_cache)throw DatabaseError("Governance callback replaced publication");};
            if(plan.action==Action::Disband)repository_.disband(state.leader,state.applications,{proof,proof});
            else repository_.change_officer(state.leader,state.applications,plan.target,plan.join,plan.action==Action::Appoint?Repository::Original::OfficerAction::Appoint:Repository::Original::OfficerAction::RemoveOffice,{proof,proof});
            consumed_.erase(session);return true;
        }catch(...){const auto at=consumed_.find(session);if(at!=consumed_.end() && at->second==plan)consumed_.erase(at);panel_.invalidate_exact(plan.publication);return false;}
    }
private:Repository& repository_;Panel& panel_;Ready ready_;std::map<std::uint64_t,Plan> consumed_;
};
}
