#pragma once

#include "net/Session.h"
#include <asio.hpp>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <string>

namespace god2 {
class TaiwanChannelServers;
class SharedWorldPresence;
class TcpServer {
public:
    TcpServer(asio::io_context& network, asio::any_io_executor game_executor,
              const std::string& host, std::uint16_t port,
              std::size_t max_sessions, bool packet_dump,
              Session::PacketHandler on_packet,
              Session::DisconnectHandler on_disconnect,ProtocolMode mode=ProtocolMode::Fixture,
              Session::RecoveredLoginHandler recovered_login={},Session::RecoveredCharacterHandlers characters={},
              std::vector<std::uint8_t> character_routes={});
    ~TcpServer();
    TcpServer(const TcpServer&) = delete;
    TcpServer& operator=(const TcpServer&) = delete;
    void start();
    // Keep both executors running until pending callbacks and closes drain.
    void stop();
    std::uint16_t port() const noexcept;
    asio::ip::tcp::endpoint bound_endpoint() const noexcept;
private:
    friend class TaiwanChannelServers;
    // Constructor-only integration before start; never exposed as a Session
    // rebinding API. Failed three-listener construction closes unstarted binds.
    void bind_native_channel(std::shared_ptr<SharedWorldPresence>,std::uint8_t group,std::uint8_t channel);
    void discard_unstarted();
    struct Impl;
    std::shared_ptr<Impl> impl_;
};
} // namespace god2
