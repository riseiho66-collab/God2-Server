#pragma once
#include "cn/net/SharedCredentialConnection.h"
#include "cn/protocol/CnBattleCommand35.h"
#include "game/SharedNativeWorldTransports.h"
#include <functional>
#include <memory>
#include <optional>
#include <utility>
#include <vector>

namespace god2::cn {
// Actual CN ready connection -> entire native35 request -> real battle owner
// -> ordered logical replies through its original held native transport.
// Ready common identity supplies no battle grant, actor mapping or settlement.
class SharedNativeBattleCommandSource final {
public:
    using Connection=SharedCredentialConnection;
    using Lease=SharedWorldPresence::Lease;
    using Token=SharedNativeWorldTransports::Token;
    using Request=god2cn::CnBattleCommand35::Request;
    struct Scope {
        Lease lease;
        RecoveredCharacter character; // Full common root, never raw actor position.
        RecoveredPosition saved_position;
        Token native_token; // Original private endpoint incarnation; never a battle grant.
    };
    class Reply {
    public:
        static Reply records(std::vector<god2cn::Bytes> actual_ordered_logical);
        static Reply no_reply(); // Explicit real native operation decision only.
        const std::vector<god2cn::Bytes>& logical_records() const noexcept {return records_;}
        bool native_no_reply() const noexcept {return no_reply_;}
    private:
        Reply(std::vector<god2cn::Bytes>,bool);
        std::vector<god2cn::Bytes> records_;
        bool no_reply_;
    };
    class OperationEvidence {
    public:
        virtual ~OperationEvidence()=default;
    };
    struct Result {
        Reply reply;
        // Opaque immutable actual owner evidence, never synthesized by this source.
        std::shared_ptr<const OperationEvidence> evidence;
        explicit Result(Reply actual,std::shared_ptr<const OperationEvidence> proof={})
            :reply(std::move(actual)),evidence(std::move(proof)) {}
    };
    enum class Check {BeforeExecute,AfterExecute,BeforeQueue,BeforeRelease,AfterRelease};
    struct Budgets {std::size_t max_reply_records,max_reply_logical_bytes;};
    class WorldOwner {
    public:
        virtual ~WorldOwner()=default;
        // Mandatory actual native battle/actor ownership,82 context,86 grant,
        // incarnation, primary/secondary commands, targets/formation, learned
        // skills, MP/range, held item slot/count, semantic duplicate handling,
        // once settlement and complete ordered native replies/cipher/profile.
        // Pure read-only/non-yielding/non-reentrant: no write/send/pump or
        // retained borrowed arguments. Post checks see freshly observed Scope
        // and the exact retained Result. Raw positions are not common IDs;
        // padding/unknown kinds/operands are not normalized or inferred grants.
        // Qualify actual native command variants: raw target field is not a
        // universal mask, and continuation records are not implicit duplicates.
        virtual bool current(Connection&,Check,const Scope&,const Request&,const Result*)=0;
        // Exactly once after qualification. Actual native request remains owned
        // in full. Real committed prefixes are neither rolled back nor retried.
        // Actual logical records/noReply only, never pre-encrypted envelopes,
        // guessed ACK/cost/clock/default success. Null/failure terminalizes source.
        virtual std::optional<Result> execute(Connection&,const Scope&,const Request&)=0;
        // Retire only this exact bound owner's pending operation/group. No
        // transport/presence/successor cleanup, sends, pumping or throwing.
        // Invoked once outside Current/Execute stages, already terminal.
        virtual void release_binding(const Lease&,const Token&) noexcept {}
    };
    struct Binding {
        Connection::Ingress ingress;
        std::function<void()> invalidate_active;
        std::function<void()> release; // Exact own binding only; no common cleanup.
    };
    // Initialize before initial readiness. First actual ready request lazily
    // acquires the original private registry Token; permanent receiver is weak.
    static Binding create(const std::shared_ptr<Connection>&,
        std::shared_ptr<SharedWorldPresence>,const Lease&,
        std::shared_ptr<SharedNativeWorldTransports>,std::shared_ptr<WorldOwner>,Budgets);
};
}
