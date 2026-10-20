#pragma once
#include "handlers/SynchronousCallbackFence.h"
#include <type_traits>
#include <utility>
#include "db/SqliteOwnedMixedBankRepository.h"
#include "db/SqliteBeastBankRepository.h"
#include "handlers/RecoveredBankService.h"
#include "protocol/RecoveredBankItems.h"
#include <functional>
#include <map>

namespace god2 {
// CUSTOM-0070 opt-in complete vault custody exchange. Existing 63/64 repositories
// retain their mutation routes; full foreign metadata is verified before COMMIT.
class OwnedMixedBankService {
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
    using EligibleBeast=std::function<bool(const StoredVaultBeast&,const RecoveredBankItems::Request&)>;
    struct Result {Batches batches;bool committed{},rejected{};};
    // Both repositories MUST share the same SQLite connection; paired proofs
    // verify the full repository is inside the plain mutation transaction.
    OwnedMixedBankService(SqliteOwnedMixedBankRepository&,SqliteOwnedForeignBankRepository&,SqliteOwnedArmorBankRepository&,SqliteBankItemsRepository&,
        Lookup,Permit,Renew,Eligible,PlainProjection,Receipt,QualifyWeapon,SqliteBeastBankRepository* beasts=nullptr,EligibleBeast beast_eligible={});
    Batches open(std::uint64_t session,std::uint16_t target,Clock::time_point now);
    Result handle(std::uint64_t session,std::span<const RecoveredBankItems::Request>,Clock::time_point now);
    void disconnect(std::uint64_t session){callbacks_.invalidate_if_running();contexts_.erase(session);}
private:
    using Snapshot=SqliteBeastBankRepository::Snapshot;
    struct Context {std::uint16_t target;RecoveredBankService::Peer peer;Snapshot expected;};
    void require_live(std::uint64_t,const RecoveredBankService::Peer&,std::uint16_t,Clock::time_point) const;
    static void append(Batches&,std::span<const std::uint8_t>);
    Batches synchronization(const Snapshot&,const Snapshot* before,bool bags) const;
    std::array<std::uint8_t,29> vault_slot(const Snapshot&,std::size_t) const;
    std::vector<std::uint8_t> bag_slot(const Snapshot&,std::uint8_t) const;
    void validate_projection_snapshot(const Snapshot&) const;
    static SqliteBankItemsRepository::Snapshot plain_snapshot(const Snapshot&);
    Snapshot load_snapshot(std::uint64_t,std::uint64_t) const;
    void verify_snapshot(const Snapshot&) const;
    bool duplicate(const std::string&) const;
    SqliteOwnedMixedBankRepository& repo_;SqliteOwnedForeignBankRepository& foreign_repo_;SqliteOwnedArmorBankRepository& armor_repo_;SqliteBankItemsRepository& plain_repo_;
    Lookup lookup_;Permit permit_;Renew renew_;Eligible eligible_;PlainProjection plain_;Receipt receipt_;QualifyWeapon weapon_;
    SqliteBeastBankRepository* beasts_;EligibleBeast beast_eligible_;
    std::map<std::uint64_t,Context> contexts_;
    template<class F,class... Args>
    auto invoke_adapter(const F& function,Args&&... args) const {
        callbacks_.require_current();
        if constexpr(std::is_void_v<std::invoke_result_t<const F&,Args...>>) {
            function(std::forward<Args>(args)...);callbacks_.require_current();
        } else {
            auto result=function(std::forward<Args>(args)...);
            callbacks_.require_current();return result;
        }
    }
    SynchronousCallbackFence callbacks_;

};
}
