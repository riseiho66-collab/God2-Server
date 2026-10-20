#include "game/Battle.h"
#include "game/BattleCheckpointCodec.h"
#include "game/DiagnosticBattleRecovery.h"
#include <nlohmann/json.hpp>
#include "scripting/LuaEngine.h"
#include "protocol/RecoveredWorldFrame.h"
#include "protocol/DiagnosticBattleParticipants.h"
#include "protocol/DiagnosticShunyingManual.h"
#include <iostream>
#include <stdexcept>
#include <memory>
#include <sqlite3.h>

namespace {
using namespace god2;
void require(bool value,const char* message) {if(!value) throw std::runtime_error(message);}
template<class F> void rejects(F function) {
    bool failed=false;
    try {function();} catch(const std::exception&) {failed=true;}
    require(failed,"Invalid transaction accepted");
}
const std::array<BattleActor,3> actors{{
    {0,7,100,100,20,20,31,40,8,10},
    {14,0,100,100,30,30,20,25,13,6},
    {15,0,100,100,30,30,20,25,13,6}}};
const BattleAction attack{0,{14,15},false,100,100,8,0,150};
// Diagnostic encoder uses explicit zero opaque fields, not a production policy.
std::vector<std::uint8_t> encode(const BattleSnapshot& state,const BattleActionResult&) {
    std::vector<std::uint8_t> logical;
    for(const auto& actor:state.actors) if(actor) {
        for(unsigned kind=0;kind<(actor->position<14?2u:1u);++kind) {
            std::array<std::uint8_t,17> record{};
            record[0]=0x86;record[1]=static_cast<std::uint8_t>(kind);record[2]=actor->position;
            const auto maximum=kind?actor->max_mp:actor->max_hp;
            const auto current=kind?actor->mp:actor->hp;
            for(unsigned byte=0;byte<4;++byte) {
                record[5+byte]=static_cast<std::uint8_t>(maximum>>(8*byte));
                record[9+byte]=static_cast<std::uint8_t>(current>>(8*byte));
            }
            logical.insert(logical.end(),record.begin(),record.end());
        }
    }
    return RecoveredWorldFrame::encode(logical);
}
void signed_endpoint_transaction_test() {
    const std::array<BattleActor,2> pair{{{0,7,40000,40000,20,20,31,40,8,10},
        {14,0,40000,40000,0,0,20,25,13,6}}};
    const BattleAction action{0,{14},false,100,100,8,0,150};
    unsigned visits=0;
    const auto encode_native=[&](const BattleSnapshot& state,const BattleActionResult& result){
        ++visits;const auto& hit=result.hits.front();
        const auto raw=diagnostic_battle_basic_animation(result.source,hit.target,hit.hp_loss,0,
            state.actors[hit.target]->hp!=0);
        return RecoveredWorldFrame::encode(raw);
    };
    Battle rejected_wire(33,pair,123);const auto original=rejected_wire.checkpoint();
    rejects([&]{rejected_wire.act(7,1,action,[](const CombatRuleInput&){
        return CombatRuleResult{32769,8,false};},encode_native);});
    require(visits==1&&rejected_wire.checkpoint()==original,
        "Unrepresentable native endpoint changed HP/MP/revision/RNG before successful encode");
    for(const std::uint64_t loss:{32767u,32768u}) {
        Battle direct(34,pair,123);
        const auto wire=direct.act(7,1,action,[loss](const CombatRuleInput&){
            return CombatRuleResult{loss,8,false};},encode_native);
        const auto decoded=RecoveredWorldFrame::decode(wire);
        require(decoded&&decoded->size()==15&&(*decoded)[9]==(loss==32768?0:1)&&(*decoded)[10]==0x80&&
            direct.inspect().actors[14]->hp==40000-loss&&direct.inspect().actors[0]->mp==12&&
            direct.inspect().revision==2,"Native endpoint action lost exact bytes or single resource settlement");
    }
    const auto exact=[](const CombatRuleInput&){return CombatRuleResult{32768,8,false};};
    const auto retried=rejected_wire.act(7,1,action,exact,encode_native);
    Battle fresh(33,pair,123);const auto expected=fresh.act(7,1,action,exact,encode_native);
    require(retried==expected&&rejected_wire.checkpoint()==fresh.checkpoint(),
        "Failed endpoint encoding consumed RNG or prevented exact retry");
}
void signed_hp_domain_transaction_test() {
    const BattleAction action{0,{14},false,100,100,8,0,150};
    const auto rule=[](const CombatRuleInput&){return CombatRuleResult{32768,8,false};};
    for(const std::uint64_t maximum:{0x7fffffffu,0x80000000u,0x90000000u}){
        const std::array<BattleActor,2> pair{{{0,7,40000,40000,20,20,31,40,8,10},
            {14,0,40000,maximum,0,0,20,25,13,6}}};
        Battle subject(35,pair,987,BattleNumericProfile::ExtendedHealth64);
        const auto before=subject.checkpoint();
        const auto deferred=[](const BattleSnapshot& state,const BattleActionResult& result){
            return diagnostic_shunying_manual_basic_reply(state,result,0);
        };
        if(maximum==0x7fffffff){
            const auto wire=subject.act(7,1,action,rule,deferred);
            const auto logical=RecoveredWorldFrame::decode(wire);
            require(logical&&(*logical)[9]==0&&(*logical)[10]==0x80&&
                subject.inspect().actors[14]->hp==7232,"Signed target boundary lost exact subtraction");
        }else{
            rejects([&]{subject.act(7,1,action,rule,deferred);});
            require(subject.checkpoint()==before,"Deferred HP rejection changed extended state or RNG");
            Battle control(35,pair,987,BattleNumericProfile::ExtendedHealth64);
            const auto retried=subject.act(7,1,action,rule,encode);
            require(retried==control.act(7,1,action,rule,encode)&&subject.checkpoint()==control.checkpoint()&&
                subject.inspect().actors[14]->hp==7232&&subject.inspect().actors[14]->max_hp==maximum&&
                subject.inspect().actors[0]->mp==12,
                "Deferred representation check capped core64, absolute DWORD, rollback or retry");
        }
    }
}
void callback_fence_transaction_test() {
    // Synthetic core transactions, not native combat rules or packet evidence.
    const std::array<BattleActor,3> team{{
        {0,7,100,100,20,20,31,40,8,10},
        {1,7,100,100,20,20,31,40,8,10},
        {14,0,100,100,30,30,20,25,13,6}}};
    auto initial=Battle(36,team,987).checkpoint();
    initial.snapshot.actors[1]->hp=0;
    const BattleAction action{0,{14},false,100,100,8,0,150};
    RecoveredBattleDelta::Bytes delta_bytes{};
    delta_bytes[0]=0x83;delta_bytes[1]=0x0d;delta_bytes[7]=1;
    delta_bytes[9]=0xff;delta_bytes[10]=0xff; // One HP loss, kind1/selector0/live.
    delta_bytes[11]=1;delta_bytes[14]=28;
    const auto delta=RecoveredBattleDelta::parse(delta_bytes);
    require(delta.has_value(),"Callback fence fixture has an invalid native delta");
    const std::array<RecoveredBattleDelta::Record,1> deltas{*delta};
    // operation: attack, revival, native delta, read-only poison observation.
    // Hook selection covers every external rule/encoder boundary in the core.
    const auto invoke=[&](Battle& subject,unsigned operation,bool in_encoder,
                         const std::function<void()>& hook){
        const auto visit=[&]{if(hook)hook();};
        switch(operation){
        case 0:
            (void)subject.act(7,subject.inspect().revision,action,
                [&](const CombatRuleInput& input){
                    if(!in_encoder)visit();
                    return CombatRuleResult{1+input.roll%5,input.mp_cost,false};
                },[&](const auto& state,const auto& result){
                    if(in_encoder)visit();
                    return encode(state,result);
                });
            break;
        case 1:
            (void)subject.revive(7,subject.inspect().revision,0,1,
                [&](const auto&){if(!in_encoder)visit();return RevivalResult{25,8};},
                [&](const auto& state,const auto&){
                    if(in_encoder)visit();
                    return encode(state,BattleActionResult{0,8,{}});
                });
            break;
        case 2:
            (void)subject.apply_native_deltas(7,subject.inspect().revision,deltas,
                [&](const auto& state,const auto&){
                    visit();return encode(state,BattleActionResult{0,0,{}});
                });
            break;
        case 3:
            (void)subject.poison_share(subject.inspect().revision,0,
                [&](const PoisonShareInput& input){
                    visit();return PoisonShareResult{input.target_current_max_hp/10,
                        static_cast<std::uint8_t>(input.target_current_max_hp%10)};
                });
            break;
        default:throw std::runtime_error("Unknown callback fence fixture operation");
        }
    };
    const std::array<std::pair<unsigned,bool>,6> boundaries{{
        {0,false},{0,true},{1,false},{1,true},{2,true},{3,false}}};
    for(const auto [outer,in_encoder]:boundaries)
    for(unsigned inner=0;inner<4;++inner)
    for(const bool catch_inner:{false,true}){
        auto subject=Battle::restore(initial),control=Battle::restore(initial);
        unsigned visits=0;bool inner_refused=false,outer_refused=false;
        try{
            invoke(subject,outer,in_encoder,[&]{
                ++visits;
                try{invoke(subject,inner,false,{});}
                catch(const std::logic_error&){inner_refused=true;if(!catch_inner)throw;}
            });
        }catch(const std::logic_error&){outer_refused=true;}
        require(visits==1&&inner_refused&&outer_refused&&subject.checkpoint()==initial,
            "Same Battle callback reentry committed, escaped outer poison or advanced RNG");
        // A failed transaction must release its fence, and retry must use the
        // exact unchanged checkpoint/RNG, including encoder-phase RNG draws.
        invoke(subject,outer,in_encoder,{});invoke(control,outer,in_encoder,{});
        require(subject.checkpoint()==control.checkpoint(),
            "Callback refusal retained a fence or changed a subsequent transaction");
    }
    {
        // Equal logical IDs are independent staged values, not a lock key.
        auto subject=Battle::restore(initial),other=Battle::restore(initial);
        auto subject_control=Battle::restore(initial),other_control=Battle::restore(initial);
        invoke(subject,0,false,[&]{invoke(other,0,false,{});});
        invoke(subject_control,0,false,{});invoke(other_control,0,false,{});
        require(subject.checkpoint()==subject_control.checkpoint()&&
                other.checkpoint()==other_control.checkpoint(),
            "Independent Battle copies with equal IDs were incorrectly fenced");
    }
    {
        auto first=Battle::restore(initial),second=Battle::restore(initial);
        auto first_control=Battle::restore(initial),second_control=Battle::restore(initial);
        bool nested_refused=false,outer_refused=false;
        try{
            invoke(first,0,false,[&]{
                invoke(second,0,true,[&]{
                    try{invoke(first,3,false,{});}
                    catch(const std::logic_error&){nested_refused=true;}
                });
            });
        }catch(const std::logic_error&){outer_refused=true;}
        invoke(second_control,0,true,{});
        require(nested_refused&&outer_refused&&first.checkpoint()==initial&&
                second.checkpoint()==second_control.checkpoint(),
            "A-to-B-to-A reentry missed the original owner or corrupted independent B");
        invoke(first,0,false,{});invoke(first_control,0,false,{});
        require(first.checkpoint()==first_control.checkpoint(),
            "Nested reentry did not unwind both callback fences before retry");
    }
}
}
int main(int argc,char** argv) {
    try {
        signed_endpoint_transaction_test();
        signed_hp_domain_transaction_test();
        callback_fence_transaction_test();
        LuaEngine lua(std::filesystem::path(GOD2_SOURCE_DIR)/"scripts",false);
        require(lua.initialize(),"Lua initialization failed");
        const Battle::Rule rule=[&](const CombatRuleInput& input){return lua.combat_damage(input);};
        if(argc==2) {
            sqlite3* raw=nullptr;
            const auto opened=sqlite3_open_v2(argv[1],&raw,SQLITE_OPEN_READONLY,nullptr);
            std::unique_ptr<sqlite3,decltype(&sqlite3_close)> db(raw,sqlite3_close);
            require(opened==SQLITE_OK,"Cannot read native checkpoint evidence");
            sqlite3_stmt* statement=nullptr;
            const auto prepared=sqlite3_prepare_v2(raw,"SELECT document FROM battle_checkpoints",-1,&statement,nullptr);
            std::unique_ptr<sqlite3_stmt,decltype(&sqlite3_finalize)> query(statement,sqlite3_finalize);
            require(prepared==SQLITE_OK && sqlite3_step(statement)==SQLITE_ROW,"Missing native checkpoint");
            const auto saved=BattleCheckpointCodec::decode(reinterpret_cast<const char*>(sqlite3_column_text(statement,0)));
            require(sqlite3_step(statement)==SQLITE_DONE,"Ambiguous native checkpoint evidence");
            validate_diagnostic_first_exchange(saved,1,rule);
        } else require(argc==1,"Expected optional read-only evidence database");
        {
            const std::array<BattleActor,2> pair{{
                {0,7,100,120,50,80,31,40,8,10},{14,0,150,150,0,0,20,25,13,6}}};
            Battle source(9,pair,123);
            source.act(7,1,{0,{14},true,150,100,8,0,150},rule,encode);
            source.act(0,2,{14,{0},false,100,100,0,0,150},rule,encode);
            const auto saved=source.checkpoint();
            validate_diagnostic_first_exchange(saved,7,rule);
            rejects([&]{validate_diagnostic_first_exchange(saved,8,rule);});
            auto changed=saved;changed.snapshot.actors[14]->physical_attack++;
            rejects([&]{validate_diagnostic_first_exchange(changed,7,rule);});
            changed=saved;changed.random_state=Battle(9,pair,124).checkpoint().random_state;
            (void)Battle::restore(changed);
            rejects([&]{validate_diagnostic_first_exchange(changed,7,rule);});
            changed=saved;changed.snapshot.revision++;
            rejects([&]{validate_diagnostic_first_exchange(changed,7,rule);});
            require(source.checkpoint()==saved,"Recovery validation mutated the source");
            source.act(7,3,{0,{14},true,150,100,8,0,150},rule,encode);
            const auto partial=source.checkpoint();
            rejects([&]{validate_diagnostic_exchange(partial,7,2,rule);});
            source.act(0,4,{14,{0},false,100,100,0,0,150},rule,encode);
            const auto second=source.checkpoint();
            require(second.snapshot.revision==5 && second.snapshot.actors[0]->hp==76 &&
                    second.snapshot.actors[0]->mp==34 && second.snapshot.actors[14]->hp==42,
                    "Second diagnostic exchange operands changed");
            validate_diagnostic_exchange(second,7,2,rule);
            rejects([&]{validate_diagnostic_first_exchange(second,7,rule);});
            rejects([&]{validate_diagnostic_exchange(saved,7,2,rule);});
            for(const auto boundary:{0u,3u,~0u})
                rejects([&]{validate_diagnostic_exchange(second,7,boundary,rule);});
            for(unsigned fault=0;fault<7;++fault) {
                changed=second;
                switch(fault) {
                case 0:--changed.snapshot.actors[0]->hp;break;
                case 1:--changed.snapshot.actors[0]->mp;break;
                case 2:++changed.snapshot.actors[14]->hp;break;
                case 3:++changed.snapshot.actors[14]->physical_defense;break;
                case 4:changed.random_state=saved.random_state;break;
                case 5:changed.snapshot.actors[0]->controller=8;break;
                case 6:changed.snapshot.revision=3;break;
                }
                rejects([&]{validate_diagnostic_exchange(changed,7,2,rule);});
            }
            auto restored=Battle::restore(BattleCheckpointCodec::decode(BattleCheckpointCodec::encode(second)));
            const BattleAction terminal{0,{14},true,150,100,8,0,150};
            require(source.act(7,5,terminal,rule,encode)==restored.act(7,5,terminal,rule,encode),
                    "Second exchange restore changed terminal wire");
            require(source.checkpoint()==restored.checkpoint() && !restored.active() &&
                    restored.inspect().actors[0]->mp==26 && restored.inspect().victorious_side==0,
                    "Second exchange restore changed settlement state or RNG");
            rejects([&]{validate_diagnostic_exchange(source.checkpoint(),7,2,rule);});
        }
        Battle battle(1,actors,123);
        const auto wire=battle.act(7,1,attack,rule,encode);
        const auto plain=RecoveredWorldFrame::decode(wire);
        require(plain && plain->size()==68,"Native diagnostic response invalid");
        require(battle.inspect().revision==2 && battle.inspect().actors[0]->mp==12 &&
                battle.inspect().actors[14]->hp==82 && battle.inspect().actors[15]->hp==82,
                "Multi-target transaction or single MP charge failed");
        rejects([&]{battle.act(7,1,attack,rule,encode);});
        rejects([&]{battle.act(8,2,attack,rule,encode);});
        const BattleAction retaliation{14,{0},false,100,100,0,0,150};
        battle.act(0,2,retaliation,rule,encode);
        require(battle.inspect().actors[0]->hp==88,"Server AI did not damage player");
        {
            const auto saved=battle.checkpoint();
            const auto document=BattleCheckpointCodec::encode(saved);
            require(BattleCheckpointCodec::decode(document)==saved,"Checkpoint codec lost state");
            auto restored=Battle::restore(BattleCheckpointCodec::decode(document));
            for(unsigned fault=0;fault<12;++fault) {
                auto bad=nlohmann::json::parse(document);
                switch(fault) {
                case 0:bad["version"]=2;break;
                case 1:bad["engine"]="other-runtime";break;
                case 2:bad["design_id"]="NATIVE_VERIFIED";break;
                case 3:bad["id"]=-1;break;
                case 4:bad["revision"]=1.5;break;
                case 5:bad["winner"]=256;break;
                case 6:bad["actors"][0][0]=256;break;
                case 7:bad["actors"][0][2]=4294967296ULL;break;
                case 8:bad["actors"][0][1]=true;break;
                case 9:bad["actors"].erase(0);break;
                case 10:bad.erase("rng");break;
                case 11:bad["extra"]=1;break;
                }
                rejects([&]{BattleCheckpointCodec::decode(bad.dump());});
            }
            rejects([&]{BattleCheckpointCodec::decode(document.substr(0,document.size()-1));});
            rejects([&]{BattleCheckpointCodec::decode(std::string(32769,' '));});
            rejects([&]{BattleCheckpointCodec::decode("{\"id\":1,"+document.substr(1));});
            rejects([&]{BattleCheckpointCodec::decode("[[[[[[[[0]]]]]]]]");});
            for(std::size_t length=0;length<document.size();length+=97)
                rejects([&]{BattleCheckpointCodec::decode(document.substr(0,length));});
            auto wide=saved;wide.snapshot.id=9007199254740993ULL;
            wide.snapshot.actors[0]->controller=18446744073709551615ULL;
            require(BattleCheckpointCodec::decode(BattleCheckpointCodec::encode(wide))==wide,
                    "Checkpoint rounded a64-bit identity");
            require(restored.checkpoint()==saved,"Checkpoint changed state or RNG");
            auto original=battle;
            auto next=attack;next.mp_cost=0;next.critical_chance_bp=5000;
            std::vector<std::uint32_t> original_rolls,restored_rolls;
            const Battle::Rule original_rule=[&](const auto& input){original_rolls.push_back(input.roll);return rule(input);};
            const Battle::Rule restored_rule=[&](const auto& input){restored_rolls.push_back(input.roll);return rule(input);};
            for(unsigned step=0;step<3 && original.active();++step) {
                require(original.act(7,original.inspect().revision,next,original_rule,encode)==
                        restored.act(7,restored.inspect().revision,next,restored_rule,encode),"Restored wire differs");
                require(original.checkpoint()==restored.checkpoint(),"Restored continuation diverged");
            }
            require(!original_rolls.empty() && original_rolls==restored_rolls,"Restore rerolled critical checks");
            for(unsigned fault=0;fault<12;++fault) {
                auto bad=saved;
                switch(fault) {
                case 0:bad.version=2;break;
                case 1:bad.snapshot.id=0;break;
                case 2:bad.snapshot.revision=0;break;
                case 3:bad.snapshot.actors[0]->position=1;break;
                case 4:bad.snapshot.actors[0]->hp=101;break;
                case 5:bad.snapshot.victorious_side=0;break;
                case 6:bad.snapshot.state=BattleState::Pending;break;
                case 7:bad.random_state="1 2";break;
                case 8:bad.random_state+=" trailing";break;
                case 9:bad.random_state=std::string(10001,'0');break;
                case 10:bad.snapshot.actors[14].reset();bad.snapshot.actors[15].reset();break;
                case 11:bad.random_state.replace(bad.random_state.rfind(' ')+1,std::string::npos,"4294967296");break;
                }
                rejects([&]{Battle::restore(bad);});
            }
            require(battle.checkpoint()==saved,"Rejected restore changed original");
        }
        for(unsigned bad=0;bad<8;++bad) {
            auto action=attack;
            switch(bad) {
            case 0:action.targets={14,14};break;
            case 1:action.targets={0};break;
            case 2:action.targets={27};break;
            case 3:action.targets={28};break;
            case 4:action.source=28;break;
            case 5:action.mp_cost=13;break;
            case 6:action.targets={};break;
            case 7:action.power_percent=10001;break;
            }
            rejects([&]{battle.act(7,3,action,rule,encode);});
            require(battle.inspect().revision==3 && battle.inspect().actors[0]->mp==12,
                    "Invalid command changed state");
        }
        // A late rule or encoder failure must roll back both earlier targets and RNG.
        for(unsigned failure=0;failure<4;++failure) {
            Battle subject(2,actors,987), control(2,actors,987);
            auto action=attack;action.critical_chance_bp=5000;
            unsigned calls=0;
            Battle::Rule failed=[&](const CombatRuleInput& input) {
                if(++calls==2 && failure==0) throw std::runtime_error("Second target fault");
                auto value=rule(input);
                if(failure==1) ++value.mp_cost;
                return value;
            };
            Battle::Encode failed_encode=[&](const auto& state,const auto& result) {
                if(failure==2) throw std::runtime_error("Encoding fault");
                if(failure==3) return std::vector<std::uint8_t>{};
                return encode(state,result);
            };
            rejects([&]{subject.act(7,1,action,failed,failed_encode);});
            require(subject.inspect().revision==1 && subject.inspect().actors[0]->mp==20 &&
                    subject.inspect().actors[14]->hp==100,"Failed transaction changed state");
            std::vector<std::uint32_t> retried_rolls,control_rolls;
            auto capture=[&](auto& rolls) -> Battle::Rule {
                return [&](const CombatRuleInput& input){rolls.push_back(input.roll);return rule(input);};
            };
            require(subject.act(7,1,action,capture(retried_rolls),encode)==
                    control.act(7,1,action,capture(control_rolls),encode),"Retry result changed");
            require(retried_rolls==control_rolls && retried_rolls.size()==2,"RNG advanced on failure");
        }
        Battle magic(3,actors,1);
        auto spell=attack;spell.magical=true;
        magic.act(7,1,spell,rule,encode);
        require(magic.inspect().actors[14]->hp==66,"Magical stat selection failed");
        auto lethal=attack;lethal.power_percent=10000;lethal.mp_cost=0;
        std::uint32_t applied=0;
        magic.act(7,2,lethal,rule,[&](const auto& state,const auto& result) {
            for(const auto& hit:result.hits) applied+=hit.hp_loss;
            return encode(state,result);
        });
        require(!magic.active() && applied==132 && magic.inspect().actors[14]->hp==0,
                "Lethal clipping or terminal state failed");
        require(magic.inspect().victorious_side==0,"Player side victory missing");
        Battle defeat(31,actors,1);
        require(!defeat.inspect().victorious_side,"Active battle declared a winner");
        auto enemy_lethal=lethal;enemy_lethal.source=14;enemy_lethal.targets={0};
        rejects([&]{defeat.act(0,1,enemy_lethal,rule,[](const auto& state,const auto&) -> std::vector<std::uint8_t> {
            require(state.victorious_side==1,"Staged enemy victory missing");
            throw std::runtime_error("Terminal outcome encoding failed");
        });});
        require(defeat.active() && !defeat.inspect().victorious_side && defeat.inspect().revision==1,
                "Failed terminal response published a winner");
        defeat.act(0,1,enemy_lethal,rule,encode);
        require(!defeat.active() && defeat.inspect().victorious_side==1 && defeat.inspect().actors[0]->hp==0,
                "Enemy victory confused with player victory");
        auto restored_defeat=Battle::restore(BattleCheckpointCodec::decode(BattleCheckpointCodec::encode(defeat.checkpoint())));
        require(restored_defeat.checkpoint()==defeat.checkpoint(),"Terminal checkpoint lost winner");
        rejects([&]{restored_defeat.act(0,restored_defeat.inspect().revision,enemy_lethal,rule,encode);});
        std::vector<BattleActor> team(actors.begin(),actors.end());
        auto ally=actors[0];ally.position=1;team.push_back(ally);
        Battle partial_defeat(32,team,1);
        partial_defeat.act(0,1,enemy_lethal,rule,encode);
        require(partial_defeat.active() && !partial_defeat.inspect().victorious_side &&
                partial_defeat.inspect().actors[0]->hp==0 && partial_defeat.inspect().actors[1]->hp>0,
                "One defeated party member incorrectly ended the battle");
        enemy_lethal.targets={1};
        partial_defeat.act(0,2,enemy_lethal,rule,encode);
        require(!partial_defeat.active() && partial_defeat.inspect().victorious_side==1,
                "Full party elimination did not identify opposing winner");
        rejects([&]{magic.act(7,3,attack,rule,encode);});
        rejects([&]{Battle invalid(0,actors,1);});
        auto duplicates=actors;duplicates[1].position=0;
        rejects([&]{Battle invalid(1,duplicates,1);});
        auto same_side=actors;same_side[1].position=1;same_side[2].position=2;
        rejects([&]{Battle invalid(1,same_side,1);});
        std::cout<<"Battle/Lua atomic actions, retaliation, rollback and native framing passed\n";
    } catch(const std::exception& error) {std::cerr<<error.what()<<'\n';return 1;}
}
