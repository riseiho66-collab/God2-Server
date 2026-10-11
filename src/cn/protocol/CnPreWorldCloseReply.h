#pragma once
#include <algorithm>
#include <array>
#include <cstdint>
#include <optional>
#include <span>

namespace god2cn {
// Native S2C03 has3 logical bytes (00567B50), not an opcode-only ACK.
// 00480B10 waits for03 and locally returns0;0048FCC0's03 branch sets EAX8
// before its cookie check/return, consumed separately by0048AA10. Neither
// recovers the two payload bytes' meaning or server issuance rule.
// Preserve complete actual-source bytes; no public/default success generator.
class CnPreWorldCloseReply {
public:
    static std::optional<CnPreWorldCloseReply> read(std::span<const std::uint8_t> record) {
        if(record.size()!=3 || record[0]!=0x03)return std::nullopt;
        CnPreWorldCloseReply value;
        std::copy(record.begin(),record.end(),value.record_.begin());return value;
    }
    std::array<std::uint8_t,3> record_bytes() const {return record_;}
private:
    CnPreWorldCloseReply()=default;
    std::array<std::uint8_t,3> record_{};
};
}
