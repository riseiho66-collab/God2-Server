#pragma once
#include "game/OwnedBattleFormation.h"
#include "protocol/RecoveredPveRoomProjection.h"
#include <nlohmann/json.hpp>
#include <memory>
namespace god2 {
// CUSTOM-0161/0162: immutable operator-authored encounter/format policy. No
// monster placement, client name lookup or packet supplies these combat stats.
// A whole DB version is validated before publication. Missing material fails;
// there is no diagnostic/default/first-item import fallback.
class OwnedPveWorldCatalog {
public:
    using Types=OwnedPveRoomTypes;
    struct Scene {
        std::uint64_t id{};
        std::uint16_t area{},scene{};
        std::uint32_t movement_steps{};
        OwnedBattleFormation::Topology topology;
        std::vector<BattleActor> enemies;
        std::map<std::uint8_t,RecoveredPveRoomProjection::ActorProfile> enemy_profiles;
        BattleAction basic,ai;
        nlohmann::json templates;
        bool support_enabled{};
    };
    explicit OwnedPveWorldCatalog(const nlohmann::json&);
    std::uint64_t version()const noexcept{return version_;}
    const std::string& source_sha256()const noexcept{return source_sha256_;}
    const std::string& source_record()const noexcept{return source_record_;}
    const Scene* scene(std::uint16_t area,std::uint16_t scene)const noexcept;
    // An exact native source tuple, not a fallback row. The actual source host
    // rechecks root/position and calls the room's full CAS before entry.
    const nlohmann::json& actor_profile(std::uint64_t character)const;
    // Select one complete explicitly supplied native pet profile by actual
    // active44 material. No species/name/default lookup or SQL is performed.
    // Optional per-variant CUSTOM owned_saved_vitals_level_v1 projects only
    // already-saved HP/MP maxima/current and level; other stats/metadata/source
    // bits remain pinned. Omitted policy retains legacy current-only matching.
    RecoveredPveRoomProjection::ActorProfile pet_profile(std::uint64_t character,
        const StoredPet2Slot&)const;
    bool has_actor_profile(std::uint64_t character)const noexcept{return actors_.contains(character);}
    static bool same_entry_material(const nlohmann::json& prototype,std::span<const std::uint8_t> actual);
    RecoveredPveRoomProjection::Profiles profiles(const Scene&,const Types::Snapshot&,
        const Types::Change&)const;
    static nlohmann::json schema_description();
private:
    std::uint64_t version_{};
    std::string source_sha256_,source_record_;
    std::vector<Scene> scenes_;
    std::map<std::uint64_t,nlohmann::json> actors_;
};
}
