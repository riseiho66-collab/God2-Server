#pragma once
#include "game/RecoveredCharacter.h"
#include "protocol/LegacyCharacterListCandidate.h"
#include <algorithm>
#include <span>
#include <stdexcept>

namespace god2 {
// Experimental populated 07: current client consumer correspondence, not
// captured original-server bytes. Unknown server-owned fields remain zero.
// See docs/research/original-client-create-profile-20260919.md.
struct RecoveredCharacterListCandidate {
    using Frame=LegacyCharacterListCandidate::Frame;
    static bool valid_profile(const std::array<std::uint8_t,40>& p) {
        const auto end=std::find(p.begin(),p.begin()+15,0);
        const auto packed=static_cast<unsigned>(p[38])+256u*p[39];
        return end!=p.begin() && end!=p.begin()+15 &&
            p[29]>=1 && p[29]<=8 && p[31]>=1 && p[31]<=5 &&
            p[32]<=6 && p[33]<=1 && (p[29]-1)%2==p[33] &&
            ((p[36]>>5)&7)<=6 && (packed&15)==p[33] &&
            ((packed>>4)&63)<=9 && ((packed>>10)&63)<=9;
    }
    static Frame decoded(std::span<const RecoveredCharacter> characters, std::uint8_t route_id=0) {
        if(characters.empty()) return LegacyCharacterListCandidate::decoded();
        if(characters.size()>2) throw std::invalid_argument("Character list exceeds current wire capacity");
        Frame frame{};frame[0]=78;frame[2]=7;
        frame[3]=static_cast<std::uint8_t>(characters.size());
        std::array<bool,2> seen{};
        for(std::size_t i=0;i<characters.size();++i) {
            const auto& character=characters[i];
            if(character.slot>=2 || seen[character.slot] || !valid_profile(character.profile))
                throw std::invalid_argument("Character profile cannot be represented by candidate");
            seen[character.slot]=true;
            const auto& p=character.profile;
            const auto start=5+36*i;
            const auto end=std::find(p.begin(),p.begin()+15,0);
            std::copy(p.begin(),end,frame.begin()+start);
            // Raw UI W[17] and create C[29] share paired-category arithmetic.
            frame[start+17]=p[29];
            // Local opaque selection token, not a recovered original slot rule.
            // RVA BA13 -> 14C50 echoes W[19]&7 (builder supports 0..3).
            frame[start+19]=character.slot;
            // Equivalent resource consumers at 8067/8093/80B0/80DE and
            // CC05/CC2F/CC4D; only mapped appearance bits are populated.
            frame[start+20]=p[36];
            frame[start+22]=static_cast<std::uint8_t>(p[38]&0xf0);
            frame[start+23]=p[39];
            // The current selection renderer (RVA 8310..852E) consumes W[24..31]
            // as four two-byte component records and passes each high three bits
            // to FFA20. The current create preview (RVA 9A10..9A65) builds the
            // same component records from C[32], C[33], and C[36]. Omitting the
            // remaining records made a saved female use default component banks.
            frame[start+24]=p[33];
            frame[start+25]=static_cast<std::uint8_t>(p[32]<<5);
            frame[start+26]=p[33];
            frame[start+27]=static_cast<std::uint8_t>(p[36]&0xe0);
            frame[start+28]=p[33];
            frame[start+30]=static_cast<std::uint8_t>(0x80|p[33]);
            // Current RVA 1235E reads W[32] for 05/06 endpoint lookup.
            // Zero preserves the existing candidate; advertised routes are nonzero.
            frame[start+32]=static_cast<std::uint8_t>(route_id);
        }
        std::uint8_t checksum=0;
        for(std::size_t i=0;i+1<frame.size();++i)
            checksum=static_cast<std::uint8_t>(checksum+frame[i]+0x3c);
        frame.back()=checksum;
        return frame;
    }
    static Frame wire(std::span<const RecoveredCharacter> characters, std::uint8_t route_id=0) {
        const auto plain=decoded(characters,route_id);auto result=plain;
        std::uint8_t previous=0;
        for(std::size_t i=2;i<result.size();++i) {
            result[i]=static_cast<std::uint8_t>((plain[i]^recovered_zero_seed_key[i-2])+previous-3);
            previous=plain[i];
        }
        return result;
    }
};
}
