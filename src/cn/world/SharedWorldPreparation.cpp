#include "cn/world/SharedWorldPreparation.h"
#include "cn/protocol/CnWorldSelectionStatus.h"
#include "cn/world/SharedSceneIdentity.h"
#include <stdexcept>
#include <utility>

namespace god2::cn {
namespace {
struct ReleaseOnce {
    std::shared_ptr<SharedWorldPreparation::Reservation> reservation;
    std::function<void()> supplied;
    bool released=false;
    void release() noexcept {
        if(!std::exchange(released,true)) {
            if(supplied)try {supplied();}catch(...) {}
            if(reservation)reservation->release();
        }
    }
    ~ReleaseOnce(){release();}
};
}
SharedWorldPreparation::SharedWorldPreparation(RecoveredCharacterRepository& characters,const NativeMapCatalog& maps,
    std::shared_ptr<SharedWorldPresence> presence,std::shared_ptr<SharedActorVisibility> visibility,
    std::shared_ptr<const god2cn::CnSceneAssets> assets,Reserve reserve,std::size_t encoded,std::size_t plain,
    std::shared_ptr<SharedNativeWorldTransports> world_transports)
    :characters_(characters),maps_(maps),presence_(std::move(presence)),visibility_(std::move(visibility)),
     world_transports_(std::move(world_transports)),
     assets_(std::move(assets)),reserve_(std::move(reserve)),encoded_budget_(encoded),plain_budget_(plain) {}
void SharedWorldPreparation::owner() const {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("CN world-preparation game owner mismatch");
}
bool SharedWorldPreparation::owns_registries(const std::shared_ptr<SharedWorldPresence>& presence,
                                            const std::shared_ptr<SharedActorVisibility>& visibility) const {
    owner();return presence && visibility && presence_==presence && visibility_==visibility &&
        visibility_->owns_presence(presence);
}
bool SharedWorldPreparation::owns_transport_source(const std::shared_ptr<SharedNativeWorldTransports>& source) const {
    owner();return world_transports_==source && (!source || source->owns_presence(presence_));
}
std::shared_ptr<SharedWorldPreparation> SharedWorldPreparation::create(
    RecoveredCharacterRepository& characters,const NativeMapCatalog& maps,
    std::shared_ptr<SharedWorldPresence> presence,std::shared_ptr<SharedActorVisibility> visibility,
    std::shared_ptr<const god2cn::CnSceneAssets> assets,Reserve reserve,std::size_t encoded,std::size_t plain,
    std::shared_ptr<SharedNativeWorldTransports> world_transports) {
    if(!presence || !presence->owns_repository(characters) || !visibility || !visibility->owns_presence(presence) ||
       (world_transports && !world_transports->owns_presence(presence)) ||
       !assets || !reserve || !encoded || !plain)return {};
    return std::shared_ptr<SharedWorldPreparation>(new SharedWorldPreparation(characters,maps,std::move(presence),
        std::move(visibility),std::move(assets),std::move(reserve),encoded,plain,std::move(world_transports)));
}
SharedWorldSelection::Selected SharedWorldPreparation::selected() {
    owner();return [self=shared_from_this()](std::shared_ptr<SharedWorldSelection> selection,Choice choice,
                                           Connection::Transport::Completion done) {
        self->prepare(selection,choice,std::move(done));
    };
}
void SharedWorldPreparation::prepare(const std::shared_ptr<SharedWorldSelection>& selection,Choice choice,
                                    Connection::Transport::Completion done) {
    owner();if(!done)throw std::invalid_argument("CN world preparation completion required");
    auto completion=std::make_shared<Connection::Transport::Completion>(std::move(done));
    const auto finish=[completion](bool accepted) {
        auto callback=std::move(*completion);if(callback)callback(accepted);
    };
    std::shared_ptr<Connection> connection;
    std::shared_ptr<ReleaseOnce> release;
    std::optional<Lease> lease;
    bool accepted=false;
    try {
        const auto process=[&] {
            if(!selection)return false;
            connection=selection->connection_for_choice(choice,characters_,maps_);if(!connection)return false;
            const auto position=characters_.load_position(choice.account,choice.character);
            if(!position)return false; // Placement must already be authoritative and persisted.
            // Allocate the guard before obtaining an external reservation.
            // A later local allocation failure cannot strand its native handle.
            release=std::make_shared<ReleaseOnce>();
            release->reservation=reserve_(choice,*position);if(!release->reservation)return false;
            const auto native=release->reservation->snapshot();
            const auto status=god2cn::CnWorldSelectionStatus::read(native.status02);
            const auto entry=god2cn::CnWorldEntry::read_begin_play(native.begin2a);
            const bool transfer=choice.path==SharedWorldSelection::NativeOffer::Path::Transfer;
            if(!status || status->status!=0 || !entry || !native.scene_revision ||
               transfer!=native.previous.has_value() || !release->reservation->current(choice,*position,native))return false;
            const auto map=maps_.lookup(NativeMapCatalog::current_dataset_id,position->area,position->scene);
            if(!map || !SharedSceneIdentity::matches(*map,*position,*entry,native.previous))return false;
            // Shared presence re-reads ownership/storage and excludes conflicting
            // sessions/characters/handles. No placement write or ID truncation.
            lease=presence_->prepare(connection->world_session_id(),choice.account,choice.character,
                entry->actor_handle(),*position);
            if(!lease)return false;
            std::shared_ptr<SharedInitialScene> scene;
            if(!transfer) {
                scene=SharedInitialScene::prepare(connection,presence_,*lease,maps_,*assets_,native.begin2a,
                    native.scene_revision,encoded_budget_,plain_budget_);
                if(!scene)return false;
            }else if(!release->reservation->qualify_transfer(connection,*lease,native))return false;
            auto sources=release->reservation->gameplay(connection,*lease,scene);if(!sources)return false;
            release->supplied=std::move(sources->release_world);
            if(world_transports_) {
                // Actual host selects one exact native endpoint source. A
                // supplier may select that same source or leave it absent;
                // a competing registry never silently replaces the host.
                if(sources->world_transports && sources->world_transports!=world_transports_)return false;
                sources->world_transports=world_transports_;
            }
            if(!transfer) {
                // Concrete live scene adoption requires ready. Preserve this
                // exact initial profile/lease and defer adoption until then.
                if(sources->movement || sources->prepare_movement)return false;
                auto authority=release->reservation->normal_movement_authority();if(!authority)return false;
                sources->prepare_movement=[weak=std::weak_ptr<Connection>(connection),presence=presence_,
                    lease=*lease,scene,assets=assets_,authority=std::move(authority),
                    encoded=encoded_budget_,plain=plain_budget_]() -> std::shared_ptr<SharedMovement::WorldOwner> {
                    return SharedNativeMovementScene::adopt(weak.lock(),presence,lease,scene,*assets,authority,encoded,plain);
                };
            }
            // Keep real suppliers alive and release the external reservation
            // once alongside this connection's common incarnation cleanup.
            sources->release_world=[release] {release->release();};
            if(selection->connection_for_choice(choice,characters_,maps_)!=connection ||
               !presence_->preparation_current(*lease) || !release->reservation->current(choice,*position,native))return false;
            auto ready=SharedWorldGameplay::compose(connection,presence_,*lease,visibility_,std::move(*sources));
            if(!ready || !presence_->preparation_current(*lease) ||
               !release->reservation->current(choice,*position,native))return false;
            return selection->install_selected_ingress(choice.character,*position,native.previous,
                native.status02,native.begin2a,ready,scene,
                [self=shared_from_this(),release,lease=*lease,choice,position=*position,native](
                    SharedWorldSelection::PublicationCheck check) {
                    self->owner();
                    return self->presence_->preparation_current(lease) &&
                        release->reservation->current(choice,position,native,check) &&
                        self->presence_->preparation_current(lease);
                },
                [self=shared_from_this(),weak=std::weak_ptr<Connection>(connection),release,
                 lease=*lease,choice,session=connection->world_session_id(),completion,finish](bool queued) {
                    if(!*completion)return;
                    self->owner();const auto connection=weak.lock();bool current=false;
                    try {current=queued && connection && !connection->closing() &&
                        connection->verified_account_id()==choice.account &&
                        connection->world_session_id()==session;}catch(...) {current=false;}
                    if(!current) {
                        try {self->visibility_->release(lease);}catch(...) {}
                        try {self->presence_->release(lease);}catch(...) {}
                        release->release();if(connection)connection->close();
                    }
                    finish(current); // Qualified publication, not stale prepared lease/ready stage.
                });
        };
        accepted=process();
    }catch(...) {accepted=false;}
    if(accepted)return; // Scheduled02/2A: only the game-owner queue callback completes1A.
    if(!accepted) {
        if(lease) {
            try {visibility_->release(*lease);}catch(...) {}
            try {presence_->release(*lease);}catch(...) {}
        }
        if(release)release->release();
        if(connection)connection->close();
    }
    finish(false); // Once across synchronous failure and any posted queue callback.
}
}
