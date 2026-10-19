#include "game/SharedTaiwanWorldLifecycle.h"
#include <stdexcept>
#include <utility>

namespace god2 {
SharedTaiwanWorldLifecycle::Binding::~Binding() { retire_status_incarnation(); }
void SharedTaiwanWorldLifecycle::Binding::retire_status_incarnation() noexcept {
    if(status_incarnations&&status_incarnation)status_incarnations->retire(*status_incarnation);
    status_incarnation.reset(); // No visibility/presence/game callback from destructor.
}
bool SharedTaiwanWorldLifecycle::Binding::admit_status_incarnation(Session& session) {
    if(!status_incarnations)return true;
    if(stage!=Stage::Prepared||!lease||connection.lock().get()!=&session)return false;
    const auto expected=*lease;const auto source=status_incarnations;
    const auto token=source->prepare(session,expected);
    if(!token)return false;
    // Keep owning copies across Session's allocation/new_handler boundary.
    if(stage!=Stage::Prepared||!lease||*lease!=expected||status_incarnations!=source||
       connection.lock().get()!=&session||!source->retained(*token)) {
        source->retire(*token);return false;
    }
    status_incarnation=*token;
    if(!session.bind_actor_status_incarnation(*token)||stage!=Stage::Prepared||!lease||
       *lease!=expected||status_incarnations!=source||!status_incarnation||
       *status_incarnation!=*token||connection.lock().get()!=&session||!source->current(*token)) {
        source->retire(*token);return false;
    }
    return true;
}
void SharedTaiwanWorldLifecycle::Binding::owner() const {
    if(thread!=std::this_thread::get_id())throw std::logic_error("TW common lifecycle game owner mismatch");
}
bool SharedTaiwanWorldLifecycle::Binding::current(Session& session) const {
    owner();
    if(!session.native_channel_allows_presence(presence))return false;
    if(status_incarnations&&(!status_incarnation||!status_incarnations->current(*status_incarnation)))return false;
    if(identity==TaiwanWorldEntryIdentity::QualifiedSceneHandle) {
        if(!lease || stage==Stage::Fresh || stage==Stage::Released)return false;
        const auto pinned=connection.lock();const auto registry=presence;const auto expected=*lease;const auto phase=stage;
        const auto matches=[&] {
            return stage==phase && lease && *lease==expected && pinned.get()==&session && !session.closing() &&
                session.id()==expected.session && session.account_id==expected.account && session.character_id==expected.character&&
                session.native_channel_allows_presence(registry);
        };
        if(!matches() || !registry->preparation_current(expected) || !matches())return false;
        return phase==Stage::Prepared?registry->retained_preparation_current(expected):registry->retained_ready_current(expected);
    }
    return lease && connection.lock().get()==&session && !session.closing() &&
        session.id()==lease->session && session.account_id==lease->account &&
        session.character_id==lease->character && presence->preparation_current(*lease)&&
        session.native_channel_allows_presence(presence);
}
void SharedTaiwanWorldLifecycle::Binding::fail_terminal() noexcept {
    terminal_failed=true;
    if(const auto session=connection.lock())session->mark_common_world_cleanup_failed();
}
void SharedTaiwanWorldLifecycle::Binding::arm_terminal_retirement() {
    owner();
    if(!lease)return;
    if(terminal_attempted) {
        if(!terminal_retirement)throw std::logic_error("TW terminal claim acquisition failed");
        return;
    }
    // Set before allocation/reentry. Presence marks the exact claim first, so
    // failed token allocation also remains occupied without a recovery grant.
    terminal_attempted=true;
    try {
        terminal_retirement=presence->begin_terminal_retirement(*lease);
        if(!terminal_retirement)throw std::logic_error("TW terminal claim not retained");
    }catch(...) {fail_terminal();throw;}
}
void SharedTaiwanWorldLifecycle::Binding::begin_terminal(Session& session) {
    owner();
    if(!lease || connection.lock().get()!=&session || session.id()!=lease->session ||
       session.account_id!=lease->account || session.character_id!=lease->character || terminal_finished) {
        fail_terminal();throw std::logic_error("TW terminal cleanup source mismatch");
    }
    arm_terminal_retirement();
}
bool SharedTaiwanWorldLifecycle::Binding::finish_terminal(Session& session,bool clean) {
    owner();
    if(terminal_finished)return false;
    terminal_finished=true;
    const bool exact=lease && connection.lock().get()==&session && session.id()==lease->session &&
        session.account_id==lease->account && session.character_id==lease->character;
    clean=clean && exact && terminal_attempted && !terminal_failed && stage==Stage::Released;
    if(!terminal_retirement){fail_terminal();return false;}
    try {
        const bool released=presence->finish_terminal_retirement(*terminal_retirement,clean);
        if(!released)fail_terminal();
        return released;
    }catch(...) {fail_terminal();throw;}
}
void SharedTaiwanWorldLifecycle::Binding::release() {
    owner();retire_status_incarnation();
    std::exception_ptr failure;
    // Early async cancellation adopts this same hold when Session cleans later.
    try {arm_terminal_retirement();}catch(...) {failure=std::current_exception();}
    if(stage==Stage::Released) {
        if(failure)std::rethrow_exception(failure);
        if(terminal_failed)throw std::logic_error("TW earlier terminal cleanup failed");
        return;
    }
    stage=Stage::Released;
    if(!lease){if(failure)std::rethrow_exception(failure);return;}
    const auto expected=*lease;
    if(transport_token) {
        const auto token=*transport_token;transport_token.reset();
        try {transports->release(token);}catch(...) {if(!failure)failure=std::current_exception();}
    }
    try {if(const auto session=connection.lock())
        session->release_common_world_delivery_identity(expected.account,expected.character,expected.generation);
    }catch(...) {if(!failure)failure=std::current_exception();}
    try {visibility->release(expected);}catch(...) {if(!failure)failure=std::current_exception();}
    try {if(!presence->release(expected))throw std::logic_error("TW terminal lease did not detach");}
    catch(...) {if(!failure)failure=std::current_exception();}
    if(failure){fail_terminal();std::rethrow_exception(failure);}
}
bool SharedTaiwanWorldLifecycle::Binding::prepare(Session& session,const RecoveredWorldEntry::Frame& wire) {
    owner();if(stage!=Stage::Fresh || session.closing() || !session.account_id || !session.character_id||
        !session.native_channel_allows_presence(presence))return false;
    const auto full=RecoveredWorldEntryView::read(wire);
    if(!full || !valid_taiwan_world_entry_identity(identity) ||
       (identity==TaiwanWorldEntryIdentity::SelectedCharacter && session.character_id!=full->actor_handle) ||
       (identity==TaiwanWorldEntryIdentity::QualifiedSceneHandle && !qualified_taiwan_scene_handle(full->actor_handle)))return false;
    // Default mode keeps the existing selected-character preparation behavior.
    if(identity==TaiwanWorldEntryIdentity::SelectedCharacter) {
        const auto account=session.account_id,character=session.character_id;
        const auto registry=presence;
        const auto prepared=presence->prepare_geometry(session.id(),account,character,
            full->actor_handle,full->area,full->scene,full->x,full->y);
        if(!prepared)return false;
        // Opt-in only: caught reentrant release must never revive a binding.
        if((status_incarnations||session.native_channel_bound())&&(stage!=Stage::Fresh||session.closing()||
           session.account_id!=account||session.character_id!=character||
           !registry->retained_preparation_current(*prepared)||!session.native_channel_allows_presence(registry))) {
            registry->release(*prepared);return false;
        }
        lease=*prepared;entry=*full;connection=session.shared_from_this();stage=Stage::Prepared;
        if(!admit_status_incarnation(session)){release();return false;}
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
       !registry->retained_preparation_current(*prepared)||!session.native_channel_allows_presence(registry)) {
        registry->release(*prepared);return false;
    }
    lease=*prepared;entry=*full;connection=pinned;stage=Stage::Prepared;
    if(!admit_status_incarnation(session)){release();return false;}
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
            expected.position.x==retained.x && expected.position.y==retained.y&&session.native_channel_allows_presence(registry);
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
    std::shared_ptr<SharedWorldPresence> presence,std::shared_ptr<shared::SharedActorVisibility> visibility,Entered entered,
    std::shared_ptr<SharedNativeWorldTransports> transports,TaiwanWorldEntryIdentity identity,
    std::shared_ptr<TaiwanActorStatusIncarnationSource> status_incarnations) {
    if(!valid_taiwan_world_entry_identity(identity) || !presence || !visibility || !entered || !visibility->owns_presence(presence) ||
       (transports && !transports->owns_presence(presence)) ||
       (status_incarnations && !status_incarnations->owns_presence(presence)))return {};
    auto binding=std::make_shared<Binding>();binding->presence=std::move(presence);
    binding->status_incarnations=std::move(status_incarnations);
    binding->visibility=std::move(visibility);binding->entered=std::move(entered);binding->transports=std::move(transports);binding->identity=identity;
    auto result=std::make_shared<Session::CommonWorldLifecycle>();
    result->prepared=[binding](Session& session,const RecoveredWorldEntry::Frame& frame) {
        try {
            if(!binding->prepare(session,frame))return false;
            const auto peer=session.weak_from_this();
            if(!session.install_common_world_cleanup([binding]{binding->release();},
                [binding,peer] {
                    const auto session=peer.lock();
                    if(!session){binding->fail_terminal();throw std::logic_error("TW terminal Session expired");}
                    binding->begin_terminal(*session);
                },
                [binding,peer](bool clean) {
                    const auto session=peer.lock();
                    if(!session){binding->fail_terminal();return false;}
                    return binding->finish_terminal(*session,clean);
                })) {
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
    std::shared_ptr<SharedWorldPresence> presence,std::shared_ptr<shared::SharedActorVisibility> visibility,Entered entered,
    std::shared_ptr<SharedNativeWorldTransports> transports,TaiwanWorldEntryIdentity identity,
    std::shared_ptr<TaiwanActorStatusIncarnationSource> status_incarnations) {
    if(!valid_taiwan_world_entry_identity(identity) || !presence || !visibility || !entered || !visibility->owns_presence(presence) ||
       (transports && !transports->owns_presence(presence)) ||
       (status_incarnations && !status_incarnations->owns_presence(presence)))
        throw std::invalid_argument("TW common lifecycle factory requires actual presence/visibility/scene owner");
    return [presence=std::move(presence),visibility=std::move(visibility),entered=std::move(entered),transports=std::move(transports),identity,status_incarnations=std::move(status_incarnations)](Session&) {
        return hooks(presence,visibility,entered,transports,identity,status_incarnations); // Fresh Binding on this Session's game owner.
    };
}
void SharedTaiwanWorldLifecycle::AsyncBinding::release() {
    base.owner();base.retire_status_incarnation();if(released)return;released=true;
    auto completion=std::move(done);std::exception_ptr failure;
    // cancel_common_ready can run before Session's disconnect cleanup.
    try {base.arm_terminal_retirement();}catch(...) {failure=std::current_exception();}
    if(base.lease) {
        if(const auto session=base.connection.lock()) {
            try {session->release_common_world_entry_identity(base.lease->account,base.lease->character,base.lease->generation);}
            catch(...) {if(!failure)failure=std::current_exception();}
            try {scene.cancel(*session,*base.lease);}catch(...) {if(!failure)failure=std::current_exception();}
        }
    }
    try {base.release();}catch(...) {if(!failure)failure=std::current_exception();}
    if(completion)try {completion(false);}catch(...) {if(!failure)failure=std::current_exception();}
    if(failure){base.fail_terminal();std::rethrow_exception(failure);}
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
    std::shared_ptr<SharedWorldPresence> presence,std::shared_ptr<shared::SharedActorVisibility> visibility,AsyncOwner scene,
    std::shared_ptr<SharedNativeWorldTransports> transports,TaiwanWorldEntryIdentity identity,
    std::shared_ptr<TaiwanActorStatusIncarnationSource> status_incarnations) {
    if(!valid_taiwan_world_entry_identity(identity) || !presence || !visibility || !scene.entered || !scene.cancel || !visibility->owns_presence(presence) ||
       (transports && !transports->owns_presence(presence)) ||
       (status_incarnations && !status_incarnations->owns_presence(presence)))return {};
    auto binding=std::make_shared<AsyncBinding>();binding->base.presence=std::move(presence);
    binding->base.status_incarnations=std::move(status_incarnations);
    binding->base.visibility=std::move(visibility);binding->scene=std::move(scene);binding->base.transports=std::move(transports);binding->base.identity=identity;
    auto result=std::make_shared<Session::CommonWorldLifecycle>();
    result->prepared=[binding](Session& session,const RecoveredWorldEntry::Frame& frame) {
        try {
            if(!binding->base.prepare(session,frame))return false;
            const auto peer=session.weak_from_this();
            if(!session.install_common_world_cleanup([binding]{binding->release();},
                [binding,peer] {
                    const auto session=peer.lock();
                    if(!session){binding->base.fail_terminal();throw std::logic_error("TW terminal Session expired");}
                    binding->base.begin_terminal(*session);
                },
                [binding,peer](bool clean) {
                    const auto session=peer.lock();
                    if(!session){binding->base.fail_terminal();return false;}
                    return binding->base.finish_terminal(*session,clean);
                })) {
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
    std::shared_ptr<SharedWorldPresence> presence,std::shared_ptr<shared::SharedActorVisibility> visibility,AsyncOwner scene,
    std::shared_ptr<SharedNativeWorldTransports> transports,TaiwanWorldEntryIdentity identity,
    std::shared_ptr<TaiwanActorStatusIncarnationSource> status_incarnations) {
    if(!valid_taiwan_world_entry_identity(identity) || !presence || !visibility || !scene.entered || !scene.cancel || !visibility->owns_presence(presence) ||
       (transports && !transports->owns_presence(presence)) ||
       (status_incarnations && !status_incarnations->owns_presence(presence)))
        throw std::invalid_argument("TW asynchronous lifecycle requires actual scene owner and cancellation");
    return [presence=std::move(presence),visibility=std::move(visibility),scene=std::move(scene),transports=std::move(transports),identity,status_incarnations=std::move(status_incarnations)](Session&) {
        return hooks_async(presence,visibility,scene,transports,identity,status_incarnations);
    };
}
}
