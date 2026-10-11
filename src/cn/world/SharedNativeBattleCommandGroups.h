#pragma once
#include "cn/world/SharedNativeBattleCommandSource.h"
#include <span>

namespace god2::cn {
// Bounded physical-request grouping, selected explicitly by the real native
// battle Authority. Continuation bytes never imply a cost, grant or duplicate.
class SharedNativeBattleCommandGroups final:public SharedNativeBattleCommandSource::WorldOwner {
    struct State;
public:
    using Source=SharedNativeBattleCommandSource;
    using Connection=Source::Connection;
    using Lease=Source::Lease;
    using Request=Source::Request;
    using Scope=Source::Scope;
    using Check=Source::Check;
    using Reply=Source::Reply;
    using Result=Source::Result;
    using Token=SharedNativeWorldTransports::Token;
    enum class Part {Single,Append,Final};
    class Capability {
    public:
        virtual ~Capability()=default;
    };
    struct Plan {
        Part part;
        // Actual issuer/group identities, not wire contexts/hashes/GUI IDs.
        std::shared_ptr<const Capability> issuer,group;
        std::uint64_t actual_issuer_generation,actual_group_generation; // Exact supplied values, including zero.
        std::optional<Reply> intermediate_reply; // Mandatory for Append only.
    };
    class Authority {
    public:
        virtual ~Authority()=default;
        // Pure, non-yielding/read-only/non-reentrant. No retained borrowed
        // arguments. Independently qualify context/grant/actor incarnation,
        // command variant/targets/skill/MP/item/expiry/replay and group order.
        // Saved spans are complete physical requests; no native limit14 or
        // special-WORD mask is inferred here. Null is unavailable, not success.
        virtual std::optional<Plan> prepare(Connection&,const Scope&,const Request&,
            std::span<const Request> saved,const Plan* saved_plan)=0;
        virtual bool current(Connection&,Check,const Scope&,const Request&,
            const Plan&,std::span<const Request> complete,const Result* actual)=0;
        // Single/Final only, exactly once. Complete owned input is in physical
        // arrival order. Real settlement/replies belong to this authority;
        // failed committed prefixes cannot be rolled back or replayed.
        virtual std::optional<Result> execute_group(Connection&,const Scope&,
            std::span<const Request> complete,const Plan&)=0;
    };
    struct Budgets {std::size_t max_request_records,max_request_logical_bytes;};
    static std::shared_ptr<SharedNativeBattleCommandGroups> create(
        const std::shared_ptr<Connection>&,const Lease&,
        std::shared_ptr<SharedNativeWorldTransports>,std::shared_ptr<Authority>,Budgets);
    ~SharedNativeBattleCommandGroups();
    bool current(Connection&,Check,const Scope&,const Request&,const Result*) override;
    std::optional<Result> execute(Connection&,const Scope&,const Request&) override;
    // Exact local context only; no common/token/core settlement cleanup.
    void release_binding(const Lease&,const Token&) noexcept override;
private:
    explicit SharedNativeBattleCommandGroups(std::shared_ptr<State>);
    std::shared_ptr<State> state_;
};
}
