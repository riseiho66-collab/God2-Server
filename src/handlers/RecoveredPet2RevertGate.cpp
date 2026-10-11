#include "handlers/RecoveredPet2RevertGate.h"
#include <algorithm>

namespace god2 {
RecoveredPet2RevertGate::Decision RecoveredPet2RevertGate::inspect(
        Context context,const RecoveredPet2Revert::Request& request) {
    if(!context.account || !context.character || !context.world_ready) return Decision::NotWorldReady;
    if(context.in_battle) return Decision::InBattle;
    if(!RecoveredPet2Revert::has_qualified_operands(request)) return Decision::InvalidOperands;
    // Existing repository checks account ownership even when state is absent.
    if(characters_.owned_pending_battle(context.account,context.character)) return Decision::PendingBattle;
    const auto item=characters_.load_inventory_slot(context.account,context.character,request.item_slot);
    if(!item || !item->count) return Decision::MissingItem;
    if(item->item_id!=*RecoveredPet2Revert::required_item_key(request.option)) return Decision::WrongItem;
    if(item->source_sha256!=SqliteCompanionRepository::source_sha256) return Decision::WrongItemSource;
    const auto slots=companions_.load_pet2_slots(context.account,context.character);
    const auto pet=std::find_if(slots.begin(),slots.end(),[&](const auto& value){return value.slot==request.pet_slot;});
    if(pet==slots.end() || !pet->pet || pet->pet1) return Decision::MissingPet2;
    // Loading validates owned source/metadata/slot against the current catalog.
    // Do not guess old talent/category values from the current FB bytes, debit
    // the stone, emit FB, or map this request to pet selection.
    return Decision::EffectUnqualified;
}
const char* RecoveredPet2RevertGate::name(Decision decision) noexcept {
    switch(decision) {
    case Decision::NotWorldReady:return "not_world_ready";
    case Decision::InBattle:return "in_battle";
    case Decision::InvalidOperands:return "invalid_operands";
    case Decision::PendingBattle:return "pending_battle";
    case Decision::MissingItem:return "missing_item";
    case Decision::WrongItem:return "wrong_item";
    case Decision::WrongItemSource:return "wrong_item_source";
    case Decision::MissingPet2:return "missing_pet2";
    case Decision::EffectUnqualified:return "effect_unqualified";
    }
    return "invalid_decision";
}
}
