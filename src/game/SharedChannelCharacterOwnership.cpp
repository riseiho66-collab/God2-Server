#include "game/SharedChannelCharacterOwnership.h"
#include <exception>
#include <limits>
#include <stdexcept>
#include <utility>

namespace god2 {
SharedChannelCharacterOwnership::SharedChannelCharacterOwnership(RecoveredCharacterRepository& characters)
    :characters_(characters) {}
SharedChannelCharacterOwnership::~SharedChannelCharacterOwnership() {
    if(thread_!=std::this_thread::get_id())std::terminate();
}
void SharedChannelCharacterOwnership::owner() const {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("Channel ownership game owner mismatch");
}
bool SharedChannelCharacterOwnership::owns_repository(const RecoveredCharacterRepository& characters) const {
    owner();return &characters_==&characters;
}
bool SharedChannelCharacterOwnership::character_reserved(std::uint64_t character) const {
    owner();const auto at=registry_->characters.find(character);
    return character&&at!=registry_->characters.end()&&occupied(at->second);
}
SharedChannelCharacterOwnership::World SharedChannelCharacterOwnership::register_world(std::uint8_t channel) {
    owner();
    if(channel>=channel_count||!worlds_[channel].expired())
        throw std::invalid_argument("Channel world requires one distinct owner per ordinal0..2");
    auto world=std::make_shared<const WorldIdentity>(WorldIdentity{channel});
    if(!worlds_[channel].expired())throw std::invalid_argument("Channel world changed during allocation");
    worlds_[channel]=world;return world;
}
bool SharedChannelCharacterOwnership::registered(const World& world) const {
    return world&&!world->retired&&world->channel<channel_count&&worlds_[world->channel].lock()==world;
}
bool SharedChannelCharacterOwnership::live(const Claim& claim) const {
    return claim&&!claim->retired&&claim->retirement.load()==Reservation::Retirement::None&&registered(claim->world);
}
bool SharedChannelCharacterOwnership::occupied(const Claim& claim) const {
    if(!claim||claim->retired)return false;
    const auto state=claim->retirement.load();
    return state==Reservation::Retirement::Pending||state==Reservation::Retirement::Quarantined||
        (state==Reservation::Retirement::None&&registered(claim->world));
}
bool SharedChannelCharacterOwnership::indexed(const Claim& claim) const {
    if(!claim)return false;
    const auto character=registry_->characters.find(claim->character),session=registry_->sessions.find(claim->session);
    return character!=registry_->characters.end()&&character->second==claim&&
        session!=registry_->sessions.end()&&session->second==claim;
}
SharedChannelCharacterOwnership::Claim SharedChannelCharacterOwnership::reserve(
        const World& world,std::uint64_t session,std::uint64_t account,std::uint64_t character) {
    owner();
    if(!registered(world)||!session||!account||!character)return {};
    const auto before=registry_;
    const auto reserved=[&](const auto& index,std::uint64_t id){const auto at=index.find(id);return at!=index.end()&&occupied(at->second);};
    if(reserved(before->characters,character)||reserved(before->sessions,session))return {};
    if(generation_==std::numeric_limits<std::uint64_t>::max())
        throw std::overflow_error("Channel character ownership generation exhausted");
    // Consume the epoch before allocation; even a nested failed attempt cannot
    // duplicate it. Strong immutable before keeps copy iterators valid.
    const auto generation=++generation_;
    auto claim=std::make_shared<const Reservation>(world,session,account,character,generation);
    auto candidate=std::make_shared<Registry>(*before);
    for(auto at=candidate->characters.begin();at!=candidate->characters.end();)
        if(!occupied(at->second))at=candidate->characters.erase(at);else ++at;
    for(auto at=candidate->sessions.begin();at!=candidate->sessions.end();)
        if(!occupied(at->second))at=candidate->sessions.erase(at);else ++at;
    if(!candidate->characters.emplace(character,claim).second||!candidate->sessions.emplace(session,claim).second)return {};
    if(registry_!=before||!registered(world)||claim->retired)return {};
    registry_=std::move(candidate);return claim;
}
bool SharedChannelCharacterOwnership::current(const Claim& claim) const {
    owner();return live(claim)&&indexed(claim);
}
bool SharedChannelCharacterOwnership::release(const Claim& claim) {
    owner();if(!current(claim))return false;
    claim->retired=true;return true;
}
bool SharedChannelCharacterOwnership::terminal(const Claim& claim) const noexcept {
    if(!claim)return false;
    const auto state=claim->retirement.load();
    return state==Reservation::Retirement::Pending||state==Reservation::Retirement::Quarantined;
}
bool SharedChannelCharacterOwnership::begin_terminal(const Claim& claim) {
    owner();if(!current(claim))return false;
    claim->retirement.store(Reservation::Retirement::Pending);return true;
}
void SharedChannelCharacterOwnership::quarantine_terminal(const Claim& claim) noexcept {
    if(!claim)return;
    auto pending=Reservation::Retirement::Pending;
    claim->retirement.compare_exchange_strong(pending,Reservation::Retirement::Quarantined);
}
bool SharedChannelCharacterOwnership::detach_terminal(const Claim& claim) {
    owner();if(!terminal(claim)||!indexed(claim)||claim->retired)return false;
    claim->detached=true;return true;
}
bool SharedChannelCharacterOwnership::finish_terminal(const Claim& claim,bool clean) {
    owner();
    if(!claim)return false;
    if(!clean||claim->retired||!claim->detached||!registered(claim->world)||!indexed(claim)){
        quarantine_terminal(claim);return false;
    }
    auto pending=Reservation::Retirement::Pending;
    if(!claim->retirement.compare_exchange_strong(pending,Reservation::Retirement::Released))return false;
    claim->retired=true;return true;
}
void SharedChannelCharacterOwnership::unregister_world(const World& world) noexcept {
    if(thread_!=std::this_thread::get_id())std::terminate();
    if(!registered(world))return;
    // No allocation/callbacks/SQL. Normal claims cease occupying this world;
    // terminal claims remain process-wide quarantine after world destruction.
    for(const auto& [character,claim]:registry_->characters)
        if(claim->world==world)quarantine_terminal(claim);
    world->retired=true;
    worlds_[world->channel].reset();
}
}
