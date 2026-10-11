#pragma once
#include "RecoveredBattleCommand.h"

namespace god2 {

// Pinned118E50 builder, kinds0/1/3, this+468 ==0 mask-target branch.
// Structural records/sequences only; no cast authorization or runtime assembly.
struct RecoveredSkillCommand {
    static constexpr std::size_t logical_size = RecoveredBattleCommand::logical_size;
    static constexpr std::size_t max_sequence_records = 14;
    static constexpr bool runtime_mutation_enabled = false;
    static constexpr auto image_sha256 = RecoveredBattleCommand::image_sha256;

    // 11C520 consumes this WORD after 117540 skips its caller's leading byte.
    // Bits 14/15 select client storage and state, not server cast permission.
    struct StateIdentity {
        std::uint16_t raw;
        std::uint8_t id;
        std::uint8_t kind;
        bool alternate_table;
        bool state_bit;
    };
    static constexpr std::size_t definition_stride = 110;
    static constexpr std::size_t definition_group_stride = 0x6e04;
    static constexpr std::size_t definition_file_size = 4 + 4 * definition_group_stride;

    static std::optional<StateIdentity> parse_state_word(
        std::span<const std::uint8_t> bytes) noexcept {
        if (bytes.size() != 2) return std::nullopt;
        const auto raw = u16(bytes, 0);
        return StateIdentity{raw, bytes[0], static_cast<std::uint8_t>(bytes[1] & 0x3f),
                             (raw & 0x4000) != 0, (raw & 0x8000) != 0};
    }

    // Original 12D3B0 loads version 1.03's body unchanged. 11C603/11C796
    // produce body + kind*0x6e04 + 4 + (id-1)*110. This checked lookup is a
    // supported source subset: native insertion itself does not check counts.
    static std::optional<std::size_t> definition_offset(
        std::span<const std::uint8_t> state_word,
        std::span<const std::uint8_t> source) noexcept {
        const auto identity = parse_state_word(state_word);
        if (!identity || identity->kind >= 4 || identity->id == 0 ||
            source.size() != definition_file_size || source[0] != '1' ||
            source[1] != '.' || source[2] != '0' || source[3] != '3')
            return std::nullopt;
        const auto group = 4 + identity->kind * definition_group_stride;
        const auto count = std::uint32_t{u16(source, group)} |
            (std::uint32_t{u16(source, group + 2)} << 16);
        if (count > 255 || identity->id > count) return std::nullopt;
        const auto offset = group + 4 + (identity->id - 1) * definition_stride;
        if (source[offset] != identity->id || source[offset + 1] != identity->kind)
            return std::nullopt;
        return offset;
    }

    struct Record {
        std::uint8_t actor_position;
        bool continuation;
        std::uint8_t side_flag;
        std::uint8_t unwritten_byte3;
        std::array<std::uint16_t, 2> target_masks;
        std::uint32_t context_storage;
        // Original selected entry's byte 0, not its lookup index. A source
        // identity binding additionally requires the producer/catalog evidence.
        std::uint8_t selection_id_byte;
        std::uint8_t selection_kind_byte{};
    };

    struct Sequence {
        std::array<Record, max_sequence_records> records;
        std::size_t count;
    };

    static bool same_sequence(const Record& first, const Record& next) noexcept {
        return first.actor_position == next.actor_position &&
               first.side_flag == next.side_flag &&
               first.context_storage == next.context_storage &&
               first.selection_id_byte == next.selection_id_byte &&
               first.selection_kind_byte == next.selection_kind_byte;
    }

    // Kinds0/1/3 all enter original11913D. One target per action03/83 record.
    // Parsing does not authorize casting, ownership, healing or revival.
    // Kind2 depends on selected definition WORD+3E and remains outside this
    // source-independent grammar; unchecked target aliases remain excluded.
    // A continuation record alone does not establish a complete command.
    static std::optional<Record> parse_logical(
        std::span<const std::uint8_t> record) noexcept {
        if (record.size() != logical_size || record[0] != 0x35 || record[1] > 14 ||
            (record[2] != 0x03 && record[2] != 0x83) || record[3] > 1 ||
            (record[14] != 0 && record[14] != 1 && record[14] != 3) ||
            record[15] != 0 || record[16] != 0)
            return std::nullopt;
        const auto first = u16(record, 5);
        const auto second = u16(record, 7);
        // CUSTOM-0059: native 118E50 combined branch -> 11E910 mode5 emits
        // one terminal record with the clicked side's entire 14-bit mask,
        // even when only one enemy survives. Scope this additional grammar
        // to the installed custom0/150 definition; ownership remains server-side.
        const bool thousand_bulls_all = record[13]==150 && record[14]==0 && record[2]==3 &&
            ((first==0x3fff && second==0) || (first==0 && second==0x3fff));
        if (((first | second) & 0xc000u) != 0 ||
            (!thousand_bulls_all && std::popcount(first) + std::popcount(second) != 1))
            return std::nullopt;
        return Record{record[1], record[2] == 0x83, record[3], record[4],
            {first, second}, std::uint32_t{u16(record, 9)} |
                (std::uint32_t{u16(record, 11)} << 16), record[13], record[14]};
    }

    // Caller supplies exactly one candidate sequence of decrypted logical records.
    // 118E84 bounds count; 1191BB/1191C6 mark all but the last as continuation.
    // This cannot detect missing prefixes, replay, or splicing identical headers.
    static std::optional<Sequence> parse_sequence(
        std::span<const std::uint8_t> bytes) noexcept {
        if (bytes.empty() || bytes.size() > max_sequence_records * logical_size ||
            bytes.size() % logical_size != 0)
            return std::nullopt;
        Sequence sequence{};
        sequence.count = bytes.size() / logical_size;
        for (std::size_t index = 0; index < sequence.count; ++index) {
            const auto record = parse_logical(bytes.subspan(index * logical_size, logical_size));
            if (!record || record->continuation != (index + 1 < sequence.count))
                return std::nullopt;
            // These initialized fields stay fixed in the in-range per-target loop.
            // Unwritten stack storage is opaque and is not a sequence identity.
            if (index != 0) {
                const auto& first = sequence.records[0];
                if (!same_sequence(first, *record))
                    return std::nullopt;
            }
            sequence.records[index] = *record;
        }
        return sequence;
    }

private:
    static std::uint16_t u16(std::span<const std::uint8_t> record,
                             std::size_t offset) noexcept {
        return static_cast<std::uint16_t>(record[offset] |
            (std::uint16_t{record[offset + 1]} << 8));
    }
};
}
