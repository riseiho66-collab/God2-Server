#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {
// Pinned current x86: DB -> 6B44E -> 854F0 -> C9670. Logical S2C only.
// A journal projection is not authoritative quest state or completion history.
struct RecoveredQuestSync {
    static constexpr std::size_t slotCount = 15;
    static constexpr std::size_t recordSize = 13;
    using Record = std::array<std::uint8_t, recordSize>;
    using EmptyJournal = std::array<std::uint8_t, slotCount * recordSize>;
    using JournalValues = std::array<std::uint32_t, slotCount>;

    struct SlotUpdate {
        std::uint8_t subtype; // 4: batch slot; 5: selected slot + journal refresh.
        std::uint32_t slot;
        std::uint32_t packedValue; // Preserved verbatim; see descriptionReference for display only.
    };

    struct DescriptionReference {
        std::uint16_t missionIndex; // One-based Mission_data catalog index.
        std::uint16_t descriptionIndex; // Zero-based text-array index, not completion state.
    };

    // C9581..C95DA: low word selects a 40-byte Mission_data row; high word
    // selects description max(highWord - 1, 0). Counts come from that catalog,
    // indexed by missionIndex - 1. Invalid references do not invalidate raw bytes.
    static constexpr std::optional<DescriptionReference> descriptionReference(
        std::uint32_t packedValue, std::span<const std::uint16_t> descriptionCounts) {
        const auto mission = static_cast<std::uint16_t>(packedValue);
        // The loader takes a signed 16-bit row count (584AE).
        if (descriptionCounts.size() > 0x7fff || mission == 0 ||
            mission > descriptionCounts.size()) return std::nullopt;
        const auto count = descriptionCounts[mission - 1];
        // C95C6 sign-extends this word before an unsigned comparison. Negative
        // counts would permit unsafe native reads; do not reproduce that hazard.
        if (count == 0 || count > 0x7fff) return std::nullopt;
        const auto selector = packedValue >> 16;
        const auto index = selector == 0 ? 0 : selector - 1;
        if (index >= count) return std::nullopt;
        return DescriptionReference{mission, static_cast<std::uint16_t>(index)};
    }

    static std::optional<SlotUpdate> decode(std::span<const std::uint8_t> record) {
        if (record.size() != recordSize || record[0] != 0xdb ||
            (record[1] != 4 && record[1] != 5))
            return std::nullopt;
        const auto slot = read32(record, 5);
        if (slot >= slotCount) return std::nullopt;
        // Bytes 2..4 are not read on either native quest branch.
        return SlotUpdate{record[1], slot, read32(record, 9)};
    }

    // Opaque visible projection only; caller must establish the value and World gate.
    // No catalog validity, quest transition, or reward authorization is implied.
    // Subtype 5 also selects this value; subtype 4 preserves the selection.
    static constexpr std::optional<Record> encodeSlotLogical(
        std::uint32_t slot, std::uint32_t subtype, std::uint32_t packedValue) {
        if (slot >= slotCount || (subtype != 4 && subtype != 5))
            return std::nullopt;
        Record result{};
        result[0] = 0xdb;
        // Validate before narrowing: e.g. 0x104 must not become subtype 4.
        result[1] = static_cast<std::uint8_t>(subtype);
        result[5] = static_cast<std::uint8_t>(slot);
        for (unsigned byte = 0; byte < 4; ++byte)
            result[9 + byte] = static_cast<std::uint8_t>(packedValue >> (8 * byte));
        return result;
    }

    // Visible projection only; caller must establish an authoritative clear in World.
    // Subtype 4 preserves the selected value; 5 clears it and requests refresh.
    // Subtype 4 on slot 14 also consumes the native batch refresh suppression flag.
    static constexpr std::optional<Record> clearSlotLogical(
        std::uint32_t slot, std::uint32_t subtype) {
        return encodeSlotLogical(slot, subtype, 0);
    }

    // Restores every visible slot, including empty slots, in native batch order.
    // Validate references against the matching loaded catalog before emitting any
    // bytes. Ownership, persistence and quest authority belong to the caller.
    static constexpr std::optional<EmptyJournal> encodeJournalLogical(
        const JournalValues& values, std::span<const std::uint16_t> descriptionCounts) {
        if (descriptionCounts.size() > 0x7fff) return std::nullopt;
        for (const auto value : values)
            if (value != 0 && !descriptionReference(value, descriptionCounts))
                return std::nullopt;
        EmptyJournal result{};
        for (std::size_t slot = 0; slot < slotCount; ++slot) {
            const auto record = encodeSlotLogical(static_cast<std::uint32_t>(slot), 4, values[slot]);
            for (std::size_t byte = 0; byte < recordSize; ++byte)
                result[slot * recordSize + byte] = (*record)[byte];
        }
        return result;
    }

    // Caller must already know the character's journal is empty and be in World.
    // Clearing the visible slots does not reset quests, rewards, or daily state.
    // Pass the result to RecoveredWorldFrame::encode; no encryption lives here.
    static constexpr EmptyJournal emptyJournalLogical() {
        EmptyJournal result{};
        for (std::size_t slot = 0; slot < slotCount; ++slot) {
            result[slot * recordSize] = 0xdb;
            result[slot * recordSize + 1] = 4;
            result[slot * recordSize + 5] = static_cast<std::uint8_t>(slot);
        }
        return result;
    }

private:
    static std::uint32_t read32(std::span<const std::uint8_t> bytes, std::size_t at) {
        std::uint32_t result = 0;
        for (unsigned i = 0; i < 4; ++i)
            result |= std::uint32_t{bytes[at + i]} << (8 * i);
        return result;
    }
};
}
