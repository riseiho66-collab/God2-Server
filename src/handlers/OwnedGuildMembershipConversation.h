#pragma once
#include "protocol/RecoveredGuildMembership.h"
#include <chrono>
#include <cstdint>
#include <functional>
#include <map>
#include <optional>
#include <utility>

namespace god2 {
// CUSTOM-0078: admission lifecycle for configured membership and isolated QA.
// No client hint, old membership, UI role or stack byte grants authority.
// Caller must qualify a real interaction before open and supply a complete
// fresh owned world fingerprint at consume. C++ game-executor confined.
class OwnedGuildMembershipConversation {
public:
    using Wire=RecoveredGuildMembership;
    using Clock=std::chrono::steady_clock;
    using Time=Clock::time_point;
    static constexpr auto lifetime=std::chrono::seconds{30}; // CUSTOM, not original timer.
    struct Owner {
        std::uint64_t session{},account{},character{},world_generation{};
        std::uint32_t area{},scene{};
        std::int32_t x{},y{};
        std::uint16_t name_codepage{};
        // Separate monotonic lifecycle evidence prevents out-and-back ABA.
        // Neither value is taken from a client request or placed on the wire.
        std::uint64_t battle_generation{},position_revision{};
        bool operator==(const Owner&) const=default;
    };
    struct Accepted {
        Owner owner;
        Wire::Operation operation;
        Wire::Name name;
        bool operator==(const Accepted&) const=default;
    };
    using NameValidator=std::function<bool(const Wire::Name&,std::uint16_t)>;
    explicit OwnedGuildMembershipConversation(NameValidator validate):validate_(std::move(validate)) {}
    std::optional<Wire::Prompt> open(const Owner& owner,Wire::Operation operation,Time now,
                                     bool qualified_interaction) {
        if(!qualified_interaction || !valid(owner) || !Wire::supported(operation) || !validate_ ||
            now>Time::max()-lifetime)return {};
        const auto old=pending_.find(owner.session);
        if(old!=pending_.end()) {
            // Backward clock values cannot expire a live conversation.
            if(now<old->second.expires)return {};
            pending_.erase(old);
        }
        auto& generation=generations_[owner.session];
        // Context16 never wraps within one transport session. Reusing a
        // native nonce would allow delayed requests to bind a new opening.
        if(generation>=0xffff)return {};
        ++generation;
        const auto context=static_cast<std::uint16_t>(generation);
        pending_.emplace(owner.session,Pending{owner,operation,context,now,now+lifetime});
        return Wire::prompt(context,operation);
    }
    std::optional<Accepted> consume(const Owner& owner,const Wire::Request& request,Time now,
                                    bool qualified_interaction) {
        const auto it=pending_.find(owner.session);
        if(it==pending_.end())return {};
        const auto state=it->second;
        if(now>=state.expires) {pending_.erase(it);return {};}
        if(!qualified_interaction || !valid(owner) || owner!=state.owner) {
            pending_.erase(it);return {};
        }
        if(now<state.opened || request.context!=state.context || request.operation!=state.operation)return {};
        // A bound attempt is single-use even if name validation or later
        // storage fails. Caller must reopen; replay never retries a mutation.
        pending_.erase(it);
        const auto name=Wire::canonical(request);
        if(!name || (*name)[0]==0)return {};
        try {if(!validate_(*name,owner.name_codepage))return {};}
        catch(...) {return {};}
        return Accepted{owner,state.operation,*name};
    }
    // Rejected delivery of an old prompt must not revoke a later context.
    bool invalidate_exact(const Owner& owner,const Wire::Prompt& prompt) {
        const auto at=pending_.find(owner.session);
        if(at==pending_.end() || at->second.owner!=owner ||
            Wire::prompt(at->second.context,at->second.operation)!=std::optional{prompt})return false;
        pending_.erase(at);return true;
    }
    // On world departure/close clear permission, retain nonce generation.
    // Session IDs must be lifetime-unique. Transport disconnect may release
    // its clock only if the caller guarantees that ID is never reused.
    void invalidate(std::uint64_t session) {pending_.erase(session);}
    // Caller guarantees lifetime-unique disconnected transport IDs.
    void disconnect(std::uint64_t session) {pending_.erase(session);generations_.erase(session);}
    bool pending(std::uint64_t session) const {return pending_.contains(session);}
private:
    struct Pending {Owner owner;Wire::Operation operation;std::uint16_t context;Time opened,expires;};
    static bool valid(const Owner& owner) noexcept {
        return owner.session && owner.account && owner.character && owner.world_generation &&
            (owner.name_codepage==950 || owner.name_codepage==936);
    }
    NameValidator validate_;
    std::map<std::uint64_t,Pending> pending_;
    std::map<std::uint64_t,std::uint32_t> generations_;
};
}
