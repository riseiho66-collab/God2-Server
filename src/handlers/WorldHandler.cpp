#include "handlers/WorldHandler.h"
#include "handlers/HandlerUtil.h"
#include "protocol/OpcodeDispatcher.h"
#include "db/CharacterRepository.h"
namespace god2 {
namespace {
PacketWriter spawn_payload(const Player& p) {
    PacketWriter w;
    w.write_u32(wire_id(p.id)); w.write_u32(wire_id(p.character.id)); w.write_u32(p.map_id);
    w.write_i32(p.x); w.write_i32(p.y); w.write_u8(0); w.write_u32(p.character.hp); w.write_u32(p.character.mp);
    return w;
}
}
void register_world_handlers(OpcodeDispatcher& d) {
    d.register_handler(Opcode::C2S_EnterWorld,[](HandlerContext& c,PacketReader& r) {
        require_end(r);
        const auto ch=c.database.characters().find_by_id(c.session.character_id);
        if(!ch || ch->account_id!=c.session.account_id) throw std::runtime_error("Character unavailable");
        if(c.world.character_online(ch->id)) {
            // Another session may have entered after this session selected it.
            c.session.character_id=0;
            c.session.set_state(SessionState::Authenticated);
            throw std::runtime_error("Character already in world; select another character");
        }
        auto p=std::make_shared<Player>(); p->id=c.session.id(); p->type=EntityType::Player;
        p->map_id=ch->map_id; p->x=ch->x; p->y=ch->y; p->character=*ch; p->session=c.session.shared_from_this();
        const auto w=spawn_payload(*p);
        c.world.add_player(p); c.session.set_state(SessionState::InWorld);
        respond(c.session,Opcode::S2C_EnterWorld,w);
        c.world.get_or_create_map(ch->map_id).broadcast(Packet{static_cast<std::uint16_t>(Opcode::S2C_PlayerSpawn),w.bytes()});
        for(const auto& other:c.world.players_on_map(ch->map_id))
            if(other->id!=p->id) respond(c.session,Opcode::S2C_PlayerSpawn,spawn_payload(*other));
    });
}
}
