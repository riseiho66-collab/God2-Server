#include "game/FixtureBattle.h"

#include <algorithm>
#include <limits>
#include <stdexcept>
#include <type_traits>
#include <utility>

namespace god2 {

// CUSTOM-0002: fixture stats/turn lifecycle; see docs/custom-designs.json.

FixtureBattleService::FixtureBattleService(DamageCallback damage)
    : damage_(std::move(damage)) {
    if (!damage_) throw std::invalid_argument("Missing fixture damage callback");
}

FixtureBattleSnapshot FixtureBattleService::start(std::uint64_t session) {
    const auto found = battles_.find(session);
    if (found != battles_.end() && found->second.snapshot.outcome == "active")
        throw std::invalid_argument("Fixture battle already active");
    if (next_battle_id_ > std::numeric_limits<std::uint32_t>::max())
        throw std::overflow_error("Fixture battle IDs exhausted");

    const auto id = static_cast<std::uint32_t>(next_battle_id_);
    State staged{{id, 1, {120, 120, 24, 24, 28, 32, 8, 6},
                        {100, 100, 0, 0, 18, 0, 10, 8}, "active"}, std::mt19937{id}};
    auto result = staged.snapshot;
    if (found == battles_.end()) {
        battles_.emplace(session, std::move(staged));
    } else {
        static_assert(std::is_nothrow_swappable_v<State>);
        using std::swap;
        swap(found->second, staged);
    }
    ++next_battle_id_;
    return result;
}

FixtureBattleService::State& FixtureBattleService::active(
        std::uint64_t session, std::uint32_t battle_id, std::uint32_t turn) {
    const auto found = battles_.find(session);
    if (found == battles_.end()) throw std::invalid_argument("Missing fixture battle");
    const auto& snapshot = found->second.snapshot;
    if (snapshot.battle_id != battle_id || snapshot.turn != turn)
        throw std::invalid_argument("Stale fixture battle or turn");
    if (snapshot.outcome != "active") throw std::invalid_argument("Fixture battle finished");
    if (turn == std::numeric_limits<std::uint32_t>::max())
        throw std::overflow_error("Fixture battle turns exhausted");
    return found->second;
}

void FixtureBattleService::hit(State& state, FixtureCombatant& actor,
        FixtureCombatant& target, std::uint8_t skill, FixtureDamage& action) {
    // Explicit mapping avoids implementation-dependent distribution behavior.
    const auto roll = static_cast<std::uint32_t>(state.rng() % 10000u);
    action = damage_(actor, target, skill, roll);
    if (action.damage > 1000000u || action.mp_cost > 1000000u)
        throw std::invalid_argument("Fixture damage callback exceeds bounds");
    if (action.mp_cost > actor.mp) throw std::invalid_argument("Insufficient fixture MP");
    actor.mp -= action.mp_cost;
    // Action metadata retains the callback's damage; only HP loss is clipped.
    target.hp -= std::min(target.hp, action.damage);
}

FixtureBattleSnapshot FixtureBattleService::commit(State& current, State& staged) {
    // Prepare the potentially allocating return value before committing anything.
    auto result = staged.snapshot;
    static_assert(std::is_nothrow_swappable_v<State>);
    static_assert(std::is_nothrow_move_constructible_v<FixtureBattleSnapshot>);
    using std::swap;
    swap(current, staged);
    return result;
}

FixtureBattleSnapshot FixtureBattleService::act(std::uint64_t session,
        std::uint32_t battle_id, std::uint32_t turn, std::uint8_t skill) {
    auto& current = active(session, battle_id, turn);
    if (skill < 1 || skill > 3) throw std::invalid_argument("Invalid fixture skill");
    auto staged = current;
    auto& snapshot = staged.snapshot;
    snapshot.player_action = {};
    snapshot.monster_action = {};
    hit(staged, snapshot.player, snapshot.monster, skill, snapshot.player_action);
    if (snapshot.monster.hp == 0) {
        snapshot.outcome = "won";
    } else {
        hit(staged, snapshot.monster, snapshot.player, 1, snapshot.monster_action);
        if (snapshot.player.hp == 0) snapshot.outcome = "lost";
    }
    ++snapshot.turn;
    return commit(current, staged);
}

FixtureBattleSnapshot FixtureBattleService::flee(std::uint64_t session,
        std::uint32_t battle_id, std::uint32_t turn) {
    auto& current = active(session, battle_id, turn);
    auto staged = current;
    staged.snapshot.outcome = "fled";
    staged.snapshot.player_action = {};
    staged.snapshot.monster_action = {};
    ++staged.snapshot.turn;
    return commit(current, staged);
}

void FixtureBattleService::remove(std::uint64_t session) { battles_.erase(session); }

FixtureBattleSnapshot FixtureBattleService::inspect(std::uint64_t session) const {
    const auto found = battles_.find(session);
    if (found == battles_.end()) throw std::invalid_argument("Missing fixture battle");
    return found->second.snapshot;
}

}
