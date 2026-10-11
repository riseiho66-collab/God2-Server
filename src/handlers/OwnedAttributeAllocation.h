#pragma once
#include "handlers/RecoveredPlayerSnapshot.h"
#include "protocol/RecoveredAttributeAllocation.h"
#include "protocol/RecoveredWorldFrame.h"
#include "scripting/LuaEngine.h"
namespace god2 {
// Native one-point operation on an already-authoritative saved snapshot.
// Existing CUSTOM seed/XP provenance is preserved, never created here.
inline std::vector<std::uint8_t> allocate_owned_attributes(RecoveredCharacterRepository& repository,LuaEngine& lua,
    std::uint64_t account,std::uint64_t character,std::span<const RecoveredAttributeAllocation::Request> requests) {
    if(requests.empty() || requests.size()>RecoveredWorldFrame::max_logical_size/2)
        throw std::invalid_argument("Invalid allocation batch size");
    const auto saved=RecoveredPlayerSnapshot::load_for_world_entry(repository,account,character);
    if(!saved || !saved->role)return {};
    const auto prior=RecoveredRoleLevel::parse(saved->role->logical).value();
    constexpr std::array<unsigned,4> indices{2,0,1,3};
    for(const auto request:requests)
        if(request.selector<1 || request.selector>4)throw std::invalid_argument("Invalid allocation selector");
    // Return the complete authoritative22 to undo an optimistic local attempt.
    if(requests.size()>prior.state_word() || prior.state_word()>32767)
        return RecoveredWorldFrame::encode(saved->role->logical);
    auto projected=CharacterGrowthResult{prior.base_stats(),prior.state_word()};
    for(const auto request:requests) {
        if(projected.attributes[indices[request.selector-1]]==65535)
            return RecoveredWorldFrame::encode(saved->role->logical);
        projected=lua.allocate_attribute({request.selector,projected.attributes,projected.unspent_points});
    }
    auto next=*saved->role;
    next.logical=RecoveredRoleLevel::encode(RecoveredRoleLevel::with_base_stats_and_points(prior,
        projected.attributes,projected.unspent_points));
    auto response=RecoveredWorldFrame::encode(next.logical); // Allocate before the transaction.
    repository.commit_role_resources(account,character,saved->role,saved->resources,next,saved->resources);
    return response;
}
inline std::vector<std::uint8_t> allocate_owned_attribute(RecoveredCharacterRepository& repository,LuaEngine& lua,
    std::uint64_t account,std::uint64_t character,RecoveredAttributeAllocation::Request request) {
    return allocate_owned_attributes(repository,lua,account,character,std::span(&request,1));
}
}
