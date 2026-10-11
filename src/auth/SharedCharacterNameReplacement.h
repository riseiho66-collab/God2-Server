#pragma once
#include "auth/SharedWorldAdmission.h"
#include "auth/SharedCharacterRemovalPresence.h"
#include "db/SqliteRecoveredCharacterRepository.h"

namespace god2 {
// Shared saved-name/offer coordination, not native name rules, a D3 handler,
// reply provider or durable replay receipt. Run on the serial game owner.
// Reuse the actual common prepared/active occupancy observer; its original
// removal name does not authorize deletion or eviction here. Host must supply
// the same repository and actual presence/world/movement registries.
class SharedCharacterNameReplacement {
public:
    using Phase=SqliteRecoveredCharacterRepository::NameReplacementPhase;
    using Current=SqliteRecoveredCharacterRepository::CurrentNameReplacement;
    static std::optional<RecoveredCharacter> commit(SqliteRecoveredCharacterRepository&,
        SharedWorldAdmission&,const SharedCharacterRemovalPresence&,std::uint64_t account,
        std::vector<RecoveredCharacter> expected,std::uint64_t character,
        SqliteRecoveredCharacterRepository::OwnedNameCandidate,Current actual_operation);
};
}
