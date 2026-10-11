#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {
// Pinned current client: S2C size RVA 12AC, dispatch 6A04D, consumer 991E0.
// This is an occupancy projection, not a character birth or item grant rule.
struct RecoveredInventory {
    static constexpr std::uint8_t opcode = 0x41;
    static constexpr std::size_t slot_count = 50;
    static constexpr std::size_t logical_size = 5;
    using LogicalRecord = std::array<std::uint8_t, logical_size>;
    using ClearRecord = LogicalRecord;
    using EmptyLogical = std::array<std::uint8_t, slot_count * logical_size>;

    struct SlotUpdate {
        std::uint16_t client_item_id;
        std::uint8_t slot;
        std::uint8_t raw_count;
    };

    // Lossless scalar projection for an already-established client slot. This
    // does not create item metadata/resources or validate ownership/stack rules.
    // Preserve raw_count, including the signed-clear values 0x80..0xff.
    static std::optional<LogicalRecord> encode_slot_update(SlotUpdate update) noexcept {
        if (update.slot >= slot_count) return std::nullopt;
        return LogicalRecord{opcode, static_cast<std::uint8_t>(update.client_item_id),
            static_cast<std::uint8_t>(update.client_item_id >> 8),
            update.slot, update.raw_count};
    }

    // Decoded S2C record only, without length/checksum. No gameplay validation:
    // the consumer treats raw_count as signed; 0x80..0xff also clear occupancy.
    static std::optional<SlotUpdate> decode_slot_update(
        std::span<const std::uint8_t> logical) noexcept {
        if (logical.size() != logical_size || logical[0] != opcode ||
            logical[3] >= slot_count) return std::nullopt;
        return SlotUpdate{
            static_cast<std::uint16_t>(logical[1] + 256u * logical[2]),
            logical[3], logical[4]};
    }

    static std::optional<ClearRecord> clear_slot(std::size_t slot) noexcept {
        if (slot >= slot_count) return std::nullopt;
        return ClearRecord{opcode, 0, 0, static_cast<std::uint8_t>(slot), 0};
    }

    // Caller must establish authoritative emptiness across ALL 50 slots,
    // including equipment-related slots. No inference from absent database rows.
    // Clears count and the low item-id word only, retaining 21/24 slot bytes.
    // UI/resource state must already be initialized; this does not create it.
    // Logical S2C batch for RecoveredWorldFrame::encode, after world-ready.
    static EmptyLogical empty_owned_inventory() noexcept {
        EmptyLogical frame{};
        for (std::size_t slot = 0; slot < slot_count; ++slot) {
            frame[slot * logical_size] = opcode;
            frame[3 + slot * logical_size] = static_cast<std::uint8_t>(slot);
        }
        return frame;
    }
};
}
