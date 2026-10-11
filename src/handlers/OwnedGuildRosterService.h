#pragma once
#include "db/SqliteGuildRosterRepository.h"
#include "handlers/OwnedPrivateChatService.h"
#include "protocol/RecoveredGuildRoster.h"
#include "text/LegacyChineseCodec.h"
#include <functional>
#include <map>
#include <set>
namespace god2 {
// CUSTOM-0076: read-only administrator-owned membership projection. Every
// member receives native role1 (洞府成員); this grants NO officer/leader action.
// No invented8E economics/header is sent. The original panel entry is OPEN.
class OwnedGuildRosterService {
public:
    using Peer=OwnedPrivateChatService::Peer;
    using Resolve=std::function<std::optional<Peer>(std::uint64_t)>;
    using Read=std::function<std::optional<StoredGuildRoster>(std::uint64_t,std::uint64_t)>;
    using Online=std::function<std::set<std::uint32_t>()>;
    struct State {
        Peer peer;
        std::optional<StoredGuildRoster> roster;
        std::set<std::uint32_t> online;
        bool operator==(const State&) const=default;
    };
    struct Plan {State next;std::vector<std::uint8_t> logical;};
    OwnedGuildRosterService(Resolve resolve,Read read,Online online):
        resolve_(std::move(resolve)),read_(std::move(read)),online_(std::move(online)){}
    std::optional<Plan> prepare(std::uint64_t session) const {
        try {
            const auto next=read_state(session);if(!next)return {};
            const auto at=sent_.find(session);
            const State* previous=at!=sent_.end() && same_actor(at->second.peer,next->peer)?&at->second:nullptr;
            const bool reset=previous && (previous->peer.name!=next->peer.name ||
                previous->peer.simplified!=next->peer.simplified);
            Plan plan{*next,{}};
            if(previous && *previous==*next)return current(plan)?std::optional{plan}:std::nullopt;
            auto append=[&](const auto& record){plan.logical.insert(plan.logical.end(),record.begin(),record.end());};
            // Native92 self removal resets the roster AND closes its window.
            // Use it only for real membership removal/switch; never page ends.
            if(previous && previous->roster && (reset || !next->roster ||
               previous->roster->membership.guild_id!=next->roster->membership.guild_id))
            {
                // Remove others first, self last. A changed native Actor name
                // may no longer match the old self row, so self92 alone would
                // otherwise leave stale rows instead of triggering reset.
                for(std::size_t slot=1;slot<previous->roster->members.size();++slot)
                    append(RecoveredGuildRoster::remove(static_cast<std::uint8_t>(slot)));
                append(RecoveredGuildRoster::remove(0));
            }
            if(next->roster) {
                const auto& roster=*next->roster;
                if(roster.members.empty() || roster.members.size()>50 ||
                   roster.requester_account!=next->peer.account || roster.requester_character!=next->peer.character)
                    return {};
                std::vector<std::vector<std::uint8_t>> rows;
                std::set<std::string> names;
                const GuildRosterMember* self=nullptr;
                for(const auto& member:roster.members)if(member.character_id==next->peer.character) {
                    if(self || member.account_id!=next->peer.account)return {};self=&member;
                }
                if(!self || self->name_utf8!=next->peer.name)return {};
                auto make_row=[&](const GuildRosterMember& member,std::uint8_t slot) {
                    if(!member.role || member.character_id>UINT32_MAX || !member.character_id ||
                       member.profile[29]<1 || member.profile[29]>8)
                        throw std::invalid_argument("Guild member lacks qualified level/profession");
                    const auto level=RecoveredRoleLevel::parse(member.role->logical);
                    if(!level || !level->level())throw std::invalid_argument("Guild member level missing");
                    // Exact names are identity, never OpenCC aliases or '?' fallback.
                    const auto name=LegacyChineseCodec::encode(member.name_utf8,next->peer.simplified);
                    // Native551DE0 is bytewise case-insensitive, including
                    // ASCII-valued trail bytes. This collision key protects
                    // projection identity; it never changes saved/auth names.
                    auto comparison=name;
                    for(auto& byte:comparison)if(byte>='A' && byte<='Z')byte=static_cast<char>(byte+('a'-'A'));
                    if(LegacyChineseCodec::decode(name,next->peer.simplified)!=member.name_utf8 || !names.insert(comparison).second)
                        throw std::invalid_argument("Guild projected name is ambiguous");
                    // CUSTOM presentation: bit0 selects the native first two
                    // status icons using the current owned ready-session set.
                    return RecoveredGuildRoster::member(slot,1,level->level(),member.profile[29],
                        next->online.contains(static_cast<std::uint32_t>(member.character_id))?1:0,name);
                };
                // Slot0 is always this recipient's self. This is a session-local
                // roster identity, NOT the database character/account slot.
                rows.push_back(make_row(*self,0));
                for(const auto& member:roster.members)if(member.character_id!=self->character_id)
                    rows.push_back(make_row(member,static_cast<std::uint8_t>(rows.size())));
                if(previous && previous->roster && !reset && previous->roster->membership.guild_id==roster.membership.guild_id)
                    for(std::size_t slot=1;slot<previous->roster->members.size();++slot)
                        append(RecoveredGuildRoster::remove(static_cast<std::uint8_t>(slot)));
                // Remove others BEFORE upserts: native91 rejects even updates
                // when its count is50. Preserve self to avoid reset/close.
                for(const auto& row:rows)append(row);
            }
            if(!current(plan))return {};
            return plan;
        }catch(const std::exception&){return {};}
    }
    bool current(const Plan& plan) const {
        try {return read_state(plan.next.peer.session)==std::optional{plan.next};}
        catch(const std::exception&){return false;}
    }
    void published(const Plan& plan) {sent_.insert_or_assign(plan.next.peer.session,plan.next);}
    bool panel_ready(std::uint64_t session) const {
        const auto at=sent_.find(session);
        return at!=sent_.end() && at->second.roster && current(Plan{at->second,{}});
    }
    void forget(std::uint64_t session) {sent_.erase(session);}
private:
    static bool same_actor(const Peer& a,const Peer& b) {
        return a.session==b.session && a.account==b.account && a.character==b.character;
    }
    std::optional<State> read_state(std::uint64_t session) const {
        if(!session || !resolve_ || !read_ || !online_)return {};
        const auto peer=resolve_(session);
        if(!peer || peer->session!=session || !peer->account || !peer->character || !peer->ready || peer->name.empty())return {};
        State state{*peer,read_(peer->account,peer->character),{}};
        if(state.roster) {
            const auto online=online_();
            for(const auto& member:state.roster->members)
                if(member.character_id<=UINT32_MAX && online.contains(static_cast<std::uint32_t>(member.character_id)))
                    state.online.insert(static_cast<std::uint32_t>(member.character_id));
        }
        return state;
    }
    Resolve resolve_;Read read_;Online online_;std::map<std::uint64_t,State> sent_;
};
}
