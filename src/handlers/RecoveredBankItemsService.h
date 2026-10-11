#pragma once
#include "db/SqliteBankItemsRepository.h"
#include "handlers/RecoveredBankService.h"
#include "protocol/RecoveredBankItems.h"
#include <functional>
#include <map>
namespace god2 {
// CUSTOM-0065: scoped ordinary scalar bank transfers using the existing
// independently qualified bank money lease. No new NPC/access authority.
class RecoveredBankItemsService {
public:
    using Clock=RecoveredBankService::Clock;
    using Lookup=RecoveredBankService::Lookup;
    using Batches=std::vector<std::vector<std::uint8_t>>;
    using Permit=std::function<bool(std::uint64_t,std::uint16_t,Clock::time_point)>;
    using Renew=std::function<void(std::uint64_t,Clock::time_point)>;
    using Eligible=std::function<bool(const StoredInventorySlot&)>;
    using Projection=std::function<std::vector<std::uint8_t>(std::uint8_t,const StoredInventorySlot&)>;
    using OwnedProjection=std::function<std::vector<std::uint8_t>(std::uint64_t,std::uint64_t,std::uint8_t,const StoredInventorySlot&,const StoredInventorySlot&)>;
    using Receipt=RecoveredBankService::Receipt;
    struct Result {Batches batches;bool committed{},rejected{};};
    RecoveredBankItemsService(SqliteBankItemsRepository& repo,Lookup lookup,Permit permit,Renew renew,
        Eligible eligible,Projection projection,Receipt receipt,OwnedProjection owned_projection={},SqliteBankItemsRepository::PrepareProof proof={}):repo_(repo),lookup_(std::move(lookup)),
        permit_(std::move(permit)),renew_(std::move(renew)),eligible_(std::move(eligible)),
        projection_(std::move(projection)),receipt_(std::move(receipt)),owned_projection_(std::move(owned_projection)),proof_(std::move(proof)){}
    Batches open(std::uint64_t session,std::uint16_t target,Clock::time_point now);
    Result handle(std::uint64_t session,std::span<const RecoveredBankItems::Request> requests,Clock::time_point now);
    void disconnect(std::uint64_t session){contexts_.erase(session);}
private:
    struct Context {std::uint16_t target;SqliteBankItemsRepository::Snapshot expected;};
    static void append(Batches& batches,std::span<const std::uint8_t> logical);
    std::array<std::uint8_t,29> bank_slot(std::size_t flat,const StoredInventorySlot& slot) const;
    Batches synchronization(const SqliteBankItemsRepository::Snapshot& current,
        const SqliteBankItemsRepository::Snapshot* previous,bool bags) const;
    SqliteBankItemsRepository& repo_;Lookup lookup_;Permit permit_;Renew renew_;
    Eligible eligible_;Projection projection_;Receipt receipt_;std::map<std::uint64_t,Context> contexts_;
    OwnedProjection owned_projection_;SqliteBankItemsRepository::PrepareProof proof_;
};
}
