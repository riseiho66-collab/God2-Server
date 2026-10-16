#pragma once
#include "protocol/RecoveredMovement.h"
#include <algorithm>

namespace god2 {
// TW15790 writes coordinates/index, queues6 bytes including an unwritten tail.
// Native ring1036B0 has40 slots, with one slot reserved (39 pending max).
// Both native102558/102608 callers supply the pre-push write cursor+236.
// The recovered reset-then-one-seed paths leave that cursor at1; this is
// client state, not a server admission/reset rule or5D echo contract.
// See docs/research/tw-native-movement-cursor-recovery-20261016.md.
// Ordinary branch only: the old parser/policies
// remain unchanged; no modulo reduction, zero-tail requirement or echo builder.
struct RecoveredNativeMovement {
    static bool ordinary_request(const RecoveredMovement::Request& request) noexcept {
        return request.sequence<40;
    }
    class Ack {
    public:
        const std::array<std::uint8_t,2>& logical() const noexcept {return logical_;}
    private:
        friend struct RecoveredNativeMovement;
        explicit Ack(std::array<std::uint8_t,2> bytes):logical_(bytes){}
        std::array<std::uint8_t,2> logical_;
    };
    // TW WORLD692FA stores byte at+231 and pops one pending point regardless
    // of its value. Full native value is a mandatory authority input, not an
    // automatically echoed request index or manufactured success record.
    static std::optional<Ack> read_ack(std::span<const std::uint8_t> logical) {
        if(logical.size()!=2 || logical[0]!=0x5d)return std::nullopt;
        std::array<std::uint8_t,2> full;
        std::copy(logical.begin(),logical.end(),full.begin());return Ack{full};
    }
};
}
