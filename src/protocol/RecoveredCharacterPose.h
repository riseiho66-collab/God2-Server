#pragma once
#include "protocol/RecoveredWorldFrame.h"
#include <array>
#include <cstdint>
#include <optional>

namespace god2 {
// Current503820 ->497E00 queues66 [0, (pose_mode<<3)|direction, tail].
// This caller pushes a zero DWORD, but other97E00 callers leave upper bytes
// unwritten. Tail does not participate in pose authorization.
// Modes1/2/3 select native character animation16/17/18. They are not logout.
// Live UI06 proves matching local S2C77 changes World+30 and packed pose.
// Receive table401324[77] ->4012CA gives7 logical bytes; dispatcher
// 46B5D4[77] ->469BBA ->501610 sets World+30 to16/17/18 for the local ID.
// Ordinary peers dispatch to4FB980: actor+79 mode,+3A direction,+38 animation.
// Other pose modes/effects remain unqualified.
struct RecoveredCharacterPose {
    using LogicalRecord=std::array<std::uint8_t,7>;
    // Native502570/4FB290 reset animation18 at ACT completion. Animation16/17
    // remain until another action. A one-shot cannot be replayed as presence:
    // 77 contains no elapsed animation time and would restart the old action.
    static bool is_persistent_pose(const std::array<std::uint8_t,3>& payload) noexcept {
        return is_qualified_pose(payload) && (payload[1]>>3)<3;
    }
    static bool is_qualified_pose(const std::array<std::uint8_t,3>& payload) noexcept {
        const auto mode=payload[1]>>3;
        return payload[0]==0 && mode>=1 && mode<=3;
    }
    static std::optional<LogicalRecord> logical(
        std::uint64_t owned_character,const std::array<std::uint8_t,3>& payload) {
        if(!owned_character || owned_character>65535 || !is_qualified_pose(payload))return std::nullopt;
        // Native consumer ignores effect0, checks ordinary flags bit3=0 and
        // reads packed pose/direction. Final unread byte is a zero candidate.
        return LogicalRecord{0x77,
            static_cast<std::uint8_t>(owned_character),
            static_cast<std::uint8_t>(owned_character>>8),0,payload[1],0,0};
    }
    static std::optional<std::vector<std::uint8_t>> synchronize(
        std::uint64_t owned_character,const std::array<std::uint8_t,3>& payload) {
        const auto record=logical(owned_character,payload);
        if(!record)return std::nullopt;
        return RecoveredWorldFrame::encode(*record);
    }
};
}
