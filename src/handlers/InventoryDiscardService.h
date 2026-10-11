#pragma once
#include "db/SqliteRecoveredCharacterRepository.h"
#include "db/DbTypes.h"
#include "protocol/RecoveredInventoryDiscard.h"
#include "protocol/RecoveredInventoryProjection.h"
#include "protocol/RecoveredWorldFrame.h"
#include <functional>

namespace god2 {
// CUSTOM-0061: destructive discard for qualified, owned scalar bag records.
// Does not create a ground drop, grant money or invent enhanced item metadata.
class InventoryDiscardService {
public:
    using Eligible=std::function<bool(const StoredInventorySlot&)>;
    struct Result {StoredInventorySlot slot;std::vector<std::uint8_t> wire;};
    InventoryDiscardService(SqliteRecoveredCharacterRepository& repository,Eligible eligible)
        : repository_(repository),eligible_(std::move(eligible)) {}
    Result discard(std::uint64_t account,std::uint64_t character,
        RecoveredInventoryDiscard::Request request,const StoredInventorySlot& expected) {
        if(request.slot>=30 || !request.quantity || request.quantity>expected.count ||
           !expected.item_id || request.item!=expected.item_id || !eligible_ || !eligible_(expected))
            throw DatabaseError("Unqualified owned discard");
        auto next=expected;
        next.count=static_cast<std::uint8_t>(expected.count-request.quantity);
        if(!next.count)next.item_id=0;
        // Native absolute41 suffices: an occupied slot keeps its metadata;
        // clearing emits item0/slot/0, which the existing consumer understands.
        const auto logical=next.count ? RecoveredInventory::encode_slot_update({next.item_id,request.slot,next.count})
                                     : RecoveredInventory::clear_slot(request.slot);
        if(!logical)throw DatabaseError("Discard projection rejected");
        auto wire=RecoveredWorldFrame::encode(*logical);
        next=repository_.commit_inventory_discard(account,character,request.slot,request.quantity,expected);
        return {std::move(next),std::move(wire)};
    }
private:
    SqliteRecoveredCharacterRepository& repository_;
    Eligible eligible_;
};
}
