#pragma once
#include "game/NativeParty.h"
#include "protocol/RecoveredPartyPositionQuery.h"
#include <functional>

namespace god2 {
// CUSTOM-0072: readonly position query within the existing consenting party.
// Native56 has no area/map identity; do not project another map's coordinates
// through the requester's current-map descriptor or invent a cross-map reply.
class OwnedPartyPositionQuery {
public:
    using Resolve=std::function<std::optional<NativeParty::Member>(std::uint64_t)>;
    explicit OwnedPartyPositionQuery(Resolve resolve):resolve_(std::move(resolve)){}
    std::optional<std::vector<std::uint8_t>> query(const NativeParty& parties,
        std::uint64_t sender,const RecoveredPartyPositionQuery::Request& request) const {
        try {
            if(!resolve_ || !sender || !request.target || request.target>=3000 || parties.party_size(sender)<2)return {};
            const auto group=parties.participants(sender);
            if(group.size()<2 || group.size()>5 || std::count(group.begin(),group.end(),sender)!=1)return {};
            const auto cached_source=parties.member(sender);
            if(!cached_source || request.target==cached_source->character)return {};
            std::optional<NativeParty::Member> cached_target;
            for(const auto id:group)if(const auto member=parties.member(id);member && member->character==request.target) {
                if(cached_target)return {};cached_target=member;
            }
            if(!cached_target || cached_target->session==sender)return {};
            const auto source=resolve_(sender),target=resolve_(cached_target->session);
            if(!source || !target || !owns(*cached_source,*source,sender) ||
                !owns(*cached_target,*target,cached_target->session) || !source->ready || !target->ready ||
                source->area!=target->area || source->scene!=target->scene || target->x>0x7fff || target->y>0x7fff)return {};
            auto logical=RecoveredParty::position(target->character,target->x,target->y);
            // Preparation/observation callbacks cannot authorize an old lease or
            // publish coordinates after a party/scene/readiness change.
            const auto source_after=resolve_(sender),target_after=resolve_(target->session);
            if(!source_after || !target_after || *source_after!=*source || *target_after!=*target ||
                parties.party_size(sender)!=group.size() || parties.participants(sender)!=group ||
                parties.member(sender)!=cached_source || parties.member(target->session)!=cached_target)return {};
            return logical;
        } catch(...) {return {};}
    }
private:
    static bool owns(const NativeParty::Member& cached,const NativeParty::Member& fresh,std::uint64_t session) {
        return session && fresh.session==session && cached.session==session && fresh.account &&
            fresh.character && cached.account==fresh.account && cached.character==fresh.character;
    }
    Resolve resolve_;
};
}
