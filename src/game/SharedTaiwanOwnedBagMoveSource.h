#pragma once
#include "db/SqliteOwnedEquipmentTransaction.h"
#include "game/SharedTaiwanWorldRecordSource.h"

namespace god2 {
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
};
}
