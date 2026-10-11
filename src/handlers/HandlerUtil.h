#pragma once
#include "handlers/HandlerContext.h"
#include "protocol/PacketWriter.h"
#include "protocol/Opcode.h"
#include "protocol/PacketReader.h"
#include <limits>
#include <stdexcept>
namespace god2 {
inline void require_end(PacketReader& r) { if(r.remaining()) throw std::runtime_error("Unexpected trailing payload"); }
inline std::uint32_t wire_id(std::uint64_t id) {
    if(id>std::numeric_limits<std::uint32_t>::max()) throw std::runtime_error("Placeholder ID exceeds u32");
    return static_cast<std::uint32_t>(id);
}
inline void respond(Session& s,Opcode op,const PacketWriter& w) { s.send(Packet{static_cast<std::uint16_t>(op),w.bytes()}); }
}
