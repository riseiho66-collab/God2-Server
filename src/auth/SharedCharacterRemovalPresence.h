#pragma once
#include "game/SharedWorldPresence.h"
#include "game/World.h"
#include "handlers/RecoveredMovementService.h"
#include <functional>
#include <memory>
#include <variant>

namespace god2 {
// Common saved-state integrity policy, NOT native deletion permission or a
// rule/reply issuer. Observes actual owner registries on the serial game thread.
// and actual legacy World/movement instances, and keep referenced objects alive.
class SharedCharacterRemovalPresence {
public:
    struct RecoveredMovementDisabled {};
    // No default/null source: explicit disabled host configuration or the real
    // existing movement object. Rebind before activating a previously disabled
    // service. The tagged configuration is not inferred from an empty registry.
    using LegacyMovement=std::variant<std::reference_wrapper<const RecoveredMovementService>,
                                      RecoveredMovementDisabled>;
    SharedCharacterRemovalPresence(const RecoveredCharacterRepository&,
        std::shared_ptr<const SharedWorldPresence>,const World&,LegacyMovement);
    bool owns_repository(const RecoveredCharacterRepository&) const;
    bool owns_presence_registry(const SharedWorldPresence&) const;
    // Includes unready preparation/transfer reservations. Does not read SQL,
    // consult a now-deleted root row, evict an actor or clear stale leases.
    // Absence here is only an occupancy condition; real rules stay mandatory.
    bool unreserved(std::uint64_t account,std::uint64_t character) const;
private:
    void owner() const;
    std::thread::id thread_=std::this_thread::get_id();
    const RecoveredCharacterRepository& characters_;
    std::shared_ptr<const SharedWorldPresence> presence_;
    const World& world_;
    LegacyMovement movement_;
};
}
