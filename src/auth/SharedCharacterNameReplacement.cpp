#include "auth/SharedCharacterNameReplacement.h"
#include <stdexcept>
#include <utility>

namespace god2 {
std::optional<RecoveredCharacter> SharedCharacterNameReplacement::commit(
    SqliteRecoveredCharacterRepository& characters,SharedWorldAdmission& admission,
    const SharedCharacterRemovalPresence& presence,std::uint64_t account,
    std::vector<RecoveredCharacter> expected,std::uint64_t character,
    SqliteRecoveredCharacterRepository::OwnedNameCandidate proposed,Current operation) {
    if(!account || !character || !operation || !presence.owns_repository(characters))return std::nullopt;
    // common character must become stale even though its ID remains unchanged.
    auto invalidation=admission.prepare_character_offer_invalidation(account,character);
    if(!invalidation)return std::nullopt;
    const auto current=[&](Phase phase) {
        return admission.character_offer_invalidation_current(*invalidation) &&
            presence.unreserved(account,character) && operation(phase) &&
            presence.unreserved(account,character) &&
            admission.character_offer_invalidation_current(*invalidation);
    };
    auto updated=characters.replace_owned_name_snapshot(account,std::move(expected),character,
        std::move(proposed),current);
    if(!updated)return std::nullopt;
    // No callback/allocation/game yield after SQL COMMIT and before apply.
    // This invalidates old native records; it does not fabricate replacement07
    // or update a world-owned actor. A qualified fresh source must reselect.
    if(!admission.apply_character_offer_invalidation(*invalidation))
        throw std::logic_error("Committed character name lost its prepared offer invalidation");
    return updated;
}
}
