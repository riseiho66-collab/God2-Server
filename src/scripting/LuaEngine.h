#pragma once

#include "db/NativeMapCatalog.h"
#include "db/NativeSkillCatalog.h"
#include "db/NativeSkillBookCatalog.h"
#include "db/NativeWeaponCatalog.h"
#include "db/NativeArmorCatalog.h"
#include "game/CombatRule.h"
#include "game/ProgressionRule.h"
#include "game/CharacterGrowthRule.h"
#include "game/SupplyRule.h"
#include "game/RevivalRule.h"
#include "game/TownGuideRule.h"
#include "game/DiagnosticDoorRule.h"
#include "game/OwnedGuildMembershipRule.h"

#include <cstdint>
#include <filesystem>
#include <functional>
#include <memory>
#include <optional>
#include <string>
#include <thread>
#include <vector>

namespace god2 {

struct FixtureCombatant;
struct FixtureDamage;

// Snapshots only: scripts never receive references to live game objects.
struct ScriptPlayer {
    std::uint64_t id{};
    std::string name;
};

struct ScriptMonster {
    std::uint64_t id{};
    std::uint32_t template_id{};
    std::optional<std::int32_t> hp;
};

class LuaEngine {
public:
    using SharedSkillLookupFunction=std::function<std::optional<SharedSkillLookup>(
        std::int64_t kind,std::int64_t definition_id)>;
    using NativeArmorLookup = std::function<std::optional<NativeArmorRecord>(std::uint16_t item)>;
    using NativeWeaponLookup = std::function<std::optional<NativeWeaponRecord>(std::uint16_t item)>;
    using NativeMapLookup = std::function<std::optional<NativeMapRecord>(std::int64_t area,
                                                                      std::int64_t scene)>;
    using NativeSkillLookup = std::function<std::optional<NativeSkillRecord>(std::int64_t kind,
                                                                          std::int64_t definition_id)>;
    using NativeSkillBookLookup = std::function<std::optional<NativeSkillBookRecord>(std::int64_t kind,
                                                                                  std::int64_t definition_id)>;
    // Standalone callers retain fixture behavior; the server supplies its runtime mode.
    // The callable is owned across reloads and runs on the game executor thread.
    // Borrowed dependencies captured by it must outlive the engine. nullopt means
    // missing; errors must throw. An empty callable reports unavailable to Lua.
    explicit LuaEngine(std::filesystem::path script_root = "scripts", bool fixture_mode = true,
                       NativeMapLookup native_map_lookup = {}, NativeSkillLookup native_skill_lookup = {},
                       NativeSkillBookLookup native_skill_book_lookup = {}, NativeWeaponLookup native_weapon_lookup = {},
                       NativeArmorLookup native_armor_lookup = {},
                       SharedSkillLookupFunction common_skill_lookup = {});
    ~LuaEngine();
    LuaEngine(const LuaEngine&) = delete;
    LuaEngine& operator=(const LuaEngine&) = delete;
    LuaEngine(LuaEngine&&) = delete;
    LuaEngine& operator=(LuaEngine&&) = delete;

    // Initialize, invoke, reload, and destroy on the same game executor thread.
    // initialize() is idempotent; it binds the thread but does not load bootstrap.
    bool initialize();
    bool load_script(const std::filesystem::path& path);
    bool load_directory(const std::filesystem::path& path);
    bool reload_all();
    void call_event(const std::string& event_name);
    bool has_npc(std::uint32_t npc_id) const;
    // Custom fixture rules only. Snapshot fields and results are bounded to 1,000,000;
    // skill is 1..3 and roll is 0..9999. The caller stages HP/MP changes.
    FixtureDamage fixture_damage(const FixtureCombatant& attacker, const FixtureCombatant& defender,
                                 std::uint8_t skill, std::uint32_t roll);
    // CUSTOM-0006: pure rule evaluation, available without fixture mode.
    // Caller owns actor/skill authorization, RNG, and transactional HP/MP mutation.
    CombatRuleResult combat_damage(const CombatRuleInput& input);
    // CUSTOM-0013: pure, explicit-table projection. No award, storage or growth mutation.
    ProgressionResult progression(const ProgressionInput& input);
    // Owner-confirmed per-level growth; caller supplies trusted profession,
    // persisted baseline and authorized levels. No client profile guessing.
    CharacterGrowthResult character_growth(const CharacterGrowthInput& input);
    CharacterGrowthResult allocate_attribute(const CharacterAllocationInput& input);
    // CUSTOM-0016: pure diagnostic policy. Caller owns item authorization/storage.
    SupplyResult supply(const SupplyInput& input);
    // CUSTOM-0085 placement only. C++ supplies explicitly owned empty bag
    // cells; scripts receive no DB/session refs or item-generation authority.
    std::optional<std::uint8_t> beast_equipment_destination(std::uint8_t source,
        const std::vector<std::uint8_t>& owned_empty_slots);
    // CUSTOM-0085 whole-instance discard eligibility, not original bind/drop
    // or activity rules. Inputs are copied from authoritative owned custody.
    bool beast_discard_allowed(std::uint8_t source,std::uint8_t quantity,
        bool native_exploring,bool alternate7,bool alternate8);
    bool beast_transfer_allowed(std::uint8_t source,std::uint8_t quantity,
        bool native_exploring,bool alternate7,bool alternate8);
    bool beast_bank_allowed(std::uint8_t operation,std::uint8_t page,std::uint8_t quantity,
        bool native_exploring,bool alternate7,bool alternate8);
    // CUSTOM-0086 negotiation eligibility only, no battle/stat/skill grants.
    bool pk_invitation_allowed(bool challenger_ready,bool recipient_ready,
        bool same_scene,bool distinct_characters,bool challenger_blocked,bool recipient_blocked);
    // CUSTOM-0017: isolated first-tier projection, no ownership or state mutation.
    RevivalResult revival(const RevivalInput& input);
    // CUSTOM-0021: pure proposed transition; no implicit acceptance or reward.
    TownGuidePlan town_guide(const TownGuideInput& input);
    // CUSTOM-0025: isolated proposal only; not called by production Application.
    std::optional<DiagnosticDoorPlan> diagnostic_door(const DiagnosticDoorInput& input);
    // CUSTOM-0078: pure reference-based membership policy; caller owns all
    // account/session authority, stale leases and atomic storage mutations.
    OwnedGuildMembershipPolicy owned_guild_membership(const OwnedGuildMembershipInput& input);
    std::string talk(std::uint32_t npc_id, std::uint64_t player_id,
                     const std::string& player_name);

    void quest_accept(std::uint32_t quest_id, const ScriptPlayer& player);
    void quest_complete(std::uint32_t quest_id, const ScriptPlayer& player);
    void monster_spawn(std::uint32_t ai_id, const ScriptMonster& monster);
    void monster_update(std::uint32_t ai_id, const ScriptMonster& monster, double dt);
    void monster_death(std::uint32_t ai_id, const ScriptMonster& monster,
                       const ScriptPlayer& killer);
    // The host must authorize the admin before invoking this API.
    void call_gm_command(const std::string& command, const ScriptPlayer& admin,
                         const std::vector<std::string>& args);

private:
    struct Vm;
    struct Entry { std::filesystem::path path; bool directory; };
    void check_thread() const;
    Vm& vm();
    std::filesystem::path resolve(const std::filesystem::path& path) const;
    bool rebuild(const std::vector<Entry>& entries);
    std::filesystem::path root_;
    const bool fixture_mode_;
    // One callable instance for both active and staged VMs, including mutable state.
    const std::shared_ptr<const NativeMapLookup> native_map_lookup_;
    const std::shared_ptr<const NativeSkillLookup> native_skill_lookup_;
    const std::shared_ptr<const NativeSkillBookLookup> native_skill_book_lookup_;
    const std::shared_ptr<const NativeWeaponLookup> native_weapon_lookup_;
    const std::shared_ptr<const NativeArmorLookup> native_armor_lookup_;
    const std::shared_ptr<const SharedSkillLookupFunction> common_skill_lookup_;
    std::thread::id owner_;
    std::unique_ptr<Vm> vm_;
    std::vector<Entry> entries_;
};

} // namespace god2
