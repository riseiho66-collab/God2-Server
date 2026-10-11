#pragma once
#include "db/SqliteOwnedPkRoomRepository.h"
#include "protocol/RecoveredTaiwanPkTerminalNotification.h"

namespace god2 {
class OwnedPkRoomState;
// CUSTOM-0126 private source from ONE actual Finished room and original Ticket.
// RoomState appends this after its final88; repository independently rederives
// it under the same paired checkpoint/round/outbox transaction. Never caller
// templates/award scalars, diagnostic89, another room or a fabricated revision.
class OwnedTaiwanPkTerminalSource final {
    friend class OwnedPkRoomState;
    friend class SqliteOwnedPkRoomRepository;
    static RecoveredBattleExperience::LogicalRecord prepare(
            const SqliteOwnedPkRoomRepository::Ticket& ticket,
            const BattleSnapshot& actual,const OwnedPkRound& round){
        const auto& input=ticket.input();const auto& entry=input.entry;
        if(actual.id!=ticket.id()||actual.state!=BattleState::Finished||
           actual.numeric_profile!=BattleNumericProfile::LegacyCustom||
           !actual.victorious_side||*actual.victorious_side>1||
           round.phase()!=OwnedPkRound::Phase::Terminal||!round.terminal_notification()||
           round.battle_revision()!=actual.revision||!round.result_notification_bounds()||
           !input.combat_sources||!entry.owned_appearances()||!entry.owned_players()||
           !entry.owned_vitals()||!entry.owned_initial_contexts()||!entry.owned_initial_grants())
            throw DatabaseError("PK terminal notification requires its actual private Finished source graph");
        for(std::size_t position=0;position<actual.actors.size();++position)
            if(actual.actors[position].has_value()!=(position==0||position==14))
                throw DatabaseError("PK terminal notification actor topology changed");
        for(std::uint8_t viewer=0;viewer<2;++viewer){
            const auto& peer=viewer==0?input.pair.challenger:input.pair.recipient;
            const auto& actor=*actual.actors[14*viewer];
            if(actor.position!=14*viewer||actor.controller!=peer.character||!actor.max_hp||
               actor.hp>actor.max_hp||actor.mp>actor.max_mp||
               (actor.hp!=0)!=(viewer==*actual.victorious_side)||
               entry.characters()[viewer]!=peer.character)
                throw DatabaseError("PK terminal notification differs from the actual owned outcome");
        }
        return RecoveredTaiwanPkTerminalNotification::encode();
    }
};
}
