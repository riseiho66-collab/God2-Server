#pragma once
#include "game/SharedNativeSpectatorPublication.h"
#include <memory>
#include <optional>
#include <span>
#include <vector>

namespace god2 {
// Explicit core issuer bindings for its actually released D0 UI operands.
// This does not recover every official mode1 context namespace, map IDs or
// create battle/admission/visibility permission. Full raw DWORDs remain raw.
class SharedNativeSpectatorTargets final {
    struct State;
    struct Observed;
    struct Retirement;
public:
    using Token=SharedNativeWorldTransports::Token;
    using Lease=SharedWorldPresence::Lease;
    using Publication=SharedNativeSpectatorPublication;
    enum class Operand {First,Second};
    enum class Status {Missing,Matched,Ambiguous,Expired,ForeignContext,Unavailable,Retired};
    struct Scope {
        Lease recipient;
        RecoveredCharacter character;
        RecoveredPosition saved_position;
        Publication::Protocol protocol;
        std::optional<SessionState> taiwan_phase;
        std::uint64_t taiwan_battle_generation; // Actual Taiwan battle incarnation.
    };
    class Target {
    public:
        virtual ~Target()=default;
        // Actual core target incarnation observer. Pure/non-yielding/read-only,
        // no pumping/reentry/write/send or retained borrowed arguments.
        virtual bool current(const Scope&,std::uint64_t actual_generation)=0;
    };
    struct Binding {
        std::uint64_t event_revision;
        std::size_t record_ordinal; // Zero-based full record ordinal in that event.
        Operand operand;
        std::shared_ptr<Target> target; // Actual input only; stored weakly.
        std::uint64_t target_generation;
    };
    struct BindingView {
        std::uint64_t event_revision;
        std::size_t record_ordinal;
        Operand operand;
        std::uint8_t slot;
        std::uint32_t raw_context; // Zero-extended exact published WORD, no ID cast.
        std::weak_ptr<Target> target;
        std::uint64_t target_generation;
    };
    class Issuer {
    public:
        virtual ~Issuer()=default;
        // Real UI flags/epoch/window/reset/source namespace and core binding
        // observer, not implicit authorization. Explicit issuer generation is
        // supplied by that core. Pure/non-yielding/read-only, never retain args.
        virtual bool current(const Scope&,const Publication::Observation&,
            std::span<const BindingView>,std::uint64_t actual_issuer_generation)=0;
    };
    struct Budgets {std::size_t max_bindings,actual_session_capacity;};
    class Observation {
    public:
        Observation(const Observation&)=default;
        Observation& operator=(const Observation&)=default;
        Observation(Observation&&) noexcept;
        Observation& operator=(Observation&&) noexcept;
        Status status() const noexcept;
        const Token& token() const noexcept;
        const std::optional<Publication::Observation>& ui() const noexcept;
        std::uint32_t raw_context() const noexcept;
        const std::vector<BindingView>& bindings() const noexcept;
        std::weak_ptr<Target> target() const noexcept;
        std::uint64_t target_generation() const noexcept;
        std::uint64_t issuer_generation() const noexcept;
    private:
        friend class SharedNativeSpectatorTargets;
        explicit Observation(std::shared_ptr<const Observed>);
        std::shared_ptr<const Observed> storage_;
    };
    // Captured by the real WindowOwner before closing. The immutable private
    // target-entry identity distinguishes reissues even in the same UI epoch.
    // It retains no strong actual receiver/target/issuer and grants no rights.
    class UiRetirement {
    public:
        UiRetirement(const UiRetirement&)=default;
        UiRetirement& operator=(const UiRetirement&)=default;
        UiRetirement(UiRetirement&&) noexcept;
        UiRetirement& operator=(UiRetirement&&) noexcept;
        const Token& token() const noexcept;
        const Publication::Observation& ui() const noexcept;
        std::uint64_t ui_epoch() const noexcept;
        std::uint64_t issuer_generation() const noexcept;
    private:
        friend class SharedNativeSpectatorTargets;
        explicit UiRetirement(std::shared_ptr<const Retirement>);
        std::shared_ptr<const Retirement> storage_;
    };
    static std::shared_ptr<SharedNativeSpectatorTargets> create(std::shared_ptr<SharedWorldPresence>,
        std::shared_ptr<SharedNativeWorldTransports>,std::shared_ptr<Publication>,Budgets);
    ~SharedNativeSpectatorTargets();
    bool owns_source(const std::shared_ptr<SharedWorldPresence>&,
        const std::shared_ptr<SharedNativeWorldTransports>&,const std::shared_ptr<Publication>&) const;
    // Complete batch qualification/allocation precedes registry replacement.
    // Every binding must identify the last released D0 of its exact UI slot.
    // No default binding for FFFF/0, missing operands or unrelated caller domains.
    bool issue(const Publication::Observation&,std::span<const Binding>,std::shared_ptr<Issuer>,std::uint64_t actual_issuer_generation);
    Observation resolve(const Token&,std::uint32_t raw_context) const;
    bool current(const Observation&) const; // Truth of this view, not rights.
    bool same(const Observation&,const Observation&) const;
    bool registry_current(const Observation&) const; // No repository/external observer.
    bool retire(const Observation&);
    bool remove(const Observation&); // Exact own incarnation, no common cleanup.
    // Pure registry/private-view proof only; never invokes repository, Target,
    // Issuer or window Current. Capture before publication/token retirement.
    std::optional<UiRetirement> retirement_for_ui(const Publication::Observation&) const;
    // After actual close/common cleanup, retire only this captured entry.
    // A successor/same-epoch reissue cannot match its old private capability.
    bool retire_for_ui(const UiRetirement&);
private:
    explicit SharedNativeSpectatorTargets(std::shared_ptr<State>);
    std::shared_ptr<State> state_;
};
}
