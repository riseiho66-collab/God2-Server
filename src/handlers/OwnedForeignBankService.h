#pragma once
#include "db/SqliteOwnedForeignBankRepository.h"
#include "handlers/RecoveredBankService.h"
#include "protocol/RecoveredBankItems.h"
#include <functional>
#include <map>

namespace god2 {
// CUSTOM-0068 opt-in full instance custody. Existing armor/MED repositories
// retain their mutation routes; full foreign metadata is verified before COMMIT.
class OwnedForeignBankService {
public:
    using Clock=RecoveredBankService::Clock;
    using Lookup=RecoveredBankService::Lookup;
    using Receipt=RecoveredBankService::Receipt;
    using Batches=std::vector<std::vector<std::uint8_t>>;
    using Permit=std::function<bool(std::uint64_t,std::uint16_t,Clock::time_point)>;
    using Renew=std::function<void(std::uint64_t,Clock::time_point)>;
    using Eligible=std::function<bool(const StoredInventorySlot&)>;
    using PlainProjection=std::function<std::vector<std::uint8_t>(std::uint8_t,const StoredInventorySlot&)>;
    using QualifyWeapon=std::function<bool(std::uint16_t)>;
    struct Result {Batches batches;bool committed{},rejected{};};
    // Both repositories MUST share the same SQLite connection; paired proofs
    // verify the full repository is inside the plain mutation transaction.
    OwnedForeignBankService(SqliteOwnedForeignBankRepository&,SqliteOwnedArmorBankRepository&,SqliteBankItemsRepository&,
        Lookup,Permit,Renew,Eligible,PlainProjection,Receipt,QualifyWeapon);
    Batches open(std::uint64_t session,std::uint16_t target,Clock::time_point now);
    Result handle(std::uint64_t session,std::span<const RecoveredBankItems::Request>,Clock::time_point now);
    void disconnect(std::uint64_t session){contexts_.erase(session);}
private:
    using Snapshot=SqliteOwnedForeignBankRepository::Snapshot;
    struct Context {std::uint16_t target;Snapshot expected;};
    static void append(Batches&,std::span<const std::uint8_t>);
    Batches synchronization(const Snapshot&,const Snapshot* before,bool bags) const;
    std::array<std::uint8_t,29> vault_slot(const Snapshot&,std::size_t) const;
    std::vector<std::uint8_t> bag_slot(const Snapshot&,std::uint8_t) const;
    void validate_projection_snapshot(const Snapshot&) const;
    static SqliteBankItemsRepository::Snapshot plain_snapshot(const Snapshot&);
    SqliteOwnedForeignBankRepository& repo_;SqliteOwnedArmorBankRepository& armor_repo_;SqliteBankItemsRepository& plain_repo_;
    Lookup lookup_;Permit permit_;Renew renew_;Eligible eligible_;PlainProjection plain_;Receipt receipt_;QualifyWeapon weapon_;
    std::map<std::uint64_t,Context> contexts_;
};
}
