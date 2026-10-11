#pragma once
#include "handlers/OwnedGuildLeaderPanelService.h"
#include <functional>

namespace god2 {
// CUSTOM-0080 founder-only ordinary member removal through native72/slot.
// The complete persisted panel + publication serial supplies action authority;
// a displayed slot/role alone never grants it. No fee or officer ranks are
// inferred. Founder and target must be nonbattle; each connected target must be
// presently projection-ready. TargetReady is a readiness policy, not an immutable
// target movement/ABA lease. Capturing must precede world-batch prefix processing.
// All use is confined to the existing game executor.
class OwnedGuildKickService {
public:
    using Repository=SqliteOwnedGuildMembershipRepository;
    using Panel=OwnedGuildLeaderPanelService;
    using Owner=Panel::Owner;
    using Resolve=Panel::Resolve;
    using TargetReady=std::function<bool(const Repository::Identity&)>;
    struct ActionPlan {
        Panel::State panel;
        std::uint8_t slot{};
        std::uint64_t publication{};
        Repository::Identity target;
        StoredGuildMembership target_membership;
        bool operator==(const ActionPlan&) const=default;
    };
    OwnedGuildKickService(Repository& repository,Panel& panels,Resolve resolve,TargetReady target_ready):
        repository_(repository),panels_(panels),resolve_(std::move(resolve)),target_ready_(std::move(target_ready)){}

    std::optional<ActionPlan> prepare_action(std::uint64_t session,std::uint8_t slot) const {
        try {
            const auto publication=panels_.action_publication(session);
            if(!publication || !publication->serial || !founder(publication->state))return {};
            const auto& state=publication->state;
            if(!slot || slot>=state.rows.size())return {};
            const auto& row=state.rows[slot];
            if(row.role!=1 || row.application || !row.identity.membership_revision ||
               row.identity.character_id==state.owner.character || !row.identity.account_id || !row.identity.character_id)return {};
            auto target=row.identity;target.membership_revision=0;
            const StoredGuildMembership membership{state.membership.guild_id,state.membership.name_utf8,
                state.membership.guild_revision,row.identity.membership_revision};
            if(!resolve_ || resolve_(session)!=std::optional{state.owner} || !target_ready_ || !target_ready_(target))return {};
            // Resolver/readiness callbacks may invalidate/reopen the panel; do
            // not return an authority derived before their side effects.
            if(panels_.action_publication(session)!=publication)return {};
            return ActionPlan{state,slot,publication->serial,std::move(target),membership};
        }catch(...){return {};}
    }
    bool current(const ActionPlan& plan) const {
        try {
            const auto fresh=prepare_action(plan.panel.owner.session,plan.slot);
            return fresh && *fresh==plan;
        }catch(...){return false;}
    }
    bool execute(const ActionPlan& plan) {
        try {
            const auto session=plan.panel.owner.session;
            const auto publication=panels_.action_publication(session);
            if(!publication) {panels_.invalidate(session);return false;}
            // A stale action cannot consume a different freshly reopened panel.
            if(publication->serial!=plan.publication || publication->state!=plan.panel)return false;
            const bool qualified=current(plan);
            // Consume before any SQL attempt, including readiness/CAS failures.
            // A readonly refresh cannot restore consumed permission; only a
            // fresh qualified explicit open may authorize another request.
            panels_.invalidate(session);
            if(!qualified)return false;
            const auto owner=plan.panel.owner;
            const auto target=plan.target;
            const auto proof=[this,owner,target] {
                if(!resolve_ || resolve_(owner.session)!=std::optional{owner} ||
                   !target_ready_ || !target_ready_(target))
                    throw DatabaseError("CUSTOM-0080 founder world/target readiness changed");
            };
            repository_.member_kick(plan.panel.leader,plan.panel.applications,
                plan.target,plan.target_membership,{proof,proof});
            return true;
        }catch(...){
            // Callback exceptions are also failed attempts. Retain panel cache
            // for the next native92/91 reconciliation, but revoke authority.
            panels_.invalidate(plan.panel.owner.session);return false;
        }
    }
    void invalidate(std::uint64_t session){panels_.invalidate(session);}
    void observe_world(std::uint64_t session){panels_.observe_world(session);}
    // This service owns no independent cached rows. Host owns panel cache
    // removal; forgotten kick authority must not silently drop native92 debt.
    void forget(std::uint64_t session){panels_.invalidate(session);}
private:
    static bool founder(const Panel::State& state) {
        return state.owner.session && state.owner.account && state.owner.character &&
            state.owner.account==state.leader.governance.owner_account &&
            state.owner.character==state.leader.governance.owner_character &&
            state.membership.guild_id==state.leader.governance.guild_id &&
            state.membership.guild_id==state.leader.membership.guild_id &&
            state.membership.guild_revision==state.leader.membership.guild_revision &&
            state.membership.name_utf8==state.leader.membership.name_utf8 &&
            !state.rows.empty() && state.rows.front().role==3 && !state.rows.front().application &&
            state.rows.front().identity.account_id==state.owner.account &&
            state.rows.front().identity.character_id==state.owner.character;
    }
    Repository& repository_;Panel& panels_;Resolve resolve_;TargetReady target_ready_;
};
}
