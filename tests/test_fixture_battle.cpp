#include "game/FixtureBattle.h"

#include <iostream>
#include <limits>
#include <stdexcept>
#include <tuple>
#include <vector>

namespace {
using namespace god2;

void require(bool ok) {
    if (!ok) throw std::runtime_error("Fixture battle check failed");
}

template<class F> void rejected(F&& fn) {
    try { fn(); } catch (const std::invalid_argument&) { return; }
    throw std::runtime_error("Invalid fixture request accepted");
}

auto fields(const FixtureCombatant& value) {
    return std::tie(value.hp, value.max_hp, value.mp, value.max_mp,
                    value.physical_attack, value.magical_attack,
                    value.physical_defense, value.magical_defense);
}

auto fields(const FixtureDamage& value) {
    return std::tie(value.damage, value.mp_cost, value.critical);
}

void same(const FixtureBattleSnapshot& a, const FixtureBattleSnapshot& b) {
    require(a.battle_id == b.battle_id && a.turn == b.turn && a.outcome == b.outcome);
    require(fields(a.player) == fields(b.player) && fields(a.monster) == fields(b.monster));
    require(fields(a.player_action) == fields(b.player_action));
    require(fields(a.monster_action) == fields(b.monster_action));
}

FixtureDamage formula(const FixtureCombatant& actor, const FixtureCombatant& target,
                      std::uint8_t skill, std::uint32_t roll) {
    require(roll < 10000 && skill >= 1 && skill <= 3);
    if (skill == 2) return {actor.magical_attack - target.magical_defense, 8, false};
    if (skill == 3) return {1, 0, roll < 5000};
    return {actor.physical_attack - target.physical_defense, 0, roll < 5000};
}

void lifecycle() {
    rejected([] { FixtureBattleService service({}); });
    FixtureBattleService service(formula);
    rejected([&] { service.inspect(1); });
    rejected([&] { service.act(1, 1, 1, 1); });
    rejected([&] { service.flee(1, 1, 1); });
    auto initial = service.start(1);
    require(initial.battle_id != 0 && initial.turn == 1 && initial.outcome == "active");
    require(fields(initial.player) == fields(FixtureCombatant{120,120,24,24,28,32,8,6}));
    require(fields(initial.monster) == fields(FixtureCombatant{100,100,0,0,18,0,10,8}));
    require(fields(initial.player_action) == fields(FixtureDamage{}));
    require(fields(initial.monster_action) == fields(FixtureDamage{}));
    rejected([&] { service.start(1); });
    rejected([&] { service.act(1, initial.battle_id + 1, 1, 1); });
    rejected([&] { service.act(1, initial.battle_id, 0, 1); });
    rejected([&] { service.act(1, initial.battle_id, 2, 1); });
    for (const auto skill : {0, 4, 255})
        rejected([&] { service.act(1, initial.battle_id, 1, static_cast<std::uint8_t>(skill)); });
    same(initial, service.inspect(1));

    auto current = service.act(1, initial.battle_id, 1, 1);
    require(current.turn == 2 && current.player.hp == 110 && current.monster.hp == 82);
    require(current.player_action.damage == 18 && current.monster_action.damage == 10);
    rejected([&] { service.act(1, initial.battle_id, 1, 1); });
    rejected([&] { service.flee(1, initial.battle_id, 1); });
    rejected([&] { service.flee(1, initial.battle_id + 1, 2); });
    same(current, service.inspect(1));
    auto fled = service.flee(1, current.battle_id, current.turn);
    require(fled.outcome == "fled" && fled.turn == 3);
    require(fields(fled.player) == fields(current.player));
    require(fields(fled.monster) == fields(current.monster));
    require(fields(fled.player_action) == fields(FixtureDamage{}));
    require(fields(fled.monster_action) == fields(FixtureDamage{}));
    rejected([&] { service.act(1, fled.battle_id, fled.turn, 1); });
    rejected([&] { service.flee(1, fled.battle_id, fled.turn); });
    const auto restart = service.start(1);
    require(restart.battle_id != fled.battle_id && restart.turn == 1);
    service.remove(1);
    service.remove(1);
    rejected([&] { service.inspect(1); });
    const auto after_remove = service.start(1);
    require(after_remove.battle_id != restart.battle_id);
    rejected([&] { service.act(1, restart.battle_id, restart.turn, 1); });
}

void mp_and_replay() {
    FixtureBattleService tested(formula), control(formula);
    auto a = tested.start(7), b = control.start(7);
    for (int i = 0; i < 3; ++i) {
        a = tested.act(7, a.battle_id, a.turn, 2);
        b = control.act(7, b.battle_id, b.turn, 2);
        same(a, b);
    }
    require(a.player.mp == 0 && a.monster.hp == 28 && a.player.hp == 90);
    for (int i = 0; i < 2; ++i) {
        rejected([&] { tested.act(7, a.battle_id, a.turn, 2); });
        same(a, tested.inspect(7));
    }
    for (int i = 0; i < 4; ++i) {
        a = tested.act(7, a.battle_id, a.turn, 3);
        b = control.act(7, b.battle_id, b.turn, 3);
        same(a, b);
    }
}

void terminal_hits() {
    unsigned calls = 0;
    FixtureBattleService victory([&](const auto&, const auto&, auto, auto) {
        ++calls;
        return FixtureDamage{1000000, 24, true};
    });
    auto a = victory.start(1);
    a = victory.act(1, a.battle_id, a.turn, 2);
    require(calls == 1 && a.outcome == "won" && a.turn == 2);
    require(a.monster.hp == 0 && a.player.hp == 120 && a.player.mp == 0);
    require(a.player_action.critical && a.player_action.damage == 1000000);
    require(fields(a.monster_action) == fields(FixtureDamage{}));
    rejected([&] { victory.act(1, a.battle_id, a.turn, 1); });
    require(victory.start(1).outcome == "active");

    FixtureBattleService defeat([](const auto& actor, const auto& target, auto skill, auto) {
        if (actor.max_hp == 120) return FixtureDamage{0, 8, false};
        require(skill == 1 && target.mp == 16);
        return FixtureDamage{1000000, 0, false};
    });
    auto b = defeat.start(2);
    b = defeat.act(2, b.battle_id, b.turn, 2);
    require(b.outcome == "lost" && b.player.hp == 0 && b.monster.hp == 100 && b.turn == 2);
    rejected([&] { defeat.flee(2, b.battle_id, b.turn); });
    rejected([&] { defeat.act(2, b.battle_id, b.turn, 1); });
    auto fresh = defeat.start(2);
    require(fresh.battle_id != b.battle_id && fresh.player.hp == 120 && fresh.player.mp == 24);
}

void rollback() {
    // Instrumentation injects faults and records the exact rolls on both sides.
    for (const bool monster_fault : {false, true}) {
        for (int fault = 0; fault < 5; ++fault) {
            bool enabled = true;
            std::vector<std::uint32_t> rolls;
            FixtureBattleService tested([&](const auto& actor, const auto& target,
                                           auto skill, auto roll) {
                rolls.push_back(roll);
                if (enabled && (actor.max_hp == 100) == monster_fault) {
                    if (fault == 0) throw std::runtime_error("Injected callback failure");
                    if (fault == 1) return FixtureDamage{1000001, 0, false};
                    if (fault == 2) return FixtureDamage{0, 1000001, false};
                    if (fault == 3) return FixtureDamage{0, actor.mp + 1, false};
                    return FixtureDamage{std::numeric_limits<std::uint32_t>::max(), 0, false};
                }
                return formula(actor, target, skill, roll);
            });
            FixtureBattleService control(formula);
            const auto before = tested.start(1);
            auto expected = control.start(1);
            bool threw = false;
            try { tested.act(1, before.battle_id, before.turn, 2); }
            catch (const std::exception&) { threw = true; }
            require(threw);
            same(before, tested.inspect(1));
            const auto failed_rolls = rolls;
            rolls.clear();
            enabled = false;
            auto actual = tested.act(1, before.battle_id, before.turn, 2);
            expected = control.act(1, expected.battle_id, expected.turn, 2);
            same(actual, expected);
            require(failed_rolls.size() == (monster_fault ? 2u : 1u));
            for (std::size_t i = 0; i < failed_rolls.size(); ++i)
                require(failed_rolls[i] == rolls[i]);
        }
    }
}

void isolation() {
    FixtureBattleService service(formula), control(formula);
    auto first = service.start(0);
    const auto session = std::numeric_limits<std::uint64_t>::max();
    const auto second = service.start(session);
    control.start(0);
    auto expected = control.start(session);
    require(first.battle_id != second.battle_id);
    rejected([&] { service.act(session, first.battle_id, first.turn, 1); });
    first = service.act(0, first.battle_id, first.turn, 2);
    same(second, service.inspect(session));
    service.remove(0);
    auto actual = service.act(session, second.battle_id, second.turn, 1);
    expected = control.act(session, expected.battle_id, expected.turn, 1);
    same(actual, expected);
    actual.player.hp = 0;
    require(service.inspect(session).player.hp == 110);
}
}

int main() {
    try {
        lifecycle();
        mp_and_replay();
        terminal_hits();
        rollback();
        isolation();
        std::cout << "Fixture battle checks passed\n";
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
