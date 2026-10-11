#pragma once
#include <array>
#include <cstdint>

namespace god2 {
// CUSTOM-0018: current template531/resource21, diagnostic (17,12), not native placement.
// Direction0, state1, selector high bits3, remaining bytes0 are unqualified test inputs.
struct DiagnosticQuestNpc {
    static constexpr std::array<std::uint8_t,21> logical() noexcept {
        return {0x72,0x13,0x02,0,0,21,0x60,0,0,1,0,0,0,0,0,0,0,0x44,0,0x18,0};
    }
};
}
