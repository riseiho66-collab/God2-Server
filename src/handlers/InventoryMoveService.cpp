#include "handlers/InventoryMoveService.h"
#include "db/DbTypes.h"
#include "game/OwnedStackQuantity.h"
#include "protocol/RecoveredWorldFrame.h"
#include <limits>

namespace god2 {
InventoryMoveService::Result InventoryMoveService::move(std::uint64_t account,std::uint64_t character,
        const Request& request,const StoredInventorySlot& expected_source,const StoredInventorySlot& expected_destination) {
    const auto limit=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max());
    const auto valid=[&](const StoredInventorySlot& slot) {
        return OwnedStackQuantity::from(slot.count).has_value() && (slot.item_id==0)==(slot.count==0) &&
            slot.revision && slot.revision<limit && slot.source_sha256.size()==64 &&
            slot.source_sha256.find_first_not_of("0123456789abcdef")==std::string::npos &&
            (!slot.item_id || (eligible_ && eligible_(slot)));
    };
    if(request.source_slot>=30 || request.destination_slot>=30 || request.source_slot==request.destination_slot ||
       !expected_source.count || !valid(expected_source) || !valid(expected_destination) || !reply_)
        throw DatabaseError("Unqualified bag move");
    InventoryMoveCommit projected{expected_destination,expected_source};
    projected.source.revision=expected_source.revision+1;
    projected.destination.revision=expected_destination.revision+1;
    auto wire=reply_(request,projected);
    const auto logical=RecoveredWorldFrame::decode(wire);
    if(!logical || logical->empty()) throw DatabaseError("Invalid bag move projection");
    // No resources or counts are spent/merged. CAS validates both trusted
    // baselines again and rejects pending battles inside BEGIN IMMEDIATE.
    auto saved=repository_.commit_inventory_move(account,character,request.source_slot,request.destination_slot,
        expected_source,expected_destination);
    return {std::move(saved),std::move(wire)};
}
}
