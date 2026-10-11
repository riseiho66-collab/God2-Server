#pragma once
#include "cn/protocol/CnWorldConsumerRecords.h"

namespace god2cn {
// CN582f WORLD24: 00492A68 ->004912E8 (packet+1,actualU,mode0),
// lengthcell00567D34 ->00567B9A returns17. Original sixteen-byte payload.
// These four raw unsigned DWORDs store inline-role offsets5C/64/60/68.
// They do not identify an actor, selected subject, skill grant, MP/HP meaning,
// native64 profile, numerical cap or a causal ready-C1F reply.
class CnInlineRoleCounters24 final {
public:
    using Record=CnWorldConsumerRecord<0x24,17>;
    static constexpr std::size_t logical_size=17;
    inline static constexpr std::array<std::size_t,4> inline_offsets={0x5c,0x64,0x60,0x68};
    static std::optional<CnInlineRoleCounters24> read(std::span<const std::uint8_t> bytes) {
        const auto record=Record::parse_logical(bytes);
        if(!record)return std::nullopt;return CnInlineRoleCounters24(*record);
    }
    std::span<const std::uint8_t> payload() const noexcept {return record_.payload();}
    std::span<const std::uint8_t> logical_bytes() const noexcept {return record_.logical_bytes();}
    std::array<std::uint32_t,4> native_unsigned_words() const noexcept {
        const auto bytes=record_.payload();std::array<std::uint32_t,4> result;
        for(std::size_t n=0;n<result.size();++n) {
            const auto at=4*n;
            result[n]=std::uint32_t(bytes[at])|(std::uint32_t(bytes[at+1])<<8)|
                (std::uint32_t(bytes[at+2])<<16)|(std::uint32_t(bytes[at+3])<<24);
        }
        return result;
    }
private:
    explicit CnInlineRoleCounters24(Record record):record_(record){}
    Record record_;
};
}
