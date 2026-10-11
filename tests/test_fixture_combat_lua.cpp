#include "game/FixtureBattle.h"
#include "scripting/LuaEngine.h"

#include <chrono>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <thread>

namespace {
void expect(bool condition, const std::string& message) {
    if (!condition) throw std::runtime_error(message);
}

template<class F>
void rejects(F&& call, const std::string& diagnostic = {}) {
    try { call(); }
    catch (const std::runtime_error& error) {
        expect(diagnostic.empty() || std::string(error.what()).find(diagnostic) != std::string::npos,
               "unexpected diagnostic: " + std::string(error.what()));
        return;
    }
    throw std::runtime_error("expected fixture combat rejection: " + diagnostic);
}

struct Scripts {
    std::filesystem::path root;
    Scripts() {
        const auto seed = std::chrono::steady_clock::now().time_since_epoch().count();
        for (int i = 0; i < 100; ++i) {
            root = std::filesystem::temp_directory_path() /
                ("god2-fixture-combat-" + std::to_string(seed) + "-" + std::to_string(i));
            if (std::filesystem::create_directory(root)) {
                std::filesystem::create_directory(root / "fixtures");
                return;
            }
        }
        throw std::runtime_error("cannot create test script root");
    }
    ~Scripts() { std::error_code ec; std::filesystem::remove_all(root, ec); }
    void write(const std::string& source) const {
        std::ofstream stream(root / "fixtures/combat.lua", std::ios::binary | std::ios::trunc);
        stream << source;
        stream.close();
        expect(!stream.fail(), "write test module");
    }
    void copy_formula() const {
        std::filesystem::copy_file(std::filesystem::path(GOD2_SOURCE_DIR) /
            "scripts/fixtures/combat.lua", root / "fixtures/combat.lua",
            std::filesystem::copy_options::overwrite_existing);
    }
};

god2::FixtureCombatant combatant() {
    god2::FixtureCombatant value{};
    value.hp = value.max_hp = 500;
    value.mp = value.max_mp = 30;
    value.physical_attack = 11;
    value.magical_attack = 13;
    value.physical_defense = 4;
    value.magical_defense = 5;
    return value;
}

void formulas_and_guards() {
    Scripts scripts;
    scripts.copy_formula();
    god2::LuaEngine engine(scripts.root);
    auto attacker = combatant();
    auto defender = combatant();
    rejects([&] { engine.fixture_damage(attacker, defender, 1, 1000); }, "not initialized");
    expect(engine.initialize(), "initialize");
    for (std::uint8_t skill = 1; skill <= 3; ++skill) {
        const std::uint32_t expected[] = {0, 7, 14, 18};
        const std::uint32_t costs[] = {0, 0, 8, 20};
        for (const auto roll : {0U, 999U, 1000U, 9999U}) {
            const auto result = engine.fixture_damage(attacker, defender, skill, roll);
            expect(result.damage == (roll < 1000 ? expected[skill] * 150 / 100 : expected[skill]),
                   "formula floors power before defense and critical after defense");
            expect(result.critical == (roll < 1000), "critical threshold");
            expect(result.mp_cost == costs[skill], "skill MP cost");
        }
    }
    defender.physical_defense = defender.magical_defense = 100;
    for (std::uint8_t skill = 1; skill <= 3; ++skill)
        for (const auto roll : {999U, 1000U})
            expect(engine.fixture_damage(attacker, defender, skill, roll).damage == 1, "minimum hit");
    defender = combatant();
    attacker.mp = 0;
    expect(engine.fixture_damage(attacker, defender, 3, 1000).mp_cost == 20,
           "service owns insufficient mana decision");
    for (const auto skill : {0, 4, 255})
        rejects([&] { engine.fixture_damage(attacker, defender, static_cast<std::uint8_t>(skill), 0); });
    for (const auto roll : {10000U, UINT32_MAX})
        rejects([&] { engine.fixture_damage(attacker, defender, 1, roll); });
    std::uint32_t god2::FixtureCombatant::* const fields[] = {
        &god2::FixtureCombatant::hp, &god2::FixtureCombatant::max_hp,
        &god2::FixtureCombatant::mp, &god2::FixtureCombatant::max_mp,
        &god2::FixtureCombatant::physical_attack, &god2::FixtureCombatant::magical_attack,
        &god2::FixtureCombatant::physical_defense, &god2::FixtureCombatant::magical_defense
    };
    for (const auto field : fields) {
        auto invalid = combatant();
        invalid.*field = 1'000'001;
        rejects([&] { engine.fixture_damage(invalid, defender, 1, 0); });
        rejects([&] { engine.fixture_damage(attacker, invalid, 1, 0); });
    }
    auto invalid = combatant();
    invalid.hp = invalid.max_hp + 1;
    rejects([&] { engine.fixture_damage(invalid, defender, 1, 0); });
    invalid = combatant();
    invalid.mp = invalid.max_mp + 1;
    rejects([&] { engine.fixture_damage(attacker, invalid, 1, 0); });
    auto maximum = combatant();
    maximum.hp = maximum.max_hp = maximum.mp = maximum.max_mp = 1'000'000;
    maximum.physical_attack = 1'000'000;
    defender.physical_defense = 0;
    expect(engine.fixture_damage(maximum, defender, 1, 1000).damage == 1'000'000, "inclusive input/output bound");
    rejects([&] { engine.fixture_damage(maximum, defender, 3, 0); }, "out of bounds");
    bool wrong_thread_rejected = false;
    std::thread other([&] {
        try { engine.fixture_damage(attacker, defender, 1, 0); }
        catch (const std::runtime_error&) { wrong_thread_rejected = true; }
    });
    other.join();
    expect(wrong_thread_rejected, "owner thread enforcement");
    god2::LuaEngine production(scripts.root, false);
    expect(production.initialize(), "production initialize");
    rejects([&] { production.fixture_damage(attacker, defender, 1, 0); }, "fixture mode");
}

void hostile_modules() {
    Scripts scripts;
    const auto actor = combatant();
    for (const auto* source : {
        "return false", "return {}", "return {damage=7}",
        "return setmetatable({}, {__index=function() while true do end end})",
        "return {damage=function() end}", "return {damage=function() return 1 end}",
        "return {damage=function() return {}, {} end}",
        "return {damage=function() return setmetatable({}, {__index=function() while true do end end}) end}",
        "return {damage=function() error('formula failed') end}",
        "return {damage=function() while true do end end}",
        "return {damage=function() pcall(function() while true do end end); return {damage=1,mp_cost=0,critical=false} end}",
        "while true do end", "this is invalid Lua"
    }) {
        scripts.write(source);
        god2::LuaEngine engine(scripts.root);
        expect(engine.initialize(), "hostile initialize");
        rejects([&] { engine.fixture_damage(actor, actor, 1, 0); });
    }
    for (const auto* field : {"damage", "mp_cost", "critical"}) {
        for (const auto* value : {"nil", "'1'", "{}", "function() end", "-1", "1.5",
                                  "1000001", "1e300", "math.huge", "0/0", "true"}) {
            if (std::string(field) == "critical" && std::string(value) == "true") continue;
            scripts.write("return {damage=function() local r={damage=1,mp_cost=0,critical=false}; r." +
                          std::string(field) + "=" + value + "; return r end}");
            god2::LuaEngine engine(scripts.root);
            expect(engine.initialize(), "hostile result initialize");
            rejects([&] { engine.fixture_damage(actor, actor, 1, 0); });
        }
    }
    scripts.write(R"lua(
local calls = 0
return {damage=function(a, d, skill, roll)
    calls = calls + 1
    assert(a.hp == 500 and a.max_hp == 500 and a.mp == 30 and a.max_mp == 30)
    assert(a.physical_attack == 11 and a.magical_attack == 13)
    assert(a.physical_defense == 4 and a.magical_defense == 5)
    a.hp = 0; d.mp = 0
    if calls == 1 then error('formula failed') end
    if calls == 2 then while true do end end
    return {damage=1,mp_cost=1000000,critical=false}
end}
)lua");
    god2::LuaEngine engine(scripts.root);
    expect(engine.initialize(), "recovery initialize");
    rejects([&] { engine.fixture_damage(actor, actor, 1, 0); }, "formula failed");
    rejects([&] { engine.fixture_damage(actor, actor, 1, 0); }, "instruction budget exceeded");
    expect(engine.fixture_damage(actor, actor, 1, 0).mp_cost == 1'000'000, "recovery and inclusive MP bound");
    expect(actor.hp == 500 && actor.mp == 30, "snapshots cannot mutate host");
    scripts.copy_formula();
    expect(engine.reload_all(), "reload clears module cache");
    expect(engine.fixture_damage(actor, actor, 3, 1000).mp_cost == 20, "reload updated formula");
}
}

int main() {
    try {
        formulas_and_guards();
        hostile_modules();
        std::cout << "fixture combat Lua tests passed\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
