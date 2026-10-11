#pragma once
#include "cn/protocol/CnInlineRoleCounters24.h"
#include "game/SharedNativeWorldTransports.h"
#include <memory>
#include <optional>
#include <vector>

namespace god2::cn {
// Actual committed inline-role event -> original WORLD24 -> original held
// world queue. No actor ID exists in this record; the real common owner must
// qualify THIS recipient's current inline role and complete four raw DWORDs.
class SharedInlineRoleCountersPublication final {
    struct State;
    struct ReceiptStorage;
public:
    using Connection=SharedCredentialConnection;
    using Lease=SharedWorldPresence::Lease;
    using Token=SharedNativeWorldTransports::Token;
    using Wire=god2cn::CnInlineRoleCounters24;
    struct Scope {
        Lease lease;
        RecoveredCharacter character;
        RecoveredPosition saved_position;
        Token native_token;
    };
    struct Plan {
        Lease recipient;
        std::uint64_t actual_event_id,actual_committed_revision;
        std::vector<Wire> actual_records; //All seventeen native bytes, original order.
    };
    enum class Check {BeforeQueue,BeforeRelease,AfterRelease};
    class WorldOwner {
    public:
        virtual ~WorldOwner()=default;
        // Required actual post-commit common authority, read-only/nonyielding/
        // nonreentrant. Qualify event/save/durable replay/revision, recipient's
        // inline-role identity/lifetime/profile, every word and order. Raw
        // DWORDs/resource IDs/client pointers cannot authorize themselves.
        // No native process-memory reader or pre-commit snapshot is required.
        virtual bool current(Connection&,Check,const Scope&,const Plan&)=0;
    };
    struct Budgets {std::size_t max_records,max_logical_bytes;};
    class ReleaseReceipt final {
    public:
        const Scope& original_scope() const;
        const Plan& plan() const;
        bool post_release_current() const;
        // Delivered-TRUE LOCAL held-release fact only; never ACK/client acceptance or
        // proof of C1F/C25 causality, learning, numerical semantics or numeric64.
        // Legacy transport masks accepted=true if closing before its game
        // callback. No receipt/false completion therefore leaves release
        // UNKNOWN; it never proves no release and must not authorize replay.
    private:
        friend class SharedInlineRoleCountersPublication;
        explicit ReleaseReceipt(std::shared_ptr<const ReceiptStorage>);
        std::shared_ptr<const ReceiptStorage> storage_;
    };
    static std::shared_ptr<SharedInlineRoleCountersPublication> create(
        std::shared_ptr<SharedWorldPresence>,std::shared_ptr<SharedNativeWorldTransports>,
        std::shared_ptr<WorldOwner>,Budgets);
    bool owns_source(const std::shared_ptr<SharedWorldPresence>&,
        const std::shared_ptr<SharedNativeWorldTransports>&) const;
    // Bind once during real1C preparation; no event read, send or default owner.
    // First actual ready publication acquires the existing registry Token.
    bool bind(const std::shared_ptr<Connection>&,const Lease&);
    // Completion preserves the existing transport bool. True is positive
    // local release evidence; false can include released-then-closed. The
    // actual common issuer owns durable recovery, never this local bool.
    void publish(Plan,Connection::Transport::Completion);
    void invalidate_active();
    void release(); //Own pending bookkeeping only; no core/token/event release.
    std::optional<ReleaseReceipt> last_release() const;
    ~SharedInlineRoleCountersPublication();
private:
    explicit SharedInlineRoleCountersPublication(std::shared_ptr<State>);
    std::shared_ptr<State> state_;
};
}
