#pragma once

#include <algorithm>
#include <array>
#include <cstdint>
#include <optional>
#include <span>
#include <stdexcept>
#include <utility>

namespace god2 {

// Current 11EE90/11ED00 client setup semantics, not server cast authorization.
// See current-skill-target-setup-20260919.md for original code and state bounds.
struct NativeSkillTargeting {
    using Masks = std::array<std::uint32_t, 2>;
    struct Fields {
        std::uint8_t definition_id, kind;
        std::uint16_t word_3e;
        std::uint8_t reach_44, mode_45;
        bool passes_kind_gate() const noexcept { return kind != 2 || word_3e == 0x0ff5; }
    };
    struct State {
        Masks masks, saved_masks;
        // Null original type-0 pointer, or its signed WORD at +1A. Not HP.
        std::array<std::optional<std::int16_t>, 28> entity_words;
    };
    struct Result {
        Masks masks, saved_masks;
        std::uint32_t stored_mode;
        // Null means the subsequent 11EAD0 enters its unqualified diagnostic.
        std::optional<std::pair<std::uint32_t, std::uint32_t>> setup;
        bool passes_kind_gate;
    };

    static Fields from_record(std::span<const std::uint8_t> raw) {
        if (raw.size() != 110 || raw[0] == 0 || raw[1] > 3)
            throw std::invalid_argument("Native skill definition identity/size rejected");
        return {raw[0], raw[1], static_cast<std::uint16_t>(
            std::uint16_t{raw[0x3e]} | (std::uint16_t{raw[0x3f]} << 8)), raw[0x44], raw[0x45]};
    }

    static unsigned row_index(unsigned side, unsigned slot) {
        if (side >= 2 || slot >= 14)
            throw std::invalid_argument("Native target side/slot outside qualified domain");
        for (unsigned row = side * 4; row < side * 4 + 4; ++row)
            if (row_masks[row] & (std::uint32_t{1} << slot)) return row;
        throw std::logic_error("Native target row table incomplete");
    }

    static unsigned row_distance(unsigned side_a, unsigned slot_a,
                                 unsigned side_b, unsigned slot_b, const Masks& masks) {
        auto a = row_index(side_a, slot_a), b = row_index(side_b, slot_b);
        if (a > b) std::swap(a, b);
        auto distance = b - a;
        for (auto row = a + 1; row < b; ++row)
            if (!(masks[row / 4] & row_masks[row])) --distance;
        return distance;
    }

    static Result evaluate(const Fields& fields, unsigned actor, const State& state) {
        const auto row = row_index(0, actor);
        auto masks = state.masks;
        if (fields.kind == 3 && fields.definition_id >= 8 && fields.definition_id <= 10) {
            for (unsigned i = 0; i < state.entity_words.size(); ++i)
                if (state.entity_words[i] && *state.entity_words[i] >= 0)
                    masks[i / 14] |= std::uint32_t{1} << (i % 14);
        }
        const auto mode = fields.mode_45, reach = fields.reach_44;
        Result result{{0, 0}, state.saved_masks, mode, std::nullopt, fields.passes_kind_gate()};
        if ((mode >= 1 && mode <= 5) || mode == 13 || mode == 14 || mode == 16) {
            result.masks = reachable(actor, reach, masks);
        } else if (mode == 6 || mode == 7 || mode == 15) {
            const auto& templates = mode == 6 ? row_masks : mode == 7 ? mode7 : mode15;
            result.masks[0] = templates[row];
            const auto distance = row_distance(0, actor, 0, 12, masks);
            if (row != 0 && distance <= reach) {
                for (unsigned i = 0; i < row; ++i) result.masks[0] |= templates[i];
            } else if (row >= 2 && distance > 0) {
                result.masks[0] |= templates[row - 1];
            }
            unsigned upper = 7;
            while (upper > row && row_distance(0, actor, upper / 4, row_slots[upper], masks) > reach)
                --upper;
            for (auto i = row + 1; i <= upper; ++i) result.masks[i / 4] |= templates[i];
        } else if (mode >= 8 && mode <= 10) {
            for (unsigned side = 0; side < 2; ++side)
                if (row_distance(0, actor, side, mode == 8 ? 0 : 4, masks) <= reach)
                    result.masks[side] = mode == 8 ? 0x1f : 0x400;
        } else if (mode == 11) {
            result.masks[0] = std::uint32_t{1} << actor;
        } else if (mode == 12) {
            result.masks[0] = reachable(actor, reach, masks)[0];
        } else if (mode == 17) {
            // Original calls reachable, then overwrites its output unconditionally.
            result.masks[0] = std::uint32_t{1} << actor;
            result.saved_masks = state.masks;
        }
        if (mode >= 1 && mode <= 17)
            result.setup = std::pair{mode_values[mode], std::uint32_t{mode != 13 && mode != 14 && mode != 16}};
        return result;
    }

private:
    static constexpr std::array<std::uint32_t, 8> row_masks{0x3000,0xe00,0x1e0,0x1f,0x1f,0x1e0,0xe00,0x3000};
    static constexpr std::array<unsigned, 8> row_slots{12,9,5,0,0,5,9,12};
    static constexpr std::array<std::uint32_t, 8> mode7{0,0x400,0xc0,0xe,0xe,0xc0,0x400,0};
    static constexpr std::array<std::uint32_t, 8> mode15{0x3000,0xe00,0x1e0,0,0,0x1e0,0xe00,0x3000};
    static constexpr std::array<std::uint32_t, 18> mode_values{0,1,2,3,4,1,1,1,1,1,1,1,1,2,7,1,3,2};

    static Masks reachable(unsigned actor, unsigned reach, const Masks& masks) {
        const auto row = row_index(0, actor);
        const auto lower = row > reach ? row - reach : 0;
        int upper = 7;
        while (upper >= static_cast<int>(lower) && row_distance(
                0, actor, static_cast<unsigned>(upper) / 4, row_slots[upper], masks) > reach) --upper;
        Masks result{0, 0};
        for (auto i = lower; static_cast<int>(i) <= upper; ++i) result[i / 4] |= row_masks[i];
        for (unsigned side = 0; side < 2; ++side) result[side] &= masks[side];
        return result;
    }
};
}
