#include "handlers/NpcHandler.h"
#include "handlers/HandlerUtil.h"
#include "protocol/OpcodeDispatcher.h"
#include "text/ChineseText.h"
namespace god2 {
void register_npc_handlers(OpcodeDispatcher& d) {
    d.register_handler(Opcode::C2S_NpcTalk,[](HandlerContext& c,PacketReader& r) {
        const auto npc=r.read_u32(); require_end(r);
        auto p=c.world.find_player(c.session.id()); if(!p) throw std::runtime_error("Player unavailable");
        auto dialog=c.lua.talk(npc,p->id,p->character.name);
        // CUSTOM-0029: translate only player-visible values, preserving option IDs.
        if(c.chinese_text)
            dialog=c.chinese_text->convert_dialogue_json(dialog,p->text_language);
        PacketWriter w; w.write_u32(npc); w.write_string(dialog); respond(c.session,Opcode::S2C_NpcDialog,w);
    });
}
}
