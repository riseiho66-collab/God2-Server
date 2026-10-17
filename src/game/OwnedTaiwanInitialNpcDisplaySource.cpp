#include "game/OwnedTaiwanInitialNpcDisplaySource.h"
#include "game/TaiwanInitialNpcSceneObservation.h"
#include "protocol/RecoveredNpcRecord.h"
#include "protocol/RecoveredTaiwanServerRecords.h"
#include <algorithm>
#include <stdexcept>
#include <thread>
#include <type_traits>
#include <utility>

namespace god2 {
namespace {
using Entered=SharedTaiwanWorldEntered;
using Visibility=shared::SharedActorVisibility;
template<class A,class B> bool same_owner(const std::shared_ptr<A>& a,const std::shared_ptr<B>& b) noexcept {
    return a.get()==b.get()&&!a.owner_before(b)&&!b.owner_before(a);
}
bool same_scope(const Entered::Scope& a,const Entered::Scope& b) noexcept {
    return a.lease==b.lease&&a.entry.wire==b.entry.wire&&a.entry.logical==b.entry.logical&&
        a.entry.actor_handle==b.entry.actor_handle&&a.entry.area==b.entry.area&&a.entry.scene==b.entry.scene&&
        a.entry.x==b.entry.x&&a.entry.y==b.entry.y&&a.entry.kind==b.entry.kind&&
        a.tail_language==b.tail_language&&a.population==b.population&&
        same_owner(a.actor_input,b.actor_input)&&same_owner(a.actor_endpoints,b.actor_endpoints);
}
static_assert(std::is_nothrow_move_constructible_v<Entered::Native>);
}
struct OwnedTaiwanInitialNpcDisplaySource::Owner {
    const std::shared_ptr<SharedWorldPresence> presence;
    SqliteWorldDisplayRepository& repository;
    const NativeNpcDisplayCatalog& npcs;
    const NativeEnemyDisplayCatalog& enemies;
    const Entered::Source genuine;
    const std::thread::id thread=std::this_thread::get_id();
    const std::shared_ptr<std::atomic<bool>> live=std::make_shared<std::atomic<bool>>(true);
    bool running=false,poisoned=false;
    Owner(std::shared_ptr<SharedWorldPresence> p,SqliteWorldDisplayRepository& r,
            const NativeNpcDisplayCatalog& n,const NativeEnemyDisplayCatalog& e,Entered::Source source)
        :presence(std::move(p)),repository(r),npcs(n),enemies(e),genuine(std::move(source)){}
    struct Call {
        Owner& owner;bool entered=false;
        explicit Call(Owner& value):owner(value) {
            if(owner.thread!=std::this_thread::get_id())return;
            if(owner.running){
                owner.live->store(false,std::memory_order_release);
                owner.poisoned=true;return;
            }
            if(!owner.poisoned){owner.running=true;entered=true;}
        }
        ~Call(){if(entered)owner.running=false;}
    };
};
struct OwnedTaiwanInitialNpcDisplaySource::State {
    const std::shared_ptr<Owner> owner;
    const Entered::Scope scope;
    const std::weak_ptr<Session> connection;
    const SqliteWorldDisplayRepository::SceneReadset readset;
    const std::shared_ptr<std::atomic<bool>> scene_live=std::make_shared<std::atomic<bool>>(true);
    std::shared_ptr<const TaiwanInitialNpcSceneObservation> observation;
    // The returned Native is a distinct object. Its callbacks capture State;
    // this immutable original never captures State or creates that cycle.
    std::shared_ptr<const Entered::Native> original;
    bool cancelled=false,cleaned=false,installed=false,outward_started=false;
    State(std::shared_ptr<Owner> actual,Entered::Scope input,Session& session,
            SqliteWorldDisplayRepository::SceneReadset saved)
        :owner(std::move(actual)),scope(std::move(input)),connection(session.weak_from_this()),readset(std::move(saved)){}
    ~State() {
        if(owner->thread!=std::this_thread::get_id())std::terminate();
        try{cleanup();}catch(...){}
    }
    void cancel() noexcept {
        scene_live->store(false,std::memory_order_release);
        cancelled=true;
    }
    void cleanup(Entered::Native* unpublished=nullptr) {
        if(owner->thread!=std::this_thread::get_id())std::terminate();
        cancel(); // Revoke the private receipt before callbacks/destructors/reentry.
        if(std::exchange(cleaned,true))return;
        if(original&&original->cleanup)original->cleanup(scope);
        else if(unpublished&&unpublished->cleanup)unpublished->cleanup(scope);
    }
    bool pure() const noexcept {
        try {
            if(owner->thread!=std::this_thread::get_id()||owner->poisoned||cancelled||
               !observation||!observation->retained()||!scope.actor_input||
               !scope.population||!observation->matches_scope(scope.lease,*scope.population,scope.actor_input)||
               !owner->repository.uses_catalogs(owner->npcs,owner->enemies)||
               !scope.population||scope.population->joining().lease!=scope.lease||
               readset.area()!=scope.entry.area||readset.scene()!=scope.entry.scene||readset.isolated_test()||
               scope.entry.area!=scope.lease.position.area||scope.entry.scene!=scope.lease.position.scene||
               !owner->presence->retained_initial_population_current(*scope.population))return false;
            bool bound=false;
            {
                const auto actual=connection.lock();
                bound=actual&&!actual->closing()&&actual->id()==scope.lease.session&&
                    actual->account_id==scope.lease.account&&actual->character_id==scope.lease.character&&
                    actual->recovered_world_ready()&&actual->recovered_client_language()==scope.tail_language;
            } // Last temporary strong Session dies before the final pure fence.
            return bound&&!cancelled&&!owner->poisoned&&
                owner->presence->retained_initial_population_current(*scope.population)&&
                observation->matches_scope(scope.lease,*scope.population,scope.actor_input)&&
                !cancelled&&!owner->poisoned;
        }catch(...){return false;}
    }
    bool scene_current() const noexcept {
        // The full saved rows/levels/referenced catalogs are compared together.
        // This is a value observation, not an ABA token or complete-world proof.
        return pure()&&owner->repository.current_scene(readset,owner->npcs,owner->enemies)&&pure();
    }
    bool live(Entered::Check check) const {
        const auto retained=original;if(!retained||!retained->current||!pure())return false;
        bool accepted=false;
        {
            const auto current=retained->current;
            if(!pure())return false;
            accepted=current(check,scope);
        } // All actual callback-copy destruction precedes the final SQL cut.
        return accepted&&scene_current();
    }
    bool same_connection(Session& actual) const noexcept {
        bool same=false;
        {
            const auto retained=connection.lock();
            same=retained.get()==&actual&&retained&&same_owner(retained,actual.weak_from_this().lock());
        }
        return same&&pure();
    }
};
Entered::Source OwnedTaiwanInitialNpcDisplaySource::wrap(
        std::shared_ptr<SharedWorldPresence> presence,SqliteWorldDisplayRepository& repository,
        const NativeNpcDisplayCatalog& npcs,const NativeEnemyDisplayCatalog& enemies,Entered::Source genuine) {
    if(!presence||!genuine||!repository.uses_catalogs(npcs,enemies))
        throw std::invalid_argument("Initial NPC source requires actual same-connection owners and genuine source");
    const auto owner=std::make_shared<Owner>(std::move(presence),repository,npcs,enemies,std::move(genuine));
    return [owner](Session& session,const Entered::Scope& scope){return supply(owner,session,scope);};
}
std::optional<Entered::Native> OwnedTaiwanInitialNpcDisplaySource::supply(
        const std::shared_ptr<Owner>& supplied_owner,Session& session,const Entered::Scope& supplied_scope) {
    const auto owner=supplied_owner;
    if(owner->thread!=std::this_thread::get_id())throw std::logic_error("Initial NPC source game owner mismatch");
    Owner::Call call(*owner);if(!call.entered)return {};
    const auto scope=supplied_scope;
    if(!scope.actor_input||!scope.actor_input->initial_population()||!scope.population||
       *scope.actor_input->initial_population()!=*scope.population||scope.population->joining().lease!=scope.lease||
       scope.entry.area!=scope.lease.position.area||scope.entry.scene!=scope.lease.position.scene||
       !owner->presence->retained_initial_population_current(*scope.population)||
       session.closing()||session.id()!=scope.lease.session||session.account_id!=scope.lease.account||
       session.character_id!=scope.lease.character||!session.recovered_world_ready()||
       session.recovered_client_language()!=scope.tail_language)return {};
    // Observe BEFORE invoking the genuine source. A read failure has no native
    // scene to clean up; no isolated/test or guessed empty-scene fallback.
    auto readset=owner->repository.observe_scene(owner->npcs,owner->enemies,scope.entry.area,scope.entry.scene,false);
    const auto state=std::make_shared<State>(owner,scope,session,std::move(readset));
    // Mint only here, before genuine Source. The receipt owns immutable values
    // and weak affine owners, never State, callbacks, Session or full Profile.
    state->observation=std::shared_ptr<const TaiwanInitialNpcSceneObservation>(
        new TaiwanInitialNpcSceneObservation(state->readset,owner->repository,owner->npcs,owner->enemies,
            scope.lease,*scope.population,scope.actor_input,scope.actor_input->source(),
            std::shared_ptr<const void>(owner),owner->live,state->scene_live));
    if(!state->pure())return {};
    auto supplied=owner->genuine(session,state->scope);if(!supplied)return {};
    try{state->original=std::make_shared<const Entered::Native>(std::move(*supplied));}
    catch(...){try{state->cleanup(&*supplied);}catch(...){}throw;}
    supplied.reset(); // Drop moved-from provider/result before any final cut.
    bool delivered=false;
    struct CleanupGuard {
        std::shared_ptr<State> state;bool& delivered;
        ~CleanupGuard(){if(!delivered)try{state->cleanup();}catch(...){}}
    } cleanup_guard{state,delivered};
    const auto original=state->original;
    if(original->initial_npc_observation||!original->current||!original->install||!original->cleanup||
       !state->live(Entered::Check::AfterSupply))return {};
    if((original->outward_decision==Entered::OutwardDecision::Supplied&&original->outward_provider)||
       (original->outward_decision==Entered::OutwardDecision::AfterInitialPublication&&
        (!original->outward.empty()||!original->outward_provider||!*original->outward_provider))||
       (original->outward_decision!=Entered::OutwardDecision::Supplied&&
        original->outward_decision!=Entered::OutwardDecision::AfterInitialPublication))return {};
    std::vector<RecoveredTaiwanServerRecords::Record> records;
    if(original->decision==Entered::ReplyDecision::ExplicitNoInitialReply){
        if(!original->logical.empty()||!original->incoming.empty()||!original->incoming_offsets.empty())return {};
    }else if(original->decision==Entered::ReplyDecision::CompleteNativeAggregate){
        auto parsed=RecoveredTaiwanServerRecords::read_aggregate(original->logical);if(!parsed)return {};
        records=std::move(*parsed);
    }else return {};
    std::vector<std::uint8_t> logical;logical.reserve(original->logical.size());
    for(const auto& record:records){
        if(record.offset!=logical.size())return {};
        if(record.opcode==0x72){
            const auto npc=RecoveredNpcRecord::parse(record.bytes);
            if(!npc)return {};
            const StoredWorldDisplay* saved=nullptr;
            for(const auto& row:state->readset.rows()){
                const auto candidate=RecoveredNpcRecord::parse(row.logical);
                if(!candidate||candidate->instanceIdentity()!=npc->instanceIdentity())continue;
                if(saved)return {}; // One actual instance, never an ambiguous join.
                saved=&row;
            }
            if(!saved||saved->area!=scope.entry.area||saved->scene!=scope.entry.scene||
               saved->origin!="NATIVE_CAPTURE_VERIFIED"||saved->provenance.empty()||
               !std::equal(saved->logical.begin(),saved->logical.end(),record.bytes.begin(),record.bytes.end()))return {};
            // Author the real selected record from the captured owning row.
            // Position/facing/secondary/opaque bits must already match exactly.
            logical.insert(logical.end(),saved->logical.begin(),saved->logical.end());
        }else logical.insert(logical.end(),record.bytes.begin(),record.bytes.end());
    }
    // Preserve repeated selected boundaries when the same unique saved row
    // matches each full record. A conflicting historical update is not guessed.
    // No requirement that all DB NPC rows appear: genuine selection owns its
    // exact visibility audience. Missing/empty rows never prove completeness.
    Entered::Native result=*original;
    result.logical=std::move(logical);
    result.initial_npc_observation=state->observation;
    result.current=[state](Entered::Check check,const Entered::Scope& value){
        Owner::Call call(*state->owner);
        return call.entered&&same_scope(state->scope,value)&&state->live(check);
    };
    result.install=[state](Session& actual,const Entered::Scope& value){
        Owner::Call call(*state->owner);
        if(!call.entered||state->installed||!same_scope(state->scope,value)||!state->same_connection(actual))return false;
        state->installed=true;
        // Held install is PURE: no scene_current/observe_scene/SQL here.
        const bool accepted=state->original->install(actual,state->scope);
        return accepted&&state->pure();
    };
    result.cleanup=[state](const Entered::Scope&){state->cleanup();};
    if(original->outward_decision==Entered::OutwardDecision::AfterInitialPublication){
        Entered::OutwardProvider outward=[state](Session& actual,const Entered::Scope& value)
            ->std::optional<std::vector<Visibility::OutwardRecipient>> {
            Owner::Call call(*state->owner);if(!call.entered)return {};
            // Latch before any callback copy, allocation or live observer.
            if(std::exchange(state->outward_started,true)){state->cancel();return {};}
            bool committed=false;
            struct Attempt {State& state;bool& committed;~Attempt(){if(!committed)state.cancel();}} attempt{*state,committed};
            if(!same_scope(state->scope,value)||!state->same_connection(actual)||!state->installed)return {};
            std::optional<std::vector<Visibility::OutwardRecipient>> selected;
            {
                const auto provider=*state->original->outward_provider;
                if(!state->pure())return {};
                auto supplied=provider(actual,state->scope);
                if(supplied)selected.emplace(std::move(*supplied));
            } // Actual provider copy and moved-from result die before SQL.
            if(!selected||!state->scene_current())return {};
            committed=true;return selected;
        };
        result.outward_provider=std::make_shared<const Entered::OutwardProvider>(std::move(outward));
    }
    // Result callback replacements and their actual old-copy destructors are
    // complete before the final original Current/full readset comparison.
    if(!state->live(Entered::Check::AfterSupply))return {};
    delivered=true;return std::optional<Entered::Native>(std::move(result));
}
}
