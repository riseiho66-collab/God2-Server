#include "auth/SharedCharacterRemovalPresence.h"
#include <stdexcept>
#include <utility>

namespace god2 {
SharedCharacterRemovalPresence::SharedCharacterRemovalPresence(
    const RecoveredCharacterRepository& characters,std::shared_ptr<const SharedWorldPresence> presence,
    const World& world,LegacyMovement movement)
    :characters_(characters),presence_(std::move(presence)),world_(world),movement_(std::move(movement)) {
    if(!presence_ || !presence_->owns_repository(characters_))
        throw std::invalid_argument("Character removal requires actual common presence repository");
    if(const auto* active=std::get_if<std::reference_wrapper<const RecoveredMovementService>>(&movement_))
        if(!active->get().owns_repository(characters_))
            throw std::invalid_argument("Character removal legacy movement uses another repository");
}
void SharedCharacterRemovalPresence::owner() const {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("Character removal presence game owner mismatch");
}
bool SharedCharacterRemovalPresence::owns_repository(const RecoveredCharacterRepository& characters) const {
    owner();return &characters_==&characters && presence_->owns_repository(characters);
}
bool SharedCharacterRemovalPresence::owns_presence_registry(const SharedWorldPresence& presence) const {
    owner();return presence_.get()==&presence;
}
bool SharedCharacterRemovalPresence::unreserved(std::uint64_t account,std::uint64_t character) const {
    owner();if(!account || !character)return false;
    // Check raw reservations, not presence.current()/ready(): the SQL root may
    // be staged absent, and preparation itself already excludes other owners.
    if(presence_->character_reserved(character) || world_.character_online(character))return false;
    const auto* active=std::get_if<std::reference_wrapper<const RecoveredMovementService>>(&movement_);
    return !active || !active->get().character_active(account,character);
}
}
