#pragma once
#include "shared/world/SharedMovementPublication.h"
#include "scripting/TaiwanMovementRules.h"

namespace god2 {
class SqliteOwnedEquipmentTransaction;
// TW native2E ->actual native scene/Lua geometry/permission ->single common
// position CAS ->real actor/cache publication ->version-native peers5E ->full5D.
// Separate opt-in source; never replaces frozen TW CUSTOM movement implicitly.
class SharedTaiwanMovement {
public:
    using Lease=SharedWorldPresence::Lease;
    struct Scene {
        std::uint16_t area,scene;
        std::uint64_t revision;
        std::uint8_t previous_direction,native_cell;
    };
    struct Authorization {std::vector<std::uint8_t> full_native_ack;};
    struct Committed {RecoveredPosition before,after;TaiwanMovementRules::Step step;};
    class WorldOwner {
    public:
        virtual ~WorldOwner()=default;
        // Read destination raw cell from the actual initialized native map/view,
        // including its real resource/frame/object/window lifecycle. No generic
        virtual std::optional<Scene> scene(const Lease&,const RecoveredPosition&,
            const RecoveredMovement::Request&)=0;
        virtual bool current(const Lease&,const Scene&)=0;
        // Timing, pending/reset/index, collision/corner/actor state, transfer and
        // battle authority plus complete original5D byte supplier. No default permit.
        virtual std::optional<Authorization> authorize(const Lease&,const RecoveredPosition&,
            const Scene&,const TaiwanMovementRules::Step&)=0;
        virtual bool publish(const Lease&,const Scene&,const Committed&)=0;
    };
    static std::shared_ptr<SharedTaiwanMovement> attach(const std::shared_ptr<Session>&,
        std::shared_ptr<SharedWorldPresence>,const Lease&,TaiwanMovementRules&,
        std::shared_ptr<shared::SharedActorVisibility>,WorldOwner&);
    // Explicit actual-source opt-in. Retain both real game-owned suppliers and
    // require the exact active common delivery generation, with reentry guards.
    static std::shared_ptr<SharedTaiwanMovement> attach(const std::shared_ptr<Session>&,
        std::shared_ptr<SharedWorldPresence>,const Lease&,std::shared_ptr<TaiwanMovementRules>,
        std::shared_ptr<shared::SharedActorVisibility>,std::shared_ptr<WorldOwner>,
        std::shared_ptr<SqliteOwnedEquipmentTransaction> movement_custody={});
    ~SharedTaiwanMovement();
    // Same signature as actual Session::RecoveredCharacterHandlers.movement.
    // A real world-record dispatcher can invoke it for2E runs as well. It owns
    // mixed/control records; this controller never silently discards them.
    // Returns full encrypted TW5D envelopes; Session supplies the response queue.
    std::vector<std::uint8_t> handle(Session&,std::span<const RecoveredMovement::Request>);
private:
    SharedTaiwanMovement(const std::shared_ptr<Session>&,std::shared_ptr<SharedWorldPresence>,
        const Lease&,TaiwanMovementRules&,std::shared_ptr<shared::SharedActorVisibility>,WorldOwner&);
    SharedTaiwanMovement(const std::shared_ptr<Session>&,std::shared_ptr<SharedWorldPresence>,
        const Lease&,std::shared_ptr<TaiwanMovementRules>,std::shared_ptr<shared::SharedActorVisibility>,
        std::shared_ptr<WorldOwner>,std::shared_ptr<SqliteOwnedEquipmentTransaction>);
    void owner() const;
    bool current(Session&) const;
    std::optional<std::vector<std::uint8_t>> move(Session&,const RecoveredMovement::Request&);
    std::optional<std::vector<std::uint8_t>> move_owned(Session&,const RecoveredMovement::Request&);
    std::vector<std::uint8_t> handle_owned(Session&,std::span<const RecoveredMovement::Request>);
    bool scene_current_owned(Session&,const Scene&);
    void reject(Session&);
    std::thread::id thread_=std::this_thread::get_id();
    std::weak_ptr<Session> connection_;
    std::shared_ptr<SharedWorldPresence> presence_;
    Lease lease_;
    std::shared_ptr<TaiwanMovementRules> rules_owner_;
    TaiwanMovementRules& rules_;
    std::shared_ptr<shared::SharedActorVisibility> visibility_;
    shared::SharedMovementPublication publication_;
    std::shared_ptr<WorldOwner> world_owner_;
    WorldOwner& world_;
    // CUSTOM-0095 explicit actual joint position/custody retention. The real
    // borrowed database writers must outlive this game-owned controller/drain.
    std::shared_ptr<SqliteOwnedEquipmentTransaction> movement_custody_;
    bool owned_handling_=false,owned_reentered_=false;
};
}
