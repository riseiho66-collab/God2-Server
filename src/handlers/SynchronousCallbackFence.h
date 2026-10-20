#pragma once
#include "db/DbTypes.h"
#include <functional>
#include <utility>

namespace god2 {
// Serialized game-owner callbacks only, not a cross-thread lock. Services must
// own-copy context before any callback and re-find it before publication.
// An explicit disconnect may erase the original immediately; its invalidation
// must still stop a caught nested callback from committing the outer request.
class SynchronousCallbackFence final {
public:
    SynchronousCallbackFence()=default;
    SynchronousCallbackFence(const SynchronousCallbackFence&)=delete;
    SynchronousCallbackFence& operator=(const SynchronousCallbackFence&)=delete;
    class Operation final {
    public:
        explicit Operation(SynchronousCallbackFence& state):state_(state) {
            if(state_.running_) {
                state_.invalidated_=true;
                throw DatabaseError("Synchronous service callback reentry rejected");
            }
            state_.running_=true;state_.invalidated_=false;
        }
        ~Operation(){state_.dependency_={};state_.running_=false;}
        Operation(const Operation&)=delete;
        Operation& operator=(const Operation&)=delete;
    private:
        SynchronousCallbackFence& state_;
    };
    Operation enter(){return Operation(*this);}
    void invalidate_if_running() noexcept {if(running_)invalidated_=true;}
    // Only a side-effect-free owner-held source may be installed here: no
    // provider, SQL, publication or new authority from the final check.
    void depend_on(std::function<bool()> current) {
        require_current();
        if(!running_ || !current)throw DatabaseError("Missing active callback dependency");
        dependency_=std::move(current);require_current();
    }
    bool invalidated() const noexcept {
        if(!invalidated_ && dependency_) {
            try {if(!dependency_())invalidated_=true;}catch(...){invalidated_=true;}
        }
        return invalidated_;
    }
    void require_current() const {
        if(invalidated())throw DatabaseError("Synchronous service callback invalidated its operation");
    }
private:
    bool running_=false;
    mutable bool invalidated_=false;
    std::function<bool()> dependency_;
};
}
