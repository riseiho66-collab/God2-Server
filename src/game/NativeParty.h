#pragma once
#include "protocol/RecoveredParty.h"
#include <algorithm>
#include <chrono>
#include <map>
#include <stdexcept>
#include <string>
namespace god2 {
// CUSTOM-0062: consenting transient parties, maximum5 from native four-peer
// roster. No shared movement, combat/XP/drop rules or persistent party guessed.
class NativeParty {
public:
    using Time=std::chrono::steady_clock::time_point;
    struct Member {
        std::uint64_t session{},account{};std::uint16_t character{},area{},scene{},x{},y{};
        std::string name;std::uint8_t profession{},transfer{},level{};
        std::array<std::uint8_t,4> hud{};
        // Preserve the complete source values before the recipient's native
        // HUD/projection gates. MP authority remains the original uint32 domain;
        // this snapshot carrier does not widen its gameplay or storage rules.
        std::array<std::uint64_t,4> resources{};
        bool ready{};
        bool operator==(const Member&) const=default;
    };
    // Read-only full ephemeral authority fence for the menu adapter. Includes
    // pending offers and their exact expiry, not just visible group membership.
    bool same_state(const NativeParty& other) const {
        return members_==other.members_ && membership_==other.membership_ && groups_==other.groups_ && pending_==other.pending_;
    }
    enum class Event {Preview,Add,Remove,Position,Vitals};
    struct Delivery {std::uint64_t recipient;Event event;Member actor;bool leader=false;};
    using Deliveries=std::vector<Delivery>;
    void observe(Member member) {
        if(!member.session || !member.account || !member.character || member.character>0x3fff || member.name.empty())
            throw std::invalid_argument("Party owner snapshot invalid");
        // CUSTOM-0062: a session's party and pending consent belong to this
        // exact account/character. Rebinding must disconnect the predecessor
        // first; refreshing stats must not transfer its membership or offers.
        if(const auto old=members_.find(member.session);old!=members_.end() &&
           (old->second.account!=member.account || old->second.character!=member.character))
            throw std::invalid_argument("Party session owner changed without retirement");
        for(const auto& [sid,peer]:members_)if(sid!=member.session && peer.character==member.character)
            throw std::invalid_argument("Party duplicate character lease");
        members_.insert_or_assign(member.session,std::move(member));
    }
    std::optional<Member> member(std::uint64_t session) const {
        const auto at=members_.find(session);return at==members_.end()?std::nullopt:std::optional{at->second};
    }
    std::size_t party_size(std::uint64_t session) const {
        const auto leader=membership_.find(session);if(leader==membership_.end())return 0;
        return groups_.at(leader->second).size();
    }
    std::vector<std::uint64_t> participants(std::uint64_t session) const {
        const auto at=membership_.find(session);
        return at==membership_.end()?std::vector<std::uint64_t>{session}:groups_.at(at->second);
    }
    Deliveries handle(std::uint64_t sender,const RecoveredParty::Request& request,Time now) {
        expire(now);const auto source=members_.find(sender);if(source==members_.end() || !source->second.ready)return {};
        if(request.kind==RecoveredParty::Kind::Leave) {
            if(request.self!=source->second.character)return {};
            return leave(sender);
        }
        if(request.kind==RecoveredParty::Kind::Kick) {
            const auto target=find(request.target);const auto own=membership_.find(sender);
            if(!target || *target==sender || own==membership_.end() || own->second!=sender ||
                !membership_.contains(*target) || membership_.at(*target)!=sender)return {};
            return leave(*target);
        }
        if(request.kind==RecoveredParty::Kind::Join) {
            const auto target=find(request.target);
            if(request.self!=source->second.character || !target || *target==sender || membership_.contains(sender) ||
                !compatible(source->second,members_.at(*target)))return {};
            if(membership_.contains(*target) && membership_.at(*target)!=*target)return {};
            if(party_size(*target)>=5)return {};
            for(const auto& [id,pending]:pending_)if(id==sender || pending.leader==*target)return {};
            pending_.emplace(sender,Pending{*target,now+std::chrono::seconds(30)});
            return {{*target,Event::Preview,source->second}};
        }
        // 4EA770 returns0 decline/1 accept;4EA8A0 emits2 if preview is busy.
        const auto joiner=find(request.target);if(!joiner || request.answer>2)return {};
        const auto offer=pending_.find(*joiner);
        if(offer==pending_.end() || offer->second.leader!=sender)return {};
        pending_.erase(offer);
        if(request.answer!=1 || membership_.contains(*joiner) || !compatible(members_.at(*joiner),source->second) ||
            (membership_.contains(sender) && membership_.at(sender)!=sender) || party_size(sender)>=5)return {};
        // A roster replay must not bypass the ready/resource/scene admission
        // boundary for an existing member who entered battle or changed scene.
        if(membership_.contains(sender))for(const auto peer:groups_.at(sender))
            if(!compatible(members_.at(peer),source->second))return {};
        if(!membership_.contains(sender)){groups_.emplace(sender,std::vector<std::uint64_t>{sender});membership_.emplace(sender,sender);}
        auto& group=groups_.at(sender);group.push_back(*joiner);membership_.emplace(*joiner,sender);
        Deliveries result;
        // Full bounded roster replay deduplicates by native name; actor metadata
        // for existing members stays authoritative, including the designated leader.
        for(const auto recipient:group)for(const auto actor:group) {
            result.push_back({recipient,Event::Add,members_.at(actor),actor==sender});
            if(actor!=recipient){result.push_back({recipient,Event::Position,members_.at(actor)});
                result.push_back({recipient,Event::Vitals,members_.at(actor)});}
        }
        return result;
    }
    Deliveries refresh(std::uint64_t session,const Member& before) const {
        Deliveries out;const auto at=membership_.find(session);if(at==membership_.end())return out;
        const auto& next=members_.at(session);if(!next.ready)return out;
        for(const auto recipient:groups_.at(at->second))if(recipient!=session && members_.at(recipient).ready) {
            if(next.area==members_.at(recipient).area && next.scene==members_.at(recipient).scene &&
                (!before.ready || next.x!=before.x || next.y!=before.y || next.area!=before.area || next.scene!=before.scene))
                out.push_back({recipient,Event::Position,next});
            if(!before.ready || next.resources!=before.resources)out.push_back({recipient,Event::Vitals,next});
            // A recipient can miss changes while unavailable. Rehydrate it
            // from the current authoritative snapshots, not just actor diffs.
            if(!before.ready || next.area!=before.area || next.scene!=before.scene) {
                const auto& peer=members_.at(recipient);
                if(next.area==peer.area && next.scene==peer.scene)
                    out.push_back({session,Event::Position,peer});
                out.push_back({session,Event::Vitals,peer});
            }
        }
        return out;
    }
    Deliveries disconnect(std::uint64_t sender) {
        auto out=leave(sender);members_.erase(sender);
        for(auto it=pending_.begin();it!=pending_.end();)if(it->first==sender || it->second.leader==sender)it=pending_.erase(it);else ++it;
        return out;
    }
private:
    struct Pending {std::uint64_t leader;Time expiry;bool operator==(const Pending&) const=default;};
    std::map<std::uint64_t,Member> members_;
    std::map<std::uint64_t,std::uint64_t> membership_;
    std::map<std::uint64_t,std::vector<std::uint64_t>> groups_;
    std::map<std::uint64_t,Pending> pending_;
    void expire(Time now){for(auto it=pending_.begin();it!=pending_.end();)if(it->second.expiry<=now)it=pending_.erase(it);else ++it;}
    std::optional<std::uint64_t> find(std::uint32_t character)const {
        for(const auto& [sid,m]:members_)if(m.character==character)return sid;return {};
    }
    static bool compatible(const Member& a,const Member& b){return a.ready && b.ready && a.area==b.area && a.scene==b.scene;}
    Deliveries leave(std::uint64_t sender) {
        // Leaving also revokes outstanding offers before membership exists.
        for(auto it=pending_.begin();it!=pending_.end();)if(it->first==sender || it->second.leader==sender)it=pending_.erase(it);else ++it;
        const auto at=membership_.find(sender);if(at==membership_.end())return {};
        const auto leader=at->second;auto group=groups_.at(leader);Deliveries out;
        if(sender==leader) {
            for(const auto recipient:group)for(const auto actor:group)out.push_back({recipient,Event::Remove,members_.at(actor)});
            for(const auto actor:group)membership_.erase(actor);groups_.erase(leader);
        } else {
            for(const auto recipient:group)out.push_back({recipient,Event::Remove,members_.at(sender)});
            membership_.erase(sender);std::erase(groups_.at(leader),sender);
            if(groups_.at(leader).size()==1){membership_.erase(leader);groups_.erase(leader);}
        }
        for(auto it=pending_.begin();it!=pending_.end();)if(it->first==sender || it->second.leader==sender)it=pending_.erase(it);else ++it;
        return out;
    }
};
}
