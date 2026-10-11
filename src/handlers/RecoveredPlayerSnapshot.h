#pragma once
#include "db/RecoveredCharacterRepository.h"
#include <optional>
#include <vector>

namespace god2 {
// Saved-state projection, not character creation or a growth/EXP formula.
// The existing rows retain CUSTOM-0012/0013 provenance. This does not promote
// their values into recovered native starting stats.
struct RecoveredPlayerSnapshot {
    CharacterResources resources;
    std::optional<CharacterRoleSnapshot> role;
    // Native22 (if saved), then native24. Send after the local actor exists and
    // BEFORE any S2C30 companion binding. E71E0's HP-loss path also subtracts
    // companion HP; this API is not an arbitrary mid-session refresh.
    std::vector<std::uint8_t> logical_before_companion_binding;

    // Owner-qualified repository reads only. Absent resources => nullopt, no
    // seed, XP conversion, skills, modifiers or companion fields synthesized.
    // Throws on invalid ownership, inconsistent/corrupt rows or a changed read.
    // Caller must serialize this with account/session mutations and enforce
    // fresh world-entry ordering; this helper owns no session lifecycle.
    static std::optional<RecoveredPlayerSnapshot> load_for_world_entry(
        RecoveredCharacterRepository& repository,
        std::uint64_t account, std::uint64_t character);
};
}
