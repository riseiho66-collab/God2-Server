#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {
// Current aaf image: 46AE12 logical DWORD1/5 -> Main context T+28/T+2C;
// 511409/51140F -> battle B+3C/B+40. See
// tw-battle-identity-and-signed-loss-boundary-20261019.md, round469 identity v2.
// B+48 is separate: 4657CA captures current World R0 into T0, then 51141A
// copies T0 to B+48. Neither raw82 context establishes that self identity.
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
