#pragma once
#include "protocol/RecoveredBattleAttackPresentation.h"
#include "protocol/RecoveredBattleBootstrap.h"
#include "protocol/RecoveredPkRelativeView.h"
#include "protocol/RecoveredBattleVitals.h"
#include "protocol/RecoveredBattleVitalsBatch.h"
#include "game/Battle.h"
namespace god2 {
// CUSTOM-0086 two relative native views of ONE canonical two-player result.
// Owned raw templates and fresh batch/cycle bytes are mandatory inputs.
// Does not invent opaque fields, native permissions/turns or terminal packets.
struct RecoveredPkActionProjection {
    struct Templates {
        std::array<RecoveredBattleAttackPresentation::Record,2> animation;
        // Owner-qualified templates indexed by canonical participant0/14.
        // Raw MP is an owned side0 record; position is rebound per viewer.
        std::array<RecoveredBattleVitals::Record,2> hp,mp;
        // Viewer-local slot0 only; cycle/group meanings remain caller-qualified.
        std::array<RecoveredBattleVitalsBatch::Record,2> bulk;
    };
    using Replies=std::array<std::vector<std::uint8_t>,2>;
    static Replies logical(const BattleSnapshot& state,const BattleActionResult& result,const Templates& input,
                           std::optional<std::uint16_t> skill_key,bool emit_cycle_bulk=true){
        if(!state.id||!state.revision||(result.source!=0&&result.source!=14)||result.hits.size()!=1||
           !state.actors[0]||!state.actors[14]||!state.actors[0]->controller||!state.actors[14]->controller||
           state.actors[0]->controller==state.actors[14]->controller)
            throw std::invalid_argument("PK projection requires the common owned player pair and one hit");
        for(std::size_t i=0;i<state.actors.size();++i)
            if(state.actors[i].has_value()!=(i==0||i==14))throw std::invalid_argument("PK projection actor topology changed");
        const auto& hit=result.hits.front();
        if((hit.target!=0&&hit.target!=14)||hit.target==result.source||hit.hp_loss>hit.damage||
           hit.hp_loss>RecoveredBattleAttackPresentation::maximum_hp_loss)
            throw std::invalid_argument("PK actual hit cannot be represented by scalar signed16 presentation");
        for(std::size_t i=0;i<2;++i){
            const auto& actor=*state.actors[14*i];
            if(actor.position!=14*i||!actor.max_hp||actor.hp>actor.max_hp||actor.mp>actor.max_mp||
               input.hp[i].resource()!=RecoveredBattleVitals::Resource::Hp||
               input.mp[i].resource()!=RecoveredBattleVitals::Resource::Mp||
               !input.mp[i].native_actor_write_supported()||
               input.hp[i].maximum()!=actor.max_hp||input.mp[i].maximum()!=actor.max_mp||
               input.animation[i].skill_key()!=skill_key)
                throw std::invalid_argument("PK raw result templates do not match actor authority/action family");
        }
        Replies replies;
        for(std::uint8_t viewer=0;viewer<2;++viewer){
            auto& out=replies[viewer];
            const auto source=RecoveredPkRelativeView::position(result.source,viewer);
            const auto target=RecoveredPkRelativeView::position(hit.target,viewer);
            // Opponent MP has no actor-write branch. Actual cost is common;
            // only that actor's own viewer receives its86/1 absolute update.
            if(result.mp_cost&&source==0)
                append(out,vital(input.mp[viewer],0,state.actors[14*viewer]->mp));
            append(out,RecoveredBattleAttackPresentation::hit(input.animation[viewer],source,target,hit.hp_loss,
                state.actors[hit.target]->hp!=0));
            // BASIC522FB0 and ordinary skill524820 apply the signed83 HP at
            // their animation event. The special526890 skill branch uses the
            // outcome as a pose only and still requires its absolute HP86.
            if(input.animation[viewer].requires_absolute_hp_update())
                append(out,vital(input.hp[hit.target/14],target,state.actors[hit.target]->hp));
            if(emit_cycle_bulk){
                auto bulk=RecoveredBattleVitalsBatch::encode_logical(input.bulk[viewer]);
                if(std::all_of(bulk.begin()+1,bulk.begin()+5,[](auto b){return b==0xff;}))
                    throw std::invalid_argument("PK result bulk cannot use uninitialized counter");
                for(std::size_t slot=1;slot<14;++slot){
                    const auto values=*input.bulk[viewer].at(slot);
                    if(values.hp||values.mp)throw std::invalid_argument("PK raw bulk includes unowned friendly slots");
                }
                put(bulk,5,state.actors[14*viewer]->hp);put(bulk,9,state.actors[14*viewer]->mp);
                append(out,bulk);
            }
            // No86/5 grant or89 result appended: their authority must wait for
            // the genuine native receipt/terminal lifecycle, implemented later.
        }
        return replies;
    }
private:
    template<class Bytes>static void put(Bytes& bytes,std::size_t at,std::uint64_t value){
        const auto projected=RecoveredBattleBootstrap::native_hp_dword(value);
        for(unsigned i=0;i<4;++i)bytes[at+i]=static_cast<std::uint8_t>(projected>>(8*i));
    }
    static RecoveredBattleVitals::Bytes vital(const RecoveredBattleVitals::Record& prototype,
                                             std::uint8_t position,std::uint64_t current){
        if(current>prototype.maximum())throw std::invalid_argument("PK absolute resource exceeds owned maximum");
        auto bytes=RecoveredBattleVitals::encode_logical(prototype);bytes[2]=position;put(bytes,9,current);return bytes;
    }
    template<class Bytes>static void append(std::vector<std::uint8_t>& out,const Bytes& bytes){
        out.insert(out.end(),bytes.begin(),bytes.end());
    }
};
}
