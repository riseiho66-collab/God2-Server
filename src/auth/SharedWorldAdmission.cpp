#include "auth/SharedWorldAdmission.h"
#include <algorithm>
#include <limits>
#include <stdexcept>
#include <utility>

namespace god2 {
SharedWorldAdmission::SharedWorldAdmission(std::size_t live,std::size_t issued)
    :live_capacity_(live),issued_capacity_(issued) {
    if(!live || issued<live)throw std::invalid_argument("World admission capacity");
}
void SharedWorldAdmission::owner() const {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("World admission game owner mismatch");
}
void SharedWorldAdmission::expire(Clock::time_point now) {
    owner();
    // A handoff deadline is not a gameplay logout timer.
    std::erase_if(entries_,[now](const auto& row) {
        return row.second.stage!=Stage::WorldOwned && row.second.deadline<=now;
    });
}
std::optional<SharedWorldAdmission::Grant> SharedWorldAdmission::issue(
    std::uint64_t session,Key key,std::vector<Target> allowed,Clock::time_point deadline,Clock::time_point now) {
    owner();expire(now);
    if(!session || !key.account || allowed.empty() || deadline<=now ||
       key.protocol!=Protocol::Taiwan ||
       entries_.size()>=live_capacity_ || issued_.size()>=issued_capacity_ || issued_.contains(key) ||
       generation_==std::numeric_limits<std::uint64_t>::max())return std::nullopt;
    // Do not require check_key nonzero: no such native field contract is proven.
    // Never reuse a previously supplied tuple in this registry's lifetime.
    const auto generation=generation_+1;
    const auto [used,inserted]=issued_.insert(key);
    if(!inserted)return std::nullopt;
    try {
        entries_.emplace(key,Entry{generation,session,0,0,std::move(allowed),{},{},{},deadline,Stage::Issued});
    } catch(...) {issued_.erase(used);throw;}
    generation_=generation;
    return Grant{key,generation};
}
bool SharedWorldAdmission::account_owned(const Grant& grant,std::uint64_t session,
    std::uint64_t verified,Clock::time_point now) {
    owner();expire(now);
    const auto at=entries_.find(grant.key);
    return session && verified && grant.key.account==verified && at!=entries_.end() &&
        at->second.generation==grant.generation && at->second.account_session==session &&
        (at->second.stage==Stage::Issued || at->second.stage==Stage::Selected);
}
bool SharedWorldAdmission::account_target_allowed(const Grant& grant,std::uint64_t session,
    Target target,Clock::time_point now) {
    owner();
    if(!account_owned(grant,session,grant.key.account,now))return false;
    const auto& allowed=entries_.find(grant.key)->second.allowed;
    return std::find(allowed.begin(),allowed.end(),target)!=allowed.end();
}
std::optional<SharedWorldAdmission::AccountOffer> SharedWorldAdmission::selected_account_offer(
    const QueuedSelection& publication,std::uint64_t verified,Clock::time_point now) const {
    owner();
    if(publication.issuer_!=this)return std::nullopt;
    const auto& grant=publication.grant_;
    const auto session=publication.account_session_;
    const auto at=entries_.find(grant.key);
    if(!session || !verified || verified!=grant.key.account || at==entries_.end())return std::nullopt;
    const auto& entry=at->second;
    if(entry.generation!=grant.generation || entry.account_session!=session ||
       entry.offer_revision!=publication.offer_revision_ ||
       entry.stage!=Stage::Selected || !entry.selected || entry.deadline<=now ||
       !entry.invalidated_characters.empty() || entry.adapter_record.empty())return std::nullopt;
    return AccountOffer(this,grant,session,entry.offer_revision,*entry.selected,
        OfferSource{entry.offered_characters,entry.adapter_record});
}
bool SharedWorldAdmission::selected_account_offer_current(const AccountOffer& offer,Clock::time_point now) const {
    owner();if(offer.issuer_!=this)return false;
    const auto at=entries_.find(offer.grant_.key);
    if(at==entries_.end())return false;
    const auto& entry=at->second;
    return offer.account_session_ && entry.generation==offer.grant_.generation &&
        entry.account_session==offer.account_session_ && entry.offer_revision==offer.revision_ &&
        entry.stage==Stage::Selected && entry.deadline>now && entry.selected &&
        *entry.selected==offer.target_ && entry.invalidated_characters.empty() &&
        entry.offered_characters==offer.source_.character_ids && entry.adapter_record==offer.source_.adapter_record;
}
bool SharedWorldAdmission::select(const Grant& grant,std::uint64_t session,Target target,
    std::vector<std::uint64_t> characters,Clock::time_point now,std::vector<std::uint8_t> adapter_record) {
    owner();expire(now);
    const auto at=entries_.find(grant.key);
    if(at==entries_.end() || !session || at->second.generation!=grant.generation ||
       at->second.account_session!=session || adapter_record.size()>4096 ||
       (at->second.stage!=Stage::Issued && at->second.stage!=Stage::Selected))return false;
    auto& entry=at->second;
    if(entry.offer_revision==std::numeric_limits<std::uint64_t>::max())return false;
    if(std::find(entry.allowed.begin(),entry.allowed.end(),target)==entry.allowed.end())return false;
    std::set<std::uint64_t> seen;
    for(const auto id:characters)if(!id || !seen.insert(id).second)return false;
    // Prepare/qualify first, then replace this generation's whole offer. The
    // concrete character repository owner must establish ownership beforehand.
    entry.offered_characters=std::move(characters);
    entry.adapter_record=std::move(adapter_record); // Operational bounded snapshot, not a native max length.
    entry.invalidated_characters.clear(); // Actual newly qualified offer replaces the stale source.
    ++entry.offer_revision; // Even an identical reselection supersedes prepared source plans.
    entry.selected=target;entry.stage=Stage::Selected;
    return true;
}
std::optional<SharedWorldAdmission::QueuedSelection> SharedWorldAdmission::begin_selection_queue(
    const Grant& grant,std::uint64_t session,Target target,std::vector<std::uint64_t> characters,
    Clock::time_point now,std::vector<std::uint8_t> record) {
    owner();
    if(!select(grant,session,target,std::move(characters),now,std::move(record)))return std::nullopt;
    auto& entry=entries_.find(grant.key)->second;
    entry.stage=Stage::SelectionQueued;
    return QueuedSelection(this,grant,session,entry.offer_revision);
}
bool SharedWorldAdmission::queued_selection_current(const QueuedSelection& token,Clock::time_point now) const {
    owner();if(token.issuer_!=this)return false;
    const auto at=entries_.find(token.grant_.key);
    return at!=entries_.end() && token.account_session_ &&
        at->second.generation==token.grant_.generation && at->second.account_session==token.account_session_ &&
        at->second.stage==Stage::SelectionQueued && at->second.offer_revision==token.offer_revision_ &&
        at->second.deadline>now && at->second.selected && at->second.invalidated_characters.empty();
}
bool SharedWorldAdmission::commit_selection_queue(const QueuedSelection& token,Clock::time_point now) {
    owner();expire(now);
    if(!queued_selection_current(token,now))return false;
    entries_.find(token.grant_.key)->second.stage=Stage::Selected;
    return true;
}
bool SharedWorldAdmission::cancel_selection_queue(const QueuedSelection& token) {
    owner();if(token.issuer_!=this)return false;
    const auto at=entries_.find(token.grant_.key);
    if(at==entries_.end() || at->second.generation!=token.grant_.generation ||
       (at->second.account_session!=token.account_session_ &&
        !(at->second.account_session==0 && at->second.stage==Stage::Selected)) ||
       (at->second.stage!=Stage::SelectionQueued && at->second.stage!=Stage::Selected) ||
       at->second.offer_revision!=token.offer_revision_)return false;
    entries_.erase(at);return true;
}
std::optional<SharedWorldAdmission::Ticket> SharedWorldAdmission::reserve(
    Key key,std::uint64_t verified,std::uint64_t session,Target endpoint,Clock::time_point now) {
    owner();expire(now);
    if(!session || !verified || key.account!=verified)return std::nullopt;
    const auto at=entries_.find(key);
    if(at==entries_.end())return std::nullopt;
    auto& entry=at->second;
    if(!entry.invalidated_characters.empty())return std::nullopt;
    if(!entry.selected || *entry.selected!=endpoint)return std::nullopt;
    if(entry.stage==Stage::Reserved && entry.world_session==session)
        return Ticket{Grant{key,entry.generation},session,entry.reservation};
    if(entry.stage!=Stage::Selected || reservation_==std::numeric_limits<std::uint64_t>::max())return std::nullopt;
    entry.reservation=++reservation_;entry.world_session=session;entry.stage=Stage::Reserved;
    return Ticket{Grant{key,entry.generation},session,entry.reservation};
}
bool SharedWorldAdmission::matches(const Entry& entry,const Ticket& ticket) const {
    return ticket.world_session && ticket.reservation && entry.generation==ticket.grant.generation &&
        entry.world_session==ticket.world_session && entry.reservation==ticket.reservation;
}
bool SharedWorldAdmission::commit(const Ticket& ticket,Clock::time_point now) {
    owner();expire(now);
    const auto at=entries_.find(ticket.grant.key);
    if(at==entries_.end() || at->second.stage!=Stage::Reserved || !matches(at->second,ticket) ||
       !at->second.invalidated_characters.empty())return false;
    at->second.stage=Stage::WorldOwned;
    return true;
}
bool SharedWorldAdmission::cancel_reservation(const Ticket& ticket) {
    owner();const auto at=entries_.find(ticket.grant.key);
    if(at==entries_.end() || at->second.stage!=Stage::Reserved || !matches(at->second,ticket))return false;
    at->second.stage=Stage::Selected;at->second.world_session=0;at->second.reservation=0;
    return true;
}
bool SharedWorldAdmission::character_offered(const Ticket& ticket,std::uint64_t character) const {
    owner();
    const auto at=entries_.find(ticket.grant.key);
    return character && at!=entries_.end() && at->second.stage==Stage::WorldOwned &&
        matches(at->second,ticket) &&
        !at->second.invalidated_characters.contains(character) &&
        std::find(at->second.offered_characters.begin(),at->second.offered_characters.end(),character)
            !=at->second.offered_characters.end();
}
std::optional<SharedWorldAdmission::OfferSource> SharedWorldAdmission::offered_source(const Ticket& ticket) const {
    owner();
    const auto at=entries_.find(ticket.grant.key);
    if(at==entries_.end() || at->second.stage!=Stage::WorldOwned || !matches(at->second,ticket) ||
       at->second.adapter_record.empty() || !at->second.invalidated_characters.empty())return std::nullopt;
    return OfferSource{at->second.offered_characters,at->second.adapter_record};
}
bool SharedWorldAdmission::world_owned(const Ticket& ticket) const {
    owner();const auto at=entries_.find(ticket.grant.key);
    return at!=entries_.end() && at->second.stage==Stage::WorldOwned && matches(at->second,ticket);
}
std::optional<SharedWorldAdmission::CharacterOfferInvalidation>
SharedWorldAdmission::prepare_character_offer_invalidation(
    std::uint64_t account,std::uint64_t character) const {
    owner();if(!account || !character)return std::nullopt;
    CharacterOfferInvalidation result;result.issuer_=this;
    result.account_=account;result.character_=character;
    for(const auto& [key,entry]:entries_) {
        if(key.account!=account ||
           std::find(entry.offered_characters.begin(),entry.offered_characters.end(),character)
               ==entry.offered_characters.end())continue;
        if(entry.offer_revision==std::numeric_limits<std::uint64_t>::max())return std::nullopt;
        auto next=entry.invalidated_characters;next.insert(character);
        result.changes_.push_back({key,entry,std::move(next)});
    }
    // All copying/set/vector allocation completes before the caller changes
    // saved state. An empty plan is legitimate when no grant offered this ID.
    return std::optional<CharacterOfferInvalidation>{std::move(result)};
}
bool SharedWorldAdmission::character_offer_invalidation_current(
    const CharacterOfferInvalidation& plan) const {
    owner();
    if(plan.issuer_!=this || plan.consumed_ || !plan.account_ || !plan.character_)return false;
    std::size_t seen=0;
    for(const auto& [key,entry]:entries_) {
        if(key.account!=plan.account_ ||
           std::find(entry.offered_characters.begin(),entry.offered_characters.end(),plan.character_)
               ==entry.offered_characters.end())continue;
        const auto change=std::find_if(plan.changes_.begin(),plan.changes_.end(),[&key](const auto& row) {
            return row.key==key;
        });
        if(change==plan.changes_.end() || change->before!=entry)return false;
        ++seen;
    }
    // New/replaced/removed grants, reservation/phase transitions, a changed
    // full offer or any previous invalidation make the prepared plan stale.
    return seen==plan.changes_.size();
}
bool SharedWorldAdmission::apply_character_offer_invalidation(CharacterOfferInvalidation& plan) {
    owner();if(!character_offer_invalidation_current(plan))return false;
    // No allocations, callbacks, SQL, transport or yields in this application.
    // Existing world's ticket and unaffected character memberships survive.
    for(auto& change:plan.changes_) {
        const auto at=entries_.find(change.key);
        at->second.invalidated_characters.swap(change.after_invalidated);
        ++at->second.offer_revision; // prepare/current qualified the non-wrapping increment.
    }
    plan.consumed_=true;
    return true;
}
bool SharedWorldAdmission::release_world(const Ticket& ticket) {
    owner();const auto at=entries_.find(ticket.grant.key);
    if(at==entries_.end() ||
       (at->second.stage!=Stage::WorldOwned && at->second.stage!=Stage::Reserved) || !matches(at->second,ticket))return false;
    entries_.erase(at);return true;
}
bool SharedWorldAdmission::revoke_pending(const Grant& grant,std::uint64_t session) {
    owner();const auto at=entries_.find(grant.key);
    if(at==entries_.end() || !session || at->second.generation!=grant.generation ||
       at->second.account_session!=session || at->second.stage==Stage::WorldOwned)return false;
    entries_.erase(at);return true;
}
void SharedWorldAdmission::detach_account(std::uint64_t session) {
    owner();if(!session)return;
    // A queued, unpublished offer is not a handoff to preserve. Closing this
    // account must also remove invalidated/revision-changed queue attempts.
    std::erase_if(entries_,[session](const auto& row) {
        return row.second.account_session==session && row.second.stage==Stage::SelectionQueued;
    });
    for(auto& [key,entry]:entries_) {
        (void)key;
        if(entry.account_session==session)entry.account_session=0;
    }
}
}
