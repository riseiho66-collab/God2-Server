#pragma once
#include "protocol/Opcode.h"
#include "protocol/Packet.h"
#include "protocol/PacketReader.h"
#include "net/Session.h"
#include <functional>
#include <initializer_list>
#include <unordered_map>
#include <vector>
namespace god2 {
struct HandlerContext;
using PacketHandler=std::function<void(HandlerContext&,PacketReader&)>;
bool state_allows(Opcode opcode,SessionState state);
void send_error(Session& session,const std::string& message);
class OpcodeDispatcher {
public:
    void register_handler(Opcode opcode,PacketHandler handler);
    void dispatch(HandlerContext& ctx,Packet& packet);
private:
    std::unordered_map<std::uint16_t,PacketHandler> handlers_;
};
}
