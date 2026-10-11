#pragma once
#include <array>
#include <bit>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {

// Pinned current client: 118E50..1191EE, queue copier 132E0.
// This is a structural input contract, not authorization to execute combat.
// A separate 68A30 secondary dispatcher contains a potential C2S35 producer
// with only body bytes8..11 explicitly set to FF. Its reachability and other
// body bytes are not qualified. Do not mistake it for action1/2/0B or accept it
// through this parser without an independently recovered state/meaning.
struct RecoveredBattleCommand {
    static constexpr std::size_t logical_size = 17;
    static constexpr bool runtime_mutation_enabled = false;
    static constexpr char image_sha256[] =
        "149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763";

    struct BasicAttackRequest {
        std::uint8_t actor_position;
        std::uint8_t side_flag;
        std::uint8_t unwritten_byte3;
        std::array<std::uint16_t, 2> target_masks;
        // Initialized from this+0x3c. Targets >=28 can alias its low word;
        // no third target group or context meaning is promoted here.
        std::uint32_t context_storage;
        std::uint32_t unwritten_parameter;
    };

    // Native 115AD8 -> 118E50 action 0B; no turn/ack meaning is inferred.
    struct ControlRequest {
        BasicAttackRequest fields;
    };
    // Native 112C37..112E2A also produces action2 when the command window
    // expires. The revival/reconnect branches use this action in other contexts.
    // Structural only; neither defense mitigation nor turn authority is inferred.
    struct Action2Request { BasicAttackRequest fields; };
    static std::optional<Action2Request> parse_action2_logical(
        std::span<const std::uint8_t> record) noexcept {
        const auto fields=parse_fields(record,2);
        if(!fields) return std::nullopt;
        return Action2Request{*fields};
    }

    // Exactly one decrypted logical record, including opcode, with no frame
    // length/checksum. Caller owns transport, record splitting and state policy.
    // Supported action is exactly 1 (basic attack), without continuation.
    static std::optional<BasicAttackRequest> parse_logical(
        std::span<const std::uint8_t> record) noexcept {
        return parse_fields(record, 1);
    }

    static std::optional<ControlRequest> parse_control_logical(
        std::span<const std::uint8_t> record) noexcept {
        const auto fields = parse_fields(record, 0x0b);
        if (!fields) return std::nullopt;
        return ControlRequest{*fields};
    }

private:
    static std::optional<BasicAttackRequest> parse_fields(
        std::span<const std::uint8_t> record, std::uint8_t action) noexcept {
        if (record.size() != logical_size || record[0] != 0x35 ||
            record[1] > 14 || record[2] != action || record[3] > 1)
            return std::nullopt;
        const auto first = u16(record, 5);
        const auto second = u16(record, 7);
        if (((first | second) & 0xc000u) != 0 ||
            std::popcount(first) + std::popcount(second) > 14)
            return std::nullopt;
        return BasicAttackRequest{record[1], record[3], record[4],
            {first, second}, u32(record, 9), u32(record, 13)};
    }

    static std::uint16_t u16(std::span<const std::uint8_t> r, std::size_t at) noexcept {
        return static_cast<std::uint16_t>(r[at] | (std::uint16_t{r[at + 1]} << 8));
    }
    static std::uint32_t u32(std::span<const std::uint8_t> r, std::size_t at) noexcept {
        return std::uint32_t{u16(r, at)} | (std::uint32_t{u16(r, at + 2)} << 16);
    }
};
}
