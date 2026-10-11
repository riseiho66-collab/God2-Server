#pragma once
#include "protocol/RecoveredZeroSeedKey.h"
#include <algorithm>
#include <array>
#include <cstdint>
#include <optional>
#include <span>

namespace god2 {
struct RecoveredC2S0002 {
    using Wire=std::array<std::uint8_t,176>;
    using Payload=std::array<std::uint8_t,173>;
    struct Parsed {
        Wire raw;
        Payload logical; // Contains local test credentials. Never log this buffer.
        std::size_t consumed=176;
    };
    static Wire encode(const Payload& payload) {
        Wire wire{};wire[0]=176;
        std::uint8_t checksum=static_cast<std::uint8_t>(176+2*0x3c);
        for(auto byte:payload) checksum=static_cast<std::uint8_t>(checksum+byte+0x3c);
        std::uint8_t previous=0;
        for(std::size_t i=0;i<174;++i) {
            const auto clear=i<173?payload[i]:checksum;
            wire[i+2]=static_cast<std::uint8_t>((recovered_zero_seed_key[i]^clear)+previous-3);
            previous=clear;
        }
        return wire;
    }
    static std::optional<Parsed> parse(std::span<const std::uint8_t> wire,std::uint8_t expected_opcode=4) {
        if(expected_opcode!=4 && expected_opcode!=0) return std::nullopt;
        if(wire.size()!=176 || wire[0]!=176 || wire[1]!=0) return std::nullopt;
        Parsed result{};std::copy(wire.begin(),wire.end(),result.raw.begin());
        std::uint8_t previous=0;
        for(std::size_t i=0;i<173;++i) {
            const auto clear=static_cast<std::uint8_t>(wire[i+2]+3-previous)^recovered_zero_seed_key[i];
            result.logical[i]=static_cast<std::uint8_t>(clear);previous=static_cast<std::uint8_t>(clear);
        }
        const auto& p=result.logical;
        // Exact observed builder: two bounded strings, constant 0xc8, config word <1000.
        if(p[0]!=expected_opcode || p[24]!=0 || p[156]!=0 || p[167]!=0xc8 || (p[165]+256*p[166])>=1000)
            return std::nullopt;
        if(encode(p)!=result.raw) return std::nullopt;
        return result;
    }
    static std::optional<Wire> response(const Parsed& request) {
        auto p=request.logical;
        // This experiment only covers the observed zero flag branch; no fabricated flags.
        if(p[0]!=4 || p[168]!=0) return std::nullopt;
        p[0]=0x1d;
        return encode(p);
    }
};
}
