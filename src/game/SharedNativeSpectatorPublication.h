#pragma once
#include "game/SharedNativeWorldTransports.h"
#include <functional>
#include <memory>
#include <optional>
#include <vector>

namespace god2 {
// One actual same-host recipient's supplied native UI publication history.
// Issued means local held-queue release, never native client receipt, target
// identity mapping or battle permission. Original byte records are retained.
class SharedNativeSpectatorPublication final {
    struct State;
    struct Observed;
public:
    using Lease=SharedWorldPresence::Lease;
    using Token=SharedNativeWorldTransports::Token;
    enum class Protocol {Taiwan,Mainland};
    enum class Status {Missing,Pending,Published,Retired,Unavailable};
    struct Event {
        Lease recipient;
        Protocol protocol;
        std::uint64_t ui_epoch,previous_revision,revision; // Actual issuer lineage, not recovered native fields.
        std::vector<std::uint8_t> logical; // Entire supplied CD65/D07 sequence.
    };
    struct Budgets {std::size_t max_logical_bytes,max_records,max_history_bytes,max_history_events;};
    struct Scope {
        Lease recipient;
        RecoveredCharacter character;
        RecoveredPosition saved_position;
        Protocol protocol;
        std::optional<SessionState> taiwan_phase;
        std::uint64_t taiwan_battle_generation; // No fabricated CN battle counter.
    };
    enum class Check {BeforeQueue,BeforeRelease,AfterRelease,Observe};
    class WorldOwner {
    public:
        virtual ~WorldOwner()=default;
        // Mandatory real UI/window/recipient/resource/target namespace/epoch and
        // native profile observer, pure non-yielding read-only. Never retain
        // borrowed arguments, send/write/pump/reenter or grant rights via history.
        // Actual saved position may advance between asynchronous stages; inside
        // each observer call the complete actual root/position/tuple is stable.
        // A first previous_revision0 requires actual issuer qualification of the
        // full supplied baseline. This source invents no initial flag/reset wire.
        virtual bool current(Check,const Scope&,const Event&)=0;
    };
    class Observation {
    public:
        Observation(const Observation&)=default;
        Observation& operator=(const Observation&)=default;
        Observation(Observation&&) noexcept;
        Observation& operator=(Observation&&) noexcept;
        Status status() const noexcept;
        const Lease& lease() const noexcept;
        const Token& token() const noexcept;
        std::uint64_t ui_epoch() const noexcept;
        std::uint64_t revision() const noexcept; // Last locally released revision only.
        const std::vector<Event>& history() const noexcept;
        const Event* pending_event() const noexcept;
    private:
        friend class SharedNativeSpectatorPublication;
        explicit Observation(std::shared_ptr<const Observed>);
        std::shared_ptr<const Observed> storage_;
    };
    using Completion=std::function<void(bool locally_released)>;
    static std::shared_ptr<SharedNativeSpectatorPublication> create(
        std::shared_ptr<SharedWorldPresence>,std::shared_ptr<SharedNativeWorldTransports>,Budgets,std::size_t actual_capacity);
    ~SharedNativeSpectatorPublication();
    bool owns_source(const std::shared_ptr<SharedWorldPresence>&,const std::shared_ptr<SharedNativeWorldTransports>&) const;
    // Entire event and history storage are deep-owned before effect. Pending
    // callbacks strongly retain the actual receiver/owner; persistent registry,
    // histories and observations retain both weakly, preventing Host cycles.
    // TW send is limited to InWorld by the existing held API. Observation is
    // still meaningful in battle; missing/retired/unavailable never grant rights.
    void publish(Event,std::shared_ptr<WorldOwner>,Completion);
    Observation observe(const Token&) const; // Exact saved private token, no lease alias lookup proof.
    bool current(const Observation&) const; // Accurate state observation, not active-window authorization.
    bool registry_current(const Observation&) const; // No repository or real Current callback.
    bool same(const Observation&,const Observation&) const; // Complete immutable private view/registration equality.
    // Exact private entry/epoch cleanup, also after actual common release.
    // Pending remove retires immediately, then erases only this entry on its
    // completion. Already released prefixes are recorded without reactivation.
    bool retire(const Observation&);
    bool remove(const Observation&);
private:
    explicit SharedNativeSpectatorPublication(std::shared_ptr<State>);
    std::shared_ptr<State> state_;
};
}
