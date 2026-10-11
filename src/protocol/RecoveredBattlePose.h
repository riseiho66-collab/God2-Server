#pragma once
#include "protocol/RecoveredBattleBootstrap.h"
#include "protocol/RecoveredWorldFrame.h"
#include <algorithm>
#include <array>
#include <cstdint>
#include <optional>
#include <span>
#include <utility>
#include <vector>

namespace god2 {
// Pinned TW battle519300 reads only body WORD0 and symbol BYTE2 from S77.
// This differs from the world77 posture consumer. Native C66 Ctrl callers
// supply posture0, a dynamic symbol BYTE and an unwritten opaque tail BYTE.
// No symbol-to-skill/key mapping, actor construction or original ACK inferred.
struct RecoveredBattlePose {
    using Logical=std::array<std::uint8_t,7>;
    using Grant=std::array<std::uint8_t,17>;
    class Publication {
    public:
        const std::vector<std::uint8_t>& logical()const noexcept{return logical_;}
        const std::array<std::optional<RecoveredBattleIdentity::Record>,28>& actors()const noexcept{return actors_;}
        const Grant& grant()const noexcept{return grant_;}
    private:
        friend struct RecoveredBattlePose;
        Publication(std::vector<std::uint8_t> logical,
                std::array<std::optional<RecoveredBattleIdentity::Record>,28> actors,Grant grant)
            :logical_(std::move(logical)),actors_(std::move(actors)),grant_(grant){}
        std::vector<std::uint8_t> logical_;
        std::array<std::optional<RecoveredBattleIdentity::Record>,28> actors_;
        Grant grant_;
    };
    // CUSTOM-0103: closed parser for the ACTUAL existing Application bootstrap,
    // not a new client authority input. Preserve all bytes and every actor.
    // Unknown shapes fail closed rather than scan arbitrary payloads for1C/86.
    // This is prepared publication material, not Written/constructed/ACK.
    static std::optional<Publication> publication(std::span<const std::uint8_t> logical) {
        if(logical.empty() || logical.size()>RecoveredWorldFrame::max_logical_size)return {};
        const auto original=logical;
        std::array<std::optional<RecoveredBattleIdentity::Record>,28> actors;
        std::optional<Grant> grant;
        bool any_actor=false;
        while(!logical.empty()) {
            std::size_t size=0;
            switch(logical[0]) {
            case 0x1c:size=RecoveredBattleIdentity::logical_size;break;
            case 0x22:size=25;break; // existing complete role-level prefix
            case 0x83:size=15;break; // existing diagnostic summon/action prefix
            case 0x86:size=17;break;
            case 0x87:size=3;break;  // existing skill-enable prefix
            case 0x88:size=121;break;
            default:return {};
            }
            if(logical.size()<size)return {};
            const auto record=logical.first(size);
            if(record[0]==0x1c) {
                const auto actor=RecoveredBattleIdentity::parse_logical(record);
                if(!actor || actors[actor->position()])return {};
                actors[actor->position()]=*actor;any_actor=true;
            } else if(record[0]==0x86 && record[1]==5) {
                if(grant)return {}; // no guessed last-wins grant authority
                Grant copy;std::copy(record.begin(),record.end(),copy.begin());grant=copy;
            }
            logical=logical.subspan(size);
        }
        if(!any_actor || !grant)return {};
        return Publication({original.begin(),original.end()},std::move(actors),*grant);
    }
    static bool qualified_request(const std::array<std::uint8_t,3>& payload)noexcept {
        return (payload[1]>>3)==0; // low3 and unwritten tail are not authority
    }
    static Logical logical(std::uint16_t native_actor,std::uint8_t symbol)noexcept {
        // Unread bytes are an explicit CUSTOM zero projection, not native data.
        return {0x77,static_cast<std::uint8_t>(native_actor),
            static_cast<std::uint8_t>(native_actor>>8),symbol,0,0,0};
    }
};
}
