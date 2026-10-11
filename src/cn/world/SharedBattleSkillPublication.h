#pragma once
#include "cn/protocol/CnBattleSkillUpdate87.h"
#include "cn/world/SharedNativeBattleCommandData.h"
#include <memory>
#include <optional>
#include <vector>

namespace god2::cn {
// Actual committed common event -> supplied native87 -> original held queue.
// No learning mutation, default flags, native actor IDs, or successful ACK.
class SharedBattleSkillPublication final {
    struct State;
    struct ReceiptStorage;
public:
    using Connection=SharedCredentialConnection;
    using Lease=SharedWorldPresence::Lease;
    using Token=SharedNativeWorldTransports::Token;
    using CatalogBinding=SharedNativeBattleCommandData::CatalogBinding;
    using Wire=god2cn::CnBattleSkillUpdate87;
    struct Scope {
        Lease lease;
        RecoveredCharacter character;
        RecoveredPosition saved_position;
        Token native_token;
    };
    struct Plan {
        Lease recipient;
        std::uint64_t actual_event_id,actual_committed_revision;
        std::vector<Wire::Record> actual_records; // Entire original order/WORD flags.
    };
    enum class Check {BeforeQueue,BeforeRelease,AfterRelease};
    class WorldOwner {
    public:
        virtual ~WorldOwner()=default;
        // Mandatory exact store lifetime/reader/catalog relationship BEFORE
        // every borrowed lookup. Non-null pointers or row existence do not prove it.
        virtual bool catalog_current(Connection&,const Scope&,const CatalogBinding&)=0;
        // Pure, read-only/nonyielding/nonreentrant post-commit observation.
        // Qualify common learned event/save/replay/actual revision, recipient's
        // battle/list/slot epoch, raw flags/order, definition/native namespace,
        // resources and native profile. No retained borrowed arguments.
        virtual bool current(Connection&,Check,const Scope&,const Plan&,
            const std::vector<NativeSkillRecord>&,const CatalogBinding&)=0;
    };
    struct Budgets {std::size_t max_records,max_logical_bytes;};
    class ReleaseReceipt final {
    public:
        const Scope& original_scope() const;
        const Plan& plan() const;
        const std::vector<NativeSkillRecord>& definitions() const;
        bool post_release_current() const;
        // Existence is the actual local held-release fact only. No client
        // receipt, learning/permission proof, or currently live connection.
    private:
        friend class SharedBattleSkillPublication;
        explicit ReleaseReceipt(std::shared_ptr<const ReceiptStorage>);
        std::shared_ptr<const ReceiptStorage> storage_;
    };
    static std::shared_ptr<SharedBattleSkillPublication> create(
        std::shared_ptr<SharedWorldPresence>,std::shared_ptr<SharedNativeWorldTransports>,
        CatalogBinding,std::shared_ptr<WorldOwner>,Budgets);
    bool owns_source(const std::shared_ptr<SharedWorldPresence>&,
        const std::shared_ptr<SharedNativeWorldTransports>&) const;
    bool owns_catalog(const CatalogBinding&) const;
    // Install once before readiness without any catalog/store read or send.
    // First actual ready publish acquires the existing original registry Token.
    bool bind(const std::shared_ptr<Connection>&,const Lease&);
    void publish(Plan,Connection::Transport::Completion);
    void invalidate_active();
    void release(); // Own pending/bookkeeping only; no common/token/core cleanup.
    std::optional<ReleaseReceipt> last_release() const;
    ~SharedBattleSkillPublication();
private:
    explicit SharedBattleSkillPublication(std::shared_ptr<State>);
    std::shared_ptr<State> state_;
};
}
