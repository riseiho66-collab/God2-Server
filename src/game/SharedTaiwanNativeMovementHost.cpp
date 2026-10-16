#include "game/SharedTaiwanNativeMovementHost.h"
#include <exception>
#include <map>
#include <stdexcept>
#include <thread>
#include <utility>

namespace god2 {
struct SharedTaiwanNativeMovementHost::State:std::enable_shared_from_this<State> {
    enum class Kind {Idle,Install,Replace,Remove,Movement};
    enum class Phase {Preparing,Installed};
    struct Slot {
        const Lease lease;
        const std::weak_ptr<Session> connection;
        const std::uint64_t resource_generation,scene_generation;
        const std::optional<std::uint64_t> owned_battle_generation;
        Phase phase=Phase::Preparing;
        bool active=true,controller_bound=false;
        Slot(const std::shared_ptr<Session>& session,const Lease& actual,const Input& input)
            :lease(actual),connection(session),resource_generation(input.actual_resource_generation),
             scene_generation(input.actual_initial_scene_generation),
             owned_battle_generation(input.owned_ordinary?std::optional<std::uint64_t>(session->battle_generation()):std::nullopt) {}
    };
    const std::thread::id thread=std::this_thread::get_id();
    const std::shared_ptr<SharedWorldPresence> presence;
    const std::shared_ptr<cn::SharedActorVisibility> visibility;
    const std::shared_ptr<TaiwanMovementRules> rules;
    const std::size_t capacity;
    const InputSource input_source;
    const std::shared_ptr<SqliteOwnedEquipmentTransaction> movement_custody;
    std::shared_ptr<TaiwanNativeSceneResourceOwner> resources;
    SharedTaiwanMovementSource::Binding actual;
    std::map<std::uint64_t,std::shared_ptr<Slot>> slots;
    struct BattleRefresh {std::uint64_t old_scene_generation,battle_generation;};
    std::optional<BattleRefresh> battle_refresh;
    std::shared_ptr<Slot> active_slot;
    Session* active_session=nullptr; // Borrowed only for the synchronous operation.
    std::optional<Lease> active_lease;
    Kind operation=Kind::Idle;
    bool closed=false,reentered=false;
    State(std::shared_ptr<SharedWorldPresence> common,std::shared_ptr<cn::SharedActorVisibility> peers,
        std::shared_ptr<TaiwanMovementRules> native,InputSource source,std::size_t limit,
        std::shared_ptr<SqliteOwnedEquipmentTransaction> custody={})
        :presence(std::move(common)),visibility(std::move(peers)),rules(std::move(native)),
         capacity(limit),input_source(std::move(source)),movement_custody(std::move(custody)) {}
    ~State() {if(thread!=std::this_thread::get_id())std::terminate();}
    void owner() const {
        if(thread!=std::this_thread::get_id())throw std::logic_error("TW native movement host game owner mismatch");
    }
    void detach(const std::shared_ptr<Slot>& slot) {
        slot->active=false;
        const auto found=slots.find(slot->lease.session);
        if(found!=slots.end() && found->second==slot)slots.erase(found);
    }
    void poison() {
        owner();
        if(operation==Kind::Idle)return;
        reentered=true;
        if(active_slot)detach(active_slot);
        const auto invalidate=actual.invalidate_active;const auto retained=resources;
        if(invalidate)invalidate();
        if(retained)retained->invalidate_active();
    }
    struct Operation {
        State& state;
        Operation(State& actual,Kind kind):state(actual) {
            state.owner();
            if(state.operation!=Kind::Idle) {state.poison();throw std::logic_error("TW native movement host reentry rejected");}
            if(state.closed)throw std::logic_error("TW native movement host closed");
            state.operation=kind;state.reentered=false;
        }
        ~Operation() {
            state.battle_refresh.reset();
            state.active_slot.reset();state.active_session=nullptr;state.active_lease.reset();state.operation=Kind::Idle;
        }
    };
    bool ready(Session& session,const Lease& lease) const {
        if(closed || reentered || session.id()!=lease.session || session.account_id!=lease.account ||
           session.character_id!=lease.character || session.closing() || session.state()!=SessionState::InWorld ||
           !session.recovered_world_ready() ||
           !session.common_world_delivery_current(lease.account,lease.character,lease.generation) ||
           session.common_world_entry_current(lease.account,lease.character,lease.generation))return false;
        const auto current=presence->ready_lease(lease.session,lease.account,lease.character);
        return current && *current==lease;
    }
    bool phase_current(Session& session,const std::shared_ptr<Slot>& slot) const noexcept {
        return (!slot->owned_battle_generation || *slot->owned_battle_generation==session.battle_generation()) &&
            (!battle_refresh || battle_refresh->battle_generation==session.battle_generation());
    }
    bool stored(Session& session,const std::shared_ptr<Slot>& slot) const {
        const auto found=slots.find(slot->lease.session);
        return slot->active && slot->connection.lock().get()==&session && session.id()==slot->lease.session &&
            found!=slots.end() && found->second==slot;
    }
    bool qualification(const std::shared_ptr<Slot>& slot,SharedTaiwanNativeMovementScene::Check check,
        const SharedTaiwanNativeMovementScene::Scope& scope,const SharedTaiwanNativeMovementScene::Resources& images) const {
        const auto session=slot->connection.lock();
        if(!slot->active || !session || !phase_current(*session,slot) || !ready(*session,slot->lease) || scope.lease!=slot->lease ||
           scope.position.area!=slot->lease.position.area || scope.position.scene!=slot->lease.position.scene ||
           images.actual_resource_generation!=slot->resource_generation ||
           images.actual_initial_scene_generation!=slot->scene_generation)return false;
        if(slot->phase==Phase::Preparing)
            return check==SharedTaiwanNativeMovementScene::Check::Adopt && operation!=Kind::Idle &&
                active_slot==slot && active_session==session.get() && active_lease && *active_lease==slot->lease;
        return slot->phase==Phase::Installed && stored(*session,slot) && operation==Kind::Movement &&
            active_slot==slot && active_session==session.get() && active_lease && *active_lease==slot->lease;
    }
    Input qualified_input(const Input& input,const std::shared_ptr<Slot>& slot) {
        Input qualified=input;
        const auto weak=weak_from_this();const std::weak_ptr<Slot> weak_slot=slot;const auto observe=input.current;
        if(!observe)throw std::invalid_argument("TW native movement host requires actual source Current");
        qualified.current=[weak,weak_slot,observe](auto check,const auto& scope,const auto& images,const auto& sources) {
            const auto state=weak.lock();const auto slot=weak_slot.lock();
            if(!state || !slot)return false;state->owner();
            if(!state->qualification(slot,check,scope,images))return false;
            const bool actual=observe(check,scope,images,sources);
            return actual && state->qualification(slot,check,scope,images);
        };
        return qualified;
    }
    void cleanup(Session& session,const std::shared_ptr<Slot>& slot) {
        const auto retire=actual.retire;const auto retained=resources;
        detach(slot); // Old incarnation unavailable before actual destructors/callbacks.
        std::exception_ptr failure;
        try {if(retire)retire(session,slot->lease);}catch(...) {failure=std::current_exception();}
        slot->controller_bound=false;
        try {if(retained)retained->remove(session,slot->lease);}catch(...) {if(!failure)failure=std::current_exception();}
        if(failure)std::rethrow_exception(failure);
        // A missing exact source/resource slot is already retired; neither
        // owner is allowed to clean a mismatched successor generation.
    }
    bool install_internal(const std::shared_ptr<Session>& session,const Lease& lease,const Input& supplied) {
        std::optional<Input> owned;
        if(supplied.owned_ordinary)owned.emplace(supplied);
        const Input& input=owned?*owned:supplied;
        const bool custom=bool(input.owned_ordinary);
        const auto retained=resources;
        if(!session || !ready(*session,lease) || slots.contains(lease.session) || slots.size()>=capacity ||
           !input.current || bool(input.authority)==input.owned_ordinary.has_value() ||
           (input.owned_ordinary && input.owned_ordinary->rules!=rules) || !retained)return false;
        const auto saved=presence->saved_position(lease);
        if(!saved || *saved!=input.actual_position)return false;
        auto slot=std::make_shared<Slot>(session,lease,input);
        active_session=session.get();active_lease=lease;active_slot=slot;
        try {
            auto qualified=qualified_input(input,slot);
            if(!retained->install(session,lease,qualified) || !ready(*session,lease) ||
               presence->saved_position(lease)!=saved || !slot->active || !phase_current(*session,slot) ||
               (custom && !retained->owned_ordinary_retained_current(*session,lease))) {
                retained->remove(*session,lease);slot->active=false;return false;
            }
            slot->phase=Phase::Installed;
            if(!slots.emplace(lease.session,slot).second) {
                retained->remove(*session,lease);slot->active=false;return false;
            }
            if(custom) {
                // Drain both copied callbacks before the last pure custody
                // fence. The installed entry retains all selected originals.
                qualified.current={};owned.reset();
                if(reentered || !stored(*session,slot) || !phase_current(*session,slot) ||
                   !retained->owned_ordinary_retained_current(*session,lease)) {cleanup(*session,slot);return false;}
            }
            return true;
        }catch(...) {
            slot->active=false;
            try {retained->remove(*session,lease);}catch(...) {}
            throw;
        }
    }
    std::shared_ptr<SharedTaiwanMovement::WorldOwner> first_factory(Session& session,const Lease& lease,
        const SharedTaiwanMovementSource::Factory& factory) {
        owner();
        if(operation!=Kind::Movement || active_session!=&session || !active_lease || *active_lease!=lease ||
           !ready(session,lease))return {};
        auto found=slots.find(lease.session);
        if(found==slots.end()) {
            if(!input_source)return {};
            const auto saved=presence->saved_position(lease);
            if(!saved)return {};
            const SharedTaiwanNativeMovementScene::FactoryScope scope{lease,*saved};
            const auto supply=input_source;auto input=supply(session,scope);
            if(battle_refresh && (!input || !input->owned_ordinary ||
               input->actual_initial_scene_generation==battle_refresh->old_scene_generation ||
               session.battle_generation()!=battle_refresh->battle_generation))return {};
            if(!input || !ready(session,lease) || presence->saved_position(lease)!=saved ||
               input->actual_position!=*saved || !install_internal(session.shared_from_this(),lease,*input))return {};
            found=slots.find(lease.session);
        }
        if(found==slots.end())return {};
        const auto slot=found->second;active_slot=slot;
        if(slot->lease!=lease || !stored(session,slot) || !ready(session,lease))return {};
        auto native=factory(session,lease);
        return native && stored(session,slot) && ready(session,lease) && phase_current(session,slot) &&
            (!slot->owned_battle_generation || (stored(session,slot) && resources &&
                resources->owned_ordinary_retained_current(session,lease)))?native:std::shared_ptr<SharedTaiwanMovement::WorldOwner>{};
    }
    std::vector<std::uint8_t> movement(Session& session,std::span<const RecoveredMovement::Request> requests) {
        Operation guard(*this,Kind::Movement);
        const auto lease=presence->ready_lease(session.id(),session.account_id,session.character_id);
        if(!lease || !ready(session,*lease))throw std::invalid_argument("TW native movement host requires exact published ready lease");
        active_session=&session;active_lease=*lease;
        const auto found=slots.find(lease->session);
        if(found!=slots.end()) {
            active_slot=found->second;
            if(active_slot->lease!=*lease || !stored(session,active_slot))
                throw std::invalid_argument("TW native movement host stale Session/resource generation");
            if(!phase_current(session,active_slot)) {
                // Same ready Lease after real battle completion still has a
                // different phase fingerprint. Retire exact old controller and
                // resources before invoking the actual input source again.
                const auto previous_scene=active_slot->scene_generation;
                const auto next_battle=session.battle_generation();
                cleanup(session,active_slot);active_slot.reset();
                if(!input_source || !ready(session,*lease) || session.battle_generation()!=next_battle)
                    throw std::invalid_argument("TW owned movement requires actual post-battle scene source");
                battle_refresh=BattleRefresh{previous_scene,next_battle};
            }
        }
        try {
            const auto dispatch=actual.movement;
            auto output=dispatch(session,requests);
            if(!active_slot || !stored(session,active_slot) || !phase_current(session,active_slot) || !ready(session,*lease) ||
               (active_slot->owned_battle_generation && (!stored(session,active_slot) || !phase_current(session,active_slot) ||
                  !resources || !resources->owned_ordinary_retained_current(session,*lease))))
                throw std::runtime_error("TW native movement host final source qualification failed");
            active_slot->controller_bound=true;return output;
        }catch(...) {
            const auto failure=std::current_exception();
            if(active_slot && active_slot->lease==*lease && active_slot->connection.lock().get()==&session)
                try {cleanup(session,active_slot);}catch(...) {}
            std::rethrow_exception(failure); // The real committed prefix remains durable.
        }
    }
    bool replace(const std::shared_ptr<Session>& session,const Lease& lease,const Input& supplied) {
        Operation guard(*this,Kind::Replace);
        std::optional<Input> owned;
        if(supplied.owned_ordinary)owned.emplace(supplied);
        const Input& input=owned?*owned:supplied;
        const bool custom=bool(input.owned_ordinary);
        const auto retained=resources;const auto retire=actual.retire;
        if(!session || !ready(*session,lease) || !input.current || bool(input.authority)==input.owned_ordinary.has_value() ||
           (input.owned_ordinary && input.owned_ordinary->rules!=rules) || !retained || !retire)return false;
        const auto found=slots.find(lease.session);
        if(found==slots.end() || found->second->lease!=lease || !stored(*session,found->second))return false;
        const auto previous=found->second;active_slot=previous;active_session=session.get();active_lease=lease;
        const auto saved=presence->saved_position(lease);
        if(!saved || *saved!=input.actual_position)return false;
        try {
            const bool retired=retire(*session,lease);
            if((previous->controller_bound && !retired) || !ready(*session,lease) || !stored(*session,previous)) {
                cleanup(*session,previous);return false;
            }
            previous->controller_bound=false;detach(previous);
            auto next=std::make_shared<Slot>(session,lease,input);active_slot=next;
            auto qualified=qualified_input(input,next);
            if(!retained->replace(session,lease,qualified) || !ready(*session,lease) ||
               presence->saved_position(lease)!=saved || !next->active || !phase_current(*session,next) ||
               (custom && !retained->owned_ordinary_retained_current(*session,lease))) {
                cleanup(*session,next);return false;
            }
            next->phase=Phase::Installed;
            if(!slots.emplace(lease.session,next).second) {cleanup(*session,next);return false;}
            if(custom) {
                qualified.current={};owned.reset();
                if(reentered || !stored(*session,next) || !phase_current(*session,next) ||
                   !retained->owned_ordinary_retained_current(*session,lease)) {cleanup(*session,next);return false;}
            }
            return true;
        }catch(...) {
            const auto failure=std::current_exception();
            if(active_slot)try {cleanup(*session,active_slot);}catch(...) {}
            std::rethrow_exception(failure);
        }
    }
    bool remove(Session& session,const Lease& lease) {
        Operation guard(*this,Kind::Remove);
        const auto found=slots.find(lease.session);
        if(found==slots.end() || found->second->lease!=lease || found->second->connection.lock().get()!=&session ||
           session.id()!=lease.session)return false;
        active_slot=found->second;active_session=&session;active_lease=lease;
        cleanup(session,active_slot);return !reentered;
    }
    void release(Session& session) {
        owner();
        if(operation!=Kind::Idle) {poison();throw std::logic_error("TW native movement host cleanup reentered");}
        if(closed)return;
        const auto found=slots.find(session.id());
        if(found==slots.end())return;
        const auto lease=found->second->lease;
        if(!remove(session,lease))throw std::invalid_argument("TW native movement host cleanup Session mismatch");
    }
    void initialize() {
        resources=TaiwanNativeSceneResourceOwner::create(presence,capacity);
        const auto factory=resources->factory();const auto weak=weak_from_this();
        actual=SharedTaiwanMovementSource::create(presence,visibility,rules,
            [weak,factory](Session& session,const Lease& lease) {
                const auto state=weak.lock();
                return state?state->first_factory(session,lease,factory):std::shared_ptr<SharedTaiwanMovement::WorldOwner>{};
            },capacity,movement_custody);
        if(!actual.movement || !actual.release || !actual.invalidate_active || !actual.retire)
            throw std::invalid_argument("TW native movement host requires complete actual controller binding");
    }
    void shutdown() noexcept {
        if(thread!=std::this_thread::get_id())std::terminate();
        closed=true;reentered=true;
        const auto callbacks=actual;const auto retained_resources=resources;
        if(callbacks.invalidate_active)try {callbacks.invalidate_active();}catch(...) {}
        if(retained_resources)try {retained_resources->invalidate_active();}catch(...) {}
        for(auto& row:slots)row.second->active=false;
        auto retired=std::move(slots);slots.clear();
        for(auto& row:retired)if(const auto session=row.second->connection.lock()) {
            try {callbacks.retire(*session,row.second->lease);}catch(...) {}
            try {retained_resources->remove(*session,row.second->lease);}catch(...) {}
        }
        retired.clear();actual={};resources.reset();
    }
};
SharedTaiwanNativeMovementHost::SharedTaiwanNativeMovementHost(std::shared_ptr<State> state):state_(std::move(state)) {}
std::shared_ptr<SharedTaiwanNativeMovementHost> SharedTaiwanNativeMovementHost::create(
    std::shared_ptr<SharedWorldPresence> presence,std::shared_ptr<cn::SharedActorVisibility> visibility,
    std::shared_ptr<TaiwanMovementRules> rules,std::size_t capacity) {
    if(!presence || !visibility || !visibility->owns_presence(presence) || !rules || !capacity)
        throw std::invalid_argument("TW native movement host requires exact common presence/visibility/native rules/capacity");
    auto state=std::make_shared<State>(std::move(presence),std::move(visibility),std::move(rules),InputSource{},capacity);
    state->initialize();
    return std::shared_ptr<SharedTaiwanNativeMovementHost>(new SharedTaiwanNativeMovementHost(std::move(state)));
}
std::shared_ptr<SharedTaiwanNativeMovementHost> SharedTaiwanNativeMovementHost::create(
    std::shared_ptr<SharedWorldPresence> presence,std::shared_ptr<cn::SharedActorVisibility> visibility,
    std::shared_ptr<TaiwanMovementRules> rules,InputSource source,std::size_t capacity,
    std::shared_ptr<SqliteOwnedEquipmentTransaction> movement_custody) {
    if(!presence || !visibility || !visibility->owns_presence(presence) || !rules || !source || !capacity)
        throw std::invalid_argument("TW native movement host requires actual common owners/rules/input provider/capacity");
    auto state=std::make_shared<State>(std::move(presence),std::move(visibility),std::move(rules),std::move(source),capacity,
        std::move(movement_custody));
    state->initialize();
    return std::shared_ptr<SharedTaiwanNativeMovementHost>(new SharedTaiwanNativeMovementHost(std::move(state)));
}
SharedTaiwanNativeMovementHost::~SharedTaiwanNativeMovementHost() {state_->shutdown();}
bool SharedTaiwanNativeMovementHost::install(const std::shared_ptr<Session>& session,const Lease& lease,const Input& input) {
    const auto state=state_;State::Operation guard(*state,State::Kind::Install);return state->install_internal(session,lease,input);
}
bool SharedTaiwanNativeMovementHost::replace(const std::shared_ptr<Session>& session,const Lease& lease,const Input& input) {
    const auto state=state_;return state->replace(session,lease,input);
}
bool SharedTaiwanNativeMovementHost::remove(Session& session,const Lease& lease) {
    const auto state=state_;return state->remove(session,lease);
}
SharedTaiwanMovementSource::Binding SharedTaiwanNativeMovementHost::binding() {
    State::Operation guard(*state_,State::Kind::Install);const auto self=shared_from_this();
    return {
        [self](Session& session,std::span<const RecoveredMovement::Request> requests){return self->state_->movement(session,requests);},
        [self](Session& session){self->state_->release(session);},
        [self]{self->invalidate_active();},
        [self](Session& session,const Lease& lease){return self->remove(session,lease);}
    };
}
void SharedTaiwanNativeMovementHost::invalidate_active() {state_->poison();}
}
