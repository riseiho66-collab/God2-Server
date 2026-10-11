#pragma once
#include "db/DbTypes.h"
#include "db/SqliteWorldDisplayRepository.h"
#include "db/NativeNpcDisplayCatalog.h"
#include "db/NativeEnemyDisplayCatalog.h"
#include "protocol/RecoveredNpcRecord.h"
#include "protocol/RecoveredMonsterRecord.h"
#include "protocol/RecoveredMonsterLevel.h"
#include "protocol/RecoveredWorldFrame.h"
namespace god2 {
// Full records remain opaque; existing native render resource selection applies.
// NPC catalog selectors, monster namespace and scene identity are separate keys.
inline std::vector<std::vector<std::uint8_t>> recovered_world_display_batches(
    const SqliteWorldDisplayRepository& repository,const NativeNpcDisplayCatalog& npcs,
    const NativeEnemyDisplayCatalog& enemies,std::uint16_t area,std::uint16_t scene,bool isolated_test=false) {
    std::vector<std::vector<std::uint8_t>> batches;
    const auto rows=repository.load(area,scene,isolated_test);
    const auto levels=repository.load_levels(area,scene,isolated_test);
    std::vector<std::uint16_t> selectors;
    for(const auto& row:rows) if(const auto npc=RecoveredNpcRecord::parse(row.logical)) {
        selectors.push_back(npc->primarySelector());
        if(npc->secondarySelector())selectors.push_back(npc->secondarySelector());
    }
    if(!npcs.contains_all(selectors))throw DatabaseError("World NPC selectors lack qualified current catalog");
    for(const auto& row:rows) {
        if(const auto npc=RecoveredNpcRecord::parse(row.logical)) {
            // Membership was qualified in one full catalog read above.
            (void)npc;
        } else if(const auto monster=RecoveredMonsterRecord::parse(row.logical)) {
            if(!enemies.lookup(NativeEnemyDisplayCatalog::current_dataset_id,
                monster->catalogArea(),monster->catalogScene(),monster->catalogOrdinal()))
                throw DatabaseError("World monster namespace lacks qualified current catalog");
        } else throw DatabaseError("Invalid world display record");
        if(batches.empty() || batches.back().size()+21>RecoveredWorldFrame::max_logical_size)batches.emplace_back();
        batches.back().insert(batches.back().end(),row.logical.begin(),row.logical.end());
        if(const auto monster=RecoveredMonsterRecord::parse(row.logical)) {
            const auto level=std::find_if(levels.begin(),levels.end(),[&](const auto& value){return value.identity==monster->identity();});
            if(level!=levels.end()) {
                const auto logical=RecoveredMonsterLevel::encode({level->identity,level->level});
                if(batches.back().size()+logical.size()>RecoveredWorldFrame::max_logical_size)batches.emplace_back();
                batches.back().insert(batches.back().end(),logical.begin(),logical.end());
            }
        }
    }
    return batches;
}
}
