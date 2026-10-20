#include "protocol/RecoveredPveRoomProjection.h"
#include "protocol/RecoveredTaiwanServerRecords.h"
#include <algorithm>
#include <set>

namespace god2 {
namespace {
using P=RecoveredPveRoomProjection;
using T=OwnedPveRoomTypes;
void need(bool value,const char* why){if(!value)throw P::ProfileRequired(why);}
bool recipient(const T::Member& m){return m.status!=T::MemberStatus::Returned&&m.status!=T::MemberStatus::Retired&&!m.disconnected&&!m.return_context;}
bool present(const T::Member& m){return m.status!=T::MemberStatus::Returned&&m.status!=T::MemberStatus::Retired&&m.status!=T::MemberStatus::Withdrawn;}
template<class Bytes>void put(Bytes& bytes,std::size_t at,std::uint64_t value){
    const auto n=RecoveredBattleBootstrap::native_hp_dword(value);
    for(unsigned i=0;i<4;++i)bytes[at+i]=static_cast<std::uint8_t>(n>>(8*i));
}
struct Writer {
    std::vector<T::Output>& output;std::uint64_t character;T::OutputKind kind;
    std::vector<std::uint8_t> bytes;
    void flush(){if(!bytes.empty()){output.push_back({character,kind,std::move(bytes)});bytes.clear();}}
    template<class Bytes>void append(const Bytes& record){
        need(!record.empty()&&record.size()<=RecoveredWorldFrame::max_logical_size,"profile_required: oversized native record");
        if(bytes.size()>RecoveredWorldFrame::max_logical_size-record.size())flush();
        bytes.insert(bytes.end(),record.begin(),record.end());
    }
};
struct Roster {
    std::array<bool,28> visible{};
    std::array<const T::Member*,14> owners{};
    std::array<bool,14> pets{};
};
Roster roster(const T::Snapshot& room){
    const auto& state=room.checkpoint.snapshot;
    need(room.id&&room.revision&&state.id==room.id&&state.revision,"profile_required: actual room snapshot missing");
    Roster result;
    for(const auto& [id,m]:room.members){
        const auto& input=m.input;
        need(id==input.identity.character&&id&&input.identity.actor_handle&&m.primary_position()<14,
             "profile_required: member slot/identity missing");
        const auto bind=[&](std::uint8_t slot,bool pet){
            need(slot<14&&!result.owners[slot],"profile_required: duplicate member slot");
            result.owners[slot]=&m;result.pets[slot]=pet;
            need(state.actors[slot]&&state.actors[slot]->position==slot&&state.actors[slot]->controller==id,
                 "profile_required: formation does not own its actual Battle actor");
            result.visible[slot]=present(m);
        };
        bind(m.primary_position(),false);
        if(input.pet)bind(*m.pet_position(),true);
    }
    for(std::uint8_t i=0;i<28;++i)if(const auto& a=state.actors[i]){
        need(a->position==i&&a->max_hp&&a->hp<=a->max_hp&&a->mp<=a->max_mp,
             "profile_required: invalid actual actor resources");
        if(i<14)need(result.owners[i]!=nullptr,"profile_required: unowned friendly actor");
        else{need(!a->controller,"profile_required: opponent is not encounter-owned AI");result.visible[i]=true;}
    }
    return result;
}
const P::ActorProfile& actor_profile(const P::RecipientProfile& p,std::uint8_t slot,const Roster& r,
                                   const BattleSnapshot& state){
    const auto found=p.actors.find(slot);need(found!=p.actors.end(),"profile_required: full native actor profile missing");
    const auto& a=found->second;const auto& actual=*state.actors[slot];
    need(a.hp.resource()==RecoveredBattleVitals::Resource::Hp&&a.hp.maximum()==actual.max_hp,
         "profile_required: HP template differs from current actor maximum");
    if(slot<14){
        need(a.mp&&a.mp->resource()==RecoveredBattleVitals::Resource::Mp&&a.mp->maximum()==actual.max_mp,
             "profile_required: friendly MP template differs from current actor maximum");
        const auto& owner=*r.owners[slot];const auto native=owner.input.identity.actor_handle;
        if(r.pets[slot])need(native<0x4000&&(a.identity.variant()&0x6000)==0x4000&&
            a.identity.identity_word()==static_cast<std::uint16_t>(native|0x4000),
            "profile_required: pet identity is not this actual member's secondary actor");
        else need((a.identity.variant()&0x6000)==0x2000&&a.identity.identity_word()==native&&a.appearance,
             "profile_required: player identity/appearance is not this actual native WORLD owner");
    }
    return a;
}
RecoveredBattleVitals::Bytes vital(const RecoveredBattleVitals::Record& prototype,std::uint8_t slot,std::uint64_t current){
    need(current<=prototype.maximum(),"profile_required: current vital exceeds qualified maximum");
    auto bytes=RecoveredBattleVitals::encode_logical(prototype);bytes[2]=slot;put(bytes,9,current);return bytes;
}
void emit_roster(Writer& w,const P::RecipientProfile& p,const Roster& r,const BattleSnapshot& state,
                 std::span<const std::uint8_t> slots){
    // Normal player1C consumes the already constructed86/4 renderer. Emit ALL
    // required player appearances first, not one after its own identity.
    for(const auto slot:slots){
        const auto& a=actor_profile(p,slot,r,state);
        if(a.appearance)w.append(RecoveredBattlePlayerAppearance::encode(
            RecoveredBattlePlayerAppearance::at_position(*a.appearance,slot)));
    }
    for(const auto slot:slots){
        const auto& a=actor_profile(p,slot,r,state);const auto& actual=*state.actors[slot];
        auto id=RecoveredBattleIdentity::encode_logical(a.identity);id[1]=slot;
        //515C90 normalizes flag bit0 to dead9. Newcomers see actual CURRENT
        // death state, not a replay of the encounter's initially alive packet.
        id[41]=static_cast<std::uint8_t>((id[41]&0xfe)|(actual.hp==0?1:0));
        w.append(id);w.append(vital(a.hp,slot,actual.hp));
        if(slot<14)w.append(vital(*a.mp,slot,actual.mp)); // No native side1 MP writer.
    }
}
void emit_bulk(Writer& w,const P::RecipientProfile& p,const Roster& r,const BattleSnapshot& state){
    need(p.bulk&&p.bulk->counter_bits()!=UINT32_MAX,"profile_required: actual non-sentinel bulk counter missing");
    auto bytes=RecoveredBattleVitalsBatch::encode_logical(*p.bulk);
    for(unsigned i=0;i<14;++i){
        const auto visible=r.visible[i]&&state.actors[i].has_value();
        std::uint64_t hp=visible?state.actors[i]->hp:0;std::uint32_t mp=visible?state.actors[i]->mp:0;
        // A fleeing member's combat tombstones are not saved death. Native88
        // also feeds its own HUD, so retain its exact pre-withdraw resources.
        if(const auto owner=r.owners[i];owner&&owner->input.identity.character==p.character&&owner->status==T::MemberStatus::Withdrawn){
            if(!r.pets[i]){hp=owner->input.resources.hp;mp=owner->input.resources.mp;}
            else if(const auto& pet=owner->input.pet->saved;pet.pet){const auto v=pet.pet->stats.vitals();hp=v.current_hp;mp=v.current_mp;}
            else{const auto v=owner->input.pet->saved.pet1->stats.vitals();hp=v.current_hp;mp=v.current_mp;}
        }
        put(bytes,5+8*i,hp);put(bytes,9+8*i,mp);
    }
    w.append(bytes);
}
void emit_grant(Writer& w,const P::RecipientProfile& p,const T::Member& m,const BattleSnapshot& state){
    need(p.grant&&(*p.grant)[0]==0x86&&(*p.grant)[1]==5,
         "profile_required: complete current native grant template missing");
    auto bytes=*p.grant;const auto primary=m.primary_position();
    need(primary<14&&state.actors[primary]&&(!m.primary_grant||state.actors[primary]->hp),
         "profile_required: primary grant names no living owned actor");
    need(!m.secondary_grant||(m.input.pet&&state.actors[*m.pet_position()]&&state.actors[*m.pet_position()]->hp),
         "profile_required: secondary grant names no living owned pet");
    bytes[3]=static_cast<std::uint8_t>((bytes[3]&0xfc)|(m.primary_grant?1:0)|(m.secondary_grant?2:0));
    bytes[4]=static_cast<std::uint8_t>((bytes[4]&0xf0)|primary);
    if(m.input.pet)bytes[4]=static_cast<std::uint8_t>((bytes[4]&0x0f)|(*m.pet_position()<<4));
    // Native517590 sets only the flagged A/B controls; absent bits DO NOT
    // clear an old client control/slot. Server grants remain the core's exact
    // current epoch. Native input cleanup/completion must come from the host;
    // neither mask0 nor this prepared/whole-Written output proves that cleanup.
    w.append(bytes);
}
void emit_action(Writer& w,const P::RecipientProfile& p,const T::Snapshot& room,const T::Change& change,const Roster& r){
    need(change.result.has_value()&&change.animation_group&&*change.animation_group<255,"profile_required: actual ordered action/group missing");
    const auto& result=*change.result;const auto& state=room.checkpoint.snapshot;
    need(result.source<28&&state.actors[result.source]&&p.attacks.size()==result.hits.size()&&!result.hits.empty(),
         "profile_required: actual action/template sequence differs");
    if(result.mp_cost&&result.source<14){const auto& a=actor_profile(p,result.source,r,state);
        w.append(vital(*a.mp,result.source,state.actors[result.source]->mp));}
    std::set<std::uint8_t> seen;
    for(std::size_t i=0;i<result.hits.size();++i){
        const auto& hit=result.hits[i];const auto& prototype=p.attacks[i];
        need(hit.target<28&&state.actors[hit.target]&&seen.insert(hit.target).second&&hit.hp_loss<=hit.damage&&
             prototype.skill_key()==p.action_skill,"profile_required: actual hit/family differs from raw template");
        const auto& target=*state.actors[hit.target];
        if(!prototype.requires_absolute_hp_update())
            RecoveredBattleAttackPresentation::require_deferred_hp_target(target.max_hp,target.hp);
        auto bytes=RecoveredBattleAttackPresentation::hit(prototype,result.source,hit.target,hit.hp_loss,target.hp!=0);
        bytes[3]=*change.animation_group;w.append(bytes);
        if(prototype.requires_absolute_hp_update())
            w.append(vital(actor_profile(p,hit.target,r,state).hp,hit.target,target.hp));
    }
    // The following88 is a true queued group boundary (5140C0/52AC20),
    // processed after renderer completion. Written alone proves no animation.
}
}
std::vector<OwnedPveRoomTypes::Output> RecoveredPveRoomProjection::prepare(
    const Types::Snapshot& room,const Types::Change& change,const Profiles& profiles){
    need(!change.cycle_progress_observed||change.kind==Types::Change::Kind::Grant,
         "profile_required: reported cycle progress belongs only to a new grant round");
    const auto r=roster(room);const auto& state=room.checkpoint.snapshot;
    const auto changed=room.members.find(change.character);
    if(change.kind==Types::Change::Kind::Admission||change.kind==Types::Change::Kind::Withdrawal||
       change.kind==Types::Change::Kind::Support||change.kind==Types::Change::Kind::RowSwap||change.kind==Types::Change::Kind::RowSwapComplete)
        need(changed!=room.members.end(),"profile_required: changed member missing");
    std::vector<Types::Output> out;
    for(const auto& [id,m]:room.members)if(recipient(m)){
        const auto at=profiles.find(id);need(at!=profiles.end()&&at->second.character==id,"profile_required: exact recipient profile missing");
        const auto& p=at->second;
        const bool entry=change.kind==Types::Change::Kind::Entry||(change.kind==Types::Change::Kind::Admission&&id==change.character);
        auto kind=entry?Types::OutputKind::Entry:Types::OutputKind::Roster;
        if(change.kind==Types::Change::Kind::Action)kind=Types::OutputKind::Action;
        if(change.kind==Types::Change::Kind::Grant)kind=Types::OutputKind::Grant;
        if(change.kind==Types::Change::Kind::Terminal)kind=Types::OutputKind::Terminal;
        Writer w{out,id,kind,{}};
        const auto grant=[&]{if(std::find(change.suppress_grants.begin(),change.suppress_grants.end(),id)==change.suppress_grants.end())emit_grant(w,p,m,state);};
        if(entry||change.kind==Types::Change::Kind::Admission){
            std::vector<std::uint8_t> slots;
            if(entry){
                need(p.entry&&p.entry->context_a==m.input.command_context,"profile_required: original entry command context missing");
                w.append(RecoveredBattleEntry::encode_logical(*p.entry));
                for(std::uint8_t s=0;s<28;++s)if(r.visible[s])slots.push_back(s);
            }else{
                const auto& joined=changed->second;slots.push_back(joined.primary_position());
                if(joined.input.pet)slots.push_back(*joined.pet_position());
            }
            emit_roster(w,p,r,state,slots);
            if(entry){
                //5112C0 clears B+488. A newcomer to an already enabled SOS
                // room therefore needs a real matching08 profile as well;
                // incumbent actors/flags must not be reset to accomplish it.
                if(room.support_enabled){
                    need(p.support&&p.support->word9_operand()!=0&&
                        (p.support->source()==m.primary_position()||
                         (m.input.pet&&p.support->source()==*m.pet_position()))&&
                        state.actors[p.support->source()]&&state.actors[p.support->source()]->hp,
                        "profile_required: enabled room needs entrant's actual support profile");
                    auto control=RecoveredBattleAction08Control::encode(*p.support);
                    control[3]=change.animation_group.value_or(0);w.append(control);
                }
                emit_bulk(w,p,r,state);grant();
            }else emit_bulk(w,p,r,state); // new native progress edge for incumbents; no roster reset
        }else if(change.kind==Types::Change::Kind::Action||change.kind==Types::Change::Kind::Terminal){
            if(change.result)emit_action(w,p,room,change,r);
            else need(change.kind==Types::Change::Kind::Terminal,"profile_required: action result missing");
            // Native5140C0 queues83 of one label until88/different label.
            // The88 is applied only AFTER that animation group completes.
            // Its fixed profile counter is not the manager's actor count.
            if(change.result)emit_bulk(w,p,r,state);
            if(change.kind==Types::Change::Kind::Terminal){
                need(p.terminal.has_value(),"profile_required: actual terminal89 profile missing");
                w.append(RecoveredBattleExperience::encode_logical(*p.terminal));
            }else grant();
        }else if(change.kind==Types::Change::Kind::Pass){
            // Actual action2/target-gone pass has no83. Reset the native sent0B
            // latch with a fixed-counter88 boundary, never on grant refresh.
            emit_bulk(w,p,r,state);grant();
        }else if(change.kind==Types::Change::Kind::Grant){
            // CUSTOM-0161 host observes untrusted original0B only after all
            // server grants are consumed and all room outputs Written. This
            // explicit cycle gate is not an animation ACK or a turn nonce.
            if(change.cycle_progress_observed)emit_bulk(w,p,r,state);
            grant();
        }else if(change.kind==Types::Change::Kind::Support){
            const auto& input=changed->second.input;
            need(change.actor_position&&(*change.actor_position==changed->second.primary_position()||
                 (input.pet&&*change.actor_position==*changed->second.pet_position()))&&
                 state.actors[*change.actor_position]&&state.actors[*change.actor_position]->hp&&
                 p.support&&p.support->source()==*change.actor_position&&
                 (p.support->word9_operand()!=0)==room.support_enabled,
                 "profile_required: actual support state/template mismatch");
            need(change.animation_group&&*change.animation_group<255,"profile_required: support animation label missing");
            auto control=RecoveredBattleAction08Control::encode(*p.support);control[3]=*change.animation_group;w.append(control);
            emit_bulk(w,p,r,state);
            //518E50 common cleanup consumes the selected A/B control for08.
            // CUSTOM-0161 consumes that same actual role grant; advertise any
            // remaining owned role without treating absent bits as a clear.
            grant();
        }else if(change.kind==Types::Change::Kind::RowSwap){
            need(change.formation_before&&change.actor_position&&change.animation_group&&*change.animation_group<255&&
                room.pending_swap&&room.pending_swap->identity==changed->second.input.identity&&
                room.pending_swap->before==*change.formation_before&&p.row_swap,
                "profile_required: exact pending native row swap/source missing");
            const auto from=change.formation_before->primary,to=changed->second.primary_position();
            need(from!=to&&p.row_swap->source()==*change.actor_position&&p.row_swap->from()==from&&p.row_swap->to()==to&&
                p.row_swap->success_operand()!=0,"profile_required: row swap is not the authorized original pair permutation");
            auto bytes=RecoveredBattleRowSwapResult::encode(*p.row_swap);bytes[3]=*change.animation_group;w.append(bytes);
            emit_bulk(w,p,r,state); // actual native group boundary, not a Written/renderer ACK
        }else if(change.kind==Types::Change::Kind::RowSwapComplete){
            need(!room.pending_swap&&change.formation_before,"profile_required: row swap completion has no cleared exact edge");
            grant();
        }else if(change.kind==Types::Change::Kind::Withdrawal){
            std::set<std::uint8_t> expected{changed->second.primary_position()};
            if(changed->second.input.pet)expected.insert(*changed->second.pet_position());
            for(const auto& control:p.withdrawal){
                const auto records=RecoveredTaiwanServerRecords::read(control);
                need(records&&records->size()==1&&control[0]==0x83&&control[1]==6&&control[12]==2&&
                     expected.erase(control[2])==1,"profile_required: actual flee-removal template missing/mismatched");
                need(change.animation_group&&*change.animation_group<255,"profile_required: withdrawal animation label missing");
                auto bytes=control;bytes[3]=*change.animation_group;w.append(bytes);
            }
            need(expected.empty(),"profile_required: withdrawal omits primary or secondary actor");
            emit_bulk(w,p,r,state);
        }else throw ProfileRequired("profile_required: unsupported room change");
        w.flush();
    }
    // Last-member disconnection still persists withdrawal/save truth even
    // when no live recipient remains. No synthetic empty output is queued.
    return out;
}
}
