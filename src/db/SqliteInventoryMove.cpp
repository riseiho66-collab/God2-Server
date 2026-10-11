#include "db/SqliteRecoveredCharacterRepository.h"
#include "db/SqliteSupport.h"
#include "game/OwnedStackQuantity.h"
#include <algorithm>
#include <limits>

namespace god2 {
// CUSTOM-0037: owned 30-slot allocation and whole-stack swap policy. Native C2S24
// supplies slot indices only; it does not establish server allocation/merge rules.
namespace {
bool has_pending_battle(sqlite3* db,std::uint64_t character) {
    sqlite_detail::Statement pending(db,
        "SELECT 1 FROM battle_reservations r LEFT JOIN battle_settlements s "
        "ON s.battle_id=r.id WHERE r.character_id=? AND s.battle_id IS NULL LIMIT 1");
    pending.bind_id(1,character);
    return pending.row();
}
}

std::size_t SqliteRecoveredCharacterRepository::provision_owned_bag(
        std::uint64_t account,std::uint64_t character) {
    sqlite_detail::Transaction transaction(db_);
    if(!load_inventory_slot(account,character,0))
        throw DatabaseError("Bag allocation requires explicit owned town slot");
    // Only this explicit allocation operation establishes missing bag capacity.
    // All existing records, including non-town item provenance, are preserved.
    const auto before=load_saved_supply_slots(account,character);
    if(before.size()==30) { transaction.commit();return 0; }
    // Older saves can have a pending battle and only their reward slot. Let
    // login restore those rows; allocation can retry after battle settlement.
    if(has_pending_battle(db_,character)) { transaction.commit();return 0; }
    std::size_t inserted=0;
    const StoredInventorySlot empty{0,0,1,town_reward_item_source_sha256};
    for(std::uint8_t slot=1;slot<30;++slot) {
        if(load_inventory_slot(account,character,slot)) continue;
        sqlite_detail::Statement insert(db_,
            "INSERT INTO diagnostic_inventory_slots(item_id,count,revision,source_sha256,character_id,slot,design_id) "
            "VALUES(0,0,1,?,?,?,'CUSTOM-0015')");
        insert.bind(1,empty.source_sha256);insert.bind_id(2,character);insert.bind(3,slot);
        insert.done();
        if(sqlite3_changes(db_)!=1 || load_inventory_slot(account,character,slot)!=std::optional{empty})
            throw DatabaseError("Bag allocation readback mismatch");
        ++inserted;
    }
    const auto after=load_saved_supply_slots(account,character);
    if(after.size()!=30)
        throw DatabaseError("Bag allocation incomplete");
    for(const auto& [slot,snapshot]:after) {
        const auto previous=std::find_if(before.begin(),before.end(),
            [&](const auto& pair){return pair.first==slot;});
        if(snapshot!=(previous==before.end() ? empty : previous->second))
            throw DatabaseError("Bag allocation changed slot contents");
    }
    transaction.commit();
    return inserted;
}

InventoryMoveCommit SqliteRecoveredCharacterRepository::commit_inventory_move(
        std::uint64_t account,std::uint64_t character,std::uint8_t source,std::uint8_t destination,
        const StoredInventorySlot& expected_source,const StoredInventorySlot& expected_destination) {
    if(source>=30 || destination>=30 || source==destination)
        throw DatabaseError("Invalid bag transfer slots");
    sqlite_detail::Transaction transaction(db_);
    if(load_inventory_slot(account,character,source)!=std::optional{expected_source} ||
       load_inventory_slot(account,character,destination)!=std::optional{expected_destination})
        throw DatabaseError("Bag transfer version conflict");
    if(has_pending_battle(db_,character)) throw DatabaseError("Bag change during pending battle");
    const auto limit=static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max());
    if(!expected_source.item_id || !expected_source.count ||
       !OwnedStackQuantity::from(expected_source.count) || !OwnedStackQuantity::from(expected_destination.count) ||
       (expected_destination.item_id==0)!=(expected_destination.count==0) ||
       !expected_source.revision || !expected_destination.revision ||
       expected_source.revision>=limit || expected_destination.revision>=limit)
        throw DatabaseError("Invalid bag transfer state");
    // CUSTOM-0089 is a write-domain ceiling, never clipping a saved quantity.
    //Read/projection compatibility stays native signedBYTE127; old over-limit
    //rows remain intact and require their own separately authorized transition.
    InventoryMoveCommit result{expected_destination,expected_source};
    result.source.revision=expected_source.revision+1;
    result.destination.revision=expected_destination.revision+1;
    const auto write=[&](std::uint8_t slot,const StoredInventorySlot& expected,const StoredInventorySlot& next) {
        sqlite_detail::Statement update(db_,
            "UPDATE diagnostic_inventory_slots SET item_id=?,count=?,revision=?,source_sha256=? "
            "WHERE character_id=? AND slot=? AND revision=?");
        update.bind(1,next.item_id);update.bind(2,next.count);update.bind_id(3,next.revision);
        update.bind(4,next.source_sha256);update.bind_id(5,character);update.bind(6,slot);
        update.bind_id(7,expected.revision);update.done();
        if(sqlite3_changes(db_)!=1) throw DatabaseError("Bag transfer write rejected");
    };
    write(source,expected_source,result.source);
    write(destination,expected_destination,result.destination);
    if(load_inventory_slot(account,character,source)!=std::optional{result.source} ||
       load_inventory_slot(account,character,destination)!=std::optional{result.destination})
        throw DatabaseError("Bag transfer readback mismatch");
    transaction.commit();
    return result;
}
}
