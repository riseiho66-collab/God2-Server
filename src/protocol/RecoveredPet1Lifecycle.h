#pragma once
#include "protocol/RecoveredPet1Stats.h"
#include "protocol/RecoveredPet2Lifecycle.h"
namespace god2 {
// E3 snapshots occupy the same native cells42..44 as FB. No second capacity.
struct RecoveredPet1Lifecycle {
    using Owner=RecoveredPet2Lifecycle::Owner;
    using Context=RecoveredPet2Lifecycle::Context;
    using Metadata=RecoveredPet2Lifecycle::Metadata;
    using Request=RecoveredPet2Lifecycle::Request;
    struct Snapshot {Owner owner;Metadata inventory;RecoveredPet1Stats::Record stats;};
    template<class Resolver> static bool valid(const Context& context,const Snapshot& pet,Resolver resolves) {
        const auto key=static_cast<std::uint16_t>(pet.inventory[0]|(std::uint16_t{pet.inventory[1]}<<8));
        return context.world_ready && !context.in_battle && RecoveredPet2Lifecycle::same_owner(context.owner,pet.owner) &&
            (pet.inventory[2]&0x3f)==32 && key==pet.stats.metadata_key() && resolves(key);
    }
    template<class Resolver> static bool accepts(const Context& context,const Request& request,const Snapshot& pet,Resolver resolves) {
        return valid(context,pet,resolves) && request.key==pet.stats.metadata_key() && request.source==pet.stats.slot() &&
            request.intent==(request.source==44?RecoveredPet2Lifecycle::Intent::ReturnActive:RecoveredPet2Lifecycle::Intent::SelectReserve);
    }
    static void append(std::vector<std::uint8_t>& out,const Snapshot& pet,std::uint8_t slot) {
        out.insert(out.end(),{0x3b,1,slot,0,0});out.insert(out.end(),pet.inventory.begin(),pet.inventory.end());
        out.insert(out.end(),{0x41,pet.inventory[0],pet.inventory[1],slot,1});
        auto bytes=RecoveredPet1Stats::encode_logical(pet.stats);bytes[0x27]=slot;
        out.insert(out.end(),bytes.begin(),bytes.end());
    }
};
}
