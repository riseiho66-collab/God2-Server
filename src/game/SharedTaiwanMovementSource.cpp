#include "game/SharedTaiwanMovementSource.h"
#include <map>
#include <stdexcept>
#include <thread>
#include <utility>

namespace god2 {
namespace {
using Source=SharedTaiwanMovementSource;
struct Slot {
    Source::Lease lease;
    std::weak_ptr<Session> connection;
    std::shared_ptr<SharedTaiwanMovement> controller;
};
// Identity/lifetime delegation only: every native value and authorization
// still comes from the actual WorldOwner. Caught source-level reentry poisons
// the enclosing provider call before the controller can commit a position.
struct QualifiedWorld final:SharedTaiwanMovement::WorldOwner {
    std::shared_ptr<SharedTaiwanMovement::WorldOwner> actual;
    std::function<bool(const Source::Lease&)> bound;
    QualifiedWorld(std::shared_ptr<SharedTaiwanMovement::WorldOwner> owner,
        std::function<bool(const Source::Lease&)> current):actual(std::move(owner)),bound(std::move(current)){}
    std::optional<SharedTaiwanMovement::Scene> scene(const Source::Lease& lease,
        const RecoveredPosition& before,const RecoveredMovement::Request& request) override {
        if(!bound(lease))return std::nullopt;
        auto result=actual->scene(lease,before,request);
        return bound(lease)?result:std::nullopt;
    }
    bool current(const Source::Lease& lease,const SharedTaiwanMovement::Scene& scene) override {
        return bound(lease) && actual->current(lease,scene) && bound(lease);
    }
    std::optional<SharedTaiwanMovement::Authorization> authorize(const Source::Lease& lease,
        const RecoveredPosition& before,const SharedTaiwanMovement::Scene& scene,
        const TaiwanMovementRules::Step& step) override {
        if(!bound(lease))return std::nullopt;
        auto result=actual->authorize(lease,before,scene,step);
        return bound(lease)?result:std::nullopt;
    }
    bool publish(const Source::Lease& lease,const SharedTaiwanMovement::Scene& scene,
        const SharedTaiwanMovement::Committed& committed) override {
        return bound(lease) && actual->publish(lease,scene,committed) && bound(lease);
    }
};
struct MovementOwner:std::enable_shared_from_this<MovementOwner> {
    std::shared_ptr<SharedWorldPresence> presence;
    std::shared_ptr<shared::SharedActorVisibility> visibility;
    std::shared_ptr<TaiwanMovementRules> rules;
    std::shared_ptr<SqliteOwnedEquipmentTransaction> movement_custody;
    Source::Factory factory;
    std::size_t capacity;
    const std::thread::id thread=std::this_thread::get_id();
    std::map<std::uint64_t,std::shared_ptr<Slot>> slots;
    bool operating=false,reentered=false;

    void owner() const {
        if(std::this_thread::get_id()!=thread)
            throw std::logic_error("TW movement source game owner mismatch");
    }
    void invalidate_active() {
        owner();if(operating)reentered=true;
    }
    struct Operation {
        MovementOwner& owner;
        explicit Operation(MovementOwner& state):owner(state) {
            owner.owner();
            if(owner.operating) {
                owner.reentered=true;
                throw std::logic_error("TW movement source reentry rejected");
            }
            owner.operating=true;owner.reentered=false;
        }
        ~Operation() {owner.operating=false;}
    };
    ~MovementOwner() {
        if(std::this_thread::get_id()!=thread)std::terminate();
        // Detach every slot before invoking real controller/WorldOwner
        // destructors. The host tears us down while its common DB is alive.
        operating=true;
        auto retired=std::move(slots);slots.clear();retired.clear();
        factory={};rules.reset();
    }
    bool identity(Session& session,const Source::Lease& lease) const {
        return session.id()==lease.session && session.account_id==lease.account &&
            session.character_id==lease.character;
    }
    bool ready(Session& session,const Source::Lease& lease) const {
        if(reentered || !identity(session,lease) || session.closing() ||
           !session.recovered_world_ready() || session.state()!=SessionState::InWorld ||
           !session.common_world_delivery_current(lease.account,lease.character,lease.generation) ||
           session.common_world_entry_current(lease.account,lease.character,lease.generation))return false;
        const auto actual=presence->ready_lease(lease.session,lease.account,lease.character);
        return actual && *actual==lease;
    }
    bool stored(Session& session,const std::shared_ptr<Slot>& slot) const {
        if(!slot || slot->connection.lock().get()!=&session || !identity(session,slot->lease))return false;
        const auto found=slots.find(slot->lease.session);
        return found!=slots.end() && found->second==slot;
    }
    void erase(const std::shared_ptr<Slot>& slot) {
        if(!slot)return;
        const auto found=slots.find(slot->lease.session);
        if(found!=slots.end() && found->second==slot)slots.erase(found);
        // Caller retains the detached slot while callbacks unwind. No common
        // lease or visible peer is released here; lifecycle owns that cleanup.
    }
    void close_current(Session& session,const Source::Lease& lease) noexcept {
        try {
            if(identity(session,lease) &&
               session.common_world_delivery_current(lease.account,lease.character,lease.generation) &&
               presence->current(lease))session.close();
        }catch(...) {}
    }
    std::vector<std::uint8_t> movement(Session& session,
        std::span<const RecoveredMovement::Request> requests) {
        Operation operation(*this);
        std::optional<Source::Lease> captured;
        std::shared_ptr<Slot> slot;
        try {
            const auto found=slots.find(session.id());
            if(found!=slots.end()) {slot=found->second;captured=slot->lease;}
            // Reject malformed batches before constructing any real native
            // owner. This matches the actual movement controller's contract.
            if(requests.empty() || requests.size()>RecoveredMovement::max_logical_size/7)
                throw std::runtime_error("TW movement source batch rejected");
            for(const auto& request:requests)
                if(!RecoveredNativeMovement::ordinary_request(request))
                    throw std::runtime_error("TW movement source native ring index rejected");
            if(slot) {
                if(!stored(session,slot) || !ready(session,slot->lease))
                    throw std::runtime_error("TW movement source stale stored owner");
            }else {
                captured=presence->ready_lease(session.id(),session.account_id,session.character_id);
                if(!captured || !ready(session,*captured) || slots.size()>=capacity)
                    throw std::runtime_error("TW movement source actual ready lease/capacity rejected");
                const auto connection=session.shared_from_this();
                // Copy the actual factory before external provider code. No
                // reference into mutable storage survives the provider call.
                const auto supply=factory;
                auto world=supply(session,*captured);
                if(!world || connection.get()!=&session || !ready(session,*captured))
                    throw std::runtime_error("TW movement source actual factory/lease rejected");
                slot=std::make_shared<Slot>(Slot{*captured,connection,{}});
                const std::weak_ptr<MovementOwner> weak_owner=shared_from_this();
                const std::weak_ptr<Slot> weak_slot=slot;
                auto qualified=std::make_shared<QualifiedWorld>(std::move(world),
                    [weak_owner,weak_slot](const Source::Lease& lease) {
                        const auto owner=weak_owner.lock();const auto slot=weak_slot.lock();
                        if(!owner || !slot || lease!=slot->lease)return false;
                        owner->owner();const auto session=slot->connection.lock();
                        return session && owner->operating && owner->stored(*session,slot) && owner->ready(*session,lease);
                    });
                auto controller=SharedTaiwanMovement::attach(connection,presence,*captured,rules,visibility,
                    std::move(qualified),movement_custody);
                if(!controller || !ready(session,*captured))
                    throw std::runtime_error("TW movement source actual controller rejected");
                slot->controller=std::move(controller);
                if(!slots.emplace(captured->session,slot).second)
                    throw std::runtime_error("TW movement source duplicate slot");
            }
            if(!stored(session,slot) || !ready(session,slot->lease))
                throw std::runtime_error("TW movement source pre-transaction owner rejected");
            auto response=slot->controller->handle(session,requests);
            if(!stored(session,slot) || !ready(session,slot->lease))
                throw std::runtime_error("TW movement source final owner rejected");
            return response; // Complete native envelopes; no queue/client ACK.
        }catch(...) {
            if(slot && slot->connection.lock().get()==&session && session.id()==slot->lease.session)erase(slot);
            // The controller's durable committed prefix is never rolled back.
            // Stale generations cannot close or evict a successor connection.
            if(captured && (!slot || slot->connection.lock().get()==&session))close_current(session,*captured);
            throw;
        }
    }
    void release(Session& session) {
        Operation operation(*this);
        const auto found=slots.find(session.id());
        if(found==slots.end())return;
        auto slot=found->second;
        if(!stored(session,slot))
            throw std::invalid_argument("TW movement source cleanup identity mismatch");
        // Disconnect may already clear the synchronized delivery identity.
        // Only stored actual Session/tuple and the immutable old lease matter.
        // A successor's common registry is never touched by this source.
        erase(slot);
    }
    bool retire(Session& session,const Source::Lease& lease) {
        Operation operation(*this);
        const auto found=slots.find(lease.session);
        if(session.id()!=lease.session || found==slots.end())return false;
        auto slot=found->second;
        if(slot->lease!=lease || slot->connection.lock().get()!=&session)return false;
        // Disconnect may have cleared mutable account/character/common-ready
        // fields. This explicit immutable stored Lease is the exact authority.
        erase(slot);slot.reset();
        return !reentered;
    }
};
}
SharedTaiwanMovementSource::Binding SharedTaiwanMovementSource::create(
    std::shared_ptr<SharedWorldPresence> presence,std::shared_ptr<shared::SharedActorVisibility> visibility,
    std::shared_ptr<TaiwanMovementRules> rules,Factory factory,std::size_t actual_session_capacity,
    std::shared_ptr<SqliteOwnedEquipmentTransaction> movement_custody) {
    if(!presence || !visibility || !rules || !factory || !actual_session_capacity ||
       !visibility->owns_presence(presence))
        throw std::invalid_argument("TW movement source requires exact common owners, actual rules/factory/capacity");
    auto state=std::make_shared<MovementOwner>();state->presence=std::move(presence);
    state->visibility=std::move(visibility);state->rules=std::move(rules);
    state->factory=std::move(factory);state->capacity=actual_session_capacity;
    state->movement_custody=std::move(movement_custody);
    return {
        [state](Session& session,std::span<const RecoveredMovement::Request> requests) {
            return state->movement(session,requests);
        },
        [state](Session& session) {state->release(session);},
        [state] {state->invalidate_active();},
        [state](Session& session,const Lease& lease) {return state->retire(session,lease);}
    };
}
}
