#pragma once
#include "cn/auth/SharedCreationLocationIdentity.h"
#include "cn/auth/CnCreationNameProjection.h"
#include "cn/protocol/CnCharacterCreateStatus.h"
#include "db/SqliteRecoveredCharacterRepository.h"
#include <array>
#include <functional>
#include <memory>
#include <optional>
#include <span>
#include <thread>
#include <vector>

namespace god2::cn {
// Ordinary17/18 only. Qualified current-operation/native data suppliers remain
// mandatory: this controller cannot invent character defaults, permissions,
// native replies, shared transactions or special1B behavior.
class SharedCharacterCreateOperation:
    public std::enable_shared_from_this<SharedCharacterCreateOperation> {
public:
    using Connection=SharedCredentialConnection;
    using Request=god2cn::CnCharacterCreate;
    struct Scope {
        std::uint64_t account,world_session;
        std::shared_ptr<const Request> request;
        // Pointer identity is intentional; equal wire bytes are not the same
        // operation. Persistent semantic replay belongs to the actual writer.
        bool operator==(const Scope&) const=default;
    };
    struct Created {
        // Actual shared transaction output, not a CN->TW profile conversion.
        RecoveredCharacter character;
        std::vector<std::uint8_t> permitted_choices;
    };
    enum class ReplyCheck {BeforePublish,QueueAccepted};
    enum class CreateCheck {Prepared,BeforeInsert,BeforeCommit,ReadyForReply,QueueAccepted};
    class NativeCreatePlan {
    public:
        using Current=std::function<bool(const Scope&,CreateCheck)>;
        // Complete native reply and typed same-original-name common candidate/choices must be
        // prepared before SQL. This does not map17 to a TW profile or invent
        // native default stats, slot permissions, names or packet bytes. This
        // supports the bounded unchanged-name ordinary UI form; recovered
        // canonicalization/aliases require their own explicit source contract.
        static std::optional<NativeCreatePlan> from_native(Scope,
            std::span<const std::uint8_t> complete02,
            std::optional<CnCreationNameProjection>,
            std::vector<std::uint8_t> permitted_choices,Current);
        bool current(const Scope&,CreateCheck) const;
    private:
        friend class SharedCharacterCreateOperation;
        NativeCreatePlan(Scope,std::array<std::uint8_t,23>,
            std::optional<CnCreationNameProjection>,
            std::vector<std::uint8_t>,Current);
        Scope scope_;
        std::array<std::uint8_t,23> record_;
        std::optional<CnCreationNameProjection> candidate_;
        std::vector<std::uint8_t> choices_;
        Current current_;
    };
    class CreateResult {
    public:
        // Real rule/CAS/operation/replay owner must remain current through02
        // queue acceptance and until the qualified18 writer begins. All captures
        // own their lifetimes; the supplier must not retain a borrowed Scope&.
        // QueueAccepted is the game publication behind the actual IO barrier,
        // after framing/capacity success and before native bytes leave.
        using Current=std::function<bool(const Scope&,ReplyCheck)>;
        static std::optional<CreateResult> from_native(Scope,
            std::span<const std::uint8_t> complete02,std::optional<Created>,Current);
        CreateResult(const CreateResult&)=delete;
        CreateResult& operator=(const CreateResult&)=delete;
        CreateResult(CreateResult&&)=default;
        CreateResult& operator=(CreateResult&&)=default;
        bool current(const Scope&,ReplyCheck=ReplyCheck::BeforePublish) const;
        std::uint16_t status() const noexcept {return status_;}
        const std::optional<Created>& created() const noexcept {return created_;}
        std::span<const std::uint8_t,23> record_bytes() const {return record_;}
    private:
        CreateResult(Scope,std::array<std::uint8_t,23>,std::uint16_t,
                     std::optional<Created>,Current);
        Scope scope_;
        std::array<std::uint8_t,23> record_;
        std::uint16_t status_;
        std::optional<Created> created_;
        Current current_;
    };
    class ChoiceResult {
    public:
        // Actual committed choice and full18 source. This must check the writer's
        // consumed operation/CAS and destination entitlement, not only IDs.
        // Last argument is the actual reply's low3 native slot association;
        // common slot/ID cannot infer it. The18 writer must check that mapping.
        using Current=std::function<bool(const Scope&,std::uint64_t,std::uint8_t,std::uint8_t,ReplyCheck)>;
        static std::optional<ChoiceResult> from_native(Scope,std::uint64_t character,
            std::uint8_t choice,std::span<const std::uint8_t> complete18,Current);
        ChoiceResult(const ChoiceResult&)=delete;
        ChoiceResult& operator=(const ChoiceResult&)=delete;
        ChoiceResult(ChoiceResult&&)=default;
        ChoiceResult& operator=(ChoiceResult&&)=default;
        bool current(const Scope&,std::uint64_t,std::uint8_t,ReplyCheck=ReplyCheck::BeforePublish) const;
        std::span<const std::uint8_t,3> record_bytes() const {return record_;}
    private:
        ChoiceResult(Scope,std::uint64_t,std::uint8_t,std::array<std::uint8_t,3>,Current);
        Scope scope_;
        std::uint64_t character_;
        std::uint8_t choice_;
        std::array<std::uint8_t,3> record_;
        Current current_;
    };
    enum class ChoiceCheck {Prepared,BeforeInsert,BeforeCommit,ReadyForReply,QueueAccepted};
    class NativeChoicePlan {
    public:
        // Actual native destination/slot relation and current operation/rules,
        // not merely the persisted position. Observe only, own all captures.
        using Current=std::function<bool(const Scope&,std::uint64_t,std::uint8_t,std::uint8_t,ChoiceCheck)>;
        static std::optional<NativeChoicePlan> from_native(Scope,std::uint64_t character,
            std::uint8_t choice,std::span<const std::uint8_t> complete18,
            SqliteRecoveredCharacterRepository::InitialOwnedPosition,Current);
        bool current(const Scope&,std::uint64_t,std::uint8_t,ChoiceCheck) const;
    private:
        friend class SharedCharacterCreateOperation;
        NativeChoicePlan(Scope,std::uint64_t,std::uint8_t,std::array<std::uint8_t,3>,
            SqliteRecoveredCharacterRepository::InitialOwnedPosition,Current);
        Scope scope_;
        std::uint64_t character_;
        std::uint8_t choice_;
        std::array<std::uint8_t,3> record_;
        SqliteRecoveredCharacterRepository::InitialOwnedPosition position_;
        Current current_;
    };
    struct Sources {
        // Synchronous serial-game supplier. Must perform the real shared atomic
        // transaction/rules or return an actual full failure02. No default data.
        std::function<std::optional<CreateResult>(const Scope&)> create;
        std::function<std::optional<ChoiceResult>(const Scope&,
            const SharedCreationLocationIdentity&)> choose;
        // Alternative concrete common CAS path. Exact same repository as the
        // selection controller; prepare is observing, not a storage writer.
        // Use exactly one of create or characters+prepare; no implicit fallback.
        SqliteRecoveredCharacterRepository* characters=nullptr;
        std::function<std::optional<NativeCreatePlan>(const Scope&,
            std::span<const RecoveredCharacter>)> prepare;
        // Alternative initial-position CAS for ordinary18. Supplies actual
        // destination/native18 before writing; never infers map/spawn from
        // identity.projection(). Existing choose callback stays independent.
        std::function<std::optional<NativeChoicePlan>(const Scope&,
            const SharedCreationLocationIdentity&,const RecoveredCharacter&)> prepare_choice;
        explicit operator bool() const noexcept {
            const bool direct=create && !prepare;
            const bool cas=!create && characters && prepare;
            const bool choice_direct=choose && !prepare_choice;
            const bool choice_cas=!choose && characters && prepare_choice;
            // An otherwise unused repository declaration is not a third mode.
            if(characters && direct && choice_direct)return false;
            return (direct || cas) && (choice_direct || choice_cas);
        }
    };
    // Exact Selection controller/current world ticket, independent of an old
    // offered07 membership that a real commit may invalidate. Not rule authority.
    using CurrentSelection=std::function<bool(const Scope&)>;
    static std::shared_ptr<SharedCharacterCreateOperation> prepare(
        const std::shared_ptr<Connection>&,RecoveredCharacterRepository&,
        std::shared_ptr<const Request>,Sources,CurrentSelection);
    const Scope& scope() const noexcept {return scope_;}
    // Selection must retain and designate this owner before start(). Ingress is
    // held until each entire native reply's local queue result is returned.
    // Exact next operation stage is published behind the IO barrier before
    // bytes leave; queue callbacks never reapply stale pre-operation checks.
    void start(Connection::Transport::Completion);
    void receive_choice(std::span<const std::uint8_t>,Connection::Transport::Completion);
    bool retry_available() const;
    bool terminal_quiescent() const;
private:
    enum class Phase {Prepared,Creating,CreateReplyQueued,AwaitingChoice,
                      RetryAvailable,Failed,Choosing,ChoiceReplyQueued,Completed,Stopped};
    SharedCharacterCreateOperation(const std::shared_ptr<Connection>&,
        RecoveredCharacterRepository&,Scope,Sources,CurrentSelection,
        std::vector<RecoveredCharacter> existing_rows);
    void owner() const;
    bool selection_current() const;
    bool created_owned(bool exact_snapshot) const;
    bool pending_current(const std::shared_ptr<const Request>&,
                         std::uint64_t,std::span<const std::uint8_t>) const;
    void stop();
    std::thread::id thread_=std::this_thread::get_id();
    std::weak_ptr<Connection> connection_;
    RecoveredCharacterRepository& characters_;
    Scope scope_;
    Sources sources_;
    CurrentSelection selection_;
    std::vector<RecoveredCharacter> existing_rows_;
    std::shared_ptr<const CreateResult> created_;
    std::shared_ptr<const ChoiceResult> chosen_;
    Phase phase_=Phase::Prepared;
};
}
