#pragma once
#include "cn/protocol/CnBattleScalarUpdate.h"
#include "cn/protocol/CnBattleRoundBatch.h"

namespace god2cn {
// Pure projection of primary0055B910/0055BA40/0055B740 DWORD stores.
// Values/handle must come from the actual existing native object. This source
// neither captures memory nor supplies authority, pointers or a battle owner.
struct CnBattleScalarProjection {
    struct ExistingActor {
        std::uint16_t render_handle; // native unsigned WORD+1A, not+1D8 bar
        std::uint32_t current_a;    // native+DE8
        std::uint32_t current_b;    // native+DEC
        std::uint32_t maximum_a;    // native+DF0
        std::uint32_t maximum_b;    // native+DF4
    };
    static std::optional<ExistingActor> actor_stores(
        const CnBattleScalarUpdate::Record& record,const ExistingActor& prior) noexcept {
        if(!record.has_primary_actor_store_branch())return std::nullopt;
        if(record.side()==1 && prior.render_handle>=0x1000)return std::nullopt;
        auto next=prior;
        if(record.kind()==1) {
            next.current_b=record.supplied_current();next.maximum_b=record.supplied_maximum();
        } else {
            next.current_a=record.supplied_current();next.maximum_a=record.supplied_maximum();
        }
        // The object stores are full32 bits and unclamped. Native render bar
        // copy00453EE0 separately caps its current values by supplied maxima.
        return next;
    }
    // Side0/kind6 does not store these actor values: actual self-slot/+1A
    // qualification and00518F70's secondary role-resource path are separate.
    static std::array<ExistingActor,CnBattleRoundBatch::slots> batch_actor_stores(
        const CnBattleRoundBatch::Record& record,
        const std::array<ExistingActor,CnBattleRoundBatch::slots>& actual_prior_side0) noexcept {
        //00561C40 unconditionally dereferences all fourteen base actors. Caller
        // must supply each actual existing slot; an absent slot is not zero.
        auto result=actual_prior_side0;
        for(std::size_t slot=0;slot<CnBattleRoundBatch::slots;++slot) {
            const auto pair=*record.at(slot);
            result[slot].current_a=pair.a;result[slot].current_b=pair.b;
        }
        // Maxima,handles and side1 are not changed by this narrow projection.
        //0054D450 also resets effects/skill pointers via00561FD0; no claim that
        // this scalar projection models that lifecycle or native acceptance.
        return result;
    }
};
}
