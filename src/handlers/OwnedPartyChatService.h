#pragma once
#include "game/NativeParty.h"
#include "protocol/RecoveredPartyChat.h"
#include <functional>
namespace god2 {
// CUSTOM-0073: authenticated transient-party audience; no common-chat rewrite.
// Native selector1 proves display routing, not original server audience policy.
class OwnedPartyChatService {
public:
    struct Peer {
        NativeParty::Member member;
        bool simplified{};
        std::uint8_t privilege{};
        bool operator==(const Peer&) const=default;
    };
    struct Delivery {std::uint64_t recipient;std::vector<std::uint8_t> logical;};
    using Resolve=std::function<std::optional<Peer>(std::uint64_t)>;
    using Prepare=std::function<std::vector<std::uint8_t>(const Peer&,const Peer&,const RecoveredPartyChat::Request&)>;
    OwnedPartyChatService(Resolve resolve,Prepare prepare):resolve_(std::move(resolve)),prepare_(std::move(prepare)){}
    std::optional<std::vector<Delivery>> prepare(const NativeParty& parties,std::uint64_t sender,
        std::span<const RecoveredPartyChat::Request> requests) const {
        try {
            if(!resolve_ || !prepare_ || !sender || requests.empty() || parties.party_size(sender)<2)return {};
            const auto group=parties.participants(sender);
            if(group.size()<2 || group.size()>5 || std::count(group.begin(),group.end(),sender)!=1)return {};
            std::map<std::uint64_t,NativeParty::Member> cached;
            std::map<std::uint64_t,Peer> current;
            for(const auto id:group) {
                const auto old=parties.member(id);const auto fresh=resolve_(id);
                if(!old || !fresh || !owns(*old,fresh->member,id))return {};
                cached.emplace(id,*old);current.emplace(id,*fresh);
            }
            const auto& source=current.at(sender);
            if(!source.member.ready)return {};
            std::vector<Delivery> deliveries;
            for(const auto& request:requests) {
                // Revalidate text bounds even for callers bypassing the parser.
                RecoveredPartyChat::encode(request);
                for(const auto& [id,peer]:current)if(peer.member.ready) {
                    auto wire=prepare_(source,peer,request);
                    if(!display_valid(wire,source,peer))return {};
                    deliveries.push_back({id,std::move(wire)});
                }
            }
            // Publish nothing if a callback changed any audience lease/state.
            if(parties.participants(sender)!=group || parties.party_size(sender)!=group.size())return {};
            for(const auto& [id,peer]:current) {
                const auto after=resolve_(id);
                if(!after || *after!=peer || parties.member(id)!=std::optional{cached.at(id)})return {};
            }
            return deliveries;
        } catch(...) {return {};}
    }
private:
    static bool owns(const NativeParty::Member& old,const NativeParty::Member& fresh,std::uint64_t id) {
        return id && old.session==id && fresh.session==id && fresh.account && fresh.character &&
            fresh.account==old.account && fresh.character==old.character && !fresh.name.empty();
    }
    static bool display_valid(const std::vector<std::uint8_t>& wire,const Peer& source,const Peer& recipient) {
        if(wire.size()<15 || wire.size()>RecoveredChat::max_text_bytes+14 || wire[0]!=0x5c ||
            (std::size_t{wire[1]}+256u*wire[2])!=wire.size() || wire.back()!=0 ||
            wire[9]!=static_cast<std::uint8_t>((recipient.simplified?0x80:0)|1) ||
            std::find(wire.begin()+13,wire.end()-1,0)!=wire.end()-1)return false;
        const auto actor=std::uint32_t{wire[5]}|(std::uint32_t{wire[6]}<<8)|(std::uint32_t{wire[7]}<<16)|(std::uint32_t{wire[8]}<<24);
        return actor==source.member.character;
    }
    Resolve resolve_;Prepare prepare_;
};
}
