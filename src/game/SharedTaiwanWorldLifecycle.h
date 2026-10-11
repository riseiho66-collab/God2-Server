#pragma once
#include "cn/world/SharedActorVisibility.h"
#include "game/SharedNativeWorldTransports.h"
#include "protocol/RecoveredWorldEntryView.h"

namespace god2 {
// One binding per actual TW Session. A dual-client host must explicitly install
// these hooks and the same common presence/visibility as CN. No automatic opt-in
// of frozen Application handlers or invented full2A data/publish policy.
class SharedTaiwanWorldLifecycle {
public:
    using Lease=SharedWorldPresence::Lease;
    using Entered=std::function<bool(Session&,const Lease&,const RecoveredWorldEntryView&)>;
    using ReadyCompletion=std::function<void(bool)>;
    using EnteredAsync=std::function<void(Session&,const Lease&,const RecoveredWorldEntryView&,ReadyCompletion)>;
    struct AsyncOwner {
        EnteredAsync entered;
        // Revokes actual scene payload before the shared registry is released.
        // Both functions belong to the game owner, never network callback copies.
        std::function<void(Session&,const Lease&)> cancel;
    };
    // Entered is the real scene owner: publication, state and actual native
    // visibility/resource suppliers remain its responsibility. No generic success.
    // Successful same-lease ready binds the Session's separate common delivery
    // identity; generation-qualified release revokes it before visibility cleanup.
    static std::shared_ptr<const Session::CommonWorldLifecycle> hooks(
        std::shared_ptr<SharedWorldPresence>,std::shared_ptr<cn::SharedActorVisibility>,Entered,
        std::shared_ptr<SharedNativeWorldTransports> = {});
    // Safe to copy into listener handlers: each actual game-owner invocation
    // creates fresh per-Session Binding state. Does not supply data or admission.
    static Session::CommonWorldLifecycleFactory factory(
        std::shared_ptr<SharedWorldPresence>,std::shared_ptr<cn::SharedActorVisibility>,Entered,
        std::shared_ptr<SharedNativeWorldTransports> = {});
    static std::shared_ptr<const Session::CommonWorldLifecycle> hooks_async(
        std::shared_ptr<SharedWorldPresence>,std::shared_ptr<cn::SharedActorVisibility>,AsyncOwner,
        std::shared_ptr<SharedNativeWorldTransports> = {});
    static Session::CommonWorldLifecycleFactory factory_async(
        std::shared_ptr<SharedWorldPresence>,std::shared_ptr<cn::SharedActorVisibility>,AsyncOwner,
        std::shared_ptr<SharedNativeWorldTransports> = {});
private:
    enum class Stage {Fresh,Prepared,Entering,Ready,Released};
    struct Binding {
        std::thread::id thread=std::this_thread::get_id();
        std::shared_ptr<SharedWorldPresence> presence;
        std::shared_ptr<cn::SharedActorVisibility> visibility;
        std::shared_ptr<SharedNativeWorldTransports> transports;
        std::optional<SharedNativeWorldTransports::Token> transport_token;
        Entered entered;
        std::weak_ptr<Session> connection;
        std::optional<Lease> lease;
        std::optional<RecoveredWorldEntryView> entry;
        Stage stage=Stage::Fresh;
        void owner() const;
        bool current(Session&) const;
        bool prepare(Session&,const RecoveredWorldEntry::Frame&);
        bool ready(Session&);
        void release();
    };
    struct AsyncBinding:std::enable_shared_from_this<AsyncBinding> {
        Binding base;
        AsyncOwner scene;
        ReadyCompletion done;
        bool released=false;
        bool invoking=false;
        std::optional<bool> inline_result;
        void release();
        void ready(Session&,ReadyCompletion);
        void complete(bool);
    };
};
}
