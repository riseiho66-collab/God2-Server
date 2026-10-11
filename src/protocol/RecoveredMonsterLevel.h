#pragma once
#include <array>
#include <cstdint>
#include <optional>
#include <span>
namespace god2 {
// S2C78 -> 004CC840. Five logical bytes: lowWORD instance, highWORD
// supplied level. Native formats0..30 numerically,31..99 by band,>=100
// with its special label; pool+17B retains only the lowBYTE. Not a stat formula.
struct RecoveredMonsterLevel {
    using Bytes=std::array<std::uint8_t,5>;
    struct Record {std::uint16_t identity,level;bool operator==(const Record&) const=default;};
    static std::optional<Record> parse(std::span<const std::uint8_t> bytes) noexcept {
        if(bytes.size()!=5 || bytes[0]!=0x78)return std::nullopt;
        return Record{static_cast<std::uint16_t>(bytes[1]|(std::uint16_t{bytes[2]}<<8)),
            static_cast<std::uint16_t>(bytes[3]|(std::uint16_t{bytes[4]}<<8))};
    }
    static Bytes encode(Record value) noexcept {
        return {0x78,static_cast<std::uint8_t>(value.identity),static_cast<std::uint8_t>(value.identity>>8),
            static_cast<std::uint8_t>(value.level),static_cast<std::uint8_t>(value.level>>8)};
    }
};
}
