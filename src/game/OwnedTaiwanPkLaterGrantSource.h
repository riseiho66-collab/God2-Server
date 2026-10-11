#pragma once
#include "db/SqliteOwnedPkRoomRepository.h"
#include "protocol/RecoveredBattlePlayerGrant.h"
#include <limits>

namespace god2 {
// CUSTOM-0121 fresh later primary UI grants for the private two-player arena.
// Repository alone calls this after qualifying the original owned Ticket and
// full actual runtime checkpoint against the same durable transaction. This
// is neither the original server producer nor skill/command permission.
class OwnedTaiwanPkLaterGrantSource final {
    friend class SqliteOwnedPkRoomRepository;
    static std::array<RecoveredBattlePlayerGrant::Bytes,2> prepare(
            const SqliteOwnedPkRoomRepository::Ticket& ticket,
            const BattleSnapshot& state,const OwnedPkRound& round){
        const auto& input=ticket.input();
        if(state.id!=ticket.id()||state.state!=BattleState::Active||
           state.numeric_profile!=BattleNumericProfile::LegacyCustom||
           round.phase()!=OwnedPkRound::Phase::Grants||round.round()<2||
           round.round()>static_cast<std::uint64_t>(std::numeric_limits<std::int32_t>::max())||
           !round.grant_epoch()||state.revision<=1||round.battle_revision()!=state.revision||
           !input.entry.waiting_control())
            throw DatabaseError("PK fresh later grant requires a qualified current owned Grants phase");
        for(std::size_t position=0;position<state.actors.size();++position)
            if(state.actors[position].has_value()!=(position==0||position==14))
                throw DatabaseError("PK fresh later grant has unowned arena actors");
        std::array<RecoveredBattlePlayerGrant::Bytes,2> result{};
        for(std::uint8_t viewer=0;viewer<2;++viewer){
            const auto& peer=viewer==0?input.pair.challenger:input.pair.recipient;
            const auto& actor=*state.actors[14*viewer];
            if(actor.position!=14*viewer||actor.controller!=peer.character||
               !actor.hp||actor.hp>actor.max_hp||actor.mp>actor.max_mp)
                throw DatabaseError("PK fresh later grant requires both living private controllers");
            RecoveredBattlePlayerGrant::Bytes bytes{};
            bytes[0]=0x86;bytes[1]=5;bytes[3]=1;bytes[4]=0;
            // Explicit CUSTOM display policy: labels001..999, repeating.
            // Native WORD5 is unsigned+1, lowest three decimal glyphs only.
            // It is NOT an epoch, timer, target mask or the88 counter. Only
            // primary own0 is enabled; no secondary-clear claim. Raw2/7..16
            // canonical0 is bounded serialization, not global padding proof.
            const auto label=static_cast<std::uint16_t>((round.round()-1)%999);
            bytes[5]=static_cast<std::uint8_t>(label);
            bytes[6]=static_cast<std::uint8_t>(label>>8);
            const auto parsed=RecoveredBattlePlayerGrant::parse(bytes);
            if(!parsed)throw DatabaseError("PK fresh later primary grant cannot be encoded");
            result[viewer]=RecoveredBattlePlayerGrant::encode(*parsed);
        }
        return result;
    }
};
}
