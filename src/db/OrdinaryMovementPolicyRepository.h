#pragma once
#include "game/OwnedOrdinaryMovementPolicy.h"
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

namespace god2 {
// CUSTOM-0150 configuration only; no player save, wire image or native claim.
class OrdinaryMovementPolicyRepository {
public:
    // Recoverable candidate-content rejection ONLY. load() may emit this
    // after its own read transaction/statements have ended and all ownership
    // fences passed. SQL, lifetime, reentry and allocation failures stay fatal.
    class InvalidSnapshot final:public std::runtime_error {
    public:
        using std::runtime_error::runtime_error;
    };
    struct Row {
        std::string profile_key;
        OwnedOrdinaryMovementPolicy policy;
        bool operator==(const Row&) const=default;
    };
    struct Snapshot {
        std::uint64_t version;
        std::vector<Row> rows;
        bool operator==(const Snapshot&) const=default;
    };
    class Lifetime {
    public:
        bool available() const noexcept {return alive_.load(std::memory_order_acquire);}
    private:
        friend class OrdinaryMovementPolicyRepository;
        Lifetime()=default;
        std::atomic<bool> alive_{true};
    };
    virtual ~OrdinaryMovementPolicyRepository(){revoke_lifetime();}
    OrdinaryMovementPolicyRepository(const OrdinaryMovementPolicyRepository&)=delete;
    OrdinaryMovementPolicyRepository& operator=(const OrdinaryMovementPolicyRepository&)=delete;
    virtual Snapshot load(std::size_t max_profiles)=0;
    std::shared_ptr<const Lifetime> lifetime() const noexcept {return lifetime_;}
protected:
    OrdinaryMovementPolicyRepository():lifetime_(new Lifetime){}
    // Derived teardown can revoke before destroying its own fields. Keeping a
    // token alive never keeps the actual repository available or owns its DB.
    void revoke_lifetime() noexcept {lifetime_->alive_.store(false,std::memory_order_release);}
private:
    const std::shared_ptr<Lifetime> lifetime_;
};
}
