#include "game/OwnedOrdinaryMovementPolicies.h"
#include <algorithm>
#include <exception>
#include <limits>
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
OwnedOrdinaryMovementPolicies::Observation OwnedOrdinaryMovementPolicies::Binding::refresh() {
    const auto cache=owner_;return cache->refresh(profile_key_);
}
bool OwnedOrdinaryMovementPolicies::Binding::current(const Observation& observation) const {
    return owner_->current(profile_key_,observation);
}
bool OwnedOrdinaryMovementPolicies::Binding::available() const {return owner_->available();}
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
    if(!valid_profile(profile))throw std::invalid_argument("ordinary movement policy profile key invalid");
    if(!available() || !snapshot_)throw std::runtime_error("ordinary movement policy cache unavailable");
    find(profile);
    return std::shared_ptr<Binding>(new Binding(shared_from_this(),std::move(profile)));
}
OwnedOrdinaryMovementPolicies::Observation OwnedOrdinaryMovementPolicies::refresh(const std::string& input) {
    const auto profile=input; // Own the Binding key before the virtual DB observer.
    owner();
    if(!valid_profile(profile))throw std::invalid_argument("ordinary movement policy profile key invalid");
    refresh_snapshot();
    if(!available() || !snapshot_)throw std::runtime_error("ordinary movement policy cache unavailable");
    return Observation(issuer_,snapshot_,find(profile));
}
bool OwnedOrdinaryMovementPolicies::current(const std::string& profile,const Observation& observation) const {
    return available() && snapshot_ && observation.issuer_==issuer_ && observation.snapshot_==snapshot_ &&
        observation.index_<snapshot_->value.rows.size() &&
        snapshot_->value.rows[observation.index_].profile_key==profile;
}
}
