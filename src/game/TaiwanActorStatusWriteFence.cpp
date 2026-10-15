#include "game/TaiwanActorStatusWriteFence.h"
#include <atomic>
#include <limits>

namespace god2 {
struct TaiwanActorStatusWriteFence::Identity {
    std::atomic<std::uint64_t> generation{1};
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
    if(presence_.expired())return {};
    const auto generation=identity_->generation.load(std::memory_order_acquire);
    if(generation==std::numeric_limits<std::uint64_t>::max()||presence_.expired())return {};
    // Invalidation immediately after this load makes the returned checkpoint
    // stale. No exclusion of a subsequent writer is implied by this snapshot.
    return Checkpoint(identity_,generation);
}
bool TaiwanActorStatusWriteFence::current(const Checkpoint& checkpoint) const noexcept {
    if(checkpoint.identity_!=identity_||presence_.expired()||
       checkpoint.generation_==std::numeric_limits<std::uint64_t>::max())return false;
    const auto generation=identity_->generation.load(std::memory_order_acquire);
    return generation!=std::numeric_limits<std::uint64_t>::max()&&generation==checkpoint.generation_&&
        !presence_.expired();
}
void TaiwanActorStatusWriteFence::invalidate() noexcept {
    auto generation=identity_->generation.load(std::memory_order_relaxed);
    while(generation!=std::numeric_limits<std::uint64_t>::max()) {
        if(identity_->generation.compare_exchange_weak(generation,generation+1,
            std::memory_order_acq_rel,std::memory_order_relaxed))return;
    }
}
void TaiwanActorStatusWriteFence::stop() noexcept {
    identity_->generation.exchange(std::numeric_limits<std::uint64_t>::max(),std::memory_order_acq_rel);
}
}
