#pragma once
#include "handlers/RecoveredBattleService.h"

namespace god2 {
// CUSTOM-0058, owner-designed skill; never an original native skill.
struct ShunyingSanshazhan final {
    static constexpr std::uint8_t kind=0, id=126, max_targets=3;
    // CUSTOM-0058: owner-requested provisional physical coefficient, per target.
    static constexpr bool magical=false;
    static constexpr std::uint32_t provisional_power_percent=300;
    static constexpr std::uint32_t mp_cost=20;
    static constexpr auto key=RecoveredBattleService::skill_key(kind,id);
    static constexpr char design_id[]="CUSTOM-0058";
    static constexpr char traditional_name[]="瞬影三煞斬";

    // Approved formal policy: physical attack*300%, existing defense and
    // critical policy, one20MP charge for the complete1..3-target action.
    static BattleAction owned_action(const BattleAction& basic) {
        auto action=basic;action.targets.clear();action.magical=magical;
        action.power_percent=provisional_power_percent;action.mp_cost=mp_cost;
        return action;
    }

    // Caller must establish ownership and supply a qualified blade3 combat
    // policy plus native-client encoder. Never invent damage/cost here.
    static void authorize(RecoveredBattleService::Policy& policy,
                          const BattleAction& blade3, Battle::Encode encode) {
        if(!encode || policy.skills.contains(key) || policy.skill_target_limits.contains(key) ||
           policy.skill_encoders.contains(key))
            throw std::invalid_argument("Missing renderer or duplicate Shunying binding");
        auto staged=policy;
        auto action=blade3;action.targets.clear();
        staged.skills.emplace(key,std::move(action));
        staged.skill_target_limits.emplace(key,max_targets);
        staged.skill_encoders.emplace(key,std::move(encode));
        policy=std::move(staged);
    }

    struct VisualAssignment { std::uint8_t caster,target; bool clone; };
    // Visual clones borrow the CURRENT cast's actor appearance. They never
    // become battle actors or independently charge MP/apply damage. Client
    // adapter must snapshot that actor's layers/palettes per cast, and reuse
    // native blade3 hit markers for floating damage (no guessed frame times).
    static std::vector<VisualAssignment> visual_assignments(const BattleActionResult& result) {
        if(result.source>=28 || result.hits.empty() || result.hits.size()>max_targets)
            throw std::invalid_argument("Invalid Shunying cast result");
        std::array<bool,28> seen{};
        std::vector<VisualAssignment> out;
        for(const auto& hit:result.hits) {
            if(hit.target>=28 || hit.target/14==result.source/14 || seen[hit.target])
                throw std::invalid_argument("Invalid Shunying result target");
            seen[hit.target]=true;
            out.push_back({result.source,hit.target,!out.empty()});
        }
        return out;
    }
};
}
