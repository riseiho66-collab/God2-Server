#pragma once
#include <algorithm>
#include <array>
#include <cstdint>
#include <optional>
#include <span>
namespace god2 {
// Current86/5 ->117590: bit0 enables primary actor from low nibble; bit1
// secondary/high nibble is OUTSIDE this two-player owner-slot0 source.
// Full raw bytes retained. This is a format, not a server turn permission.
struct RecoveredBattlePlayerGrant {
    using Bytes=std::array<std::uint8_t,17>;
    class Record {
    private:
        friend struct RecoveredBattlePlayerGrant;
        explicit Record(Bytes bytes):bytes_(bytes){}
        Bytes bytes_;
    };
    static std::optional<Record> parse(std::span<const std::uint8_t> bytes)noexcept{
        if(bytes.size()!=17||bytes[0]!=0x86||bytes[1]!=5||bytes[3]!=1||bytes[4]!=0)return {};
        Bytes copy;std::copy(bytes.begin(),bytes.end(),copy.begin());return Record(copy);
    }
    static Bytes encode(const Record& record)noexcept{return record.bytes_;}
};
}
