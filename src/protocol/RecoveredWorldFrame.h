#pragma once
#include "protocol/RecoveredZeroSeedKey.h"
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>
#include <stdexcept>
#include <vector>

namespace god2 {
// Envelope for the existing zero-seed recovered lab connection only. The
// 0xA00 cap is the current client's logical send queue, not an opcode grammar.
// Consumers still validate direction, record lengths, fields and session state.
struct RecoveredWorldFrame {
    static constexpr std::size_t max_logical_size=0xa00;
    static std::optional<std::vector<std::uint8_t>> decode(std::span<const std::uint8_t> wire) {
        if(wire.size()<4 || wire.size()>max_logical_size+3 ||
           wire[0]+256u*wire[1]!=wire.size()) return std::nullopt;
        std::vector<std::uint8_t> logical;
        logical.reserve(wire.size()-3);
        std::uint8_t previous=0,checksum=static_cast<std::uint8_t>(wire[0]+wire[1]+2*0x3c);
        for(std::size_t i=2;i<wire.size();++i) {
            previous=static_cast<std::uint8_t>(wire[i]+3-previous)^recovered_zero_seed_key[(i-2)&255];
            if(i+1==wire.size()) {
                if(previous!=checksum) return std::nullopt;
            } else {
                logical.push_back(previous);
                checksum=static_cast<std::uint8_t>(checksum+previous+0x3c);
            }
        }
        return logical;
    }

    static std::vector<std::uint8_t> encode(std::span<const std::uint8_t> logical) {
        if(logical.empty() || logical.size()>max_logical_size)
            throw std::invalid_argument("Recovered world logical frame exceeds queue bounds");
        const auto length=logical.size()+3;
        std::vector<std::uint8_t> wire{static_cast<std::uint8_t>(length),static_cast<std::uint8_t>(length>>8)};
        wire.reserve(length);
        std::uint8_t previous=0,checksum=static_cast<std::uint8_t>(wire[0]+wire[1]+2*0x3c);
        for(std::size_t i=0;i<logical.size();++i) {
            const auto plain=logical[i];
            wire.push_back(static_cast<std::uint8_t>((plain^recovered_zero_seed_key[i&255])+previous-3));
            previous=plain;
            checksum=static_cast<std::uint8_t>(checksum+plain+0x3c);
        }
        wire.push_back(static_cast<std::uint8_t>((checksum^recovered_zero_seed_key[logical.size()&255])+previous-3));
        return wire;
    }
};
}
