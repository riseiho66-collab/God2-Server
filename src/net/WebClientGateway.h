#pragma once
#include <asio.hpp>
#include <chrono>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

namespace god2 {
// Browser-only transport policy, not native gameplay parameters. All budgets
// must be supplied explicitly by the host. This listener is loopback only;
// production public WSS termination belongs to the controlled reverse proxy.
struct WebGatewayPolicy {
    asio::ip::tcp::endpoint listen;
    std::vector<std::string> origins;
    std::size_t max_sessions=0, sessions_per_address=0, accepts_per_second=0;
    std::size_t message_bytes=0, queue_bytes=0, queue_frames=0;
    std::size_t frames_per_second=0, bytes_per_second=0;
    std::chrono::seconds handshake_timeout{0}, idle_timeout{0}, message_timeout{0}, close_timeout{0};
};
struct WebNativeRoute {std::string path;asio::ip::tcp::endpoint endpoint;};
// One WS peer owns one TCP peer into an Application-owned native listener.
// It never authenticates, decrypts, selects gameplay or changes packet bytes.
class WebClientGateway {
public:
    WebClientGateway(asio::io_context&,WebGatewayPolicy,std::vector<WebNativeRoute>);
    ~WebClientGateway();
    WebClientGateway(const WebClientGateway&)=delete;
    WebClientGateway& operator=(const WebClientGateway&)=delete;
    void start();
    void stop();
    std::uint16_t port() const noexcept;
private:
    struct State;
    std::shared_ptr<State> state_;
};
}
