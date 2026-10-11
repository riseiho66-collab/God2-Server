#pragma once
#include "db/NativeWeaponCatalog.h"
#include "protocol/RecoveredCharacterListCandidate.h"
#include <algorithm>
#include <array>
#include <stdexcept>
#include <span>
namespace god2 {
// Native source text only. This is not a recovered complete server equip rule.
struct RecoveredWeaponSexRestriction {
    enum class Sex { Male,Female };
    enum class Requirement { None,Male,Female };
    static Sex profile_sex(const std::array<std::uint8_t,40>& profile) {
        // Current create buttons0F/10 bind Flow_CarBoy/Girl; serialized40 bytes
        // retain sex33 and cross-check paired29 and packed38 low nibble.
        if(!RecoveredCharacterListCandidate::valid_profile(profile))
            throw std::invalid_argument("Owned character sex profile rejected");
        return profile[33]==0?Sex::Male:Sex::Female;
    }
    static Requirement requirement(const NativeWeaponRecord& record) {
        if((record.family!="WPN" && record.family!="TWP") || record.parsed_record.size()!=396)
            throw std::invalid_argument("Weapon source restriction shape rejected");
        const auto begin=record.parsed_record.begin()+0x2e;
        const auto end=std::find(begin,record.parsed_record.begin()+0x114,0);
        if(end==record.parsed_record.begin()+0x114)
            throw std::invalid_argument("Unterminated native weapon description");
        // Exact CP950 source phrases: 限男性角色裝備 / 限女性角色裝備.
        constexpr std::array<std::uint8_t,14> male{0xad,0xad,0xa8,0x6b,0xa9,0xca,0xa8,0xa4,0xa6,0xe2,0xb8,0xcb,0xb3,0xc6};
        constexpr std::array<std::uint8_t,14> female{0xad,0xad,0xa4,0x6b,0xa9,0xca,0xa8,0xa4,0xa6,0xe2,0xb8,0xcb,0xb3,0xc6};
        const bool m=std::search(begin,end,male.begin(),male.end())!=end;
        const bool f=std::search(begin,end,female.begin(),female.end())!=end;
        if(m && f)throw std::invalid_argument("Ambiguous native weapon sex restriction");
        return m?Requirement::Male:f?Requirement::Female:Requirement::None;
    }
    static bool permits(Requirement requirement,Sex sex) noexcept {
        return requirement==Requirement::None ||
            (requirement==Requirement::Male && sex==Sex::Male) ||
            (requirement==Requirement::Female && sex==Sex::Female);
    }
};
}
