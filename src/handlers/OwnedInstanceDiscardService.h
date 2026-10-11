#pragma once
#include "db/SqliteOwnedInstanceDiscardRepository.h"
#include "handlers/RecoveredBankService.h"
#include "protocol/RecoveredWorldRecords.h"
#include <functional>

namespace god2 {
// CUSTOM-0071: whole destruction of a qualified owned instance. Native27 has
// no revision/token. The existing CUSTOM-0061 scalar route remains separate.
class OwnedInstanceDiscardService {
public:
    using Clock=RecoveredBankService::Clock;
    using Peer=RecoveredBankService::Peer;
    using Lookup=RecoveredBankService::Lookup;
    using Receipt=RecoveredBankService::Receipt;
    using Permit=std::function<bool(std::uint64_t,std::uint8_t,Clock::time_point)>;
    using PlainProjection=std::function<std::vector<std::uint8_t>(std::uint8_t,const StoredInventorySlot&)>;
    using BeforeCommit=std::function<void(std::uint64_t)>;
    using PrepareExtra=SqliteOwnedInstanceDiscardRepository::Prepare;
    struct Result {std::vector<std::uint8_t> wire;bool committed{},rejected{};};
    OwnedInstanceDiscardService(SqliteOwnedInstanceDiscardRepository&,Lookup,Permit,Receipt,PlainProjection,BeforeCommit invalidate_bank={},PrepareExtra extra={});
    // Exactly one27 and optional native ticks, no second/mixed mutation.
    static std::optional<RecoveredInventoryDiscard::Request> request(std::span<const RecoveredWorldRecords::Record>);
    Result handle(std::uint64_t session,std::span<const RecoveredWorldRecords::Record>,Clock::time_point now);
private:
    using Snapshot=SqliteOwnedInstanceDiscardRepository::Snapshot;
    static bool same_owner_world(const Peer&,const Peer&);
    std::vector<std::uint8_t> project_source(const Snapshot&,std::uint8_t) const;
    SqliteOwnedInstanceDiscardRepository& repo_;
    Lookup lookup_;Permit permit_;Receipt receipt_;PlainProjection plain_;BeforeCommit invalidate_bank_;PrepareExtra extra_;
};
}
