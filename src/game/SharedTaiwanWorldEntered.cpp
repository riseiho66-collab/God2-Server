#include "game/SharedTaiwanWorldEntered.h"
#include "protocol/RecoveredTaiwanServerRecords.h"
#include "protocol/RecoveredWorldFrame.h"
#include <algorithm>
#include <map>
#include <stdexcept>
#include <thread>
#include <type_traits>
#include <utility>

namespace god2 {
namespace {
using Entered=SharedTaiwanWorldEntered;
using Visibility=cn::SharedActorVisibility;
static_assert(std::is_nothrow_move_constructible_v<Entered::Native>);
struct Pending {
    Entered::Scope scope;
    std::weak_ptr<Session> connection;
    std::shared_ptr<Entered::Native> native;
    std::shared_ptr<Visibility::TaiwanInitialPublication> incoming;
    SharedTaiwanWorldLifecycle::ReadyCompletion done;
    bool cancelled=false,published=false,completed=false;
    bool outward_started=false,outward_poisoned=false;
};
struct SceneOwner:std::enable_shared_from_this<SceneOwner> {
    std::shared_ptr<SharedWorldPresence> presence;
    std::shared_ptr<Visibility> visibility;
    Entered::Source source;
    TaiwanWorldEntryIdentity identity=TaiwanWorldEntryIdentity::SelectedCharacter;
    Entered::InitialDeityPublisher deity_publisher=Entered::InitialDeityPublisher::External;
    // Friend-only bridges are minted by Entered::create from the same Presence;
    // suppliers never receive activation or retirement callbacks.
    std::function<bool(const SharedWorldPresence::InitialPopulation&,std::uint16_t)> activate_population;
    std::function<void(const SharedWorldPresence::InitialPopulation&)> retire_population;
    const std::thread::id thread=std::this_thread::get_id();
    std::map<std::uint64_t,std::shared_ptr<Pending>> pending;
    bool supplying=false,reentered=false;
    bool materializing=false,materialization_reentered=false;
    void owner() const {
        if(std::this_thread::get_id()!=thread)throw std::logic_error("TW scene publication game owner mismatch");
    }
    ~SceneOwner() {
        if(std::this_thread::get_id()!=thread)std::terminate();
        while(!pending.empty())cancel(pending.begin()->second);
    }
    bool pending_bound(const std::shared_ptr<Pending>& state,bool active) {
        owner();if(!state || state->cancelled || state->outward_poisoned ||
            (supplying && reentered) || (materializing && materialization_reentered))return false;
        const auto found=pending.find(state->scope.lease.session);
        const auto session=state->connection.lock();const auto& lease=state->scope.lease;
        if(found==pending.end() || found->second!=state || !session || session->closing() ||
           session->id()!=lease.session || session->account_id!=lease.account || session->character_id!=lease.character ||
           !session->recovered_world_ready() || session->recovered_client_language()!=state->scope.tail_language)return false;
        if(active)return session->state()==SessionState::InWorld &&
            session->common_world_delivery_current(lease.account,lease.character,lease.generation);
        return (session->state()==SessionState::CharacterSelected || session->state()==SessionState::InWorld) &&
            session->common_world_entry_current(lease.account,lease.character,lease.generation) &&
            !session->common_world_delivery_current(lease.account,lease.character,lease.generation);
    }
    bool population_bound(const std::shared_ptr<Pending>& state,bool active) {
        return pending_bound(state,active) && state->scope.population &&
            state->scope.population->joining().lease==state->scope.lease &&
            state->scope.population->activated()==active &&
            presence->retained_initial_population_current(*state->scope.population) && pending_bound(state,active);
    }
    bool bound(const std::shared_ptr<Pending>& state,bool active) {
        owner();if(!state || !state->native || !population_bound(state,active))return false;
        const auto session=state->connection.lock();const auto& lease=state->scope.lease;
        if(!presence->preparation_current(lease) || !population_bound(state,active) ||
           presence->ready(lease)!=active || !population_bound(state,active))return false;
        if(identity==TaiwanWorldEntryIdentity::QualifiedSceneHandle &&
           (state->cancelled || !state->native || session->closing() || session->id()!=lease.session ||
            session->account_id!=lease.account || session->character_id!=lease.character ||
            !session->recovered_world_ready() || session->recovered_client_language()!=state->scope.tail_language ||
            !pending.contains(lease.session) || pending.at(lease.session)!=state ||
            (active?!presence->retained_ready_current(lease):!presence->retained_preparation_current(lease))))return false;
        return population_bound(state,active);
    }
    bool current(const std::shared_ptr<Pending>& state,bool active,Entered::Check check) {
        if(!bound(state,active))return false;
        const auto material=state->native;
        bool observed=false;
        {
            const auto observe=material->current;
            if(!bound(state,active) || state->native!=material)return false;
            observed=observe(check,state->scope);
        } // A copied callback's destructor may cancel before the final fence.
        return observed && bound(state,active) && state->native==material;
    }
    void cancel(std::shared_ptr<Pending> state,Entered::Native* unpublished=nullptr) noexcept {
        if(std::this_thread::get_id()!=thread)std::terminate();
        // Erase/revoke before actual callbacks: late IO and nested completion
        // cannot retain affine payload or touch a successor generation.
        if(!state)return;
        if(state->cancelled) {
            if(unpublished)try {unpublished->cleanup(state->scope);}catch(...) {}
            return;
        }
        state->cancelled=true;
        state->outward_poisoned=true;
        if(state->scope.population)retire_population(*state->scope.population);
        // Keep the exact revoked Scope stable through an in-flight supplier
        // and its eventual returned-material cleanup; it grants no successor.
        const auto found=pending.find(state->scope.lease.session);
        if(found!=pending.end() && found->second==state)pending.erase(found);
        auto done=std::move(state->done);auto material=std::move(state->native);state->native.reset();
        state->incoming.reset();
        // Also cancels pending outward fanout. Its legacy transport callbacks
        // receive only our already-revoked weak Current, never native payload.
        try {visibility->release(state->scope.lease);}catch(...) {}
        if(material)try {material->cleanup(state->scope);}catch(...) {}
        if(unpublished && unpublished!=material.get())try {unpublished->cleanup(state->scope);}catch(...) {}
        if(done)try {done(false);}catch(...) {}
    }
    void fail(const std::shared_ptr<Pending>& state,Entered::Native* unpublished=nullptr) {
        owner();cancel(state,unpublished);
    }
    bool publish(const std::shared_ptr<Pending>& state) {
        owner();if(!state || state->published || !current(state,false,Entered::Check::BeforePublish))return false;
        const auto material=state->native;
        const auto session=state->connection.lock();const auto& lease=state->scope.lease;
        std::shared_ptr<Visibility::TaiwanInitialPublication> retained_incoming;
        if(identity==TaiwanWorldEntryIdentity::QualifiedSceneHandle) {
            retained_incoming=state->incoming;
            if(!visibility->taiwan_initial_current(retained_incoming,session,lease,false) ||
               !bound(state,false) || state->incoming!=retained_incoming)return false;
        }else if(!visibility->taiwan_initial_current(state->incoming,session,lease,false) ||
                 !bound(state,false))return false;
        bool installed=false;
        {
            const auto install=material->install;
            if(!bound(state,false) || state->native!=material)return false;
            installed=install(*session,state->scope);
        }
        if(!installed || state->cancelled || state->native!=material ||
           !current(state,false,Entered::Check::AfterInstall) || session->state()!=SessionState::InWorld ||
           !state->scope.population ||
           !activate_population(*state->scope.population,state->scope.entry.actor_handle))return false;
        session->bind_common_world_delivery_identity(lease.account,lease.character,lease.generation);
        if(!bound(state,true) || !visibility->publish_initial_taiwan(
           identity==TaiwanWorldEntryIdentity::QualifiedSceneHandle?retained_incoming:state->incoming,session,lease))return false;
        if(identity==TaiwanWorldEntryIdentity::QualifiedSceneHandle &&
           (!bound(state,true) || state->incoming!=retained_incoming))return false;
        state->published=true;return bound(state,true);
    }
    bool outward_mode(const Entered::Native& material) const noexcept {
        if(material.outward_decision==Entered::OutwardDecision::Supplied)return !material.outward_provider;
        return material.outward_decision==Entered::OutwardDecision::AfterInitialPublication &&
            material.outward.empty() && material.outward_provider && bool(*material.outward_provider);
    }
    void queued(const std::shared_ptr<Pending>& state,bool accepted) {
        owner();
        if(materializing) {
            materialization_reentered=true;
            if(state && !state->completed)fail(state);
            return;
        }
        if(!state || state->cancelled || state->completed)return;
        // Queue completion and every Current/copy/allocation below may reenter.
        // A second attempt is terminal, including while the provider is active.
        if(std::exchange(state->outward_started,true)) {fail(state);return;}
        try {
        const auto material=state->native;
        const auto session=state->connection.lock();
        if(!material || !session || !outward_mode(*material)) {fail(state);return;}
        const bool deferred=material->outward_decision==Entered::OutwardDecision::AfterInitialPublication;
        std::vector<Visibility::OutwardRecipient> outward;
        std::function<bool(Visibility::OutwardCheck)> outward_current;
        std::function<void(std::optional<std::vector<Visibility::Binding>>)> outward_done;
        const auto prepare=[&] {
            if(deferred) {materializing=true;materialization_reentered=false;}
            struct EndMaterializing {
                SceneOwner& owner;bool active;
                ~EndMaterializing(){if(active)owner.materializing=false;}
            } guard{*this,deferred};
            const std::weak_ptr<SceneOwner> weak_owner=shared_from_this();const std::weak_ptr<Pending> weak_state=state;
            // Allocate the sink callbacks before the last actual Current cuts.
            // They retain only revocable weak scene identities, never material.
            outward_current=[weak_owner,weak_state](Visibility::OutwardCheck) {
                const auto owner=weak_owner.lock();const auto pending=weak_state.lock();
                return owner && pending && owner->current(pending,true,Entered::Check::OutwardPublish);
            };
            outward_done=[weak_owner,weak_state](std::optional<std::vector<Visibility::Binding>> bindings) {
                const auto owner=weak_owner.lock();const auto pending=weak_state.lock();
                if(!owner || !pending || pending->cancelled || pending->completed)return;
                owner->owner();
                try {
                if(!bindings || !owner->current(pending,true,Entered::Check::Completed)) {owner->fail(pending);return;}
                pending->completed=true;auto done=std::move(pending->done);if(done)done(true);
                }catch(...) {owner->fail(pending);}
            };
            const auto released=material->decision==Entered::ReplyDecision::ExplicitNoInitialReply ?
                Entered::Check::LocalPublished:Entered::Check::QueueReleased;
            if(!accepted || !state->published || !current(state,true,released) ||
               !current(state,true,Entered::Check::BeforeOutward) || state->native!=material ||
               !outward_mode(*material))return false;
            if(deferred) {
                if(!current(state,true,Entered::Check::BeforeDeferredOutward) || state->native!=material ||
                   !outward_mode(*material))return false;
                {
                    // Shared immutable callback ownership survives cancellation
                    // of Native while the actual game-only provider is inside.
                    const auto provider=material->outward_provider;
                    if(!bound(state,true) || state->native!=material)return false;
                    auto observed=(*provider)(*session,state->scope);
                    if(!observed || observed->size()>256 || !bound(state,true) ||
                       state->native!=material || material->outward_provider!=provider ||
                       !outward_mode(*material))return false;
                    outward=std::move(*observed);
                } // Drop provider/result temporaries before final actual Current.
                if(!current(state,true,Entered::Check::AfterDeferredOutward) ||
                   state->native!=material || !outward_mode(*material))return false;
            }else outward=std::move(material->outward);
            return bound(state,true) && state->native==material;
        };
        if(!prepare() || !bound(state,true) || state->native!=material) {fail(state);return;}
        visibility->publish_outward_initial(state->scope.lease,std::move(outward),
            std::move(outward_current),std::move(outward_done));
        }catch(...) {fail(state);}
    }
    void enter(Session& session,const SharedWorldPresence::Lease& lease,
               const RecoveredWorldEntryView& entry,SharedTaiwanWorldLifecycle::ReadyCompletion done) {
        owner();if(!done)throw std::invalid_argument("TW entered completion required");
        if(supplying || materializing) {
            if(supplying)reentered=true;
            if(materializing)materialization_reentered=true;
            done(false);return;
        }
        if(pending.contains(lease.session) || session.id()!=lease.session || session.account_id!=lease.account ||
           session.character_id!=lease.character || entry.actor_handle!=lease.actor_handle ||
           entry.area!=lease.position.area || entry.scene!=lease.position.scene || entry.x!=lease.position.x ||
           entry.y!=lease.position.y || !presence->preparation_current(lease) || presence->ready(lease)) {done(false);return;}
        auto state=std::make_shared<Pending>(Pending{Entered::Scope{lease,entry,session.recovered_client_language()},
            session.weak_from_this(),{}, {},std::move(done)});
        pending.emplace(lease.session,state);
        try {
            supplying=true;reentered=false;
            struct EndSupply {SceneOwner& owner;~EndSupply(){owner.supplying=false;}} guard{*this};
            // The pending identity and reentry guard precede allocation and
            // actual repository observers. A cancelled capture never reaches
            // the real supplier or gains a later activation opportunity.
            if(!pending_bound(state,false)) {fail(state);return;}
            auto population=presence->observe_initial_population(lease);
            if(!population || !pending_bound(state,false) || population->joining().lease!=lease ||
               population->activated() || !presence->retained_initial_population_current(*population)) {
                if(population)retire_population(*population);
                fail(state);return;
            }
            state->scope.population=*population;
            if(!population_bound(state,false)) {fail(state);return;}
            auto native=source(session,state->scope);
            if(state->cancelled) {
                retire_population(*population);
                if(native)fail(state,&*native);
                return;
            }
            if(!native) {fail(state);return;}
            if(reentered || !population_bound(state,false) || !outward_mode(*native)) {fail(state,&*native);return;}
            std::shared_ptr<Entered::Native> retained_material;
            try {
                // Allocation precedes the noexcept Native move. Until it
                // succeeds the local optional still owns exact real cleanup.
                retained_material=std::make_shared<Entered::Native>(std::move(*native));
            }catch(...) {fail(state,&*native);throw;}
            native.reset(); // Drop moved-from callback values before adoption/current.
            if(reentered || !population_bound(state,false) || state->native) {
                fail(state,retained_material.get());return;
            }
            state->native=retained_material;
            if(!current(state,false,Entered::Check::AfterSupply) || state->native!=retained_material) {fail(state);return;}
            // Keep actual material alive through parser/vector allocations and
            // Visibility observers, even when cancellation clears Pending.
            auto& material=*retained_material;
            if(material.logical.size()>RecoveredTaiwanServerRecords::max_aggregate_logical_size ||
               material.incoming_offsets.size()!=material.incoming.size()) {fail(state);return;}
            if(material.decision==Entered::ReplyDecision::ExplicitNoInitialReply) {
                if(!material.logical.empty() || !material.incoming.empty() || !material.incoming_offsets.empty()) {fail(state);return;}
            }else if(material.decision!=Entered::ReplyDecision::CompleteNativeAggregate || material.logical.empty()) {fail(state);return;}
            std::optional<std::vector<RecoveredTaiwanServerRecords::Record>> native_records;
            if(material.decision==Entered::ReplyDecision::CompleteNativeAggregate) {
                native_records=RecoveredTaiwanServerRecords::read_aggregate(material.logical);
                if(!native_records) {fail(state);return;}
                // Inspect ALL actual initial boundaries before any queue. Never
                // drop or rewrite an overlapping native deity publication.
                if(deity_publisher==Entered::InitialDeityPublisher::ApplicationOwned &&
                   std::any_of(native_records->begin(),native_records->end(),[](const auto& record) {
                       return record.opcode==0x30 || record.opcode==0x31 ||
                              record.opcode==0x34 || record.opcode==0x35;
                   })) {fail(state);return;}
                // CUSTOM-0149 exclusive saved player/deity publisher. Keep the
                // old deity-only predicate unchanged and reject every actual
                // conflicting boundary before any initial queue/installation.
                if(deity_publisher==Entered::InitialDeityPublisher::ApplicationOwnedPlayerAndDeities &&
                   std::any_of(native_records->begin(),native_records->end(),[](const auto& record) {
                       return record.opcode==0x22 || record.opcode==0x24 ||
                              record.opcode==0x30 || record.opcode==0x31 ||
                              record.opcode==0x34 || record.opcode==0x35;
                   })) {fail(state);return;}
            }
            if(!population_bound(state,false)) {fail(state);return;}
            state->incoming=visibility->prepare_initial_taiwan_recipient(lease,session.shared_from_this(),std::move(material.incoming));
            if(!state->incoming || !current(state,false,Entered::Check::AfterSupply)) {fail(state);return;}
            const auto records=state->incoming->records();const auto supplied=state->incoming->supplied_records();
            std::size_t incoming_index=0;
            if(records.size()!=material.incoming_offsets.size() || supplied.size()!=records.size()) {fail(state);return;}
            // Walk the full aggregate, not only supplier-designated slices.
            // A6F inside opaque record payload is not a record boundary; an
            // actual6F boundary cannot be hidden, duplicated or omitted.
            if(native_records)for(const auto& native_record:*native_records) {
                if(native_record.opcode!=0x6f)continue;
                if(incoming_index>=records.size()) {fail(state);return;}
                const auto& record=records[incoming_index];
                if(native_record.offset!=material.incoming_offsets[incoming_index] ||
                   native_record.bytes.size()!=RecoveredRemoteActor::logical_size ||
                   record.size()!=RecoveredRemoteActor::logical_size || supplied[incoming_index].size()!=record.size() ||
                   (!std::equal(supplied[incoming_index].begin(),supplied[incoming_index].end(),native_record.bytes.begin()) &&
                    !std::equal(record.begin(),record.end(),native_record.bytes.begin()))) {fail(state);return;}
                ++incoming_index;
            }
            if(incoming_index!=records.size()) {fail(state);return;}
            // Match every real6F full input or its exact prepared projection, then splice only
            // the equal-sized common-name projections; all other bytes remain.
            for(std::size_t i=0;i<records.size();++i)
                std::copy(records[i].begin(),records[i].end(),material.logical.begin()+material.incoming_offsets[i]);
            if(!current(state,false,Entered::Check::BeforeQueue)) {fail(state);return;}
            // Every asynchronous callback carries only revocable weak tokens.
            // Native ownership remains in pending until game cleanup/cancel.
            std::weak_ptr<SceneOwner> weak_owner=shared_from_this();std::weak_ptr<Pending> weak_state=state;
            auto publication=[weak_owner,weak_state] {
                const auto owner=weak_owner.lock();const auto pending=weak_state.lock();
                return owner && pending && owner->publish(pending);
            };
            auto queued=[weak_owner,weak_state](bool accepted) {
                const auto owner=weak_owner.lock();const auto pending=weak_state.lock();
                if(owner && pending)owner->queued(pending,accepted);
            };
            if(material.decision==Entered::ReplyDecision::ExplicitNoInitialReply) {
                // Actual source explicitly chose no initial bytes. This is
                // local publication only, never a fabricated queue/native ACK.
                queued(publication());
            }else session.send_common_world_entry_with_publication(std::move(material.logical),
                lease.account,lease.character,lease.generation,std::move(publication),std::move(queued));
        }catch(...) {supplying=false;fail(state);throw;}
    }
};
}
SharedTaiwanWorldEntered::Native::Native(ReplyDecision selected,std::vector<std::uint8_t> bytes,
    std::vector<std::size_t> offsets,std::vector<Visibility::InitialTaiwanActor> actors,
    std::vector<Visibility::OutwardRecipient> observers,Current observe,Install commit,Cleanup release)
    :decision(selected),logical(std::move(bytes)),incoming_offsets(std::move(offsets)),incoming(std::move(actors)),
     outward(std::move(observers)),current(std::move(observe)),install(std::move(commit)),cleanup(std::move(release)) {
    if(!current || !install || !cleanup)throw std::invalid_argument("TW entered requires actual Current/scene install/cleanup");
}
SharedTaiwanWorldEntered::Native::Native(ReplyDecision selected,std::vector<std::uint8_t> bytes,
    std::vector<std::size_t> offsets,std::vector<Visibility::InitialTaiwanActor> actors,
    OutwardDecision outward_selected,OutwardProvider provider,Current observe,Install commit,Cleanup release)
    :decision(selected),logical(std::move(bytes)),incoming_offsets(std::move(offsets)),incoming(std::move(actors)),
     current(std::move(observe)),install(std::move(commit)),cleanup(std::move(release)),
     outward_decision(outward_selected),outward_provider(std::make_shared<const OutwardProvider>(std::move(provider))) {
    if(outward_decision!=OutwardDecision::AfterInitialPublication || !*outward_provider ||
       !current || !install || !cleanup)
        throw std::invalid_argument("TW deferred outward requires explicit post-publication provider and actual scene owners");
}
SharedTaiwanWorldLifecycle::AsyncOwner SharedTaiwanWorldEntered::create(
    std::shared_ptr<SharedWorldPresence> presence,std::shared_ptr<Visibility> visibility,Source source,
    TaiwanWorldEntryIdentity identity,InitialDeityPublisher deity_publisher) {
    if((deity_publisher!=InitialDeityPublisher::External && deity_publisher!=InitialDeityPublisher::ApplicationOwned &&
        deity_publisher!=InitialDeityPublisher::ApplicationOwnedPlayerAndDeities) ||
       !valid_taiwan_world_entry_identity(identity) || !presence || !visibility || !source || !visibility->owns_presence(presence))
        throw std::invalid_argument("TW entered requires exact common owners and actual native scene supplier");
    auto state=std::make_shared<SceneOwner>();state->presence=std::move(presence);
    state->visibility=std::move(visibility);state->source=std::move(source);state->identity=identity;
    state->deity_publisher=deity_publisher;
    // Access is lexical to this friend class, not the anonymous SceneOwner or
    // any native supplier. Capture only the actual Presence and identity mode.
    state->activate_population=[presence=state->presence,identity](
            const SharedWorldPresence::InitialPopulation& population,std::uint16_t handle) {
        return presence->activate_initial_population(population,handle,identity);
    };
    state->retire_population=[presence=state->presence](
            const SharedWorldPresence::InitialPopulation& population) noexcept {
        presence->retire_initial_population(population);
    };
    return {
        [state](Session& session,const Lease& lease,const RecoveredWorldEntryView& entry,
                SharedTaiwanWorldLifecycle::ReadyCompletion done) {state->enter(session,lease,entry,std::move(done));},
        [state](Session& session,const Lease& lease) {
            state->owner();const auto found=state->pending.find(lease.session);
            if(found!=state->pending.end() && found->second->scope.lease==lease &&
               found->second->connection.lock().get()==&session)state->cancel(found->second);
        }
    };
}
}
