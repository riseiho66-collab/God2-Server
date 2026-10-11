#include "db/SqliteDatabase.h"
#include "handlers/HandlerContext.h"
#include "handlers/RegisterHandlers.h"
#include "net/IoContextPool.h"
#include "net/TcpServer.h"
#include "protocol/God2ProtocolSpec.h"
#include "protocol/OpcodeDispatcher.h"
#include "protocol/PacketWriter.h"
#include "text/ChineseText.h"
#include <nlohmann/json.hpp>
#include <spdlog/spdlog.h>
#include <spdlog/sinks/ostream_sink.h>
#include <array>
#include <atomic>
#include <chrono>
#include <condition_variable>
#include <filesystem>
#include <future>
#include <mutex>
#include <sstream>
#include <stdexcept>
#include <thread>

namespace {
using namespace god2;
using namespace std::chrono_literals;
void check(bool value, const std::string& message) {
    if (!value) throw std::runtime_error("Network test: " + message);
}
Packet packet(Opcode opcode, const PacketWriter& writer = {}) {
    return {static_cast<std::uint16_t>(opcode), writer.bytes()};
}

struct PacketLogCapture {
    std::ostringstream output;
    std::shared_ptr<spdlog::logger> previous = spdlog::get("packet");
    PacketLogCapture() {
        auto sink = std::make_shared<spdlog::sinks::ostream_sink_mt>(output);
        auto log = std::make_shared<spdlog::logger>("packet", sink);
        log->set_level(spdlog::level::debug);
        spdlog::drop("packet");
        spdlog::register_logger(log);
    }
    ~PacketLogCapture() {
        spdlog::drop("packet");
        if (previous) spdlog::register_logger(previous);
    }
};

class ServerFixture {
public:
    // Network teardown may release handlers that still own the game strand.
    // Declare game first so it outlives the network context and its handlers.
    asio::io_context game;
    IoContextPool network;
    asio::executor_work_guard<asio::io_context::executor_type> game_work{game.get_executor()};
    std::thread game_thread;
    std::promise<std::uint16_t> ready;
    std::function<void()> stop_server;
    std::exception_ptr failure;
    std::atomic<unsigned> disconnects{0};
    std::atomic<unsigned> persisted_moves{0};
    std::atomic<unsigned> world_disconnects{0};
    bool forced = false;

    std::uint16_t start() {
        auto future = ready.get_future();
        network.start(3);
        game_thread = std::thread([this] {
            bool announced = false;
            try {
                // Construction, use, and destruction all occur on this thread.
                SqliteDatabase database(":memory:");
                database.initialize();
                database.migrate();
                LuaEngine lua(std::filesystem::path(GOD2_SOURCE_DIR) / "scripts");
                check(lua.initialize() && lua.load_script("bootstrap.lua"), "Lua bootstrap");
                ChineseText chinese_text(std::filesystem::path(GOD2_SOURCE_DIR) / "resources/opencc");
                World world;
                check(world.initialize(), "world initialization");
                OpcodeDispatcher dispatcher;
                register_handlers(dispatcher);
                const auto owner = std::this_thread::get_id();
                TcpServer server(network.context(), game.get_executor(), "127.0.0.1", 0, 16, true,
                    [&](std::shared_ptr<Session> session, Packet request) {
                        try {
                            check(std::this_thread::get_id() == owner, "packet runs on game thread");
                            HandlerContext ctx{*session, world, database, lua, true, nullptr, &chinese_text};
                            dispatcher.dispatch(ctx, request);
                        } catch (...) {
                            if (!failure) failure = std::current_exception();
                            session->close();
                        }
                    },
                    [&](std::shared_ptr<Session> session) {
                        try {
                            check(std::this_thread::get_id() == owner, "disconnect runs on game thread");
                            check(session->state() == SessionState::Disconnected, "terminal state");
                            if (session->character_id) {
                                const auto character = database.characters().find_by_id(session->character_id);
                                const auto player = world.find_player(session->id());
                                check(character && player && character->x == player->x && character->y == player->y,
                                      "database position matches world at disconnect");
                                if (character->x == 321 && character->y == 654) ++persisted_moves;
                                ++world_disconnects;
                            }
                            world.remove_player(session->id());
                            check(!world.find_player(session->id()), "disconnect removes player");
                        } catch (...) { if (!failure) failure = std::current_exception(); }
                        ++disconnects;
                    });
                stop_server = [&server, this] { server.stop(); network.stop(); };
                server.start();
                ready.set_value(server.port());
                announced = true;
                game.run();
                stop_server = {};
            } catch (...) {
                if (!failure) failure = std::current_exception();
                if (!announced) ready.set_exception(failure);
                network.context().stop();
            }
        });
        check(future.wait_for(5s) == std::future_status::ready, "server startup timed out");
        return future.get();
    }

    void stop() {
        if (!game_thread.joinable()) { network.stop(); network.join(); return; }
        // A watchdog bounds teardown even when a failed assertion interrupts the
        // client flow or a shutdown regression strands an executor work guard.
        std::mutex mutex;
        std::condition_variable cv;
        bool done = false;
        std::thread watchdog([&] {
            std::unique_lock lock(mutex);
            if (!cv.wait_for(lock, 8s, [&] { return done; })) {
                forced = true;
                network.context().stop();
                game.stop();
            }
        });
        asio::post(game, [this] {
            if (stop_server) stop_server();
            else network.stop();
        });
        network.join();
        game_work.reset();
        game_thread.join();
        {
            std::lock_guard lock(mutex);
            done = true;
        }
        cv.notify_one();
        watchdog.join();
    }
    ~ServerFixture() { stop(); }
};

class Client {
    asio::io_context io;
    asio::ip::tcp::socket socket{io};
    God2ProtocolSpec codec;

    template<class Initiate> asio::error_code operation(Initiate initiate) {
        io.restart();
        asio::steady_timer timer(io, 3s);
        asio::error_code result;
        bool timed_out = false;
        timer.async_wait([&](const asio::error_code& ec) {
            if (!ec) { timed_out = true; asio::error_code ignored; socket.cancel(ignored); }
        });
        initiate([&](const asio::error_code& ec, auto...) { result = ec; timer.cancel(); });
        io.run();
        check(!timed_out, "client operation timed out");
        return result;
    }
    void read(std::span<std::uint8_t> bytes) {
        const auto ec = operation([&](auto callback) {
            asio::async_read(socket, asio::buffer(bytes.data(), bytes.size()), callback);
        });
        check(!ec, "read: " + ec.message());
    }
public:
    explicit Client(std::uint16_t port) {
        auto ec = operation([&](auto callback) {
            socket.async_connect({asio::ip::make_address("127.0.0.1"), port}, callback);
        });
        check(!ec, "connect: " + ec.message());
        socket.set_option(asio::ip::tcp::no_delay(true));
    }
    void write(std::span<const std::uint8_t> bytes) {
        const auto ec = operation([&](auto callback) {
            asio::async_write(socket, asio::buffer(bytes.data(), bytes.size()), callback);
        });
        check(!ec, "write: " + ec.message());
    }
    void send(const Packet& request) { write(codec.encode(request)); }
    void coalesced(std::initializer_list<Packet> requests) {
        std::vector<std::uint8_t> bytes;
        for (const auto& request : requests) {
            const auto frame = codec.encode(request);
            bytes.insert(bytes.end(), frame.begin(), frame.end());
        }
        write(bytes);
    }
    void fragmented(const Packet& request) {
        const auto bytes = codec.encode(request);
        for (const auto byte : bytes) {
            write(std::span<const std::uint8_t>(&byte, 1));
            std::this_thread::sleep_for(2ms);
        }
    }
    Packet receive(Opcode opcode) {
        std::array<std::uint8_t, 2> header{};
        read(header);
        const std::size_t length = header[0] | (static_cast<unsigned>(header[1]) << 8);
        check(length >= 4, "response frame length");
        std::vector<std::uint8_t> bytes(length);
        bytes[0] = header[0]; bytes[1] = header[1];
        read(std::span(bytes).subspan(2));
        Buffer input;
        input.append(bytes);
        std::vector<Packet> packets;
        const auto result = codec.try_decode(input, packets);
        check(result.ok && packets.size() == 1 && input.size() == 0, "decode response");
        if(packets[0].opcode != static_cast<std::uint16_t>(opcode)) {
            std::string detail;
            if(packets[0].opcode == static_cast<std::uint16_t>(Opcode::S2C_Error)) {
                PacketReader error(packets[0].payload);
                detail = ": " + error.read_string();
            }
            check(false,"unexpected opcode " + std::to_string(packets[0].opcode) +
                  " while expecting " + std::to_string(static_cast<std::uint16_t>(opcode)) + detail);
        }
        return std::move(packets[0]);
    }
    void heartbeat() {
        send(packet(Opcode::C2S_Heartbeat));
        heartbeat_response();
    }
    void heartbeat_response() {
        const auto response = receive(Opcode::S2C_HeartbeatAck);
        PacketReader reader(response.payload);
        check(reader.read_u32() > 0 && reader.remaining() == 0, "heartbeat timestamp");
    }
    void error() {
        const auto response = receive(Opcode::S2C_Error);
        PacketReader reader(response.payload);
        check(!reader.read_string().empty() && reader.remaining() == 0, "error payload");
    }
    void closed() {
        std::array<std::uint8_t, 1> bytes{};
        const auto ec = operation([&](auto callback) {
            socket.async_read_some(asio::buffer(bytes), callback);
        });
        check(ec == asio::error::eof || ec == asio::error::connection_reset ||
              ec == asio::error::connection_aborted, "server closed connection");
    }
};

std::uint32_t login_as(Client& client, const std::string& name) {
    PacketWriter login;
    login.write_string(name); login.write_string("mock-password"); login.write_string("test-v1");
    client.send(packet(Opcode::C2S_LoginRequest, login));
    const auto response = client.receive(Opcode::S2C_LoginResult);
    PacketReader reader(response.payload);
    check(reader.read_u8() == 0, "additional client login succeeds");
    const auto id = reader.read_u32();
    check(id != 0 && reader.read_string() == "Login OK (MOCK)" && reader.remaining() == 0,
          "additional client login payload");
    return id;
}

std::uint32_t character_list(Client& client, std::int32_t x = 100, std::int32_t y = 100) {
    client.send(packet(Opcode::C2S_RequestCharList));
    const auto response = client.receive(Opcode::S2C_CharacterList);
    PacketReader reader(response.payload);
    check(reader.read_u16() == 1, "additional account has one character");
    const auto id = reader.read_u32();
    check(id != 0 && reader.read_string() == "TestPlayer", "additional character identity");
    check(reader.read_u32() == 1 && reader.read_u32() == 1 && reader.read_u32() == 1,
          "additional character level, job and map");
    check(reader.read_i32() == x && reader.read_i32() == y && reader.remaining() == 0,
          "character list position");
    return id;
}

void select_character(Client& client, std::uint32_t id) {
    PacketWriter writer;
    writer.write_u32(id);
    client.send(packet(Opcode::C2S_SelectCharacter, writer));
    const auto response = client.receive(Opcode::S2C_SelectCharResult);
    PacketReader reader(response.payload);
    check(reader.read_u8() == 0 && reader.read_u32() == id && reader.remaining() == 0,
          "additional character select succeeds");
}

std::vector<std::uint8_t> spawn_payload(std::uint32_t player, std::uint32_t character,
                                      std::int32_t x = 100, std::int32_t y = 100) {
    PacketWriter writer;
    writer.write_u32(player); writer.write_u32(character); writer.write_u32(1);
    writer.write_i32(x); writer.write_i32(y); writer.write_u8(0);
    writer.write_u32(100); writer.write_u32(50);
    return writer.bytes();
}

Packet enter_world(Client& client, std::uint32_t character) {
    client.send(packet(Opcode::C2S_EnterWorld));
    const auto response = client.receive(Opcode::S2C_EnterWorld);
    PacketReader reader(response.payload);
    const auto player = reader.read_u32();
    check(player != 0 && response.payload == spawn_payload(player, character), "additional enter-world payload");
    return response;
}
}

void test_network() {
    PacketLogCapture packet_log;
    ServerFixture server;
    const auto port = server.start();
    check(port != 0, "ephemeral port published");
    Client client(port);
    client.coalesced({packet(Opcode::C2S_PlayerMove), Packet{0x7777, {}}, packet(Opcode::C2S_Heartbeat)});
    client.error(); client.error(); client.heartbeat_response();

    client.fragmented(packet(Opcode::C2S_Handshake));
    auto response = client.receive(Opcode::S2C_HandshakeAck);
    PacketReader handshake(response.payload);
    check(handshake.read_string() == "GOD2 PLACEHOLDER v1" && handshake.remaining() == 0, "handshake");

    // A valid frame containing an incomplete login string must not kill TCP.
    client.send(Packet{static_cast<std::uint16_t>(Opcode::C2S_LoginRequest), {5, 0, 'x'}});
    client.error(); client.heartbeat();
    PacketWriter login;
    login.write_string("network-test"); login.write_string("mock-password"); login.write_string("test-v1");
    client.fragmented(packet(Opcode::C2S_LoginRequest, login));
    response = client.receive(Opcode::S2C_LoginResult);
    PacketReader logged_in(response.payload);
    check(logged_in.read_u8() == 0, "login status");
    const auto account_id = logged_in.read_u32();
    check(account_id != 0, "account id");
    check(logged_in.read_string() == "Login OK (MOCK)" && logged_in.remaining() == 0, "mock login result");

    client.send(packet(Opcode::C2S_RequestCharList));
    response = client.receive(Opcode::S2C_CharacterList);
    PacketReader characters(response.payload);
    check(characters.read_u16() == 1, "one initial character");
    const auto character_id = characters.read_u32();
    check(character_id != 0 && characters.read_string() == "TestPlayer", "character identity");
    check(characters.read_u32() == 1 && characters.read_u32() == 1, "level and job");
    check(characters.read_u32() == 1 && characters.read_i32() == 100 && characters.read_i32() == 100,
          "initial character position");
    check(characters.remaining() == 0, "character list consumed");

    PacketWriter select;
    select.write_u32(character_id);
    client.coalesced({packet(Opcode::C2S_SelectCharacter, select), packet(Opcode::C2S_EnterWorld)});
    response = client.receive(Opcode::S2C_SelectCharResult);
    PacketReader selected(response.payload);
    check(selected.read_u8() == 0 && selected.read_u32() == character_id && selected.remaining() == 0,
          "character selected before coalesced enter-world");
    response = client.receive(Opcode::S2C_EnterWorld);
    PacketReader entered(response.payload);
    const auto player_id = entered.read_u32();
    check(player_id != 0 && entered.read_u32() == character_id && entered.read_u32() == 1, "entered identity");
    check(entered.read_i32() == 100 && entered.read_i32() == 100 && entered.read_u8() == 0, "spawn position");
    check(entered.read_u32() == 100 && entered.read_u32() == 50 && entered.remaining() == 0, "spawn stats");
    check(client.receive(Opcode::S2C_PlayerSpawn).payload == response.payload, "world spawn broadcast");

    PacketWriter move, chat, npc;
    move.write_i32(321); move.write_i32(654);
    chat.write_string("loopback says hello"); npc.write_u32(1001);
    client.coalesced({packet(Opcode::C2S_PlayerMove, move), packet(Opcode::C2S_ChatMessage, chat),
                      packet(Opcode::C2S_NpcTalk, npc), packet(Opcode::C2S_Heartbeat)});
    response = client.receive(Opcode::S2C_PlayerMove);
    PacketReader moved(response.payload);
    check(moved.read_u32() == player_id && moved.read_i32() == 321 && moved.read_i32() == 654 &&
          moved.remaining() == 0, "movement broadcast");
    response = client.receive(Opcode::S2C_ChatMessage);
    PacketReader chatted(response.payload);
    check(chatted.read_u32() == player_id && chatted.read_string() == "loopback says hello" &&
          chatted.remaining() == 0, "chat broadcast");
    response = client.receive(Opcode::S2C_NpcDialog);
    PacketReader talked(response.payload);
    check(talked.read_u32() == 1001, "NPC identity");
    const auto dialog = nlohmann::json::parse(talked.read_string());
    check(dialog["text"] == "Hello, welcome to GOD2 rebuild server." && dialog["options"].size() == 2 &&
          talked.remaining() == 0, "Lua NPC dialogue");
    client.heartbeat_response();

    client.coalesced({packet(Opcode::C2S_PlayerMove), packet(Opcode::C2S_Handshake),
                      Packet{0x7777, {1, 2}}, packet(Opcode::C2S_Heartbeat)});
    client.error(); client.error(); client.error(); client.heartbeat_response();

    Client newcomer(port);
    const auto newcomer_account = login_as(newcomer, "network-newcomer");
    check(newcomer_account != account_id, "newcomer uses a different account");
    const auto newcomer_character = character_list(newcomer);
    check(newcomer_character != character_id, "newcomer uses a different character");
    select_character(newcomer, newcomer_character);
    const auto newcomer_entry = enter_world(newcomer, newcomer_character);
    const auto original_snapshot = spawn_payload(player_id, character_id, 321, 654);
    const auto newcomer_spawn_a = newcomer.receive(Opcode::S2C_PlayerSpawn).payload;
    const auto newcomer_spawn_b = newcomer.receive(Opcode::S2C_PlayerSpawn).payload;
    check((newcomer_spawn_a == newcomer_entry.payload && newcomer_spawn_b == original_snapshot) ||
          (newcomer_spawn_b == newcomer_entry.payload && newcomer_spawn_a == original_snapshot),
          "newcomer receives self spawn and existing player's current snapshot exactly once");
    check(client.receive(Opcode::S2C_PlayerSpawn).payload == newcomer_entry.payload,
          "existing player receives newcomer spawn");
    newcomer.heartbeat(); client.heartbeat();

    Client duplicate(port);
    check(login_as(duplicate, "network-test") == account_id, "duplicate uses original account");
    check(character_list(duplicate, 321, 654) == character_id, "duplicate sees original character");
    duplicate.coalesced({packet(Opcode::C2S_SelectCharacter, select), packet(Opcode::C2S_Heartbeat)});
    duplicate.error(); duplicate.heartbeat_response();
    check(character_list(duplicate, 321, 654) == character_id,
          "online-character select rejection preserves Authenticated state");

    Client winner(port), loser(port);
    const auto race_account = login_as(winner, "network-selection-race");
    check(race_account != account_id && race_account != newcomer_account, "race has a separate account");
    check(login_as(loser, "network-selection-race") == race_account, "race shares one account");
    const auto race_character = character_list(winner);
    check(character_list(loser) == race_character, "race shares one character");
    // Both selections complete while the character is still offline. This
    // deterministically exercises the stale selection at enter-world time.
    select_character(winner, race_character);
    select_character(loser, race_character);
    const auto winner_entry = enter_world(winner, race_character);
    bool saw_self = false, saw_original = false, saw_newcomer = false;
    for (unsigned i = 0; i < 3; ++i) {
        const auto snapshot = winner.receive(Opcode::S2C_PlayerSpawn).payload;
        if (snapshot == winner_entry.payload) { check(!saw_self, "no repeated self snapshot"); saw_self = true; }
        else if (snapshot == original_snapshot) { check(!saw_original, "no repeated original snapshot"); saw_original = true; }
        else if (snapshot == newcomer_entry.payload) { check(!saw_newcomer, "no repeated newcomer snapshot"); saw_newcomer = true; }
        else check(false, "unexpected world snapshot");
    }
    check(saw_self && saw_original && saw_newcomer, "winner receives complete map snapshot");
    check(client.receive(Opcode::S2C_PlayerSpawn).payload == winner_entry.payload, "original sees race winner");
    check(newcomer.receive(Opcode::S2C_PlayerSpawn).payload == winner_entry.payload, "newcomer sees race winner");
    loser.send(packet(Opcode::C2S_EnterWorld));
    loser.error();
    check(character_list(loser) == race_character, "lost enter-world race resets state to Authenticated");
    loser.heartbeat(); winner.heartbeat(); client.heartbeat(); newcomer.heartbeat();

    Client invalid_frame(port);
    invalid_frame.write(std::array<std::uint8_t, 2>{3, 0});
    invalid_frame.closed();
    client.heartbeat();
    // Leave the healthy socket open: server stop must close it and deliver the
    // disconnect callback while the game executor and its Lua VM remain alive.
    server.stop();
    client.closed();
    newcomer.closed(); duplicate.closed(); winner.closed(); loser.closed();
    check(!server.forced, "shutdown completed without watchdog intervention");
    if (server.failure) std::rethrow_exception(server.failure);
    check(server.disconnects == 6, "exactly one disconnect per admitted connection");
    check(server.world_disconnects == 3, "only three successfully entered sessions own world players");
    check(server.persisted_moves == 1, "game-thread persistence checked before destruction");
    const auto logged = packet_log.output.str();
    check(logged.find("[REDACTED LOGIN PAYLOAD]") != std::string::npos, "login dump redacted");
    check(logged.find("mock-password") == std::string::npos &&
          logged.find("6D 6F 63 6B 2D 70 61 73 73 77 6F 72 64") == std::string::npos,
          "password absent from text and hex packet logs");
}
