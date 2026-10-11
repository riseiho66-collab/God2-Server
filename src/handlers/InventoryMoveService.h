#pragma once
#include "db/SqliteRecoveredCharacterRepository.h"
#include "protocol/RecoveredInventoryMoveRequest.h"
#include <functional>

namespace god2 {
// CUSTOM-0037. Call only after standalone, world-ready, authenticated admission.
// This scalar storage has no equipment/upgrade metadata. Eligibility must be
// explicitly bound to current pinned map5569 or qualified MED02 catalog rows.
// CUSTOM-0089 quantity ceiling99 is applied before preparation and again by
//the writer. Eligibility still owns stackability/provenance; no merge, grant,
//equipment/PET transfer or alteration of over-limit historical saves follows.
class InventoryMoveService {
public:
    using Request=RecoveredInventoryMoveRequest::Request;
    using Eligible=std::function<bool(const StoredInventorySlot&)>;
    // Must prepare the full native projection for both resulting slots. All
    // allocation/encoding runs before the database transaction commits.
    using ReplyEncoder=std::function<std::vector<std::uint8_t>(const Request&,const InventoryMoveCommit&)>;
    struct Result {
        InventoryMoveCommit commit;
        std::vector<std::uint8_t> wire;
    };
    InventoryMoveService(SqliteRecoveredCharacterRepository& repository,Eligible eligible,ReplyEncoder reply)
        : repository_(repository),eligible_(std::move(eligible)),reply_(std::move(reply)) {}
    Result move(std::uint64_t account,std::uint64_t character,const Request& request,
        const StoredInventorySlot& expected_source,const StoredInventorySlot& expected_destination);
private:
    SqliteRecoveredCharacterRepository& repository_;
    Eligible eligible_;
    ReplyEncoder reply_;
};
}
