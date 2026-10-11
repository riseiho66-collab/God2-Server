#pragma once
#include "protocol/RecoveredPet2Stats.h"
#include "protocol/RecoveredSelectionItemRequest.h"
#include <vector>

namespace god2 {
// Native 49A330 -> 496550: reserve slots42/43 -> active slot44 sends
// 28 key:u16 source:u8 01 (no destination byte), followed by 1F 00.
// This codec does not choose a free return slot, grant pets, or calculate stats.
struct RecoveredPet2Lifecycle {
    using Metadata = std::array<std::uint8_t,20>;
    struct Owner { std::uint64_t account, character; };
    struct Context { Owner owner; bool world_ready; bool in_battle; };
    struct Snapshot {
        Owner owner;
        Metadata inventory;
        RecoveredPet2Stats::Record stats;
    };
    enum class Intent { SelectReserve, ReturnActive };
    struct Request { std::uint16_t key; std::uint8_t source; Intent intent; };
    static bool same_owner(Owner a, Owner b) noexcept {
        return a.account && a.character && a.account==b.account && a.character==b.character;
    }
    static std::optional<Request> decode(std::span<const std::uint8_t> bytes) noexcept {
        const auto r=RecoveredSelectionItemRequest::decode(bytes);
        if(!r || r->raw_slot<42 || r->raw_slot>44) return std::nullopt;
        return Request{r->client_item_id,r->raw_slot,
            r->raw_slot==44 ? Intent::ReturnActive : Intent::SelectReserve};
    }
    // Resolver must validate an actual build-matched NCP metadata row, not a
    // range alone. All opaque bytes come from an explicitly owned snapshot.
    template<class Resolver>
    static bool valid(const Context& context,const Snapshot& pet,Resolver resolves) {
        const auto key=static_cast<std::uint16_t>(pet.inventory[0] | (std::uint16_t{pet.inventory[1]}<<8));
        return context.world_ready && !context.in_battle && same_owner(context.owner,pet.owner) &&
            (pet.inventory[2]&0x3f)==34 && key==pet.stats.metadata_key() && resolves(key);
    }
    template<class Resolver>
    static bool accepts(const Context& context,const Request& request,const Snapshot& source,Resolver resolves) {
        return valid(context,source,resolves) && request.source==source.stats.slot() &&
            request.key==source.stats.metadata_key() && request.source>=42 && request.source<=44 &&
            request.intent==(request.source==44 ? Intent::ReturnActive : Intent::SelectReserve);
    }
    static void clear(std::vector<std::uint8_t>& out,std::uint8_t slot) {
        // 4991E0 -> A2C90: retained type34 clears all72 cached bytes, closes
        // the pet panel, and invokes AD080 (slot44 HUD). Never send FB key0.
        out.insert(out.end(),{0x41,0,0,slot,0});
    }
    static void append(std::vector<std::uint8_t>& out,const Snapshot& pet,std::uint8_t slot) {
        out.insert(out.end(),{0x3b,1,slot,0,0});
        out.insert(out.end(),pet.inventory.begin(),pet.inventory.end());
        out.insert(out.end(),{0x41,pet.inventory[0],pet.inventory[1],slot,1});
        auto stats=RecoveredPet2Stats::encode_logical(pet.stats);
        stats[3]=slot; // Only the native record's routing slot changes.
        out.insert(out.end(),stats.begin(),stats.end());
    }
    template<class Resolver>
    static std::optional<std::vector<std::uint8_t>> restore(
        const Context& context,const Snapshot& pet,Resolver resolves) {
        if(!valid(context,pet,resolves)) return std::nullopt;
        std::vector<std::uint8_t> out;
        clear(out,pet.stats.slot()); append(out,pet,pet.stats.slot());
        return out;
    }
    // Caller picks destination from authoritative storage, then atomically
    // commits both records with revision/ownership checks before sending this
    // projection. A failed commit must not send this speculative after-state.
    // Return-active currently supports empty reserve only; no arbitrary swap
    // destination or item consumption is inferred from the native request.
    template<class Resolver>
    static std::optional<std::vector<std::uint8_t>> transfer(
        const Context& context,const Request& request,const Snapshot& source,
        std::uint8_t destination,const std::optional<Snapshot>& existing,Resolver resolves) {
        if(!accepts(context,request,source,resolves) || destination==request.source) return std::nullopt;
        if(request.intent==Intent::SelectReserve ? destination!=44 :
            (destination<42 || destination>43 || existing.has_value())) return std::nullopt;
        if(existing && (!valid(context,*existing,resolves) || existing->stats.slot()!=destination)) return std::nullopt;
        std::vector<std::uint8_t> out;
        clear(out,request.source); clear(out,destination);
        if(existing) append(out,*existing,request.source);
        append(out,source,destination);
        return out;
    }
};
}
