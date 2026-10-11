#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {
// Current image RVA6AE12/111409; see current-battle-entry-20260919.md.
// Raw contexts only: no encounter, map, monster or turn semantics established.
struct RecoveredBattleEntry {
    static constexpr std::size_t logical_size=9;
    using Bytes=std::array<std::uint8_t,logical_size>;
    struct Record {
        std::uint32_t context_a,context_b;
        bool operator==(const Record&) const = default;
    };
    static constexpr Bytes encode_logical(Record record) noexcept {
        Bytes bytes{};bytes[0]=0x82;
        for(unsigned i=0;i<4;++i) {
            bytes[1+i]=static_cast<std::uint8_t>(record.context_a>>(8*i));
            bytes[5+i]=static_cast<std::uint8_t>(record.context_b>>(8*i));
        }
        return bytes;
    }
    static constexpr std::optional<Record> parse_logical(std::span<const std::uint8_t> bytes) noexcept {
        if(bytes.size()!=logical_size || bytes[0]!=0x82) return std::nullopt;
        Record record{};
        for(unsigned i=0;i<4;++i) {
            record.context_a|=std::uint32_t{bytes[1+i]}<<(8*i);
            record.context_b|=std::uint32_t{bytes[5+i]}<<(8*i);
        }
        return record;
    }
};
}
