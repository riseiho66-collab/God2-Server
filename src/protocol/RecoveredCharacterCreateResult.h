#pragma once
#include "protocol/RecoveredZeroSeedKey.h"
#include <array>
#include <cstdint>

namespace god2 {
// Current mapped image SHA-256:
// 149C1B4510A2DEE85EB988D3F6C05785A69CBF50BB8FB751AF7D9814A5A6E763
// RVA 0x1507A..0x1507F selects opcode 2; 0x150D8 reads its result WORD.
// Result zero branches to 0x15166. Length table [0x132C] -> 0x1234
// Opcode17 caller uses14EB0: 14F16 selects2,14F72 reads WORD,
// zero branches15000 to consume, then1500B returns EAX0.
// returns 23 logical bytes: 26 with the length header and checksum.
// Static contract only. Not wired to Session until creation commits to storage.
struct RecoveredCharacterCreateResult {
    using Frame=std::array<std::uint8_t,26>;
    static constexpr Frame committed_success() {
        Frame plain{};
        plain[0]=26;plain[2]=2;
        unsigned checksum=0;
        for(std::size_t i=0;i+1<plain.size();++i) checksum+=plain[i]+0x3c;
        plain.back()=static_cast<std::uint8_t>(checksum);
        Frame wire=plain;
        std::uint8_t previous=0;
        for(std::size_t i=2;i<wire.size();++i) {
            wire[i]=static_cast<std::uint8_t>((plain[i]^recovered_zero_seed_key[i-2])+previous-3);
            previous=plain[i];
        }
        return wire;
    }
};
}
