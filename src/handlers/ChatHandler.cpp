#include "handlers/ChatHandler.h"
#include "handlers/HandlerUtil.h"
#include "protocol/OpcodeDispatcher.h"
#include "text/ChineseText.h"
namespace god2 {
void register_chat_handlers(OpcodeDispatcher& d) {
    d.register_handler(Opcode::C2S_ChatMessage,[](HandlerContext& c,PacketReader& r) {
        auto text=r.read_string(); require_end(r);
        if(text.empty() || text.size()>512) throw std::runtime_error("Invalid chat length");
        auto p=c.world.find_player(c.session.id()); if(!p) throw std::runtime_error("Player unavailable");
        // CUSTOM-0029: explicit per-player selection in the placeholder chat route.
        if(text=="/lang zh-CN" || text=="/lang zh-TW") {
            p->text_language=text=="/lang zh-CN"?ChineseLanguage::Simplified:ChineseLanguage::Traditional;
            PacketWriter confirmation; confirmation.write_u32(wire_id(p->id));
            confirmation.write_string(p->text_language==ChineseLanguage::Simplified?
                "Language: 简体中文":"語言：繁體中文");
            c.session.send(Packet{static_cast<std::uint16_t>(Opcode::S2C_ChatMessage),confirmation.bytes()});
            return;
        }
        if(!c.chinese_text || !ChineseText::valid_utf8(text) || text.find('\0')!=std::string::npos)
            throw std::runtime_error("Chat requires valid UTF-8 text");
        for(const auto& recipient:c.world.players_on_map(p->map_id)) {
            if(auto session=recipient->session.lock()) {
                PacketWriter message; message.write_u32(wire_id(p->id));
                message.write_string(c.chinese_text->convert(text,recipient->text_language));
                session->send(Packet{static_cast<std::uint16_t>(Opcode::S2C_ChatMessage),message.bytes()});
            }
        }
    });
}
}
