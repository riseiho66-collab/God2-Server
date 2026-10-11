#include "protocol/OpcodeDispatcher.h"
#include "handlers/HandlerContext.h"
#include "protocol/PacketWriter.h"
#include "core/HexDump.h"
#include <spdlog/spdlog.h>
namespace god2 {
bool state_allows(Opcode opcode,SessionState s) {
    switch(opcode) {
    case Opcode::C2S_Handshake: return s==SessionState::Connected;
    case Opcode::C2S_LoginRequest: return s==SessionState::Connected || s==SessionState::Handshaked;
    case Opcode::C2S_RequestCharList:
    case Opcode::C2S_SelectCharacter: return s==SessionState::Authenticated;
    case Opcode::C2S_EnterWorld: return s==SessionState::CharacterSelected;
    case Opcode::C2S_PlayerMove:
    case Opcode::C2S_ChatMessage:
    case Opcode::C2S_NpcTalk: return s==SessionState::InWorld;
    case Opcode::C2S_BattleAction: return s==SessionState::InBattle;
    case Opcode::C2S_Heartbeat: return s!=SessionState::Disconnected;
    default: return false;
    }
}
void send_error(Session& s,const std::string& message) {
    PacketWriter w; w.write_string(message.substr(0,512));
    s.send(Packet{static_cast<std::uint16_t>(Opcode::S2C_Error),w.bytes()});
}
void OpcodeDispatcher::register_handler(Opcode opcode,PacketHandler handler) {
    if(!handlers_.emplace(static_cast<std::uint16_t>(opcode),std::move(handler)).second)
        throw std::logic_error("Duplicate opcode registration");
}
void OpcodeDispatcher::dispatch(HandlerContext& ctx,Packet& packet) {
    if(ctx.session.state()==SessionState::Disconnected) return;
    const auto it=handlers_.find(packet.opcode);
    if(it==handlers_.end()) {
        spdlog::warn("Unknown opcode session={} opcode={:04X} size={} hex={}",ctx.session.id(),packet.opcode,packet.payload.size(),hex_dump(std::span(packet.payload).first(std::min<std::size_t>(packet.payload.size(),256))));
        send_error(ctx.session,"Unknown PLACEHOLDER opcode"); return;
    }
    const bool fixture_battle_entry=ctx.fixture_battles &&
        packet.opcode==static_cast<std::uint16_t>(Opcode::C2S_BattleAction) &&
        ctx.session.state()==SessionState::InWorld;
    if(!fixture_battle_entry && !state_allows(static_cast<Opcode>(packet.opcode),ctx.session.state())) {
        spdlog::warn("Invalid state session={} opcode={:04X} state={}",ctx.session.id(),packet.opcode,static_cast<int>(ctx.session.state()));
        send_error(ctx.session,"Opcode not allowed in current session state"); return;
    }
    try { PacketReader reader(packet.payload); it->second(ctx,reader); }
    catch(const std::exception& e) {
        spdlog::warn("Handler failed session={} opcode={:04X}: {}",ctx.session.id(),packet.opcode,e.what());
        send_error(ctx.session,"Request rejected");
    }
}
}
