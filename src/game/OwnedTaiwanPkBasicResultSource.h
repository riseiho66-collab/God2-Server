#pragma once
#include "db/SqliteOwnedPkRoomRepository.h"
#include "protocol/RecoveredPkActionProjection.h"
#include <limits>

namespace god2 {
class OwnedPkRoomState;
// CUSTOM-0117 fresh BASIC1 result policy for the private two-player TW arena.
// Only RoomState may construct it from its actual Ticket/checkpoint/Ready round.
// No diagnostic/raw template promotion, public scalar capability or skill3.
// Not installed by Application; native renderer/global-alias acceptance OPEN.
class OwnedTaiwanPkBasicResultSource final {
    friend class OwnedPkRoomState;
    using Templates=RecoveredPkActionProjection::Templates;
    static std::array<Templates,2> prepare(const SqliteOwnedPkRoomRepository::Ticket& ticket,
            const BattleSnapshot& state,const OwnedPkRound& round,
            const std::array<std::uint8_t,2>& order){
        const auto& input=ticket.input();const auto& entry=input.entry;
        if(state.id!=ticket.id()||state.state!=BattleState::Active||
           state.numeric_profile!=BattleNumericProfile::LegacyCustom||
           round.phase()!=OwnedPkRound::Phase::Ready||round.battle_revision()!=state.revision||
           !round.round()||round.round()>static_cast<std::uint64_t>(std::numeric_limits<std::int32_t>::max())||
           !((order==std::array<std::uint8_t,2>{0,1})||(order==std::array<std::uint8_t,2>{1,0}))||
           !input.combat_sources||!entry.owned_appearances()||!entry.owned_players()||
           !entry.owned_vitals()||!entry.vital_templates()||!entry.owned_initial_contexts()||
           !entry.owned_initial_grants()||!entry.waiting_control())
            throw DatabaseError("PK fresh basic result requires the exact owned initial source graph and Ready round");
        for(std::size_t position=0;position<state.actors.size();++position)
            if(state.actors[position].has_value()!=(position==0||position==14))
                throw DatabaseError("PK fresh basic result has unowned arena actors");
        for(std::uint8_t viewer=0;viewer<2;++viewer){
            const auto& peer=viewer==0?input.pair.challenger:input.pair.recipient;
            const auto& actor=*state.actors[14*viewer];
            const auto& vital=(*entry.owned_vitals())[viewer];
            const auto& context=(*entry.owned_initial_contexts())[viewer];
            const auto& combat=(*input.combat_sources)[viewer];
            const auto& intent=round.intents()[viewer];
            if(!intent||intent->skill_key||!intent->definition_readset.empty()||
               intent->action.source!=14*viewer||intent->action.targets!=std::vector<std::uint8_t>{
                   static_cast<std::uint8_t>(14*(1-viewer))}||intent->action.magical||intent->action.mp_cost||
               actor.position!=14*viewer||actor.controller!=peer.character||!actor.hp||
               actor.hp>actor.max_hp||actor.mp>actor.max_mp||
               entry.characters()[viewer]!=peer.character||
               combat.appearance()!=(*entry.owned_appearances())[viewer]||vital.combat()!=combat||
               (*entry.owned_players())[viewer].combat()!=combat||
               context.player()!=(*entry.owned_players())[viewer]||context.vital()!=vital||
               vital.hp().maximum()!=actor.max_hp||vital.mp().maximum()!=actor.max_mp||
               (*entry.vital_templates())[viewer][0]!=RecoveredBattleVitals::encode_logical(vital.hp())||
               (*entry.vital_templates())[viewer][1]!=RecoveredBattleVitals::encode_logical(vital.mp()))
                throw DatabaseError("PK fresh basic result does not match both private participants and collected basic intents");
            // Retained CUSTOM-0111 initial88 seed is exactly0. A genuine legacy
            // Ticket alone is insufficient. Never call prebattle world Current
            // after commit: immutable entry receipts bind the source identity;
            // actual mutable values come from this room's current Battle.
            const auto& initial=context.bulk_bytes();
            if(initial[0]!=0x88||!std::all_of(initial.begin()+1,initial.begin()+5,[](auto b){return b==0;})||
               !std::all_of(initial.begin()+117,initial.end(),[](auto b){return b==0;}))
                throw DatabaseError("PK fresh result counter requires the exact retained initial zero seed");
            for(std::size_t slot=1;slot<14;++slot){
                const auto values=*context.bulk().at(slot);
                if(values.hp||values.mp)throw DatabaseError("PK fresh result requires reset friendly placeholders");
            }
            const auto own=*context.bulk().at(0);
            if(own.hp!=vital.hp().current()||own.mp!=vital.mp().current())
                throw DatabaseError("PK retained initial resources no longer match their immutable source");
        }
        const auto build=[&](std::uint8_t canonical_actor){
            const auto animation=[&](std::uint8_t viewer){
                RecoveredBattleAttackPresentation::Bytes bytes{};
                bytes[0]=0x83;bytes[1]=1;
                bytes[2]=RecoveredPkRelativeView::position(static_cast<std::uint8_t>(14*canonical_actor),viewer);
                // CUSTOM queue schedule: two distinct groups in explicit server
                // execution order, range0..253, repeating every127 rounds.
                // Avoid255: manager12AC20 increments the BYTE boundary and
                // skips its actor scan on wrap. Not a nonce/original formula.
                bytes[3]=static_cast<std::uint8_t>(((round.round()-1)%127)*2+(order[0]==canonical_actor?0:1));
                const auto target=RecoveredPkRelativeView::position(static_cast<std::uint8_t>(14*(1-canonical_actor)),viewer);
                bytes[5+2*(target/14)]=1;bytes[12]=28;
                // R4/basic R13/R14 zero are explicit CUSTOM serialization.
                // Qualified selected handlers do not read them; full15 copies,
                // global/context aliases and later rendering are not erased.
                return *RecoveredBattleAttackPresentation::parse(bytes);
            };
            const auto bulk=[&]{
                RecoveredBattleVitalsBatch::Bytes bytes{};bytes[0]=0x88;
                const auto counter=static_cast<std::uint32_t>(round.round());
                for(unsigned i=0;i<4;++i)bytes[1+i]=static_cast<std::uint8_t>(counter>>(8*i));
                // Positive signed DWORD relative to retained seed0; not native
                // round identity or proof readiness/event/0B will succeed.
                // Raw117..120=0 is explicit fresh display policy. Slots1..13
                // remain reset placeholders. Projection writes actual own HP/MP.
                return *RecoveredBattleVitalsBatch::parse_logical(bytes);
            };
            return Templates{{animation(0),animation(1)},
                {(*entry.owned_vitals())[0].hp(),(*entry.owned_vitals())[1].hp()},
                {(*entry.owned_vitals())[0].mp(),(*entry.owned_vitals())[1].mp()},
                {bulk(),bulk()}};
        };
        return {build(0),build(1)};
    }
};
}
