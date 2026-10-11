#include "handlers/DiagnosticSupplyService.h"
#include "protocol/RecoveredInventory.h"
#include "protocol/RecoveredTargetItemRequest.h"
#include "protocol/RecoveredRoleVitals.h"
#include "protocol/RecoveredWorldFrame.h"
#include <stdexcept>

namespace god2 {
std::optional<DiagnosticSupplyService::Policy> DiagnosticSupplyService::current_supply_policy(
        std::uint16_t item, std::uint16_t target) {
    if (!target || target > 0x3fff || (item != 3101 && item != 3107)) return std::nullopt;
    return Policy{item,target,"70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731",
        item==3101 ? 100u : 0u,item==3107 ? 50u : 0u};
}
std::optional<DiagnosticSupplyService::Policy> DiagnosticSupplyService::native_declared_policy(
        const NativeSupplyCatalog& catalog,std::uint16_t item,std::uint16_t target) {
    if(!target || target>0x3fff || !item) return std::nullopt;
    const auto declaration=catalog.lookup(item);
    if(!declaration) return std::nullopt;
    return Policy{item,target,NativeSupplyCatalog::current_source_sha256,
                  declaration->declared_hp,declaration->declared_mp};
}
DiagnosticSupplyService::Result DiagnosticSupplyService::use(
        std::uint64_t account, std::uint64_t character, std::span<const std::uint8_t> logical,
        const Policy& policy, const StoredInventorySlot& expected_slot,
        const CharacterResources& expected_resources) {
    if(policy.numeric_profile!=BattleNumericProfile::LegacyCustom &&
       policy.numeric_profile!=BattleNumericProfile::ExtendedHealth64)
        throw std::invalid_argument("Unknown supply numeric profile");
    if((policy.numeric_profile==BattleNumericProfile::LegacyCustom && policy.projector) ||
       (policy.numeric_profile==BattleNumericProfile::ExtendedHealth64 && !policy.projector))
        throw std::invalid_argument("Supply projector does not match trusted numeric profile");
    const auto request = RecoveredTargetItemRequest::decode(logical);
    if (!request || request->raw_slot >= 30 || !policy.expected_target || policy.expected_target > 0x3fff ||
        !policy.item_id || request->client_item_id != policy.item_id ||
        request->raw_target != policy.expected_target || expected_slot.item_id != policy.item_id ||
        !expected_slot.count || expected_slot.count > 127 || !expected_slot.revision ||
        expected_slot.source_sha256 != policy.source_sha256)
        throw std::invalid_argument("Diagnostic supply request or policy mismatch");
    if (repository_.load_inventory_slot(account,character,request->raw_slot) != expected_slot ||
        repository_.load_resources(account,character) != expected_resources)
        throw std::runtime_error("Stale diagnostic supply baseline");
    SupplyInput input;
    if(policy.numeric_profile==BattleNumericProfile::LegacyCustom) {
        const auto legacy=expected_resources.legacy_vitals();
        if(!legacy)throw std::invalid_argument("Diagnostic supply requires legacy resource representation");
        input={(*legacy)[0],(*legacy)[1],(*legacy)[2],(*legacy)[3],
            policy.restore_hp,policy.restore_mp,policy.numeric_profile};
    } else {
        if(!expected_resources.valid_health())
            throw std::invalid_argument("Invalid extended supply health domain");
        input={expected_resources.hp,expected_resources.max_hp,expected_resources.mp,expected_resources.max_mp,
            policy.restore_hp,policy.restore_mp,policy.numeric_profile};
    }
    const auto projected = lua_.supply(input);
    if (!projected.consume) return {}; // No write and no stale-state projection.
    auto slot = expected_slot;
    if (--slot.count == 0) slot.item_id = 0;
    auto resources = expected_resources;
    resources.hp = projected.hp;
    resources.mp = projected.mp;
    std::vector<std::uint8_t> reply;
    if(policy.numeric_profile==BattleNumericProfile::LegacyCustom) {
        const auto occupancy = RecoveredInventory::encode_slot_update(
            {slot.item_id,request->raw_slot,slot.count});
        if (!occupancy) throw std::runtime_error("Diagnostic supply slot projection rejected");
        const auto vitals = RecoveredRoleVitals::encode(resources.hp,resources.mp,resources.max_hp,resources.max_mp);
        reply.assign(occupancy->begin(),occupancy->end());
        reply.insert(reply.end(),vitals.begin(),vitals.end());
    } else {
        reply=policy.projector(request->raw_slot,slot,resources);
        if(reply.empty() || reply.size()>RecoveredWorldFrame::max_logical_size)
            throw std::invalid_argument("Extended supply logical projection exceeds queue bounds");
    }
    Result result{true,RecoveredWorldFrame::encode(reply),std::nullopt};
    // All allocations for outgoing data precede the atomic CAS. Pending battle
    // reservations are checked inside this transaction, not via a racy precheck.
    auto committed=repository_.commit_inventory_resources(account,character,request->raw_slot,
        expected_slot,expected_resources,std::move(slot),std::move(resources));
    result.resources.emplace(std::move(committed.resources));
    return result;
}
}
