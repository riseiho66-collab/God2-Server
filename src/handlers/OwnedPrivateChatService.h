#pragma once
#include "protocol/RecoveredPrivateChat.h"
#include <functional>
#include <map>
namespace god2 {
// CUSTOM-0074: exact owned online-name audience, source+target only, no SQL
// writes. Native client proves private display, not original server name policy.
class OwnedPrivateChatService {
public:
    struct Peer {
        std::uint64_t session{},account{};std::uint32_t character{};
        std::string name;bool ready{},simplified{};std::uint8_t privilege{};
        bool operator==(const Peer&) const=default;
    };
    struct Delivery {std::uint64_t recipient;std::vector<std::uint8_t> logical;};
    using Resolve=std::function<std::optional<Peer>(std::uint64_t)>;
    using Audience=std::function<std::vector<Peer>()>;
    using Decode=std::function<std::string(const Peer&,const RecoveredPrivateChat::Request&)>;
    using Prepare=std::function<std::vector<std::uint8_t>(const Peer&,const Peer&,const Peer&,
        const RecoveredPrivateChat::Request&,const RecoveredPrivateChat::Text&)>;
    OwnedPrivateChatService(Resolve resolve,Audience audience,Decode decode,Prepare prepare):
        resolve_(std::move(resolve)),audience_(std::move(audience)),decode_(std::move(decode)),prepare_(std::move(prepare)){}
    std::optional<std::vector<Delivery>> prepare(std::uint64_t sender,
        std::span<const RecoveredPrivateChat::Request> requests) const {
        try {
            if(!resolve_ || !audience_ || !decode_ || !prepare_ || !sender || requests.empty())return {};
            const auto source=resolve_(sender);
            if(!source || !valid(*source) || source->session!=sender || !source->ready || !name_supported(source->name))return {};
            const auto audience=index(audience_());
            if(!audience || !audience->contains(sender) || audience->at(sender)!=*source)return {};
            std::vector<Delivery> deliveries;
            for(const auto& request:requests) {
                RecoveredPrivateChat::encode(request);
                const auto text=RecoveredPrivateChat::split(decode_(*source,request));if(!text)return {};
                const Peer* target=nullptr;
                for(const auto& [id,peer]:*audience)if(peer.name==text->recipient) {
                    if(target)return {};target=&peer;
                }
                if(!target || !target->ready || target->session==sender || !name_supported(target->name))return {};
                for(const auto* recipient:{&*source,target}) {
                    auto wire=prepare_(*source,*target,*recipient,request,*text);
                    if(!display_valid(wire,*source,*recipient,request.client_header[0]&0x7f))return {};
                    deliveries.push_back({recipient->session,std::move(wire)});
                }
            }
            // Recheck all names to prevent late ambiguity, plus fresh owner
            // leases before publishing any part of a multi-message batch.
            if(index(audience_())!=audience)return {};
            for(const auto& delivery:deliveries) {
                const auto after=resolve_(delivery.recipient);
                if(!after || *after!=audience->at(delivery.recipient))return {};
            }
            return deliveries;
        }catch(...) {return {};}
    }
private:
    static bool name_supported(std::string_view name) {
        // These delimiters are parsed by native47DD60/47EEB0. Reject names
        // that cannot form an unambiguous native private conversation.
        return name.find_first_of(" :[]$\r\n\t")==std::string_view::npos;
    }
    static bool valid(const Peer& peer) {
        return peer.session && peer.account && peer.character && peer.character<=0x3fff && !peer.name.empty();
    }
    static std::optional<std::map<std::uint64_t,Peer>> index(const std::vector<Peer>& peers) {
        std::map<std::uint64_t,Peer> result;std::map<std::uint32_t,std::uint64_t> characters;
        for(const auto& peer:peers)if(!valid(peer) || !result.emplace(peer.session,peer).second ||
            !characters.emplace(peer.character,peer.session).second)return {};
        return result;
    }
    static bool display_valid(const std::vector<std::uint8_t>& wire,const Peer& source,const Peer& recipient,std::uint8_t mode) {
        if(wire.size()<15 || wire.size()>RecoveredChat::max_text_bytes+14 || wire[0]!=0x5c ||
            (std::size_t{wire[1]}+256u*wire[2])!=wire.size() || wire.back()!=0 ||
            wire[9]!=static_cast<std::uint8_t>((recipient.simplified?0x80:0)|mode) ||
            std::find(wire.begin()+13,wire.end()-1,0)!=wire.end()-1)return false;
        const auto actor=std::uint32_t{wire[5]}|(std::uint32_t{wire[6]}<<8)|(std::uint32_t{wire[7]}<<16)|(std::uint32_t{wire[8]}<<24);
        return actor==source.character;
    }
    Resolve resolve_;Audience audience_;Decode decode_;Prepare prepare_;
};
}
