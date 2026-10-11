#pragma once
#include "protocol/RecoveredCharacterListCandidate.h"
#include "protocol/RecoveredRoleLevel.h"
#include "scripting/LuaEngine.h"
#include <stdexcept>

namespace god2 {
// Current 409680/40C580: (pre-wire byte29 >> 1)+56 selects FlowGui
// TipSword, TipWizard, TipRuse, TipDoctor. Wire29 is pre-wire+1.
// Catalog order differs: pharmacist=3, warlock=4. Never use raw29 as class ID.
inline CharacterGrowthClass recovered_growth_class(const std::array<std::uint8_t,40>& profile) {
    if(!RecoveredCharacterListCandidate::valid_profile(profile))
        throw std::invalid_argument("Unqualified raw create profession profile");
    constexpr std::array classes{CharacterGrowthClass::Swordsman,CharacterGrowthClass::Taoist,
        CharacterGrowthClass::Warlock,CharacterGrowthClass::Pharmacist};
    return classes[(profile[29]-1)/2];
}

// OWNER_CONFIRMED_20260927 growth; native22 words are Con/Str/Int/Speed.
// Caller supplies a qualified level result. No XP thresholds, HP/MP formula or
// level1 starting stats inferred here. A persisted full snapshot avoids replay.
inline RecoveredRoleLevel::Record project_character_growth(LuaEngine& lua,
    CharacterGrowthClass profession,const RecoveredRoleLevel::Record& prior,
    std::uint16_t next_level,std::uint16_t progress) {
    auto growth=lua.character_growth({profession,prior.level(),next_level,prior.base_stats(),prior.state_word()});
    auto next=RecoveredRoleLevel::with_level_progress(prior,static_cast<std::uint8_t>(next_level),progress);
    return RecoveredRoleLevel::with_base_stats_and_points(next,growth.attributes,growth.unspent_points);
}
}
