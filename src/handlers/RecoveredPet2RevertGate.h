#pragma once
#include "db/SqliteCompanionRepository.h"
#include "db/SqliteRecoveredCharacterRepository.h"
#include "protocol/RecoveredPet2Revert.h"

namespace god2 {
// Read-only admission of the current D6 route. There is deliberately no
// successful effect result: neither a trusted previous-instance history nor
// the consumption/response contract is qualified. A transport handler can
// report the exact denial without disconnecting or changing saved state.
class RecoveredPet2RevertGate {
public:
    enum class Decision {
        NotWorldReady, InBattle, InvalidOperands, PendingBattle,
        MissingItem, WrongItem, WrongItemSource, MissingPet2, EffectUnqualified
    };
    struct Context {
        std::uint64_t account,character;
        bool world_ready,in_battle;
    };
    RecoveredPet2RevertGate(SqliteRecoveredCharacterRepository& characters,
                           SqliteCompanionRepository& companions)
        :characters_(characters),companions_(companions) {}
    Decision inspect(Context context,const RecoveredPet2Revert::Request& request);
    static const char* name(Decision decision) noexcept;
private:
    SqliteRecoveredCharacterRepository& characters_;
    SqliteCompanionRepository& companions_;
};
}
