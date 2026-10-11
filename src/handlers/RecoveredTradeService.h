#pragma once
#include "db/SqliteTradeRepository.h"
#include "protocol/RecoveredTrade.h"
#include <chrono>
#include <functional>
#include <map>

namespace god2 {
// CUSTOM-0063. Invoke on the serialized game executor. Native UI temporarily
// removes offered inventory locally; persistent items remain owned until the
// single two-player commit, and cancellation projects current saved contents.
class RecoveredTradeService {
public:
    using Clock=std::chrono::steady_clock;
    struct Peer {
        std::uint64_t session{},account{},character{};
        std::uint16_t area{},scene{};
        bool ready{};
    };
    using Deliveries=std::map<std::uint64_t,std::vector<std::uint8_t>>;
    struct Result {Deliveries deliveries;bool committed{},rejected{};};
    using Lookup=std::function<std::optional<Peer>(std::uint64_t)>;
    using Resolve=std::function<std::optional<Peer>(std::uint16_t)>;
    using Name=std::function<RecoveredTrade::Name(const Peer&,const Peer&)>;
    using Eligible=std::function<bool(const StoredInventorySlot&)>;
    using Projection=std::function<std::vector<std::uint8_t>(std::uint8_t,const StoredInventorySlot&)>;
    using OwnedProjection=std::function<std::vector<std::uint8_t>(std::uint64_t,std::uint64_t,std::uint8_t,const StoredInventorySlot&,const StoredInventorySlot&)>;
    using Receipt=std::function<std::string()>;
    RecoveredTradeService(SqliteTradeRepository& repo,Lookup lookup,Resolve resolve,
        Name name,Eligible eligible,Projection projection,Receipt receipt,OwnedProjection owned_projection={},SqliteTradeRepository::PrepareProof proof={})
        :repo_(repo),lookup_(std::move(lookup)),resolve_(std::move(resolve)),name_(std::move(name)),
        eligible_(std::move(eligible)),projection_(std::move(projection)),receipt_(std::move(receipt)),owned_projection_(std::move(owned_projection)),proof_(std::move(proof)) {}
    Result handle(std::uint64_t session,std::span<const RecoveredTrade::Request> requests,Clock::time_point now);
    Deliveries disconnect(std::uint64_t session);
    Deliveries refresh(Clock::time_point now);
    bool active(std::uint64_t session) const;
private:
    struct Context {
        std::array<Peer,2> peers;
        std::array<SqliteTradeRepository::Side,2> sides;
        std::array<bool,2> confirmed{};
        std::array<bool,2> money_submitted{};
        Clock::time_point expires;
    };
    using Contexts=std::map<std::uint64_t,Context>;
    Contexts contexts_;
    SqliteTradeRepository& repo_;
    Lookup lookup_;Resolve resolve_;Name name_;Eligible eligible_;Projection projection_;Receipt receipt_;
    OwnedProjection owned_projection_;SqliteTradeRepository::PrepareProof proof_;
    std::vector<std::uint8_t> project(std::uint64_t account,std::uint64_t character,std::uint8_t slot,const StoredInventorySlot& before,const StoredInventorySlot& after) const;
    static bool compatible(const Peer&,const Peer&);
    static void append(Deliveries&,std::uint64_t,const std::vector<std::uint8_t>&);
    Contexts::iterator find(std::uint64_t session);
    bool current(const Context&) const;
    Deliveries restore(const Context&) const;
};
}
