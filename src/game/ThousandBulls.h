#pragma once
#include "handlers/RecoveredBattleService.h"

namespace god2 {
// CUSTOM-0059. Owner-designed physical all-opponents skill, not native balance.
struct ThousandBulls final {
    static constexpr std::uint8_t kind=0,id=150,max_targets=14;
    static constexpr std::uint32_t power_percent=1000,mp_cost=100;
    static constexpr auto key=RecoveredBattleService::skill_key(kind,id);
    static constexpr char design_id[]="CUSTOM-0059";
    static constexpr char traditional_name[]="牛轉仙界踏";
    // Cost provenance: original cbspec2 kind0/id73 鯨吞亂舞, record+0x42
    // (file offset7994) WORD6400=100. This is the owner-selected native cost
    // reference; the new skill coefficient and four presentation phases are custom.
    static constexpr std::array<unsigned,4> hit_ticks{70,110,150,190};
    static constexpr unsigned duration_ticks=240,ticks_per_second=30;

    static BattleAction owned_action(const BattleAction& basic) {
        auto action=basic;action.targets.clear();action.magical=false;
        action.power_percent=power_percent;action.mp_cost=mp_cost;return action;
    }
    static void authorize(RecoveredBattleService::Policy& policy,const BattleAction& action,
                          Battle::Encode encode) {
        if(!encode || policy.skills.contains(key) || policy.skill_target_limits.contains(key) ||
           policy.skill_encoders.contains(key) || policy.skill_all_living_opponents.contains(key))
            throw std::invalid_argument("Missing renderer or duplicate ThousandBulls binding");
        auto staged=policy;auto owned=owned_action(action);
        staged.skills.emplace(key,std::move(owned));
        staged.skill_target_limits.emplace(key,max_targets);
        staged.skill_encoders.emplace(key,std::move(encode));
        staged.skill_all_living_opponents.emplace(key);policy=std::move(staged);
    }
    // Presentation only: split the already authoritative, defense-adjusted and
    // remaining-HP-clamped loss. Never call the damage formula four times.
    // uint64 products prevent overflow. Differences of cumulative20/45/75/100
    // percent floors conserve every point and distribute small totals fairly.
    static constexpr std::array<std::uint32_t,4> presentation_losses(std::uint32_t total) noexcept {
        const auto a=static_cast<std::uint32_t>(std::uint64_t{total}*20/100);
        const auto b=static_cast<std::uint32_t>(std::uint64_t{total}*45/100);
        const auto c=static_cast<std::uint32_t>(std::uint64_t{total}*75/100);
        return {a,b-a,c-b,total-c};
    }
    static void validate_result(const BattleActionResult& result) {
        if(result.source>=28 || result.hits.empty() || result.hits.size()>max_targets)
            throw std::invalid_argument("Invalid ThousandBulls cast result");
        std::array<bool,28> seen{};
        for(const auto& hit:result.hits) {
            if(hit.target>=28 || hit.target/14==result.source/14 || seen[hit.target])
                throw std::invalid_argument("Invalid ThousandBulls result target");
            seen[hit.target]=true;
        }
    }
};
}
