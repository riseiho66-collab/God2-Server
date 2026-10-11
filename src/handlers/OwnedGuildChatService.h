#pragma once
#include "handlers/OwnedPrivateChatService.h"
#include "db/SqliteGuildRepository.h"
#include "protocol/RecoveredGuildChat.h"
#include <set>
namespace god2 {
// CUSTOM-0075: persistent administrator-configured guild membership governs
// audience. Native mode3/2D proves UI routing, not original guild economics.
// Fresh owner/membership leases are checked again before any publication.
class OwnedGuildChatService {
public:
    struct Peer {
        OwnedPrivateChatService::Peer actor;
        StoredGuildMembership membership;
        bool operator==(const Peer&) const=default;
    };
    struct Delivery {std::uint64_t recipient;std::vector<std::uint8_t> logical;};
    using Resolve=std::function<std::optional<Peer>(std::uint64_t)>;
    using Audience=std::function<std::vector<Peer>()>;
    using Prepare=std::function<std::vector<std::uint8_t>(const Peer&,const Peer&,const RecoveredGuildChat::Request&)>;
    OwnedGuildChatService(Resolve resolve,Audience audience,Prepare prepare):
        resolve_(std::move(resolve)),audience_(std::move(audience)),prepare_(std::move(prepare)){}
    std::optional<std::vector<Delivery>> prepare(std::uint64_t sender,std::span<const RecoveredGuildChat::Request> requests) const {
        try {
            if(!sender || requests.empty() || !resolve_ || !audience_ || !prepare_)return {};
            const auto source=resolve_(sender);
            if(!source || !valid(*source) || !source->actor.ready)return {};
            const auto group=members(audience_(),source->membership.guild_id);
            if(!group || !group->contains(sender) || group->at(sender)!=*source)return {};
            std::vector<Delivery> out;
            for(const auto& request:requests) {
                RecoveredGuildChat::encode(request);
                for(const auto& [id,peer]:*group)if(peer.actor.ready) {
                    const auto fresh=resolve_(id);if(!fresh || *fresh!=peer)return {};
                    auto wire=prepare_(*source,peer,request);
                    if(!display_valid(wire,*source,peer))return {};
                    out.push_back({id,std::move(wire)});
                }
            }
            if(members(audience_(),source->membership.guild_id)!=group)return {};
            for(const auto& [id,peer]:*group)if(resolve_(id)!=std::optional{peer})return {};
            return out;
        }catch(...){return {};}
    }
private:
    using Group=std::map<std::uint64_t,Peer>;
    static bool valid(const Peer& peer) {
        return peer.actor.session && peer.actor.account && peer.actor.character &&
            !peer.actor.name.empty() && peer.membership.guild_id && !peer.membership.name_utf8.empty() &&
            peer.membership.guild_revision && peer.membership.membership_revision;
    }
    static std::optional<Group> members(const std::vector<Peer>& audience,std::uint64_t guild) {
        Group out;std::set<std::uint32_t> characters;
        for(const auto& peer:audience)if(peer.membership.guild_id==guild) {
            if(!valid(peer) || !out.emplace(peer.actor.session,peer).second ||
               !characters.insert(peer.actor.character).second)return {};
        }
        return out;
    }
    static bool display_valid(const std::vector<std::uint8_t>& wire,const Peer& source,const Peer& recipient) {
        if(wire.size()<15 || wire.size()>RecoveredChat::max_text_bytes+14 || wire[0]!=0x5c ||
           (std::size_t{wire[1]}+256u*wire[2])!=wire.size() || wire.back()!=0 ||
           wire[9]!=static_cast<std::uint8_t>((recipient.actor.simplified?0x80:0)|3) ||
           std::find(wire.begin()+13,wire.end()-1,0)!=wire.end()-1)return false;
        const auto actor=std::uint32_t{wire[5]}|(std::uint32_t{wire[6]}<<8)|(std::uint32_t{wire[7]}<<16)|(std::uint32_t{wire[8]}<<24);
        return actor==source.actor.character;
    }
    Resolve resolve_;Audience audience_;Prepare prepare_;
};
}
