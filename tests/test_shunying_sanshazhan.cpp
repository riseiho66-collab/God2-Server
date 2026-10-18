#include "game/ShunyingSanshazhan.h"
#include "protocol/DiagnosticBattleParticipants.h"
#include "protocol/DiagnosticShunyingManual.h"
#include "protocol/ShunyingSanshazhanReply.h"
#include "scripting/LuaEngine.h"
#include <iostream>

using namespace god2;
namespace {
void check(bool pass,const char* message){if(!pass)throw std::runtime_error(message);}
template<class F> void rejects(F fn){bool bad=false;try{fn();}catch(const std::exception&){bad=true;}check(bad,"Expected rejection");}
auto commands(std::uint8_t source,std::initializer_list<unsigned> targets) {
    std::vector<RecoveredWorldRecords::Record> out;
    unsigned n=0;
    for(auto target:targets) {
        std::array<std::uint8_t,17> bytes{};
        bytes[0]=0x35;bytes[1]=source%14;bytes[2]=++n<targets.size()?0x83:3;bytes[3]=source/14;
        const auto mask=1u<<(target%14), offset=5+2*(target/14);
        bytes[offset]=static_cast<std::uint8_t>(mask);bytes[offset+1]=static_cast<std::uint8_t>(mask>>8);
        bytes[13]=ShunyingSanshazhan::id;
        auto decoded=RecoveredWorldRecords::decode(bytes);
        check(decoded.has_value(),"Native command grammar rejected");
        out.insert(out.end(),decoded->begin(),decoded->end());
    }
    return out;
}
}
int main(){try {
    asio::io_context io;
    {
        LuaEngine lua(std::filesystem::path(__FILE__).parent_path().parent_path()/"scripts",false);
        check(lua.initialize(),"Lua initialization failed");
        for(const std::uint8_t source:{std::uint8_t{0},std::uint8_t{14}}) {
            const unsigned enemy=source?0:14;
            auto session=std::make_shared<Session>(asio::ip::tcp::socket(io),io.get_executor(),8,false,
                Session::PacketHandler{},Session::DisconnectHandler{});
            session->account_id=7;session->character_id=9;session->set_state(SessionState::InBattle);
            std::vector<BattleActor> actors{{source,9,100,100,40,40,31,999,5,5}};
            for(unsigned i=0;i<4;++i)actors.push_back({static_cast<std::uint8_t>(enemy+i),0,150,150,0,0,10,10,13,1});
            BattleAction basic{source,{},false,1000,100,0,0,150};
            const auto action=ShunyingSanshazhan::owned_action(basic);
            check(action.power_percent==300 && action.mp_cost==20 && !action.magical,"Formal policy not300% physical/20MP");
            RecoveredBattleService::Policy policy{static_cast<std::uint8_t>(source%14),static_cast<std::uint8_t>(source/14),source,0,basic,{}};
            auto encoder=[](const auto& state,const auto& result){return shunying_sanshazhan_reply(state,result,7);};
            ShunyingSanshazhan::authorize(policy,action,encoder);
            auto rule=[&](const CombatRuleInput& input){return lua.combat_damage(input);};
            for(unsigned count=1;count<=3;++count) {
                RecoveredBattleService service(rule);service.bind(*session,Battle(count,actors,123),policy,encoder);
                check(service.has_authorized_skill(8,ShunyingSanshazhan::key),"Bound skill missing");
                auto request=count==1?commands(source,{enemy}):count==2?commands(source,{enemy,enemy+1}):commands(source,{enemy,enemy+1,enemy+2});
                auto reply=service.handle(*session,request);check(reply.has_value(),"Formal cast rejected");
                const auto& state=service.inspect(8);
                check(state.actors[source]->mp==20,"Formal cast did not charge20MP once");
                for(unsigned i=0;i<count;++i)check(state.actors[enemy+i]->hp==70,"Lua physical31*300%-13 did not equal80");
                const auto logical=RecoveredWorldFrame::decode(*reply);
                const unsigned mp_bytes=source<14?17:0;
                check(logical && logical->size()==mp_bytes+count*15+121 && (*logical)[mp_bytes+count*15]==0x88,
                    "Formal action inserted eager HP86 before deferred skill damage or omitted cycle88");
                if(source<14)check(RecoveredBattleVitals::parse_logical(std::span(*logical).first(17))->current()==20,"MP display mismatch");
                for(unsigned i=0;i<count;++i) {
                    const auto at=mp_bytes+i*15;
                    const auto target_mask=at+5+2*(enemy/14);
                    check((*logical)[at]==0x83 && (*logical)[at+1]==3 && (*logical)[at+2]==source &&
                          (*logical)[target_mask]==(1u<<i) && (*logical)[target_mask+1]==0 &&
                          (*logical)[at+9]==0xb0 && (*logical)[at+10]==0xff &&
                          (*logical)[at+11]==126 && (*logical)[at+12]==0 && (*logical)[at+14]==28,
                          "Formal hit lost its126 identity, exact negative80 delta or living outcome");
                }
                const BattleActionResult projected{source,20,{{static_cast<std::uint8_t>(enemy),80,80,false}}};
                auto oversized=state;
                oversized.actors[enemy]->max_hp=std::uint64_t{1}<<32;
                rejects([&]{shunying_sanshazhan_reply(oversized,projected,7,false);});
                oversized=state;oversized.actors[enemy]->hp=std::uint64_t{1}<<32;
                rejects([&]{shunying_sanshazhan_reply(oversized,projected,7,false);});
            }
            auto checkpoint=Battle(5,actors,123).checkpoint();checkpoint.snapshot.actors[enemy+2]->hp=0;
            RecoveredBattleService guarded(rule);guarded.bind(*session,Battle::restore(checkpoint),policy,encoder);
            auto before=guarded.inspect(8);
            rejects([&]{guarded.handle(*session,commands(source,{enemy+2}));});
            rejects([&]{guarded.handle(*session,commands(source,{enemy,enemy}));});
            check(!guarded.handle(*session,commands(source,{enemy,enemy+1,enemy+2,enemy+3})),"Fourth formal target accepted");
            check(guarded.inspect(8)==before,"Rejected formal cast changed resources");
            checkpoint.snapshot.actors[source]->mp=19;
            RecoveredBattleService low(rule);low.bind(*session,Battle::restore(checkpoint),policy,encoder);
            before=low.inspect(8);rejects([&]{low.handle(*session,commands(source,{enemy}));});
            check(low.inspect(8)==before,"Insufficient20MP cast mutated state");
        }
    }
    for(const std::uint8_t source:{std::uint8_t{0},std::uint8_t{14}}) {
        auto session=std::make_shared<Session>(asio::ip::tcp::socket(io),io.get_executor(),1,false,
            Session::PacketHandler{},Session::DisconnectHandler{});
        session->account_id=7;session->character_id=9;session->set_state(SessionState::InBattle);
        const unsigned enemy=source?0:14;
        std::vector<BattleActor> actors{{source,9,100,100,20,20,30,30,5,5}};
        for(unsigned i=0;i<4;++i)actors.push_back({static_cast<std::uint8_t>(enemy+i),0,100,100,0,0,10,10,5,5});
        unsigned skill_calls=0,normal_calls=0;
        std::vector<ShunyingSanshazhan::VisualAssignment> visuals;
        // CUSTOM_TEST_NOT_NATIVE: deterministic damage and transport-valid
        // basic display fixture; this test does not certify blade3 rendering.
        auto encode=[&](const BattleSnapshot&,const BattleActionResult& r){
            std::vector<std::uint8_t> logical;
            for(const auto& hit:r.hits){auto bytes=diagnostic_battle_basic_animation(r.source,hit.target,hit.hp_loss);
                logical.insert(logical.end(),bytes.begin(),bytes.end());}
            return RecoveredWorldFrame::encode(logical);
        };
        auto main_encode=[&](const auto& state,const auto& r){++normal_calls;return encode(state,r);};
        auto custom_encode=[&](const auto& state,const auto& r){++skill_calls;
            visuals=ShunyingSanshazhan::visual_assignments(r);return encode(state,r);};
        const BattleAction action{source,{},false,100,100,4,0,150};
        RecoveredBattleService::Policy policy{static_cast<std::uint8_t>(source%14),static_cast<std::uint8_t>(source/14),source,0,action,{}};
        ShunyingSanshazhan::authorize(policy,action,custom_encode);
        rejects([&]{ShunyingSanshazhan::authorize(policy,action,custom_encode);});
        auto rule=[](const CombatRuleInput& p){return CombatRuleResult{10,p.mp_cost,false};};
        for(unsigned count=1;count<=3;++count) {
            RecoveredBattleService service(rule);service.bind(*session,Battle(1,actors,123),policy,main_encode);
            auto request=count==1?commands(source,{enemy}):count==2?commands(source,{enemy,enemy+1}):commands(source,{enemy,enemy+1,enemy+2});
            auto reply=service.handle(*session,request);check(reply.has_value(),"Valid cast rejected");
            check(service.inspect(1).actors[source]->mp==16,"Cost charged more than once");
            check(visuals.size()==count && !visuals[0].clone,"Wrong main caster assignment");
            for(unsigned i=0;i<count;++i){check(visuals[i].caster==source && visuals[i].target==enemy+i && visuals[i].clone==(i>0),"Wrong current-caster clone assignment");
                check(service.inspect(1).actors[enemy+i]->hp==90,"Damage not once per target");}
            check(service.inspect(1).actors[enemy+3]->hp==100,"Unselected actor hit");
        }
        check(skill_calls==3 && normal_calls==0,"Skill did not use its own presentation callback");
        {
            RecoveredBattleService service(rule);service.bind(*session,Battle(2,actors,123),policy,main_encode);
            const auto before=service.inspect(1);
            check(!service.handle(*session,commands(source,{enemy,enemy+1,enemy+2,enemy+3})),"Fourth target accepted");
            rejects([&]{service.handle(*session,commands(source,{enemy,enemy}));});
            rejects([&]{service.handle(*session,commands(source,{source}));});
            rejects([&]{service.handle(*session,commands(source,{enemy+8}));});
            check(service.inspect(1)==before && skill_calls==3,"Rejected command mutated state/rendered");
        }
        {
            auto reduced=Battle(3,actors,123).checkpoint();
            reduced.snapshot.actors[enemy+2]->hp=0;reduced.snapshot.actors[enemy+3]->hp=0;
            RecoveredBattleService service(rule);service.bind(*session,Battle::restore(reduced),policy,main_encode);
            rejects([&]{service.handle(*session,commands(source,{enemy+2}));});
            check(service.handle(*session,commands(source,{enemy,enemy+1})).has_value() && visuals.size()==2,"Two living enemies failed");
            reduced.snapshot.actors[enemy+1]->hp=0;reduced.snapshot.id=4;
            RecoveredBattleService solo(rule);solo.bind(*session,Battle::restore(reduced),policy,main_encode);
            check(solo.handle(*session,commands(source,{enemy})).has_value() && visuals.size()==1 && !visuals[0].clone,"Single enemy spawned clone");
        }
        {
            auto p=policy;p.diagnostic_single_action=true;p.diagnostic_retaliation=BattleAction{static_cast<std::uint8_t>(enemy),{source},false,100,100,0,0,150};
            RecoveredBattleService service(rule);service.bind(*session,Battle(5,actors,123),p,main_encode);
            const auto previous=normal_calls;
            check(service.handle(*session,commands(source,{enemy})).has_value() && normal_calls==previous+1,"Retaliation inherited clone encoder");
        }
        {
            auto p=policy;p.skill_encoders[ShunyingSanshazhan::key]=[](const auto&,const auto&)->std::vector<std::uint8_t>{throw std::runtime_error("renderer unavailable");};
            RecoveredBattleService service(rule);service.bind(*session,Battle(6,actors,123),p,main_encode);
            const auto before=service.inspect(1);
            rejects([&]{service.handle(*session,commands(source,{enemy}));});
            check(service.inspect(1)==before,"Failed presentation committed HP/MP");
        }
    }
    {
        const auto seed=diagnostic_shunying_manual_seed();
        check(seed.size()==8 && seed[1]==102 && seed[3]==ShunyingSanshazhan::id && seed[5]==102 && seed[7]==8,
              "Manual seed did not bind the owned female deity");
        auto appearance=RecoveredWorldEntry::historical_body;
        appearance[12]=0x12;appearance[13]=0x34;
        const auto participants=diagnostic_shunying_manual_participants(9,appearance);
        check(participants[4]==0x12 && participants[5]==0x34,"Manual appearance did not follow current character");
        const CharacterResources saved{8000,9999,7000,9999,1,"CUSTOM-0012"};
        const auto configured=diagnostic_shunying_manual_participants(9,appearance,&saved,50);
        check(configured[19]==50,"Manual battle level did not follow stored role");
        const auto configured_hp=RecoveredBattleVitals::parse_logical(std::span(configured).subspan(62,17));
        const auto configured_mp=RecoveredBattleVitals::parse_logical(std::span(configured).subspan(79,17));
        check(configured_hp && configured_hp->current()==8000 && configured_hp->maximum()==9999 &&
              configured_mp && configured_mp->current()==7000 && configured_mp->maximum()==9999,
              "Saved resources diverged from battle projection");
        const auto central=diagnostic_shunying_manual_participants(9,appearance,&saved,50,
            diagnostic_shunying_manual_slot);
        check(central[2]==2 && central[18]==2 && central[64]==2 && central[81]==2,
              "Central caster appearance/identity/vitals use different slots");
        const auto central_components=DiagnosticShunyingFemaleDeity::battle_components(2);
        check(std::equal(central_components.begin(),central_components.end(),central.begin()+96),
              "Central deity owner attachment mismatch");
        const auto central_summon=DiagnosticShunyingFemaleDeity::battle_summon(2);
        check(std::equal(central_summon.begin(),central_summon.end(),central.end()-153) &&
              central_summon[2]==2 && central_summon[5]==4 && central_summon[6]==0,
              "Central deity summon source/self mask mismatch");
        const auto central_bulk=RecoveredBattleVitalsBatch::parse_logical(std::span(central).subspan(central.size()-138,121));
        check(central_bulk && central_bulk->at(2)->hp==8000 && central_bulk->at(2)->mp==7000 &&
              central_bulk->at(0)->hp==0 && central[central.size()-13]==2,
              "Central bulk resources/grant remain in old slot");
        rejects([&]{diagnostic_shunying_manual_participants(9,appearance,nullptr,1,14);});
        rejects([&]{DiagnosticShunyingFemaleDeity::battle_summon(14);});
        check(!ShunyingSanshazhan::magical && ShunyingSanshazhan::provisional_power_percent==300,
              "Owner provisional physical triple coefficient differs");
        check(participants.size()==1134,"Manual bootstrap size changed");
        const auto deity=DiagnosticShunyingFemaleDeity::battle_components();
        const auto summon=DiagnosticShunyingFemaleDeity::battle_summon();
        check(std::equal(deity.begin(),deity.end(),participants.begin()+96),"Female deity components missing after player");
        check(std::equal(summon.begin(),summon.end(),participants.end()-153),"Female deity summon missing before ready barrier");
        check(RecoveredWorldFrame::decode(RecoveredWorldFrame::encode(participants)).value()==participants,"Full field bootstrap framing failed");
        for(unsigned i=0;i<14;++i) {
            const auto offset=113+i*62;
            check(participants[offset]==0x1c && participants[offset+1]==14+i,"Full field identity missing");
            const auto hp=RecoveredBattleVitals::parse_logical(std::span(participants).subspan(offset+45,17));
            check(hp && hp->current()==10000,"Full field target HP differs");
        }
        auto session=std::make_shared<Session>(asio::ip::tcp::socket(io),io.get_executor(),7,false,
            Session::PacketHandler{},Session::DisconnectHandler{});
        session->account_id=7;session->character_id=9;session->set_state(SessionState::InBattle);
        BattleAction action{0,{},false,100,100,0,0,150};
        RecoveredBattleService::Policy policy{0,0,0,0,action,{},true};
        policy.diagnostic_manual_receipts=true;policy.diagnostic_player_initial_control=true;
        auto encoder=[](const auto& state,const auto& result){return diagnostic_shunying_manual_reply(state,result,0);};
        ShunyingSanshazhan::authorize(policy,action,encoder);
        RecoveredBattleService service([](const auto&){return CombatRuleResult{10,0,false};});
        service.bind(*session,Battle(7,diagnostic_shunying_manual_actors(9),123),policy,encoder);
        auto control=[](unsigned friendly,unsigned enemy,unsigned source=0) {
            std::array<std::uint8_t,17> bytes{};bytes[0]=0x35;bytes[2]=0x0b;
            bytes[1]=static_cast<std::uint8_t>(source);
            bytes[5]=static_cast<std::uint8_t>(friendly);bytes[6]=static_cast<std::uint8_t>(friendly>>8);
            bytes[7]=static_cast<std::uint8_t>(enemy);bytes[8]=static_cast<std::uint8_t>(enemy>>8);
            return *RecoveredWorldRecords::decode(bytes);
        };
        check(service.handle(*session,control(0,0)).has_value(),"Initial manual receipt rejected");
        auto expired=control(1,0);
        auto timeout_bytes=std::array<std::uint8_t,17>{};
        timeout_bytes[0]=0x35;timeout_bytes[2]=2;timeout_bytes[5]=1;
        expired=*RecoveredWorldRecords::decode(timeout_bytes);
        const auto before_idle=service.inspect(7);
        for(unsigned retry=0;retry<3;++retry) {
            const auto reply=service.handle(*session,expired);
            check(reply && service.inspect(7)==before_idle,"Manual timeout disconnected or changed state");
            const auto logical=RecoveredWorldFrame::decode(*reply);
            check(logical && (*logical)[0]==0x86 && (*logical)[1]==5,"Manual timeout did not reopen input");
        }
        // Native mode16 accepts repeated clicks: retry must stay connected,
        // preserve the entire battle and leave the next valid cast available.
        for(const auto& bad: {commands(0,{16,16,16}), commands(0,{14,14}),
                             commands(0,{0}), commands(0,{1}),
                             commands(0,{14,15,16,17})}) {
            const auto before=service.inspect(7);
            const auto reply=service.handle(*session,bad);
            check(reply.has_value(),"Invalid manual selection closed the connection");
            const auto logical=RecoveredWorldFrame::decode(*reply);
            check(logical && logical->size()==17 && (*logical)[0]==0x86 &&
                  (*logical)[1]==5 && (*logical)[3]==1 && (*logical)[4]==0,
                  "Invalid manual selection did not re-grant native input");
            check(service.inspect(7)==before && !service.diagnostic_round_ready(*session),
                  "Invalid manual selection changed state or consumed action");
        }
        // A dead target must be rejected before rule/render callbacks, too.
        auto checkpoint=Battle(8,diagnostic_shunying_manual_actors(9),123).checkpoint();
        checkpoint.snapshot.actors[14]->hp=0;
        RecoveredBattleService dead([](const auto&)->CombatRuleResult {
            throw std::runtime_error("Dead target reached the damage rule");
        });
        dead.bind(*session,Battle::restore(checkpoint),policy,encoder);
        const auto dead_before=dead.inspect(7);
        check(dead.handle(*session,commands(0,{14})).has_value() && dead.inspect(7)==dead_before,
              "Dead manual target was not safely refused");
        // Unrelated authority/sequence errors remain rejected, not re-granted.
        auto unauthorized=commands(0,{14});
        std::get<RecoveredSkillCommand::Record>(unauthorized[0]).context_storage=99;
        check(!service.handle(*session,unauthorized),"Unauthorized manual context was re-granted");
        for(unsigned trial=0;trial<3;++trial) {
            const auto reply=service.handle(*session,commands(0,{14,20,27}));
            check(reply.has_value(),"Repeated manual cast rejected");
            const auto logical=RecoveredWorldFrame::decode(*reply);
            check(logical && logical->size()==3*15+121 && (*logical)[3*15]==0x88,
                  "Manual skill inserted eager HP86 before deferred damage or omitted cycle88");
            for(unsigned i=0;i<3;++i) {
                const auto at=i*15;
                const std::array<unsigned,3> masks{1,1u<<6,1u<<13};
                check((*logical)[at]==0x83 && (*logical)[at+1]==3 && (*logical)[at+2]==0 &&
                      (*logical)[at+7]==(masks[i]&0xff) && (*logical)[at+8]==(masks[i]>>8) &&
                      (*logical)[at+9]==0xf6 && (*logical)[at+10]==0xff &&
                      (*logical)[at+11]==ShunyingSanshazhan::id && (*logical)[at+14]==28,
                      "Manual skill lost its exact negative10 delta, clone routing or living outcome");
            }
            const auto before=service.inspect(7);
            check(!service.handle(*session,control(2,0)),"Absent friendly accepted in manual receipt");
            check(service.inspect(7)==before,"Invalid receipt altered HP");
            check(service.handle(*session,control(0,1u<<13)).has_value(),"Last field target receipt rejected");
            check(service.diagnostic_round_ready(*session),"Manual round not ready");
            service.rearm_diagnostic(*session,service.inspect(7).revision);
        }
        check(service.inspect(7).actors[0]->mp==50 && service.inspect(7).actors[14]->hp==9970 &&
              service.inspect(7).actors[20]->hp==9970 && service.inspect(7).actors[27]->hp==9970 &&
              service.inspect(7).actors[15]->hp==10000,"Manual trial mutation/cost mismatch");
        BattleAction center_action{2,{},false,100,100,0,0,150};
        RecoveredBattleService::Policy center_policy{2,0,2,0,center_action,{},true};
        center_policy.diagnostic_manual_receipts=true;
        center_policy.diagnostic_player_initial_control=true;
        ShunyingSanshazhan::authorize(center_policy,center_action,encoder);
        RecoveredBattleService center_service([](const auto&){return CombatRuleResult{10,0,false};});
        auto basic_encoder=[](const auto& state,const auto& result){return diagnostic_shunying_manual_basic_reply(state,result,12);};
        center_service.bind(*session,Battle(9,diagnostic_shunying_manual_actors(9,&saved,2),123),center_policy,basic_encoder);
        check(!center_service.handle(*session,control(0,0,0)),"Old source slot retained central control authority");
        auto live_initial=control(0,0,2);
        auto& live_fields=std::get<RecoveredBattleCommand::ControlRequest>(live_initial[0]).fields;
        live_fields.unwritten_byte3=11;live_fields.unwritten_parameter=0x0be53020;
        check(center_service.handle(*session,live_initial).has_value(),"Native stack residue disconnected central initial receipt");
        const auto center_before_idle=center_service.inspect(7);
        for(unsigned poison=0;poison<256;++poison) {
            auto raw=std::array<std::uint8_t,17>{};raw[0]=0x35;raw[1]=2;raw[2]=2;raw[5]=4;
            raw[4]=static_cast<std::uint8_t>(poison);
            for(unsigned i=13;i<17;++i)raw[i]=static_cast<std::uint8_t>(poison);
            const auto reply=center_service.handle(*session,*RecoveredWorldRecords::decode(raw));
            check(reply && center_service.inspect(7)==center_before_idle,"Unused stack bytes changed timeout handling or state");
            raw[5]=1;
            check(!center_service.handle(*session,*RecoveredWorldRecords::decode(raw)),"Wrong self mask accepted after residue fix");
        }
        check(!center_service.handle(*session,commands(0,{14})),"Old slot accepted central skill command");
        const auto center_reply=center_service.handle(*session,commands(2,{14,20,27}));
        check(center_reply.has_value(),"Central caster could not select three targets");
        const auto center_logical=RecoveredWorldFrame::decode(*center_reply);
        check(center_logical && (*center_logical)[2]==2 && center_service.inspect(7).actors[2]->mp==7000 &&
              !center_service.inspect(7).actors[0],"Central cast source/resource binding mismatch");
        check(center_service.handle(*session,control(0,1,2)).has_value() &&
              center_service.diagnostic_round_ready(*session),"Central skill did not complete before basic click");
        center_service.rearm_diagnostic(*session,center_service.inspect(7).revision);
        auto basic=[](unsigned target) {
            std::array<std::uint8_t,17> raw{};raw[0]=0x35;raw[1]=2;raw[2]=1;
            const unsigned bit=1u<<(target%14),at=5+2*(target/14);
            raw[at]=static_cast<std::uint8_t>(bit);raw[at+1]=static_cast<std::uint8_t>(bit>>8);
            return *RecoveredWorldRecords::decode(raw);
        };
        for(unsigned retry=0;retry<3;++retry) {
            const auto reply=center_service.handle(*session,basic(14));
            check(reply.has_value(),"Manual basic click rejected");
            const auto logical=RecoveredWorldFrame::decode(*reply);
            check(logical && logical->size()==153 && (*logical)[0]==0x83 && (*logical)[1]==1 &&
                  (*logical)[2]==2 && (*logical)[12]==28 && (*logical)[15]==0x86 &&
                  (*logical)[32]==0x88 && (*logical)[33]==12,
                  "Manual basic reply omitted native animation/HP/current-cycle88 or became a skill");
            const auto before_receipt=center_service.inspect(7);
            check(!center_service.diagnostic_round_ready(*session),"Basic input reopened before receipt");
            check(center_service.handle(*session,control(0,1,2)).has_value() &&
                  center_service.inspect(7)==before_receipt && center_service.diagnostic_round_ready(*session),
                  "Basic receipt failed or mutated state");
            center_service.rearm_diagnostic(*session,before_receipt.revision);
        }
        check(center_service.handle(*session,commands(2,{14,20,27})).has_value(),
              "Custom skill unavailable after basic turn cycles");
        auto dead_state=center_service.inspect(7);dead_state.actors[14]->hp=0;
        const BattleActionResult lethal{2,0,{{14,10,10,false}}};
        const auto lethal_logical=RecoveredWorldFrame::decode(diagnostic_shunying_manual_basic_reply(dead_state,lethal,13));
        check(lethal_logical && (*lethal_logical)[12]==0 && (*lethal_logical)[32]==0x88 &&
              RecoveredBattleVitals::parse_logical(std::span(*lethal_logical).subspan(15,17))->current()==0,
              "Dead basic target did not retain death route/zeroHP/88");
        const auto lethal_skill=RecoveredWorldFrame::decode(diagnostic_shunying_manual_reply(dead_state,lethal,13));
        check(lethal_skill && lethal_skill->size()==15+121 && (*lethal_skill)[0]==0x83 &&
              (*lethal_skill)[1]==3 && (*lethal_skill)[2]==2 && (*lethal_skill)[9]==0xf6 &&
              (*lethal_skill)[10]==0xff && (*lethal_skill)[11]==ShunyingSanshazhan::id &&
              (*lethal_skill)[14]==0 && (*lethal_skill)[15]==0x88,
              "Dead manual skill target lost deferred damage/death/88 or gained eager HP86");
        auto oversized=dead_state;oversized.actors[14]->max_hp=std::uint64_t{1}<<32;
        rejects([&]{diagnostic_shunying_manual_reply(oversized,lethal,13);});
        oversized=dead_state;oversized.actors[14]->hp=std::uint64_t{1}<<32;
        rejects([&]{diagnostic_shunying_manual_reply(oversized,lethal,13);});
        rejects([&]{diagnostic_shunying_manual_basic_reply(dead_state,BattleActionResult{2,0,{}},0);});
        rejects([&]{diagnostic_shunying_manual_basic_reply(dead_state,BattleActionResult{28,0,{{14,1,1,false}}},0);});
        rejects([&]{diagnostic_shunying_manual_basic_reply(dead_state,BattleActionResult{2,0,{{28,1,1,false}}},0);});
        rejects([&]{diagnostic_shunying_manual_basic_reply(dead_state,BattleActionResult{2,0,{{0,1,1,false}}},0);});
        rejects([&]{diagnostic_shunying_manual_basic_reply(dead_state,BattleActionResult{2,0,{{2,1,1,false}}},0);});
        rejects([&]{diagnostic_shunying_manual_basic_reply(dead_state,BattleActionResult{2,0,{{14,1,32768,false}}},0);});
    }
    std::cout<<"Shunying policy: both sides, 1/2/3 targets, caps, rejection, atomic MP, visual mapping, rollback passed\n";
    return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
