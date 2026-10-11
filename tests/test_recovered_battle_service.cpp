#include "handlers/RecoveredBattleService.h"
#include "handlers/RecoveredWorldService.h"
#include "scripting/LuaEngine.h"
#include "protocol/DiagnosticBattleParticipants.h"
#include "db/SqliteRecoveredCharacterRepository.h"
#include "db/SqliteMigrationManager.h"
#include "db/SqliteSupport.h"
#include <iostream>

namespace {
using namespace god2;
void require(bool value,const char* message){if(!value) throw std::runtime_error(message);}
template<class F> void rejects(F f) {
    bool failed=false;try{f();}catch(const std::exception&){failed=true;}
    require(failed,"Expected rejection");
}
std::vector<RecoveredWorldRecords::Record> command(std::uint8_t action,std::uint16_t targets=1,std::uint8_t skill=0,std::uint8_t kind=0) {
    std::array<std::uint8_t,17> bytes{0x35,2,action,1,0,0,0,
        static_cast<std::uint8_t>(targets),static_cast<std::uint8_t>(targets>>8),0x34,0x12,0,0,skill,kind,0,0};
    auto records=RecoveredWorldRecords::decode(bytes);
    require(records.has_value(),"Diagnostic command did not parse");return *records;
}
}
int main() {
    try {
        using R=RecoveredWorldRecords::Record;
        asio::io_context io;
        auto session=std::make_shared<Session>(asio::ip::tcp::socket(io),io.get_executor(),1,false,
            Session::PacketHandler{},Session::DisconnectHandler{});
        session->account_id=7;session->character_id=9;session->set_state(SessionState::InBattle);
        LuaEngine lua(std::filesystem::path(GOD2_SOURCE_DIR)/"scripts",false);
        require(lua.initialize(),"Lua initialization failed");
        RecoveredBattleService service([&](auto input){return lua.combat_damage(input);});
        const std::array<BattleActor,3> actors{{
            {0,9,100,100,20,20,31,40,8,10},
            {14,0,100,100,0,0,20,25,13,6},
            {15,0,100,100,0,0,20,25,13,6}}};
        const BattleAction basic{0,{},false,100,100,0,0,150};
        auto spell=basic;spell.magical=true;spell.mp_cost=8;
        RecoveredBattleService::Policy policy{2,1,0,0x1234,basic,{{5,spell}}};
        bool malformed=false;
        auto encoder=[&](const BattleSnapshot& state,const BattleActionResult& result) {
            // Synthetic zero opaque fields, only for domain/transport testing.
            std::vector<std::uint8_t> logical;
            if(result.mp_cost) {
                const auto& source=*state.actors[result.source];
                const auto mp=diagnostic_battle_mp(result.source,source.mp,source.max_mp);
                logical.insert(logical.end(),mp.begin(),mp.end());
            }
            for(const auto& hit:result.hits) {
                std::array<std::uint8_t,17> packet{0x86,0,hit.target};
                const auto& target=*state.actors[hit.target];
                for(unsigned i=0;i<4;++i) {
                    packet[5+i]=static_cast<std::uint8_t>(target.max_hp>>(8*i));
                    packet[9+i]=static_cast<std::uint8_t>(target.hp>>(8*i));
                }
                logical.insert(logical.end(),packet.begin(),packet.end());
            }
            auto wire=RecoveredWorldFrame::encode(logical);
            if(malformed) wire.back()^=1;
            return wire;
        };
        {
            RecoveredBattleService typed([&](auto input){return lua.combat_damage(input);});
            typed.bind(*session,Battle(179,actors,123),policy,encoder);
            const auto unchanged=typed.inspect(1);
            require(!typed.handle(*session,command(3,1,5,1)),"Kind1 aliased a kind0 policy with the same ID");
            require(typed.inspect(1).revision==unchanged.revision && typed.inspect(1).actors[0]->mp==20 &&
                typed.inspect(1).actors[14]->hp==100,"Unconfigured kind1 changed battle state");
            typed.remove(1);auto configured=policy;configured.skills.clear();
            configured.skills.emplace(RecoveredBattleService::skill_key(1,5),spell);
            typed.bind(*session,Battle(179,actors,123),configured,encoder);
            require(!typed.handle(*session,command(3,1,5,0)),"Kind0 aliased a kind1 policy with the same ID");
            require(typed.handle(*session,command(3,1,5,1)).has_value(),"Explicit kind1 policy did not execute");
            require(typed.inspect(1).actors[0]->mp==12 && typed.inspect(1).actors[14]->hp<100,
                "Kind1 action failed to publish its explicit test policy");
        }
        {
            RecoveredBattleService exclusive([&](auto input){return lua.combat_damage(input);});
            auto other=std::make_shared<Session>(asio::ip::tcp::socket(io),io.get_executor(),2,false,
                Session::PacketHandler{},Session::DisconnectHandler{});
            other->account_id=7;other->character_id=9;other->set_state(SessionState::InBattle);
            exclusive.bind(*session,Battle(180,actors,123),policy,encoder);
            rejects([&]{exclusive.bind(*other,Battle(181,actors,123),policy,encoder);});
            other->account_id=8;
            rejects([&]{exclusive.bind(*other,Battle(181,actors,123),policy,encoder);});
            other->character_id=10;
            auto others=actors;others[0].controller=10;
            rejects([&]{exclusive.bind(*other,Battle(180,others,123),policy,encoder);});
            require(exclusive.inspect(1).id==180 && exclusive.inspect(1).actors[0]->mp==20,
                    "Duplicate bind changed original battle");
            require(!exclusive.handle(*other,command(1)),"Rejected session gained battle authorization");
            exclusive.bind(*other,Battle(181,others,123),policy,encoder);
            require(exclusive.handle(*other,command(1)).has_value(),"Distinct character battle was blocked");
            require(exclusive.inspect(1).actors[14]->hp==100,"Other battle mutated original target");
            exclusive.remove(2);
            exclusive.remove(1);
            other->character_id=9;
            exclusive.bind(*other,Battle(180,actors,123),policy,encoder);
            require(exclusive.handle(*other,command(1)).has_value(),"Removed binding retained stale occupancy");
        }
        {
            RecoveredBattleService durable([&](auto input){return lua.combat_damage(input);});
            auto p=policy;p.diagnostic_single_action=true;
            p.diagnostic_retaliation=BattleAction{14,{0},false,100,100,0,0,150};
            bool fail_store=true;
            unsigned commits=0;
            std::optional<BattleSnapshot> stored;
            durable.bind(*session,Battle(190,actors,123),p,encoder,
                [&](const BattleSnapshot& before,const BattleSnapshot& after) {
                    ++commits;
                    require(before.revision==1 && after.revision==3,"Persist whole exchange once");
                    require(before.actors[0]->mp==20 && after.actors[0]->mp==12 &&
                            after.actors[0]->hp==88 && after.actors[14]->hp==66,"Commit must include skill and retaliation");
                    if(fail_store) throw std::runtime_error("Injected storage failure");
                    stored=after;
                });
            const auto cast=command(3,1,5);
            malformed=true;
            rejects([&]{durable.handle(*session,cast);});
            malformed=false;
            require(commits==0,"Malformed reply must not reach persistence");
            rejects([&]{durable.handle(*session,cast);});
            require(commits==1 && !stored && durable.inspect(1).revision==1 &&
                    durable.inspect(1).actors[0]->mp==20 && durable.inspect(1).actors[0]->hp==100 &&
                    durable.inspect(1).actors[14]->hp==100,"Storage failure must not publish battle state");
            fail_store=false;
            require(durable.handle(*session,cast).has_value(),"Storage failure must preserve action admission for retry");
            require(commits==2 && stored && durable.inspect(1).revision==3,"Successful persistence publishes once");
            require(!durable.handle(*session,cast),"Committed action cannot be replayed");
            require(commits==2,"Replay must not persist again");
        }
        {
            sqlite3* raw=nullptr;
            require(sqlite3_open(":memory:",&raw)==SQLITE_OK,"Unable to open battle storage fixture");
            const std::unique_ptr<sqlite3,decltype(&sqlite3_close_v2)> db(raw,sqlite3_close_v2);
            sqlite_detail::execute(raw,"PRAGMA foreign_keys=ON");
            SqliteMigrationManager(raw,default_sqlite_migrations()).migrate();
            sqlite_detail::execute(raw,"INSERT INTO accounts(id,username,password_hash) VALUES(7,'battle-store','test')");
            SqliteRecoveredCharacterRepository repository(raw);
            std::array<std::uint8_t,40> profile{};profile[0]='T';
            const auto character=repository.create(7,profile);
            auto db_session=std::make_shared<Session>(asio::ip::tcp::socket(io),io.get_executor(),191,false,
                Session::PacketHandler{},Session::DisconnectHandler{});
            db_session->account_id=7;db_session->character_id=character.id;db_session->set_state(SessionState::InBattle);
            auto db_actors=actors;db_actors[0].controller=character.id;
            std::optional<CharacterResources> saved=repository.commit_resources(7,character.id,{},
                CharacterResources{100,100,20,20,0,"CUSTOM-0012"});
            const auto initial=saved;
            RecoveredBattleService durable([&](auto input){return lua.combat_damage(input);});
            auto p=policy;p.diagnostic_single_action=true;
            p.diagnostic_retaliation=BattleAction{14,{0},false,100,100,0,0,150};
            unsigned attempts=0;
            durable.bind(*db_session,Battle(191,db_actors,123),p,encoder,
                [&](const BattleSnapshot& before,const BattleSnapshot& after) {
                    ++attempts;
                    const auto& old=*before.actors[0];const auto& next=*after.actors[0];
                    require(saved && old.hp==saved->hp && old.mp==saved->mp,"Battle/storage base mismatch");
                    auto committed=repository.commit_resources(7,character.id,saved,
                        CharacterResources{next.hp,next.max_hp,next.mp,next.max_mp,0,"CUSTOM-0012"});
                    saved=std::move(committed);
                });
            sqlite_detail::execute(raw,"CREATE TRIGGER reject_resources BEFORE UPDATE ON character_resources BEGIN SELECT RAISE(ABORT,'injected'); END");
            const auto cast=command(3,1,5);
            rejects([&]{durable.handle(*db_session,cast);});
            require(repository.load_resources(7,character.id)==initial && saved==initial &&
                    durable.inspect(191).revision==1 && durable.inspect(191).actors[0]->mp==20 &&
                    durable.inspect(191).actors[14]->hp==100,"SQLite failure published partial exchange");
            sqlite_detail::execute(raw,"DROP TRIGGER reject_resources");
            require(durable.handle(*db_session,cast).has_value(),"SQLite retry failed");
            auto reopened_repository=SqliteRecoveredCharacterRepository(raw);
            const auto loaded=reopened_repository.load_resources(7,character.id);
            require(loaded==saved && loaded->revision==2 && loaded->hp==88 && loaded->mp==12 &&
                    durable.inspect(191).revision==3,"SQLite must persist one complete skill/retaliation exchange");
            require(!durable.handle(*db_session,cast) && attempts==2,"Replay attempted another database commit");
            require(repository.load_resources(7,character.id)==loaded,"Replay changed saved resources");
            durable.remove(191);
            const auto battle_id=repository.reserve_battle(7,character.id,*saved);
            db_actors[0].hp=saved->hp;db_actors[0].mp=saved->mp;
            Battle continued(battle_id,db_actors,456);
            auto checkpoint=repository.commit_checkpoint(7,character.id,{},*saved,continued.checkpoint(),*saved,
                "CUSTOM-0012/diagnostic-v1");
            saved=repository.load_resources(7,character.id);
            const auto seed_checkpoint=checkpoint;
            const auto seed_resources=saved;
            const RecoveredBattleService::CheckpointCommit save_checkpoint=[&](const BattleCheckpoint& before,const BattleCheckpoint& after) {
                require(before==checkpoint.checkpoint,"Checkpoint callback lost RNG baseline");
                const auto& player=*after.snapshot.actors[0];
                CharacterResources next{player.hp,player.max_hp,player.mp,player.max_mp,0,"CUSTOM-0012"};
                auto committed=repository.commit_checkpoint(7,character.id,checkpoint,*saved,after,next,checkpoint.policy_id);
                next.revision=committed.resource_revision;
                checkpoint=std::move(committed);saved=std::move(next);
            };
            rejects([&]{durable.bind(*db_session,continued,p,encoder,
                [](const BattleSnapshot&,const BattleSnapshot&){},save_checkpoint);});
            durable.bind(*db_session,continued,p,encoder,{},save_checkpoint);
            sqlite_detail::execute(raw,"CREATE TRIGGER reject_checkpoint BEFORE INSERT ON battle_checkpoints BEGIN SELECT RAISE(ABORT,'injected'); END");
            rejects([&]{durable.handle(*db_session,cast);});
            require(durable.inspect(191)==seed_checkpoint.checkpoint.snapshot &&
                    repository.load_checkpoint(7,character.id,battle_id)==seed_checkpoint &&
                    repository.load_resources(7,character.id)==seed_resources,"Checkpoint failure partially committed exchange");
            sqlite_detail::execute(raw,"DROP TRIGGER reject_checkpoint");
            require(durable.handle(*db_session,cast).has_value(),"Checkpoint exchange retry rejected");
            require(checkpoint.checkpoint.snapshot==durable.inspect(191) && checkpoint.checkpoint.snapshot.revision==3 &&
                    saved->hp==76 && saved->mp==4,"Checkpoint failed complete skill/retaliation state");
            auto expected=Battle::restore(seed_checkpoint.checkpoint);
            auto action=spell;action.targets={14};
            const Battle::Rule damage=[&](const auto& input){return lua.combat_damage(input);};
            expected.act(character.id,1,action,damage,encoder);
            expected.act(0,2,*p.diagnostic_retaliation,damage,encoder);
            require(checkpoint.checkpoint==expected.checkpoint(),"Failed callback consumed random state");
            const auto stored=repository.load_checkpoint(7,character.id,battle_id);
            require(!durable.handle(*db_session,cast) && repository.load_checkpoint(7,character.id,battle_id)==stored,
                    "Replay altered durable checkpoint");
        }
        // CUSTOM-0012: insufficient resource must not consume action/receipt admission.
        for(std::uint32_t available=0;available<=8;++available) {
            auto limited=actors;limited[0].mp=available;
            unsigned rule_calls=0,encode_calls=0;
            RecoveredBattleService checked([&](auto input){++rule_calls;return lua.combat_damage(input);});
            auto guarded_policy=policy;guarded_policy.diagnostic_single_action=true;
            guarded_policy.diagnostic_retaliation=BattleAction{14,{0},false,100,100,0,0,150};
            checked.bind(*session,Battle(200+available,limited,123),guarded_policy,
                [&](const auto& state,const auto& result){++encode_calls;return encoder(state,result);});
            auto cast=command(3,1,5);
            auto receipt=command(0x0b);
            std::get<RecoveredBattleCommand::ControlRequest>(receipt.front()).fields.target_masks={1,0};
            auto combined=cast;combined.push_back(receipt.front());
            const auto before=checked.inspect(1).revision;
            if(available<8) {
                bool resource_refused=false;
                try { checked.handle(*session,combined); }
                catch(const InsufficientBattleMp& refusal) {
                    resource_refused=true;
                    require(refusal.available==available && refusal.required==8,"Resource refusal lost exact bounds");
                }
                require(resource_refused,"Legal low-MP skill lacks typed resource refusal");
                for(const auto invalid_target:{0u,13u}) {
                    auto bad=cast;
                    auto& request=std::get<RecoveredSkillCommand::Record>(bad.front());
                    request.target_masks={static_cast<std::uint16_t>(1u<<invalid_target),0};
                    bool invalid=false;
                    try { checked.handle(*session,bad); }
                    catch(const InsufficientBattleMp&) { throw std::runtime_error("Illegal target disguised as recoverable MP refusal"); }
                    catch(const std::invalid_argument&) { invalid=true; }
                    require(invalid,"Invalid low-MP target accepted");
                }
                auto unauthorized=cast;
                std::get<RecoveredSkillCommand::Record>(unauthorized.front()).actor_position=3;
                require(!checked.handle(*session,unauthorized),"Foreign actor admitted as resource refusal");
                require(rule_calls==0 && encode_calls==0,"Insufficient MP reached damage/encoder callbacks");
                require(checked.inspect(1).revision==before && checked.inspect(1).actors[0]->mp==available &&
                        checked.inspect(1).actors[0]->hp==100 && checked.inspect(1).actors[14]->hp==100,
                        "Rejected cast mutated MP/HP/revision");
                require(!checked.diagnostic_round_ready(*session) && !checked.handle(*session,receipt),
                        "Rejected cast admitted a completion receipt");
                rejects([&]{checked.rearm_diagnostic(*session,before);});
                require(checked.handle(*session,command(1)).has_value(),"Rejected skill consumed action admission");
                require(checked.inspect(1).actors[0]->mp==available && checked.inspect(1).actors[0]->hp==88 &&
                        checked.inspect(1).actors[14]->hp==82,"Basic recovery after rejected cast changed resource policy");
            } else {
                require(checked.handle(*session,combined).has_value(),"Exact-cost skill rejected");
                require(checked.inspect(1).actors[0]->mp==0 && checked.inspect(1).actors[0]->hp==88 &&
                        checked.inspect(1).actors[14]->hp==66 && checked.diagnostic_round_ready(*session),
                        "Exact-cost skill/retaliation did not commit once");
                require(rule_calls==2 && encode_calls==2,"Unexpected exact-cost callback count");
                require(!checked.handle(*session,cast),"Exact-cost cast replay accepted");
            }
        }
        for(unsigned failure=0;failure<3;++failure) {
            auto limited=actors;limited[0].mp=7;
            auto guarded_policy=policy;guarded_policy.diagnostic_single_action=true;
            unsigned refused=0;
            guarded_policy.diagnostic_mp_refusal=[&](const BattleSnapshot&,const BattleAction&,const InsufficientBattleMp&) {
                ++refused;
                if(failure==0) return std::vector<std::uint8_t>{};
                if(failure==1) return std::vector<std::uint8_t>{4,0,0,0};
                throw std::runtime_error("Diagnostic refusal encoder failure");
            };
            RecoveredBattleService checked([&](auto input){return lua.combat_damage(input);});
            auto not_diagnostic=guarded_policy;not_diagnostic.diagnostic_single_action=false;
            rejects([&]{checked.bind(*session,Battle(300,limited,123),not_diagnostic,encoder);});
            checked.bind(*session,Battle(300+failure,limited,123),guarded_policy,encoder);
            auto cast=command(3,1,5);
            auto combined=cast;
            auto receipt=command(0x0b);
            std::get<RecoveredBattleCommand::ControlRequest>(receipt.front()).fields.target_masks={1,0};
            combined.push_back(receipt.front());
            rejects([&]{checked.handle(*session,combined);});
            require(refused==0,"Mixed command invoked recoverable refusal callback");
            rejects([&]{checked.handle(*session,cast);});
            require(refused==1 && checked.inspect(1).revision==1 && checked.inspect(1).actors[0]->mp==7 &&
                    checked.inspect(1).actors[14]->hp==100 && !checked.diagnostic_round_ready(*session),
                    "Malformed refusal reply mutated battle or admission");
            require(checked.handle(*session,command(1)).has_value(),"Refusal encoder failure consumed action admission");
        }
        {
            RecoveredBattleService checked([&](auto input){return lua.combat_damage(input);});
            auto collision=policy;
            collision.skills.emplace(8,spell);
            checked.bind(*session,Battle(299,actors,123),collision,encoder);
            auto revival=command(3,1,8);
            std::get<RecoveredSkillCommand::Record>(revival.front()).selection_kind_byte=3;
            require(!checked.handle(*session,revival) && checked.inspect(1).revision==1 &&
                    checked.inspect(1).actors[0]->mp==20,"Revival aliased a kind0 attack policy");
            require(checked.handle(*session,command(3,1,8)).has_value(),
                    "Revival rejection consumed kind0 action admission");
        }
        // Recorded player action: final DWORD is native unwritten stack storage.
        const std::array<std::uint8_t,17> player_action{
            0x35,0,1,0,0,0,0,1,0,0,0,0,0,0xd0,0x1c,0x90,0x37};
        const auto player_records=RecoveredWorldRecords::decode(player_action);
        require(player_records.has_value(),"Recorded player action failed structural decode");
        auto player_policy=policy;
        player_policy.client_actor=0;player_policy.client_side=0;player_policy.context=0;
        player_policy.diagnostic_single_action=true;
        player_policy.diagnostic_player_initial_control=true;
        player_policy.diagnostic_retaliation=BattleAction{14,{0},false,100,100,0,0,150};
        service.bind(*session,Battle(99,actors,123),player_policy,encoder);
        RecoveredWorldService player_world({},[&](Session& s,auto records){return service.handle(s,records);});
        const std::array<std::uint8_t,17> initial_control{0x35,0,0x0b};
        const auto initial_records=*RecoveredWorldRecords::decode(initial_control);
        {
            RecoveredBattleService grant_service([&](auto input){return lua.combat_damage(input);});
            auto p=player_policy;bool malformed_grant=true;unsigned grants=0;
            std::array<std::uint8_t,17> grant{};grant[0]=0x86;grant[1]=5;grant[3]=1;
            const auto good_grant=RecoveredWorldFrame::encode(grant);
            p.diagnostic_initial_control_reply=[&] {
                ++grants;auto wire=good_grant;if(malformed_grant)wire.back()^=1;return wire;
            };
            auto invalid=p;invalid.diagnostic_player_initial_control=false;
            rejects([&]{grant_service.bind(*session,Battle(198,actors,123),invalid,encoder);});
            grant_service.bind(*session,Battle(198,actors,123),p,encoder);
            rejects([&]{grant_service.handle(*session,initial_records);});
            require(grant_service.inspect(1).revision==1 && grant_service.inspect(1).actors[0]->mp==20,
                    "Malformed initial grant changed battle/resources");
            malformed_grant=false;
            const auto accepted=grant_service.handle(*session,initial_records);
            require(accepted && *accepted==good_grant && grants==2 && grant_service.inspect(1).revision==1,
                    "Initial grant failed retry or advanced battle revision");
            require(!grant_service.handle(*session,initial_records) && grants==2,
                    "Initial receipt replay reissued grant");
        }
        const auto initial_revision=service.inspect(1).revision;
        auto wrong_initial=initial_records;
        std::get<RecoveredBattleCommand::ControlRequest>(wrong_initial.front()).fields.context_storage=1;
        require(!player_world.handle(*session,wrong_initial),"Foreign initial control accepted");
        auto mixed_initial=initial_records;
        mixed_initial.insert(mixed_initial.end(),player_records->begin(),player_records->end());
        require(!player_world.handle(*session,mixed_initial) && service.inspect(1).revision==initial_revision,
                "Unqualified mixed initial notice committed a prefix");
        const auto initial_reply=player_world.handle(*session,initial_records);
        require(initial_reply && initial_reply->empty() && service.inspect(1).revision==initial_revision &&
                !service.diagnostic_round_ready(*session),"Initial player control changed battle");
        require(!player_world.handle(*session,initial_records),"Initial player control replay accepted");
        require(player_world.handle(*session,*player_records).has_value() &&
                service.inspect(1).actors[14]->hp==82 && service.inspect(1).actors[0]->hp==88,
                "Recorded player attack/retaliation rejected");
        require(!service.diagnostic_round_ready(*session),"Action alone fabricated control receipt");
        service.remove(1);
        {
            auto opening_policy=player_policy;
            opening_policy.diagnostic_opening_action2=true;
            service.bind(*session,Battle(198,actors,123),opening_policy,encoder);
            const std::array<std::uint8_t,17> native_opening{0x35,0,2,0,0,1};
            const auto opening=*RecoveredWorldRecords::decode(native_opening);
            require(!player_world.handle(*session,opening),"Opening action02 preceded initial control");
            require(player_world.handle(*session,initial_records).has_value(),"Initial control rejected");
            auto wrong_opening=opening;
            std::get<RecoveredBattleCommand::Action2Request>(wrong_opening.front()).fields.context_storage=1;
            require(!player_world.handle(*session,wrong_opening),"Foreign opening context accepted");
            require(player_world.handle(*session,opening).has_value() &&
                    service.inspect(1).revision==initial_revision,"Opening action02 changed battle");
            require(!player_world.handle(*session,opening),"Opening action02 replay accepted");
            require(player_world.handle(*session,*player_records).has_value(),
                    "Opening action02 blocked native attack");
            service.remove(1);
        }
        {
            auto timeout_policy=player_policy;
            timeout_policy.diagnostic_timeout_action2=true;
            timeout_policy.diagnostic_control_targets={0,1};
            auto invalid_policy=timeout_policy;
            invalid_policy.diagnostic_retaliation.reset();
            rejects([&]{service.bind(*session,Battle(197,actors,123),invalid_policy,encoder);});
            bool reject_commit=true;
            service.bind(*session,Battle(197,actors,123),timeout_policy,encoder,
                [&](const BattleSnapshot&,const BattleSnapshot&) {
                    if(reject_commit) throw std::runtime_error("injected timeout commit failure");
                });
            const std::array<std::uint8_t,17> native_timeout{0x35,0,2,0,0,1};
            const auto timeout=*RecoveredWorldRecords::decode(native_timeout);
            require(!player_world.handle(*session,timeout),"Timeout preceded initial control");
            require(player_world.handle(*session,initial_records).has_value(),"Timeout initial control rejected");
            auto wrong_timeout=timeout;
            std::get<RecoveredBattleCommand::Action2Request>(wrong_timeout.front()).fields.context_storage=1;
            require(!player_world.handle(*session,wrong_timeout),"Foreign timeout context accepted");
            rejects([&]{player_world.handle(*session,timeout);});
            require(service.inspect(1).revision==initial_revision && service.inspect(1).actors[0]->hp==100,
                    "Failed timeout commit changed battle");
            reject_commit=false;
            const auto response=player_world.handle(*session,timeout);
            require(response && !response->empty() && service.inspect(1).revision==initial_revision+1 &&
                    service.inspect(1).actors[0]->hp==88 && service.inspect(1).actors[14]->hp==100,
                    "Timeout did not commit only the isolated enemy turn");
            require(!player_world.handle(*session,timeout) && !player_world.handle(*session,*player_records),
                    "Expired player command was replayed or followed by an attack");
            auto receipt=initial_records;
            std::get<RecoveredBattleCommand::ControlRequest>(receipt.front()).fields.target_masks={0,1};
            require(!player_world.handle(*session,receipt),"Ordinary attack receipt admitted after timeout");
            std::get<RecoveredBattleCommand::ControlRequest>(receipt.front()).fields.target_masks={1,0};
            require(player_world.handle(*session,receipt).has_value() && service.diagnostic_round_ready(*session) &&
                    service.diagnostic_timeout_round_ready(*session),
                    "Timeout receipt did not complete round");
            service.rearm_diagnostic(*session,initial_revision+1);
            require(!service.diagnostic_round_ready(*session) &&
                    !service.diagnostic_timeout_round_ready(*session) &&
                    player_world.handle(*session,timeout).has_value() &&
                    service.inspect(1).revision==initial_revision+2,
                    "Next no-input turn did not advance exactly once");
            service.remove(1);
        }
        {
            auto repeated=player_policy;
            repeated.diagnostic_second_encounter_entry=true;
            repeated.diagnostic_control_targets={0,1};
            auto missing_initial=repeated;missing_initial.diagnostic_player_initial_control=false;
            rejects([&]{service.bind(*session,Battle(199,actors,123),missing_initial,encoder);});
            service.bind(*session,Battle(199,actors,123),repeated,encoder);
            auto entry=initial_records;
            auto& fields=std::get<RecoveredBattleCommand::ControlRequest>(entry.front()).fields;
            fields.target_masks={1,0};
            fields.context_storage=1;
            require(!player_world.handle(*session,entry),"Foreign repeated-entry context accepted");
            fields.context_storage=0;
            require(!player_world.handle(*session,initial_records),"First-entry mask accepted during repeated entry");
            const auto before=service.inspect(1);
            const auto reply=player_world.handle(*session,entry);
            require(reply && reply->empty() && service.inspect(1)==before,"Repeated entry mutated battle");
            require(!player_world.handle(*session,entry),"Repeated entry replay accepted");
            require(player_world.handle(*session,*player_records).has_value(),"Repeated entry blocked action");
            require(!player_world.handle(*session,entry),"Initial notice counted as action completion");
            fields.target_masks={0,1};
            require(player_world.handle(*session,entry).has_value(),"Normal action receipt rejected after repeated entry");
            service.remove(1);
        }
        player_policy.diagnostic_control_targets={0,1};
        service.bind(*session,Battle(100,actors,123),player_policy,encoder);
        auto animation_control=initial_records;
        auto& control_fields=std::get<RecoveredBattleCommand::ControlRequest>(animation_control.front()).fields;
        control_fields.target_masks={0,1};
        require(!player_world.handle(*session,animation_control),"Animation receipt admitted before action");
        require(player_world.handle(*session,*player_records).has_value(),"Animation-mode action rejected");
        control_fields.target_masks={1,0};
        require(!player_world.handle(*session,animation_control),"Wrong animation receipt target admitted");
        control_fields.target_masks={0,1};
        const auto before_receipt=service.inspect(1).revision;
        require(player_world.handle(*session,animation_control).has_value() &&
                service.diagnostic_round_ready(*session) && service.inspect(1).revision==before_receipt,
                "Observed animation receipt rejected or mutated battle");
        require(!player_world.handle(*session,animation_control),"Animation receipt replay accepted");
        service.remove(1);
        service.bind(*session,Battle(1,actors,123),policy,encoder);
        require(!service.handle(*session,initial_records),"Normal policy admitted player diagnostic notice");
        rejects([&]{service.bind(*session,Battle(2,actors,123),policy,encoder);});
        RecoveredWorldService world({},[&](Session& s,auto records){return service.handle(s,records);});
        const auto attack=command(1);
        auto reply=world.handle(*session,attack);
        require(reply && RecoveredWorldFrame::decode(*reply).has_value(),"Native reply not framed");
        require(service.inspect(1).actors[14]->hp==82,"Parsed basic attack not applied");
        for(unsigned bad=0;bad<5;++bad) {
            auto records=attack;
            auto& request=std::get<RecoveredBattleCommand::BasicAttackRequest>(records[0]);
            if(bad==0) request.actor_position=3;
            if(bad==1) request.side_flag=0;
            if(bad==2) request.context_storage=0x9999;
            if(bad==3) request.target_masks[1]=3;
            if(bad==4) records.push_back(records.front());
            require(!world.handle(*session,records),"Unauthorized input accepted");
        }
        require(!world.handle(*session,command(3,1,6)),"Unknown skill accepted");
        require(!world.handle(*session,command(0x0b)),"Control opcode guessed");
        auto sequence=command(0x83,1,5);
        require(!world.handle(*session,sequence),"Partial cast committed");
        auto end=command(3,2,5);sequence.insert(sequence.end(),end.begin(),end.end());
        reply=world.handle(*session,sequence);
        require(reply && service.inspect(1).actors[0]->mp==12 &&
                service.inspect(1).actors[14]->hp==48 && service.inspect(1).actors[15]->hp==66,
                "Native skill sequence not applied atomically");
        const auto decoded=*RecoveredWorldFrame::decode(*reply);
        require(decoded.size()==3*RecoveredBattleVitals::logical_size,"Multi-target skill must emit one MP and two HP records");
        const auto mp=RecoveredBattleVitals::parse_logical(std::span(decoded).first(17));
        require(mp && mp->resource()==RecoveredBattleVitals::Resource::Mp && mp->position()==0 &&
                mp->current()==12 && mp->maximum()==20,"MP reply differs from committed caster state");
        const auto revision=service.inspect(1).revision;
        malformed=true;
        rejects([&]{world.handle(*session,command(3,1,5));});
        require(service.inspect(1).revision==revision && service.inspect(1).actors[0]->mp==12 &&
                service.inspect(1).actors[14]->hp==48,"Bad skill response committed MP or HP");
        rejects([&]{world.handle(*session,attack);});
        require(service.inspect(1).revision==revision && service.inspect(1).actors[14]->hp==48,
                "Bad wire response committed damage");
        malformed=false;
        session->account_id=8;require(!world.handle(*session,attack),"Account binding ignored");
        session->account_id=7;session->character_id=10;
        require(!world.handle(*session,attack),"Character binding ignored");
        session->character_id=9;
        const std::array<R,1> heartbeat{RecoveredWorldRecords::Tick{}};
        const auto silent=world.handle(*session,heartbeat);
        require(silent && silent->empty(),"Tick fabricated combat");
        service.remove(1);
        require(!world.handle(*session,attack),"Removed battle still callable");
        policy.diagnostic_single_action=true;
        service.bind(*session,Battle(3,actors,123),policy,encoder);
        auto completion=command(0x0b);
        std::get<RecoveredBattleCommand::ControlRequest>(completion.front()).fields.target_masks={1,0};
        require(!world.handle(*session,completion),"Premature control accepted");
        auto combined=attack;combined.push_back(completion.front());
        auto duplicate=combined;duplicate.push_back(completion.front());
        require(!world.handle(*session,duplicate) && service.inspect(1).actors[14]->hp==100,
                "Duplicate control committed attack prefix");
        malformed=true;
        rejects([&]{world.handle(*session,combined);});
        require(service.inspect(1).actors[14]->hp==100,"Failed diagnostic response committed damage");
        malformed=false;
        require(world.handle(*session,combined).has_value() && service.inspect(1).actors[14]->hp==82,
                "Diagnostic single action/control not committed together");
        require(!world.handle(*session,combined) && !world.handle(*session,completion),"Diagnostic replay accepted");
        service.remove(1);
        service.bind(*session,Battle(4,actors,123),policy,encoder);
        require(world.handle(*session,attack).has_value(),"Separated diagnostic action rejected");
        const auto control_reply=world.handle(*session,completion);
        require(control_reply && control_reply->empty() && service.inspect(1).actors[14]->hp==82,
                "Separate control caused damage or invented reply");
        service.remove(1);
        policy.diagnostic_retaliation=BattleAction{14,{0},false,100,100,0,0,150};
        bool counter_fails=true;
        auto round_encoder=[&](const auto& state,const auto& result) {
            if(counter_fails && result.source==14) throw std::runtime_error("Injected retaliation encoding failure");
            return encoder(state,result);
        };
        service.bind(*session,Battle(5,actors,123),policy,round_encoder);
        rejects([&]{world.handle(*session,combined);});
        require(service.inspect(1).actors[0]->hp==100 && service.inspect(1).actors[14]->hp==100 &&
                service.inspect(1).revision==1,"Retaliation failure committed partial round");
        counter_fails=false;
        require(world.handle(*session,combined).has_value() && service.inspect(1).actors[0]->hp==88 &&
                service.inspect(1).actors[14]->hp==82 && service.inspect(1).revision==3,
                "Atomic diagnostic attack and retaliation mismatch");
        require(!world.handle(*session,combined),"Retaliating diagnostic round replayed");
        rejects([&]{service.rearm_diagnostic(*session,2);});
        session->account_id=8;
        rejects([&]{service.rearm_diagnostic(*session,3);});
        session->account_id=7;
        service.rearm_diagnostic(*session,3);
        rejects([&]{service.rearm_diagnostic(*session,3);});
        require(world.handle(*session,combined).has_value() && service.inspect(1).actors[0]->hp==76 &&
                service.inspect(1).actors[14]->hp==64 && service.inspect(1).revision==5,
                "Second authorized diagnostic round mismatch");
        require(!world.handle(*session,combined),"Second round admitted duplicate action");
        service.rearm_diagnostic(*session,5);
        require(world.handle(*session,attack).has_value() && service.inspect(1).actors[0]->hp==64 &&
                service.inspect(1).actors[14]->hp==46 && service.inspect(1).revision==7,
                "Third authorized diagnostic round mismatch");
        rejects([&]{service.rearm_diagnostic(*session,7);});
        require(world.handle(*session,completion).has_value(),"Third round control not received");
        service.rearm_diagnostic(*session,7);
        service.remove(1);
        policy.basic.power_percent=10000;
        {
            auto observed=policy;
            observed.basic.power_percent=100;
            observed.diagnostic_control_targets={0,1};
            observed.diagnostic_three_round_friendly_receipts=true;
            auto enemy_receipt=completion;
            std::get<RecoveredBattleCommand::ControlRequest>(enemy_receipt.front()).fields.target_masks={0,1};
            std::optional<BattleCheckpoint> committed_checkpoint;
            service.bind(*session,Battle(65,actors,123),observed,encoder,{},
                [&](const BattleCheckpoint&,const BattleCheckpoint& after) { committed_checkpoint=after; });
            require(world.handle(*session,attack).has_value(),"First exchange action");
            require(!world.handle(*session,completion),"Friendly receipt wrongly accepted at revision3");
            require(world.handle(*session,enemy_receipt).has_value(),"First enemy receipt");
            require(committed_checkpoint.has_value(),"Missing committed first exchange checkpoint");
            const auto resume_checkpoint=*committed_checkpoint;
            service.rearm_diagnostic(*session,3);
            require(world.handle(*session,attack).has_value(),"Second exchange action");
            const auto second_resume_checkpoint=*committed_checkpoint;
            require(!world.handle(*session,enemy_receipt),"Old mask accepted at qualified second exchange");
            require(world.handle(*session,completion).has_value(),"Observed second friendly receipt rejected");
            require(!world.handle(*session,completion),"Observed receipt replay accepted");
            service.rearm_diagnostic(*session,5);
            require(world.handle(*session,attack).has_value(),"Third exchange action");
            require(!world.handle(*session,completion),"Second-exchange exception leaked to revision7");
            require(world.handle(*session,enemy_receipt).has_value(),"Default third receipt rejected");
            service.remove(1);
            {
                auto resumed_policy=observed;
                resumed_policy.diagnostic_first_exchange_resume=true;
                const auto checkpoint=resume_checkpoint;
                rejects([&]{service.bind(*session,Battle(67,actors,123),resumed_policy,encoder);});
                auto wrong_policy=resumed_policy;
                wrong_policy.diagnostic_three_round_friendly_receipts=false;
                rejects([&]{service.bind(*session,Battle::restore(checkpoint),wrong_policy,encoder);});
                wrong_policy=resumed_policy;
                wrong_policy.diagnostic_single_action=false;
                rejects([&]{service.bind(*session,Battle::restore(checkpoint),wrong_policy,encoder);});
                wrong_policy=resumed_policy;
                wrong_policy.diagnostic_retaliation.reset();
                rejects([&]{service.bind(*session,Battle::restore(checkpoint),wrong_policy,encoder);});
                wrong_policy=resumed_policy;
                wrong_policy.diagnostic_control_targets={1,0};
                rejects([&]{service.bind(*session,Battle::restore(checkpoint),wrong_policy,encoder);});
                service.bind(*session,Battle::restore(checkpoint),resumed_policy,encoder);
                require(world.handle(*session,attack).has_value(),"Resumed exchange action");
                require(!world.handle(*session,completion),"Old connection friendly mask accepted after resume");
                require(world.handle(*session,enemy_receipt).has_value(),"Fresh resume enemy receipt rejected");
                require(!world.handle(*session,enemy_receipt),"Resume receipt replay accepted");
                service.remove(1);
            }
            {
                auto resumed=observed;
                resumed.diagnostic_player_initial_control=true;
                resumed.diagnostic_second_exchange_resume=true;
                rejects([&]{service.bind(*session,Battle::restore(resume_checkpoint),resumed,encoder);});
                for(unsigned fault=0;fault<6;++fault) {
                    auto invalid=resumed;
                    switch(fault) {
                    case 0:invalid.diagnostic_first_exchange_resume=true;break;
                    case 1:invalid.diagnostic_player_initial_control=false;break;
                    case 2:invalid.diagnostic_three_round_friendly_receipts=false;break;
                    case 3:invalid.diagnostic_retaliation.reset();break;
                    case 4:invalid.diagnostic_control_targets={1,0};break;
                    case 5:invalid.diagnostic_single_action=false;break;
                    }
                    rejects([&]{service.bind(*session,Battle::restore(second_resume_checkpoint),invalid,encoder);});
                }
                service.bind(*session,Battle::restore(second_resume_checkpoint),resumed,encoder);
                auto initial=completion;
                auto& fields=std::get<RecoveredBattleCommand::ControlRequest>(initial.front()).fields;
                fields.target_masks={0,0};fields.unwritten_byte3=0;fields.unwritten_parameter=0;
                require(world.handle(*session,initial).has_value(),"Second resume initialization rejected");
                require(!world.handle(*session,initial),"Second resume initialization replay accepted");
                require(world.handle(*session,attack).has_value(),"Second resume action rejected");
                require(!world.handle(*session,attack),"Second resume duplicate action accepted");
                service.remove(1);
            }
            std::array<BattleActor,2> terminal_actors{actors[0],actors[1]};terminal_actors[1].hp=50;
            service.bind(*session,Battle(66,terminal_actors,123),observed,encoder,{},
                [&](const BattleCheckpoint&,const BattleCheckpoint& after) { committed_checkpoint=after; });
            require(world.handle(*session,attack).has_value() && world.handle(*session,enemy_receipt).has_value(),"Terminal fixture round1");
            service.rearm_diagnostic(*session,3);
            require(world.handle(*session,attack).has_value() && world.handle(*session,completion).has_value(),"Terminal fixture round2");
            const auto terminal_resume_checkpoint=*committed_checkpoint;
            service.rearm_diagnostic(*session,5);
            require(world.handle(*session,attack).has_value() && service.inspect(1).revision==6 &&
                    service.inspect(1).state==BattleState::Finished,"Terminal fixture did not finish at revision6");
            require(!world.handle(*session,enemy_receipt),"Unobserved terminal mask accepted");
            require(world.handle(*session,completion).has_value(),"Observed terminal friendly receipt rejected");
            require(!world.handle(*session,completion),"Terminal receipt replay accepted");
            service.remove(1);
            auto terminal_resume=observed;
            terminal_resume.diagnostic_player_initial_control=true;
            terminal_resume.diagnostic_second_exchange_resume=true;
            service.bind(*session,Battle::restore(terminal_resume_checkpoint),terminal_resume,encoder);
            require(world.handle(*session,attack).has_value() && service.inspect(1).revision==6 &&
                    service.inspect(1).state==BattleState::Finished,"Second resume terminal action failed");
            require(!world.handle(*session,completion),"Old connection terminal mask accepted after second resume");
            require(world.handle(*session,enemy_receipt).has_value(),"Observed second resume terminal enemy mask rejected");
            require(!world.handle(*session,enemy_receipt),"Second resume terminal receipt replay accepted");
            service.remove(1);
        }
        service.bind(*session,Battle(6,actors,123),policy,encoder);
        require(world.handle(*session,combined).has_value() && service.inspect(1).actors[14]->hp==0 &&
                service.inspect(1).actors[0]->hp==100,"Dead diagnostic monster retaliated");
        service.remove(1);
        const std::array<BattleActor,2> duel{actors[0],actors[1]};
        service.bind(*session,Battle(7,duel,123),policy,encoder);
        require(world.handle(*session,combined).has_value() && !service.inspect(1).actors[14]->hp,
                "Diagnostic finishing action failed");
        rejects([&]{service.rearm_diagnostic(*session,service.inspect(1).revision);});
        service.remove(1);
        bool outcome_fails=true;
        unsigned outcome_encodes=0;
        service.bind(*session,Battle(8,duel,123),policy,
            [&](const BattleSnapshot& state,const BattleActionResult&) {
                require(state.state==BattleState::Finished && state.actors[14]->hp==0,
                        "Outcome encoded before terminal state");
                ++outcome_encodes;
                if(outcome_fails) throw std::runtime_error("Injected outcome encoding failure");
                return RecoveredWorldFrame::encode(diagnostic_battle_zero_result());
            });
        rejects([&]{world.handle(*session,combined);});
        require(service.inspect(1).state==BattleState::Active && service.inspect(1).revision==1 &&
                service.inspect(1).actors[14]->hp==duel[1].hp,"Outcome failure committed terminal state");
        require(!service.release_finished_diagnostic(*session),"Failed terminal transaction released battle");
        outcome_fails=false;
        const auto terminal_reply=world.handle(*session,combined);
        require(terminal_reply && service.inspect(1).state==BattleState::Finished && outcome_encodes==2,
                "Terminal retry did not commit exactly once");
        const auto terminal_plain=RecoveredWorldFrame::decode(*terminal_reply);
        const auto expected_outcome=diagnostic_battle_zero_result();
        require(terminal_plain && std::equal(terminal_plain->begin(),terminal_plain->end(),
                expected_outcome.begin(),expected_outcome.end()),"Outcome reply changed");
        require(!world.handle(*session,combined) && outcome_encodes==2,"Terminal action replay emitted another outcome");
        session->account_id=8;
        require(!service.release_finished_diagnostic(*session),"Wrong account released battle");
        session->account_id=7;
        require(service.release_finished_diagnostic(*session) && session->state()==SessionState::InWorld,
                "Committed terminal diagnostic did not return server to world");
        require(!service.release_finished_diagnostic(*session) && !world.handle(*session,combined),
                "Released battle accepted duplicate release/action");
        rejects([&]{service.inspect(session->id());});
        session->set_state(SessionState::InBattle);
        service.bind(*session,Battle(9,duel,123),policy,encoder);
        require(world.handle(*session,attack).has_value() && service.inspect(1).state==BattleState::Finished,
                "Separated terminal action failed");
        require(!service.release_finished_diagnostic(*session) && session->state()==SessionState::InBattle,
                "Terminal action released before its control receipt");
        require(!world.handle(*session,attack),"Finished battle accepted another attack");
        auto wrong_completion=completion;
        std::get<RecoveredBattleCommand::ControlRequest>(wrong_completion[0]).fields.context_storage^=1;
        require(!world.handle(*session,wrong_completion),"Finished battle accepted foreign control context");
        const auto late_control=world.handle(*session,completion);
        require(late_control && late_control->empty() && service.inspect(1).revision==2,
                "Separate terminal control mutated or rejected committed action");
        require(!world.handle(*session,completion),"Terminal control replay accepted");
        require(service.release_finished_diagnostic(*session) && session->state()==SessionState::InWorld,
                "Separate terminal control did not allow trusted release");
        {
            // CUSTOM-0011: synthetic defeat receipt, not native defeat qualification.
            session->set_state(SessionState::InBattle);
            auto defeat_policy=policy;
            defeat_policy.basic.power_percent=100;
            auto defeated=duel;
            defeated[0].hp=4;
            bool commit_fails=true;
            unsigned commits=0;
            std::optional<BattleCheckpoint> saved_defeat;
            service.bind(*session,Battle(10,defeated,123),defeat_policy,encoder,{},
                [&](const BattleCheckpoint& before,const BattleCheckpoint& after) {
                    require(before.snapshot.revision==1,"Defeat retry changed pre-state");
                    ++commits;
                    if(commit_fails) throw std::runtime_error("Injected defeat persistence failure");
                    saved_defeat=after;
                });
            rejects([&]{world.handle(*session,attack);});
            require(service.inspect(1).state==BattleState::Active &&
                    service.inspect(1).revision==1 && service.inspect(1).actors[0]->hp==4 &&
                    service.inspect(1).actors[14]->hp==100 && !saved_defeat,
                    "Failed defeat persistence committed a partial exchange");
            require(!service.release_finished_diagnostic(*session),"Uncommitted defeat released battle");
            commit_fails=false;
            require(world.handle(*session,attack).has_value() && commits==2 && saved_defeat,
                    "Defeat retry failed to commit");
            const auto& lost=service.inspect(1);
            require(lost.state==BattleState::Finished && lost.victorious_side==1 &&
                    lost.revision==3 && lost.actors[0]->hp==0 && lost.actors[14]->hp==82,
                    "Retaliation did not preserve the defeated actor at zero HP");
            const auto restored=Battle::restore(*saved_defeat);
            require(restored.inspect().state==BattleState::Finished &&
                    restored.inspect().victorious_side==1 && restored.inspect().actors[0]->hp==0,
                    "Defeat checkpoint resurrected the player");
            require(!service.diagnostic_round_ready(*session) &&
                    !service.release_finished_diagnostic(*session) && !world.handle(*session,attack),
                    "Defeat allowed another action or released before receipt");
            rejects([&]{service.rearm_diagnostic(*session,3);});
            require(!world.handle(*session,wrong_completion),"Defeat admitted foreign receipt");
            require(world.handle(*session,completion).has_value() && commits==2 &&
                    service.inspect(1).actors[0]->hp==0,"Defeat receipt mutated committed state");
            require(!world.handle(*session,completion),"Defeat receipt replay accepted");
            require(service.release_finished_diagnostic(*session) &&
                    session->state()==SessionState::InWorld && !service.release_finished_diagnostic(*session),
                    "Defeat did not release exactly once");
        }
        std::cout<<"Native command -> session authorization -> Lua -> atomic battle -> envelope checks passed\n";
    }catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}
}
