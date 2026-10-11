#include "handlers/CharacterHandler.h"
#include "handlers/HandlerUtil.h"
#include "protocol/OpcodeDispatcher.h"
#include "db/CharacterRepository.h"
namespace god2 {
void register_character_handlers(OpcodeDispatcher& d) {
    d.register_handler(Opcode::C2S_RequestCharList,[](HandlerContext& c,PacketReader& r) {
        require_end(r);
        const auto chars=c.database.characters().list_for_account(c.session.account_id);
        if(chars.size()>100) throw std::runtime_error("Placeholder character list exceeds limit");
        PacketWriter w; w.write_u16(static_cast<std::uint16_t>(chars.size()));
        for(const auto& ch:chars) {
            w.write_u32(wire_id(ch.id)); w.write_string(ch.name); w.write_u32(ch.level); w.write_u32(ch.job);
            w.write_u32(ch.map_id); w.write_i32(ch.x); w.write_i32(ch.y);
        }
        respond(c.session,Opcode::S2C_CharacterList,w);
    });
    d.register_handler(Opcode::C2S_SelectCharacter,[](HandlerContext& c,PacketReader& r) {
        const auto id=r.read_u32(); require_end(r);
        const auto ch=c.database.characters().find_by_id(id);
        if(!ch || ch->account_id!=c.session.account_id) throw std::runtime_error("Character not owned by account");
        if(c.world.character_online(id)) throw std::runtime_error("Character already in world");
        PacketWriter w; w.write_u8(0); w.write_u32(id);
        c.session.character_id=id; c.session.set_state(SessionState::CharacterSelected);
        respond(c.session,Opcode::S2C_SelectCharResult,w);
    });
}
}
