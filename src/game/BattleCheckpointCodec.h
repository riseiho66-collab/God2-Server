#pragma once
#include "game/Battle.h"
#include <string_view>

namespace god2 {
// CUSTOM-0007 canonical server storage format; never accepted from C2S.
struct BattleCheckpointCodec {
    static std::string encode(const BattleCheckpoint& checkpoint);
    static BattleCheckpoint decode(std::string_view text);
};
}
