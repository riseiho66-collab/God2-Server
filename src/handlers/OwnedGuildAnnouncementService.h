#pragma once
#include "db/SqliteOwnedGuildAnnouncementRepository.h"
#include "handlers/OwnedGuildLeaderPanelService.h"
#include "protocol/RecoveredGuildAnnouncement.h"
#include <chrono>
#include <limits>
#include <map>
namespace god2 {
// CUSTOM-0078 founder announcement policy, using native79/98 codecs only.
// Successful explicit help publication grants a single-use300s server lease.
// 300s is CUSTOM, not a recovered native timer. Local27 edit/local30 cancel
// emit no request: neither grants permission nor proves immediate revocation.
// Game-executor confined; prepare_action must precede world-batch prefix work.
class OwnedGuildAnnouncementService {
public:
    using Repository=SqliteOwnedGuildAnnouncementRepository;
    using Panel=OwnedGuildLeaderPanelService;
    using Owner=Panel::Owner;
    using Resolve=Panel::Resolve;
    using Time=OwnedGuildMembershipConversation::Time;
    using Wire=RecoveredGuildAnnouncement;
    static constexpr auto lifetime=std::chrono::seconds{300};
    struct Plan {
        Panel::Plan panel;
        Repository::Snapshot announcement;
        std::vector<std::uint8_t> logical;
    };
    struct ActionPlan {
        Panel::State panel;
        Repository::Snapshot announcement;
        std::uint64_t publication{};
        Time opened{},expires{};
        bool operator==(const ActionPlan&) const=default;
    };
    OwnedGuildAnnouncementService(Repository& repository,Panel& panels,Resolve resolve):
        repository_(repository),panels_(panels),resolve_(std::move(resolve)){}
    // Explicit help opens the frozen complete member panel. Readonly projection
    // never creates write authority, including member views during founder battle.
    // Host uses readonly preparation for qualified open/save echo, not unsolicited
    // Tick refresh: native98 may overwrite a locally edited unsaved draft.
    std::optional<Plan> prepare(std::uint64_t session,bool open_panel=false) const {
        try {
            const auto panel=panels_.prepare(session,open_panel);if(!panel)return {};
            auto snapshot=repository_.load(panel->next.membership.guild_id);
            const auto text=snapshot.value?snapshot.value->text_utf8:std::string{};
            const auto update=Wire::update(Wire::text_request(text,panel->next.owner.name_codepage));
            if(!update)return {};
            Plan plan{*panel,std::move(snapshot),panel->logical};
            plan.logical.insert(plan.logical.end(),update->begin(),update->end());
            if(!current(plan))return {};return plan;
        }catch(...){return {};}
    }
    bool current(const Plan& plan) const {
        try {
            return panels_.current(plan.panel) && resolve_ &&
                resolve_(plan.panel.next.owner.session)==std::optional{plan.panel.next.owner} &&
                repository_.load(plan.panel.next.membership.guild_id)==plan.announcement;
        }catch(...){return false;}
    }
    // Call only after the complete logical batch successfully queues and current
    // still holds. open_panel must originate from qualified explicit native help.
    bool published(const Plan& plan,Time now) {
        try {
            if(!current(plan))return false;
            const auto session=plan.panel.next.owner.session;
            const auto old=leases_.find(session);
            if(!plan.panel.open_panel) {
                if(old!=leases_.end() && (old->second.panel!=plan.panel.next ||
                    old->second.announcement!=plan.announcement))leases_.erase(old);
                return panels_.published(plan.panel);
            }
            // Any actual explicit reopen supersedes the prior publication,
            // including a member publication; no fabricated role or editor flag.
            leases_.erase(session);
            if(!panels_.published(plan.panel))return false;
            const auto& state=plan.panel.next;
            if(!founder(state))return true;
            if(now>Time::max()-lifetime || serial_==std::numeric_limits<std::uint64_t>::max())return false;
            if(!current(plan))return false;
            leases_.emplace(session,ActionPlan{state,plan.announcement,++serial_,now,now+lifetime});
            return true;
        }catch(...){return false;}
    }
    std::optional<ActionPlan> prepare_action(std::uint64_t session,Time now) const {
        try {
            const auto at=leases_.find(session);if(at==leases_.end() || !current(at->second,now))return {};
            return at->second;
        }catch(...){return {};}
    }
    bool current(const ActionPlan& plan,Time now) const {
        try {
            const auto at=leases_.find(plan.panel.owner.session);
            return at!=leases_.end() && at->second==plan && plan.publication &&
                now>=plan.opened && now<plan.expires && founder(plan.panel) &&
                current(Plan{Panel::Plan{plan.panel,{},false},plan.announcement,{}});
        }catch(...){return false;}
    }
    // The immutable action captured before prefix work is consumed before any
    // request canonicality/encoding or SQL attempt. Failed saves cannot replay.
    std::optional<Repository::Snapshot> execute(const ActionPlan& plan,const Wire::Request& request,Time now) {
        try {
            const auto at=leases_.find(plan.panel.owner.session);
            if(at==leases_.end() || at->second!=plan)return {};
            const bool qualified=current(plan,now);
            leases_.erase(plan.panel.owner.session);
            if(!qualified)return {};
            const auto text=Wire::text_utf8(request,plan.panel.owner.name_codepage);
            const auto owner=plan.panel.owner;
            const auto proof=[this,owner] {
                if(!resolve_ || resolve_(owner.session)!=std::optional{owner})
                    throw DatabaseError("Guild announcement immutable world lease changed");
            };
            return repository_.save(plan.panel.leader,plan.announcement,text,{proof,proof});
        }catch(...){return {};}
    }
    void invalidate(std::uint64_t session){leases_.erase(session);}
    void observe_world(std::uint64_t session) {
        const auto at=leases_.find(session);if(at==leases_.end())return;
        try {if(!resolve_ || resolve_(session)!=std::optional{at->second.panel.owner})invalidate(session);}
        catch(...){invalidate(session);}
    }
    void forget(std::uint64_t session){leases_.erase(session);}
private:
    static bool founder(const Panel::State& state) {
        return state.owner.session && state.owner.account && state.owner.character &&
            state.owner.account==state.leader.governance.owner_account &&
            state.owner.character==state.leader.governance.owner_character &&
            state.membership.guild_id==state.leader.governance.guild_id &&
            !state.rows.empty() && state.rows.front().role==3 && !state.rows.front().application &&
            state.rows.front().identity.account_id==state.owner.account &&
            state.rows.front().identity.character_id==state.owner.character;
    }
    Repository& repository_;Panel& panels_;Resolve resolve_;
    std::map<std::uint64_t,ActionPlan> leases_;std::uint64_t serial_{};
};
}
