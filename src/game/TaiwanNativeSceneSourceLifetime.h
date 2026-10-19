#pragma once
#include "game/SharedWorldPresence.h"
#include <atomic>

namespace god2 {
class TaiwanNativeHmdBundleSource;
class Session;
// Revocation-only custody for one actual selected scene supply. This token
// grants no movement permission, native identity or acknowledgement.
class TaiwanNativeSceneSourceLifetime final {
public:
    bool current()const noexcept{return active_.load(std::memory_order_acquire);}
    void revoke()noexcept{active_.store(false,std::memory_order_release);}
    bool owned_by(const Session&,const SharedWorldPresence::Lease&)const noexcept;
private:
    friend class TaiwanNativeHmdBundleSource;
    TaiwanNativeSceneSourceLifetime(const std::shared_ptr<Session>&,const SharedWorldPresence::Lease&);
    const std::weak_ptr<Session> session_;
    const SharedWorldPresence::Lease lease_;
    std::atomic<bool> active_{true};
};
}
