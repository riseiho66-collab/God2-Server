#pragma once

#include "db/NativeEnemyDisplayCatalog.h"
#include "protocol/RecoveredBattleBootstrap.h"

#include <stdexcept>

namespace god2 {

// Current-client S2C 1C normal enemy display selector. This resolves a display
// name only; it does not identify a server monster template or combat stats.
inline std::optional<NativeEnemyDisplayRecord> resolve_normal_enemy_display(
    const NativeEnemyDisplayCatalog& catalog,const RecoveredBattleIdentity::Record& packet) {
    if(packet.position()<14 || packet.variant()!=0x0400 ||
       !packet.enemy_area() || !packet.enemy_scene())
        throw std::invalid_argument("Not a qualified normal enemy display packet");
    return catalog.lookup(NativeEnemyDisplayCatalog::current_dataset_id,
                          *packet.enemy_area(),*packet.enemy_scene(),packet.ordinal());
}

}
