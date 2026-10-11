#include "handlers/HeartbeatHandler.h"
#include "handlers/HandlerUtil.h"
#include "protocol/OpcodeDispatcher.h"
#include "core/Time.h"
namespace god2 {
void register_heartbeat_handlers(OpcodeDispatcher& d) {
    d.register_handler(Opcode::C2S_Heartbeat,[](HandlerContext& c,PacketReader& r) {
        require_end(r); PacketWriter w; w.write_u32(unix_seconds()); respond(c.session,Opcode::S2C_HeartbeatAck,w);
    });
}
}
