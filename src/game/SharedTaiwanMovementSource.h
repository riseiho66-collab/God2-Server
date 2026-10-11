#pragma once
#include "game/SharedTaiwanMovement.h"
#include <cstddef>
#include <functional>

namespace god2 {
// Explicit source for the actual common world's native TW movement path.
// The real host supplies the same presence/visibility, native Lua rules and
// complete WorldOwner factory. No default scene, permission or5D is supplied.
class SharedTaiwanMovementSource {
public:
    using Lease=SharedWorldPresence::Lease;
    using Factory=std::function<std::shared_ptr<SharedTaiwanMovement::WorldOwner>(Session&,const Lease&)>;
    struct Binding {
        decltype(Session::RecoveredCharacterHandlers::movement) movement;
        // Actual Session cleanup, on game, before common lifecycle/DB teardown.
        // Releases only this source's exact stored controller, not registries.
        std::function<void(Session&)> release;
        // The actual hosting vault invokes this before rejecting a nested
        // operation that cannot reach movement/release. No cleanup or gameplay mutation;
        // poisons only a currently active source authority operation, on game.
        std::function<void()> invalidate_active;
        // Explicit exact-generation controller retirement. A stale Session or
        // Lease cannot remove a successor. No common registry cleanup/close.
        // Appended after the original three callbacks; old release is unchanged.
        std::function<bool(Session&,const Lease&)> retire;
    };
    // Factory runs on the serial game owner only after real initial publication
    // completes. It must not retain Session/Lease references, yield or pump
    // events. Returned actual owners and rules remain strongly game-owned.
    // Capacity comes from the actual host, not an invented native player limit.
    static Binding create(std::shared_ptr<SharedWorldPresence>,
        std::shared_ptr<cn::SharedActorVisibility>,std::shared_ptr<TaiwanMovementRules>,
        Factory,std::size_t actual_session_capacity,
        std::shared_ptr<SqliteOwnedEquipmentTransaction> movement_custody={});
};
}
