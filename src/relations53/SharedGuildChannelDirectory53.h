#pragma once
#include "SharedGuildCoordinator53Draft.h"
#include "net/Session.h"
#include <array>
#include <cstddef>
#include <cstdint>
#include <functional>
#include <memory>
#include <optional>
#include <set>
#include <vector>

namespace god2 {
// CUSTOM-0159: GAME-owned routing of supplied Common53 evidence across three
// worlds. This directory grants no membership, native publication or readiness.
// Retire before framed sources unwind; copied facades retain only weak state.
class SharedGuildChannelDirectory53 final {
public:
    using Common=SharedGuildCoordinator53Draft;
    using Host=Common::Host;
    using Panel=Common::Panel;
    using Owner=Common::Owner;
    struct Source {
        std::function<std::shared_ptr<Session>(std::uint64_t)> session;
        Host::Enumerate enumerate;
        Panel::Resolve owner;
        Host::PeerReady peer_ready;
        Panel::RecipientReady recipient_ready;
        Panel::ConnectionClosed closed;
        Common::Send send;
        Common::KnownBaseline baseline;
        std::function<std::set<std::uint32_t>()> online;
        std::function<void(const Owner&)> sync_name;
    };
    struct Binding {
        Host::Enumerate enumerate;
        Panel::Resolve owner;
        Host::PeerReady peer_ready;
        Panel::RecipientReady recipient_ready;
        Panel::ConnectionClosed closed;
        Common::Send send;
        Common::KnownBaseline baseline;
        std::function<std::set<std::uint32_t>()> online;
        std::function<void(const Owner&)> sync_name;
    };
    static std::shared_ptr<SharedGuildChannelDirectory53> create(std::size_t expected=3);
    void install(std::uint8_t,Source);
    void seal();
    Binding binding();
    void retire();
    ~SharedGuildChannelDirectory53();
    SharedGuildChannelDirectory53(const SharedGuildChannelDirectory53&)=delete;
    SharedGuildChannelDirectory53& operator=(const SharedGuildChannelDirectory53&)=delete;
private:
    struct State;
    explicit SharedGuildChannelDirectory53(std::shared_ptr<State> state):state_(std::move(state)){}
    std::shared_ptr<State> state_;
};
}
