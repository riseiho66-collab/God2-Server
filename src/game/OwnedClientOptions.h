#pragma once
#include "net/Session.h"
#include <cstdint>
#include <map>
#include <memory>
#include <optional>
#include <utility>
namespace god2 {
// CUSTOM-0100: transient untrusted display-preference material only. These
// WORD bits never grant permissions or change chat/filter/combat/game rules.
// Exact full common ownership is separate from opaque native option bits.
class OwnedClientOptions final {
public:
    struct Entry {
        std::weak_ptr<Session> session;
        std::uint64_t session_id,account,character;
        std::uint16_t word;
        std::uint64_t revision;
        Session::NormalWorldInitialization initialization;
        bool pending_replay=false;
        // Provisional exact original response; Queued is not Written/native ACK.
        std::optional<Session::NormalWorldResponseAttempt> response;
    };
    struct State {std::map<std::uint64_t,Entry> entries;};
    using Snapshot=std::shared_ptr<const State>;
    OwnedClientOptions():state_(std::make_shared<const State>()) {}
    Snapshot snapshot() const noexcept {return state_;}
    bool publish(const Snapshot& expected,Snapshot next) noexcept {
        if(state_!=expected || !next)return false;state_=std::move(next);return true;
    }
    void disconnect(const Session& session) {
        const auto at=state_->entries.find(session.id());
        if(at==state_->entries.end() || at->second.session.lock().get()!=&session)return;
        auto next=std::make_shared<State>(*state_);next->entries.erase(session.id());state_=std::move(next);
    }
    void ready(const Session& session) {
        const auto at=state_->entries.find(session.id());
        if(at==state_->entries.end() || at->second.session.lock().get()!=&session)return;
        // The real ready hook runs BEFORE ready/private initialization is
        // published. Mark only; later world records qualify the new receipt.
        if(at->second.account!=session.account_id || at->second.character!=session.character_id) {
            disconnect(session);return;
        }
        if(at->second.pending_replay)return;
        auto next=std::make_shared<State>(*state_);next->entries.at(session.id()).pending_replay=true;state_=std::move(next);
    }
private:
    Snapshot state_;
};
}
