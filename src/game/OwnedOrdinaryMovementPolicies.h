#pragma once
#include "db/OrdinaryMovementPolicyRepository.h"
#include <chrono>
#include <memory>
#include <optional>
#include <string>
#include <thread>
#include <vector>

namespace god2 {
class OwnedOrdinaryMovementPolicyReloads;
// CUSTOM-0150 whole-version DB policy publication. Borrowed repository lifetime
// is revocable; immutable observations own values, never the DB or game owner.
class OwnedOrdinaryMovementPolicies final:
    public std::enable_shared_from_this<OwnedOrdinaryMovementPolicies> {
    struct SnapshotData;
    struct Issuer;
    friend class OwnedOrdinaryMovementPolicyReloads;
public:
    class Binding;
    class Observation {
    public:
        Observation(const Observation&)=default;
        Observation& operator=(const Observation&)=default;
        const OwnedOrdinaryMovementPolicy& policy() const;
    private:
        friend class OwnedOrdinaryMovementPolicies;
        friend class Binding;
        Observation(std::shared_ptr<const Issuer>,std::shared_ptr<const SnapshotData>,std::size_t);
        std::shared_ptr<const Issuer> issuer_;
        std::shared_ptr<const SnapshotData> snapshot_;
        std::size_t index_;
    };
    class Binding final {
    public:
        Binding(const Binding&)=delete;
        Binding& operator=(const Binding&)=delete;
        // Pure current immutable snapshot observation; never loads SQL.
        Observation observe();
        bool current(const Observation&) const;
        bool available() const;
    private:
        friend class OwnedOrdinaryMovementPolicies;
        Binding(std::shared_ptr<OwnedOrdinaryMovementPolicies>,std::string);
        const std::shared_ptr<OwnedOrdinaryMovementPolicies> owner_;
        const std::string profile_key_;
    };
    static std::shared_ptr<OwnedOrdinaryMovementPolicies> create(
        OrdinaryMovementPolicyRepository&,std::size_t max_profiles);
    ~OwnedOrdinaryMovementPolicies();
    OwnedOrdinaryMovementPolicies(const OwnedOrdinaryMovementPolicies&)=delete;
    OwnedOrdinaryMovementPolicies& operator=(const OwnedOrdinaryMovementPolicies&)=delete;
    std::shared_ptr<Binding> bind(std::string profile_key);
private:
    struct Operation;
    OwnedOrdinaryMovementPolicies(OrdinaryMovementPolicyRepository&,std::size_t,
        std::shared_ptr<const OrdinaryMovementPolicyRepository::Lifetime>);
    void owner() const;
    bool available() const; // Internal repository lifetime, including our own load.
    bool readable() const; // Public observation rejects/poisons load reentry.
    static bool valid_profile(const std::string&) noexcept;
    void refresh_snapshot();
    void reload(); // Actual game scheduler only; fatal failure revokes this cache.
    void retire() noexcept;
    Observation observe(const std::string&);
    bool current(const std::string&,const Observation&) const;
    std::size_t find(const std::string&) const;
    const std::thread::id thread_=std::this_thread::get_id();
    OrdinaryMovementPolicyRepository& repository_;
    const std::size_t max_profiles_;
    const std::shared_ptr<const OrdinaryMovementPolicyRepository::Lifetime> lifetime_;
    const std::shared_ptr<const Issuer> issuer_;
    std::shared_ptr<const SnapshotData> snapshot_;
    bool busy_=false,closing_=false;
    mutable bool poisoned_=false;
};
// Actual Application game-owner reload registrations. No per-packet SQL,
// private timer, timing default, borrowed Context or network-thread callback.
class OwnedOrdinaryMovementPolicyReloads final:
    public std::enable_shared_from_this<OwnedOrdinaryMovementPolicyReloads> {
public:
    using Clock=std::chrono::steady_clock;
    explicit OwnedOrdinaryMovementPolicyReloads(std::size_t max_sources);
    ~OwnedOrdinaryMovementPolicyReloads();
    OwnedOrdinaryMovementPolicyReloads(const OwnedOrdinaryMovementPolicyReloads&)=delete;
    OwnedOrdinaryMovementPolicyReloads& operator=(const OwnedOrdinaryMovementPolicyReloads&)=delete;
    void attach(std::shared_ptr<OwnedOrdinaryMovementPolicies>,std::chrono::milliseconds required_interval);
    void poll(Clock::time_point actual_now);
    void stop();
private:
    struct Entry {
        std::shared_ptr<OwnedOrdinaryMovementPolicies> cache;
        std::chrono::milliseconds interval;
        Clock::time_point due;
    };
    void owner() const;
    static Clock::time_point deadline(Clock::time_point,std::chrono::milliseconds);
    void retire_all() noexcept;
    const std::thread::id thread_=std::this_thread::get_id();
    const std::size_t max_sources_;
    std::vector<Entry> entries_;
    std::optional<Clock::time_point> last_poll_;
    bool busy_=false,poisoned_=false,stopped_=false;
};
}
