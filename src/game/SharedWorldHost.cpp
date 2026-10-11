#include "game/SharedWorldHost.h"
#include "game/SharedWorldPresence.h"
#include "game/SharedNativeWorldTransports.h"
#include "game/SharedNativeSpectatorPublication.h"
#include "game/SharedNativeSpectatorTargets.h"
#include "cn/world/SharedActorVisibility.h"
#include <exception>
#include <stdexcept>
#include <utility>

namespace god2 {
SharedWorldHost::SharedWorldHost(RecoveredCharacterRepository& characters)
    :characters_(characters),presence_(std::make_shared<SharedWorldPresence>(characters)),
     visibility_(std::make_shared<cn::SharedActorVisibility>(presence_)),
     transports_(SharedNativeWorldTransports::create(presence_)) {}
SharedWorldHost::~SharedWorldHost() {
    if(thread_!=std::this_thread::get_id())std::terminate();
}
void SharedWorldHost::owner() const {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("Shared world host game owner mismatch");
}
std::shared_ptr<SharedWorldPresence> SharedWorldHost::presence() const {
    owner();return presence_;
}
std::shared_ptr<cn::SharedActorVisibility> SharedWorldHost::visibility() const {
    owner();return visibility_;
}
std::shared_ptr<SharedNativeWorldTransports> SharedWorldHost::transports() const {
    owner();return transports_;
}
std::shared_ptr<SharedNativeSpectatorPublication> SharedWorldHost::native_spectator_publication() const {
    owner();return spectator_publication_;
}
void SharedWorldHost::install_native_spectator_publication(std::shared_ptr<SharedNativeSpectatorPublication> supplied) {
    owner();
    if(spectator_publication_ || !supplied || !supplied->owns_source(presence_,transports_))
        throw std::invalid_argument("Common spectator publisher requires a fresh actual same-host source");
    spectator_publication_=std::move(supplied);
}
std::shared_ptr<SharedNativeSpectatorTargets> SharedWorldHost::native_spectator_targets() const {
    owner();return spectator_targets_;
}
void SharedWorldHost::install_native_spectator_targets(std::shared_ptr<SharedNativeSpectatorTargets> supplied) {
    owner();
    if(spectator_targets_ || !spectator_publication_ || !supplied ||
       !supplied->owns_source(presence_,transports_,spectator_publication_))
        throw std::invalid_argument("Common spectator targets require a fresh exact actual publication source");
    spectator_targets_=std::move(supplied);
}
bool SharedWorldHost::owns_repository(const RecoveredCharacterRepository& characters) const {
    owner();return &characters_==&characters && presence_->owns_repository(characters) &&
        visibility_->owns_presence(presence_) && transports_->owns_presence(presence_) &&
        (!spectator_publication_ || spectator_publication_->owns_source(presence_,transports_)) &&
        (!spectator_targets_ || spectator_targets_->owns_source(presence_,transports_,spectator_publication_));
}
}
