#include "game/TaiwanActorStatusWriteFence.h"
#include <atomic>
#include <limits>
#include <mutex>

namespace god2 {
struct TaiwanActorStatusWriteFence::Identity {
    std::mutex mutex;
    std::uint64_t generation=1,pending=0;
    std::atomic<bool> poisoned{false};
    // Caller holds mutex. Stop never resets either counter or this poison.
    void advance_locked() noexcept {
        if(generation!=std::numeric_limits<std::uint64_t>::max())++generation;
        if(generation==std::numeric_limits<std::uint64_t>::max())
            poisoned.store(true,std::memory_order_release);
    }
};
struct TaiwanActorStatusWriteFence::WriterData {
    const std::shared_ptr<Identity> identity;
    bool armed=false; // Set once under mutex before any Writer publication.
    explicit WriterData(std::shared_ptr<Identity> value) noexcept:identity(std::move(value)){}
    ~WriterData() noexcept {
        if(!armed)return;
        try {
            std::lock_guard lock(identity->mutex);
            if(!identity->pending){identity->poisoned.store(true,std::memory_order_release);return;}
            --identity->pending;identity->advance_locked();
        }catch(...){identity->poisoned.store(true,std::memory_order_release);}
    }
};
TaiwanActorStatusWriteFence::TaiwanActorStatusWriteFence(const std::shared_ptr<SharedWorldPresence>& presence)
    :presence_(presence),presence_address_(presence.get()),identity_(std::make_shared<Identity>()){}
std::shared_ptr<TaiwanActorStatusWriteFence> TaiwanActorStatusWriteFence::create(
    std::shared_ptr<SharedWorldPresence> presence) {
    if(!presence)return {};
    return std::shared_ptr<TaiwanActorStatusWriteFence>(new TaiwanActorStatusWriteFence(presence));
}
bool TaiwanActorStatusWriteFence::owns_presence(const std::shared_ptr<SharedWorldPresence>& presence) const noexcept {
    return presence&&presence.get()==presence_address_&&!presence_.expired()&&
        !presence_.owner_before(presence)&&!presence.owner_before(presence_);
}
std::optional<TaiwanActorStatusWriteFence::Checkpoint> TaiwanActorStatusWriteFence::checkpoint() const noexcept {
    try {
        if(presence_.expired()||identity_->poisoned.load(std::memory_order_acquire))return {};
        std::lock_guard lock(identity_->mutex);
        if(identity_->pending||identity_->poisoned.load(std::memory_order_acquire)||
           identity_->generation==std::numeric_limits<std::uint64_t>::max()||presence_.expired())return {};
        // Quiescent at this cut only. A later writer immediately revokes it.
        return Checkpoint(identity_,identity_->generation);
    }catch(...){identity_->poisoned.store(true,std::memory_order_release);return {};}
}
bool TaiwanActorStatusWriteFence::current(const Checkpoint& checkpoint) const noexcept {
    try {
        if(checkpoint.identity_!=identity_||presence_.expired()||identity_->poisoned.load(std::memory_order_acquire))return false;
        std::lock_guard lock(identity_->mutex);
        return !identity_->pending&&!identity_->poisoned.load(std::memory_order_acquire)&&
            identity_->generation!=std::numeric_limits<std::uint64_t>::max()&&
            identity_->generation==checkpoint.generation_&&!presence_.expired();
    }catch(...){identity_->poisoned.store(true,std::memory_order_release);return false;}
}
void TaiwanActorStatusWriteFence::invalidate() noexcept {
    try {
        if(identity_->poisoned.load(std::memory_order_acquire))return;
        std::lock_guard lock(identity_->mutex);
        identity_->advance_locked();
    }catch(...){identity_->poisoned.store(true,std::memory_order_release);}
}
std::optional<TaiwanActorStatusWriteFence::Writer> TaiwanActorStatusWriteFence::begin_writer() noexcept {
    try {
        if(presence_.expired()||identity_->poisoned.load(std::memory_order_acquire))return {};
        // Allocation/new_handler precedes the mutex/count mutation. An unarmed
        // failed admission's Data destructor never locks this mutex.
        auto data=std::make_shared<WriterData>(identity_);
        {
            std::lock_guard lock(identity_->mutex);
            if(identity_->poisoned.load(std::memory_order_acquire)||presence_.expired())return {};
            if(identity_->pending==std::numeric_limits<std::uint64_t>::max()||
               identity_->generation>=std::numeric_limits<std::uint64_t>::max()-1){
                identity_->poisoned.store(true,std::memory_order_release);return {};
            }
            ++identity_->pending;identity_->advance_locked();data->armed=true;
        }
        // No allocation or throwing operation after arming; release the lock
        // BEFORE any possible last armed Data destruction.
        return Writer(std::move(data));
    }catch(...){identity_->poisoned.store(true,std::memory_order_release);return {};}
}
void TaiwanActorStatusWriteFence::stop() noexcept {
    identity_->poisoned.store(true,std::memory_order_release);
}
}
