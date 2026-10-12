#include "game/SharedTaiwanWorldLifecycle.h"
#include <stdexcept>
#include <utility>

namespace god2 {
void SharedTaiwanWorldLifecycle::Binding::owner() const {
    if(thread!=std::this_thread::get_id())throw std::logic_error("TW common lifecycle game owner mismatch");
}
bool SharedTaiwanWorldLifecycle::Binding::current(Session& session) const {
    owner();
    if(identity==TaiwanWorldEntryIdentity::QualifiedSceneHandle) {
        if(!lease || stage==Stage::Fresh || stage==Stage::Released)return false;
        const auto pinned=connection.lock();const auto registry=presence;const auto expected=*lease;const auto phase=stage;
        const auto matches=[&] {
            return stage==phase && lease && *lease==expected && pinned.get()==&session && !session.closing() &&
                session.id()==expected.session && session.account_id==expected.account && session.character_id==expected.character;
        };
        if(!matches() || !registry->preparation_current(expected) || !matches())return false;
        return phase==Stage::Prepared?registry->retained_preparation_current(expected):registry->retained_ready_current(expected);
    }
    return lease && connection.lock().get()==&session && !session.closing() &&
        session.id()==lease->session && session.account_id==lease->account &&
        session.character_id==lease->character && presence->preparation_current(*lease);
}
void SharedTaiwanWorldLifecycle::Binding::release() {
    owner();if(stage==Stage::Released)return;stage=Stage::Released;
    if(!lease)return;
    if(transport_token) {transports->release(*transport_token);transport_token.reset();}
    if(const auto session=connection.lock())
        session->release_common_world_delivery_identity(lease->account,lease->character,lease->generation);
    // Both owners get cleanup even if visibility/native output fails. Session
    // independently invokes its existing disconnect callback afterwards.
    std::exception_ptr failure;
    try {visibility->release(*lease);}catch(...){failure=std::current_exception();}
    try {presence->release(*lease);}catch(...){if(!failure)failure=std::current_exception();}
    if(failure)std::rethrow_exception(failure);
}
bool SharedTaiwanWorldLifecycle::Binding::prepare(Session& session,const RecoveredWorldEntry::Frame& wire) {
    owner();if(stage!=Stage::Fresh || session.closing() || !session.account_id || !session.character_id)return false;
    const auto full=RecoveredWorldEntryView::read(wire);
    if(!full || !valid_taiwan_world_entry_identity(identity) ||
       (identity==TaiwanWorldEntryIdentity::SelectedCharacter && session.character_id!=full->actor_handle) ||
       (identity==TaiwanWorldEntryIdentity::QualifiedSceneHandle && !qualified_taiwan_scene_handle(full->actor_handle)))return false;
    // Default mode keeps the existing selected-character preparation behavior.
    if(identity==TaiwanWorldEntryIdentity::SelectedCharacter) {
        const auto prepared=presence->prepare_geometry(session.id(),session.account_id,session.character_id,
            full->actor_handle,full->area,full->scene,full->x,full->y);
        if(!prepared)return false;
        lease=*prepared;entry=*full;connection=session.shared_from_this();stage=Stage::Prepared;
        return true;
    }
    const auto pinned=session.shared_from_this();
    const auto account=session.account_id,character=session.character_id;
    const auto registry=presence;
    // Geometry is compared to common saved position including its actual DB
    // revision. The wire has no revision; the real repository supplies it.
    // prepare() requires exact saved geometry and ownership, not guessed placement.
    // Load through the existing selected-character repository via a qualification
    // method; no storage write or initial position default is permitted here.
    const auto prepared=registry->prepare_geometry(session.id(),account,character,
        full->actor_handle,full->area,full->scene,full->x,full->y);
    if(!prepared)return false;
    if(stage!=Stage::Fresh || session.closing() || session.account_id!=account || session.character_id!=character ||
       !registry->retained_preparation_current(*prepared)) {
        registry->release(*prepared);return false;
    }
    lease=*prepared;entry=*full;connection=pinned;stage=Stage::Prepared;
    return true;
}
std::optional<std::uint16_t> SharedTaiwanWorldLifecycle::Binding::prepared_actor(
    Session& session,const RecoveredWorldEntry::Frame& wire) const {
    owner();
    if(identity!=TaiwanWorldEntryIdentity::QualifiedSceneHandle || stage!=Stage::Prepared || !lease || !entry)return std::nullopt;
    // Keep owning copies across virtual repository observers. Cleanup may be
    // reentered there; no optional member reference crosses that boundary.
    const auto pinned=connection.lock();const auto registry=presence;
    const auto expected=*lease;const auto retained=*entry;const auto supplied=wire;
    const auto matches=[&] {
        return stage==Stage::Prepared && lease && *lease==expected && entry && entry->wire==retained.wire &&
            supplied==retained.wire && pinned.get()==&session && !session.closing() &&
            session.id()==expected.session && session.account_id==expected.account && session.character_id==expected.character &&
            expected.actor_handle==retained.actor_handle && qualified_taiwan_scene_handle(expected.actor_handle) &&
            expected.position.area==retained.area && expected.position.scene==retained.scene &&
            expected.position.x==retained.x && expected.position.y==retained.y;
    };
    if(!matches() || !registry->preparation_current(expected) || !matches() ||
       !registry->retained_preparation_current(expected))return std::nullopt;
    return expected.actor_handle;
}
bool SharedTaiwanWorldLifecycle::Binding::ready(Session& session) {
    owner();
    if(stage!=Stage::Prepared || !current(session) || !session.recovered_world_ready() ||
       !entry || !(identity==TaiwanWorldEntryIdentity::QualifiedSceneHandle?
           presence->activate_qualified_scene(*lease,entry->actor_handle):presence->activate(*lease,entry->actor_handle)))return false;
    if(identity==TaiwanWorldEntryIdentity::QualifiedSceneHandle && stage!=Stage::Prepared)return false;
    stage=Stage::Entering;
    bool accepted=false;
    try {accepted=entered(session,*lease,*entry);}catch(...){release();throw;}
    if(!accepted || stage!=Stage::Entering || !current(session) ||
       !(identity==TaiwanWorldEntryIdentity::QualifiedSceneHandle?presence->retained_ready_current(*lease):presence->ready(*lease)) ||
       (identity==TaiwanWorldEntryIdentity::QualifiedSceneHandle && stage!=Stage::Entering) || session.state()!=SessionState::InWorld) {release();return false;}
    try {session.bind_common_world_delivery_identity(lease->account,lease->character,lease->generation);}
    catch(...) {release();throw;}
    if(transports) {
        const auto registered=transports->bind(*lease,session.shared_from_this());
        if(!registered) {release();return false;}
        if(stage!=Stage::Entering) {transports->release(*registered);release();return false;}
        transport_token=*registered;
        if(!current(session) || stage!=Stage::Entering || !transport_token ||
           !transports->current(*registered) || stage!=Stage::Entering || !transport_token) {
            transports->release(*registered);release();return false;
        }
    }
    if(identity==TaiwanWorldEntryIdentity::QualifiedSceneHandle && !presence->retained_ready_current(*lease)) {release();return false;}
    stage=Stage::Ready;return true;
}
std::shared_ptr<const Session::CommonWorldLifecycle> SharedTaiwanWorldLifecycle::hooks(
    std::shared_ptr<SharedWorldPresence> presence,std::shared_ptr<cn::SharedActorVisibility> visibility,Entered entered,
    std::shared_ptr<SharedNativeWorldTransports> transports,TaiwanWorldEntryIdentity identity) {
    if(!valid_taiwan_world_entry_identity(identity) || !presence || !visibility || !entered || !visibility->owns_presence(presence) ||
       (transports && !transports->owns_presence(presence)))return {};
    auto binding=std::make_shared<Binding>();binding->presence=std::move(presence);
    binding->visibility=std::move(visibility);binding->entered=std::move(entered);binding->transports=std::move(transports);binding->identity=identity;
    auto result=std::make_shared<Session::CommonWorldLifecycle>();
    result->prepared=[binding](Session& session,const RecoveredWorldEntry::Frame& frame) {
        try {
            if(!binding->prepare(session,frame))return false;
            if(!session.install_common_world_cleanup([binding]{binding->release();})) {
                binding->release();return false;
            }
            return true;
        }catch(...) {binding->release();throw;}
    };
    if(identity==TaiwanWorldEntryIdentity::QualifiedSceneHandle)
        result->prepared_actor=[binding](Session& session,const RecoveredWorldEntry::Frame& frame) {return binding->prepared_actor(session,frame);};
    result->ready=[binding](Session& session) {return binding->ready(session);};
    return result;
}
Session::CommonWorldLifecycleFactory SharedTaiwanWorldLifecycle::factory(
    std::shared_ptr<SharedWorldPresence> presence,std::shared_ptr<cn::SharedActorVisibility> visibility,Entered entered,
    std::shared_ptr<SharedNativeWorldTransports> transports,TaiwanWorldEntryIdentity identity) {
    if(!valid_taiwan_world_entry_identity(identity) || !presence || !visibility || !entered || !visibility->owns_presence(presence) ||
       (transports && !transports->owns_presence(presence)))
        throw std::invalid_argument("TW common lifecycle factory requires actual presence/visibility/scene owner");
    return [presence=std::move(presence),visibility=std::move(visibility),entered=std::move(entered),transports=std::move(transports),identity](Session&) {
        return hooks(presence,visibility,entered,transports,identity); // Fresh Binding on this Session's game owner.
    };
}
void SharedTaiwanWorldLifecycle::AsyncBinding::release() {
    base.owner();if(released)return;released=true;
    auto completion=std::move(done);std::exception_ptr failure;
    if(base.lease) {
        if(const auto session=base.connection.lock()) {
            session->release_common_world_entry_identity(base.lease->account,base.lease->character,base.lease->generation);
            try {scene.cancel(*session,*base.lease);}catch(...) {failure=std::current_exception();}
        }
    }
    try {base.release();}catch(...) {if(!failure)failure=std::current_exception();}
    if(completion)try {completion(false);}catch(...) {}
    if(failure)std::rethrow_exception(failure);
}
void SharedTaiwanWorldLifecycle::AsyncBinding::complete(bool accepted) {
    base.owner();if(released || !done)return;
    if(invoking) {
        // Inline completion is not exposed until the actual provider returns.
        // A throw after completion or duplicate inline result rejects once.
        if(inline_result)inline_result=false;else inline_result=accepted;
        return;
    }
    try {
    const auto session=base.connection.lock();
    if(!accepted || !session || base.stage!=Stage::Entering || !base.current(*session) ||
       !(base.identity==TaiwanWorldEntryIdentity::QualifiedSceneHandle?
           base.presence->retained_ready_current(*base.lease):base.presence->ready(*base.lease)) ||
       (base.identity==TaiwanWorldEntryIdentity::QualifiedSceneHandle && (released || !done || base.stage!=Stage::Entering)) || session->state()!=SessionState::InWorld ||
       !session->common_world_delivery_current(base.lease->account,base.lease->character,base.lease->generation)) {
        release();return;
    }
    session->release_common_world_entry_identity(base.lease->account,base.lease->character,base.lease->generation);
    if(base.transports) {
        const auto registered=base.transports->bind(*base.lease,session);
        if(!registered) {release();return;}
        if(released || !done || base.stage!=Stage::Entering) {base.transports->release(*registered);release();return;}
        base.transport_token=*registered;
        if(!base.current(*session) || released || !done || base.stage!=Stage::Entering || !base.transport_token ||
           !base.transports->current(*registered) || released || !done || base.stage!=Stage::Entering || !base.transport_token) {
            base.transports->release(*registered);release();return;
        }
    }
    if(base.identity==TaiwanWorldEntryIdentity::QualifiedSceneHandle && !base.presence->retained_ready_current(*base.lease)) {release();return;}
    base.stage=Stage::Ready;auto completion=std::move(done);completion(true);
    }catch(...) {release();throw;}
}
void SharedTaiwanWorldLifecycle::AsyncBinding::ready(Session& session,ReadyCompletion completion) {
    base.owner();if(!completion)throw std::invalid_argument("TW asynchronous ready completion required");
    if(released || done || base.stage!=Stage::Prepared || !base.current(session) ||
       !session.recovered_world_ready() || !base.entry || base.presence->ready(*base.lease)) {
        completion(false);return;
    }
    if(base.identity==TaiwanWorldEntryIdentity::QualifiedSceneHandle && (released || base.stage!=Stage::Prepared)) {
        completion(false);return;
    }
    done=std::move(completion);base.stage=Stage::Entering;
    try {
        session.bind_common_world_entry_identity(base.lease->account,base.lease->character,base.lease->generation);
        std::weak_ptr<AsyncBinding> weak=shared_from_this();
        invoking=true;
        scene.entered(session,*base.lease,*base.entry,[weak](bool accepted) {
            if(const auto binding=weak.lock())binding->complete(accepted);
        });
        invoking=false;
        if(inline_result) {const auto result=*inline_result;inline_result.reset();complete(result);}
    }catch(...) {invoking=false;inline_result.reset();release();throw;}
}
std::shared_ptr<const Session::CommonWorldLifecycle> SharedTaiwanWorldLifecycle::hooks_async(
    std::shared_ptr<SharedWorldPresence> presence,std::shared_ptr<cn::SharedActorVisibility> visibility,AsyncOwner scene,
    std::shared_ptr<SharedNativeWorldTransports> transports,TaiwanWorldEntryIdentity identity) {
    if(!valid_taiwan_world_entry_identity(identity) || !presence || !visibility || !scene.entered || !scene.cancel || !visibility->owns_presence(presence) ||
       (transports && !transports->owns_presence(presence)))return {};
    auto binding=std::make_shared<AsyncBinding>();binding->base.presence=std::move(presence);
    binding->base.visibility=std::move(visibility);binding->scene=std::move(scene);binding->base.transports=std::move(transports);binding->base.identity=identity;
    auto result=std::make_shared<Session::CommonWorldLifecycle>();
    result->prepared=[binding](Session& session,const RecoveredWorldEntry::Frame& frame) {
        try {
            if(!binding->base.prepare(session,frame))return false;
            if(!session.install_common_world_cleanup([binding]{binding->release();})) {
                binding->release();return false;
            }
            return true;
        }catch(...) {binding->release();throw;}
    };
    if(identity==TaiwanWorldEntryIdentity::QualifiedSceneHandle)
        result->prepared_actor=[binding](Session& session,const RecoveredWorldEntry::Frame& frame)->std::optional<std::uint16_t> {
            binding->base.owner();if(binding->released)return std::nullopt;
            const auto actor=binding->base.prepared_actor(session,frame);
            return binding->released?std::nullopt:actor;
        };
    result->ready_async=[binding](Session& session,ReadyCompletion done) {binding->ready(session,std::move(done));};
    result->cancel=[binding](Session& session) {
        binding->base.owner();
        if(!binding->base.lease)return;
        const auto& lease=*binding->base.lease;
        if(binding->base.connection.lock().get()!=&session || session.id()!=lease.session ||
           session.account_id!=lease.account || session.character_id!=lease.character)
            throw std::invalid_argument("TW asynchronous cancellation identity mismatch");
        binding->release();
    };
    return result;
}
Session::CommonWorldLifecycleFactory SharedTaiwanWorldLifecycle::factory_async(
    std::shared_ptr<SharedWorldPresence> presence,std::shared_ptr<cn::SharedActorVisibility> visibility,AsyncOwner scene,
    std::shared_ptr<SharedNativeWorldTransports> transports,TaiwanWorldEntryIdentity identity) {
    if(!valid_taiwan_world_entry_identity(identity) || !presence || !visibility || !scene.entered || !scene.cancel || !visibility->owns_presence(presence) ||
       (transports && !transports->owns_presence(presence)))
        throw std::invalid_argument("TW asynchronous lifecycle requires actual scene owner and cancellation");
    return [presence=std::move(presence),visibility=std::move(visibility),scene=std::move(scene),transports=std::move(transports),identity](Session&) {
        return hooks_async(presence,visibility,scene,transports,identity);
    };
}
}
