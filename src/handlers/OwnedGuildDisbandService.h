#pragma once
#include "handlers/OwnedGuildLeaderPanelService.h"
#include <functional>

namespace god2 {
// CUSTOM-0081 candidate native75 service; live acceptance is tracked separately.
// Native75 main25/modal5 sends only self local slot; slot/role is not authority.
// This independent service requires Repository::disband(Leader,applications,Proof)
// from the separately reviewed storage draft. No changes to frozen old methods.
//
// Policy: exact persisted original founder, qualified explicit full native panel,
// slot0, current immutable founder Owner, all connected accepted/pending audience
// ready/nonbattle. Storage also requires persisted nonbattle for every member
// AND applicant, including offline characters. No fee/refund/rank rule inferred.
// AliveReady is CURRENT audience readiness, not immutable audience movement ABA.
// Founder Owner equality retains its existing full immutable world/ABA lease.
// All access is confined to the existing game executor.
class OwnedGuildDisbandService {
public:
    using Repository=SqliteOwnedGuildMembershipRepository;
    using Panel=OwnedGuildLeaderPanelService;
    using Owner=Panel::Owner;
    using Resolve=Panel::Resolve;
    // Host must examine every captured member and pending applicant, and EVERY
    // connected matching-character session. Exact account/character identity,
    // projected/world-ready/nonbattle required. Offline audience returns ready
    // only for world policy; repository still checks all persistent snapshots.
    // Resolve and AliveReady MUST read retained current world readiness plus the
    // captured account/character identities ONLY. Both proofs execute inside
    // disband's transaction; after_write runs AFTER membership/governance/apps
    // removal. A callback that reloads membership/governance/panel to require
    // still-active membership would make EVERY successful disband roll back.
    // Existing Application guild_world_owner is world-only and can be reused.
    // Callbacks promise no storage or UI effects: no DB mutation/read-based
    // membership qualification, packet sends, panel reopen or executor reentry.
    // Game-executor serialization is required, not an incidental assumption.
    using AliveReady=std::function<bool(const Panel::State&)>;
    struct ActionPlan {
        Panel::State panel;
        std::uint8_t slot{};
        std::uint64_t publication{};
        bool operator==(const ActionPlan&) const=default;
    };
    OwnedGuildDisbandService(Repository& repository,Panel& panels,Resolve resolve,AliveReady alive_ready):
        repository_(repository),panels_(panels),resolve_(std::move(resolve)),alive_ready_(std::move(alive_ready)){}

    // MUST be called once per75 before ANY recursive batch prefix. Parser accepts
    // structural slots0..49, but this qualified current recipient puts self0.
    // No prepare retry after help/Tick/B8, SQL failure or readonly refresh.
    std::optional<ActionPlan> prepare_action(std::uint64_t session,std::uint8_t slot) const {
        try {
            if(slot!=0 || !session || !resolve_ || !alive_ready_)return {};
            const auto publication=panels_.action_publication(session);
            if(!publication || !publication->serial || !founder(publication->state))return {};
            const auto& state=publication->state;
            if(state.owner.session!=session || resolve_(session)!=std::optional{state.owner} ||
               !alive_ready_(state))return {};
            // Even an incorrectly stateful callback cannot return authority
            // from the publication that existed before it invalidated/reopened.
            if(resolve_(session)!=std::optional{state.owner} ||
               panels_.action_publication(session)!=publication)return {};
            return ActionPlan{state,slot,publication->serial};
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
            // Old stale replay must not consume a different, genuinely fresh
            // explicit open. Runtime batch guard separately revokes at boundary.
            if(publication->serial!=plan.publication || publication->state!=plan.panel)return false;
            const bool qualified=current(plan);
            // current() may invoke callbacks: compare again before consumption.
            // Consume matching permission BEFORE SQL, including denied readiness
            // and stale SQL snapshots. Keep cached rows for native92 cleanup.
            if(!consume_matching(plan) || !qualified)return false;
            const auto state=plan.panel;
            const auto proof=[this,state] {
                // This same callback runs before AND after SQL retirement.
                // World-only readiness must not depend on now-deleted rows.
                if(!resolve_ || resolve_(state.owner.session)!=std::optional{state.owner} ||
                   !alive_ready_ || !alive_ready_(state) ||
                   resolve_(state.owner.session)!=std::optional{state.owner})
                    throw DatabaseError("CUSTOM-0081 immutable founder/all audience readiness changed");
                // No mutation may borrow a panel reopened inside a SQL proof.
                // There should be NO authoritative publication after consume.
                // A surviving readonly cached projection is expected and safe.
                if(panels_.action_publication(state.owner.session))
                    throw DatabaseError("CUSTOM-0081 action authority reopened inside disband proof");
            };
            repository_.disband(state.leader,state.applications,{proof,proof});
            return true;
        }catch(...){
            // Preserve a distinct fresh explicit publication at service level;
            // host still must revoke actor permissions at EACH75 boundary.
            // Failure to qualify any current publication revokes cached authority.
            consume_matching(plan);return false;
        }
    }
    void invalidate(std::uint64_t session){panels_.invalidate(session);}
    void observe_world(std::uint64_t session){panels_.observe_world(session);}
    // No independent cache. Do not erase Panel published rows before native92.
    void forget(std::uint64_t session){panels_.invalidate(session);}
private:
    bool consume_matching(const ActionPlan& plan) {
        const auto session=plan.panel.owner.session;
        const auto current=panels_.action_publication(session);
        if(current && (current->serial!=plan.publication || current->state!=plan.panel))return false;
        panels_.invalidate(session);return true;
    }
    static bool founder(const Panel::State& state) {
        if(!state.owner.session || !state.owner.account || !state.owner.character ||
           !state.owner.world_generation || state.rows.empty() ||
           state.owner.account!=state.leader.governance.owner_account ||
           state.owner.character!=state.leader.governance.owner_character ||
           state.membership.guild_id!=state.leader.governance.guild_id ||
           state.membership.guild_id!=state.leader.membership.guild_id ||
           state.membership.guild_revision!=state.leader.membership.guild_revision ||
           state.membership.membership_revision!=state.leader.membership.membership_revision ||
           state.membership.name_utf8!=state.leader.membership.name_utf8)return false;
        const auto& self=state.rows.front();
        if(self.role!=3 || self.application || self.identity.account_id!=state.owner.account ||
           self.identity.character_id!=state.owner.character ||
           self.identity.membership_revision!=state.membership.membership_revision)return false;
        auto identity=self.identity;identity.membership_revision=0;
        return identity==state.leader.identity;
    }
    Repository& repository_;Panel& panels_;Resolve resolve_;AliveReady alive_ready_;
};
}
