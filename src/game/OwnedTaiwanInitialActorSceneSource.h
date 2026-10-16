#pragma once
#include "game/OwnedTaiwanPkReturnSceneSource.h"
#include "game/SharedTaiwanWorldEntered.h"

namespace god2 {
// CUSTOM-0133 initial-only full actor adapter. The genuine supplier still owns
// the exact ordered selection, other scene records, install and cleanup.
// No default audience, early clear, outward actor or native ACK is authored.
class OwnedTaiwanInitialActorSceneSource final {
    struct Owner;
    struct State;
public:
    static SharedTaiwanWorldEntered::Source wrap(
        std::shared_ptr<SharedWorldPresence>,std::shared_ptr<TaiwanCustomFullActorProfile>,
        OwnedTaiwanPkReturnSceneSource::MaterialSources,SharedTaiwanWorldEntered::Source genuine);
private:
    static std::optional<SharedTaiwanWorldEntered::Native> supply(
        const std::shared_ptr<Owner>&,Session&,const SharedTaiwanWorldEntered::Scope&);
    static std::optional<TaiwanActorStatusPublication::ActorUnit> mint(
        const TaiwanCustomFullActorProfile::Profile&);
};
}
