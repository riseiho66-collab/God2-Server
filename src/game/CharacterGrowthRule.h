#pragma once
#include <array>
#include <cstdint>

namespace god2 {
// Owner-confirmed 2026-09-27. These are catalog IDs, never raw client fields.
enum class CharacterGrowthClass : std::uint8_t { Swordsman=1, Taoist=2, Pharmacist=3, Warlock=4 };
struct CharacterGrowthInput {
    CharacterGrowthClass profession{};
    std::uint16_t previous_level{}, next_level{};
    // Named order: constitution, strength, intelligence, speed.
    std::array<std::uint16_t,4> attributes{};
    std::uint16_t unspent_points{};
};
struct CharacterGrowthResult {
    std::array<std::uint16_t,4> attributes{};
    std::uint16_t unspent_points{};
    bool operator==(const CharacterGrowthResult&) const = default;
};
struct CharacterAllocationInput {
    std::uint8_t selector{};
    std::array<std::uint16_t,4> attributes{};
    std::uint16_t unspent_points{};
};
}
