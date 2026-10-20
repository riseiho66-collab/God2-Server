#include "game/OwnedBattleFormation.h"
#include "protocol/RecoveredPveRoomProjection.h"
#include "protocol/RecoveredTaiwanServerRecords.h"
#include "protocol/RecoveredWorldRecords.h"
#include <iostream>
#include <set>

namespace {
using namespace god2;
using F=OwnedBattleFormation;
using P=RecoveredPveRoomProjection;
using T=OwnedPveRoomTypes;
void require(bool value,const char* why){if(!value)throw std::runtime_error(why);}
template<class Fn>void refused(Fn fn){bool no=false;try{fn();}catch(const std::invalid_argument&){no=true;}require(no,"Expected refusal");}
RecoveredBattleVitals::Record vital(std::uint8_t slot,bool mp,std::uint32_t max){
    RecoveredBattleVitals::Bytes b{};b[0]=0x86;b[1]=mp?1:0;b[2]=slot;
    for(unsigned i=0;i<4;++i)b[5+i]=static_cast<std::uint8_t>(max>>(8*i));
    return *RecoveredBattleVitals::parse_logical(b);
}
P::ActorProfile profile(std::uint8_t slot,std::uint16_t owner,bool pet,bool enemy=false){
    // Explicit CUSTOM_TEST_NOT_NATIVE profiles; no renderer/resource entitlement
    // or native opaque values are inferred from these isolated source fixtures.
    RecoveredBattleIdentity::Bytes id{};id[0]=0x1c;id[1]=slot;id[2]=1;
    const auto native=static_cast<std::uint16_t>(pet?(owner|0x4000):owner);
    id[3]=static_cast<std::uint8_t>(native);id[4]=static_cast<std::uint8_t>(native>>8);
    id[6]=enemy?4:(pet?0x40:0x20);
    id[9]='T';
    std::optional<RecoveredBattlePlayerAppearance::Record> appearance;
    if(!pet&&!enemy){RecoveredBattlePlayerAppearance::Bytes b{};b[0]=0x86;b[1]=4;b[2]=slot;b[3]=1;
        appearance=RecoveredBattlePlayerAppearance::parse(b);}
    return {*RecoveredBattleIdentity::parse_logical(id),appearance,vital(slot,false,100),
        enemy?std::optional<RecoveredBattleVitals::Record>{}:std::optional{vital(slot,true,50)}};
}
std::vector<RecoveredTaiwanServerRecords::Record> records(const std::vector<T::Output>& out,std::uint64_t who){
    std::vector<RecoveredTaiwanServerRecords::Record> result;
    for(const auto& o:out)if(o.character==who){
        require(!o.logical.empty()&&o.logical.size()<=RecoveredWorldFrame::max_logical_size,"Output is not native frame bounded");
        const auto read=RecoveredTaiwanServerRecords::read(o.logical);require(read.has_value(),"Output records invalid");
        // Record views borrow Output, which remains owned by each caller.
        result.insert(result.end(),read->begin(),read->end());
    }
    return result;
}
struct Fixture {
    T::Snapshot room;
    P::Profiles profiles;
    Fixture(){
        room.id=room.checkpoint.snapshot.id=161;room.revision=room.checkpoint.snapshot.revision=4;
        room.checkpoint.snapshot.state=BattleState::Active;
        T::Member old{},joined{};
        old.input.identity={1,1,11,1,1,1,11};old.input.primary_slot=6;old.input.pet=T::PetInput{};old.input.pet->actor_slot=1;
        old.input.command_context=101;old.status=T::MemberStatus::Active;old.secondary_grant=true;
        joined.input.identity={2,2,22,1,1,1,22};joined.input.primary_slot=0;joined.input.pet=T::PetInput{};joined.input.pet->actor_slot=5;
        joined.input.command_context=202;joined.status=T::MemberStatus::Entering;
        room.members.emplace(11,old);room.members.emplace(22,joined);
        for(const auto [s,c,h]:std::array<std::array<unsigned,3>,5>{{{6,11,0},{1,11,20},{0,22,40},{5,22,30},{14,0,7}}})
            room.checkpoint.snapshot.actors[s]=BattleActor{static_cast<std::uint8_t>(s),c,h,100,9,50,1,1,1,1};
        RecoveredBattleVitalsBatch::Bytes bulk{};bulk[0]=0x88;bulk[1]=37; // Explicit fixture counter, not a room formula.
        for(const auto id:{11u,22u}){
            P::RecipientProfile p{};p.character=id;p.entry=RecoveredBattleEntry::Record{id==11?101u:202u,0x12345678};
            p.actors.emplace(6,profile(6,11,false));p.actors.emplace(1,profile(1,11,true));
            p.actors.emplace(0,profile(0,22,false));p.actors.emplace(5,profile(5,22,true));p.actors.emplace(14,profile(14,1,false,true));
            p.bulk=RecoveredBattleVitalsBatch::parse_logical(bulk);
            std::array<std::uint8_t,17> grant{};grant[0]=0x86;grant[1]=5;grant[5]=0x71;grant[16]=0xa5;p.grant=grant;
            profiles.emplace(id,std::move(p));
        }
    }
};
void formation(){
    // These pairs are EXPLICIT TEST configuration, not a claimed original pair rule.
    F::Topology topology{"CUSTOM_TEST_NOT_NATIVE:configured-pairs",9,{{1,6},{0,5}}};
    const F::Owner a{1,1,11,11},b{2,2,22,22};
    const std::array members{F::Member{a,0,1,true},F::Member{b,1,0,false}};
    const auto initial=F::make(topology,members,7);
    require(initial.position(a,F::Role::Primary)==6&&initial.position(a,F::Role::Pet)==1,
        "Saved explicit row did not bind both actual role slots");
    require(initial.reserved_by(5)==b&&!initial.actors()[5],"Absent pet reservation was promoted into an actor");
    const auto swapped=initial.swapped_pair(a);
    require(swapped.revision()==8&&swapped.position(a,F::Role::Primary)==1&&swapped.position(a,F::Role::Pet)==6&&
        initial.position(a,F::Role::Primary)==6,"Staged pair swap changed old authority or lost role identity");
    refused([&]{(void)initial.swapped_pair(b);});
    refused([&]{(void)initial.joined(F::Member{{3,3,33,33},0,0,false});});
    refused([&]{auto bad=topology;bad.lanes[1]={6,8};(void)F::make(bad,members,1);});
    refused([&]{(void)F::make(F::Topology{},members,1);});
    const auto departed=initial.departed(a);
    require(!departed.reserved_by(1)&&!departed.reserved_by(6)&&initial.reserved_by(1)==a,
        "Departure failed to retire exact reservation or modified old snapshot");
}
void flee(){
    for(const auto actor:{0u,13u,14u})for(const auto secondary:{0u,1u})
        for(const auto tail:{0u,1u,0x7fffffffu,0x80000000u,0xffffffffu}){
            RecoveredBattleFleeCommand::Bytes b{};b[0]=0x35;b[1]=static_cast<std::uint8_t>(actor);b[2]=6;
            b[3]=static_cast<std::uint8_t>(secondary);b[4]=0xa7;
            const auto mask=1u<<(actor%14);const auto at=5+2*(actor/14);
            b[at]=static_cast<std::uint8_t>(mask);b[at+1]=static_cast<std::uint8_t>(mask>>8);
            for(unsigned i=0;i<4;++i){b[9+i]=static_cast<std::uint8_t>(0x12345678u>>(8*i));b[13+i]=static_cast<std::uint8_t>(tail>>(8*i));}
            const auto request=RecoveredBattleFleeCommand::decode(b);
            require(request&&request->actor_position()==actor&&request->side_flag()==secondary&&
                request->opaque4()==0xa7&&request->context()==0x12345678&&request->unwritten_tail_bits()==tail&&
                RecoveredBattleFleeCommand::encode(*request)==b,"Flee parser normalized uninitialized producer bits");
            std::vector<std::uint8_t> batch{0x30,0};batch.insert(batch.end(),b.begin(),b.end());
            const auto parsed=RecoveredWorldRecords::decode(batch);
            require(parsed&&parsed->size()==2&&std::holds_alternative<RecoveredBattleFleeCommand::Request>((*parsed)[1]),
                "Actual world grammar sent native flee through action2/skill fallback");
            batch.push_back(0);require(!RecoveredWorldRecords::decode(batch),"Invalid suffix retained a partial flee batch");
            for(const auto index:{1u,3u,5u,7u}){
                auto invalid=b;
                if(index==1)invalid[index]=15;
                else if(index==3)invalid[index]=2;
                else invalid[index]^=0x40;
                require(!RecoveredBattleFleeCommand::decode(invalid)&&!RecoveredWorldRecords::decode(invalid),
                    "Invalid native flee actor/side/selfmask fell through another grammar");
            }
            require(!RecoveredBattleFleeCommand::decode(std::span<const std::uint8_t>(b).first(16)),"Flee accepted truncation");
        }
}
void projection(){
    Fixture f;
    const auto out=P::prepare(f.room,{T::Change::Kind::Admission,22,{}},f.profiles);
    const auto old=records(out,11),joined=records(out,22);
    require(!old.empty()&&!joined.empty()&&joined.front().opcode==0x82,"New entrant lacks actual initial context");
    std::set<std::uint8_t> old_ids,new_ids;
    bool saw_first_id=false,dead=false,current_enemy=false;
    for(const auto& r:old){
        require(r.opcode!=0x82&&r.opcode!=0x88&&!(r.opcode==0x86&&r.bytes[1]==5),
            "Admission reset incumbent entry/counter/grant");
        if(r.opcode==0x1c)old_ids.insert(r.bytes[1]);
    }
    for(const auto& r:joined){
        if(r.opcode==0x1c){saw_first_id=true;new_ids.insert(r.bytes[1]);if(r.bytes[1]==6)dead=(r.bytes[41]&1)!=0;}
        if(r.opcode==0x86&&r.bytes[1]==4)require(!saw_first_id,"Player renderer appeared after first identity");
        if(r.opcode==0x86&&r.bytes[1]==0&&r.bytes[2]==14)
            current_enemy=RecoveredBattleVitals::parse_logical(r.bytes)->current()==7;
    }
    require(old_ids==std::set<std::uint8_t>{0,5}&&new_ids==std::set<std::uint8_t>{0,1,5,6,14}&&dead&&current_enemy,
        "Admission replayed initial actors/HP or omitted current death state");
    auto missing=f.profiles;missing.at(22).actors.erase(14);
    refused([&]{(void)P::prepare(f.room,{T::Change::Kind::Admission,22,{}},missing);});
    const auto full=P::prepare(f.room,{T::Change::Kind::Entry,0,{}},f.profiles);
    const auto first=records(full,11);
    const auto grant=std::find_if(first.begin(),first.end(),[](const auto& r){return r.opcode==0x86&&r.bytes[1]==5;});
    require(grant!=first.end()&&(grant->bytes[3]&3)==2&&grant->bytes[4]==0x16&&
        grant->bytes[5]==0x71&&grant->bytes[16]==0xa5,"Grant lost actual nonzero role slots or changed opaque source bytes");
    RecoveredBattleAttackPresentation::Bytes attack{};attack[0]=0x83;attack[1]=1;attack[3]=9;attack[7]=1;attack[12]=28;
    for(auto& [id,p]:f.profiles){(void)id;p.attacks={*RecoveredBattleAttackPresentation::parse(attack)};}
    f.room.members.at(11).secondary_grant=false;
    const BattleActionResult hit{1,2,{{14,3,3,false}}};
    const auto actions=P::prepare(f.room,{T::Change::Kind::Action,11,hit},f.profiles);
    bool actual_hit=false,actual_mp=false;
    for(const auto& r:records(actions,11)){
        if(r.opcode==0x83)actual_hit=r.bytes[2]==1&&r.bytes[3]==9&&r.bytes[7]==1&&r.bytes[9]==0xfd&&r.bytes[10]==0xff;
        if(r.opcode==0x86&&r.bytes[1]==1)actual_mp=r.bytes[2]==1&&RecoveredBattleVitals::parse_logical(r.bytes)->current()==9;
        require(r.opcode!=0x88&&!(r.opcode==0x86&&r.bytes[1]==0&&r.bytes[2]==14),"Basic deferred HP was eagerly applied twice");
    }
    require(actual_hit&&actual_mp,"Action lost actual secondary source/ordered hit/MP or raw group");
    // AI damage to a friendly actor must not receive finalHP88 before its
    // deferred83 event. It writes the same native DE8 HP field twice.
    auto ai_profiles=f.profiles;auto ai_attack=attack;ai_attack[2]=14;ai_attack[5]=2;ai_attack[7]=0;
    for(auto& [id,p]:ai_profiles){(void)id;p.attacks={*RecoveredBattleAttackPresentation::parse(ai_attack)};p.bulk.reset();}
    f.room.checkpoint.snapshot.actors[1]->hp=17;
    const auto ai_out=P::prepare(f.room,{T::Change::Kind::Action,0,BattleActionResult{14,0,{{1,3,3,false}}}},ai_profiles);
    bool ai_deferred=false;
    for(const auto& r:records(ai_out,11)){
        require(r.opcode!=0x88&&!(r.opcode==0x86&&r.bytes[1]==0&&r.bytes[2]==1),
            "AI friendly hit eagerly reset HP before its deferred native delta");
        if(r.opcode==0x83)ai_deferred=r.bytes[2]==14&&r.bytes[5]==2&&r.bytes[9]==0xfd&&r.bytes[10]==0xff;
    }
    require(ai_deferred,"AI action lost its actual friendly target deferred hit");
    const auto grant_only=P::prepare(f.room,{T::Change::Kind::Grant,0,{}},ai_profiles);
    for(const auto& r:records(grant_only,11))require(r.opcode==0x86&&r.bytes[1]==5,
        "Next grant improperly treated network Written as safe88 cycle completion");
    const T::Change progressed{T::Change::Kind::Grant,0,{},{},true};
    refused([&]{(void)P::prepare(f.room,progressed,ai_profiles);}); // True gate still needs full counter/profile.
    const auto qualified_cycle=P::prepare(f.room,progressed,f.profiles);
    const auto cycle_records=records(qualified_cycle,11);
    require(cycle_records.size()==2&&cycle_records[0].opcode==0x88&&
        RecoveredBattleVitalsBatch::parse_logical(cycle_records[0].bytes)->counter_bits()==37&&
        cycle_records[1].opcode==0x86&&cycle_records[1].bytes[1]==5,
        "Explicit reported-cycle grant omitted the complete supplied native counter snapshot");
    refused([&]{(void)P::prepare(f.room,{T::Change::Kind::Action,0,BattleActionResult{14,0,{{1,3,3,false}}},{},true},ai_profiles);});
    f.room.checkpoint.snapshot.state=BattleState::Finished;f.room.checkpoint.snapshot.victorious_side=0;
    f.room.checkpoint.snapshot.actors[14]->hp=0;
    const BattleActionResult killed{1,0,{{14,10,10,false}}};
    refused([&]{(void)P::prepare(f.room,{T::Change::Kind::Terminal,11,killed},f.profiles);});
    RecoveredBattleExperience::LogicalRecord terminal{};terminal[0]=0x89;terminal[49]=4;
    for(auto& [id,p]:f.profiles){(void)id;p.terminal=RecoveredBattleExperience::parse_logical(terminal);}
    const auto finished=P::prepare(f.room,{T::Change::Kind::Terminal,11,killed},f.profiles);
    for(const auto id:{11u,22u}){const auto r=records(finished,id);require(!r.empty()&&r.back().opcode==0x89,
        "Terminal omitted the complete supplied native result profile");
        for(const auto& record:r)require(record.opcode!=0x88,"Terminal eagerly reset deferred HP/playback with88");}
    f.room.checkpoint.snapshot.state=BattleState::Active;f.room.checkpoint.snapshot.victorious_side.reset();
    f.room.checkpoint.snapshot.actors[14]->hp=7;
    f.room.support_enabled=true;
    RecoveredBattleAction08Control::Bytes support{};support[0]=0x83;support[1]=8;support[2]=1;support[5]=2;support[9]=1;
    for(auto& [id,p]:f.profiles){(void)id;p.support=RecoveredBattleAction08Control::parse(support);}
    const auto secondary=P::prepare(f.room,{T::Change::Kind::Support,11,{},std::uint8_t{1}},f.profiles);
    const auto support_records=records(secondary,11);
    require(support_records.size()==2&&support_records[0].opcode==0x83&&
        support_records[0].bytes[1]==8&&support_records[0].bytes[2]==1&&
        support_records[1].opcode==0x86&&support_records[1].bytes[1]==5&&
        (support_records[1].bytes[3]&3)==0&&support_records[1].bytes[4]==0x16,
        "Secondary support lost its exact source or manufactured a consumed grant");
    // Primary08 consumes A first; native B remains available for this member's pet.
    f.room.checkpoint.snapshot.actors[6]->hp=40;f.room.members.at(11).secondary_grant=true;
    auto primary_support=f.profiles;
    auto primary_template=support;primary_template[2]=6;primary_template[5]=0x40;
    for(auto& [id,p]:primary_support){(void)id;p.support=RecoveredBattleAction08Control::parse(primary_template);}
    const auto primary_out=P::prepare(f.room,{T::Change::Kind::Support,11,{},std::uint8_t{6}},primary_support);
    const auto primary_records=records(primary_out,11);
    require(primary_records.size()==2&&primary_records[0].bytes[2]==6&&
        (primary_records[1].bytes[3]&3)==2&&primary_records[1].bytes[4]==0x16,
        "Primary support stranded the remaining owned pet grant");
    f.room.members.at(11).secondary_grant=false;
    auto dead_support=f.profiles;
    RecoveredBattleAction08Control::Bytes dead_template=support;dead_template[2]=6;
    dead_template[5]=0x40;
    dead_support.at(11).support=RecoveredBattleAction08Control::parse(dead_template);
    f.room.checkpoint.snapshot.actors[6]->hp=0;f.room.members.at(11).primary_grant=false;
    refused([&]{(void)P::prepare(f.room,{T::Change::Kind::Entry,0,{}},dead_support);});
    refused([&]{(void)P::prepare(f.room,{T::Change::Kind::Support,11,{},std::uint8_t{5}},f.profiles);});
    for(auto& [id,m]:f.room.members){(void)id;m.status=T::MemberStatus::Retired;m.disconnected=true;}
    require(P::prepare(f.room,{T::Change::Kind::Withdrawal,11,{}},{}).empty(),
        "Last disconnected member must save/retire without inventing a recipient output");
}
}
int main(){try{formation();flee();projection();return 0;}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
