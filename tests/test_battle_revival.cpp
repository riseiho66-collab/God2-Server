#include "game/Battle.h"
#include "scripting/LuaEngine.h"
#include "handlers/RecoveredBattleService.h"
#include "game/RevivalRecoveryCodec.h"
#include "protocol/DiagnosticBattleRevival.h"
#include <iomanip>
#include <iostream>
#include <limits>
#include <source_location>

using namespace god2;
static void require(bool value,const std::source_location where=std::source_location::current()) {
    if(!value) throw std::runtime_error("Revival invariant failed at line "+std::to_string(where.line()));
}
template<class F> static void rejects(F f) {
    bool failed=false;try { f(); } catch(const std::exception&) { failed=true; }
    require(failed);
}
int main(int argc,char** argv) {
    try {
        if(argc==2 && std::string_view(argv[1])=="--resume") {
            std::string document;char byte;
            while(std::cin.get(byte)) {
                if(document.size()==65536) throw std::invalid_argument("Recovery input size limit");
                document.push_back(byte);
            }
            const auto recovery=RevivalRecoveryCodec::decode(document);
            for(auto value:diagnostic_revival_resume_participants(recovery.character,recovery))
                std::cout<<std::hex<<std::setfill('0')<<std::setw(2)<<unsigned(value);
            return 0;
        }
        if(argc==2 && std::string_view(argv[1])=="--seed") {
            for(auto byte:diagnostic_revival_skill_seed())
                std::cout<<std::hex<<std::setfill('0')<<std::setw(2)<<unsigned(byte);
            return 0;
        }
        if(argc==2 && std::string_view(argv[1])=="--effect") {
            for(auto byte:diagnostic_revival_effect(0,1))
                std::cout<<std::hex<<std::setfill('0')<<std::setw(2)<<unsigned(byte);
            return 0;
        }
        LuaEngine lua(std::filesystem::path(GOD2_SOURCE_DIR)/"scripts",false);
        {
            const std::array<BattleActor,3> saved_actors{{
                {0,9,100,120,14,80,31,40,8,10},{1,0,1,120,5,20,31,40,8,10},
                {14,0,132,150,0,0,20,25,13,6}}};
            auto checkpoint=Battle(99,saved_actors,123).checkpoint();checkpoint.snapshot.revision=4;
            RevivalRecovery recovery{1,7,9,checkpoint,true,true,true,true,true};
            const auto bytes=diagnostic_revival_resume_participants(9,recovery);
            require(bytes.size()==375 && bytes[358]==0x86 && bytes[359]==5);
            const auto bulk=RecoveredBattleVitalsBatch::parse_logical(std::span<const std::uint8_t>(bytes).subspan(237,121));
            require(bulk && bulk->at(0)->mp==14 && bulk->at(1)->hp==1);
            for(unsigned mutation=0;mutation<10;++mutation) {
                auto invalid=recovery;
                switch(mutation) {
                case 0:invalid.version=2;break;
                case 1:invalid.account=0;break;
                case 2:invalid.character=8;break;
                case 3:invalid.initial_control_received=false;break;
                case 4:invalid.opening_received=false;break;
                case 5:invalid.action_received=false;break;
                case 6:invalid.control_received=false;break;
                case 7:invalid.opening_notice=false;break;
                case 8:invalid.battle.snapshot.revision=3;break;
                case 9:invalid.battle.snapshot.actors[14]->hp=0;break;
                }
                rejects([&]{diagnostic_revival_resume_participants(9,invalid);});
            }
            require(recovery.battle==checkpoint);
            recovery.battle.snapshot.revision=5;recovery.battle.snapshot.actors[14]->hp=114;
            require(diagnostic_revival_resume_participants(9,recovery).size()==375);
            recovery.battle.snapshot.revision=std::numeric_limits<std::uint64_t>::max()-1;
            rejects([&]{diagnostic_revival_resume_participants(9,recovery);});
        }
        require(lua.initialize());
        auto rule=[&](const RevivalInput& input) { return lua.revival(input); };
        for(const auto maximum:{1u,120u,1'000'000u}) require(rule({maximum})==RevivalResult{1,66});
        rejects([&]{rule({0});});rejects([&]{rule({1'000'001});});
        const std::array<BattleActor,4> actors{{
            {0,9,100,120,80,80,31,40,8,10}, {1,99,4,120,5,20,31,40,8,10},
            {14,0,100,100,0,0,20,25,13,6}, {15,0,100,100,0,0,20,25,13,6}}};
        Battle battle(1,actors,123);
        {
            const std::array<BattleActor,3> setup_actors{actors[0],actors[1],actors[2]};
            Battle setup(2,setup_actors,123);
            const auto before=setup.checkpoint();
            rejects([&]{diagnostic_revival_death_setup(9,setup,{});});
            require(setup.checkpoint()==before);
            const auto bytes=diagnostic_revival_death_setup(9,setup,
                [&](const CombatRuleInput& input){return lua.combat_damage(input);});
            require(bytes.size()==528 && bytes[375]==0x83 && bytes[377]==14 && bytes[380]==2);
            require(bytes[407]==0x88 && bytes[420]==0 && bytes[424]==5);
            require(bytes[378]==0);
            require(bytes[387]==0 && bytes[390]==0x86 && bytes[392]==1 && bytes[399]==0);
            require(bytes[358]==0x86 && bytes[359]==5);
            require(setup.inspect().revision==2 && setup.inspect().actors[1]->hp==0 && setup.active());
            require(setup.inspect().actors[0]->mp==80);
            rejects([&]{diagnostic_revival_death_setup(9,setup,
                [&](const CombatRuleInput& input){return lua.combat_damage(input);});});
        }
        battle.act(0,1,{14,{1},false,100,100,0,0,150},
            [&](const CombatRuleInput& input){return lua.combat_damage(input);},
            [](const auto&,const auto&){return std::vector<std::uint8_t>{1};});
        const auto baseline=battle.checkpoint();
        require(battle.active() && baseline.snapshot.actors[1]->hp==0);
        {
            auto setup=baseline.snapshot;setup.actors[15].reset();
            const auto bytes=diagnostic_revival_participants(9,setup);
            require(bytes.size()==375);
            require(bytes[17]==0x1c && bytes[18]==0 && bytes[20]==9);
            require(bytes[96]==0x1c && bytes[97]==1);
            require(bytes[175]==0x1c && bytes[176]==14);
            const auto bulk=RecoveredBattleVitalsBatch::parse_logical(
                std::span<const std::uint8_t>(bytes).subspan(237,121));
            require(bulk && bulk->at(0)->hp==100 && bulk->at(0)->mp==80 &&
                bulk->at(1)->hp==0 && bulk->at(1)->mp==5);
            require(bytes[358]==0x86 && bytes[359]==5);
            const auto wire=RecoveredWorldFrame::encode(bytes);
            require(RecoveredWorldFrame::decode(wire)==bytes);
            rejects([&]{diagnostic_revival_participants(8,setup);});
            rejects([&]{diagnostic_revival_participants(9,baseline.snapshot);});
            auto invalid=setup;invalid.actors[1]->position=2;
            rejects([&]{diagnostic_revival_participants(9,invalid);});
            invalid=setup;invalid.actors[1]->hp=121;
            rejects([&]{diagnostic_revival_participants(9,invalid);});
            invalid=setup;invalid.actors[0]->hp=0;
            rejects([&]{diagnostic_revival_participants(9,invalid);});
            invalid=setup;invalid.actors[14]->hp=0;
            rejects([&]{diagnostic_revival_participants(9,invalid);});
        }
        unsigned encodes=0;
        auto encode=[&](const BattleSnapshot& state,const BattleRevivalResult& result) {
            ++encodes;
            require(state.actors[0]->mp==14 && state.actors[1]->hp==1 && state.actors[1]->mp==5);
            require(result.source==0 && result.target==1 && result.hp_gain==1 && result.mp_cost==66);
            return std::vector<std::uint8_t>{1}; // Not a native packet acceptance test.
        };
        rejects([&]{battle.revive(8,2,0,1,rule,encode);});
        rejects([&]{battle.revive(9,1,0,1,rule,encode);});
        for(auto target:{0,2,14,28}) rejects([&]{battle.revive(9,2,0,static_cast<std::uint8_t>(target),rule,encode);});
        rejects([&]{battle.revive(99,2,1,0,rule,encode);});
        rejects([&]{battle.revive(9,2,28,1,rule,encode);});
        for(const auto output:{RevivalResult{0,66},{121,66},{1,0},{1,1'000'001}})
            rejects([&]{battle.revive(9,2,0,1,[&](auto){return output;},encode);});
        rejects([&]{battle.revive(9,2,0,1,{},encode);});
        rejects([&]{battle.revive(9,2,0,1,rule,{});});
        rejects([&]{battle.revive(9,2,0,1,[](auto)->RevivalResult {throw std::runtime_error("rule fault");},encode);});
        rejects([&]{battle.revive(9,2,0,1,rule,[](const auto&,const auto&)->std::vector<std::uint8_t>{throw std::runtime_error("encode fault");});});
        rejects([&]{battle.revive(9,2,0,1,rule,[](const auto&,const auto&){return std::vector<std::uint8_t>{};});});
        require(encodes==0 && battle.checkpoint()==baseline);
        auto low=baseline;low.snapshot.actors[0]->mp=65;
        auto insufficient=Battle::restore(low);
        bool refused=false;
        try { insufficient.revive(9,2,0,1,rule,encode); }
        catch(const InsufficientBattleMp& e) { refused=e.available==65 && e.required==66; }
        require(refused && insufficient.checkpoint()==low && encodes==0);
        auto exact=baseline;exact.snapshot.actors[0]->mp=66;
        auto last_mp=Battle::restore(exact);
        last_mp.revive(9,2,0,1,rule,[](const auto& state,const auto&) {
            require(state.actors[0]->mp==0 && state.actors[1]->hp==1);
            return std::vector<std::uint8_t>{1};
        });
        auto mirrored=baseline;
        for(unsigned slot=0;slot<14;++slot) std::swap(mirrored.snapshot.actors[slot],mirrored.snapshot.actors[slot+14]);
        for(unsigned slot=0;slot<28;++slot) if(mirrored.snapshot.actors[slot])
            mirrored.snapshot.actors[slot]->position=static_cast<std::uint8_t>(slot);
        auto right_side=Battle::restore(mirrored);
        right_side.revive(9,2,14,15,rule,[](const auto& state,const auto& result) {
            require(state.actors[14]->mp==14 && state.actors[15]->hp==1 && result.source==14 && result.target==15);
            return std::vector<std::uint8_t>{1};
        });
        auto enemy=baseline;enemy.snapshot.actors[14]->hp=0;
        auto hostile=Battle::restore(enemy);
        rejects([&]{hostile.revive(9,2,0,14,rule,encode);});
        require(hostile.checkpoint()==enemy);
        auto finished=baseline;finished.snapshot.actors[0]->hp=0;
        finished.snapshot.state=BattleState::Finished;finished.snapshot.victorious_side=1;
        auto eliminated=Battle::restore(finished);
        rejects([&]{eliminated.revive(9,2,0,1,rule,encode);});
        require(eliminated.checkpoint()==finished);
        auto overflow=baseline;overflow.snapshot.revision=std::numeric_limits<std::uint64_t>::max();
        auto exhausted=Battle::restore(overflow);
        rejects([&]{exhausted.revive(9,overflow.snapshot.revision,0,1,rule,encode);});
        require(exhausted.checkpoint()==overflow);
        require(!battle.revive(9,2,0,1,rule,encode).empty());
        auto expected=baseline;expected.snapshot.revision=3;
        expected.snapshot.actors[0]->mp=14;expected.snapshot.actors[1]->hp=1;
        require(encodes==1 && battle.checkpoint()==expected);
        rejects([&]{battle.revive(9,2,0,1,rule,encode);});
        rejects([&]{battle.revive(9,3,0,1,rule,encode);});
        require(encodes==1 && battle.checkpoint()==expected);
        auto restored=Battle::restore(expected);
        restored.act(99,3,{1,{14},false,100,100,0,0,150},
            [&](const CombatRuleInput& input){return lua.combat_damage(input);},
            [](const auto&,const auto&){return std::vector<std::uint8_t>{1};});
        require(restored.inspect().actors[14]->hp<100 && restored.inspect().revision==4);
        require(lua.reload_all() && rule({120})==RevivalResult{1,66});
        {
            asio::io_context io;
            auto session=std::make_shared<Session>(asio::ip::tcp::socket(io),io.get_executor(),1,false,
                Session::PacketHandler{},Session::DisconnectHandler{});
            session->account_id=7;session->character_id=9;session->set_state(SessionState::InBattle);
            RecoveredBattleService service([&](auto input){return lua.combat_damage(input);});
            RecoveredBattleService::Policy policy{0,0,0,0,{0,{},false,100,100,0,0,150},{}};
            policy.diagnostic_single_action=true;
            policy.diagnostic_player_initial_control=true;
            bool bad_wire=true,commit_fails=true;
            unsigned commits=0;
            policy.diagnostic_revival=RecoveredBattleService::DiagnosticRevival{rule,
                [&](const auto& state,const auto& result) {
                    auto wire=diagnostic_revival_reply(state,result);
                    if(bad_wire) wire.back()^=1;
                    return wire;
                },true};
            service.bind(*session,Battle::restore(baseline),policy,
                [](const auto&,const auto&){return RecoveredWorldFrame::encode(std::array<std::uint8_t,2>{0x30,0});}, {},
                [&](const auto& before,const auto& after) {
                    require(before==baseline && after==expected);++commits;
                    if(commit_fails) throw std::runtime_error("commit fault");
                });
            const std::array<std::uint8_t,17> raw{0x35,0,3,0,0xa5,2,0,0,0,0,0,0,0,8,3,0,0};
            std::array<std::uint8_t,34> opening{};
            opening[0]=opening[17]=0x35;opening[2]=2;opening[19]=11;opening[5]=opening[22]=1;
            const auto notice=*RecoveredWorldRecords::decode(opening);
            require(!service.handle(*session,notice));
            std::array<std::uint8_t,17> initial{0x35,0,11};
            require(service.handle(*session,*RecoveredWorldRecords::decode(initial)).has_value());
            auto wrong=opening;wrong[5]=2;
            require(!service.handle(*session,*RecoveredWorldRecords::decode(wrong)));
            const auto accepted_notice=service.handle(*session,notice);
            require(accepted_notice && service.inspect(1)==baseline.snapshot && commits==0);
            const auto grant=RecoveredWorldFrame::decode(*accepted_notice);
            require(grant && grant->size()==17 && (*grant)[0]==0x86 && (*grant)[1]==5 && (*grant)[3]==1 && (*grant)[4]==0);
            require(!service.handle(*session,notice));
            const auto command=*RecoveredWorldRecords::decode(raw);
            rejects([&]{service.handle(*session,command);});
            require(commits==0 && service.inspect(1)==baseline.snapshot);
            bad_wire=false;
            rejects([&]{service.handle(*session,command);});
            require(commits==1 && service.inspect(1)==baseline.snapshot);
            for(const auto offset:{1,3,9,13}) {
                auto invalid=raw;invalid[offset]^=1;
                const auto records=RecoveredWorldRecords::decode(invalid);
                require(records && !service.handle(*session,*records));
            }
            auto continuation=raw;continuation[2]=0x83;
            require(!service.handle(*session,*RecoveredWorldRecords::decode(continuation)));
            auto mixed=command;mixed.emplace_back(RecoveredWorldRecords::Tick{});
            require(!service.handle(*session,mixed));
            commit_fails=false;
            const auto reply=service.handle(*session,command);
            require(reply && service.inspect(1)==expected.snapshot && commits==2);
            const auto logical=RecoveredWorldFrame::decode(*reply);
            require(logical && logical->size()==170 && (*logical)[0]==0x86 && (*logical)[1]==1 &&
                    (*logical)[17]==0x83 && (*logical)[31]==27 && (*logical)[32]==0x86 && (*logical)[41]==1);
            require((*logical)[49]==0x88 && (*logical)[50]==1 && (*logical)[58]==14 && (*logical)[62]==1 && (*logical)[66]==5);
            require(!service.handle(*session,command) && commits==2);
            require(!service.diagnostic_round_ready(*session));
            const auto pending_phase=service.checkpoint_revival(*session);
            require(pending_phase.action_received && !pending_phase.control_received &&
                    pending_phase.initial_control_received && pending_phase.opening_received);
            std::array<std::uint8_t,17> receipt{0x35,0,0x0b,0,0,1};
            require(service.handle(*session,*RecoveredWorldRecords::decode(receipt)).has_value());
            require(service.diagnostic_round_ready(*session));
            require(!service.release_finished_diagnostic(*session));
            const auto ready_phase=service.checkpoint_revival(*session);
            require(ready_phase.action_received && ready_phase.control_received);
            for(const auto& phase:{pending_phase,ready_phase}) {
                const auto document=RevivalRecoveryCodec::encode(phase);
                require(RevivalRecoveryCodec::decode(document)==phase);
                rejects([&]{RevivalRecoveryCodec::decode(BattleCheckpointCodec::encode(phase.battle));});
                rejects([&]{RevivalRecoveryCodec::decode(document+" ");});
                rejects([&]{RevivalRecoveryCodec::decode(document.substr(0,document.size()-1));});
                rejects([&]{RevivalRecoveryCodec::decode(std::string(65537,' '));});
                const auto json=nlohmann::json::parse(document);
                for(const auto* field:{"account","character","battle","initial","opening","action","control","version"}) {
                    auto missing=json;missing.erase(field);
                    rejects([&]{RevivalRecoveryCodec::decode(missing.dump());});
                }
                for(const auto bad:{nlohmann::json(0),nlohmann::json("true"),nlohmann::json(nullptr)}) {
                    auto changed=json;changed["action"]=bad;
                    rejects([&]{RevivalRecoveryCodec::decode(changed.dump());});
                }
                for(const auto bad:{nlohmann::json(-1),nlohmann::json(1.5),nlohmann::json("7"),nlohmann::json(0)}) {
                    auto changed=json;changed["account"]=bad;
                    rejects([&]{RevivalRecoveryCodec::decode(changed.dump());});
                }
                auto wrong_owner=phase;++wrong_owner.character;
                rejects([&]{RevivalRecoveryCodec::encode(wrong_owner);});
                auto invalid_flags=phase;invalid_flags.action_received=false;invalid_flags.control_received=true;
                rejects([&]{RevivalRecoveryCodec::encode(invalid_flags);});
                RecoveredBattleService recovered([&](auto input){return lua.combat_damage(input);});
                recovered.bind(*session,Battle::restore(phase.battle),policy,
                    [](const auto&,const auto&){return RecoveredWorldFrame::encode(std::array<std::uint8_t,2>{0x30,0});});
                for(unsigned mutation=0;mutation<7;++mutation) {
                    auto invalid=phase;
                    switch(mutation) {
                    case 0:++invalid.version;break;
                    case 1:++invalid.account;break;
                    case 2:++invalid.character;break;
                    case 3:++invalid.battle.snapshot.revision;break;
                    case 4:invalid.opening_notice=false;break;
                    case 5:invalid.action_received=false;invalid.control_received=true;break;
                    case 6:invalid.initial_control_received=false;break;
                    }
                    rejects([&]{recovered.restore_revival_phase(*session,invalid);});
                    require(recovered.inspect(1)==phase.battle.snapshot &&
                            !recovered.checkpoint_revival(*session).action_received);
                }
                recovered.restore_revival_phase(*session,RevivalRecoveryCodec::decode(document));
                rejects([&]{recovered.restore_revival_phase(*session,phase);});
                require(!recovered.handle(*session,command));
                require(!recovered.handle(*session,notice));
                const std::array<std::uint8_t,17> basic{0x35,0,1,0,0,0,0,1};
                require(!recovered.handle(*session,*RecoveredWorldRecords::decode(basic)));
                require(recovered.diagnostic_round_ready(*session)==phase.control_received);
                if(phase.control_received) {
                    recovered.expect_revival_reconnect_notice(*session);
                    rejects([&]{recovered.expect_revival_reconnect_notice(*session);});
                    require(!recovered.diagnostic_round_ready(*session));
                    rejects([&]{recovered.rearm_diagnostic(*session,phase.battle.snapshot.revision);});
                    const auto before_notice=recovered.checkpoint_revival(*session);
                    const std::array<std::uint8_t,17> reconnect{0x35,0,0x0b};
                    for(const auto offset:{1,3,5,7,9,13}) {
                        auto wrong=reconnect;wrong[offset]=2;
                        const auto decoded=RecoveredWorldRecords::decode(wrong);
                        require(!decoded || !recovered.handle(*session,*decoded));
                        require(recovered.checkpoint_revival(*session)==before_notice);
                    }
                    const auto decoded=*RecoveredWorldRecords::decode(reconnect);
                    auto mixed=decoded;mixed.insert(mixed.end(),decoded.begin(),decoded.end());
                    require(!recovered.handle(*session,mixed));
                    const auto response=recovered.handle(*session,decoded);
                    require(response && response->empty());
                    require(!recovered.handle(*session,decoded));
                    rejects([&]{recovered.expect_revival_reconnect_notice(*session);});
                    const std::array<std::uint8_t,17> opening{0x35,0,2,0,0,1};
                    for(const auto offset:{1,3,5,7,9,13}) {
                        auto wrong=opening;wrong[offset]^=2;
                        const auto parsed=RecoveredWorldRecords::decode(wrong);
                        require(!parsed || !recovered.handle(*session,*parsed));
                    }
                    const auto opening_records=*RecoveredWorldRecords::decode(opening);
                    const auto opening_response=recovered.handle(*session,opening_records);
                    require(opening_response && opening_response->empty());
                    require(!recovered.handle(*session,opening_records));
                    require(recovered.checkpoint_revival(*session)==before_notice);
                } else {
                    rejects([&]{recovered.expect_revival_reconnect_notice(*session);});
                }
                const auto accepted=recovered.handle(*session,*RecoveredWorldRecords::decode(receipt));
                require(accepted.has_value()!=phase.control_received);
                require(recovered.diagnostic_round_ready(*session));
                require(recovered.inspect(1)==phase.battle.snapshot);
                recovered.rearm_diagnostic(*session,phase.battle.snapshot.revision);
                require(!recovered.checkpoint_revival(*session).action_received &&
                        !recovered.checkpoint_revival(*session).control_received);
                require(recovered.handle(*session,*RecoveredWorldRecords::decode(basic)).has_value());
            }
            // CUSTOM-0017: qualify the captured post-revival basic/receipt
            for(const std::uint64_t saved_revision:{4,5}) {
                auto saved=service.checkpoint_revival(*session);
                saved.battle.snapshot.revision=saved_revision;
                saved.battle.snapshot.actors[14]->hp=saved_revision==4 ? 132 : 114;
                saved.battle.snapshot.actors[14]->max_hp=150;
                saved.action_received=true;saved.control_received=true;
                RecoveredBattleService resumed([&](auto input){return lua.combat_damage(input);});
                resumed.bind(*session,Battle::restore(saved.battle),policy,
                    [](const auto&,const auto&){return RecoveredWorldFrame::encode(std::array<std::uint8_t,2>{0x30,0});});
                resumed.restore_revival_phase(*session,saved);
                resumed.expect_revival_reconnect_notice(*session);
                for(const auto bytes:{std::array<std::uint8_t,17>{0x35,0,0x0b},
                                      std::array<std::uint8_t,17>{0x35,0,2,0,0,1}})
                    require(resumed.handle(*session,*RecoveredWorldRecords::decode(bytes)).has_value());
                resumed.rearm_diagnostic(*session,saved_revision);
                const std::array<std::uint8_t,17> basic{0x35,0,1,0,0,0,0,1};
                require(resumed.handle(*session,*RecoveredWorldRecords::decode(basic)).has_value());
                require(resumed.inspect(1).revision==saved_revision+1);
                require(!resumed.handle(*session,*RecoveredWorldRecords::decode(receipt)));
                const std::array<std::uint8_t,17> new_receipt{0x35,0,0x0b,0,0,0,0,1};
                require(resumed.handle(*session,*RecoveredWorldRecords::decode(new_receipt)).has_value());
                require(!resumed.handle(*session,*RecoveredWorldRecords::decode(new_receipt)));
                require(resumed.diagnostic_round_ready(*session));
                resumed.rearm_diagnostic(*session,saved_revision+1);
                require(resumed.handle(*session,*RecoveredWorldRecords::decode(basic)).has_value());
                require(resumed.inspect(1).revision==saved_revision+2);
                require(!resumed.handle(*session,*RecoveredWorldRecords::decode(new_receipt)));
                require(resumed.handle(*session,*RecoveredWorldRecords::decode(receipt)).has_value());
                require(!resumed.handle(*session,*RecoveredWorldRecords::decode(receipt)));
            }
            // Same-connection followup remains independently qualified.
            {
                auto saved=service.checkpoint_revival(*session);
                saved.battle.snapshot.actors[14]->hp=1;
                saved.battle.snapshot.actors[15].reset();
                saved.action_received=true;saved.control_received=true;
                unsigned action_commits=0,phase_commits=0;
                RecoveredBattleService terminal([&](auto input){return lua.combat_damage(input);});
                terminal.bind(*session,Battle::restore(saved.battle),policy,
                    [](const auto&,const auto&){return RecoveredWorldFrame::encode(std::array<std::uint8_t,2>{0x30,0});},{},
                    [&](const auto&,const auto& after){require(after.snapshot.state==BattleState::Finished);++action_commits;});
                terminal.restore_revival_phase(*session,saved);
                terminal.set_revival_phase_commit(*session,[&](const auto&,const auto&){++phase_commits;});
                terminal.expect_revival_reconnect_notice(*session);
                for(const auto bytes:{std::array<std::uint8_t,17>{0x35,0,0x0b},
                                      std::array<std::uint8_t,17>{0x35,0,2,0,0,1}})
                    require(terminal.handle(*session,*RecoveredWorldRecords::decode(bytes)).has_value());
                terminal.rearm_diagnostic(*session,saved.battle.snapshot.revision);
                require(phase_commits==1);
                const std::array<std::uint8_t,17> basic{0x35,0,1,0,0,0,0,1};
                require(terminal.handle(*session,*RecoveredWorldRecords::decode(basic)).has_value());
                require(action_commits==1 && terminal.inspect(1).state==BattleState::Finished);
                require(!terminal.release_finished_diagnostic(*session));
                const std::array<std::uint8_t,17> final_receipt{0x35,0,0x0b,0,0,0,0,1};
                require(terminal.handle(*session,*RecoveredWorldRecords::decode(final_receipt)).has_value());
                require(phase_commits==1 && action_commits==1);
                require(!terminal.handle(*session,*RecoveredWorldRecords::decode(final_receipt)));
                require(terminal.release_finished_diagnostic(*session));
                require(session->state()==SessionState::InWorld);
                session->set_state(SessionState::InBattle);
            }
            // separately from the fault-injected revival commit callback above.
            RecoveredBattleService followup([&](auto input){return lua.combat_damage(input);});
            followup.bind(*session,Battle::restore(expected),policy,
                [](const auto&,const auto&){return RecoveredWorldFrame::encode(std::array<std::uint8_t,2>{0x30,0});});
            const auto receipt_records=*RecoveredWorldRecords::decode(receipt);
            require(!followup.handle(*session,receipt_records));
            const std::array<std::uint8_t,17> basic{0x35,0,1,0,0,0,0,1,0,0,0,0,0,0xd0,0xcc,0x8f,0x37};
            const auto basic_records=*RecoveredWorldRecords::decode(basic);
            require(followup.handle(*session,basic_records).has_value());
            const auto after_basic=followup.inspect(1);
            require(after_basic.revision==4 && after_basic.actors[14]->hp<expected.snapshot.actors[14]->hp);
            require(after_basic.actors[0]->mp==14 && after_basic.actors[1]->hp==1);
            require(!followup.diagnostic_round_ready(*session));
            for(const auto offset:{1,3,5,7,9}) {
                auto invalid=receipt;invalid[offset]^=2;
                const auto decoded=RecoveredWorldRecords::decode(invalid);
                require(!decoded || !followup.handle(*session,*decoded));
                require(followup.inspect(1)==after_basic);
            }
            require(followup.handle(*session,receipt_records).has_value());
            require(followup.diagnostic_round_ready(*session));
            require(!followup.handle(*session,receipt_records));
            require(!followup.handle(*session,basic_records));
            require(followup.inspect(1)==after_basic);
            followup.rearm_diagnostic(*session,after_basic.revision);
            require(!followup.diagnostic_round_ready(*session));
            require(!followup.handle(*session,receipt_records));
            require(followup.inspect(1)==after_basic);
        }
        std::cout<<"Isolated Lua revival, authorization, rollback, checkpoint and next action passed\n";
    } catch(const std::exception& e) { std::cerr<<e.what()<<'\n'; return 1; }
}
