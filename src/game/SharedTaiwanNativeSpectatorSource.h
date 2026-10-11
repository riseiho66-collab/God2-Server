#pragma once
#include "game/SharedNativeWorldTransports.h"
#include "game/SharedNativeSpectatorPublication.h"
#include "game/SharedNativeSpectatorTargets.h"
#include "game/SharedTaiwanWorldRecordSource.h"
#include "protocol/RecoveredSpectator6E.h"
#include "protocol/RecoveredSpectatorClose.h"
#include <functional>
#include <memory>
#include <optional>
#include <utility>

namespace god2 {
// Actual registered common-ready TW sender -> actual typed native6E handler.
// Source ownership/current guards supply no target namespace or spectator rights.
class SharedTaiwanNativeSpectatorSource final {
public:
    using Lease=SharedWorldPresence::Lease;
    using Request=RecoveredSpectator6E::Request;
    using CloseRequest=RecoveredSpectatorClose::Request;
    using Reply=SharedTaiwanWorldRecordSource::Reply;
    struct Scope {
        Lease lease;
        RecoveredCharacter character; // Full actual common root, never native ID.
        RecoveredPosition saved_position;
        SessionState phase;
        std::uint64_t battle_generation;
        // nullopt means this source did not select native UI publication.
        // Selected Missing/Pending/Published/Retired/Unavailable remain actual
        // distinct observations, never permissions or inferred target IDs.
        std::optional<SharedNativeSpectatorPublication::Observation> native_ui;
        // Only this actual issuer's D0 UI namespace. Other native mode1
        // DWORD namespaces remain the real WorldOwner's responsibility.
        std::optional<SharedNativeSpectatorTargets::Observation> native_target;
    };
    enum class Check {BeforeExecute,AfterExecute,BeforeReturn};
    struct Budgets {std::size_t max_output_bytes;};
    struct Result {
        Reply reply; // Full actual encrypted envelopes or explicit real noReply.
        SessionState expected_post_phase;
        std::uint64_t expected_post_battle_generation;
        Result(Reply actual,SessionState phase,std::uint64_t generation)
            :reply(std::move(actual)),expected_post_phase(phase),expected_post_battle_generation(generation) {}
    };
    class WorldOwner {
    public:
        virtual ~WorldOwner()=default;
        // Pure non-yielding read-only observer: no send/write/pump/reentry or
        // retained borrowed arguments. BeforeExecute gets nullptr Result and
        // actual preScope; post checks get actual postScope and the exact Result.
        // Qualify native request target namespace, mode1 publication/current
        // entry/update/reset and mode2 real membership/battle incarnation, rules,
        // execution ticket and actual same Session cipher/profile reply here.
        // The three unwritten request bytes and full raw DWORD context survive.
        // native_ui exposes only this actual recipient's publication history.
        // Negative UI states and absent opt-in neither grant nor deny admission;
        // mode1 context namespace and mode2 battle rights remain your rules.
        virtual bool current(Session&,Check,const Scope&,const Request&,const Result*)=0;
        // Invoked exactly once after current. May commit real gameplay/state;
        // never yield/pump/reenter/retain borrowed args. No fake ACK or guessed
        // noReply. A null/failure terminalizes this source-owned sender slot;
        // already committed prefixes are not rolled back or retried. Native
        // admission/exit/target mapping is this real handler's responsibility.
        virtual std::optional<Result> execute(Session&,const Scope&,const Request&)=0;
    };
    class CloseOwner {
    public:
        virtual ~CloseOwner()=default;
        // Independently qualify the actual native window, opcode/opaque byte,
        // phase, rights and complete reply. Scope has actual UI but no target;
        // closing never synthesizes context0 or grants leave-battle authority.
        // Same pure observer/once execution/prefix contract as WorldOwner.
        virtual bool current(Session&,Check,const Scope&,const CloseRequest&,const Result*)=0;
        virtual std::optional<Result> execute(Session&,const Scope&,const CloseRequest&)=0;
    };
    struct Binding {
        // Sender reply returns to mixed record order, never directly submitted.
        std::function<std::optional<Reply>(Session&,const Request&)> dispatch;
        std::function<void(Session&)> release; // Exact own bookkeeping only.
        std::function<void()> invalidate_active;
        // Empty unless an independent CloseOwner and actual publication were selected.
        std::function<std::optional<Reply>(Session&,const CloseRequest&)> close_dispatch;
    };
    static Binding create(std::shared_ptr<SharedWorldPresence>,std::shared_ptr<SharedNativeWorldTransports>,
        std::shared_ptr<WorldOwner>,Budgets,std::size_t actual_session_capacity,
        std::shared_ptr<SharedNativeSpectatorPublication> = {},
        std::shared_ptr<SharedNativeSpectatorTargets> = {},
        std::shared_ptr<CloseOwner> = {});
};
}
