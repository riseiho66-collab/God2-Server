#pragma once
#include "protocol/RecoveredWorldUiByteUpdates.h"
#include <array>
#include <cstdint>
#include <optional>
#include <span>
namespace god2 {
// Current TW aaf0fae6:4E8910 controls18/19, event20, unsigned >1000ms
// gate, call4E8D8D->4132E0: B4 + one BYTE(control-18). No local CE write.
// E8->46B46E->4E8550 writes P+15E / (P+90)+CE, then4E8580.
// Pairing a user's explicit choice with this display update and persistence
// is CUSTOM-0142. This does not recover battle actor/pet slot deployment.
struct RecoveredBattleRowPreference {
    static constexpr std::uint8_t opcode=0xb4;
    static constexpr std::size_t logical_size=2;
    struct Request {std::uint8_t row;};
    static std::optional<Request> decode(std::span<const std::uint8_t> bytes) noexcept {
        if(bytes.size()!=logical_size || bytes[0]!=opcode || bytes[1]>1)return {};
        return Request{bytes[1]};
    }
    static std::optional<RecoveredWorldUiByteUpdates::LogicalRecord> projection(std::uint8_t row) noexcept {
        if(row>1)return {};
        const std::array<std::uint8_t,2> raw{0xe8,row};
        const auto record=RecoveredWorldUiByteUpdates::parse_logical(raw);
        if(!record)return {};
        return RecoveredWorldUiByteUpdates::encode_logical(*record);
    }
};
}
