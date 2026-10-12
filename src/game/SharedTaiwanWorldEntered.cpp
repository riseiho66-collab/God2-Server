#include "game/SharedTaiwanWorldEntered.h"
#include "protocol/RecoveredTaiwanServerRecords.h"
#include "protocol/RecoveredWorldFrame.h"
#include <algorithm>
#include <map>
#include <stdexcept>
#include <thread>
#include <utility>

namespace god2 {
namespace {
using Entered=SharedTaiwanWorldEntered;
using Visibility=cn::SharedActorVisibility;
struct Pending {
    Entered::Scope scope;
    std::weak_ptr<Session> connection;
    std::optional<Entered::Native> native;
    std::shared_ptr<Visibility::TaiwanInitialPublication> incoming;
    SharedTaiwanWorldLifecycle::ReadyCompletion done;
    bool cancelled=false,published=false,completed=false;
};
struct SceneOwner:std::enable_shared_from_this<SceneOwner> {
    std::shared_ptr<SharedWorldPresence> presence;
    std::shared_ptr<Visibility> visibility;
    Entered::Source source;
    TaiwanWorldEntryIdentity identity=TaiwanWorldEntryIdentity::SelectedCharacter;
    const std::thread::id thread=std::this_thread::get_id();
    std::map<std::uint64_t,std::shared_ptr<Pending>> pending;
    bool supplying=false,reentered=false;
    void owner() const {
        if(std::this_thread::get_id()!=thread)throw std::logic_error("TW scene publication game owner mismatch");
    }
    ~SceneOwner() {
        if(std::this_thread::get_id()!=thread)std::terminate();
        while(!pending.empty())cancel(pending.begin()->second);
    }
    bool bound(const std::shared_ptr<Pending>& state,bool active) {
        owner();if(!state || state->cancelled || !state->native || (supplying && reentered))return false;
        const auto found=pending.find(state->scope.lease.session);
        const auto session=state->connection.lock();const auto& lease=state->scope.lease;
        if(found==pending.end() || found->second!=state || !session || session->closing() ||
           session->id()!=lease.session || session->account_id!=lease.account || session->character_id!=lease.character ||
           !session->recovered_world_ready() || session->recovered_client_language()!=state->scope.tail_language ||
           !presence->preparation_current(lease) || presence->ready(lease)!=active)return false;
        if(identity==TaiwanWorldEntryIdentity::QualifiedSceneHandle &&
           (state->cancelled || !state->native || session->closing() || session->id()!=lease.session ||
            session->account_id!=lease.account || session->character_id!=lease.character ||
            !session->recovered_world_ready() || session->recovered_client_language()!=state->scope.tail_language ||
            !pending.contains(lease.session) || pending.at(lease.session)!=state ||
            (active?!presence->retained_ready_current(lease):!presence->retained_preparation_current(lease))))return false;
        if(active)return session->state()==SessionState::InWorld &&
            session->common_world_delivery_current(lease.account,lease.character,lease.generation);
        return (session->state()==SessionState::CharacterSelected || session->state()==SessionState::InWorld) &&
            session->common_world_entry_current(lease.account,lease.character,lease.generation) &&
            !session->common_world_delivery_current(lease.account,lease.character,lease.generation);
    }
    bool current(const std::shared_ptr<Pending>& state,bool active,Entered::Check check) {
        if(!bound(state,active))return false;
        const auto observe=state->native->current;
        return observe(check,state->scope) && bound(state,active);
    }
    void cancel(std::shared_ptr<Pending> state) noexcept {
        if(std::this_thread::get_id()!=thread)std::terminate();
        // Erase/revoke before actual callbacks: late IO and nested completion
        // cannot retain affine payload or touch a successor generation.
        if(!state || state->cancelled)return;
        state->cancelled=true;
        const auto found=pending.find(state->scope.lease.session);
        if(found!=pending.end() && found->second==state)pending.erase(found);
        auto done=std::move(state->done);auto material=std::move(state->native);state->native.reset();
        state->incoming.reset();
        // Also cancels pending outward fanout. Its legacy transport callbacks
        // receive only our already-revoked weak Current, never native payload.
        try {visibility->release(state->scope.lease);}catch(...) {}
        if(material)try {material->cleanup(state->scope);}catch(...) {}
        if(done)try {done(false);}catch(...) {}
    }
    void fail(const std::shared_ptr<Pending>& state) {
        owner();cancel(state);
    }
    bool publish(const std::shared_ptr<Pending>& state) {
        owner();if(!state || state->published || !current(state,false,Entered::Check::BeforePublish))return false;
        const auto session=state->connection.lock();const auto& lease=state->scope.lease;
        std::shared_ptr<Visibility::TaiwanInitialPublication> retained_incoming;
        if(identity==TaiwanWorldEntryIdentity::QualifiedSceneHandle) {
            retained_incoming=state->incoming;
            if(!visibility->taiwan_initial_current(retained_incoming,session,lease,false) ||
               !bound(state,false) || state->incoming!=retained_incoming)return false;
        }else if(!visibility->taiwan_initial_current(state->incoming,session,lease,false))return false;
        const auto install=state->native->install;
        if(!install(*session,state->scope) || state->cancelled ||
           !current(state,false,Entered::Check::AfterInstall) || session->state()!=SessionState::InWorld ||
           !(identity==TaiwanWorldEntryIdentity::QualifiedSceneHandle?
             presence->activate_qualified_scene(lease,state->scope.entry.actor_handle):
             presence->activate(lease,state->scope.entry.actor_handle)))return false;
        session->bind_common_world_delivery_identity(lease.account,lease.character,lease.generation);
        if(!bound(state,true) || !visibility->publish_initial_taiwan(
           identity==TaiwanWorldEntryIdentity::QualifiedSceneHandle?retained_incoming:state->incoming,session,lease))return false;
        if(identity==TaiwanWorldEntryIdentity::QualifiedSceneHandle &&
           (!bound(state,true) || state->incoming!=retained_incoming))return false;
        state->published=true;return bound(state,true);
    }
    void queued(const std::shared_ptr<Pending>& state,bool accepted) {
        owner();if(!state || state->cancelled || state->completed)return;
        try {
        const auto released=state->native->decision==Entered::ReplyDecision::ExplicitNoInitialReply ?
            Entered::Check::LocalPublished:Entered::Check::QueueReleased;
        if(!accepted || !state->published || !current(state,true,released) ||
           !current(state,true,Entered::Check::BeforeOutward)) {fail(state);return;}
        const std::weak_ptr<SceneOwner> weak_owner=shared_from_this();const std::weak_ptr<Pending> weak_state=state;
        visibility->publish_outward_initial(state->scope.lease,std::move(state->native->outward),
            [weak_owner,weak_state](Visibility::OutwardCheck) {
                const auto owner=weak_owner.lock();const auto pending=weak_state.lock();
                return owner && pending && owner->current(pending,true,Entered::Check::OutwardPublish);
            },[weak_owner,weak_state](std::optional<std::vector<Visibility::Binding>> bindings) {
                const auto owner=weak_owner.lock();const auto pending=weak_state.lock();
                if(!owner || !pending || pending->cancelled || pending->completed)return;
                owner->owner();
                try {
                if(!bindings || !owner->current(pending,true,Entered::Check::Completed)) {owner->fail(pending);return;}
                pending->completed=true;auto done=std::move(pending->done);if(done)done(true);
                }catch(...) {owner->fail(pending);}
            });
        }catch(...) {fail(state);}
    }
    void enter(Session& session,const SharedWorldPresence::Lease& lease,
               const RecoveredWorldEntryView& entry,SharedTaiwanWorldLifecycle::ReadyCompletion done) {
        owner();if(!done)throw std::invalid_argument("TW entered completion required");
        if(supplying) {reentered=true;done(false);return;}
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
            auto native=source(session,state->scope);
            if(state->cancelled) {
                if(native)try {native->cleanup(state->scope);}catch(...) {}
                return;
            }
            if(native)state->native=std::move(*native);
            if(reentered || !native || !current(state,false,Entered::Check::AfterSupply)) {fail(state);return;}
            auto& material=*state->native;
            if(material.logical.size()>RecoveredWorldFrame::max_logical_size ||
               material.incoming_offsets.size()!=material.incoming.size()) {fail(state);return;}
            if(material.decision==Entered::ReplyDecision::ExplicitNoInitialReply) {
                if(!material.logical.empty() || !material.incoming.empty() || !material.incoming_offsets.empty()) {fail(state);return;}
            }else if(material.decision!=Entered::ReplyDecision::CompleteNativeAggregate || material.logical.empty()) {fail(state);return;}
            std::optional<std::vector<RecoveredTaiwanServerRecords::Record>> native_records;
            if(material.decision==Entered::ReplyDecision::CompleteNativeAggregate) {
                native_records=RecoveredTaiwanServerRecords::read(material.logical);
                if(!native_records) {fail(state);return;}
            }
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
SharedTaiwanWorldLifecycle::AsyncOwner SharedTaiwanWorldEntered::create(
    std::shared_ptr<SharedWorldPresence> presence,std::shared_ptr<Visibility> visibility,Source source,
    TaiwanWorldEntryIdentity identity) {
    if(!valid_taiwan_world_entry_identity(identity) || !presence || !visibility || !source || !visibility->owns_presence(presence))
        throw std::invalid_argument("TW entered requires exact common owners and actual native scene supplier");
    auto state=std::make_shared<SceneOwner>();state->presence=std::move(presence);
    state->visibility=std::move(visibility);state->source=std::move(source);state->identity=identity;
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
