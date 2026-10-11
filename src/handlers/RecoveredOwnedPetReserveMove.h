#pragma once
#include "db/SqliteCompanionRepository.h"
#include "protocol/RecoveredInventoryMoveRequest.h"
#include "protocol/RecoveredWorldFrame.h"
#include <algorithm>

namespace god2 {
// Current native 49EB44 -> 49EE6D -> 49EF1C -> 496610 sends24 for
// reserve42<->43. Caller must admit authenticated world-ready, projected owned
// companions with a current scene and no in-battle/pending-scene state.
// CUSTOM-0039 supplies whole-instance swap policy, never native growth/stats.
struct RecoveredOwnedPetReserveMove {
    static bool handles(const RecoveredInventoryMoveRequest::Request& request) noexcept {
        return (request.source_slot==42 || request.source_slot==43) &&
               (request.destination_slot==42 || request.destination_slot==43);
    }
    static std::optional<std::vector<std::uint8_t>> move(SqliteCompanionRepository& repository,
        std::uint64_t account,std::uint64_t character,const RecoveredInventoryMoveRequest::Request& request) {
        if(!handles(request))return std::nullopt;
        const auto saved=repository.load_pet2_slots(account,character);
        const auto at=[&](std::uint8_t slot) {
            return std::find_if(saved.begin(),saved.end(),[&](const auto& row){return row.slot==slot;});
        };
        const auto source=at(request.source_slot),destination=at(request.destination_slot);
        if(source==saved.end() || destination==saved.end())return std::nullopt;
        if(request.source_slot==request.destination_slot || !source->occupied())return std::vector<std::uint8_t>{};
        std::vector<std::uint8_t> wire;
        repository.move_pet_reserves(account,character,*source,*destination,[&](const auto& next) {
            std::vector<std::uint8_t> logical;
            // Clear both OLD cache families before installing either complete
            // instance. E3 and FB have independent cache sizes and routing bytes.
            RecoveredPet2Lifecycle::clear(logical,next.source.slot);
            RecoveredPet2Lifecycle::clear(logical,next.destination.slot);
            const auto append=[&](const StoredPet2Slot& row) {
                if(row.pet1)RecoveredPet1Lifecycle::append(logical,*row.pet1,row.slot);
                else if(row.pet)RecoveredPet2Lifecycle::append(logical,*row.pet,row.slot);
            };
            append(next.source);append(next.destination);
            wire=RecoveredWorldFrame::encode(logical);
        });
        return wire;
    }
};
}
