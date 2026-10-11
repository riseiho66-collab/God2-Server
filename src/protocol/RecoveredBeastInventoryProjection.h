#pragma once
#include "protocol/RecoveredInventoryProjection.h"
#include "db/NativeBeastSourceCatalog.h"
namespace god2 {
// Native3B/41 accepts50 slots, but PET equipment is specifically37. Keep
// generic ordinary-bag projection frozen. No riding/stat/appearance effect.
struct RecoveredBeastInventoryProjection {
    static constexpr std::uint8_t equipped_slot=37;
    static bool domain(std::uint8_t slot) noexcept{return slot<30||slot==equipped_slot;}
    static std::optional<std::vector<std::uint8_t>> encode(const RecoveredInventoryProjection::Slot& slot){
        if(slot.index<30)return RecoveredInventoryProjection::encode(slot);
        if(slot.index!=equipped_slot||slot.count>1)return {};
        const auto key=static_cast<std::uint16_t>(slot.metadata[0]|(std::uint16_t{slot.metadata[1]}<<8));
        if((slot.count==0)!=(key==0))return {};
        if(slot.count&&(!NativeBeastSourceCatalog::lookup(key)||(slot.metadata[2]&0x3f)!=5))return {};
        const auto clear=RecoveredInventory::clear_slot(slot.index).value();
        std::vector<std::uint8_t> out(clear.begin(),clear.end());
        if(!slot.count)return out;
        out.insert(out.end(),{0x3b,1,slot.index,0,0});out.insert(out.end(),slot.metadata.begin(),slot.metadata.end());
        const auto absolute=RecoveredInventory::encode_slot_update({key,slot.index,1}).value();out.insert(out.end(),absolute.begin(),absolute.end());return out;
    }
};
}
