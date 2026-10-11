#pragma once
#include "game/ShunyingSanshazhan.h"
#include <array>
#include <cstdint>
#include <stdexcept>

namespace god2 {
// CUSTOM-0058 isolated character6/test only. Native named-deity key102 selects
// female GodDoll bank1: 5038CD..5038E7, CSV r2 -> index1 at455374..455388.
// Basic h00/b00/w00 are explicit fixture dress, not a recovered acquisition rule.
// World36 is NOT battle1C and must not be used as a second battle participant.
struct DiagnosticShunyingFemaleDeity {
    static constexpr std::uint8_t key=102;
    static std::array<std::uint8_t,11> world_appearance(std::uint64_t owner) {
        if(owner!=6) throw std::invalid_argument("Female deity trial is character6 only");
        // 36: h,b,w,s (1-based), deitykey, opaque0, identity14+flags2,
        // presentation bytes0/0. Native resolver4614A0 decrements components.
        return {0x36,1,1,1,0,key,0,static_cast<std::uint8_t>(owner),0,0,0};
    }
    static std::array<std::uint8_t,8> learned_trial_skills() {
        // Restore owned30/31 first. No duplicate30/key1 declaration here.
        // Persisted owned validator retains native bank limits; custom126
        // is session-only under the isolated manual skill policy.
        return {0x34,key,0,ShunyingSanshazhan::id,0x34,key,0,8};
    }
    static std::array<std::uint8_t,17> battle_components(std::uint8_t friendly_slot=0) {
        if(friendly_slot>=14) throw std::invalid_argument("Invalid female deity owner slot");
        // Original51FC40 already creates type4 companion attachments for
        // every player slot. 5177C0 mode0 fills that attachment, preserving
        // the normal player's four components and independent identity.
        // 81 = female-bank high bit + basic-component index1; w00 is shared.
        return {0x86,4,friendly_slot,0,0x81,0x81,1,0,0,0,0,0,0,0,0,0,0};
    }
    static std::array<std::uint8_t,15> battle_summon(std::uint8_t friendly_slot=0) {
        if(friendly_slot>=14) throw std::invalid_argument("Invalid female deity owner slot");
        // Original83 subtype7 ->516ECD reads packed deity from logical9.
        // 52DCC0 decodes102 as named deity; source/target are the owner's slot.
        // Issue after components and player1C, before the ready88 cycle.
        const auto self=static_cast<std::uint16_t>(1u<<friendly_slot);
        return {0x83,7,friendly_slot,0,0,static_cast<std::uint8_t>(self),
                static_cast<std::uint8_t>(self>>8),0,0,key,0,0,0,0,0};
    }
};
}
