#pragma once
#include "SharedGuildCoordinator53Draft.h"
#include "handlers/OwnedGuildChatService.h"
#include "net/Session.h"
#include <array>
#include <cstddef>
#include <cstdint>
#include <functional>
#include <memory>
#include <optional>
#include <set>
#include <span>
#include <vector>

namespace god2 {
// CUSTOM-0159: GAME-owned routing of supplied Common53 evidence across three
// worlds. This directory grants no membership, native publication or readiness.
// Retire before framed sources unwind; copied facades retain only weak state.
class SharedGuildChannelDirectory53 final {
    struct ChatTicket;
public:
    using Common=SharedGuildCoordinator53Draft;
    using Host=Common::Host;
    using Panel=Common::Panel;
    using Owner=Common::Owner;
    using Chat=OwnedGuildChatService;
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
        Chat::Resolve chat_peer;
        std::function<void(const std::shared_ptr<Session>&,std::vector<std::uint8_t>)> chat_send;
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
    class ChatBatch final {
    public:
        ChatBatch(ChatBatch&&)=default;
        ChatBatch& operator=(ChatBatch&&)=default;
        ChatBatch(const ChatBatch&)=delete;
        ChatBatch& operator=(const ChatBatch&)=delete;
    private:
        friend class SharedGuildChannelDirectory53;
        explicit ChatBatch(std::shared_ptr<ChatTicket> ticket):ticket_(std::move(ticket)){}
        std::shared_ptr<ChatTicket> ticket_;
    };
    struct ChatDispatch {std::size_t submitted{};bool complete{};};
    std::optional<ChatBatch> prepare_chat(std::uint64_t,std::span<const RecoveredGuildChat::Request>,Chat::Prepare);
    // Echo receives the original sender's logical bytes only. The actual
    // caller may frame and append them after its movement response. A partial
    // submission cannot be rolled back; complete=false preserves that fact.
    ChatDispatch dispatch_chat(ChatBatch&,std::function<void(std::vector<std::uint8_t>)> sender_echo={});
    // Propagates an outer native mixed-source cancellation before a chat
    // supplier returns and the directory considers its next recipient.
    void invalidate_chat();
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
