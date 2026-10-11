#include "db/SqliteDatabase.h"
#include "handlers/HandlerContext.h"
#include "protocol/OpcodeDispatcher.h"
#include "protocol/PacketWriter.h"
#include <filesystem>
#include <stdexcept>

namespace {
void check(bool value, const char* message) {
    if (!value) throw std::runtime_error(std::string("Dispatcher test: ") + message);
}
struct Connection {
    asio::io_context io;
    std::shared_ptr<god2::Session> session = std::make_shared<god2::Session>(
        asio::ip::tcp::socket(io), io.get_executor(), 7, false,
        god2::Session::PacketHandler{}, god2::Session::DisconnectHandler{});
    ~Connection() {
        session->close();
        io.restart();
        io.poll();
    }
};
}

void test_dispatcher() {
    using namespace god2;
    SqliteDatabase database(":memory:");
    database.initialize();
    database.migrate();
    LuaEngine lua(std::filesystem::path(GOD2_SOURCE_DIR) / "scripts");
    check(lua.initialize(), "Lua initializes on test thread");
    World world;
    check(world.initialize(), "world initializes");
    Connection connection;
    HandlerContext context{*connection.session, world, database, lua, true};
    OpcodeDispatcher dispatcher;
    unsigned calls = 0;
    dispatcher.register_handler(Opcode::C2S_Heartbeat, [&](HandlerContext& ctx, PacketReader& reader) {
        check(&ctx == &context, "handler receives original context");
        check(reader.read_u32() == 0x12345678, "handler receives packet payload");
        check(reader.remaining() == 0, "reader consumes payload");
        ++calls;
    });
    bool duplicate = false;
    try { dispatcher.register_handler(Opcode::C2S_Heartbeat, [](HandlerContext&, PacketReader&) {}); }
    catch (const std::logic_error&) { duplicate = true; }
    check(duplicate, "duplicate registration rejected");

    PacketWriter writer;
    writer.write_u32(0x12345678);
    Packet heartbeat{static_cast<std::uint16_t>(Opcode::C2S_Heartbeat), writer.bytes()};
    dispatcher.dispatch(context, heartbeat);
    check(calls == 1, "original handler survives duplicate registration");
    Packet unknown{0x7777, {}};
    dispatcher.dispatch(context, unknown);
    Packet truncated{static_cast<std::uint16_t>(Opcode::C2S_Heartbeat), {1}};
    dispatcher.dispatch(context, truncated);
    check(calls == 1, "unknown and malformed packets do not invoke successful handler");
    dispatcher.dispatch(context, heartbeat);
    check(calls == 2, "dispatch continues after unknown opcode and handler exception");

    unsigned moves = 0;
    dispatcher.register_handler(Opcode::C2S_PlayerMove, [&](HandlerContext&, PacketReader&) { ++moves; });
    Packet move{static_cast<std::uint16_t>(Opcode::C2S_PlayerMove), {}};
    dispatcher.dispatch(context, move);
    check(moves == 0, "out-of-state handler blocked");
    connection.session->set_state(SessionState::InWorld);
    dispatcher.dispatch(context, move);
    check(moves == 1, "registered handler runs in allowed state");
    connection.session->set_state(SessionState::Disconnected);
    dispatcher.dispatch(context, heartbeat);
    check(calls == 2, "disconnected session ignored");
}
