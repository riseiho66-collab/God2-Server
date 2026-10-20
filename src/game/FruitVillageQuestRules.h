#pragma once
#include "InferredQuestRules.h"
#include <string_view>

namespace god2::FruitVillageQuestRules {
// CUSTOM-0051. Source text is native; executable quest policy is inferred.
// Generated-source qualification: current_inferred_quest_sources_20260927.py.
inline constexpr std::string_view client_sha256="6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98";
inline constexpr std::string_view bundle_sha256="ab3e063564d0e7b351c3abab9e3475419c3a710ec9371b3de4d9b01f44a76541";
inline constexpr const char* wiki="https://wiki2.gamer.com.tw/wiki.php?n=8591%3A%E6%9E%9C%E5%8A%9B%E6%9D%91";
inline constexpr const char* policy="CUSTOM-0051; inferred once-only scalar collection; no prerequisite; no currency/item reward; maximum level255";
struct Descriptor {
    std::uint32_t mission_id;
    std::uint16_t npc_catalog,item;
    std::uint32_t quantity,minimum_level;
    std::uint64_t experience,reputation;
    std::uint16_t source_x,source_y;
    std::uint32_t idle_before,offer,incomplete,completion,idle_after;
    std::uint32_t mission_definition_line,item_source_line;
    // Coordinates are source text hints, NOT spawn instructions. No direction
    // or world instance is fabricated. Text roles are semantic inferred joins.
};
inline constexpr std::uint8_t area=13,scene=12,kind=0;
inline constexpr std::array<Descriptor,4> descriptors{{
    {234,2936,5098,5,3,400,1,108,110,8885,8886,8887,8888,8889,1487,8074},
    {236,2937,5091,5,10,3000,1,113,69,8890,8891,8892,8893,8894,1491,8067},
    {237,2938,5098,10,5,1500,1,69,72,8900,8901,8902,8903,8904,1493,8074},
    {238,2939,3464,20,8,2000,1,68,116,8895,8896,8897,8898,8899,1495,6801}
}};
// Existing CUSTOM-0037 scalar material domain, shared by collection and banking.
// This is not permission for arbitrary materials or full captured instances.
inline constexpr bool material(std::uint16_t item) noexcept {
    return item==5098 || item==5091 || item==3464;
}
inline constexpr const Descriptor* find(std::uint32_t id) noexcept {
    for(const auto& entry:descriptors)if(entry.mission_id==id)return &entry;
    return nullptr;
}
// Only known immutable source entries can manufacture a qualified rule.
// This factory does not accept caller-provided descriptors or promote unknowns.
inline std::optional<InferredQuestRules::Rule> rule(std::uint32_t id) {
    namespace q=InferredQuestRules;
    const auto* d=find(id);if(!d)return std::nullopt;
    const std::string native="CURRENT_SOURCE client="+std::string(client_sha256)+
        "; bundle="+std::string(bundle_sha256)+"; Mission_data:"+std::to_string(d->mission_definition_line);
    const std::string item_source=native+"; gamedata:"+std::to_string(d->item_source_line);
    const auto inferred=[]<class T>(T value,std::string reference=policy)->q::Fact<T> {
        return {std::move(value),{q::Origin::CustomInferred,std::move(reference)}};
    };
    q::Rule result;
    result.authority={q::policy_design_id,"docs/research/current-inferred-quest-sources-20260927.md"};
    result.id={id,{q::Origin::NativeVerified,native}};result.revision=1;
    result.level=inferred(q::LevelRange{d->minimum_level,255},std::string(wiki)+"; historical minimum adopted; maximum255 CUSTOM-0051; rebirth prerequisite not recovered");
    result.completed_prerequisites=inferred(std::vector<q::QuestId>{});
    result.repeat=inferred(q::Repeat::Once);
    result.collect_objective_complete=inferred(true,"CUSTOM-0051; intentionally complete collect-only design, not recovered absence of hidden native conditions");
    q::Requirement requirement;
    requirement.item={d->item,{q::Origin::NativeVerified,item_source}};
    requirement.quantity={d->quantity,{q::Origin::NativeVerified,native+" description + NPCMission09 text"}};
    requirement.consume=inferred(true);
    requirement.match=inferred(q::Match{});
    result.requirements=inferred(std::vector<q::Requirement>{std::move(requirement)});
    result.rewards.currency=inferred(std::uint64_t{0});
    result.rewards.experience=inferred(d->experience,std::string(wiki)+"; historical reward adopted as CUSTOM-0051, not build-matched native reward");
    result.rewards.reputation=inferred(d->reputation,std::string(wiki)+"; historical reward adopted as CUSTOM-0051, not build-matched native reward");
    result.rewards.stacks=inferred(std::vector<q::RewardStack>{});
    return result;
}
} // namespace god2::FruitVillageQuestRules
