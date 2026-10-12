#pragma once
#include "db/SqliteOwnedEquipmentTransaction.h"
#include "game/SharedTaiwanWorldRecordSource.h"

namespace god2 {
class RecoveredMovementService;
// CUSTOM-0093: concrete whole-instance bag move/swap, never a grant or merge.
// Native41 can represent this subset only when both retained18B tails agree.
// Construction is game-affine; borrowed repositories outlive Application drain.
class SharedTaiwanOwnedBagMoveSource final {
public:
    static SharedTaiwanWorldRecordSource::InventoryMoveBinding create(
        std::shared_ptr<SqliteOwnedEquipmentTransaction>,AccountRepository&,
        RecoveredCharacterRepository&,std::shared_ptr<SharedWorldPresence>);
    // Separate CUSTOM-0094 opt-in; requires each changed item's genuine full25
    // material. Retention policy is not native opaque/helper qualification.
    static SharedTaiwanWorldRecordSource::InventoryMoveBinding create_with_item_material(
        std::shared_ptr<SqliteOwnedEquipmentTransaction>,AccountRepository&,
        RecoveredCharacterRepository&,std::shared_ptr<SharedWorldPresence>);
    // CUSTOM-0094 full25 only: actual legacy world-records callback and
    // private normal-entry receipt, never a fabricated common ready lease.
    // Requires both genuine complete saved banks at the exact live durable
    // pose. No initialization, grant, stale-witness rebase or scalar promotion.
    // Actual movement/common sources must outlive this game-owned binding.
    static SharedTaiwanWorldRecordSource::InventoryMoveBinding create_for_normal_entry_with_item_material(
        std::shared_ptr<SqliteOwnedEquipmentTransaction>,AccountRepository&,
        RecoveredCharacterRepository&,RecoveredMovementService&);
};
}
