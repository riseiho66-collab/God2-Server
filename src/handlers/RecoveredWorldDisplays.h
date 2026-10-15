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
    const SqliteWorldDisplayRepository::SceneReadset& readset) {
    std::vector<std::vector<std::uint8_t>> batches;
    const auto& rows=readset.rows();
    const auto& levels=readset.levels();
    for(const auto& row:rows) {
        // The private readset already qualified full records and all referenced
        // catalogs in one snapshot. This composer never calls SQL or callbacks.
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
// Preserve the existing Application caller, now with one joint observation.
inline std::vector<std::vector<std::uint8_t>> recovered_world_display_batches(
    const SqliteWorldDisplayRepository& repository,const NativeNpcDisplayCatalog& npcs,
    const NativeEnemyDisplayCatalog& enemies,std::uint16_t area,std::uint16_t scene,bool isolated_test=false) {
    const auto readset=repository.observe_scene(npcs,enemies,area,scene,isolated_test);
    return recovered_world_display_batches(readset);
}
}
