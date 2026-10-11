#include "game/TaiwanNativeSceneResourceOwner.h"
#include <exception>
#include <map>
#include <stdexcept>
#include <thread>
#include <utility>

namespace god2 {
struct TaiwanNativeSceneResourceOwner::State:std::enable_shared_from_this<State> {
    struct Incarnation {}; // Private exact supply identity, never a native counter.
    struct Pending {
        Scene::Candidate candidate;
        std::shared_ptr<const Scene::Permit> ticket; // Exact one-use actual permit identity.
    };
    struct Entry {
        const Lease lease;
        const std::weak_ptr<Session> connection;
        const Sources sources;
        const TaiwanNativeMapAsset::RomBound binding;
        const Scene::Resources resources;
        const ResourceCurrent actual_current;
        const std::shared_ptr<Scene::Authority> actual_authority;
        RecoveredPosition actor_position;
        std::uint8_t actor_direction;
        std::shared_ptr<const Incarnation> incarnation;
        std::optional<Pending> pending;
        bool active=true;
        Entry(const std::shared_ptr<Session>& session,const Lease& identity,Sources original,
            TaiwanNativeMapAsset::RomBound bound,Scene::Resources images,const Input& input)
            :lease(identity),connection(session),sources(std::move(original)),binding(std::move(bound)),
             resources(std::move(images)),actual_current(input.current),actual_authority(input.authority),
             actor_position(input.actual_position),actor_direction(input.actual_direction) {}
    };
    const std::thread::id thread=std::this_thread::get_id();
    std::shared_ptr<SharedWorldPresence> presence;
    const std::size_t capacity;
    std::map<std::uint64_t,std::shared_ptr<Entry>> entries;
    std::weak_ptr<Entry> affected;
    bool busy=false,reentered=false,closed=false;
    State(std::shared_ptr<SharedWorldPresence> actual,std::size_t limit)
        :presence(std::move(actual)),capacity(limit) {}
    ~State() {if(thread!=std::this_thread::get_id())std::terminate();}
    void owner() const {
        if(thread!=std::this_thread::get_id())throw std::logic_error("TW selected scene resource game owner mismatch");
    }
    void poison() {
        reentered=true;
        if(const auto entry=affected.lock()) {
            entry->active=false;
            const auto found=entries.find(entry->lease.session);
            if(found!=entries.end() && found->second==entry)entries.erase(found);
        }
        // Immediate detach, including reentry caught by an external callback
        // or destructor after its outer operation's last ordinary check.
    }
    struct Operation {
        State& state;
        explicit Operation(State& actual):state(actual) {
            state.owner();
            if(state.busy) {state.poison();throw std::logic_error("TW selected scene resource reentry rejected");}
            if(state.closed)throw std::logic_error("TW selected scene resource owner closed");
            state.busy=true;state.reentered=false;
        }
        ~Operation() {state.affected.reset();state.busy=false;}
    };
    void shutdown() noexcept {
        if(thread!=std::this_thread::get_id())std::terminate();
        closed=true;reentered=true;busy=true;
        for(auto& row:entries)row.second->active=false;
        auto retired=std::move(entries);entries.clear();retired.clear();
        // Outstanding Native/Permit closures retain retired immutable inputs,
        // but closed/active qualification rejects every further use.
    }
    bool ready(Session& session,const Lease& lease) const {
        if(closed || reentered || session.closing() || session.id()!=lease.session ||
           session.account_id!=lease.account || session.character_id!=lease.character ||
           session.state()!=SessionState::InWorld || !session.recovered_world_ready() ||
           !session.common_world_delivery_current(lease.account,lease.character,lease.generation) ||
           session.common_world_entry_current(lease.account,lease.character,lease.generation))return false;
        const auto actual=presence->ready_lease(lease.session,lease.account,lease.character);
        return actual && *actual==lease;
    }
    bool installed(const std::shared_ptr<Entry>& entry) const {
        if(!entry || !entry->active || closed || reentered)return false;
        const auto found=entries.find(entry->lease.session);
        const auto session=entry->connection.lock();
        return found!=entries.end() && found->second==entry && session && ready(*session,entry->lease);
    }
    void terminal(const std::shared_ptr<Entry>& entry) {
        entry->active=false;entry->pending.reset();
        const auto found=entries.find(entry->lease.session);
        if(found!=entries.end() && found->second==entry)entries.erase(found);
        // No common lease cleanup, rollback or foreign successor destruction.
    }
    static bool same_step(const TaiwanMovementRules::Step& a,const TaiwanMovementRules::Step& b) {
        return a.direction==b.direction && a.native_cell==b.native_cell &&
            a.request.x==b.request.x && a.request.y==b.request.y &&
            a.request.sequence==b.request.sequence && a.request.opaque_tail==b.request.opaque_tail;
    }
    static bool same_candidate(const Scene::Candidate& a,const Scene::Candidate& b) {
        return a.owner.lease==b.owner.lease && a.owner.position==b.owner.position &&
            a.owner.direction==b.owner.direction && a.owner.publication_revision==b.owner.publication_revision &&
            a.actual_resource_generation==b.actual_resource_generation &&
            a.actual_initial_scene_generation==b.actual_initial_scene_generation &&
            a.cell_source==b.cell_source && same_step(a.step,b.step);
    }
    bool images_match(const std::shared_ptr<Entry>& entry,const Scene::Resources& images) const {
        const auto& expected=entry->resources;
        return images.composed_grid && expected.composed_grid && images.complete() &&
            images.cell_source()==Scene::CellSource::ComposedMode2 &&
            images.actual_resource_generation==expected.actual_resource_generation &&
            images.actual_initial_scene_generation==expected.actual_initial_scene_generation &&
            std::addressof(images.composed_grid->material())==std::addressof(expected.composed_grid->material()) &&
            std::addressof(images.composed_grid->bytes())==std::addressof(expected.composed_grid->bytes());
    }
    bool scope_match(const std::shared_ptr<Entry>& entry,Scene::Check check,const Scene::Scope& scope,
        const RecoveredPosition& saved) const {
        if(scope.lease!=entry->lease || scope.position!=entry->actor_position ||
           scope.direction!=entry->actor_direction || scope.position.area!=entry->lease.position.area ||
           scope.position.scene!=entry->lease.position.scene)return false;
        if(check!=Scene::Check::BeforePublish)return saved==scope.position;
        // Existing Scene deliberately exposes before Scope after its sole DB
        // CAS. The retained exact candidate qualifies that already durable after.
        return entry->pending && entry->pending->candidate.owner.position==scope.position &&
            entry->pending->candidate.owner.direction==scope.direction &&
            entry->pending->candidate.owner.publication_revision==scope.publication_revision &&
            saved.area==scope.position.area && saved.scene==scope.position.scene &&
            saved.x==entry->pending->candidate.step.request.x && saved.y==entry->pending->candidate.step.request.y &&
            saved.revision>scope.position.revision;
    }
    bool resource_current(const std::shared_ptr<Entry>& entry,const std::shared_ptr<const Incarnation>& incarnation,Scene::Check check,
        const Scene::Scope& scope,const Scene::Resources& images) {
        Operation operation(*this);
        // A retired Scene cannot invalidate a successor supply of this Entry.
        if(entry->incarnation!=incarnation)return false;
        affected=entry;
        try {
            const auto saved=presence->saved_position(entry->lease);
            if(!installed(entry) || !images_match(entry,images) || !saved || !scope_match(entry,check,scope,*saved)) {
                terminal(entry);return false;
            }
            const auto observe=entry->actual_current;
            const bool actual=observe(check,scope,images,entry->sources);
            const auto after=presence->saved_position(entry->lease);
            if(!actual || !installed(entry) || !images_match(entry,images) || !after || *after!=*saved ||
               !scope_match(entry,check,scope,*after)) {terminal(entry);return false;}
            return true;
        }catch(...) {terminal(entry);throw;}
    }
    struct Authority final:Scene::Authority {
        const std::shared_ptr<State> state;
        const std::shared_ptr<Entry> entry;
        const std::shared_ptr<const Incarnation> incarnation;
        Authority(std::shared_ptr<State> owner,std::shared_ptr<Entry> sources,std::shared_ptr<const Incarnation> supplied)
            :state(std::move(owner)),entry(std::move(sources)),incarnation(std::move(supplied)) {}
        std::optional<Scene::Permit> authorize(const Scene::Candidate& candidate) override {
            Operation operation(*state);
            if(entry->incarnation!=incarnation)return std::nullopt;
            state->affected=entry;
            try {
                const auto saved=state->presence->saved_position(entry->lease);
                if(!state->installed(entry) || entry->pending || candidate.owner.lease!=entry->lease ||
                   candidate.owner.position!=entry->actor_position || candidate.owner.direction!=entry->actor_direction ||
                   !saved || *saved!=candidate.owner.position ||
                   candidate.actual_resource_generation!=entry->resources.actual_resource_generation ||
                   candidate.actual_initial_scene_generation!=entry->resources.actual_initial_scene_generation ||
                   candidate.cell_source!=Scene::CellSource::ComposedMode2)return std::nullopt;
                const auto actual=entry->actual_authority;
                auto permit=actual->authorize(candidate);
                const auto after=state->presence->saved_position(entry->lease);
                if(!state->installed(entry) || !after || *after!=*saved) {state->terminal(entry);return std::nullopt;}
                if(!permit)return std::nullopt;
                // Preserve actual full5D and ticket callbacks. No echo/fallback.
                auto retained=std::make_shared<const Scene::Permit>(std::move(*permit));
                const auto owner=state;const auto sources=entry;const auto supplied_incarnation=incarnation;
                entry->pending=Pending{candidate,retained};
                return Scene::Permit(retained->full_native_ack,
                    [owner,sources,retained,candidate,supplied_incarnation](const Scene::Candidate& supplied) {
                        Operation active(*owner);
                        if(sources->incarnation!=supplied_incarnation || !sources->pending ||
                           sources->pending->ticket!=retained)return false;
                        owner->affected=sources;
                        try {
                            const auto before=owner->presence->saved_position(sources->lease);
                            if(!owner->installed(sources) || !sources->pending ||
                               !same_candidate(supplied,candidate) || sources->pending->ticket!=retained ||
                               !same_candidate(sources->pending->candidate,candidate) ||
                               !before) {owner->terminal(sources);return false;}
                            const auto check=*before==candidate.owner.position?Scene::Check::Current:Scene::Check::BeforePublish;
                            if(!owner->scope_match(sources,check,candidate.owner,*before)) {
                                owner->terminal(sources);return false;
                            }
                            const bool actual=retained->current(supplied);
                            const auto after=owner->presence->saved_position(sources->lease);
                            if(!actual || !owner->installed(sources) || !after || *after!=*before ||
                               sources->incarnation!=supplied_incarnation || !sources->pending ||
                               sources->pending->ticket!=retained || !same_candidate(sources->pending->candidate,candidate)) {
                                owner->terminal(sources);return false;
                            }
                            return true;
                        }catch(...) {owner->terminal(sources);throw;}
                    },
                    [owner,sources,retained,candidate,supplied_incarnation](const SharedTaiwanMovement::Committed& committed) {
                        Operation active(*owner);
                        if(sources->incarnation!=supplied_incarnation || !sources->pending ||
                           sources->pending->ticket!=retained)return false;
                        owner->affected=sources;
                        try {
                            const auto saved=owner->presence->saved_position(sources->lease);
                            if(!owner->installed(sources) || !sources->pending ||
                               sources->pending->ticket!=retained || !same_candidate(sources->pending->candidate,candidate) ||
                               committed.before!=sources->actor_position || !same_step(committed.step,candidate.step) ||
                               !saved || *saved!=committed.after || committed.after.area!=committed.before.area ||
                               committed.after.scene!=committed.before.scene || committed.after.x!=committed.step.request.x ||
                               committed.after.y!=committed.step.request.y || committed.after.revision<=committed.before.revision) {
                                owner->terminal(sources);return false;
                            }
                            sources->pending.reset(); // One use before actual publication callback.
                            const bool actual=retained->publish_authority(committed);
                            const auto after=owner->presence->saved_position(sources->lease);
                            if(!actual || !owner->installed(sources) || sources->incarnation!=supplied_incarnation ||
                               !after || *after!=committed.after) {
                                owner->terminal(sources);return false;
                            }
                            // Scene has already advanced its own private pose;
                            // now retain the successful real actor prefix for a
                            // future factory. Failure never rewinds common CAS.
                            sources->actor_position=committed.after;
                            sources->actor_direction=committed.step.direction;
                            return true;
                        }catch(...) {owner->terminal(sources);throw;}
                    });
            }catch(...) {state->terminal(entry);throw;}
        }
    };
    bool put(const std::shared_ptr<Session>& session,const Lease& lease,const Input& input,bool replacing) {
        Operation operation(*this);
        if(!session || !ready(*session,lease) || !input.current || !input.authority || input.actual_direction>7 ||
           !input.sources.actual_hmd_generation || !input.actual_resource_generation ||
           !input.actual_initial_scene_generation || !input.max_hmd_plain_bytes || !input.max_rom_plain_bytes ||
           input.actual_position.area!=lease.position.area || input.actual_position.scene!=lease.position.scene)return false;
        const auto saved=presence->saved_position(lease);
        if(!saved || *saved!=input.actual_position)return false;
        auto found=entries.find(lease.session);
        auto previous=found==entries.end()?std::shared_ptr<Entry>{}:found->second;
        affected=previous;
        if(replacing) {
            if(found==entries.end() || found->second->lease!=lease || found->second->connection.lock()!=session)return false;
        }else if(found!=entries.end() || entries.size()>=capacity)return false;
        // Copy all public vectors before private const ownership. Immutable
        // Selection handles retain request/probe/selected original bytes.
        Sources sources=input.sources;
        try {
            if(sources.hmd.request().kind!=TaiwanNativeResourceSelection::Kind::TextFile)return false;
            auto hmd=TaiwanNativeMapAsset::from_selected_resource(sources.hmd.actual_source(),
                sources.hmd.encoded_bytes(),input.max_hmd_plain_bytes);
            if(!hmd || sources.roms.size()!=hmd->rom_references().size() || sources.roms.size()>128)return false;
            std::vector<TaiwanNativeMapAsset::RomSlot> slots;slots.reserve(sources.roms.size());
            for(std::size_t i=0;i<sources.roms.size();++i) {
                const auto& row=sources.roms[i];const auto& request=row.selected.request();
                const auto& reference=hmd->rom_references()[i];
                const std::vector<std::uint8_t> raw(reference.begin(),reference.end());
                if(row.ordinal!=i || !row.actual_resource_generation ||
                   request.kind!=TaiwanNativeResourceSelection::Kind::RomBinary || request.full_bank_operand!=i ||
                   request.original_reference!=raw || request.native_prefix!=sources.actual_rom_prefix ||
                   request.actual_working_directory!=sources.hmd.request().actual_working_directory)return false;
                auto rom=TaiwanNativeRomAsset::from_selected_resource(row.selected.actual_source(),
                    row.selected.encoded_bytes(),input.max_rom_plain_bytes);
                if(!rom)return false; // Selected0516 parse failure has no plain fallback.
                slots.push_back({i,reference,row.actual_resource_generation,std::move(*rom)});
            }
            auto binding=hmd->bind_rom_sources(std::move(slots));
            if(!binding)return false;
            auto images=binding->resources(input.actual_resource_generation,input.actual_initial_scene_generation);
            if(!images)return false;
            auto entry=std::make_shared<Entry>(session,lease,std::move(sources),std::move(*binding),std::move(*images),input);
            const Scene::Scope scope{lease,*saved,input.actual_direction,input.actual_initial_scene_generation};
            const bool actual=entry->actual_current(Scene::Check::Adopt,scope,entry->resources,entry->sources);
            const auto after=presence->saved_position(lease);
            if(!actual || !ready(*session,lease) || !after || *after!=*saved) {
                if(reentered && previous)terminal(previous);
                return false;
            }
            // Retire and detach before external dependency destruction. Exact
            // Entry pointer is private lineage, never a native counter.
            if(replacing) {
                previous->active=false;entries.erase(found);previous.reset();
                if(!ready(*session,lease) || presence->saved_position(lease)!=saved)return false;
            }
            entries.emplace(lease.session,std::move(entry));return true;
        }catch(const std::logic_error&) {
            if(previous)terminal(previous);
            if(reentered)throw;
            return false;
        }catch(...) {if(previous)terminal(previous);throw;}
    }
    std::optional<Scene::Material> supply(Session& session,const Scene::FactoryScope& scope) {
        Operation operation(*this);
        const auto found=entries.find(session.id());
        if(found==entries.end())return std::nullopt;
        const auto entry=found->second;
        const auto saved=presence->saved_position(scope.lease);
        if(entry->connection.lock().get()!=&session || entry->lease!=scope.lease || !installed(entry) ||
           entry->pending || !saved || *saved!=scope.saved_position || entry->actor_position!=*saved)return std::nullopt;
        const auto state=shared_from_this();
        // Every supply has a private exact identity. A complete identical
        // Candidate/publication revision cannot reactivate an older Scene.
        const auto incarnation=std::make_shared<const Incarnation>();
        entry->incarnation=incarnation;
        Scene::Native native(entry->resources,entry->actor_position,entry->actor_direction,
            [state,entry,incarnation](auto check,const auto& qualified,const auto& images) {
                return state->resource_current(entry,incarnation,check,qualified,images);
            });
        return Scene::Material(std::move(native),std::make_shared<Authority>(state,entry,incarnation));
    }
};
TaiwanNativeSceneResourceOwner::TaiwanNativeSceneResourceOwner(std::shared_ptr<State> state):state_(std::move(state)) {}
std::shared_ptr<TaiwanNativeSceneResourceOwner> TaiwanNativeSceneResourceOwner::create(
    std::shared_ptr<SharedWorldPresence> presence,std::size_t capacity) {
    if(!presence || !capacity)throw std::invalid_argument("TW selected scene resource owner requires actual presence/capacity");
    return std::shared_ptr<TaiwanNativeSceneResourceOwner>(new TaiwanNativeSceneResourceOwner(
        std::make_shared<State>(std::move(presence),capacity)));
}
TaiwanNativeSceneResourceOwner::~TaiwanNativeSceneResourceOwner() {state_->shutdown();}
bool TaiwanNativeSceneResourceOwner::install(const std::shared_ptr<Session>& session,const Lease& lease,const Input& input) {
    return state_->put(session,lease,input,false);
}
bool TaiwanNativeSceneResourceOwner::replace(const std::shared_ptr<Session>& session,const Lease& lease,const Input& input) {
    return state_->put(session,lease,input,true);
}
bool TaiwanNativeSceneResourceOwner::remove(Session& session,const Lease& lease) {
    State::Operation operation(*state_);
    const auto found=state_->entries.find(lease.session);
    if(found==state_->entries.end() || found->second->lease!=lease || found->second->connection.lock().get()!=&session)return false;
    auto retired=found->second;retired->active=false;state_->entries.erase(found);retired.reset();
    return !state_->reentered && !state_->closed;
}
TaiwanNativeSceneResourceOwner::Scene::MaterialSource TaiwanNativeSceneResourceOwner::material_source() {
    State::Operation operation(*state_);const auto state=state_;
    return [state](Session& session,const Scene::FactoryScope& scope){return state->supply(session,scope);};
}
SharedTaiwanMovementSource::Factory TaiwanNativeSceneResourceOwner::factory() {
    State::Operation operation(*state_);const auto state=state_;
    return Scene::factory(state->presence,
        [state](Session& session,const Scene::FactoryScope& scope){return state->supply(session,scope);});
}
void TaiwanNativeSceneResourceOwner::invalidate_active() {
    state_->owner();if(state_->busy)state_->poison();
}
}
