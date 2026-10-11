#pragma once
#include "db/SqlitePlayerAppearanceRepository.h"
#include "db/SqliteWeaponSlotRepository.h"
#include "db/DbTypes.h"
#include "protocol/RecoveredWorldFrame.h"
#include <algorithm>
namespace god2 {
struct RecoveredOwnedPlayerAppearance {
    // Native2A body32..33 -> DA transform, body34/35 -> raw scalar5/6.
    // Current46827B/468284/46828A/468558/46855D. Ownership is caller/repository.
    static RecoveredPlayerAppearanceUpdate::Fields from_body(std::span<const std::uint8_t> body) {
        if(body.size()!=36)throw DatabaseError("Owned appearance world body size");
        RecoveredPlayerAppearanceUpdate::Fields result{
            static_cast<std::uint16_t>((body[0]+256u*body[1])&0x3fff),
            static_cast<std::uint16_t>(body[32]+256u*body[33]),body[34],body[35],{}};
        std::copy_n(body.begin()+12,8,result.components.begin());return result;
    }
    static std::vector<std::uint8_t> world_entry(std::span<const std::uint8_t> wire,const StoredPlayerAppearance& saved) {
        auto logical=RecoveredWorldFrame::decode(wire);
        if(!logical || logical->size()!=37 || logical->front()!=0x2a ||
           from_body(std::span(*logical).subspan(1)).actor_identity!=saved.fields.actor_identity || saved.fields.transform_key)
            throw DatabaseError("Owned appearance world binding rejected");
        std::copy(saved.fields.components.begin(),saved.fields.components.end(),logical->begin()+13);
        (*logical)[33]=0;(*logical)[34]=0;(*logical)[35]=saved.fields.raw_scalar5;(*logical)[36]=saved.fields.raw_scalar6;
        return RecoveredWorldFrame::encode(*logical);
    }
    // CUSTOM-0047 isolated operand mapping, NOT original WPN-to-DA authority.
    // Only the two exact synthetic acceptance instances qualify. No stats/grant.
    static RecoveredPlayerAppearanceUpdate::Fields fixture_after(const StoredPlayerAppearance& before,const WeaponSlotMove& move) {
        if(before.origin!="CUSTOM_TEST_NOT_NATIVE" || before.fields.transform_key ||
           (before.base_components[6]&15)>1 || before.base_components[7])
            throw DatabaseError("Diagnostic appearance baseline rejected");
        const auto* wear=move.source.slot==34?&move.source:(move.destination.slot==34?&move.destination:nullptr);
        if(!wear)throw DatabaseError("Diagnostic appearance without equipment change");
        auto fields=before.fields;
        fields.components[6]=before.base_components[6];fields.components[7]=before.base_components[7];
        if(!wear->count)return fields;
        constexpr std::array<std::uint8_t,20> one{1,0,1,0,0,0,0,24,0,0,0,0,6,0,0,0,0,0,0,0};
        constexpr std::array<std::uint8_t,20> two{2,0,1,0,0,0,0,30,0,0,0,0,10,0,0,0,0,0,0,0};
        if(wear->count!=1 || wear->origin!="CUSTOM_TEST_NOT_NATIVE" || (wear->logical20!=one && wear->logical20!=two))
            throw DatabaseError("Diagnostic weapon appearance instance rejected");
        fields.components[6]=static_cast<std::uint8_t>(before.base_components[6]&15);
        fields.components[7]=wear->logical20==one?0:1;
        return fields;
    }
};
}
