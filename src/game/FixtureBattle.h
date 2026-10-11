#pragma once

#include <cstdint>
#include <functional>
#include <random>
#include <string>
#include <unordered_map>

namespace god2 {

struct FixtureCombatant {
    std::uint32_t hp, max_hp, mp, max_mp;
    std::uint32_t physical_attack, magical_attack, physical_defense, magical_defense;
};

struct FixtureDamage {
    std::uint32_t damage, mp_cost;
    bool critical;
};

struct FixtureBattleSnapshot {
    std::uint32_t battle_id, turn;
    FixtureCombatant player, monster;
    std::string outcome;
    FixtureDamage player_action{}, monster_action{};
};

// CUSTOM fixture only. Native originality: false. No native catalog or DB state.
// Single-threaded ownership; callbacks must not reenter this service. Callback
// side effects are outside rollback, so damage callbacks should be pure.
class FixtureBattleService {
public:
    using DamageCallback = std::function<FixtureDamage(
        const FixtureCombatant&, const FixtureCombatant&, std::uint8_t skill,
        std::uint32_t roll)>;

    explicit FixtureBattleService(DamageCallback damage);
    // Turns start at 1. IDs are never reused during this service's lifetime.
    FixtureBattleSnapshot start(std::uint64_t session);
    FixtureBattleSnapshot act(std::uint64_t session, std::uint32_t battle_id,
                              std::uint32_t turn, std::uint8_t skill);
    FixtureBattleSnapshot flee(std::uint64_t session, std::uint32_t battle_id,
                               std::uint32_t turn);
    void remove(std::uint64_t session);
    FixtureBattleSnapshot inspect(std::uint64_t session) const;

private:
    struct State {
        FixtureBattleSnapshot snapshot;
        std::mt19937 rng;
    };

    State& active(std::uint64_t session, std::uint32_t battle_id, std::uint32_t turn);
    void hit(State& state, FixtureCombatant& actor, FixtureCombatant& target,
             std::uint8_t skill, FixtureDamage& action);
    static FixtureBattleSnapshot commit(State& current, State& staged);

    DamageCallback damage_;
    std::unordered_map<std::uint64_t, State> battles_;
    std::uint64_t next_battle_id_ = 1;
};

}
