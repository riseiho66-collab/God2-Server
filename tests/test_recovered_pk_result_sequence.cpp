#include "protocol/RecoveredPkActionProjection.h"
#include "protocol/RecoveredTaiwanPkTerminalNotification.h"
#include <iostream>
#include <stdexcept>
#include <vector>

namespace {
using namespace god2;
using Grammar=RecoveredTaiwanPkTerminalNotification;
using Bytes=std::vector<std::uint8_t>;
void require(bool value,const char* message){if(!value)throw std::runtime_error(message);}
template<class F>void rejected(F action,const char* message){
    bool threw=false;try{action();}catch(const std::invalid_argument&){threw=true;}require(threw,message);
}
template<class Range>void append(Bytes& out,const Range& bytes){out.insert(out.end(),bytes.begin(),bytes.end());}
RecoveredBattleVitals::Record vital(bool mp,std::uint8_t position,std::uint32_t current=82,
        std::uint32_t maximum=120){
    RecoveredBattleVitals::Bytes bytes{};bytes[0]=0x86;bytes[1]=mp?1:0;bytes[2]=position;
    for(unsigned i=0;i<4;++i){bytes[5+i]=static_cast<std::uint8_t>(maximum>>(8*i));
        bytes[9+i]=static_cast<std::uint8_t>(current>>(8*i));}
    return *RecoveredBattleVitals::parse_logical(bytes);
}
RecoveredBattleAttackPresentation::Record attack(std::uint8_t source,
        std::optional<std::uint16_t> key={}){
    RecoveredBattleAttackPresentation::Bytes bytes{};bytes[0]=0x83;bytes[1]=key?3:1;bytes[2]=source;
    bytes[5+2*(1-source/14)]=1;bytes[9]=0xee;bytes[10]=0xff;
    if(key){bytes[11]=static_cast<std::uint8_t>(*key);bytes[12]=static_cast<std::uint8_t>(*key>>8);bytes[14]=28;}
    else bytes[12]=28;
    return *RecoveredBattleAttackPresentation::parse(bytes);
}
RecoveredBattleVitalsBatch::Record bulk(){
    RecoveredBattleVitalsBatch::Bytes bytes{};bytes[0]=0x88;bytes[1]=1;
    return *RecoveredBattleVitalsBatch::parse_logical(bytes);
}
Bytes group(std::uint8_t source,bool absolute_hp,std::optional<std::uint16_t> key={},bool own_mp=false){
    Bytes bytes;
    if(own_mp)append(bytes,RecoveredBattleVitals::encode_logical(vital(true,0,20)));
    append(bytes,RecoveredBattleAttackPresentation::encode(attack(source,key)));
    if(absolute_hp)append(bytes,RecoveredBattleVitals::encode_logical(vital(false,static_cast<std::uint8_t>(14-source))));
    return bytes;
}
Bytes output(Bytes bytes,bool terminal=false){
    append(bytes,RecoveredBattleVitalsBatch::encode_logical(bulk()));
    if(terminal){RecoveredBattleExperience::LogicalRecord tail{};tail[0]=0x89;tail[49]=4;append(bytes,tail);}
    return bytes;
}
void grammar_checks(){
    // Explicit native dispatch classes, independent of the modulo expression
    // used by the production classifier. Check every admitted kind0/1 ID.
    constexpr std::array<std::uint8_t,8> physical_special{96,97,98,99,100,101,102,103};
    constexpr std::array<std::uint8_t,11> magical_special{3,11,19,27,35,43,89,90,91,92,93};
    require(!attack(0).requires_absolute_hp_update(),"Basic classified as pose-only");
    for(unsigned kind=0;kind<2;++kind)for(unsigned id=1;id<256;++id){
        const bool expected=kind==0?
            std::find(physical_special.begin(),physical_special.end(),id)!=physical_special.end():
            std::find(magical_special.begin(),magical_special.end(),id)!=magical_special.end();
        const auto key=static_cast<std::uint16_t>((kind<<8)|id);
        require(attack(0,key).requires_absolute_hp_update()==expected,"Native pose-only dispatch class boundary changed");
    }
    const auto fresh=output(group(0,false));
    require(fresh.size()==15+121&&Grammar::matches_output_sequence(fresh),"Single basic must defer HP to83");
    require(Grammar::matches_retained_output_sequence(fresh),"Retained reader rejected current output");
    require(!Grammar::matches_result_sequence(fresh),"Terminal-only matcher accepted missing89");
    const auto old=output(group(0,true));const auto old_copy=old;
    require(old.size()==32+121&&!Grammar::matches_output_sequence(old)&&
        Grammar::matches_retained_output_sequence(old)&&old==old_copy,"Old saved basic requires explicit immutable read compatibility");
    const auto terminal=output(group(14,false),true);
    require(terminal.size()==15+121+57&&Grammar::matches_result_sequence(terminal)&&
        Grammar::matches_retained_result_sequence(terminal),"Deferred terminal grammar rejected");
    const auto old_terminal=output(group(14,true),true);
    require(!Grammar::matches_result_sequence(old_terminal)&&Grammar::matches_retained_result_sequence(old_terminal),
        "Fresh terminal accepted eager legacy basic");
    for(const bool first_old:{false,true}){
        auto hybrid=group(0,first_old);append(hybrid,group(14,!first_old));hybrid=output(hybrid);
        require(!Grammar::matches_output_sequence(hybrid)&&!Grammar::matches_retained_output_sequence(hybrid),
            "Hybrid legacy/current basic groups accepted");
    }
    auto both_old=group(0,true);append(both_old,group(14,true));both_old=output(both_old);
    require(!Grammar::matches_output_sequence(both_old)&&Grammar::matches_retained_output_sequence(both_old),
        "Uniform old two-group output lost read compatibility");
    for(const std::uint16_t special:{std::uint16_t{96},std::uint16_t{103},std::uint16_t{0x103},std::uint16_t{0x159}}){
        auto mixed=group(0,true,special,true);append(mixed,group(14,false));mixed=output(mixed,true);
        require(Grammar::matches_result_sequence(mixed),"Legitimate pose-only skill and deferred basic mixed policy rejected");
        require(!Grammar::matches_output_sequence(output(group(0,false,special))),"Pose-only skill missing absoluteHP accepted");
    }
    for(const std::uint16_t ordinary:{std::uint16_t{1},std::uint16_t{95},std::uint16_t{104},std::uint16_t{0x12e},std::uint16_t{0x15e}})
        require(Grammar::matches_output_sequence(output(group(0,false,ordinary,true))),"Ordinary skill must defer HP and retain ownedMP");
    auto peer_first=group(14,false);append(peer_first,group(0,false,{},true));
    require(Grammar::matches_output_sequence(output(peer_first)),"Next actor ownedMP mistaken for prior actor HP");
    require(!Grammar::matches_output_sequence(output(group(14,false,{},true))),"Opponent-ownedMP accepted");
    auto wrong_mp=output(group(0,false,{},true));wrong_mp[2]=1;
    require(!Grammar::matches_retained_output_sequence(wrong_mp),"Wrong ownedMP position accepted");
    auto wrong_target=output(group(0,false));wrong_target[7]=2;
    require(!Grammar::matches_retained_output_sequence(wrong_target),"Non-primary target accepted");
    auto duplicate=group(0,false);append(duplicate,group(0,false));
    require(!Grammar::matches_retained_output_sequence(output(duplicate)),"Repeated source group accepted");
    auto third=group(0,false);append(third,group(14,false));append(third,group(0,false));
    require(!Grammar::matches_retained_output_sequence(output(third)),"Third group accepted");
    auto bad_terminal=terminal;bad_terminal.back()=1;
    require(!Grammar::matches_retained_output_sequence(bad_terminal),"Noncanonical terminal tail accepted");
    bad_terminal=terminal;append(bad_terminal,RecoveredBattleAttackPresentation::encode(attack(0)));
    require(!Grammar::matches_retained_output_sequence(bad_terminal),"Bytes after terminal tail accepted");
    auto bad_prefix=terminal;bad_prefix.insert(bad_prefix.begin(),{0x88,0,0,0,0});
    require(!Grammar::matches_retained_output_sequence(bad_prefix),"Bad prefix before terminal accepted");
    require(!Grammar::matches_retained_output_sequence(output({})),"Bulk-only output accepted");
}
void projection_checks(){
    BattleSnapshot state{1,2,BattleState::Active,{}};
    state.actors[0]=BattleActor{0,1,100,120,20,120,10,10,10,10};
    state.actors[14]=BattleActor{14,2,82,120,20,120,10,10,10,10};
    const BattleActionResult result{0,0,{{14,18,18,false}}};
    for(const auto key:{std::optional<std::uint16_t>{},std::optional<std::uint16_t>{1},std::optional<std::uint16_t>{96}}){
        RecoveredPkActionProjection::Templates input{{attack(0,key),attack(14,key)},
            {vital(false,0,100),vital(false,14)}, {vital(true,0,20),vital(true,0,20)}, {bulk(),bulk()}};
        const auto replies=RecoveredPkActionProjection::logical(state,result,input,key);
        for(std::uint8_t viewer=0;viewer<2;++viewer){
            const auto& bytes=replies[viewer];const bool absolute=input.animation[viewer].requires_absolute_hp_update();
            require(bytes.size()==15+121+(absolute?17:0)&&Grammar::matches_output_sequence(bytes),
                "Two-viewer projection disagrees with actual HP consumer policy");
            const auto records=*RecoveredTaiwanServerRecords::read(bytes);
            const auto presented=RecoveredBattleAttackPresentation::parse(records.front().bytes);
            require(presented&&presented->source()==14*viewer&&records.back().opcode==0x88,
                "Relative source or final bulk changed");
            require(records.front().bytes[9]==0xee&&records.front().bytes[10]==0xff,
                "Projection changed exact signed HP loss");
        }
        auto cost=result;cost.mp_cost=1;
        const auto charged=RecoveredPkActionProjection::logical(state,cost,input,key);
        require(charged[0].size()==replies[0].size()+17&&charged[1].size()==replies[1].size()&&
            Grammar::matches_output_sequence(charged[0])&&Grammar::matches_output_sequence(charged[1]),
            "OwnedMP cost projection changed");
        auto invalid=state;invalid.actors[14]->hp=121;
        rejected([&]{RecoveredPkActionProjection::logical(invalid,result,input,key,false);},
            "Deferred projection lost HP above maximum guard");
        invalid=state;invalid.actors[14]->max_hp=std::uint64_t{1}<<32;
        rejected([&]{RecoveredPkActionProjection::logical(invalid,result,input,key,false);},
            "Deferred projection accepted maximum outside native DWORD template");
        auto lethal=state;lethal.actors[14]->hp=0;lethal.state=BattleState::Finished;
        const auto death=RecoveredPkActionProjection::logical(lethal,result,input,key);
        require(death[0][key?14:12]==0&&Grammar::matches_output_sequence(death[0]),
            "Consumer HP policy lost lethal outcome");
    }
}
void signed_endpoint_checks(){
    static_assert(RecoveredBattleAttackPresentation::maximum_hp_loss==32768);
    for(const std::uint8_t source:{0,14})for(const std::uint64_t loss:{32767u,32768u})
        for(const auto key:{std::optional<std::uint16_t>{},std::optional<std::uint16_t>{1},std::optional<std::uint16_t>{96}}){
            const auto target=static_cast<std::uint8_t>(14-source);
            BattleSnapshot state{2,2,BattleState::Active,{}};
            state.actors[0]=BattleActor{0,1,40000,40000,20,120,10,10,10,10};
            state.actors[14]=BattleActor{14,2,40000,40000,20,120,10,10,10,10};
            state.actors[target]->hp-=loss;
            const BattleActionResult result{source,0,{{target,loss,loss,false}}};
            RecoveredPkActionProjection::Templates input{{attack(0,key),attack(14,key)},
                {vital(false,0,40000,40000),vital(false,14,40000,40000)},
                {vital(true,0,20),vital(true,0,20)}, {bulk(),bulk()}};
            require(input.hp[0].current()==40000&&input.hp[0].maximum()==40000,"Wide test fixture lost DWORD HP");
            const auto replies=RecoveredPkActionProjection::logical(state,result,input,key);
            for(std::uint8_t viewer=0;viewer<2;++viewer){
                const auto records=RecoveredTaiwanServerRecords::read(replies[viewer]);
                require(records&&Grammar::matches_output_sequence(replies[viewer]),"Native signed endpoint rejected by PK grammar");
                const auto& animation=records->front().bytes;
                require(animation[9]==(loss==32768?0:1)&&animation[10]==0x80&&
                    animation[2]==RecoveredPkRelativeView::position(source,viewer),
                    "Signed endpoint bytes or relative source changed");
                const auto local_target=RecoveredPkRelativeView::position(target,viewer);
                require(animation[5+2*(local_target/14)]==1&&animation[6+2*(local_target/14)]==0,
                    "Signed endpoint changed relative target");
                if(input.animation[viewer].requires_absolute_hp_update()){
                    const auto hp=RecoveredBattleVitals::parse_logical((*records)[1].bytes);
                    require(hp&&hp->current()==40000-loss&&hp->maximum()==40000,
                        "Pose-only endpoint lost absolute HP projection");
                }
            }
            auto overflow=result;overflow.hits[0].damage=32769;overflow.hits[0].hp_loss=32769;
            rejected([&]{RecoveredPkActionProjection::logical(state,overflow,input,key);},"Unrepresentable -32769 PK endpoint accepted");
            rejected([&]{RecoveredBattleAttackPresentation::hit(input.animation[0],source,target,32769,true);},
                "Unrepresentable -32769 presentation accepted");
            auto inconsistent=result;inconsistent.hits[0].damage=loss-1;
            rejected([&]{RecoveredPkActionProjection::logical(state,inconsistent,input,key);},"PK loss exceeded authoritative damage");
        }
}
}
int main(){
    try{grammar_checks();projection_checks();signed_endpoint_checks();}
    catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}
}
