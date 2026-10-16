#pragma once
#include "db/SqliteWorldDisplayRepository.h"
#include "game/SharedTaiwanWorldEntered.h"

namespace god2 {
// CUSTOM-0133 actual selected initial72 source composition, backed by an owning
// SceneReadset. Genuine selection/order/other records remain authoritative;
// this is neither full scene coverage nor permission to invent placements.
class OwnedTaiwanInitialNpcDisplaySource final {
    struct Owner;
    struct State;
public:
    static SharedTaiwanWorldEntered::Source wrap(
        std::shared_ptr<SharedWorldPresence>,SqliteWorldDisplayRepository&,
        const NativeNpcDisplayCatalog&,const NativeEnemyDisplayCatalog&,
        SharedTaiwanWorldEntered::Source genuine);
private:
    static std::optional<SharedTaiwanWorldEntered::Native> supply(
        const std::shared_ptr<Owner>&,Session&,const SharedTaiwanWorldEntered::Scope&);
};
}
