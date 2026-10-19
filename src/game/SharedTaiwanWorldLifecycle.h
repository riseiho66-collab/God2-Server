#pragma once
#include "shared/world/SharedActorVisibility.h"
#include "game/SharedNativeWorldTransports.h"
#include "game/TaiwanWorldEntryIdentity.h"
#include "game/TaiwanActorStatusIncarnationSource.h"
#include "protocol/RecoveredWorldEntryView.h"

namespace god2 {
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
    // SelectedCharacter preserves the original identity join. Explicit
    // QualifiedSceneHandle retains a separate common64 character and the actual
    // full entry's 1..FFF handle through a same-Prepared-lease receipt.
    // Successful same-lease ready binds the Session's separate common delivery
    // identity; generation-qualified release revokes it before visibility cleanup.
    static std::shared_ptr<const Session::CommonWorldLifecycle> hooks(
        std::shared_ptr<SharedWorldPresence>,std::shared_ptr<shared::SharedActorVisibility>,Entered,
        std::shared_ptr<SharedNativeWorldTransports> = {},
        TaiwanWorldEntryIdentity = TaiwanWorldEntryIdentity::SelectedCharacter,
        std::shared_ptr<TaiwanActorStatusIncarnationSource> = {});
    // Safe to copy into listener handlers: each actual game-owner invocation
    // creates fresh per-Session Binding state. Does not supply data or admission.
    static Session::CommonWorldLifecycleFactory factory(
        std::shared_ptr<SharedWorldPresence>,std::shared_ptr<shared::SharedActorVisibility>,Entered,
        std::shared_ptr<SharedNativeWorldTransports> = {},
        TaiwanWorldEntryIdentity = TaiwanWorldEntryIdentity::SelectedCharacter,
        std::shared_ptr<TaiwanActorStatusIncarnationSource> = {});
    static std::shared_ptr<const Session::CommonWorldLifecycle> hooks_async(
        std::shared_ptr<SharedWorldPresence>,std::shared_ptr<shared::SharedActorVisibility>,AsyncOwner,
        std::shared_ptr<SharedNativeWorldTransports> = {},
        TaiwanWorldEntryIdentity = TaiwanWorldEntryIdentity::SelectedCharacter,
        std::shared_ptr<TaiwanActorStatusIncarnationSource> = {});
    static Session::CommonWorldLifecycleFactory factory_async(
        std::shared_ptr<SharedWorldPresence>,std::shared_ptr<shared::SharedActorVisibility>,AsyncOwner,
        std::shared_ptr<SharedNativeWorldTransports> = {},
        TaiwanWorldEntryIdentity = TaiwanWorldEntryIdentity::SelectedCharacter,
        std::shared_ptr<TaiwanActorStatusIncarnationSource> = {});
private:
    enum class Stage {Fresh,Prepared,Entering,Ready,Released};
    struct Binding {
        std::thread::id thread=std::this_thread::get_id();
        std::shared_ptr<SharedWorldPresence> presence;
        std::shared_ptr<TaiwanActorStatusIncarnationSource> status_incarnations;
        std::optional<TaiwanActorStatusIncarnationSource::Token> status_incarnation;
        std::shared_ptr<shared::SharedActorVisibility> visibility;
        std::shared_ptr<SharedNativeWorldTransports> transports;
        std::optional<SharedNativeWorldTransports::Token> transport_token;
        Entered entered;
        std::weak_ptr<Session> connection;
        std::optional<Lease> lease;
        std::optional<RecoveredWorldEntryView> entry;
        TaiwanWorldEntryIdentity identity=TaiwanWorldEntryIdentity::SelectedCharacter;
        Stage stage=Stage::Fresh;
        ~Binding();
        void retire_status_incarnation() noexcept;
        bool admit_status_incarnation(Session&);
        void owner() const;
        bool current(Session&) const;
        bool prepare(Session&,const RecoveredWorldEntry::Frame&);
        std::optional<std::uint16_t> prepared_actor(Session&,const RecoveredWorldEntry::Frame&) const;
        bool ready(Session&);
        // CUSTOM-0159: hold exact process claim through terminal cleanup.
        std::optional<SharedWorldPresence::TerminalRetirement> terminal_retirement;
        bool terminal_attempted=false,terminal_failed=false,terminal_finished=false;
        void arm_terminal_retirement();
        void begin_terminal(Session&);
        bool finish_terminal(Session&,bool clean);
        void fail_terminal() noexcept;
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
