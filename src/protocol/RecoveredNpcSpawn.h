#pragma once
#include <array>
#include <cstdint>
#include <stdexcept>

namespace god2 {
// Logical S2C72 records only. No world eligibility, transport, or asset readiness
// is implied. Provenance and current x86 checks: test_current_npc_spawn.py.
struct RecoveredNpcSpawn {
    using Record = std::array<std::uint8_t, 21>;

    static Record logical(std::uint64_t selector, std::uint64_t x, std::uint64_t y) {
        if (selector != 3793 && selector != 3954)
            throw std::invalid_argument("NPC selector has no retained qualified record");
        if (x > 0x7fff || y > 0x7fff)
            throw std::invalid_argument("NPC coordinate exceeds current 15-bit field");
        // Preserve secondary selector, reserved word, state and opaque bytes.
        // Current 6A68B selects catalog[low WORD], not an arbitrary entity ID.
        Record record{0x72,0,0,0,0,0,0x60,0,0,0,0,0,0,0xcf,1,0,0,0,0,0,0};
        record[1] = static_cast<std::uint8_t>(selector);
        record[2] = static_cast<std::uint8_t>(selector >> 8);
        record[5] = selector == 3793 ? 88 : 82;
        record[9] = selector == 3793 ? 0xa1 : 0x81;
        const auto position = static_cast<std::uint32_t>((y << 17) | (x << 2));
        for (unsigned i = 0; i < 4; ++i)
            record[17 + i] = static_cast<std::uint8_t>(position >> (8 * i));
        return record;
    }

    static Record logical(std::uint64_t selector) {
        return logical(selector, selector == 3793 ? 65 : 240, selector == 3793 ? 61 : 54);
    }
};
}
