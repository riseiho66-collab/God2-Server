#pragma once
#include "db/DbTypes.h"
#include "db/SqliteOwnedGuildMembershipRepository.h"
#include "handlers/OwnedGuildMembershipConversation.h"
#include "protocol/OwnedGuildPanelHeader.h"
#include "protocol/RecoveredGuildRoster.h"
#include "text/LegacyChineseCodec.h"
#include <functional>
#include <limits>
#include <map>
#include <set>

namespace god2 {
// CUSTOM-0078 player-created governance only. Native role/slot are display,
// never authority. Frozen administrator guild0076/0077 paths are untouched.
// Scope: reject the entire panel when members+pending exceed native50. There
// is no silent truncation, fabricated page or borrowed officer permission.
class OwnedGuildLeaderPanelService {
public:
    using Repository=SqliteOwnedGuildMembershipRepository;
    using Owner=OwnedGuildMembershipConversation::Owner;
    using Resolve=std::function<std::optional<Owner>(std::uint64_t)>;
    using Membership=std::function<std::optional<StoredGuildMembership>(std::uint64_t,std::uint64_t)>;
    using Online=std::function<std::set<std::uint32_t>()>;
    enum class Action {Approve,Reject};
    struct Row {
        Repository::Identity identity;
        std::optional<Repository::Application> application;
        std::uint8_t role{};
        bool operator==(const Row&) const=default;
    };
    struct State {
        Owner owner;
        StoredGuildMembership membership;
        Repository::Leader leader;
        std::vector<Repository::Application> applications;
        std::vector<Row> rows;
        std::set<std::uint32_t> online;
        bool operator==(const State&) const=default;
    };
    struct Plan {State next;std::vector<std::uint8_t> logical;bool open_panel=false;};
    struct ActionPlan {
        State panel;
        Action action;
        std::uint8_t slot{};
        std::uint64_t publication{};
        Repository::Application application;
        bool operator==(const ActionPlan&) const=default;
    };
    struct LeavePlan {
        State panel;
        std::uint64_t publication{};
        bool operator==(const LeavePlan&) const=default;
    };
    struct ClearPlan {
        Owner owner;
        State previous;
        std::uint64_t publication{};
        std::vector<std::uint8_t> logical;
    };
    // CUSTOM-0080 read-only view for the independent native72 kick service.
    // This accessor never creates, refreshes or consumes panel authority.
    struct ActionPublication {
        State state;
        std::uint64_t serial{};
        bool operator==(const ActionPublication&) const=default;
    };
    OwnedGuildLeaderPanelService(Repository& repo,Resolve resolve,Membership membership,Online online):
        repo_(repo),resolve_(std::move(resolve)),membership_(std::move(membership)),online_(std::move(online)){}

    std::optional<Plan> prepare(std::uint64_t session,bool open_panel=false) const {
        try {
            auto next=read_state(session);if(!next)return {};
            Plan plan{std::move(*next),{},open_panel};
            const auto old=published_.find(session);
            if(!open_panel && old!=published_.end() && old->second.state==plan.next)
                return current(plan)?std::optional{plan}:std::nullopt;
            auto append=[&](const auto& bytes){plan.logical.insert(plan.logical.end(),bytes.begin(),bytes.end());};
            if(old!=published_.end()) {
                const auto& previous=old->second.state;
                // Remove every old non-self slot before updates: native91 at
                // count50 ignores even existing upserts. Self92 also closes.
                for(std::size_t slot=1;slot<previous.rows.size();++slot)
                    append(RecoveredGuildRoster::remove(static_cast<std::uint8_t>(slot)));
                if(previous.owner.account!=plan.next.owner.account || previous.owner.character!=plan.next.owner.character ||
                   previous.owner.name_codepage!=plan.next.owner.name_codepage ||
                   previous.membership.guild_id!=plan.next.membership.guild_id ||
                   previous.rows.front().identity.name_utf8!=plan.next.rows.front().identity.name_utf8)
                    append(RecoveredGuildRoster::remove(0));
            }
            for(std::size_t slot=0;slot<plan.next.rows.size();++slot) {
                const auto& row=plan.next.rows[slot];
                const auto level=RecoveredRoleLevel::parse(row.identity.role->logical);
                const auto name=LegacyChineseCodec::encode(row.identity.name_utf8,plan.next.owner.name_codepage==936);
                append(RecoveredGuildRoster::member(static_cast<std::uint8_t>(slot),row.role,level->level(),
                    row.identity.profile[29],plan.next.online.contains(static_cast<std::uint32_t>(row.identity.character_id))?1:0,name));
            }
            if(open_panel) {
                auto header=OwnedGuildPanelHeader::readonly_members(plan.next.leader.roster.size());if(!header)return {};
                (*header)[1+0x17]=plan.next.leader.governance.capacity; // CUSTOM reviewed capacity20; pending not members.
                append(*header); // status6/inactive economics remain unchanged.
            }
            if(!current(plan))return {};
            return plan;
        }catch(...){return {};}
    }
    bool current(const Plan& plan) const {
        try{return read_state(plan.next.owner.session)==std::optional{plan.next};}catch(...){return false;}
    }
    bool published(const Plan& plan) {
        try {
            if(!current(plan))return false;
            const auto at=published_.find(plan.next.owner.session);
            // Benign unchanged Tick retains its current authorization state;
            // changed projections revoke it and never reopen the panel.
            if(!plan.open_panel && at!=published_.end() && at->second.state==plan.next)return true;
            if(publication_==std::numeric_limits<std::uint64_t>::max())return false;
            published_.insert_or_assign(plan.next.owner.session,Published{plan.next,++publication_,plan.open_panel});return true;
        }catch(...){return false;}
    }
    std::optional<ActionPlan> prepare_action(std::uint64_t session,Action action,std::uint8_t slot) const {
        try {
            const auto at=published_.find(session);if(at==published_.end() || !at->second.authority)return {};
            const auto& state=at->second.state;
            if((action!=Action::Approve && action!=Action::Reject) || slot>=state.rows.size() ||
               !state.rows[slot].application || state.rows[slot].role!=0 ||
               state.owner.account!=state.leader.governance.owner_account ||
               state.owner.character!=state.leader.governance.owner_character ||
               !current(Plan{state,{}}))return {};
            return ActionPlan{state,action,slot,at->second.serial,*state.rows[slot].application};
        }catch(...){return {};}
    }
    bool current(const ActionPlan& plan) const {
        try {
            const auto lease=prepare_action(plan.panel.owner.session,plan.action,plan.slot);
            return lease && *lease==plan;
        }catch(...){return false;}
    }
    bool execute(const ActionPlan& plan) {
        try {
            if(!current(plan))return false;
            // Consume before any SQL attempt. No replay after rollback/reject;
            // a fresh complete panel must be published for another action.
            invalidate(plan.panel.owner.session);
            const auto owner=plan.panel.owner;
            const auto proof=[this,owner] {
                // Compare only world ownership here. Approval legitimately
                // changes membership generation, roster and pending snapshot.
                // Repo independently CAS-checks all SQL identities atomically.
                if(!resolve_ || resolve_(owner.session)!=std::optional{owner})
                    throw DatabaseError("Guild leader world lease changed");
            };
            const Repository::Proof pair{proof,proof};
            const auto& application=plan.application;
            if(plan.action==Action::Approve)repo_.approve(plan.panel.leader,application,pair);
            else if(plan.action==Action::Reject)repo_.reject(plan.panel.leader,application,pair);
            else return false;
            return true;
        }catch(...){return false;}
    }
    // CUSTOM-0078 ordinary accepted member only. The exact published panel,
    // not the client slot or UI role, supplies the immutable SQL/world lease.
    std::optional<LeavePlan> prepare_leave(std::uint64_t session,std::uint8_t slot) const {
        try {
            const auto at=published_.find(session);
            if(slot!=0 || at==published_.end() || !at->second.authority)return {};
            const auto& state=at->second.state;
            if(state.rows.empty() || state.rows.front().role!=1 || state.rows.front().application ||
               state.owner.character==state.leader.governance.owner_character ||
               !current(Plan{state,{}}))return {};
            return LeavePlan{state,at->second.serial};
        }catch(...){return {};}
    }
    bool current(const LeavePlan& plan) const {
        const auto fresh=prepare_leave(plan.panel.owner.session,0);return fresh && *fresh==plan;
    }
    bool leave(const LeavePlan& plan,std::uint8_t slot) {
        try {
            if(slot!=0 || !current(plan))return false;
            invalidate(plan.panel.owner.session);
            const auto owner=plan.panel.owner;
            const auto proof=[this,owner] {
                if(!resolve_ || resolve_(owner.session)!=std::optional{owner})
                    throw DatabaseError("Guild member leave world lease changed");
            };
            auto self=plan.panel.rows.front().identity;self.membership_revision=0;
            repo_.member_leave(self,plan.panel.membership,plan.panel.leader,plan.panel.applications,{proof,proof});
            return true;
        }catch(...){return false;}
    }
    // Remove the player-created native cache after a qualified loss of SQL
    // membership before the frozen administrator roster path resumes. Clearing
    // self last lets native92 remove the old list and close the stale panel.
    std::optional<ClearPlan> prepare_clear(std::uint64_t session) const {
        try {
            const auto at=published_.find(session);if(at==published_.end() || !resolve_ || !membership_)return {};
            const auto owner=resolve_(session);
            if(!owner || owner->session!=session || owner->account!=at->second.state.owner.account ||
               owner->character!=at->second.state.owner.character ||
               membership_(owner->account,owner->character))return {};
            ClearPlan plan{*owner,at->second.state,at->second.serial,{}};
            for(std::size_t slot=1;slot<plan.previous.rows.size();++slot) {
                const auto remove=RecoveredGuildRoster::remove(static_cast<std::uint8_t>(slot));
                plan.logical.insert(plan.logical.end(),remove.begin(),remove.end());
            }
            const auto self=RecoveredGuildRoster::remove(0);plan.logical.insert(plan.logical.end(),self.begin(),self.end());
            if(!current(plan))return {};return plan;
        }catch(...){return {};}
    }
    bool current(const ClearPlan& plan) const {
        try {
            const auto at=published_.find(plan.owner.session);
            return at!=published_.end() && at->second.serial==plan.publication && at->second.state==plan.previous &&
                resolve_ && resolve_(plan.owner.session)==std::optional{plan.owner} && membership_ &&
                !membership_(plan.owner.account,plan.owner.character);
        }catch(...){return false;}
    }
    bool cleared(const ClearPlan& plan) {
        if(!current(plan))return false;published_.erase(plan.owner.session);return true;
    }
    bool cached(std::uint64_t session) const {return published_.contains(session);}
    std::optional<ActionPublication> action_publication(std::uint64_t session) const {
        try {
            const auto at=published_.find(session);
            if(at==published_.end() || !at->second.authority || at->second.state.rows.empty() ||
               !current(Plan{at->second.state,{}}))return {};
            return ActionPublication{at->second.state,at->second.serial};
        }catch(...){return {};}
    }
    // UI action-kind classification only; stale cached rows are NOT authority.
    // Native72 shares rejection/kick semantics, so a failed rejection must
    // never be retried as a different action against a newly refreshed slot.
    std::optional<std::uint8_t> cached_row_role(std::uint64_t session,std::uint8_t slot) const {
        const auto at=published_.find(session);
        if(at==published_.end() || slot>=at->second.state.rows.size())return {};
        return at->second.state.rows[slot].role;
    }
    // Active play invalidates authority but retains native slot cache so the
    // next projection can remove old rows before native91 rebuilds the list.
    void invalidate(std::uint64_t session) {
        const auto at=published_.find(session);if(at!=published_.end())at->second.authority=false;
    }
    void observe_world(std::uint64_t session) {
        const auto at=published_.find(session);if(at==published_.end())return;
        try {if(!resolve_ || resolve_(session)!=std::optional{at->second.state.owner})invalidate(session);}
        catch(...){invalidate(session);}
    }
    void forget(std::uint64_t session){published_.erase(session);}
private:
    struct Published {State state;std::uint64_t serial{};bool authority{};};
    std::optional<State> read_state(std::uint64_t session) const {
        if(!session || !resolve_ || !membership_ || !online_)return {};
        const auto owner=resolve_(session);
        if(!owner || owner->session!=session || !owner->account || !owner->character || !owner->world_generation ||
           (owner->name_codepage!=950 && owner->name_codepage!=936))return {};
        const auto membership=membership_(owner->account,owner->character);if(!membership)return {};
        const auto gov=repo_.governance(membership->guild_id);
        // An ordinary member needs the exact governance/roster snapshot, not
        // the founder's current gameplay action authority. Their own world
        // and repository nonbattle lease still qualify self-leave. Founder
        // panels/actions retain the existing leader() nonbattle restriction.
        const auto leader=owner->character==gov.owner_character?
            repo_.leader(gov.owner_account,gov.owner_character):
            repo_.governance_snapshot(gov.owner_account,gov.owner_character);
        if(leader.governance!=gov || leader.membership.guild_id!=membership->guild_id ||
           leader.membership.guild_revision!=membership->guild_revision || leader.membership.name_utf8!=membership->name_utf8)return {};
        const auto identity=repo_.identity(owner->account,owner->character);
        const auto self=std::find_if(leader.roster.begin(),leader.roster.end(),[&](const auto& member){return member.character_id==owner->character;});
        if(self==leader.roster.end() || self->account_id!=owner->account || self->membership_revision!=membership->membership_revision)return {};
        auto expected=*self;expected.membership_revision=0;if(identity!=expected)return {};
        State state{*owner,*membership,leader,repo_.applications(membership->guild_id),{}, {}};
        if(leader.roster.empty() || leader.roster.size()>gov.capacity ||
           state.applications.size()>50-leader.roster.size())return {};
        auto role=[&](const auto& member)->std::uint8_t {
            return member.account_id==gov.owner_account && member.character_id==gov.owner_character?3:1;
        };
        state.rows.push_back({*self,{},role(*self)});
        auto members=leader.roster;std::sort(members.begin(),members.end(),[](const auto& a,const auto& b){return a.character_id<b.character_id;});
        for(const auto& member:members)if(member.character_id!=owner->character)state.rows.push_back({member,{},role(member)});
        std::sort(state.applications.begin(),state.applications.end(),[](const auto& a,const auto& b){return a.id<b.id;});
        for(const auto& app:state.applications) {
            if(app.target.id!=membership->guild_id || app.target.name_utf8!=membership->name_utf8 ||
               app.target.revision>membership->guild_revision || app.applicant.membership_revision ||
               membership_(app.applicant.account_id,app.applicant.character_id))return {};
            state.rows.push_back({app.applicant,app,0});
        }
        std::set<std::uint64_t> characters,application_ids;
        std::set<std::pair<std::uint64_t,std::uint8_t>> account_slots;
        std::set<std::string> names;
        const auto online=online_();
        for(const auto& row:state.rows) {
            const auto& member=row.identity;
            if(!member.character_id || member.character_id>UINT32_MAX || !member.account_id || member.slot>1 ||
               !characters.insert(member.character_id).second || !account_slots.emplace(member.account_id,member.slot).second ||
               !member.role || member.profile[29]<1 || member.profile[29]>8)return {};
            if(row.application && !application_ids.insert(row.application->id).second)return {};
            const auto level=RecoveredRoleLevel::parse(member.role->logical);if(!level || !level->level())return {};
            auto name=LegacyChineseCodec::encode(member.name_utf8,owner->name_codepage==936);
            if(name.empty() || name.size()>15 || name.find('\0')!=std::string::npos || name.find('%')!=std::string::npos ||
               LegacyChineseCodec::decode(name,owner->name_codepage==936)!=member.name_utf8)return {};
            for(auto& byte:name)if(byte>='A' && byte<='Z')byte=static_cast<char>(byte+('a'-'A'));
            if(!names.insert(name).second)return {};
            if(online.contains(static_cast<std::uint32_t>(member.character_id)))state.online.insert(static_cast<std::uint32_t>(member.character_id));
        }
        if(resolve_(session)!=owner || online_()!=online)return {};
        return state;
    }
    Repository& repo_;Resolve resolve_;Membership membership_;Online online_;
    std::map<std::uint64_t,Published> published_;std::uint64_t publication_{};
};
}
