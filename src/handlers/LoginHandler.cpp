#include "handlers/LoginHandler.h"
#include "handlers/HandlerUtil.h"
#include "protocol/OpcodeDispatcher.h"
#include "db/AccountRepository.h"
#include "db/CharacterRepository.h"
#include <spdlog/spdlog.h>
namespace god2 {
void register_login_handlers(OpcodeDispatcher& d) {
    d.register_handler(Opcode::C2S_Handshake,[](HandlerContext& c,PacketReader& r) {
        require_end(r);
        PacketWriter w; w.write_string("GOD2 PLACEHOLDER v1");
        c.session.set_state(SessionState::Handshaked); respond(c.session,Opcode::S2C_HandshakeAck,w);
    });
    d.register_handler(Opcode::C2S_LoginRequest,[](HandlerContext& c,PacketReader& r) {
        if(!c.mock_login) throw std::runtime_error("Real authentication has not been implemented");
        std::string name="mock";
        if(r.remaining()) {
            name=r.read_string(); const auto password=r.read_string(); const auto version=r.read_string();
            if(name.empty() || name.size()>64 || password.size()>256 || version.size()>64) throw std::runtime_error("Invalid mock login fields");
            require_end(r);
        }
        auto account=c.database.accounts().find_by_username(name);
        if(!account) account=c.database.accounts().create(name,"!MOCK-NOT-A-PASSWORD-HASH!");
        auto chars=c.database.characters().list_for_account(account->id);
        if(chars.empty()) {
            Character ch; ch.account_id=account->id; ch.name="TestPlayer";
            c.database.characters().create(ch);
        }
        PacketWriter w; w.write_u8(0); w.write_u32(wire_id(account->id)); w.write_string("Login OK (MOCK)");
        c.session.account_id=account->id; c.session.set_state(SessionState::Authenticated); c.session.notify_authenticated();
        respond(c.session,Opcode::S2C_LoginResult,w);
    });
}
}
