#pragma once
#include "EffectiveGuildJoinConversationRuntimeDraft.h"
#include "protocol/RecoveredGuildLeave.h"
namespace god2 {
// Native SELF73 role0 producer is separately verified. Business cancellation is CUSTOM0083.
// Dedicated pending-self permit; NEVER grants accepted-panel transfer73 or announcement79.
class EffectiveGuildPendingCancellationServiceDraft {
public:
    using Repository=EffectiveGuildAdmissionRepositoryDraft;using Panel=OwnedGuildSuccessionServiceDraft;
    using Time=OwnedGuildMembershipConversation::Time;using Wire=RecoveredGuildLeave;
    static constexpr auto lifetime=OwnedGuildMembershipConversation::lifetime;
    struct Permit {Panel::CacheEvidence cache;Time opened,expires;bool operator==(const Permit&)const=default;};
    struct Plan {Permit permit;Wire::Request request;Repository::Original::Identity actor;Repository::Original::Application application;bool operator==(const Plan& other)const{return permit==other.permit && request.slot==other.request.slot && actor==other.actor && application==other.application;}};
    using Preflight=std::function<bool(const Panel::Audience&)>;using Current=std::function<bool(const Panel::Audience&)>;
    using Resolve=Panel::Resolve;using RevokeAnnouncement=std::function<void(const Panel::Publication&)>;
    EffectiveGuildPendingCancellationServiceDraft(Repository& repository,Repository::Original& original,Repository::Succession& effective,SqliteRecoveredCharacterRepository& profiles,Panel& panel,
        Resolve resolve,Preflight preflight,Current current,RevokeAnnouncement revoke):repository_(repository),original_(original),effective_(effective),profiles_(profiles),panel_(panel),resolve_(std::move(resolve)),preflight_(std::move(preflight)),current_(std::move(current)),revoke_(std::move(revoke)){}
    // Trusted host calls after the exact pending-self roster batch is accepted into world tail.
    // A cache epoch may grant this permission ONCE, even after a failed attempt.
    bool arm_after_publication(const Panel::CacheEvidence& cache,Time now){
        try{const auto session=cache.previous.state.recipient.session;if(now>Time::max()-lifetime || !cache.epoch || !cache.consumed || cache.previous.contract.explicit_single_use_authority ||
                panel_.cached(session)!=std::optional{cache} || !resolve_ || !preflight_ || !current_ || !revoke_)return false;
            const auto seen=highest_epoch_.find(session);if(seen!=highest_epoch_.end() && cache.epoch<=seen->second)return false;
            const auto& state=cache.previous.state;if(state.rows.empty() || state.rows.front().membership_revision || cache.previous.contract.rows.empty() || cache.previous.contract.rows.front().role!=0 ||
                state.rows.front().account_id!=state.recipient.account || state.rows.front().character_id!=state.recipient.character || !state_current(cache) || !preflight_(state.audience))return false;
            if(panel_.cached(session)!=std::optional{cache} || !state_current(cache))return false;
            highest_epoch_.insert_or_assign(session,cache.epoch);permits_.insert_or_assign(session,Permit{cache,now,now+lifetime});return true;
        }catch(...){return false;}
    }
    std::optional<Plan> capture_before_prefix(std::uint64_t session,const Wire::Request& request,Time now)const{
        try{const auto at=permits_.find(session);if(at==permits_.end() || request.slot!=0 || now<at->second.opened || now>=at->second.expires || !state_current(at->second.cache) || !preflight_ || !preflight_(at->second.cache.previous.state.audience))return {};
            const auto& state=at->second.cache.previous.state;const auto app=original_.pending(state.recipient.account,state.recipient.character);if(!app || app->applicant!=state.rows.front())return {};
            // Current actor may legitimately level/change role after applying; saved applicant profile stays history.
            const auto actor=original_.nonmember(state.recipient.account,state.recipient.character);
            const auto permit=at->second;if(permits_.find(session)==permits_.end() || permits_.at(session)!=permit || !state_current(permit.cache))return {};return Plan{permit,request,actor,*app};
        }catch(...){return {};}
    }
    bool execute(const Plan& plan,Time now){const auto session=plan.permit.cache.previous.state.recipient.session;
        try{const auto at=permits_.find(session);if(at==permits_.end() || at->second!=plan.permit)return false;
            if(capture_before_prefix(session,plan.request,now)!=std::optional{plan}){deny_exact(plan.permit);return false;}
            permits_.erase(session);consumed_.insert_or_assign(session,plan);revoke_(plan.permit.cache.previous);
            const auto& state=plan.permit.cache.previous.state;
            const auto proof=[&]{const auto token=consumed_.find(session);if(token==consumed_.end() || token->second!=plan || panel_.cached(session)!=std::optional{plan.permit.cache} || !world_resources(state) ||
                    consumed_.find(session)==consumed_.end() || consumed_.at(session)!=plan || panel_.cached(session)!=std::optional{plan.permit.cache})throw DatabaseError("Pending cancel immutable consumed cache/world lease changed");};
            repository_.cancel(plan.actor,state.leader,state.applications,plan.application,{proof,proof});consumed_.erase(session);return true;
        }catch(...){const auto at=consumed_.find(session);if(at!=consumed_.end() && at->second==plan)consumed_.erase(at);deny_exact(plan.permit);return false;}
    }
    std::optional<Permit> permit(std::uint64_t session)const{const auto at=permits_.find(session);return at==permits_.end()?std::nullopt:std::optional{at->second};}
    void deny_exact(const Permit& permit){const auto session=permit.cache.previous.state.recipient.session;const auto at=permits_.find(session);if(at!=permits_.end() && at->second==permit)permits_.erase(at);
        (void)panel_.revoke_exact(permit.cache);if(revoke_)revoke_(permit.cache.previous);}
private:
    bool world_resources(const Panel::State& state)const{
        if(!resolve_ || resolve_(state.recipient.session)!=std::optional{state.recipient} || !current_ || !current_(state.audience))return false;
        for(const auto& row:state.rows){const auto at=state.audience.resources.find(row.character_id);if(at==state.audience.resources.end() || profiles_.load_resources(row.account_id,row.character_id)!=std::optional{at->second})return false;}
        return resolve_(state.recipient.session)==std::optional{state.recipient} && current_(state.audience);
    }
    bool state_current(const Panel::CacheEvidence& cache)const{const auto& state=cache.previous.state;return panel_.cached(state.recipient.session)==std::optional{cache} &&
        effective_.effective_snapshot(state.leader.guild.id)==state.leader && effective_.applications(state.leader.guild.id)==state.applications && world_resources(state);}
    Repository& repository_;Repository::Original& original_;Repository::Succession& effective_;SqliteRecoveredCharacterRepository& profiles_;Panel& panel_;
    Resolve resolve_;Preflight preflight_;Current current_;RevokeAnnouncement revoke_;std::map<std::uint64_t,Permit> permits_;std::map<std::uint64_t,Plan> consumed_;std::map<std::uint64_t,std::uint64_t> highest_epoch_;
};
class EffectiveGuildPendingCancellationRuntimeDraft {
public:
    using Service=EffectiveGuildPendingCancellationServiceDraft;using Indexed=founder_transfer_contract_draft::IndexedLogical;
    struct Captured{std::size_t index{};Service::Wire::Request request;std::optional<Service::Permit> original;std::optional<Service::Plan> plan;};
    struct Batch{bool structurally_valid{};std::vector<Captured> actions;};
    explicit EffectiveGuildPendingCancellationRuntimeDraft(Service& service):service_(service){}
    Batch capture_before_any_prefix(std::uint64_t session,std::span<const Indexed> records,Service::Time now)const{
        std::vector<Service::Wire::Request> decoded;std::size_t previous=0;bool first=true;
        for(const auto& item:records){if(!first && item.index<=previous)return {};first=false;previous=item.index;const auto wire=Service::Wire::decode(item.logical);if(!wire)return {};decoded.push_back(*wire);}
        const auto original=service_.permit(session);Batch out{true,{}};
        for(std::size_t i=0;i<records.size();++i)out.actions.push_back({records[i].index,decoded[i],original,original?service_.capture_before_prefix(session,decoded[i],now):std::nullopt});return out;
    }
    bool execute(const Captured& item,Service::Time now){if(item.plan && item.original==std::optional{item.plan->permit} && item.request.slot==item.plan->request.slot)return service_.execute(*item.plan,now);
        if(item.original)service_.deny_exact(*item.original);return false;}
private:Service& service_;
};
}
