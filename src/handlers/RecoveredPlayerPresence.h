#pragma once
#include "handlers/RecoveredVisibility.h"
#include "protocol/RecoveredCharacterListCandidate.h"
#include "protocol/RecoveredWorldFrame.h"

namespace god2 {
// CUSTOM-0027: checked projection, not an allocator or ownership lookup.
// Caller supplies an authenticated profile and qualified spawn/removal templates.
struct RecoveredPlayerPresence {
    static RecoveredVisibility::Presence from_world_entry(
        std::uint64_t session,std::uint64_t account,std::uint64_t character,
        std::span<const std::uint8_t> wire,const std::array<std::uint8_t,40>& profile,
        const RecoveredRemoteActor::Record& spawn_template,
        const RecoveredRemoteActorRemove::Record& removal_template) {
        if(!session || !account || !character || character>0xfff ||
           !RecoveredCharacterListCandidate::valid_profile(profile))
            throw std::invalid_argument("Player presence identity/profile rejected");
        const auto logical=RecoveredWorldFrame::decode(wire);
        if(!logical || logical->size()!=37 || logical->front()!=0x2a)
            throw std::invalid_argument("Player presence world frame rejected");
        const auto body=std::span<const std::uint8_t>(*logical).subspan(1);
        const auto u32=[&](std::size_t offset) {
            return std::uint32_t{body[offset]}|(std::uint32_t{body[offset+1]}<<8)|
                (std::uint32_t{body[offset+2]}<<16)|(std::uint32_t{body[offset+3]}<<24);
        };
        const auto map=u32(24)&0xffff;
        const auto area=static_cast<std::uint16_t>(map&63);
        const auto scene=static_cast<std::uint16_t>(map>>6);
        const auto point=u32(28);
        const auto x=(point>>2)&0x7fff,y=point>>17;
        const auto original=RecoveredRemoteActor::encode_logical(spawn_template);
        const auto world_kind=point&3u;
        // Current CAN area2/0 Island01 and area4/0 Island03 are kind1.
        // Scope this projection to those qualified source scenes; kind1 is
        // not a generic authority for another world map.
        const bool island_kind=world_kind==1 && scene==0 && (area==2 || area==4);
        if((u32(0)&0x3fff)!=character || area<1 || area>16 || x>0x7ff || y>0x7ff ||
           (world_kind!=0 && world_kind!=2 && !island_kind) || (scene==15 && world_kind!=2))
            throw std::invalid_argument("Player presence world binding/position rejected");
        // The template was captured indoors(kind2). Preserve owning 2A kind0
        // city / kind1 qualified island / kind2 indoor in the peer6F low bits.
        auto normalized=original;
        normalized[13]=static_cast<std::uint8_t>((normalized[13]&~3u)|world_kind);
        auto spawn=RecoveredRemoteActor::with_identity(
            RecoveredRemoteActor::parse_logical(normalized).value(),character).value();
        spawn=RecoveredRemoteActor::with_position(spawn,x,y).value();
        const auto appearance=RecoveredRemoteActor::with_normal_world_components(spawn,body);
        if(!appearance) throw std::invalid_argument("Player presence appearance unqualified");
        const auto name_end=std::find(profile.begin(),profile.begin()+15,0);
        std::array<std::span<const std::uint8_t>,3> fields{
            std::span<const std::uint8_t>(profile.data(),static_cast<std::size_t>(name_end-profile.begin())),{},{}
        };
        for(std::size_t index=1;index<3;++index) {
            const auto start=original.begin()+29+16*index;
            fields[index]={&*start,static_cast<std::size_t>(std::find(start,start+16,0)-start)};
        }
        const auto named=RecoveredRemoteActor::with_text_fields(*appearance,fields);
        if(!named) throw std::invalid_argument("Player presence text rejected");
        return {session,account,character,{area,scene},*named,
            RecoveredRemoteActorRemove::with_identity(removal_template,character).value()};
    }
};
}
