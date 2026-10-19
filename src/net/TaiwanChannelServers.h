#pragma once
#include "net/TcpServer.h"
#include "game/SharedTaiwanChannelWorlds.h"
#include "game/TaiwanNativeClientGroupConfiguration.h"
#include <array>
#include <functional>
#include <memory>
#include <thread>

namespace god2 {
// CUSTOM-0159 actual three G listeners. The caller owns GAME sources, worlds
// and repositories through network+game drain. Supplied callbacks must be the
// existing revocable weak transport facades; this object does not own/destroy
// affine gameplay captures in NET or invent entry/scene/selection handlers.
class TaiwanChannelServers final {
public:
    struct EndpointPolicy {
        std::array<std::uint8_t,4> address;
        std::uint16_t port; //0 requests an actual kernel-assigned bound port.
        std::uint8_t status;
        std::array<std::uint8_t,4> route_body; // Actual snapshot routing material, not channel numbers.
    };
    struct Sources {
        Session::PacketHandler packet;
        Session::DisconnectHandler disconnected;
        Session::RecoveredLoginHandler authenticate;
        Session::RecoveredCharacterHandlers characters;
    };
    // Called once per actual channel on GAME. Build three independent owners
    // from the selected world, sharing the real L-issued list handoff lineage.
    // No listeners, sends, event pumping or borrowed local Context retention.
    using SourceFactory=std::function<Sources(std::uint8_t,const std::shared_ptr<SharedWorldHost>&)>;
    TaiwanChannelServers(asio::io_context& network,asio::any_io_executor game,
        const SharedTaiwanChannelWorlds&,std::shared_ptr<const TaiwanNativeClientGroupConfiguration>,
        std::uint8_t group,std::uint8_t group_byte_1,const std::array<EndpointPolicy,3>&,
        std::size_t capacity_per_channel,bool packet_dump,SourceFactory);
    ~TaiwanChannelServers();
    TaiwanChannelServers(const TaiwanChannelServers&)=delete;
    TaiwanChannelServers& operator=(const TaiwanChannelServers&)=delete;
    void start();
    // Revokes each binding before GAME can perform more input. Keep sources,
    // worlds/repositories alive until all actual Session disconnect jobs drain.
    void stop();
    asio::ip::tcp::endpoint endpoint(std::uint8_t channel) const;
    std::vector<std::uint8_t> advertisement() const;
private:
    void owner() const;
    const std::thread::id thread_=std::this_thread::get_id();
    std::array<std::unique_ptr<TcpServer>,3> listeners_{};
    std::vector<std::uint8_t> advertisement_;
    bool started_=false,stopped_=false;
};
}
