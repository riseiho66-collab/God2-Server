#pragma once
#include "protocol/RecoveredZeroSeedKey.h"
#include <algorithm>
#include <array>
#include <cstdint>
#include <optional>
#include <span>
#include <string>

namespace god2 {
// Current mapped image SHA-256:
// 149C1B4510A2DEE85EB988D3F6C05785A69CBF50BB8FB751AF7D9814A5A6E763
// RVA 0x14CC0: enabled at object+0x2CB8; writes payload[0x28]=4,
// queues opcode 0x1B and 0x2C payload bytes at 0x14CDA, flushes at 0x14CE1.
// This is a structural request decoder, not character creation or live acceptance.
struct RecoveredCharacterCreate {
    static constexpr std::size_t wire_size = 48;
    std::array<std::uint8_t, 44> payload{}; // Opaque fields; do not log names/data.
    std::uint8_t opcode = 0x1b;

    // UI validation RVA 0xAD34 passes limit 14 to 0x165D0, which copies
    // min(strlen, limit) bytes and appends NUL into object+0x15280.
    // RVA 0xC168 copies that record to this builder's payload. Keep the
    // original encoded bytes; no ASCII/UTF-8 assumption or normalization.
    std::optional<std::string> name_bytes() const {
        const auto end=std::find(payload.begin(),payload.begin()+15,0);
        if(end==payload.begin() || end==payload.begin()+15) return std::nullopt;
        return std::string(payload.begin(),end);
    }

    static std::optional<RecoveredCharacterCreate> parse(std::span<const std::uint8_t> wire) {
        if(wire.size()!=wire_size || wire[0]!=wire_size || wire[1]!=0) return std::nullopt;
        std::array<std::uint8_t, 46> clear{};
        std::uint8_t previous=0;
        for(std::size_t i=0;i<clear.size();++i) {
            clear[i]=static_cast<std::uint8_t>(wire[i+2]+3-previous)^recovered_zero_seed_key[i];
            previous=clear[i];
        }
        std::uint8_t checksum=static_cast<std::uint8_t>(wire_size+2*0x3c);
        for(std::size_t i=0;i+1<clear.size();++i)
            checksum=static_cast<std::uint8_t>(checksum+clear[i]+0x3c);
        // Live native-create-submit-20260920-03: C0B0 ->14CF0 sends17.
        // The older C160 ->14CC0 path sends1B with the same bounded body.
        if((clear[0]!=0x1b && clear[0]!=0x17) || clear[41]!=4 || clear.back()!=checksum) return std::nullopt;
        RecoveredCharacterCreate result;
        result.opcode=clear[0];
        std::copy_n(clear.begin()+1,result.payload.size(),result.payload.begin());
        return result;
    }
};
}
