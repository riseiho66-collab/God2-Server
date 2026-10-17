#pragma once
#include "game/SharedWorldPresence.h"
#include "net/Session.h"
#include "protocol/RecoveredRemoteActor.h"
#include "shared/world/SharedActorVisibility.h"
#include <variant>

namespace god2::shared {
// Concrete Taiwan-native publication over common ready leases and real transports.
// The authoritative WorldOwner selects private visible-incarnation bindings.
// Their actual6F/5E/73 lifecycle lives in SharedActorVisibility. Same scene alone
// never creates visibility, spawns or templates.
// Old TW CUSTOM0027 visibility is neither modified nor enrolled implicitly.
class SharedMovementPublication {
    struct Identity {};
public:
    using Lease=SharedWorldPresence::Lease;
    using Taiwan=SharedActorVisibility::TaiwanMovement;
    using Recipient=SharedActorVisibility::MovementRecipient;
    class Prepared {
    public:
        Prepared(Prepared&&)=default;
        Prepared& operator=(Prepared&&)=default;
        Prepared(const Prepared&)=delete;
        Prepared& operator=(const Prepared&)=delete;
    private:
        friend class SharedMovementPublication;
        struct Delivery {SharedActorVisibility::Binding binding;Recipient recipient;std::vector<std::uint8_t> bytes;};
        Prepared(std::shared_ptr<const Identity>,Lease,RecoveredPosition,std::uint16_t,
            std::uint16_t,std::vector<SharedActorVisibility::Binding>,std::vector<Delivery>);
        std::shared_ptr<const Identity> identity_;
        Lease source_;
        RecoveredPosition before_;
        std::uint16_t x_,y_;
        std::vector<SharedActorVisibility::Binding> bindings_;
        std::vector<Delivery> deliveries_;
        bool consumed_=false;
    };
    SharedMovementPublication(std::shared_ptr<SharedWorldPresence>,std::shared_ptr<SharedActorVisibility>);
    // All format/binding checks and allocations precede the source position CAS.
    // Uses every current registered observer of the source; an empty set is
    // actual registry absence, never an authority callback's omitted peer list.
    std::optional<Prepared> prepare(const Lease&,const RecoveredPosition& before,
        std::uint16_t x,std::uint16_t y) const;
    bool current(const Prepared&) const;
    // One use, after actual actor/cache publication and durable position commit.
    // Failure after any enqueue retains the commit; caller closes/reloads owner.
    // True means send API submission; neither asynchronous queue acceptance
    // nor a native client receipt/rendered acceptance is observed here.
    bool deliver(Prepared&,const RecoveredPosition& committed_after);
private:
    void owner() const;
    bool bound(const Recipient&,const RecoveredPosition& source_position) const;
    std::thread::id thread_=std::this_thread::get_id();
    std::shared_ptr<const Identity> identity_=std::make_shared<const Identity>();
    std::shared_ptr<SharedWorldPresence> presence_;
    std::shared_ptr<SharedActorVisibility> visibility_;
};
}
