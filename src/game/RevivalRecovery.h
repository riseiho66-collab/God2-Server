#pragma once
#include "game/Battle.h"

namespace god2 {
// CUSTOM-0017: trusted recovery state, never a client wire record.
struct RevivalRecovery {
    std::uint32_t version{1};
    std::uint64_t account{},character{};
    BattleCheckpoint battle;
    bool initial_control_received{},opening_received{},action_received{},control_received{};
    bool opening_notice{};
    bool operator==(const RevivalRecovery&) const = default;
};
}
