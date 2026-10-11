#pragma once
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {
// Current-native WORLD cases 6A65D (74, monster/follower pool) and 6AA93
// (75, NPC/local-marker pool). Both consume the low WORD of a logical5 record.
// Preserve the two unconsumed bytes. Native 72 constructors store their low
// selector WORD as NPC instance identity; this still does not establish a
// server-side despawn trigger or a source for the unconsumed bytes.
template<std::uint8_t Opcode>
struct RecoveredWorldPoolRemoval {
    static_assert(Opcode==0x74 || Opcode==0x75);
    static constexpr std::size_t logical_size=5;
    static constexpr bool runtime_emission_enabled=false;
    using LogicalRecord=std::array<std::uint8_t,logical_size>;
    struct Record {
        LogicalRecord bytes;
        std::uint16_t identity() const noexcept {
            return static_cast<std::uint16_t>(bytes[1]|(std::uint16_t{bytes[2]}<<8));
        }
    };
    static std::optional<Record> parse_logical(std::span<const std::uint8_t> logical) noexcept {
        if(logical.size()!=logical_size || logical[0]!=Opcode)return std::nullopt;
        Record value{};
        std::copy(logical.begin(),logical.end(),value.bytes.begin());
        return value;
    }
    static LogicalRecord encode_logical(const Record& record) noexcept {return record.bytes;}
    static Record with_identity(Record record,std::uint16_t identity) noexcept {
        record.bytes[1]=static_cast<std::uint8_t>(identity);
        record.bytes[2]=static_cast<std::uint8_t>(identity>>8);
        return record;
    }
};
using RecoveredMonsterPoolRemoval=RecoveredWorldPoolRemoval<0x74>;
using RecoveredNpcPoolRemoval=RecoveredWorldPoolRemoval<0x75>;
}
