#include "game/SharedTaiwanChannelWorlds.h"
#include <exception>
#include <stdexcept>

namespace god2 {
SharedTaiwanChannelWorlds::SharedTaiwanChannelWorlds(RecoveredCharacterRepository& characters)
    :ownership_(std::make_shared<SharedChannelCharacterOwnership>(characters)),worlds_{
        std::make_shared<SharedWorldHost>(characters,ownership_,0),
        std::make_shared<SharedWorldHost>(characters,ownership_,1),
        std::make_shared<SharedWorldHost>(characters,ownership_,2)} {}
SharedTaiwanChannelWorlds::~SharedTaiwanChannelWorlds() {
    if(thread_!=std::this_thread::get_id())std::terminate();
}
void SharedTaiwanChannelWorlds::owner() const {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("Three-channel worlds game owner mismatch");
}
std::shared_ptr<SharedWorldHost> SharedTaiwanChannelWorlds::world(std::uint8_t channel) const {
    owner();if(channel>=channel_count)throw std::out_of_range("Channel ordinal must be0..2");
    return worlds_[channel];
}
bool SharedTaiwanChannelWorlds::character_reserved(std::uint64_t character) const {
    owner();return ownership_->character_reserved(character);
}
bool SharedTaiwanChannelWorlds::owns_repository(const RecoveredCharacterRepository& characters) const {
    owner();if(!ownership_->owns_repository(characters))return false;
    for(std::uint8_t channel=0;channel<channel_count;++channel)
        if(!worlds_[channel]->owns_repository(characters)||worlds_[channel]->channel()!=channel)return false;
    return true;
}
}
