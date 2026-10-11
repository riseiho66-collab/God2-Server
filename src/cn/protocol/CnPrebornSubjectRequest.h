#pragma once
#include <array>
#include <cstdint>
#include <optional>
#include <span>

namespace god2cn {
// Pinned5342B0 local emitter:84 + WORD at *[actual_this+430AC]+0.
// Its caller/phase/root is unqualified. Do not register this reader in WORLD
// ingress, call it UI cancellation, infer84->A0 or use its WORD as a common ID.
// A shape-only result cannot qualify an actual gameplay request.
struct CnPrebornSubjectRequest {
    std::array<std::uint8_t,3> raw_record;
    static std::optional<CnPrebornSubjectRequest> read(std::span<const std::uint8_t> record) {
        if(record.size()!=3 || record[0]!=0x84)return std::nullopt;
        return CnPrebornSubjectRequest{{record[0],record[1],record[2]}};
    }
    // Raw native object-start operand, distinct from object+90 family WORD.
    // Preserves all16 bits; no sign/progression/cost/authority inference.
    std::uint16_t native_object_start_word() const noexcept {
        return static_cast<std::uint16_t>(unsigned(raw_record[1])|(unsigned(raw_record[2])<<8));
    }
};
}
