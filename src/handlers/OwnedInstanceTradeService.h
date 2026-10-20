#pragma once
#include "handlers/RecoveredTradeService.h"
#include "db/SqliteOwnedInstanceTradeRepository.h"
#include "protocol/RecoveredInventoryProjection.h"

namespace god2 {
// CUSTOM-0069. Serialized executor only; explicit custom60s lease matches
// accepted0063 orchestration, not recovered original timing. Owned metadata is
// captured from validated storage, never accepted from a client offer.
class OwnedInstanceTradeService {
public:
    using Clock=RecoveredTradeService::Clock;
    using Peer=RecoveredTradeService::Peer;
    using Deliveries=RecoveredTradeService::Deliveries;
    using Result=RecoveredTradeService::Result;
    using Lookup=RecoveredTradeService::Lookup;
    using Resolve=RecoveredTradeService::Resolve;
    using Name=RecoveredTradeService::Name;
    using Eligible=RecoveredTradeService::Eligible;
    using PlainProjection=RecoveredTradeService::Projection;
    using Receipt=RecoveredTradeService::Receipt;
    using Repo=SqliteOwnedInstanceTradeRepository;
    using EligibleBeast=std::function<bool(const StoredBeastSnapshot&)>;
    OwnedInstanceTradeService(Repo&,Lookup,Resolve,Name,Eligible plain_eligible,PlainProjection,Receipt,EligibleBeast beast_eligible={});
    Result handle(std::uint64_t,std::span<const RecoveredTrade::Request>,Clock::time_point);
    Deliveries disconnect(std::uint64_t);
    Deliveries refresh(Clock::time_point);
    bool active(std::uint64_t) const;
private:
    struct Context {
        std::array<Peer,2> peers;
        std::array<Repo::Side,2> sides;
        std::array<bool,2> confirmed{},money_submitted{};
        Clock::time_point expires;
    };
    using Contexts=std::map<std::uint64_t,Context>;
    Repo& repo_;Lookup lookup_;Resolve resolve_;Name name_;Eligible eligible_;PlainProjection plain_;Receipt receipt_;
    EligibleBeast beast_eligible_;
    Contexts contexts_;
    // Serialized execution does not exclude synchronous adapter reentry.
    // A nested mutation poisons its original operation without erasing the
    // context whose iterator/snapshot is still in use by that operation.
    bool operation_running_=false,operation_invalid_=false;
    class Operation {
        OwnedInstanceTradeService& owner_;const bool entered_;
    public:
        explicit Operation(OwnedInstanceTradeService& owner) noexcept
            :owner_(owner),entered_(!owner.operation_running_) {
            if(entered_){owner_.operation_running_=true;owner_.operation_invalid_=false;}
            else owner_.operation_invalid_=true;
        }
        Operation(const Operation&)=delete;Operation& operator=(const Operation&)=delete;
        ~Operation(){if(entered_){owner_.operation_running_=false;owner_.operation_invalid_=false;}}
        explicit operator bool() const noexcept{return entered_;}
    };
    Deliveries disconnect_impl(std::uint64_t);
    static bool compatible(const Peer&,const Peer&);
    static void append(Deliveries&,std::uint64_t,const std::vector<std::uint8_t>&);
    Contexts::iterator find(std::uint64_t);
    // lease_current is safe after repository writes: it never compares saved
    // prewrite snapshots to the planned after-state.
    bool lease_current(const Context&) const;
    bool current(const Context&) const;
    static bool whole(const Repo::Snapshot&,std::uint8_t);
    static RecoveredInventoryProjection::Metadata metadata(const Repo::Snapshot&,std::uint8_t);
    std::vector<std::uint8_t> project(const Repo::Snapshot&,std::uint8_t) const;
    static Deliveries close_only(const Context&);
    Deliveries restore(const Context&) const;
};
}
