#pragma once
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {
// S2C6B, native world dispatcher 46AABE -> 4CC910. The first body DWORD is
// looked up unchanged in the existing 256-record world monster/display pool.
// The remaining 16 bytes are passed as a C string to 509E70, which writes the
// secondary overhead text. This is unrelated to the C2S6B companion control.
// No record creation, name authority or C2S request/reply pairing is implied.
struct RecoveredWorldPoolText6B {
    static constexpr std::uint8_t opcode=0x6b;
    static constexpr std::size_t logical_size=21, text_size=16;
    using Text=std::array<std::uint8_t,text_size>;
    using Logical=std::array<std::uint8_t,logical_size>;
    struct Record {
        std::uint32_t identity{};
        Text text{};
        bool operator==(const Record&) const=default;
    };
    static std::optional<Record> decode(std::span<const std::uint8_t> bytes) noexcept {
        if(bytes.size()!=logical_size || bytes[0]!=opcode)return {};
        Record record{};
        for(unsigned i=0;i<4;++i)record.identity|=std::uint32_t{bytes[1+i]}<<(8*i);
        std::copy(bytes.begin()+5,bytes.end(),record.text.begin());
        // Native 509E70 scans for a terminator, not a bounded 16-byte field.
        if(std::find(record.text.begin(),record.text.end(),0)==record.text.end())return {};
        return record;
    }
    static std::optional<Logical> encode(const Record& record) noexcept {
        const auto end=std::find(record.text.begin(),record.text.end(),0);
        if(end==record.text.end() ||
           std::any_of(end,record.text.end(),[](std::uint8_t value){return value!=0;}))return {};
        Logical bytes{};
        bytes[0]=opcode;
        for(unsigned i=0;i<4;++i)bytes[1+i]=static_cast<std::uint8_t>(record.identity>>(8*i));
        std::copy(record.text.begin(),record.text.end(),bytes.begin()+5);
        return bytes;
    }
};
}
