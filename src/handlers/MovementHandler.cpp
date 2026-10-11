#include "handlers/MovementHandler.h"
#include "handlers/HandlerUtil.h"
#include "protocol/OpcodeDispatcher.h"
#include "db/CharacterRepository.h"
#include <spdlog/spdlog.h>
namespace god2 {
void register_movement_handlers(OpcodeDispatcher& d) {
    d.register_handler(Opcode::C2S_PlayerMove,[](HandlerContext& c,PacketReader& r) {
        const auto x=r.read_i32(), y=r.read_i32(); require_end(r);
        if(x<0 || y<0 || x>100000 || y>100000) throw std::runtime_error("Mock map bounds exceeded");
        auto p=c.world.find_player(c.session.id()); if(!p) throw std::runtime_error("Player unavailable");
        auto updated=p->character; updated.x=x; updated.y=y;
        c.database.characters().save(updated);
        p->character=updated; p->x=x; p->y=y;
        PacketWriter w; w.write_u32(wire_id(p->id)); w.write_i32(x); w.write_i32(y);
        spdlog::debug("MOCK movement player={} x={} y={}",p->id,x,y);
        c.world.get_or_create_map(p->map_id).broadcast(Packet{static_cast<std::uint16_t>(Opcode::S2C_PlayerMove),w.bytes()});
    });
}
}
