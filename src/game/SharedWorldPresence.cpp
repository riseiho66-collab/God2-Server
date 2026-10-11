#include "game/SharedWorldPresence.h"
#include <algorithm>
#include <limits>
#include <set>
#include <stdexcept>

namespace god2 {
namespace {
bool same_character_root(const RecoveredCharacter& a,const RecoveredCharacter& b) {
    return a.id==b.id && a.account_id==b.account_id && a.slot==b.slot &&
        a.profile==b.profile && a.created_at==b.created_at &&
        a.name_codepage==b.name_codepage && a.streamer_privilege==b.streamer_privilege;
}
}
void SharedWorldPresence::owner() const {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("Shared presence game owner mismatch");
}
bool SharedWorldPresence::character_reserved(std::uint64_t character) const {
    owner();if(!character)return false;
    for(const auto& [session,entry]:sessions_)
        if(entry.lease.character==character)return true;
    return false;
}
bool SharedWorldPresence::owned(const Lease& lease) const {
    const auto rows=characters_.list_for_account(lease.account);
    if(!std::any_of(rows.begin(),rows.end(),[&](const auto& row) {
        return row.id==lease.character && row.account_id==lease.account;
    }))return false;
    return true;
}
bool SharedWorldPresence::stored(const Lease& lease) const {
    if(!owned(lease))return false;
    const auto saved=characters_.load_position(lease.account,lease.character);
    return saved && *saved==lease.position;
}
std::optional<SharedWorldPresence::Lease> SharedWorldPresence::prepare(
    std::uint64_t session,std::uint64_t account,std::uint64_t character,
    std::uint16_t handle,const RecoveredPosition& position) {
    owner();
    if(snapshot_busy_)snapshot_reentered_=true;
    if(!session || !account || !character || handle>0x3fff || sessions_.contains(session))return std::nullopt;
    // Global exclusion is deliberate server policy, not inferred native scope.
    for(const auto& [id,entry]:sessions_)
        if(entry.lease.character==character || entry.lease.actor_handle==handle)return std::nullopt;
    if(generation_==std::numeric_limits<std::uint64_t>::max())
        throw std::overflow_error("Shared presence generation exhausted");
    Lease lease{session,account,character,generation_+1,handle,position};
    if(!stored(lease))return std::nullopt;
    sessions_.emplace(session,Entry{lease,false});++generation_;
    return lease;
}
bool SharedWorldPresence::current(const Lease& lease) const {
    owner();const auto found=sessions_.find(lease.session);
    return found!=sessions_.end() && found->second.lease==lease && owned(lease);
}
std::optional<SharedWorldPresence::Lease> SharedWorldPresence::prepare_geometry(
    std::uint64_t session,std::uint64_t account,std::uint64_t character,std::uint16_t handle,
    std::uint16_t area,std::uint16_t scene,std::uint16_t x,std::uint16_t y) {
    owner();if(snapshot_busy_)snapshot_reentered_=true;
    if(!session || !account || !character || handle>0x3fff)return std::nullopt;
    const auto saved=characters_.load_position(account,character);
    if(!saved || saved->area!=area || saved->scene!=scene || saved->x!=x || saved->y!=y)return std::nullopt;
    return prepare(session,account,character,handle,*saved);
}
bool SharedWorldPresence::preparation_current(const Lease& lease) const {
    owner();return current(lease) && stored(lease);
}
bool SharedWorldPresence::activate(const Lease& lease,std::uint16_t handle) {
    owner();if(snapshot_busy_)snapshot_reentered_=true;
    const auto found=sessions_.find(lease.session);
    if(found==sessions_.end() || found->second.active || handle!=lease.actor_handle || !preparation_current(lease))return false;
    found->second.active=true;return true;
}
bool SharedWorldPresence::ready(const Lease& lease) const {
    owner();const auto found=sessions_.find(lease.session);
    return found!=sessions_.end() && found->second.active && current(lease);
}
bool SharedWorldPresence::retained_ready_current(const Lease& lease) const {
    owner();const auto found=sessions_.find(lease.session);
    return found!=sessions_.end() && found->second.active && found->second.lease==lease;
}
std::optional<SharedWorldPresence::Lease> SharedWorldPresence::ready_lease(
    std::uint64_t session,std::uint64_t account,std::uint64_t character) const {
    owner();if(!session || !account || !character)return std::nullopt;
    const auto found=sessions_.find(session);
    if(found==sessions_.end() || !found->second.active ||
       found->second.lease.account!=account || found->second.lease.character!=character)return std::nullopt;
    const auto lease=found->second.lease;
    if(!ready(lease))return std::nullopt;
    return lease;
}
std::optional<std::vector<SharedWorldPresence::ReadyCharacter>> SharedWorldPresence::ready_characters() const {
    owner();
    if(snapshot_busy_){snapshot_reentered_=true;return std::nullopt;}
    snapshot_busy_=true;snapshot_reentered_=false;
    struct EndSnapshot {bool& busy;~EndSnapshot(){busy=false;}} end{snapshot_busy_};
    // Never keep a map iterator/reference across virtual repository observers.
    // Pending entries qualify the registry epoch but are not chat participants.
    const auto registry=sessions_;
    const auto unchanged=[&] {return !snapshot_reentered_ && sessions_==registry;};
    const auto read_population=[&]() -> std::optional<std::vector<ReadyCharacter>> {
        std::vector<ReadyCharacter> result;result.reserve(registry.size());
        for(const auto& [session,entry]:registry) {
            if(!entry.active)continue;
            const auto& lease=entry.lease;
            if(!lease.session || session!=lease.session || !lease.account || !lease.character || !lease.generation)
                return std::nullopt;
            if(!unchanged())return std::nullopt;
            const auto roots=characters_.list_for_account(lease.account);
            if(!unchanged())return std::nullopt;
            std::optional<RecoveredCharacter> root;std::set<std::uint64_t> ids;
            for(const auto& candidate:roots) {
                if(!candidate.id || candidate.account_id!=lease.account || !ids.insert(candidate.id).second)
                    return std::nullopt;
                if(candidate.id==lease.character)root=candidate;
            }
            if(!root)return std::nullopt;
            const auto position=characters_.load_position(lease.account,lease.character);
            if(!position || !unchanged())return std::nullopt;
            result.push_back({lease,*root,*position});
        }
        return unchanged()?std::optional{std::move(result)}:std::nullopt;
    };
    auto first=read_population();if(!first)return std::nullopt;
    const auto second=read_population();
    if(!second || first->size()!=second->size() || !unchanged())return std::nullopt;
    for(std::size_t i=0;i<first->size();++i) {
        const auto& a=(*first)[i];const auto& b=(*second)[i];
        if(a.lease!=b.lease || a.position!=b.position || !same_character_root(a.character,b.character))return std::nullopt;
    }
    return first;
}
bool SharedWorldPresence::release(const Lease& lease) {
    owner();if(snapshot_busy_)snapshot_reentered_=true;
    const auto found=sessions_.find(lease.session);
    if(found==sessions_.end() || found->second.lease!=lease)return false;
    sessions_.erase(found);return true;
}
std::optional<RecoveredPosition> SharedWorldPresence::saved_position(const Lease& lease) const {
    owner();if(!ready(lease))return std::nullopt;
    return characters_.load_position(lease.account,lease.character);
}
std::optional<RecoveredPosition> SharedWorldPresence::commit_owned_step(const Lease& lease,
    const RecoveredPosition& expected,std::uint16_t x,std::uint16_t y) {
    owner();if(snapshot_busy_)snapshot_reentered_=true;
    const auto current=saved_position(lease);
    if(!current || *current!=expected)return std::nullopt;
    // Existing common SQLite transaction rechecks ownership and the exact
    // expected position/revision. Same-map step only; no client map identity.
    return characters_.commit_position(lease.account,lease.character,expected,
        expected.area,expected.scene,x,y);
}
}
