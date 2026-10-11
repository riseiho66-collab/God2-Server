#pragma once
#include "cn/auth/SharedCharacterDeleteIdentity.h"
#include "cn/protocol/CnWorldSelectionStatus.h"
#include "auth/SharedCharacterRemoval.h"
#include "auth/SharedCharacterRemovalPresence.h"
#include "db/SqliteNativeCharacterSummarySnapshotRepository.h"
#include <array>
#include <memory>
#include <thread>
#include <functional>
#include <optional>
#include <span>
#include <vector>

namespace god2::cn {
// Conditional native19 -> actual common CAS -> native02 operation. Neither
// native identity nor a zero status supplies permission. Application must bind
// the actual native rules/online/guild/replay owner and complete native bytes.
// Native1E and its unresolved post-API continuation remain separate, open.
class SharedCharacterDeleteOperation:
    public std::enable_shared_from_this<SharedCharacterDeleteOperation> {
public:
    using Connection=SharedCredentialConnection;
    class Attempt {
        friend class SharedCharacterDeleteOperation;
        Attempt()=default;
    };
    struct Scope {
        std::uint64_t account,world_session,character;
        std::uint8_t native_slot;
        std::shared_ptr<const Attempt> attempt;
        bool operator==(const Scope&) const=default;
    };
    enum class Check {BeforeErase,BeforeCommit,BeforeQueue,AfterQueue};
    using SummaryObservation=SqliteNativeCharacterSummarySnapshotRepository::RemovalObservation;
    class SummaryDecision {
    public:
        // Actual issuer explicitly authorizes ALL observed account delivery
        // scopes, not only CN or those mentioning removedID. Owned data tied
        // to this exact Attempt/full common row. No default native permission.
        // BeforeCommit sees staged absence while storage is not yet committed;
        // queue phases require actual successful removal and issuer's receipt
        // Current, never old raw-summary Current. Observer only, no SQL/yields,
        // nested transactions/event pumps or retained borrowed inputs.
        using Current=std::function<bool(const Scope&,Check,const SummaryObservation&)>;
        static std::optional<SummaryDecision> from_actual_issuer(Scope,RecoveredCharacter,
            SummaryObservation,Current);
        SummaryDecision(const SummaryDecision&)=delete;
        SummaryDecision& operator=(const SummaryDecision&)=delete;
        SummaryDecision(SummaryDecision&&) noexcept=default;
        SummaryDecision& operator=(SummaryDecision&&)=delete;
        bool matches(const Scope&,const RecoveredCharacter&,const SummaryObservation&) const;
        bool matches_removal_inputs(std::span<const NativeCharacterSummarySnapshot>,
            std::span<const RecoveredCharacter>) const;
        bool current(const Scope&,Check) const;
        const SummaryObservation& observation() const noexcept {return observation_;}
    private:
        SummaryDecision(Scope,RecoveredCharacter,SummaryObservation,Current);
        Scope scope_;
        RecoveredCharacter expected_;
        SummaryObservation observation_;
        Current current_;
    };
    class Decision {
    public:
        // Observing serial-game predicate: actual permission, operation/CAS,
        // active-world/guild constraints and semantic replay. BeforeCommit is
        // inside SQL with the root staged absent; Before/AfterQueue follow a
        // successful COMMIT or an unmutated nonzero reply. Do not require an old
        // offered07 membership after deletion. No writes/nested transaction,
        // yield/event pump, borrowed Scope captures or default-true authority.
        using Current=std::function<bool(const Scope&,Check)>;
        static std::optional<Decision> from_native(Scope,RecoveredCharacter expected,
            std::span<const std::uint8_t> complete02,Current);
        Decision(const Decision&)=delete;
        Decision& operator=(const Decision&)=delete;
        Decision(Decision&&)=default;
        Decision& operator=(Decision&&)=default;
        bool current(const Scope&,Check) const;
        bool removal_required() const noexcept {return status_==0;}
        const RecoveredCharacter& expected() const noexcept {return expected_;}
        std::span<const std::uint8_t,23> record_bytes() const {return record_;}
    private:
        Decision(Scope,RecoveredCharacter,std::array<std::uint8_t,23>,std::uint16_t,Current);
        Scope scope_;
        RecoveredCharacter expected_;
        std::array<std::uint8_t,23> record_;
        std::uint16_t status_;
        Current current_;
    };
    struct Sources {
        // Same actual common repository as Selection, lifetime owned by host.
        // No independent CN DB and no cast from an arbitrary interface object.
        SqliteRecoveredCharacterRepository* characters=nullptr;
        // Prepare authority/complete reply BEFORE saved state changes. Receives
        // only common identity and stored snapshot; never native credentials.
        // Supplier must not retain borrowed Scope/expected references or mutate
        // storage/admission here. The transaction
        // below is the only removal writer; durable receipt/recovery is open.
        std::function<std::optional<Decision>(const Scope&,const RecoveredCharacter&)> prepare;
        // Required actual common prepared/active leases and legacy occupancy
        // observer. This is separate from the still-required native authority.
        std::shared_ptr<const SharedCharacterRemovalPresence> presence;
        struct NativeSummaryRemoval {
            std::reference_wrapper<SqliteNativeCharacterSummarySnapshotRepository> snapshots;
            // Actual same-backend observation supplied by operation, not an
            // unprotected load_for_account or invented expected empty vector.
            std::function<std::optional<SummaryDecision>(const Scope&,const RecoveredCharacter&,
                const SummaryObservation&)> prepare;
            explicit operator bool() const noexcept {return bool(prepare);}
        };
        // Explicit selected storage mode. Selected malformed/failed sources
        // hard fail; no fallback to legacy. Nonzero native02 skips this mode.
        std::optional<NativeSummaryRemoval> native_summary_removal;
        explicit operator bool() const noexcept {
            return characters && prepare && presence && (!native_summary_removal || bool(*native_summary_removal));
        }
    };
    using CurrentSelection=std::function<bool(const Scope&)>;
    static std::shared_ptr<SharedCharacterDeleteOperation> prepare(
        const std::shared_ptr<Connection>&,RecoveredCharacterRepository&,
        std::shared_ptr<SharedWorldAdmission>,SharedCharacterDeleteIdentity,Sources,CurrentSelection);
    const Scope& scope() const noexcept {return scope_;}
    void start(Connection::Transport::Completion);
    bool terminal_quiescent() const;
    bool failure_reply_complete() const;
    // Owned process-local facts for this exact designated Scope/Attempt.
    // Does not supply native permission/success or durable recovery/receipt.
    struct RemovalOutcome {bool attempted,storage_committed,offers_invalidated;};
    RemovalOutcome removal_outcome() const;
private:
    enum class Phase {Prepared,Deciding,ReplyHeld,Removing,ReplyQueued,Completed,Failed,Stopped,CommittedFailure};
    SharedCharacterDeleteOperation(const std::shared_ptr<Connection>&,
        std::shared_ptr<SharedWorldAdmission>,SharedCharacterDeleteIdentity,
        Scope,RecoveredCharacter,Sources,CurrentSelection);
    void owner() const;
    bool selection_current() const;
    bool stored_current(bool removed) const;
    bool summary_queue_current(Check) const;
    // Called only by the transport's held-reply game continuation. Local
    // transaction observers below never escape this synchronous invocation.
    bool commit_held_reply();
    bool committed() const noexcept {return removal_observation_.storage_committed();}
    void stop();
    std::thread::id thread_=std::this_thread::get_id();
    std::weak_ptr<Connection> connection_;
    std::shared_ptr<SharedWorldAdmission> admission_;
    SharedCharacterDeleteIdentity identity_;
    Scope scope_;
    RecoveredCharacter expected_;
    Sources sources_;
    CurrentSelection selection_;
    std::shared_ptr<const Decision> decision_;
    std::shared_ptr<const SummaryDecision> summary_decision_;
    Phase phase_=Phase::Prepared;
    SharedCharacterRemoval::CommitObservation removal_observation_;
};
}
