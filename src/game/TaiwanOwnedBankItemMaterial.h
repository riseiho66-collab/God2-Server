#pragma once
#include "db/SqliteOwnedEquipmentTransaction.h"
#include "protocol/RecoveredBankItems.h"
#include "protocol/RecoveredTaiwanInventoryItemRecord.h"
#include <string>
#include <vector>

namespace god2 {
// CUSTOM-0160 explicit whole-bank namespace/custody policy, not original server
// storability, split/merge, unlocking or native opaque helper qualification.
// A bank alias's BYTE is page-local; page is part of its profile, never folded
// into a BYTE. Retained full25 is the original bag material, not S48 material.
struct TaiwanOwnedBankItemMaterial {
    using Transaction=SqliteOwnedEquipmentTransaction;
    static std::string identity_profile(std::uint8_t page);
    static std::string material_profile(std::uint8_t page);
    static std::optional<RecoveredTaiwanInventoryItemRecord::Fields> observe(
        const OwnedInventoryInstance&,std::uint8_t page,std::uint8_t local);
    // Six explicit 50-cell pages are a required SOURCE population, not a
    // constructor/provisioning policy. No absent cell becomes free capacity.
    static bool qualified(const Transaction::State&);
    static std::optional<Transaction::State> plan(const Transaction::Before&,const RecoveredBankItems::Request&);
    // Original framed S48 projection, batched under the existing frame limit.
    static std::vector<std::uint8_t> opening_wire(const Transaction::State&);
    static std::vector<std::uint8_t> mutation_wire(const Transaction::State&,const RecoveredBankItems::Request&);
};
}
