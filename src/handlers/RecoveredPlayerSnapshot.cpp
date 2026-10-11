#include "handlers/RecoveredPlayerSnapshot.h"
#include "protocol/RecoveredRoleVitals.h"
#include <stdexcept>

namespace god2 {
std::optional<RecoveredPlayerSnapshot> RecoveredPlayerSnapshot::load_for_world_entry(
        RecoveredCharacterRepository& repository,
        std::uint64_t account, std::uint64_t character) {
    if(!account || !character)
        throw std::invalid_argument("Invalid saved player snapshot owner");
    const auto resources=repository.load_resources(account,character);
    const auto role=repository.load_role(account,character);
    // Detect a concurrent role/resources commit across the two reads. This is
    // not a replacement for the caller's session/account serialization.
    if(repository.load_resources(account,character)!=resources ||
       repository.load_role(account,character)!=role)
        throw std::runtime_error("Saved player snapshot changed during read");
    if(!resources) {
        if(role) throw std::runtime_error("Saved role has no resource authority");
        return std::nullopt;
    }
    if(resources->design_id!="CUSTOM-0012" || !resources->revision)
        throw std::runtime_error("Invalid saved player resource provenance");
    const auto vitals=RecoveredRoleVitals::encode(
        resources->hp,resources->mp,resources->max_hp,resources->max_mp);
    RecoveredPlayerSnapshot result{*resources,role,{}};
    if(role) {
        const auto parsed=RecoveredRoleLevel::parse(role->logical);
        if(!parsed || !parsed->level() || role->design_id!="CUSTOM-0013" || !role->revision ||
           parsed->max_hp()!=resources->max_hp || parsed->max_mp()!=resources->max_mp)
            throw std::runtime_error("Saved player role/resource mismatch");
        result.logical_before_companion_binding.insert(
            result.logical_before_companion_binding.end(),role->logical.begin(),role->logical.end());
    }
    result.logical_before_companion_binding.insert(
        result.logical_before_companion_binding.end(),vitals.begin(),vitals.end());
    return result;
}
}
