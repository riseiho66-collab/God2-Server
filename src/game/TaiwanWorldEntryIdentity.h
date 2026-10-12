#pragma once
#include <cstdint>

namespace god2 {
// Explicit source binding only; does not select a wire format or allocate an ID.
// The independent handle comes from the complete native entry and its private
// prepared lease. Existing callers retain selected-character identity semantics.
enum class TaiwanWorldEntryIdentity { SelectedCharacter, QualifiedSceneHandle };
constexpr bool valid_taiwan_world_entry_identity(TaiwanWorldEntryIdentity value) noexcept {
    return value==TaiwanWorldEntryIdentity::SelectedCharacter ||
        value==TaiwanWorldEntryIdentity::QualifiedSceneHandle;
}
constexpr bool qualified_taiwan_scene_handle(std::uint16_t value) noexcept {
    // Common native visibility packs remote handles in twelve bits. Reject,
    // rather than truncate, a local handle which cannot enter that same scene.
    return value!=0 && value<=0x0fff;
}
}
