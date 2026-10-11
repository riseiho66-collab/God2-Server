#include "game/ThousandBulls.h"
#include "game/ShunyingSanshazhan.h"
#include "protocol/ThousandBullsReply.h"
#include "protocol/DiagnosticThousandBullsManual.h"
#include "scripting/LuaEngine.h"
#include <iostream>
#include <limits>
using namespace god2;
namespace {
void check(bool x,const char* message){if(!x)throw std::runtime_error(message);}
template<class F>void rejects(F f){bool bad=false;try{f();}catch(const std::exception&){bad=true;}check(bad,"Expected rejection");}
auto command(unsigned source,unsigned mask=0x3fff,bool friendly=false,unsigned id=150,bool continuation=false){
    std::array<std::uint8_t,17> bytes{};bytes[0]=0x35;bytes[1]=std::uint8_t(source%14);bytes[2]=continuation?0x83:3;bytes[3]=std::uint8_t(source/14);bytes[13]=std::uint8_t(id);
    const unsigned side=friendly?source/14:1-source/14;
    bytes[5+side*2]=std::uint8_t(mask);bytes[6+side*2]=std::uint8_t(mask>>8);
    return RecoveredWorldRecords::decode(bytes);
}
}
int main(){try{
    asio::io_context io;LuaEngine lua(std::filesystem::path(__FILE__).parent_path().parent_path()/"scripts",false);
    check(lua.initialize(),"Lua init");
    check(diagnostic_thousand_bulls_manual_seed()==std::array<std::uint8_t,4>{0x34,102,0,150},"Manual seed must grant150 only");
    check(diagnostic_thousand_bulls_manual_selectable()==std::array<std::uint8_t,3>{0x87,150,0x80},"Manual selection identity");
    check(diagnostic_recording_skills()==std::array<std::uint8_t,8>{0x34,102,0,126,0x34,102,0,150},"Recording skills126+150 grants");
    for(unsigned side=0;side<2;++side)for(unsigned targets:{1u,3u,14u}){
        const auto caster=std::uint8_t(side*14),enemy=std::uint8_t((1-side)*14);
        std::vector<BattleActor> fixture{{caster,9,99999,99999,9999,9999,1,1,999999,999999}};
        std::vector<std::uint8_t> target_slots;
        for(unsigned i=0;i<targets;++i){target_slots.push_back(std::uint8_t(enemy+i));fixture.push_back({std::uint8_t(enemy+i),0,99999,99999,0,0,1,1,999999,999999});}
        Battle test(500,fixture,1);BattleAction action{caster,target_slots,false,1000,100,100,10000,1000};
        for(unsigned cast=0;cast<3;++cast){
            const auto reply=test.act(9,test.inspect().revision,action,RecordingCombatTest::rule,[&](const auto& state,const auto& result){
                for(const auto& hit:result.hits)check(hit.damage==39996&&!hit.critical,"Fixed recording ignores attack/defense/critical");
                return diagnostic_recording_bulls_reply(state,result,cast);
            });
            const auto logical=RecoveredWorldFrame::decode(reply);check(logical.has_value(),"Recording frame");
            for(unsigned i=0;i<targets;++i){
                const auto at=(side?0u:17u)+i*15;
                check(static_cast<std::int16_t>((*logical)[at+9]|((*logical)[at+10]<<8))==-9999,"Per-hit token overflow");
                check(test.inspect().actors[enemy+i]->hp==(cast==0?60003u:cast==1?20007u:0u),"39996 server HP settlement");
            }
        }
        check(test.inspect().state==BattleState::Finished,"Recording target death");
    }
    check(RecordingCombatTest::rule({99999,99999,300,100,20,99,10000,1000,0}).damage==9999,"126 fixed damage");
    check(RecordingCombatTest::rule({1,999999,100,100,0,99,0,150,0}).damage==9999,"Basic fixed damage");
    for(unsigned total=0;total<100000;++total){auto p=ThousandBulls::presentation_losses(total);
        check(std::uint64_t{p[0]}+p[1]+p[2]+p[3]==total,"Four phases lost damage");
        check(!total || p[3]>0,"Positive lethal remainder must survive until fourth phase");
        check(p[0]==std::uint64_t{total}*20/100 && p[0]+p[1]==std::uint64_t{total}*45/100 && p[0]+p[1]+p[2]==std::uint64_t{total}*75/100,"Cumulative phase floors changed");
    }
    auto wide=ThousandBulls::presentation_losses(std::numeric_limits<std::uint32_t>::max());
    check(std::uint64_t{wide[0]}+wide[1]+wide[2]+wide[3]==0xffffffffu,"Phase overflow");
    check(!command(0,0x3fff,false,126),"126 combined-mask grammar regressed");
    check(!command(0,0x3fff,false,150,true),"All-target continuation admitted");
    check(!command(0,0xffff),"Reserved mask bits admitted");
    for(unsigned side=0;side<2;++side)for(unsigned count:{1u,2u,14u}){
        const auto source=std::uint8_t(side*14),enemy=std::uint8_t((1-side)*14);
        auto session=std::make_shared<Session>(asio::ip::tcp::socket(io),io.get_executor(),91,false,Session::PacketHandler{},Session::DisconnectHandler{});
        session->account_id=7;session->character_id=9;session->set_state(SessionState::InBattle);
        std::vector<BattleActor> actors{{source,9,100,100,200,200,31,999,5,5}};
        for(unsigned i=0;i<count;++i)actors.push_back({std::uint8_t(enemy+i),0,2000,2000,0,0,10,10,13,1});
        BattleAction basic{source,{},true,100,100,0,0,150};
        RecoveredBattleService::Policy policy{0,std::uint8_t(side),source,0,basic,{}};
        unsigned formulas=0,encoded=0;
        auto encoder=[&](const auto& state,const auto& result){++encoded;check(result.hits.size()==count,"Not all living opponents");return thousand_bulls_reply(state,result,7);};
        ThousandBulls::authorize(policy,basic,encoder);
        check(policy.skills.at(ThousandBulls::key).power_percent==1000 && !policy.skills.at(ThousandBulls::key).magical,"Owned physical1000% policy");
        check(ShunyingSanshazhan::id==126 && ShunyingSanshazhan::mp_cost==20,"126 identity changed");
        auto rule=[&](const CombatRuleInput& input){++formulas;return lua.combat_damage(input);};
        RecoveredBattleService service(rule);service.bind(*session,Battle(1,actors,123),policy,encoder);
        auto request=command(source);check(request.has_value(),"Full native mode5 command rejected");
        auto reply=service.handle(*session,*request);check(reply.has_value(),"All-target cast refused");
        check(formulas==count && encoded==1,"Repeated damage formula or cast encoding");
        const auto& state=service.inspect(91);check(state.actors[source]->mp==100,"100MP not charged once");
        for(unsigned i=0;i<count;++i)check(state.actors[enemy+i]->hp==1703,"Physical31*1000%-13 expected297");
        auto wire=RecoveredWorldFrame::decode(*reply);const unsigned start=side?0:17;
        check(wire && wire->size()==start+count*15+121,"Unexpected eager HP86 or native target bound");
        if(!side)check((*wire)[0]==0x86 && (*wire)[1]==1 && (*wire)[2]==source,"Caster MP86 must precede action barrier");
        for(unsigned i=0;i<count;++i){
            const unsigned at=start+i*15;
            check((*wire)[at]==0x83 && (*wire)[at+1]==3 && (*wire)[at+11]==150,"Expected one total hit83 per target without intervening HP86");
            const auto delta=static_cast<std::int16_t>(std::uint16_t{(*wire)[at+9]} | (std::uint16_t{(*wire)[at+10]}<<8));
            check(delta==-297,"Wire total differs from authoritative settlement");
            int shown_hp=2000;
            for(const auto loss:ThousandBulls::presentation_losses(static_cast<unsigned>(-delta)))shown_hp-=static_cast<int>(loss);
            check(shown_hp==static_cast<int>(state.actors[enemy+i]->hp),"Four presentation deltas must settle from initial HP exactly once");
        }
        check((*wire)[start+count*15]==0x88,"Final barrier-delayed88 must follow all83 records");
        // Friendly side, arbitrary subsets, and insufficient MP never mutate.
        RecoveredBattleService guarded(rule);guarded.bind(*session,Battle(2,actors,123),policy,encoder);const auto before=guarded.inspect(91);
        check(!guarded.handle(*session,*command(source,1)),"Subset cast accepted");
        check(!guarded.handle(*session,*command(source,0x3fff,true)),"Friendly side accepted");
        check(guarded.inspect(91)==before,"Rejected target changed state");
        auto cp=Battle(3,actors,123).checkpoint();cp.snapshot.actors[source]->mp=99;
        RecoveredBattleService low(rule);low.bind(*session,Battle::restore(cp),policy,encoder);auto low_before=low.inspect(91);
        rejects([&]{low.handle(*session,*request);});check(low.inspect(91)==low_before,"Low MP mutation");
    }
    // Server resolves native full marker against current life/occupancy, not
    // fourteen synthetic targets. A low-HP target contributes actual loss1.
    auto session=std::make_shared<Session>(asio::ip::tcp::socket(io),io.get_executor(),92,false,Session::PacketHandler{},Session::DisconnectHandler{});
    session->account_id=7;session->character_id=9;session->set_state(SessionState::InBattle);
    std::vector<BattleActor> actors{{0,9,100,100,100,100,31,999,5,5},{14,0,1,1,0,0,10,10,13,1},{27,0,100,100,0,0,10,10,13,1}};
    auto cp=Battle(4,actors,123).checkpoint();cp.snapshot.actors[27]->hp=0;
    BattleAction basic{0,{},false,100,100,0,0,150};RecoveredBattleService::Policy policy{0,0,0,0,basic,{}};
    auto encode=[](const auto& state,const auto& result){check(result.hits.size()==1 && result.hits[0].target==14 && result.hits[0].hp_loss==1,"Dead/empty/lowHP handling");return thousand_bulls_reply(state,result,8);};
    ThousandBulls::authorize(policy,basic,encode);
    RecoveredBattleService service([&](const auto& in){return lua.combat_damage(in);});service.bind(*session,Battle::restore(cp),policy,encode);
    check(service.handle(*session,*command(0)).has_value(),"Sparse living enemies refused");
    std::cout<<"ThousandBulls server policy and four-phase conservation passed\n";
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
