#include "handlers/BattleHandler.h"
#include "handlers/HandlerUtil.h"
#include "protocol/OpcodeDispatcher.h"
#include "game/FixtureBattle.h"
#include <nlohmann/json.hpp>
namespace god2 {
namespace {
nlohmann::json combatant(const FixtureCombatant& c) {
    return {{"hp",c.hp},{"max_hp",c.max_hp},{"mp",c.mp},{"max_mp",c.max_mp},
        {"physical_attack",c.physical_attack},{"magical_attack",c.magical_attack},
        {"physical_defense",c.physical_defense},{"magical_defense",c.magical_defense}};
}
nlohmann::json action(const FixtureDamage& a) {
    return {{"damage",a.damage},{"mp_cost",a.mp_cost},{"critical",a.critical}};
}
void send_snapshot(Session& session,Opcode opcode,const FixtureBattleSnapshot& s) {
    const nlohmann::json json={{"authority","CUSTOM_TEST_NOT_NATIVE"},
        {"battle_id",s.battle_id},{"turn",s.turn},{"outcome",s.outcome},
        {"player",combatant(s.player)},{"monster",combatant(s.monster)},
        {"player_action",action(s.player_action)},{"monster_action",action(s.monster_action)}};
    PacketWriter w;w.write_string(json.dump());respond(session,opcode,w);
}
}
void register_battle_handlers(OpcodeDispatcher& d) {
    d.register_handler(Opcode::C2S_BattleAction,[](HandlerContext& c,PacketReader& r) {
        if(!c.fixture_battles) {
            send_error(c.session,"Custom test battle is disabled; native combat is not implemented");
            return;
        }
        const auto command=r.read_u8();
        if(command==0) {
            require_end(r);
            if(c.session.state()!=SessionState::InWorld) throw std::runtime_error("Already in battle");
            const auto result=c.fixture_battles->start(c.session.id());
            c.session.set_state(SessionState::InBattle);
            send_snapshot(c.session,Opcode::S2C_BattleStart,result);
            return;
        }
        if(command!=1 && command!=2) throw std::runtime_error("Unknown custom battle action");
        const auto battle=r.read_u32();
        const auto turn=r.read_u32();
        const auto skill=command==1?r.read_u8():std::uint8_t{};
        require_end(r);
        if(c.session.state()!=SessionState::InBattle) throw std::runtime_error("No active battle");
        const auto result=command==1?c.fixture_battles->act(c.session.id(),battle,turn,skill):
                                      c.fixture_battles->flee(c.session.id(),battle,turn);
        if(result.outcome!="active") c.session.set_state(SessionState::InWorld);
        send_snapshot(c.session,Opcode::S2C_BattleResult,result);
    });
}
}
