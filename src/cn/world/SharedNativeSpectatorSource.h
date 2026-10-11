#pragma once
#include "cn/net/SharedCredentialConnection.h"
#include "cn/protocol/CnSpectator6E.h"
#include "cn/protocol/CnSpectatorClose.h"
#include "game/SharedNativeSpectatorPublication.h"
#include "game/SharedNativeSpectatorTargets.h"
#include <functional>
#include <memory>
#include <optional>
#include <utility>
#include <vector>

namespace god2::cn {
// Actual ready CN recipient -> exact native6E -> real operation -> ordered
// logical records through that connection's native held framing/encryption.
// No CN battle counter/state is fabricated from the TW Session interface.
class SharedNativeSpectatorSource final {
public:
    using Connection=SharedCredentialConnection;
    using Lease=SharedWorldPresence::Lease;
    using Request=god2cn::CnSpectator6E::Request;
    using CloseRequest=god2cn::CnSpectatorClose::Request;
    struct Scope {
        Lease lease;
        RecoveredCharacter character;
        RecoveredPosition saved_position;
        // nullopt is NotSelected. All selected negative states are facts,
        // neither permission nor rejection of other native DWORD namespaces.
        std::optional<SharedNativeSpectatorPublication::Observation> native_ui;
        std::optional<SharedNativeSpectatorTargets::Observation> target;
    };
    class Reply {
    public:
        static Reply records(std::vector<god2cn::Bytes> actual_ordered_logical);
        static Reply no_reply(); // Explicit real native handler decision only.
        const std::vector<god2cn::Bytes>& logical_records() const noexcept {return records_;}
        bool native_no_reply() const noexcept {return no_reply_;}
    private:
        Reply(std::vector<god2cn::Bytes>,bool);
        std::vector<god2cn::Bytes> records_;
        bool no_reply_;
    };
    struct Result {
        Reply reply;
        explicit Result(Reply actual):reply(std::move(actual)) {}
    };
    enum class Check {BeforeExecute,AfterExecute,BeforeQueue,BeforeRelease,AfterRelease};
    struct Budgets {std::size_t max_reply_records,max_reply_logical_bytes;};
    class WorldOwner {
    public:
        virtual ~WorldOwner()=default;
        // Mandatory actual CN native phase/battle membership/incarnation,
        // execution ticket, request namespace/target/current UI and rules.
        // No CN battle getter/counter exists here; UI/target observations do
        // not supply those rights. Pure read-only, non-yielding/non-reentrant;
        // never send/write/pump or retain borrowed parameters. Post checks use
        // freshly observed actual Scope and the same retained execution Result.
        // Qualify complete actual reply records and this native cipher/profile.
        virtual bool current(Connection&,Check,const Scope&,const Request&,const Result*)=0;
        // Exactly once after qualification. Real committed prefixes are not
        // rolled back or retried. All original request bytes remain available.
        // Output is actual logical records, never pre-encrypted envelopes or
        // an inferred same-opcode ACK. A null/failure terminalizes this source.
        virtual std::optional<Result> execute(Connection&,const Scope&,const Request&)=0;
    };
    class CloseOwner {
    public:
        virtual ~CloseOwner()=default;
        // Independent actual native window/phase/membership/rights and reply
        // qualification; same pure observer/once execution/prefix contract.
        // Actual UI is retained, target is nullopt, no context0 is manufactured.
        // Source never automatically retires UI/targets or leaves battle.
        virtual bool current(Connection&,Check,const Scope&,const CloseRequest&,const Result*)=0;
        virtual std::optional<Result> execute(Connection&,const Scope&,const CloseRequest&)=0;
    };
    struct Binding {
        Connection::Ingress ingress;
        std::function<void()> invalidate_active;
        std::function<void()> release; // Exact own binding, no registry/common cleanup.
        Connection::Ingress close_ingress; // Empty unless actual CloseOwner/UI selected.
    };
    // Initialize before initial readiness; registry acquisition is lazy on the
    // first actual ready request. Permanent receiver retention is weak only.
    static Binding create(const std::shared_ptr<Connection>&,
        std::shared_ptr<SharedWorldPresence>,const Lease&,
        std::shared_ptr<SharedNativeWorldTransports>,std::shared_ptr<WorldOwner>,Budgets,
        std::shared_ptr<SharedNativeSpectatorPublication> = {},
        std::shared_ptr<SharedNativeSpectatorTargets> = {},
        std::shared_ptr<CloseOwner> = {});
};
}
