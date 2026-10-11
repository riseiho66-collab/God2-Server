#include "cn/net/SharedListenerRegistry.h"
#include <set>
#include <stdexcept>

namespace god2::cn {
SharedListenerRegistry::SharedListenerRegistry(std::vector<Endpoint> endpoints)
    :endpoints_(std::move(endpoints)) {
    std::size_t accounts=0,worlds=0;
    std::set<std::pair<asio::ip::address,std::uint16_t>> sockets;
    std::set<std::pair<std::uint16_t,std::uint16_t>> targets;
    for(const auto& e:endpoints_) {
        if(!e.socket.port() || !sockets.emplace(e.socket.address(),e.socket.port()).second)
            throw std::invalid_argument("CN actual bound listener registry invalid");
        if(e.role==Role::Account && !e.target)++accounts;
        else if(e.role==Role::World && e.target && e.target->group<64 && e.target->server<10 &&
                targets.emplace(e.target->group,e.target->server).second)++worlds;
        else throw std::invalid_argument("CN bound listener role/target invalid");
    }
    if(accounts!=1 || !worlds)throw std::invalid_argument("CN bound account/world registry incomplete");
}
void SharedListenerRegistry::owner() const {
    if(thread_!=std::this_thread::get_id())throw std::logic_error("CN listener registry game owner mismatch");
}
void SharedListenerRegistry::start() {owner();if(!stopped_)started_=true;}
void SharedListenerRegistry::stop() {owner();stopped_=true;}
std::optional<SharedListenerRegistry::Snapshot> SharedListenerRegistry::observe() const {
    owner();if(!started_ || stopped_)return std::nullopt;
    return Snapshot(shared_from_this());
}
std::vector<SharedListenerRegistry::Endpoint> SharedListenerRegistry::bound_endpoints() const {
    owner();return stopped_?std::vector<Endpoint>{}:endpoints_;
}
bool SharedListenerRegistry::Snapshot::current() const {
    if(!owner_)return false;
    owner_->owner();return owner_->started_ && !owner_->stopped_;
}
std::span<const SharedListenerRegistry::Endpoint> SharedListenerRegistry::Snapshot::endpoints() const {
    if(!owner_)throw std::logic_error("CN listener snapshot has no owner");
    owner_->owner();return owner_->endpoints_;
}
}
