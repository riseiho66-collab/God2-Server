#pragma once
#include "cn/net/SharedCredentialConnection.h"
#include "cn/scripting/CnMovementRules.h"
#include "game/SharedWorldPresence.h"
#include "cn/world/SharedMovementPublication.h"

namespace god2::cn {
// Ordinary adjacent2E -> native Lua/geometry -> actual world authority ->
// existing shared-position CAS -> actual world publication -> complete native5D.
// Scene assets, speed/sequence/eligibility and reply suppliers must be real;
// no default permit, guessed ring reset/echo or TW CUSTOM navigation fallback.
class SharedMovement:public std::enable_shared_from_this<SharedMovement> {
public:
    using Connection=SharedCredentialConnection;
    using Lease=SharedWorldPresence::Lease;
    struct Scene {
        std::uint16_t area,scene;
        std::uint64_t revision; // Real scene-owner revision, not DB position revision.
        std::uint8_t mode,previous_direction;
        god2cn::CnMapPassability cells; // Complete native asset/lifecycle snapshot.
    };
    struct Committed {
        RecoveredPosition before,after;
        god2cn::CnMapPreparedStep native_step;
    };
    struct Authorization {
        god2cn::Bytes native_ack; // Complete supplied5D; no index echo/default.
        // Observer bindings come from the actual common visibility registry;
        // the permission callback cannot invent templates or omit queued peers.
    };
    class WorldOwner {
    public:
        virtual ~WorldOwner()=default;
        // Qualified scene assets/direction from this lease's actual actor.
        // Missing data is nullopt, never empty cells or guessed geometry.
        virtual std::optional<Scene> scene(const Lease&,const RecoveredPosition&)=0;
        virtual bool current(const Lease&,const Scene&)=0;
        // Real timing, pending sequence/reset, battle/transfer and movement
        // permission. Return the fully supplied native5D only when authorized;
        // its opaque byte is not automatically a request-index echo.
        virtual std::optional<Authorization> authorize(const Lease&,const RecoveredPosition&,
            const Scene&,const god2cn::CnMapPreparedStep&)=0;
        // Apply the committed actor/direction, native window lifecycle and
        // actual visibility/template state using the single world owner. The
        // concrete prepared publication below performs recipient-specific sends.
        virtual bool publish(const Lease&,const Scene&,const Committed&)=0;
    };
    static std::shared_ptr<SharedMovement> attach(const std::shared_ptr<Connection>&,
        std::shared_ptr<SharedWorldPresence>,const Lease&,god2cn::CnMovementRules&,
        std::shared_ptr<SharedActorVisibility>,WorldOwner&);
    // Required later dispatcher forwards a complete homogeneous2E run. Other
    // opcodes/mixed aggregates remain with that dispatcher, not discarded here.
    Connection::Ingress ingress();
private:
    SharedMovement(const std::shared_ptr<Connection>&,std::shared_ptr<SharedWorldPresence>,
        const Lease&,god2cn::CnMovementRules&,std::shared_ptr<SharedActorVisibility>,WorldOwner&);
    void owner() const;
    bool current() const;
    bool move(std::span<const std::uint8_t>);
    void receive(god2cn::Bytes,Connection::Transport::Completion);
    std::thread::id thread_=std::this_thread::get_id();
    std::weak_ptr<Connection> connection_;
    std::shared_ptr<SharedWorldPresence> presence_;
    Lease lease_;
    god2cn::CnMovementRules& rules_;
    WorldOwner& world_;
    std::shared_ptr<SharedActorVisibility> visibility_;
    SharedMovementPublication publication_;
};
}
