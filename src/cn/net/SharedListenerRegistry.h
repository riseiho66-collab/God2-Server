#pragma once
#include "cn/net/CnTransportSession.h"
#include "auth/SharedWorldAdmission.h"
#include <memory>
#include <optional>
#include <span>
#include <thread>
#include <utility>
#include <vector>

namespace god2::cn {
class SharedCredentialServer;
// Actual successful bind/listen operands, minted only by our listener owner.
// Construction/start/stop/current checks all belong to the serial game thread.
// This is managed hosting lifetime, not native packet authority or health proof.
class SharedListenerRegistry final:public std::enable_shared_from_this<SharedListenerRegistry> {
public:
    using Role=god2cn::CnTransportSession::Role;
    struct Endpoint {
        Role role;
        std::optional<SharedWorldAdmission::Target> target;
        asio::ip::tcp::endpoint socket;
    };
    class Snapshot {
    public:
        bool current() const;
        std::span<const Endpoint> endpoints() const;
    private:
        friend class SharedListenerRegistry;
        explicit Snapshot(std::shared_ptr<const SharedListenerRegistry> owner):owner_(std::move(owner)) {}
        std::shared_ptr<const SharedListenerRegistry> owner_;
    };
    // No snapshot before this host is started, or after it is stopped. A retained
    // snapshot owns the same immutable registry; stop permanently invalidates it.
    std::optional<Snapshot> observe() const;
    // Construction-time bound socket registry for the existing Application/web
    // setup. Empty after managed stop; not permission to publish before start.
    std::vector<Endpoint> bound_endpoints() const;
private:
    friend class SharedCredentialServer;
    explicit SharedListenerRegistry(std::vector<Endpoint>);
    void start();
    void stop();
    void owner() const;
    const std::thread::id thread_=std::this_thread::get_id();
    const std::vector<Endpoint> endpoints_;
    bool started_=false,stopped_=false;
};
}
