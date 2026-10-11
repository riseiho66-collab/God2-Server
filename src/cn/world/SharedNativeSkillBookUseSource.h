#pragma once
#include "cn/assets/CnNativeSkillBookBindings.h"
#include "cn/assets/CnSharedSkillBookSourceCatalog.h"
#include "cn/protocol/CnSkillBookUse25.h"
#include "game/SharedNativeWorldTransports.h"
#include <functional>
#include <memory>
#include <optional>
#include <utility>
#include <vector>

namespace god2::cn {
class SharedNativeSkillBookUseSource final {
public:
    using Connection=SharedCredentialConnection;
    using Lease=SharedWorldPresence::Lease;
    using Token=SharedNativeWorldTransports::Token;
    using Request=god2cn::CnSkillBookUse25::Request;
    using ControlRequest=god2cn::CnSkillBookUse25::ControlRequest;
    using Book=CnNativeSkillBookBindings::Book;
    using StoredBook=NativeSkillBookSourceRecord;
    struct Scope {Lease lease;RecoveredCharacter character;RecoveredPosition saved_position;Token native_token;};
    class Reply {
    public:
        static Reply records(std::vector<god2cn::Bytes> actual);
        static Reply no_reply();
        const std::vector<god2cn::Bytes>& logical_records() const noexcept {return records_;}
        bool native_no_reply() const noexcept {return no_reply_;}
    private:
        Reply(std::vector<god2cn::Bytes>,bool);
        std::vector<god2cn::Bytes> records_;bool no_reply_;
    };
    class OperationEvidence {public:virtual ~OperationEvidence()=default;};
    struct Result {
        Reply reply;
        std::shared_ptr<const OperationEvidence> evidence; // Mandatory actual immutable operation proof.
        Result(Reply actual,std::shared_ptr<const OperationEvidence> proof):reply(std::move(actual)),evidence(std::move(proof)){}
    };
    enum class Check {BeforeCatalog,BeforeExecute,AfterExecute,BeforeQueue,BeforeRelease,AfterRelease};
    struct Budgets {std::size_t max_reply_records,max_reply_logical_bytes;};
    class WorldOwner {
    public:
        virtual ~WorldOwner()=default;
        // Pure/non-yielding/non-reentrant observers; no writes/sends/pumping or
        // retained borrowed arguments. BeforeCatalog must qualify the actual
        // shared store/reader lifetime BEFORE any book/native catalog reads;
        // book/stored/result are null then. All other stages see the same owned
        // SKB and exact same-DB source record, neither of which grants custody.
        // Real owner supplies native eligibility, common actor mapping, custody,
        // learned before/after, atomic debit/save/replay and native reply/profile.
        // True issuer prepares complete native replies and immutable evidence
        // before committed effects, and owns ONE learned+book+durable-event
        // transaction/replay boundary. Source output-copy/queue failures after
        // execute terminalize without retry or rollback of that committed prefix.
        // A raw alias/item/slot is never a skill grant or shared identity.
        virtual bool current(Connection&,Check,const Scope&,const Request&,const Book*,const StoredBook*,const Result*)=0;
        virtual std::optional<Result> execute(Connection&,const Scope&,const Request&,const Book&,const StoredBook&)=0;
        virtual void release_binding(const Lease&,const Token&) noexcept {}
    };
    class ControlOwner {
    public:
        virtual ~ControlOwner()=default;
        // Independent exact ready-world1F00 authority; no implied25 outcome,
        // acquisition or initial1F reuse. Same pure observing/once-execute and
        // immutable evidence contract. No catalog/book access in this branch.
        virtual bool current(Connection&,Check,const Scope&,const ControlRequest&,const Result*)=0;
        virtual std::optional<Result> execute(Connection&,const Scope&,const ControlRequest&)=0;
        virtual void release_binding(const Lease&,const Token&) noexcept {}
    };
    struct Binding {
        Connection::Ingress ingress; // Empty when actual WorldOwner not selected.
        std::function<void()> invalidate_active;
        std::function<void()> release; // Own pending only; no common/token cleanup.
        Connection::Ingress control_ingress; // Empty without independent ControlOwner.
    };
    // Before initial readiness: no catalog/repository read here. Lazy original
    // registry token acquisition at the first real ready request. The permanent
    // receiver is weak; operation/held queue temporarily retain it strongly.
    static Binding create(const std::shared_ptr<Connection>&,std::shared_ptr<SharedWorldPresence>,const Lease&,
        std::shared_ptr<SharedNativeWorldTransports>,std::shared_ptr<const CnNativeSkillBookBindings>,
        std::shared_ptr<const CnSharedSkillBookSourceCatalog>,std::shared_ptr<WorldOwner>,Budgets,
        std::shared_ptr<ControlOwner> = {});
};
}
