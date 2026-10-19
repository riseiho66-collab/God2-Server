#pragma once
#include <asio/ip/tcp.hpp>
#include <atomic>
#include <cstdint>
#include <memory>
#include <thread>

namespace god2 {
class SharedWorldPresence;
class Session;
class TcpServer;
// CUSTOM-0159 pure listener metadata. Only TcpServer can mint it from its
// actual bound endpoint before accepting. Weak world ownership is intentional:
// NET-held copies must never destroy an affine game world on a network thread.
class NativeTaiwanChannelBinding final {
public:
    ~NativeTaiwanChannelBinding()=default;
private:
    friend class TcpServer;
    friend class Session;
    NativeTaiwanChannelBinding(std::shared_ptr<SharedWorldPresence>,std::uint8_t group,
        std::uint8_t channel,asio::ip::tcp::endpoint);
    bool accepts(const asio::ip::tcp::endpoint&) const noexcept;
    bool matches_presence(const std::shared_ptr<SharedWorldPresence>&) const;
    bool matches_destination(std::uint8_t group,std::uint8_t channel) const;
    void retire() const noexcept {live_.store(false,std::memory_order_release);}
    void owner() const;
    const std::weak_ptr<SharedWorldPresence> presence_;
    const std::uint8_t group_,channel_;
    const asio::ip::tcp::endpoint endpoint_;
    const std::thread::id thread_=std::this_thread::get_id();
    mutable std::atomic<bool> live_{true};
};
}
