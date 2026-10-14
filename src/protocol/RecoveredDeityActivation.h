#pragma once
#include "protocol/RecoveredDeityState.h"
namespace god2 {
// Native S2C WORLD35: logical4 / body3, actual4AA830. This describes
// direct matching-entry flag3 writes only; it supplies no learning authority.
// CUSTOM-0148 owns issuance/ordering/persistence separately from this grammar.
struct RecoveredDeityActivation {
    using Record=RecoveredDeityState::Record<0x35,4>;
    using Bytes=Record::Bytes;
    static constexpr Bytes encode(std::uint8_t subject,std::uint8_t kind,std::uint8_t id) noexcept {
        return {0x35,subject,kind,id};
    }
    static std::optional<Record> parse(std::span<const std::uint8_t> raw) noexcept {return Record::parse(raw);}
};
}
