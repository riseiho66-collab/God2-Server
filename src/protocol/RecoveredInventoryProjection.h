#pragma once
#include "protocol/RecoveredInventory.h"
#include <algorithm>
#include <array>
#include <cstdint>
#include <optional>
#include <vector>

namespace god2 {
// Current S2C3B/41 consumers 498DD0/4991E0. This projects supplied instance
// bytes; it does not recover ownership, attributes, stacking or item grants.
// Caller must label invented instance bytes (e.g. id + 18 zero bytes) CUSTOM.
struct RecoveredInventoryProjection {
    using Metadata = std::array<std::uint8_t,20>;
    struct Slot { std::uint8_t index; std::uint8_t count; Metadata metadata; };

    // Restricted to ordinary bag slots. The three reserved bytes at client
    // slot+1..3 remain unchanged. All 20 metadata bytes of occupied slots are
    // replaced; clearing an empty slot preserves its now-inactive metadata.
    static std::optional<std::vector<std::uint8_t>> encode(const Slot& slot) {
        if(slot.index>=30 || slot.count>127) return std::nullopt;
        const auto item=static_cast<std::uint16_t>(slot.metadata[0]+256u*slot.metadata[1]);
        if((slot.count==0)!=(item==0)) return std::nullopt;
        const auto clear=RecoveredInventory::clear_slot(slot.index);
        std::vector<std::uint8_t> result(clear->begin(),clear->end());
        if(slot.count==0) return result;
        // 3B may add stack counts or force one, depending on the native item
        // definition. Clear before it and finish with an absolute 41 count.
        result.insert(result.end(),{0x3b,slot.count,slot.index,0,0});
        result.insert(result.end(),slot.metadata.begin(),slot.metadata.end());
        const auto absolute=RecoveredInventory::encode_slot_update({item,slot.index,slot.count});
        result.insert(result.end(),absolute->begin(),absolute->end());
        return result;
    }
};
}
