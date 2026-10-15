#pragma once
#include <cstdint>
#include <memory>
#include <optional>
#include <utility>

namespace god2 {
class Session;
class SharedWorldPresence;
class SharedTaiwanNativeWorldHostPlan;
// Explicit optional whole-host output revocation evidence only. A checkpoint
// is neither writer permission nor Known/None/EA/native status authority.
// No presence observer, game callback or actor material runs on IO threads.
class TaiwanActorStatusWriteFence final {
    struct Identity;
public:
    class Checkpoint final {
    public:
        Checkpoint(const Checkpoint&)=default;
        Checkpoint& operator=(const Checkpoint&)=default;
        bool operator==(const Checkpoint& other) const noexcept {
            return identity_==other.identity_&&generation_==other.generation_;
        }
    private:
        friend class TaiwanActorStatusWriteFence;
        Checkpoint(std::shared_ptr<const Identity> identity,std::uint64_t generation)
            :identity_(std::move(identity)),generation_(generation){}
        std::shared_ptr<const Identity> identity_;
        std::uint64_t generation_;
    };
    // Construct explicitly on the actual host owner. Absence preserves legacy
    // routing. The monitor never takes ownership of a game-affine presence.
    static std::shared_ptr<TaiwanActorStatusWriteFence> create(std::shared_ptr<SharedWorldPresence>);
    TaiwanActorStatusWriteFence(const TaiwanActorStatusWriteFence&)=delete;
    TaiwanActorStatusWriteFence& operator=(const TaiwanActorStatusWriteFence&)=delete;
    bool owns_presence(const std::shared_ptr<SharedWorldPresence>&) const noexcept;
    std::optional<Checkpoint> checkpoint() const noexcept;
    bool current(const Checkpoint&) const noexcept;
    // Public revocation only: host teardown permanently disables this node.
    // Cannot mint a checkpoint, writer permission or status authority.
    void stop() noexcept;
private:
    friend class Session;
    friend class SharedTaiwanNativeWorldHostPlan;
    explicit TaiwanActorStatusWriteFence(const std::shared_ptr<SharedWorldPresence>&);
    // Concurrent-safe and monotonic. Saturation is permanent poison: no wrap,
    // reset or revival. This performs no game-affine work or allocation.
    void invalidate() noexcept;
    const std::weak_ptr<SharedWorldPresence> presence_;
    const SharedWorldPresence* const presence_address_;
    const std::shared_ptr<Identity> identity_;
};
}
