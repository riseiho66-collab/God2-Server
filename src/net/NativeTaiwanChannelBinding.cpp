#include "net/NativeTaiwanChannelBinding.h"
#include "game/SharedWorldPresence.h"
#include <stdexcept>
#include <utility>

namespace god2 {
NativeTaiwanChannelBinding::NativeTaiwanChannelBinding(std::shared_ptr<SharedWorldPresence> presence,
        std::uint8_t group,std::uint8_t channel,asio::ip::tcp::endpoint endpoint)
    :presence_(presence),group_(group),channel_(channel),endpoint_(std::move(endpoint)) {
    if(!presence||group>=10||channel>=3||presence->channel()!=channel||
       !endpoint_.address().is_v4()||!endpoint_.address().is_loopback()||!endpoint_.port())
        throw std::invalid_argument("Native channel binding requires actual world and bound loopback IPv4 endpoint");
}
void NativeTaiwanChannelBinding::owner() const {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("Native channel binding game owner mismatch");
}
bool NativeTaiwanChannelBinding::accepts(const asio::ip::tcp::endpoint& endpoint) const noexcept {
    return live_.load(std::memory_order_acquire)&&endpoint==endpoint_;
}
bool NativeTaiwanChannelBinding::matches_presence(const std::shared_ptr<SharedWorldPresence>& presence) const {
    owner();return presence&&live_.load(std::memory_order_acquire)&&presence_.lock()==presence&&
        presence->channel()==channel_;
}
bool NativeTaiwanChannelBinding::matches_destination(std::uint8_t group,std::uint8_t channel) const {
    owner();return live_.load(std::memory_order_acquire)&&!presence_.expired()&&group==group_&&channel==channel_;
}
}
