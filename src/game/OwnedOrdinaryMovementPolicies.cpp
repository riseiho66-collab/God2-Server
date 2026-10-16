#include "game/OwnedOrdinaryMovementPolicies.h"
#include <algorithm>
#include <exception>
#include <limits>
#include <ratio>
#include <stdexcept>
#include <utility>

namespace god2 {
struct OwnedOrdinaryMovementPolicies::Issuer {};
struct OwnedOrdinaryMovementPolicies::SnapshotData {
    const OrdinaryMovementPolicyRepository::Snapshot value;
    explicit SnapshotData(OrdinaryMovementPolicyRepository::Snapshot input):value(std::move(input)) {}
};
struct OwnedOrdinaryMovementPolicies::Operation {
    OwnedOrdinaryMovementPolicies& cache;
    explicit Operation(OwnedOrdinaryMovementPolicies& input):cache(input) {
        cache.owner();
        if(cache.busy_) {
            cache.poisoned_=true;
            throw std::logic_error("ordinary movement policy refresh reentry rejected");
        }
        if(!cache.available())throw std::runtime_error("ordinary movement policy repository unavailable");
        cache.busy_=true;cache.poisoned_=false;
    }
    ~Operation(){cache.busy_=false;}
};
OwnedOrdinaryMovementPolicies::Observation::Observation(std::shared_ptr<const Issuer> issuer,
    std::shared_ptr<const SnapshotData> snapshot,std::size_t index)
    :issuer_(std::move(issuer)),snapshot_(std::move(snapshot)),index_(index) {}
const OwnedOrdinaryMovementPolicy& OwnedOrdinaryMovementPolicies::Observation::policy() const {
    return snapshot_->value.rows.at(index_).policy;
}
OwnedOrdinaryMovementPolicies::Binding::Binding(std::shared_ptr<OwnedOrdinaryMovementPolicies> owner,
    std::string profile):owner_(std::move(owner)),profile_key_(std::move(profile)) {}
OwnedOrdinaryMovementPolicies::Observation OwnedOrdinaryMovementPolicies::Binding::observe() {
    const auto cache=owner_;return cache->observe(profile_key_);
}
bool OwnedOrdinaryMovementPolicies::Binding::current(const Observation& observation) const {
    return owner_->current(profile_key_,observation);
}
bool OwnedOrdinaryMovementPolicies::Binding::available() const {return owner_->readable();}
OwnedOrdinaryMovementPolicies::OwnedOrdinaryMovementPolicies(OrdinaryMovementPolicyRepository& repository,
    std::size_t limit,std::shared_ptr<const OrdinaryMovementPolicyRepository::Lifetime> lifetime)
    :repository_(repository),max_profiles_(limit),lifetime_(std::move(lifetime)),issuer_(std::make_shared<const Issuer>()) {}
OwnedOrdinaryMovementPolicies::~OwnedOrdinaryMovementPolicies() {
    if(thread_!=std::this_thread::get_id())std::terminate();
    closing_=true;busy_=true;snapshot_.reset();
}
void OwnedOrdinaryMovementPolicies::owner() const {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("ordinary movement policy game owner mismatch");
}
bool OwnedOrdinaryMovementPolicies::available() const {
    return thread_==std::this_thread::get_id() && !closing_ && lifetime_ && lifetime_->available();
}
bool OwnedOrdinaryMovementPolicies::readable() const {
    if(thread_!=std::this_thread::get_id())return false;
    if(busy_) {poisoned_=true;return false;}
    return available() && !poisoned_ && snapshot_;
}
void OwnedOrdinaryMovementPolicies::retire() noexcept {closing_=true;poisoned_=true;}
void OwnedOrdinaryMovementPolicies::reload() {
    try {refresh_snapshot();}
    catch(...) {retire();throw;} // Scheduler failure cannot leave a readable old cache.
}
bool OwnedOrdinaryMovementPolicies::valid_profile(const std::string& profile) noexcept {
    if(profile.empty() || profile.size()>48 || profile.front()<'a' || profile.front()>'z')return false;
    return std::all_of(profile.begin()+1,profile.end(),[](char value) {
        return (value>='a' && value<='z') || (value>='0' && value<='9') || value=='_';
    });
}
std::shared_ptr<OwnedOrdinaryMovementPolicies> OwnedOrdinaryMovementPolicies::create(
    OrdinaryMovementPolicyRepository& repository,std::size_t limit) {
    if(limit<1 || limit>1024)throw std::invalid_argument("ordinary movement policy profile limit invalid");
    const auto lifetime=repository.lifetime();
    if(!lifetime || !lifetime->available())throw std::runtime_error("ordinary movement policy repository unavailable");
    auto result=std::shared_ptr<OwnedOrdinaryMovementPolicies>(new OwnedOrdinaryMovementPolicies(repository,limit,lifetime));
    result->refresh_snapshot();return result;
}
void OwnedOrdinaryMovementPolicies::refresh_snapshot() {
    const auto self=shared_from_this(); // Retain across the virtual repository observer.
    Operation operation(*this);
    if(!available())throw std::runtime_error("ordinary movement policy repository revoked before load");
    const auto retained=snapshot_;
    try {
        auto candidate=repository_.load(max_profiles_);
        if(!available() || poisoned_)throw std::runtime_error("ordinary movement policy load revoked");
        if(!candidate.version || candidate.version>std::uint64_t(std::numeric_limits<std::int64_t>::max()) ||
           candidate.rows.empty() || candidate.rows.size()>max_profiles_)
            throw OrdinaryMovementPolicyRepository::InvalidSnapshot("ordinary movement policy snapshot shape invalid");
        std::string previous;
        for(const auto& row:candidate.rows) {
            if(!valid_profile(row.profile_key) || (!previous.empty() && row.profile_key<=previous) ||
               !row.policy.valid() || row.policy.version!=candidate.version)
                throw OrdinaryMovementPolicyRepository::InvalidSnapshot("ordinary movement policy snapshot row invalid");
            previous=row.profile_key;
        }
        if(snapshot_) {
            if(candidate.version<snapshot_->value.version)
                throw OrdinaryMovementPolicyRepository::InvalidSnapshot("ordinary movement policy version rollback rejected");
            if(candidate.version==snapshot_->value.version) {
                if(candidate.rows!=snapshot_->value.rows)
                    throw OrdinaryMovementPolicyRepository::InvalidSnapshot("ordinary movement policy same-version mutation rejected");
                if(!available() || poisoned_)throw std::runtime_error("ordinary movement policy load revoked");
                return;
            }
        }
        const auto prepared=std::make_shared<const SnapshotData>(std::move(candidate));
        if(!available() || poisoned_)throw std::runtime_error("ordinary movement policy publication revoked");
        snapshot_=prepared; // One whole immutable publication; no callback or SQL follows.
    }catch(const OrdinaryMovementPolicyRepository::InvalidSnapshot&) {
        // CUSTOM-0150: reject only a cleanly read invalid candidate. Keep the
        // EXACT old whole snapshot, including its observation identity. Never
        // mask reentry/revocation, retry SQL, or manufacture startup defaults.
        if(!retained || snapshot_!=retained || !available() || poisoned_)throw;
    }
}
std::size_t OwnedOrdinaryMovementPolicies::find(const std::string& profile) const {
    const auto& rows=snapshot_->value.rows;
    const auto found=std::lower_bound(rows.begin(),rows.end(),profile,
        [](const auto& row,const auto& key){return row.profile_key<key;});
    if(found==rows.end() || found->profile_key!=profile)
        throw std::runtime_error("ordinary movement policy profile not found");
    return static_cast<std::size_t>(found-rows.begin());
}
std::shared_ptr<OwnedOrdinaryMovementPolicies::Binding> OwnedOrdinaryMovementPolicies::bind(std::string profile) {
    owner();
    if(!readable())throw std::runtime_error("ordinary movement policy cache unavailable or loading");
    if(!valid_profile(profile))throw std::invalid_argument("ordinary movement policy profile key invalid");
    find(profile);
    return std::shared_ptr<Binding>(new Binding(shared_from_this(),std::move(profile)));
}
OwnedOrdinaryMovementPolicies::Observation OwnedOrdinaryMovementPolicies::observe(const std::string& input) {
    owner();
    if(!readable())throw std::runtime_error("ordinary movement policy cache unavailable or loading");
    if(!valid_profile(input))throw std::invalid_argument("ordinary movement policy profile key invalid");
    return Observation(issuer_,snapshot_,find(input)); // No SQL, callback or version publication.
}
bool OwnedOrdinaryMovementPolicies::current(const std::string& profile,const Observation& observation) const {
    return readable() && observation.issuer_==issuer_ && observation.snapshot_==snapshot_ &&
        observation.index_<snapshot_->value.rows.size() &&
        snapshot_->value.rows[observation.index_].profile_key==profile;
}

OwnedOrdinaryMovementPolicyReloads::OwnedOrdinaryMovementPolicyReloads(std::size_t max_sources)
    :max_sources_(max_sources) {
    if(!max_sources_)throw std::invalid_argument("Movement reload registry requires an explicit positive source bound");
}
OwnedOrdinaryMovementPolicyReloads::~OwnedOrdinaryMovementPolicyReloads() {
    if(thread_!=std::this_thread::get_id())std::terminate();
    stop();
}
void OwnedOrdinaryMovementPolicyReloads::owner() const {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("Movement reload registry game owner mismatch");
}
OwnedOrdinaryMovementPolicyReloads::Clock::time_point
OwnedOrdinaryMovementPolicyReloads::deadline(Clock::time_point now,std::chrono::milliseconds interval) {
    // The actual steady clock uses a duration at least as fine as milliseconds.
    // Check the integral domain before duration_cast can multiply its count.
    static_assert(std::ratio_less_equal_v<Clock::period,std::milli>);
    const auto maximum=std::chrono::duration_cast<std::chrono::milliseconds>(Clock::duration::max());
    if(interval<=std::chrono::milliseconds::zero() || interval>maximum)
        throw std::invalid_argument("Movement reload interval is nonpositive or exceeds the clock duration");
    const auto delta=std::chrono::duration_cast<Clock::duration>(interval);
    if(delta<=Clock::duration::zero() || now>Clock::time_point::max()-delta)
        throw std::invalid_argument("Movement reload deadline overflows the clock");
    return now+delta;
}
void OwnedOrdinaryMovementPolicyReloads::retire_all() noexcept {
    for(const auto& entry:entries_)entry.cache->retire(); // Pure flags, no callbacks/SQL/destruction.
}
void OwnedOrdinaryMovementPolicyReloads::attach(std::shared_ptr<OwnedOrdinaryMovementPolicies> cache,
    std::chrono::milliseconds interval) {
    owner();
    try {
        if(busy_) {
            poisoned_=true;stopped_=true;retire_all();
            throw std::logic_error("Movement reload registry attachment reentered polling");
        }
        if(stopped_)throw std::logic_error("Movement reload registry is stopped");
        if(!cache || !cache->readable() || entries_.size()>=max_sources_)
            throw std::invalid_argument("Movement reload registration requires an available bounded cache");
        for(const auto& entry:entries_)if(entry.cache==cache)
            throw std::invalid_argument("Movement reload cache already registered");
        const auto due=deadline(Clock::now(),interval);
        entries_.push_back({cache,interval,due}); // Keep the argument alive if queue allocation throws.
    }catch(...) {
        poisoned_=true;stopped_=true;retire_all();
        // Never mutate a foreign thread's cache while rejecting its registration.
        if(cache && cache->thread_==std::this_thread::get_id())cache->retire();
        if(!busy_)entries_.clear();
        throw;
    }
}
void OwnedOrdinaryMovementPolicyReloads::poll(Clock::time_point now) {
    owner();
    if(busy_) {
        poisoned_=true;stopped_=true;retire_all();
        throw std::logic_error("Movement reload registry polling reentered");
    }
    if(stopped_)return;
    std::shared_ptr<OwnedOrdinaryMovementPolicyReloads> self;
    busy_=true;
    struct End {
        OwnedOrdinaryMovementPolicyReloads& state;
        ~End(){state.busy_=false;if(state.stopped_)state.entries_.clear();}
    } end{*this};
    try {
        self=shared_from_this(); // Retain across virtual DB observers, inside the fatal boundary.
        if(last_poll_ && now<*last_poll_)throw std::logic_error("Movement reload poll clock moved backwards");
        last_poll_=now;
        for(std::size_t index=0;index<entries_.size();++index) {
            if(poisoned_ || stopped_)throw std::runtime_error("Movement reload registry retired during polling");
            if(now<entries_[index].due)continue;
            // Own values before any observer; never retain vector references or
            // iterators across SQL. Advance once before load: no catch-up burst.
            const auto cache=entries_[index].cache;
            const auto interval=entries_[index].interval;
            entries_[index].due=deadline(now,interval);
            cache->reload();
            if(poisoned_ || stopped_)throw std::runtime_error("Movement reload registry retired during load");
        }
    }catch(...) {
        // Fatal load/poison cannot be swallowed by Scheduler while cached
        // authority stays live. Revoke every cache before rethrow/logging.
        poisoned_=true;stopped_=true;retire_all();throw;
    }
}
void OwnedOrdinaryMovementPolicyReloads::stop() {
    owner();
    if(busy_)poisoned_=true;
    stopped_=true;retire_all(); // Existing Bindings can retain only unavailable caches.
    if(!busy_)entries_.clear(); // Poll owns no dangling reference on nested stop.
}
}
