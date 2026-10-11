#pragma once
#include "db/NativeEquipmentSnapshotRepository.h"
#include "game/SharedTaiwanOwnedItemSelectionSource.h"
#include "protocol/RecoveredInstanceUpdate.h"
#include "protocol/RecoveredTaiwanInventoryItemRecord.h"
#include <algorithm>

namespace god2 {
// CUSTOM-0094 source material, not recovered original server relocation rules.
// Both aliases must originate from one genuine full25 source declaration.
// Retaining its opaque/count across a slot change is an explicit opt-in policy;
// opaque helper compatibility and current native acceptance remain OPEN.
struct TaiwanOwnedBagItemMaterial {
    static constexpr const char* profile="tw149c-item3b25-material";
    static std::optional<RecoveredTaiwanInventoryItemRecord::Fields> observe(
        const OwnedInventoryInstance& item,std::uint8_t slot) {
        if(item.aliases.size()!=2)return std::nullopt;
        const auto& identity=item.aliases[0];const auto& material=item.aliases[1];
        if(identity.client_sha256!=NativeEquipmentSnapshot::client_pin ||
           material.client_sha256!=identity.client_sha256 ||
           identity.profile!=SharedTaiwanOwnedItemSelectionSource::alias_profile || material.profile!=profile ||
           identity.native_slot!=slot || material.native_slot!=slot ||
           identity.native_key!=material.native_key || !identity.native_key ||
           identity.revision!=item.revision || material.revision!=item.revision ||
           identity.source_sha256!=material.source_sha256 || identity.source_record!=material.source_record ||
           identity.record.size()!=20)return std::nullopt;
        const auto parsed=RecoveredInstanceUpdate::parse_logical(material.record);
        if(!parsed)return std::nullopt;
        const auto raw=RecoveredInstanceUpdate::encode_logical(*parsed);
        // The source count is retained as an incoming count, never quantity.
        // This capability restricts its positive-byte subset independently.
        if(raw[1]==0 || raw[1]>99 || raw[2]!=slot || parsed->low_word_lookup_key()!=identity.native_key ||
           !std::equal(identity.record.begin(),identity.record.end(),raw.begin()+5))return std::nullopt;
        RecoveredTaiwanInventoryItemRecord::Instance instance;
        std::copy(raw.begin()+5,raw.end(),instance.begin());
        return RecoveredTaiwanInventoryItemRecord::Fields(raw[1],raw[2],
            std::uint16_t(raw[3]+256u*raw[4]),instance);
    }
};
}
