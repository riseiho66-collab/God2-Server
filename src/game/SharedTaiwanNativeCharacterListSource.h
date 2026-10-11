#pragma once
#include "db/NativeCharacterSummarySnapshotRepository.h"
#include "net/Session.h"
#include "protocol/RecoveredTaiwanServerAdvertisement.h"
#include <optional>
#include <memory>
#include <span>
#include <string>
#include <utility>

namespace god2 {
// Exact stored TW07 delivery and native issued-token selection. This is not
// the historical zero-filled list or a create40/selected40 projection.
class SharedTaiwanNativeCharacterListSource {
public:
    using Frame=std::array<std::uint8_t,78>;
    enum class Check {List,Select};
    class Issued;
    using IssuedPtr=std::shared_ptr<const Issued>;
    struct Scope {
        std::uint64_t session,account;
        SessionState state;
        std::optional<std::uint8_t> token;
        std::optional<std::uint64_t> created;
        // Exact input and marked socket-write advertisement observation from
        // this Session. Advertisement retains candidate origin, not a grant.
        // Null on a
        // separate world socket; no copied account receipt or inferred target.
        std::shared_ptr<const Session::RecoveredServerSelection> selection;
        std::optional<RecoveredTaiwanServerAdvertisement> advertised_rows;
        std::optional<RecoveredPostCreateSelect::Selection> input;
        IssuedPtr issued; // Separate issuer observation, never copied into G's A6.
    };
    // Immutable pure data, created dormant only after real successful write and
    // source Current. External retention cannot keep a DB/Target/Session alive.
    // All ticket/publication/link use is on game; this is not an admission CAS.
    class Issued final {
        friend class SharedTaiwanNativeCharacterListSource;
        std::weak_ptr<const void> owner_;
        bool active_=false;
        Session::NativeCharacterList delivery_;
        NativeCharacterSummarySnapshot snapshot_;
        std::vector<RecoveredCharacter> roots_;
        Scope issuer_scope_;
        Issued(std::weak_ptr<const void> owner,Session::NativeCharacterList delivery,
            NativeCharacterSummarySnapshot snapshot,std::vector<RecoveredCharacter> roots,Scope scope)
            :owner_(std::move(owner)),delivery_(std::move(delivery)),snapshot_(std::move(snapshot)),
             roots_(std::move(roots)),issuer_scope_(std::move(scope)) {}
    public:
        Issued(const Issued&)=delete;
        Issued& operator=(const Issued&)=delete;
        bool active() const noexcept {return active_;}
        bool source_alive() const noexcept {return !owner_.expired();}
        const Session::NativeCharacterList& delivery() const noexcept {return delivery_;}
        const NativeCharacterSummarySnapshot& snapshot() const noexcept {return snapshot_;}
        std::span<const RecoveredCharacter> roots() const noexcept {return roots_;}
        const Scope& issuer_scope() const noexcept {return issuer_scope_;}
    };
    // Private, immutable selection provenance. Retaining this data keeps no
    // Session, repository, Target or game callback alive; it is not an admission
    // reservation or a native acknowledgement of the later world frame.
    class Selected final {
        friend class SharedTaiwanNativeCharacterListSource;
        std::weak_ptr<const void> owner_;
        std::uint64_t character_;
        Scope scope_;
        NativeCharacterSummarySnapshot snapshot_;
        std::vector<RecoveredCharacter> roots_;
        Selected(std::weak_ptr<const void> owner,std::uint64_t character,Scope scope,
                NativeCharacterSummarySnapshot snapshot,std::vector<RecoveredCharacter> roots)
            :owner_(std::move(owner)),character_(character),scope_(std::move(scope)),
             snapshot_(std::move(snapshot)),roots_(std::move(roots)) {}
    public:
        Selected(const Selected&)=delete;
        Selected& operator=(const Selected&)=delete;
        bool source_alive() const noexcept {return !owner_.expired();}
        std::uint64_t character() const noexcept {return character_;}
        const Scope& scope() const noexcept {return scope_;}
        const NativeCharacterSummarySnapshot& snapshot() const noexcept {return snapshot_;}
        std::span<const RecoveredCharacter> roots() const noexcept {return roots_;}
    };
    using SelectedPtr=std::shared_ptr<const Selected>;
    struct SelectedLink {SelectedPtr selected;std::function<bool()> current;};
    using SelectedSource=std::function<std::optional<SelectedLink>(
        std::uint64_t session,std::uint64_t account,std::uint64_t character)>;
    // Real bounded handoff owner registers dormant record. False/throw/reentry
    // never activates it. Retire retained records by actual lifecycle, not a
    // made-up native timeout or account-latest selection.
    using Publish=std::function<bool(Session&,const IssuedPtr&)>;
    struct Link {
        IssuedPtr issued;
        std::function<bool(Session&,const Scope&)> current;
    };
    // New G identity/auth/transport/phase/projection qualification is mandatory.
    // Issued active() alone grants neither selection nor parallel/replay rights.
    using LinkSource=std::function<std::optional<Link>(Session&,const Scope&)>;
    struct Target {
        std::uint16_t group,server; // Actual storage/catalog scope, not guessed TW6B fields.
        std::function<bool(Session&,const Scope&)> current;
        Target(std::uint16_t,std::uint16_t,std::function<bool(Session&,const Scope&)>);
    };
    // Real per-Session realm/destination/phase source, with mandatory Current.
    // No default group0/server0/route1; do not reinterpret the fixture6B tail.
    using TargetSource=std::function<std::optional<Target>(Session&,const Scope&)>;
    using Qualify=std::function<bool(Session&,const Scope&,const Target&,
        const NativeCharacterSummarySnapshot&,std::span<const RecoveredCharacter>,Check)>;
    // Explicit issuer materialization, only on List before capturing its actual
    // stored observation. current observes session/roots/target/reentry, never
    // an old stored tuple while the writer stages next. Do not retain inputs.
    using Prepare=std::function<bool(Session&,const Scope&,const Target&,
        std::span<const RecoveredCharacter>,const std::function<bool()>& current)>;
    struct Binding {
        decltype(Session::RecoveredCharacterHandlers::native_list) list;
        decltype(Session::RecoveredCharacterHandlers::native_select) select;
        std::function<void()> invalidate_active;
        decltype(Session::RecoveredCharacterHandlers::native_list_current) current;
        decltype(Session::RecoveredCharacterHandlers::native_list_complete) complete;
        SelectedSource selected;
        // Revoke this exact pre-use selection even between Current calls. A
        // caught outer Entry rejection must be visible before issuer COMMIT.
        std::function<void(std::uint64_t session)> invalidate_selection;
    };
    // Borrowed exact same-Database sources until game-owner facade drain.
    // Real target and full native visibility/token/route/resource/source/phase
    // authority remain supplied, pure synchronous and non-yielding. Never pump,
    // persist, retain Scope/Session references or default to success here.
    static Binding create(AccountRepository&,RecoveredCharacterRepository&,
        NativeCharacterSummarySnapshotRepository&,std::string client_sha256,TargetSource,Qualify,
        std::size_t actual_pending_capacity,Publish,LinkSource,Prepare actual_issuer={});
    // Current bridges held queue release and actual write completion on game.
    // Cross-socket links need the actual supplied owner; no complete2A authority
    // or native token/local-backing variant is inferred from a ticket.
};
}
