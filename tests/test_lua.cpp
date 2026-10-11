#include "scripting/LuaEngine.h"
#include "scripting/LuaInstructionBudget.h"
#include "core/Config.h"
#include "game/Monster.h"
#include <nlohmann/json.hpp>
#include <chrono>
#include <filesystem>
#include <fstream>
#include <functional>
#include <limits>
#include <stdexcept>
#include <string>
#include <thread>
#include <utility>
#include <vector>

namespace {
void expect(bool condition, const std::string& message) {
    if (!condition) throw std::runtime_error("Lua test: " + message);
}
void expect_error(const std::function<void()>& fn, const std::string& message) {
    try { fn(); }
    catch (const std::runtime_error&) { return; }
    throw std::runtime_error("Lua test: expected runtime_error: " + message);
}
struct Fixture {
    std::filesystem::path root;
    Fixture() {
        const auto seed = std::chrono::steady_clock::now().time_since_epoch().count();
        for (int i = 0; i < 100; ++i) {
            root = std::filesystem::temp_directory_path() /
                ("god2-lua-test-" + std::to_string(seed) + "-" + std::to_string(i));
            if (std::filesystem::create_directory(root)) return;
        }
        throw std::runtime_error("could not create Lua test directory");
    }
    ~Fixture() { std::error_code ec; std::filesystem::remove_all(root, ec); }
    void write(const std::string& name, const std::string& source) {
        const auto path = root / name;
        std::filesystem::create_directories(path.parent_path());
        std::ofstream stream(path, std::ios::binary | std::ios::trunc);
        stream << source;
        stream.close();
        expect(!stream.fail(), "write fixture " + name);
    }
};
std::string npc_script(const std::string& text) {
    return "register_npc(42, {name='fixture', on_talk=function(player) return {text='" +
        text + "', options={{id=1,text='ok'}}} end})";
}

void previous_hook(lua_State*, lua_Debug*) {}

void test_instruction_hook_restore() {
    using god2::detail::LuaInstructionBudget;
    sol::state lua;
    auto* state = lua.lua_state();
    std::array<unsigned char, LUA_EXTRASPACE> marker;
    marker.fill(0x5A);
    std::memcpy(lua_getextraspace(state), marker.data(), marker.size());
    lua_sethook(state, previous_hook, LUA_MASKCOUNT | LUA_MASKCALL, 71);
    auto check_restored = [&] {
        expect(lua_gethook(state) == previous_hook, "restore previous hook");
        expect(lua_gethookmask(state) == (LUA_MASKCOUNT | LUA_MASKCALL), "restore hook mask");
        expect(lua_gethookcount(state) == 71, "restore count interval");
        expect(std::memcmp(lua_getextraspace(state), marker.data(), marker.size()) == 0,
               "restore Lua extra space");
    };
    {
        LuaInstructionBudget outer(state);
        const auto installed_hook = lua_gethook(state);
        {
            LuaInstructionBudget nested(state);
            auto chunk = lua.load("return 1");
            sol::protected_function callback = chunk;
            expect(callback().valid(), "successful budgeted call");
        }
        expect(lua_gethook(state) == installed_hook, "nested guard retains outer hook");
    }
    check_restored();
    bool shared_exhaustion = false;
    expect_error([&] {
        LuaInstructionBudget outer(state);
        {
            LuaInstructionBudget nested(state);
            auto chunk = lua.load("while true do end");
            sol::protected_function callback = chunk;
            auto result = callback();
            expect(!result.valid() && nested.exhausted(), "count hook interrupts infinite loop");
        }
        expect(outer.exhausted(), "nested invocation shares exhaustion");
        shared_exhaustion = true;
        throw std::runtime_error("exercise exception unwinding");
    }, "guard exception path");
    expect(shared_exhaustion, "hook regression reaches expected exception path");
    check_restored();
    lua_sethook(state, nullptr, 0, 0);
    {
        LuaInstructionBudget guard(state);
        expect(!guard.exhausted(), "new outer invocation resets budget");
    }
    expect(lua_gethook(state) == nullptr, "restore absence of hook");
}

void test_loop_budgets() {
    using god2::LuaEngine;
    Fixture fixture;
    fixture.write("bootstrap.lua", R"lua(
local visits = 0
register_npc(42, {name='healthy', on_talk=function()
    visits = visits + 1
    return {text=tostring(visits)}
end})
register_npc(43, {name='loop', on_talk=function() while true do end end})
register_npc(44, {name='caught loop', on_talk=function()
    pcall(function() while true do end end)
    return {text='must not succeed'}
end})
register_npc(45, {name='nested loop', on_talk=function() return require('loop') end})
register_event('loop_event', function() while true do end end)
register_event('loop_event', function() visits = visits + 10 end)
)lua");
    fixture.write("loop.lua", "while true do end");
    LuaEngine engine(fixture.root);
    expect(engine.initialize() && engine.load_script("bootstrap.lua"), "load loop fixtures");
    for (const auto id : {43U, 44U, 45U, 43U}) {
        bool budget_error = false;
        try { engine.talk(id, 1, "Tester"); }
        catch (const std::runtime_error& error) {
            budget_error = std::string(error.what()).find("instruction budget exceeded") != std::string::npos;
        }
        expect(budget_error, "loop fails with instruction budget diagnostic");
    }
    engine.call_event("loop_event");
    expect(nlohmann::json::parse(engine.talk(42, 1, "Tester"))["text"] == "11",
           "healthy callbacks and later event handlers work after exhaustion");
    fixture.write("bootstrap.lua", npc_script("must not commit") + "\nwhile true do end");
    expect(!engine.reload_all(), "infinite bootstrap rejects reload");
    expect(nlohmann::json::parse(engine.talk(42, 1, "Tester"))["text"] == "12",
           "looping bootstrap preserves old VM and closure state");
    fixture.write("bootstrap.lua", "require('loop')");
    expect(!engine.reload_all(), "infinite required bootstrap module rejects reload");
    expect(engine.has_npc(43), "nested timeout retains old registrations");

    // Each module fits individually, but four modules exceed one shared budget.
    std::string bootstrap;
    for (int i = 1; i <= 4; ++i) {
        const auto name = "work" + std::to_string(i);
        fixture.write(name + ".lua", "local sum=0; for i=1,150000 do sum=sum+i end; return sum");
        LuaEngine standalone(fixture.root);
        expect(standalone.initialize() && standalone.load_script(name + ".lua"), "module fits standalone budget");
        bootstrap += "require('" + name + "')\n";
    }
    fixture.write("bootstrap.lua", bootstrap);
    expect(!engine.reload_all(), "nested modules cannot reset outer instruction budget");
    expect(nlohmann::json::parse(engine.talk(42, 1, "Tester"))["text"] == "13",
           "shared budget failure preserves active VM");
    fixture.write("bootstrap.lua", npc_script("recovered"));
    expect(engine.reload_all(), "healthy reload succeeds after exhausted staging");
    expect(nlohmann::json::parse(engine.talk(42, 1, "Tester"))["text"] == "recovered",
           "fresh VM remains usable");
}

void test_callback_isolation_and_registration() {
    Fixture fixture;
    fixture.write("bootstrap.lua", R"lua(
local observed = ''
local function fail() error('callback sentinel') end
local function loop() while true do end end
local function record() observed = observed .. 'H' end
register_quest(1, {name='failure', on_accept=fail, on_complete=loop})
register_quest(2, {name='healthy', on_accept=record, on_complete=record})
register_monster_ai(1, {on_spawn=fail, on_update=loop, on_death=fail})
register_monster_ai(2, {on_spawn=record, on_update=record, on_death=record})
register_gm_command('failure', fail)
register_gm_command('loop', loop)
register_gm_command('healthy', function(player, args)
    assert(player.id == '18446744073709551615')
    assert(player.name == 'Tester' and args[1] == 'one' and args[2] == 'two')
    player.name = 'changed'; args[1] = 'changed'
    record()
end)
register_event('mutation', function()
    observed = observed .. 'A'
    register_event('mutation', function() observed = observed .. 'C' end)
    error('event registration sentinel')
end)
register_event('mutation', function() observed = observed .. 'B' end)
register_npc(42, {name='observer', on_talk=function() return {text=observed} end})
)lua");
    god2::LuaEngine engine(fixture.root);
    expect(engine.initialize() && engine.load_script("bootstrap.lua"), "load callback isolation fixtures");
    const god2::ScriptPlayer player{UINT64_MAX, "Tester"};
    const god2::ScriptMonster monster{UINT64_MAX, UINT32_MAX, 100};
    const std::vector<std::string> args{"one", "two"};
    const std::vector<std::pair<std::function<void()>, std::string>> failures{
        {[&] { engine.quest_accept(1, player); }, "callback sentinel"},
        {[&] { engine.quest_complete(1, player); }, "instruction budget exceeded"},
        {[&] { engine.monster_spawn(1, monster); }, "callback sentinel"},
        {[&] { engine.monster_update(1, monster, 0); }, "instruction budget exceeded"},
        {[&] { engine.monster_death(1, monster, player); }, "callback sentinel"},
        {[&] { engine.call_gm_command("failure", player, args); }, "callback sentinel"},
        {[&] { engine.call_gm_command("loop", player, args); }, "instruction budget exceeded"}
    };
    std::string expected;
    for (const auto& [call, diagnostic] : failures) {
        bool rejected = false;
        try { call(); }
        catch (const std::runtime_error& error) {
            rejected = std::string(error.what()).find(diagnostic) != std::string::npos;
        }
        expect(rejected, "callback fails with its original diagnostic: " + diagnostic);
        engine.quest_accept(2, player);
        engine.quest_complete(2, player);
        engine.monster_spawn(2, monster);
        engine.monster_update(2, monster, 0);
        engine.monster_death(2, monster, player);
        engine.call_gm_command("healthy", player, args);
        expected += "HHHHHH";
        expect(nlohmann::json::parse(engine.talk(42, 1, "Tester"))["text"] == expected,
               "all callback families remain usable after an isolated failure");
    }
    expect(player.name == "Tester" && args == std::vector<std::string>{"one", "two"},
           "GM arguments and player are copied snapshots");
    engine.call_event("mutation");
    expected += "AB";
    expect(nlohmann::json::parse(engine.talk(42, 1, "Tester"))["text"] == expected,
           "handler registered before an event error waits until next dispatch");
    engine.call_event("mutation");
    expected += "ABC";
    expect(nlohmann::json::parse(engine.talk(42, 1, "Tester"))["text"] == expected,
           "event mutation preserves registration order and snapshot");

    const std::vector<std::string> invalid_registrations{
        "register_quest(2, {name='duplicate', on_accept=function() end, on_complete=function() end})",
        "register_monster_ai(2, {on_spawn=function() end, on_update=function() end, on_death=function() end})",
        "register_gm_command('healthy', function() end)",
        "register_quest(3, {name='missing complete', on_accept=function() end})",
        "register_monster_ai(3, {on_spawn=function() end, on_update=false, on_death=function() end})",
        "register_event('mutation', false)",
        "register_gm_command('', function() end)"
    };
    for (const auto& registration : invalid_registrations) {
        fixture.write("invalid.lua", "register_npc(99, {name='partial', on_talk=function() end})\n" + registration);
        expect(!engine.load_script("invalid.lua"), "invalid registration rejects staged load");
        expect(!engine.has_npc(99), "failed registration does not leak staged NPC");
        expect(nlohmann::json::parse(engine.talk(42, 1, "Tester"))["text"] == expected,
               "failed registration preserves active callback closure state");
    }
    expect(engine.reload_all(), "invalid registrations are absent from reload manifest");
    expect(nlohmann::json::parse(engine.talk(42, 1, "Tester"))["text"] == "",
           "successful reload resets callback closure state");
}

void test_dialogue_boundaries() {
    Fixture fixture;
    fixture.write("bootstrap.lua", R"lua(
local metamethod_calls = 0
local function forbidden_index()
    metamethod_calls = metamethod_calls + 1
    error('must not execute metamethod')
end
register_npc(42, {name='boundary', on_talk=function(player)
    assert(metamethod_calls == 0, 'dialogue validation executed __index')
    local mode = player.name
    if mode == 'text max' then return {text=string.rep('x', 16384)} end
    if mode == 'text overflow' then return {text=string.rep('x', 16385)} end
    if mode == 'option text overflow' then return {text='', options={{id=1,text=string.rep('x',16385)}}} end
    if mode == 'options max' or mode == 'options overflow' then
        local options = {}
        for i=1,(mode == 'options max' and 64 or 65) do options[i] = {id=i,text='x'} end
        return {text='', options=options}
    end
    if mode == 'serialized max' or mode == 'serialized overflow' then
        -- Empty text fields plus this uint32 ID use 51 JSON bytes.
        return {text=string.rep('x',16384), options={{id=4294967295,
            text=string.rep('y', mode == 'serialized max' and 16333 or 16334)}}}
    end
    if mode == 'invalid utf8' then return {text=string.char(255)} end
    if mode == 'escaped overflow' then return {text=string.rep(string.char(0), 6000)} end
    if mode == 'fractional index' then return {text='', options={[1.5]={id=1,text='x'}}} end
    if mode == 'named index' then return {text='', options={other={id=1,text='x'}}} end
    if mode == 'zero id' then return {text='', options={{id=0,text='x'}}} end
    if mode == 'overflow id' then return {text='', options={{id=4294967296,text='x'}}} end
    if mode == 'fractional id' then return {text='', options={{id=1.5,text='x'}}} end
    if mode == 'numeric text' then return {text=7} end
    if mode == 'metatable text' then
        return setmetatable({}, {__index=forbidden_index})
    end
    if mode == 'metatable option' then
        return {text='', options={setmetatable({}, {__index=forbidden_index})}}
    end
    return {text=mode}
end})
)lua");
    god2::LuaEngine engine(fixture.root);
    expect(engine.initialize() && engine.load_script("bootstrap.lua"), "load dialogue boundary fixtures");
    expect(nlohmann::json::parse(engine.talk(42, 1, "text max"))["text"].get<std::string>().size() == 16384,
           "maximum dialogue text accepted");
    expect(nlohmann::json::parse(engine.talk(42, 1, "options max"))["options"].size() == 64,
           "maximum option count accepted");
    const auto maximum = engine.talk(42, 1, "serialized max");
    expect(maximum.size() == 32768, "exact serialized dialogue byte limit accepted");
    expect(nlohmann::json::parse(maximum)["options"][0]["id"] == UINT32_MAX,
           "maximum uint32 dialogue option id preserved");
    for (const auto* mode : {"text overflow", "option text overflow", "options overflow",
                            "serialized overflow", "invalid utf8", "escaped overflow",
                            "fractional index", "named index", "zero id", "overflow id",
                            "fractional id", "numeric text", "metatable text", "metatable option"}) {
        expect_error([&] { engine.talk(42, 1, mode); }, mode);
        expect(nlohmann::json::parse(engine.talk(42, 1, "healthy"))["text"] == "healthy",
               std::string("healthy dialogue after ") + mode);
    }
    const std::string binary_name("a\0b", 3);
    expect(nlohmann::json::parse(engine.talk(42, 1, binary_name))["text"] == binary_name,
           "snapshot and JSON preserve embedded NUL bytes");
}

void test_monster_hp_requires_explicit_value() {
    const god2::Monster unqualified;
    expect(!unqualified.hp.has_value(), "monster must not invent base HP");
    Fixture fixture;
    fixture.write("bootstrap.lua", R"lua(
local calls, total = 0, 0
local function observe(monster)
    assert(type(monster.hp) == 'number')
    calls = calls + 1
    total = total + monster.hp
end
register_monster_ai(77, {on_spawn=observe, on_update=observe, on_death=observe})
register_npc(77, {name='fixture', on_talk=function()
    return {text=tostring(calls) .. ':' .. tostring(total)}
end})
)lua");
    god2::LuaEngine engine(fixture.root, false);
    expect(engine.initialize() && engine.load_script("bootstrap.lua"), "load explicit HP boundary fixture");
    const god2::ScriptMonster unknown{9, 3001, std::nullopt};
    const god2::ScriptPlayer player{1, "Tester"};
    expect_error([&] { engine.monster_spawn(77, unknown); }, "reject absent monster HP at spawn");
    expect_error([&] { engine.monster_update(77, unknown, 0.1); }, "reject absent monster HP at update");
    expect_error([&] { engine.monster_death(77, unknown, player); }, "reject absent monster HP at death");
    expect(nlohmann::json::parse(engine.talk(77, 1, "Tester"))["text"] == "0:0",
           "unknown HP must not reach a callback");
    const god2::ScriptMonster zero{9, 3001, 0};
    const god2::ScriptMonster known{9, 3001, 321};
    engine.monster_spawn(77, zero);
    engine.monster_update(77, known, 0.1);
    engine.monster_death(77, zero, player);
    expect(nlohmann::json::parse(engine.talk(77, 1, "Tester"))["text"] == "3:321",
           "explicit zero and nonzero HP survive the C++/Lua boundary");
}

void expect_no_examples(god2::LuaEngine& engine) {
    expect(!engine.has_npc(1001), "recovered bootstrap excludes example NPC");
    const god2::ScriptPlayer player{1, "Tester"};
    const god2::ScriptMonster monster{9, 3001, 100};
    const auto unavailable = [](const std::function<void()>& call, const char* kind) {
        try { call(); }
        catch (const std::runtime_error& error) {
            expect(error.what() == std::string("unavailable Lua ") + kind,
                   "example hook must be absent, not a failing callback");
            return;
        }
        throw std::runtime_error(std::string("Lua test: example still registered: ") + kind);
    };
    unavailable([&] { engine.quest_accept(2001, player); }, "quest");
    unavailable([&] { engine.monster_spawn(3001, monster); }, "monster AI");
    unavailable([&] { engine.call_gm_command("reload_scripts", player, {}); }, "GM command");
}

void test_recovered_bootstrap() {
    const auto source = std::filesystem::path(GOD2_SOURCE_DIR);
    const auto config = god2::Config::load(source / "config/recovered-seed.json");
    expect(config.protocol_mode != god2::ProtocolMode::Fixture, "recovered config selects non-fixture mode");
    god2::LuaEngine recovered(config.script_root, config.protocol_mode == god2::ProtocolMode::Fixture);
    expect(recovered.initialize() && recovered.load_script(config.bootstrap), "load default recovered bootstrap");
    expect_no_examples(recovered);
    expect(recovered.reload_all(), "reload default recovered bootstrap");
    expect_no_examples(recovered);

    // With no sample modules present, loading either bundled entry must still work.
    Fixture custom;
    for (const auto* file : {"bootstrap.lua", "fixture_bootstrap.lua"})
        std::filesystem::copy_file(source / "scripts" / file, custom.root / file);
    custom.write("custom.lua", R"lua(
assert(GOD2_FIXTURE_MODE == false)
require('bootstrap')
require('fixture_bootstrap')
local starts = 0
register_event('server_start', function() starts = starts + 1 end)
register_npc(42, {name='custom', on_talk=function()
    return {text='custom:' .. starts}
end})
)lua");
    god2::LuaEngine custom_engine(custom.root, false);
    expect(custom_engine.initialize() && custom_engine.load_script("custom.lua"), "honor custom recovered bootstrap");
    const auto check_custom = [&] {
        expect_no_examples(custom_engine);
        custom_engine.call_event("server_start");
        expect(nlohmann::json::parse(custom_engine.talk(42, 1, "Tester"))["text"] == "custom:1",
               "custom registration and event remain usable");
    };
    check_custom();
    expect(custom_engine.reload_all(), "custom reload retains recovered runtime setting");
    check_custom();
    custom.write("custom.lua", "GOD2_FIXTURE_MODE = true; require('fixture_bootstrap')");
    expect(!custom_engine.reload_all(), "failed custom reload retains recovered VM");
    expect_no_examples(custom_engine);
    expect(custom_engine.has_npc(42), "failed reload retains custom registration");
}
}

void test_lua() {
    test_monster_hp_requires_explicit_value();
    test_instruction_hook_restore();
    test_loop_budgets();
    test_callback_isolation_and_registration();
    test_dialogue_boundaries();
    test_recovered_bootstrap();
    using god2::LuaEngine;
    const auto scripts = std::filesystem::path(GOD2_SOURCE_DIR) / "scripts";
    LuaEngine examples(scripts);
    expect(!examples.has_npc(1001), "NPC unavailable before initialize");
    expect(!examples.load_script("bootstrap.lua"), "load before initialize fails");
    expect_error([&] { examples.talk(1001, 1, "Tester"); }, "uninitialized talk");
    expect(examples.initialize(), "initialize examples");
    expect(examples.load_script(scripts / "bootstrap.lua"), "load example bootstrap");
    expect(examples.initialize(), "initialize is idempotent");
    expect(examples.has_npc(1001), "bootstrap registers NPC");
    const auto dialogue = nlohmann::json::parse(examples.talk(1001, 1, "Tester"));
    expect(dialogue["text"] == "Hello, welcome to GOD2 rebuild server.", "NPC text");
    expect(dialogue["options"].size() == 2 && dialogue["options"][0]["id"] == 1, "NPC options");
    examples.call_event("server_start");
    examples.call_event("unknown_event");
    const god2::ScriptPlayer player{1, "Tester"};
    const god2::ScriptMonster monster{9, 3001, 100};
    examples.quest_accept(2001, player);
    examples.quest_complete(2001, player);
    examples.monster_spawn(3001, monster);
    examples.monster_update(3001, monster, 0.05);
    examples.monster_death(3001, monster, player);
    examples.call_gm_command("reload_scripts", player, {"all"});
    expect_error([&] { examples.talk(999, 1, "Tester"); }, "missing NPC");
    expect_error([&] { examples.quest_accept(999, player); }, "missing quest");
    expect_error([&] { examples.call_gm_command("missing", player, {}); }, "missing GM");
    expect_error([&] { examples.monster_update(3001, monster, -1); }, "negative dt");
    expect_error([&] { examples.monster_update(3001, monster,
        std::numeric_limits<double>::quiet_NaN()); }, "NaN dt");
    expect(examples.load_directory(scripts), "directory deduplicates modules required by bootstrap");
    expect(examples.reload_all(), "example reload");
    expect(examples.has_npc(1001), "fixture reload retains example NPC");
    examples.quest_accept(2001, player);
    examples.monster_spawn(3001, monster);
    examples.call_gm_command("reload_scripts", player, {});

    bool rejected_thread = false;
    std::thread other([&] {
        try { examples.has_npc(1001); }
        catch (const std::runtime_error&) { rejected_thread = true; }
    });
    other.join();
    expect(rejected_thread, "cross-thread Lua access rejected");

    Fixture fixture;
    fixture.write("npc/value.lua", "return {value='module-value'}");
    fixture.write("cycle_a.lua", "return require('cycle_b')");
    fixture.write("cycle_b.lua", "return require('cycle_a')");
    fixture.write("bootstrap.lua", R"lua(
assert(io == nil and os == nil and debug == nil and package == nil)
assert(load == nil and loadfile == nil and dofile == nil and collectgarbage == nil)
assert(require('npc.value') == require('npc.value'))
assert(require('npc.value').value == 'module-value')
assert(not pcall(require, '../outside'))
assert(not pcall(require, 'C:/outside'))
assert(not pcall(require, 'npc..value'))
assert(not pcall(require, 'missing'))
assert(not pcall(require, 'cycle_a'))
local observed = 0
register_event('probe', function() error('expected event failure') end)
register_event('probe', function() observed = observed + 1 end)
register_npc(42, {name='snapshot', on_talk=function(player)
    assert(player.id == '18446744073709551615')
    assert(player.name == 'Tester')
    player.name = 'mutated copy'
    return {text='quote " slash \\ newline\n' .. observed, options={{id=1,text='ok'}}}
end})
register_npc(43, {name='broken', on_talk=function() error('expected NPC failure') end})
register_npc(44, {name='bad return', on_talk=function() return 7 end})
register_npc(45, {name='sparse options', on_talk=function()
    return {text='x', options={[2]={id=1,text='x'}}}
end})
register_npc(46, {name='duplicate options', on_talk=function()
    return {text='x', options={{id=1,text='x'},{id=1,text='y'}}}
end})
register_npc(47, {name='no options', on_talk=function() return {text='x'} end})
)lua");
    LuaEngine engine(fixture.root);
    expect(engine.initialize() && engine.load_script("bootstrap.lua"), "sandbox and require checks");
    engine.call_event("probe");
    const auto escaped = nlohmann::json::parse(engine.talk(42, UINT64_MAX, "Tester"));
    expect(escaped["text"] == "quote \" slash \\ newline\n1", "JSON escaping and event continuation");
    expect(engine.talk(42, UINT64_MAX, "Tester") == escaped.dump(), "fresh player snapshot");
    for (const auto id : {43U, 44U, 45U, 46U})
        expect_error([&] { engine.talk(id, 1, "Tester"); }, "invalid NPC dialogue");
    expect(nlohmann::json::parse(engine.talk(47, 1, "Tester"))["options"].empty(), "default options");

    fixture.write("bootstrap.lua", "register_npc(99, {name='partial', on_talk=function() end})\nerror('staging fails')");
    expect(!engine.reload_all(), "runtime failure rejects reload");
    expect(engine.has_npc(42) && !engine.has_npc(99), "rollback preserves registrations");
    expect(engine.talk(42, UINT64_MAX, "Tester") == escaped.dump(), "rollback preserves Lua state");
    fixture.write("bootstrap.lua", "this is not valid Lua !!!");
    expect(!engine.reload_all() && engine.has_npc(42), "syntax failure rollback");
    fixture.write("bootstrap.lua", npc_script("new version"));
    expect(engine.reload_all(), "successful reload");
    expect(!engine.has_npc(43), "reload removes obsolete NPC");
    expect(nlohmann::json::parse(engine.talk(42, 1, "Tester"))["text"] == "new version", "reload updates NPC");
    fixture.write("bad.lua", "register_npc(-1, {name='invalid',on_talk=function() end})");
    expect(!engine.load_script("bad.lua") && engine.has_npc(42), "invalid ID rollback");
    fixture.write("bad.lua", "register_npc(50, {name='invalid',on_talk=3})");
    expect(!engine.load_script("bad.lua"), "invalid callback rejected");
    fixture.write("bad.lua", npc_script("duplicate"));
    expect(!engine.load_script("bad.lua"), "duplicate registration rejected");
    expect(!engine.load_script("missing.lua"), "missing file rejected");
    expect(!engine.load_script("../outside.lua"), "path traversal rejected");
    expect(!engine.load_directory("missing-directory"), "missing directory rejected");
    fixture.write("bad.lua", "error('failed entries must not be retained')");
    expect(engine.reload_all(), "failed loads do not enter reload manifest");

    Fixture directory;
    directory.write("one.lua", npc_script("directory"));
    LuaEngine directory_engine(directory.root);
    expect(directory_engine.initialize() && directory_engine.load_directory(directory.root), "load directory");
    directory.write("nested/two.lua", "register_npc(88, {name='new',on_talk=function() return {text='new'} end})");
    expect(directory_engine.reload_all() && directory_engine.has_npc(88), "reload discovers new directory files");
    std::filesystem::remove(directory.root / "one.lua");
    expect(directory_engine.reload_all() && !directory_engine.has_npc(42), "reload removes deleted directory files");
}
