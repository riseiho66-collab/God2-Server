#pragma once
#include "db/OrdinaryMovementPolicyRepository.h"
#include <memory>
#include <string>
#include <thread>

namespace god2 {
// CUSTOM-0150 whole-version DB policy publication. Borrowed repository lifetime
// is revocable; immutable observations own values, never the DB or game owner.
class OwnedOrdinaryMovementPolicies final:
    public std::enable_shared_from_this<OwnedOrdinaryMovementPolicies> {
    struct SnapshotData;
    struct Issuer;
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
        Observation refresh();
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
    bool available() const;
    static bool valid_profile(const std::string&) noexcept;
    void refresh_snapshot();
    Observation refresh(const std::string&);
    bool current(const std::string&,const Observation&) const;
    std::size_t find(const std::string&) const;
    const std::thread::id thread_=std::this_thread::get_id();
    OrdinaryMovementPolicyRepository& repository_;
    const std::size_t max_profiles_;
    const std::shared_ptr<const OrdinaryMovementPolicyRepository::Lifetime> lifetime_;
    const std::shared_ptr<const Issuer> issuer_;
    std::shared_ptr<const SnapshotData> snapshot_;
    bool busy_=false,poisoned_=false,closing_=false;
};
}
