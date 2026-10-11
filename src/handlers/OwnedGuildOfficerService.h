#pragma once
// ARTIFACT DRAFT, NOT INSTALLED. CUSTOM-0082 PROPOSED.
// Include after repository officer declarations are integrated in a shadow.
#include "handlers/OwnedGuildLeaderPanelService.h"
#include <algorithm>
#include <utility>

namespace god2 {
// The frozen panel still owns self0/local slots/complete91/fullpanel single-use
// authority. This adapter adds93 only to proved existing recipient slots; it
// never changes old role-generation/readers, SQL founder, or pending approval.
// ALL owned panel writers must use this wrapper while feature51 is selected.
// Do not emit both wrapper and another writer's base91 in the same world tail.
class OwnedGuildOfficerProjectionDraft {
public:
    using Repo=SqliteOwnedGuildMembershipRepository;
    using Base=OwnedGuildLeaderPanelService;
    struct Plan {
        Base::Plan base;
        Repo::OfficerHistory history;
        std::vector<std::uint8_t> logical;
    };
    struct Publication {
        Base::ActionPublication base;
        Repo::OfficerHistory history;
        std::uint64_t projection_generation{};
        bool operator==(const Publication&) const=default;
    };
    OwnedGuildOfficerProjectionDraft(Repo& repo,Base& base):repo_(repo),base_(base){}
    std::optional<Plan> prepare(std::uint64_t session,bool open=false) const {
        const auto base=base_.prepare(session,open);return base?decorate_existing_base_plan(*base):std::nullopt;
    }
    // An existing announcement plan must be decorated, not independently
    // regenerated. Its exact original base and98 suffix remain authoritative.
    std::optional<Plan> decorate_existing_base_plan(const Base::Plan& base) const {
        try {
            Plan plan{base,repo_.officer_history(base.next.membership.guild_id),base.logical};
            const auto at=caches_.find(base.next.owner.session);
            if(plan.logical.empty() && (at==caches_.end() || at->second.state!=base.next || at->second.history!=plan.history))return {};
            if(!plan.logical.empty())for(std::size_t slot=0;slot<base.next.rows.size();++slot) {
                const auto& row=base.next.rows[slot];if(row.application)continue;
                const auto rank=Repo::officer_display_role(base.next.leader,row.identity,plan.history);
                if(rank!=row.role)plan.logical.insert(plan.logical.end(),{0x93,static_cast<std::uint8_t>(slot),rank});
            }
            return current(plan)?std::optional{plan}:std::nullopt;
        }catch(...){return {};}
    }
    bool current(const Plan& plan) const {
        try{return base_.current(plan.base) &&
            repo_.officer_history(plan.base.next.membership.guild_id)==plan.history;}catch(...){return false;}
    }
    // Call ONLY after this complete base+93 batch is accepted by the host world
    // tail. A codec/build result alone cannot qualify publication.
    bool published(const Plan& plan) {
        return published_with_external(plan,[&]{return base_.published(plan.base);});
    }
    // Publisher must call exactly ONE frozen Base publisher, either directly
    // or via Announcement::published. Confined to the same game executor,
    // with non-reentrant pure host resolvers. Queue success is not native ACK.
    bool published_with_external(const Plan& plan,const std::function<bool()>& publisher) {
        try {
            if(!current(plan) || !publisher || !publisher() || !current(plan)) {
                invalidate(plan.base.next.owner.session);return false;
            }
            const auto at=caches_.find(plan.base.next.owner.session);
            if(!plan.base.open_panel && at!=caches_.end() && at->second.state==plan.base.next && at->second.history==plan.history)return true;
            if(generation_==std::numeric_limits<std::uint64_t>::max()) {invalidate(plan.base.next.owner.session);return false;}
            caches_.insert_or_assign(plan.base.next.owner.session,Cache{plan.base.next,plan.history,++generation_,{}});return true;
        }catch(...){invalidate(plan.base.next.owner.session);return false;}
    }
    std::optional<Publication> publication(std::uint64_t session) const {
        try {
            const auto base=base_.action_publication(session);const auto at=caches_.find(session);
            if(!base || at==caches_.end() || base->state!=at->second.state ||
                repo_.officer_history(base->state.membership.guild_id)!=at->second.history)return {};
            return Publication{*base,at->second.history,at->second.generation};
        }catch(...){return {};}
    }
    std::optional<std::uint8_t> cached_role(std::uint64_t session,std::uint8_t slot) const {
        // Frozen displayed kind only, never newly refreshed SQL action authority.
        try {
            const auto at=caches_.find(session);if(at==caches_.end() || slot>=at->second.state.rows.size())return {};
            const auto& row=at->second.state.rows[slot];return row.application?std::optional<std::uint8_t>{std::uint8_t{0}}:
                std::optional{Repo::officer_display_role(at->second.state.leader,row.identity,at->second.history)};
        }catch(...){return {};}
    }
    void invalidate(std::uint64_t session){
        base_.invalidate(session);const auto at=caches_.find(session);
        if(at!=caches_.end())at->second.consumed.reset();
    }
    bool consume(const Publication& pub) {
        const auto session=pub.base.state.owner.session;
        if(publication(session)!=std::optional{pub})return false;
        base_.invalidate(session);caches_.at(session).consumed=pub.base.serial;return true;
    }
    bool consumed_current(const Publication& pub) const {
        // Pure cache witness for post-mutation SQL proofs. NO membership read.
        const auto at=caches_.find(pub.base.state.owner.session);
        return at!=caches_.end() && at->second.generation==pub.projection_generation &&
            at->second.state==pub.base.state && at->second.history==pub.history &&
            at->second.consumed==std::optional{pub.base.serial};
    }
    void observe_world(std::uint64_t session){base_.observe_world(session);}
    // Host settles Base::ClearPlan92 debt before forgetting both caches.
    void forget_after_clear(std::uint64_t session){caches_.erase(session);base_.forget(session);}
private:
    struct Cache {Base::State state;Repo::OfficerHistory history;std::uint64_t generation{};std::optional<std::uint64_t> consumed;};
    Repo& repo_;Base& base_;std::map<std::uint64_t,Cache> caches_;std::uint64_t generation_{};
};

class OwnedGuildOfficerServiceDraft {
public:
    using Repo=SqliteOwnedGuildMembershipRepository;
    using Panel=OwnedGuildLeaderPanelService;
    using Projection=OwnedGuildOfficerProjectionDraft;
    using Owner=Panel::Owner;
    enum class Action {Appoint,RemoveOffice,SelfLeave};
    // Captured before batch-prefix processing. Includes EVERY connected session
    // of accepted+pending identities, including duplicate sessions. Ordering
    // deterministic by session. Absence/offline target is permitted only by
    // explicit CUSTOM policy, never fabricated as native officer permission.
    struct WorldLease {std::vector<Owner> connected;bool operator==(const WorldLease&) const=default;};
    using Capture=std::function<std::optional<WorldLease>(const Panel::State&)>;
    // World/executor readiness ONLY inside SQL proof: no SQL membership,
    // governance or projection publication read after accepted self is removed.
    // Host must prove private-chat-peer/role/resources clear projection before
    // prefix + again before SQL; withinSQL guard catches profile/resource edits.
    using WorldCurrent=std::function<bool(const Panel::State&,const WorldLease&)>;
    struct Plan {
        Projection::Publication publication;
        Action action;
        std::uint8_t slot{};
        Repo::Identity target;
        StoredGuildMembership target_membership;
        WorldLease world;
        bool operator==(const Plan&) const=default;
    };
    OwnedGuildOfficerServiceDraft(Repo& repo,Projection& projection,Panel::Resolve resolve,Capture capture,WorldCurrent current):
        repo_(repo),projection_(projection),resolve_(std::move(resolve)),capture_(std::move(capture)),world_current_(std::move(current)){}
    std::optional<Plan> prepare(std::uint64_t session,Action action,std::uint8_t slot) const {
        try {
            const auto pub=projection_.publication(session);if(!pub || !pub->base.serial || !capture_ || !world_current_)return {};
            const auto& state=pub->base.state;if(slot>=state.rows.size())return {};
            const auto& row=state.rows[slot];if(row.application || !row.identity.membership_revision)return {};
            const auto role=Repo::officer_display_role(state.leader,row.identity,pub->history);
            const auto& gov=state.leader.governance;
            const bool founder=state.owner.account==gov.owner_account && state.owner.character==gov.owner_character;
            if(action==Action::SelfLeave) {
                if(slot!=0 || founder || role!=2 || row.identity.account_id!=state.owner.account ||
                   row.identity.character_id!=state.owner.character)return {};
            } else {
                // CUSTOM initial slice, not full original role2 administration.
                if(!founder || !slot || row.identity.character_id==gov.owner_character ||
                   role!=(action==Action::Appoint?1:2) ||
                   (action!=Action::Appoint && action!=Action::RemoveOffice))return {};
            }
            auto target=row.identity;target.membership_revision=0;
            const StoredGuildMembership membership{state.membership.guild_id,state.membership.name_utf8,
                state.membership.guild_revision,row.identity.membership_revision};
            const auto world=capture_(state);
            if(!world || !world_valid(state,*world) || !world_current_(state,*world) ||
               projection_.publication(session)!=pub)return {};
            return Plan{*pub,action,slot,target,membership,*world};
        }catch(...){return {};}
    }
    bool current(const Plan& plan) const {
        const auto next=prepare(plan.publication.base.state.owner.session,plan.action,plan.slot);return next && *next==plan;
    }
    bool execute(const Plan& plan) {
        const auto& state=plan.publication.base.state;const auto session=state.owner.session;
        try {
            const auto pub=projection_.publication(session);
            if(!pub){projection_.invalidate(session);return false;}
            // Never consume a different newly opened publication on stale replay.
            if(*pub!=plan.publication)return false;
            const bool valid=current(plan);
            // Callback may have reopened a fresh panel. Never consume that new
            // serial using a stale request, including a failed readiness call.
            if(projection_.publication(session)!=pub)return false;
            if(!valid){projection_.invalidate(session);return false;}
            if(!projection_.consume(plan.publication))return false;
            const auto proof=[this,&plan,&state] {
                if(!world_valid(state,plan.world) || !world_current_ ||
                   !world_current_(state,plan.world) || !projection_.consumed_current(plan.publication))
                    throw DatabaseError("Officer immutable world readiness/consumed publication conflict");
            };
            if(plan.action==Action::SelfLeave)repo_.officer_leave(plan.target,plan.target_membership,state.leader,
                state.applications,plan.publication.history,{proof,proof});
            else repo_.change_officer(state.leader,state.applications,plan.publication.history,plan.target,
                plan.target_membership,plan.action==Action::Appoint?Repo::OfficerAction::Appoint:
                    Repo::OfficerAction::RemoveOffice,{proof,proof});
            return true;
        }catch(...){projection_.invalidate(session);return false;}
    }
private:
    bool world_valid(const Panel::State& state,const WorldLease& lease) const {
        if(!resolve_ || lease.connected.empty())return false;
        std::uint64_t last_session=0;bool has_owner=false;std::set<std::uint32_t> characters;
        for(const auto& owner:lease.connected) {
            if(owner.session<=last_session || !owner.account || !owner.character || owner.character>UINT32_MAX ||
               !owner.world_generation || (owner.name_codepage!=950 && owner.name_codepage!=936) ||
               resolve_(owner.session)!=std::optional{owner})return false;
            last_session=owner.session;if(owner==state.owner)has_owner=true;
            const auto at=std::find_if(state.rows.begin(),state.rows.end(),[&](const auto& row){
                return row.identity.account_id==owner.account && row.identity.character_id==owner.character;});
            if(at==state.rows.end())return false;characters.insert(static_cast<std::uint32_t>(owner.character));
        }
        // This additionally binds every panel-online character. Complete duplicate
        // session enumeration is still the host Capture's explicit contract.
        return has_owner && characters==state.online && resolve_(state.owner.session)==std::optional{state.owner};
    }
    Repo& repo_;Projection& projection_;Panel::Resolve resolve_;Capture capture_;WorldCurrent world_current_;
};
}
