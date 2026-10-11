#pragma once
#include "protocol/RecoveredZeroSeedKey.h"
#include <array>
#include <algorithm>
#include <optional>
#include <span>

namespace god2 {
// Current D26E..D286 sends BE80 (18/5 bytes), then 14C50 (1A/41 bytes).
// Each builder flushes, but TCP may split/coalesce the two frames.
struct RecoveredPostCreateSelect {
    struct Selection {
        // Owned original credential-bearing input. Never log these buffers or
        // substitute character names for the two native credential strings.
        std::array<std::uint8_t,41> raw;
        std::array<std::uint8_t,38> logical;
        std::optional<std::array<std::uint8_t,5>> prefix;
        std::uint8_t token() const noexcept {return logical[33];}
        bool operator==(const Selection&) const=default;
    };
    static constexpr std::size_t wire_size=46;
    std::uint8_t context_byte=0;
    std::uint8_t selection_token=0;
    Selection native_selection{};

    template<std::size_t N>
    static std::optional<std::array<std::uint8_t,N-3>> decode(std::span<const std::uint8_t> wire) {
        static_assert(N==5 || N==41);
        if(wire.size()!=N || wire[0]!=N || wire[1]!=0) return std::nullopt;
        std::array<std::uint8_t,N-3> result{};
        std::uint8_t previous=0,checksum=static_cast<std::uint8_t>(N+2*0x3c);
        for(std::size_t i=0;i<N-2;++i) {
            const auto clear=static_cast<std::uint8_t>(wire[i+2]+3-previous)^recovered_zero_seed_key[i];
            previous=static_cast<std::uint8_t>(clear);
            if(i==N-3) { if(clear!=checksum) return std::nullopt; }
            else {
                result[i]=static_cast<std::uint8_t>(clear);
                checksum=static_cast<std::uint8_t>(checksum+clear+0x3c);
            }
        }
        return result;
    }
    static bool valid_prefix(std::span<const std::uint8_t> wire) {
        if(wire.size()<5) return false;
        const auto first=decode<5>(wire.first(5));
        return first && (*first)[0]==0x18;
    }
    static std::optional<Selection> selection_from_frame(std::span<const std::uint8_t> wire) {
        const auto decoded=decode<41>(wire);
        if(!decoded || (*decoded)[0]!=0x1a || (*decoded)[16]!=0 || (*decoded)[32]!=0 ||
           (*decoded)[33]>=4 || (*decoded)[34]!=4) return std::nullopt;
        Selection result{};std::copy(wire.begin(),wire.end(),result.raw.begin());
        result.logical=*decoded;return result;
    }
    static std::optional<std::uint8_t> selection_token_from_frame(std::span<const std::uint8_t> wire) {
        const auto selected=selection_from_frame(wire);
        return selected?std::optional{selected->token()}:std::nullopt;
    }
    static std::optional<RecoveredPostCreateSelect> parse(std::span<const std::uint8_t> wire) {
        if(wire.size()!=wire_size || !valid_prefix(wire)) return std::nullopt;
        const auto first=decode<5>(wire.first(5));
        auto selected=selection_from_frame(wire.subspan(5));
        if(!selected) return std::nullopt;
        std::array<std::uint8_t,5> prefix;std::copy_n(wire.begin(),5,prefix.begin());selected->prefix=prefix;
        // Tail 35..37 is unwritten client stack data, not a constant.
        return RecoveredPostCreateSelect{(*first)[1],selected->token(),*selected};
    }
};
}
