#pragma once
#include "game/CombatRule.h"
#include "game/BattleNumericProfile.h"
#include "protocol/RecoveredBattleDelta.h"
#include "game/RevivalRule.h"
#include "game/PoisonRule.h"
#include <array>
#include <cstdint>
#include <functional>
#include <optional>
#include <random>
#include <span>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>
namespace god2 {
class RecoveredBattleService;
enum class BattleState { Pending, Active, Finished };
// A resource refusal is distinguishable only after identity and target validation.
class InsufficientBattleMp final : public std::invalid_argument {
public:
    InsufficientBattleMp(std::uint32_t available,std::uint32_t required)
        : std::invalid_argument("Insufficient battle MP"), available(available), required(required) {}
    const std::uint32_t available, required;
};
struct BattleActor {
    std::uint8_t position;
    std::uint64_t controller; // Zero is server AI, never a client credential.
    std::uint64_t hp, max_hp;
    std::uint32_t mp, max_mp;
    std::uint32_t physical_attack, magical_attack, physical_defense, magical_defense;
    bool operator==(const BattleActor&) const = default;
};
struct BattleSnapshot {
    std::uint64_t id, revision;
    BattleState state;
    std::array<std::optional<BattleActor>,28> actors;
    // CUSTOM-0007 authoritative side elimination, not client outcome/display bytes.
    std::optional<std::uint8_t> victorious_side;
    BattleNumericProfile numeric_profile{BattleNumericProfile::LegacyCustom};
    bool operator==(const BattleSnapshot&) const = default;
};
// CUSTOM-0007 server-owned checkpoint, never a client wire record.
struct BattleCheckpoint {
    std::uint32_t version{1};
    BattleSnapshot snapshot;
    std::string random_state;
    bool operator==(const BattleCheckpoint&) const = default;
};
struct BattleAction {
    std::uint8_t source;
    std::vector<std::uint8_t> targets;
    bool magical;
    std::uint32_t power_percent, defense_percent, mp_cost;
    std::uint32_t critical_chance_bp, critical_multiplier_percent;
};
struct BattleHit {
    std::uint8_t target;
    std::uint64_t damage, hp_loss;
    bool critical;
};
struct BattleActionResult {
    std::uint8_t source;
    std::uint32_t mp_cost;
    std::vector<BattleHit> hits;
};
struct BattleRevivalResult {
    std::uint8_t source, target;
    std::uint64_t hp_gain;
    std::uint32_t mp_cost;
};
// CUSTOM-0007: single-game-executor transactional action core. Callbacks must
// be pure/non-reentrant. Encoding prepares bytes; it must not send or persist.
// Controller, revision, skill parameters and targets must come from an
// authorized server policy, not blindly from client fields.
class Battle {
public:
    // One service-qualified receiver view for this exact exchange. Only the
    // real Session bridge may supply it; actor policy/pose is not selfslot.
    class NativeDeltaView {
    public:
        NativeDeltaView(const NativeDeltaView&)=default;
        NativeDeltaView& operator=(const NativeDeltaView&)=default;
    private:
        friend class Battle;
        friend class RecoveredBattleService;
        NativeDeltaView(std::uint64_t battle,std::uint64_t revision,std::uint64_t controller,
                        std::uint8_t primary_slot)
            :battle_(battle),revision_(revision),controller_(controller),primary_slot_(primary_slot){}
        std::uint64_t battle_,revision_,controller_;
        std::uint8_t primary_slot_;
    };
    using Rule = std::function<CombatRuleResult(const CombatRuleInput&)>;
    using Encode = std::function<std::vector<std::uint8_t>(const BattleSnapshot&, const BattleActionResult&)>;
    using RevivalRule = std::function<RevivalResult(const RevivalInput&)>;
    using RevivalEncode = std::function<std::vector<std::uint8_t>(const BattleSnapshot&, const BattleRevivalResult&)>;
    using NativeDeltaEncode = std::function<std::vector<std::uint8_t>(const BattleSnapshot&,
        std::span<const RecoveredBattleDelta::Record>)>;
    using PoisonRule = std::function<PoisonShareResult(const PoisonShareInput&)>;
    Battle(std::uint64_t id, std::span<const BattleActor> actors, std::uint32_t seed,
           BattleNumericProfile profile=BattleNumericProfile::LegacyCustom);
    BattleCheckpoint checkpoint() const;
    static Battle restore(const BattleCheckpoint& checkpoint);
    bool active() const noexcept;
    const BattleSnapshot& inspect() const noexcept { return snapshot_; }
    // CUSTOM-0157 read-only current-snapshot observation. The pure/non-reentrant
    // rule returns the exact ratio and owner-confirmed floored damage amount;
    // no status permission, tick, HP mutation or settlement is inferred.
    // Revision and the actual current maximum HP are rechecked after it.
    PoisonShareResult poison_share(std::uint64_t revision,std::uint8_t target,
                                   const PoisonRule& rule) const;
    std::vector<std::uint8_t> act(std::uint64_t controller, std::uint64_t revision,
                                const BattleAction& action, const Rule& rule, const Encode& encode);
    // Trusted already-computed server results only, never incoming client83.
    // Existing action, fresh zeroed per-entry accumulators; no reset/formatting emulation.
    std::vector<std::uint8_t> apply_native_deltas(std::uint64_t controller,std::uint64_t revision,
        std::span<const RecoveredBattleDelta::Record> records,const NativeDeltaEncode& encode,
        std::optional<NativeDeltaView> view=std::nullopt);
    // CUSTOM-0017: caller must authorize the owned skill. Active battle only;
    // no revival after elimination, no RNG draw and no storage/send in callbacks.
    std::vector<std::uint8_t> revive(std::uint64_t controller,std::uint64_t revision,
        std::uint8_t source,std::uint8_t target,const RevivalRule& rule,const RevivalEncode& encode);
private:
    Battle(BattleSnapshot snapshot,std::mt19937 rng):snapshot_(std::move(snapshot)),rng_(std::move(rng)) {}
    BattleSnapshot snapshot_;
    std::mt19937 rng_;
};
}
