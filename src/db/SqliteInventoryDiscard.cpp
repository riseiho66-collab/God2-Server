#include "db/SqliteRecoveredCharacterRepository.h"
#include "db/SqliteSupport.h"
#include <limits>

namespace god2 {
// CUSTOM-0061: one owned scalar stack decrement, under BEGIN IMMEDIATE.
// Preserve source provenance and the original slot allocation design_id.
StoredInventorySlot SqliteRecoveredCharacterRepository::commit_inventory_discard(
        std::uint64_t account,std::uint64_t character,std::uint8_t slot,
        std::uint8_t quantity,const StoredInventorySlot& expected) {
    if(slot>=30 || !quantity || !expected.item_id || !expected.count ||
       expected.count>127 || quantity>expected.count || !expected.revision ||
       expected.revision>=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max()) ||
       expected.source_sha256.size()!=64 ||
       expected.source_sha256.find_first_not_of("0123456789abcdef")!=std::string::npos)
        throw DatabaseError("Invalid discard state");
    sqlite_detail::Transaction transaction(db_);
    if(load_inventory_slot(account,character,slot)!=std::optional{expected})
        throw DatabaseError("Discard ownership/version conflict");
    sqlite_detail::Statement pending(db_,"SELECT 1 FROM battle_reservations r LEFT JOIN battle_settlements s "
        "ON s.battle_id=r.id WHERE r.character_id=? AND s.battle_id IS NULL LIMIT 1");
    pending.bind_id(1,character);
    if(pending.row())throw DatabaseError("Discard during pending battle");
    auto next=expected;
    next.count=static_cast<std::uint8_t>(expected.count-quantity);
    if(!next.count)next.item_id=0;
    ++next.revision;
    sqlite_detail::Statement update(db_,"UPDATE diagnostic_inventory_slots SET item_id=?,count=?,revision=? "
        "WHERE character_id=? AND slot=? AND revision=?");
    update.bind(1,next.item_id);update.bind(2,next.count);update.bind_id(3,next.revision);
    update.bind_id(4,character);update.bind(5,slot);update.bind_id(6,expected.revision);update.done();
    if(sqlite3_changes(db_)!=1 || load_inventory_slot(account,character,slot)!=std::optional{next})
        throw DatabaseError("Discard readback mismatch");
    transaction.commit();return next;
}
}
