#pragma once
#include "db/EffectiveGuildAdmissionRepositoryDraft.h"
#include "handlers/OwnedGuildSuccessionServiceDraft.h"
namespace god2 {
class EffectiveGuildAdmissionServiceDraft {
public:
    using Repository=EffectiveGuildAdmissionRepositoryDraft;
    using Panel=OwnedGuildSuccessionServiceDraft;
    using Wire=RecoveredGuildLeadership;
    using Readiness=std::function<bool(const Panel::State&)>;
    struct Plan {Panel::Publication publication;Wire::Request request;Repository::Original::Application application;bool operator==(const Plan&) const=default;};
    EffectiveGuildAdmissionServiceDraft(Repository& repository,Panel& panels,Readiness ready):repository_(repository),panels_(panels),ready_(std::move(ready)){}
    std::optional<Plan> prepare_before_prefix(const Panel::Publication& publication,const Wire::Request& request) const {
        try {
            const auto& state=publication.state;const auto session=state.recipient.session;
            if(!request.slot || request.slot>=state.rows.size() || !publication.contract.explicit_single_use_authority ||
               state.leader.owner.account_id!=state.recipient.account || state.leader.owner.character_id!=state.recipient.character ||
               (request.action!=Wire::Action::ApproveOrAppoint && request.action!=Wire::Action::RejectOrRemove) ||
               panels_.publication(session)!=std::optional{publication} || !ready_ || !ready_(state))return {};
            const auto& row=state.rows[request.slot];if(row.membership_revision || publication.contract.rows.at(request.slot).role!=0)return {};
            const auto app=std::find_if(state.applications.begin(),state.applications.end(),[&](const auto& value){return value.applicant==row;});
            if(app==state.applications.end() || panels_.publication(session)!=std::optional{publication})return {};
            return Plan{publication,request,*app};
        }catch(...){return {};}
    }
    bool execute(const Plan& plan) {
        const auto& state=plan.publication.state;const auto session=state.recipient.session;
        try {
            if(panels_.publication(session)!=std::optional{plan.publication})return false;
            if(prepare_before_prefix(plan.publication,plan.request)!=std::optional{plan}) {panels_.invalidate_exact(plan.publication);return false;}
            panels_.invalidate_exact(plan.publication);consumed_.insert_or_assign(session,plan);
            const auto retained_cache=panels_.cached(session);
            if(!retained_cache || !retained_cache->consumed || retained_cache->previous!=plan.publication)throw DatabaseError("Missing exact consumed lifecycle cache");
            const auto proof=[&] {
                const auto token=consumed_.find(session);const auto cache=panels_.cached(session);
                if(token==consumed_.end() || token->second!=plan || !cache || cache!=retained_cache ||
                   !ready_ || !ready_(state))throw DatabaseError("Effective52 admission complete consumed publication/world lease changed");
                const auto final_cache=panels_.cached(session);
                if(!final_cache || final_cache!=retained_cache || consumed_.find(session)==consumed_.end() ||
                   consumed_.at(session)!=plan)throw DatabaseError("Effective52 admission readiness changed consumed lease");
            };
            if(plan.request.action==Wire::Action::ApproveOrAppoint)repository_.approve(state.leader,state.applications,plan.application,{proof,proof});
            else repository_.reject(state.leader,state.applications,plan.application,{proof,proof});
            consumed_.erase(session);return true;
        }catch(...){const auto at=consumed_.find(session);if(at!=consumed_.end() && at->second==plan)consumed_.erase(at);panels_.invalidate_exact(plan.publication);return false;}
    }
private:Repository& repository_;Panel& panels_;Readiness ready_;std::map<std::uint64_t,Plan> consumed_;
};
class EffectiveGuildAdmissionRuntimeDraft {
public:
    using Service=EffectiveGuildAdmissionServiceDraft;
    using Indexed=founder_transfer_contract_draft::IndexedLogical;
    struct Captured {std::size_t index{};Service::Wire::Request wire;std::optional<Service::Plan> plan;};
    struct Batch {bool structurally_valid{};std::vector<Captured> actions;};
    EffectiveGuildAdmissionRuntimeDraft(Service& service,OwnedGuildSuccessionServiceDraft& panel):service_(service),panel_(panel){}
    Batch capture_before_any_prefix(std::uint64_t session,std::span<const Indexed> records) const {
        const auto original=panel_.publication(session);std::vector<Service::Wire::Request> decoded;
        std::size_t previous=0;bool first=true;
        for(const auto& logical:records){if(!first && logical.index<=previous)return {};first=false;previous=logical.index;
            const auto wire=Service::Wire::decode(logical.logical);if(!wire)return {};decoded.push_back(*wire);}
        Batch out{true,{}};
        for(std::size_t i=0;i<records.size();++i)out.actions.push_back({records[i].index,decoded[i],original?service_.prepare_before_prefix(*original,decoded[i]):std::nullopt});
        return out;
    }
    bool execute(const Captured& item) {return item.plan && item.plan->request==item.wire && service_.execute(*item.plan);}
private:Service& service_;OwnedGuildSuccessionServiceDraft& panel_;
};
}
