#pragma once
#include <cstdint>
#include <optional>
#include <span>

namespace god2cn {
// Fixed23-byte S2C02 (00567B50);0047E4D0 consumes LE16 status atpayload0
// and, on failure, payload20&7F as0047F530's message-field selector.
// Other bytes stay opaque. This view never synthesizes a success/failure.
struct CnWorldSelectionStatus {
    std::uint16_t status;
    std::uint8_t message_field_selector;
    static std::optional<CnWorldSelectionStatus> read(std::span<const std::uint8_t> record) {
        if(record.size()!=23 || record[0]!=0x02)return std::nullopt;
        return CnWorldSelectionStatus{
            static_cast<std::uint16_t>(record[1]|(std::uint16_t(record[2])<<8)),
            static_cast<std::uint8_t>(record[21]&0x7f)};
    }
};
}
