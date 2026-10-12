#pragma once
#include <filesystem>
#include <string>
#include <cstdint>
#include "protocol/ProtocolMode.h"
namespace god2 {
struct Config {
    ProtocolMode protocol_mode=ProtocolMode::Fixture;
    std::string name, host, log_level;
    std::uint16_t port{};
    std::size_t max_sessions{}, worker_threads{};
    bool packet_dump{}, hot_reload{}, mock_login{};
    bool fixture_battle{};
    bool recovered_account_auth{}, local_account_registration{};
    bool recovered_character_creation{};
    bool recovered_dual_connection{};
    bool recovered_world_entry{};
    bool world_clock_enabled=false;
    bool owned_map_views_enabled=false;
    bool owned_daily_quest_views_enabled=false;
    bool owned_guild_relations53_enabled=false; // PRIVATE inactive CUSTOM84; no production receiver baseline.
    bool owned_guild_succession_enabled=false; // CUSTOM0083 explicit transfer; installed52 effective reads retained disabled.
    bool owned_guild_officers_enabled=false; // CUSTOM0082 explicit gameplay only; installed51 retained disabled.
    bool owned_guild_announcements_enabled=false; // CUSTOM-0078: explicit native79/98 route.
    bool owned_guild_membership_enabled=false; // CUSTOM-0078: explicit formal player admission.
    std::string owned_guild_entry_resource_bundle; // Qualified two-locale append2996 bundle.
    bool streamer_privileges_enabled=false; // CUSTOM-0054 requires the matching embedded client.
    bool owned_whole_bag_moves_enabled=false; // CUSTOM-0094 existing-owner full25 only; no population/import.
    bool owned_supply_enabled=false;
    bool owned_beast_panel_enabled=false; // CUSTOM-0085 display only; source-phase opt-in
    bool owned_pk_invitation_enabled=false; // CUSTOM-0086 incomplete until shared room authority exists
    bool owned_attribute_allocation_enabled=false;
    bool fruit_village_quests_enabled=false;
    bool fruit_sourcehint_placements=false;
    std::filesystem::path fruit_navigation;
    bool owned_weapon_transfers_enabled=false;
    bool owned_armor_transfers_enabled=false; // CUSTOM-0066: instance transport; formulas/appearance separate.
    bool owned_foreign_bank_enabled=false; // CUSTOM-0068: native weapon/gem custody, opt-in.
    bool owned_mixed_bank_enabled=false; // CUSTOM-0070: full-instance cross-category vault swaps, opt-in.
    bool owned_instance_discard_enabled=false; // CUSTOM-0071: whole owned typed discard, opt-in.
    bool owned_instance_trade_enabled=false; // CUSTOM-0069: whole owned-instance trade, opt-in.
    bool owned_armor_bank_enabled=false; // CUSTOM-0067: whole-instance bank custody, opt-in.
    bool owned_teleport_gem_enabled=false;
    bool owned_player_appearance_enabled=false;
    bool diagnostic_owned_weapon_appearance=false;
    unsigned world_clock_sync_seconds=60;
    bool recovered_movement{};
    bool diagnostic_battle_transition{};
    bool native_monster_placements_only=false;
    bool diagnostic_battle_after_movement{};
    unsigned diagnostic_encounter_limit{1};
    bool diagnostic_battle_participants{};
    bool diagnostic_battle_player_appearance{};
    bool diagnostic_battle_animations{};
    bool diagnostic_battle_skill_seed{};
    bool diagnostic_shunying_manual{}; // CUSTOM-0058: isolated, nonpersistent 14-enemy UI trial.
    bool diagnostic_thousand_bulls_manual{}; // CUSTOM-0059:150 instead of126 in that isolated trial only.
    bool diagnostic_recording_fixed_damage{}; // CUSTOM-0059 isolated9999-hit/99999-HP recording fixture.
    std::uint64_t diagnostic_shunying_character_id{}; // Only this disposable character receives the trial.
    unsigned diagnostic_battle_skill_kind{}; // CUSTOM-0012: isolated native family probe only.
    bool diagnostic_battle_revival{};
    bool diagnostic_battle_skill_settlement{};
    bool diagnostic_battle_mp_refusal{};
    bool diagnostic_battle_resources{};
    // Shared64 input type; this legacy diagnostic profile still requires its
    // separately checked signed32 native display bound in Config::load.
    std::uint64_t diagnostic_battle_experience{};
    bool diagnostic_role_progress{};
    bool diagnostic_level_snapshot{};
    bool diagnostic_character_growth{}; // owner-confirmed growth; isolated native22 acceptance
    bool diagnostic_resume_checkpoint{};
    std::uint32_t diagnostic_progress_span{};
    bool diagnostic_world_resources{};
    bool diagnostic_quest_dialogue{};
    bool diagnostic_knowledge_menu{};
    bool diagnostic_quest_npc{};
    bool diagnostic_world_supply{};
    unsigned diagnostic_battle_rounds{1};
    bool diagnostic_battle_terminal{};
    std::filesystem::path recovered_navigation;
    bool diagnostic_remote_actor=false;
    bool diagnostic_player_visibility=false;
    bool diagnostic_visibility_battle=false;
    bool diagnostic_visibility_checkpoint=false;
    bool diagnostic_visibility_skill_recovery=false;
    unsigned diagnostic_remote_actor_language=0;
    bool diagnostic_town=false;
    bool diagnostic_town_spawn_guides=false;
    // Owner native-only placement policy. Keeps isolated fixture support
    // explicit while preventing its invented positions in the configured game.
    bool native_npc_placements_only=false;
    bool diagnostic_town_chat_welcome=false;
    bool diagnostic_town_quest_progress=false;
    bool diagnostic_town_map_probe=false;
    bool diagnostic_town_scene_probe=false;
    bool diagnostic_town_scene_relocate=false;
    bool diagnostic_town_scene_indoor_probe=false;
    bool diagnostic_town_scene_indoor_transfer=false;
    bool diagnostic_town_scene_return_probe=false;
    bool diagnostic_town_scene_return_commit=false;
    bool diagnostic_town_door_routes=false;
    bool diagnostic_town_all_door_routes=false;
    bool diagnostic_kunlun_door_routes=false;
    bool diagnostic_kunlun_parent_routes=false; // CUSTOM-0053 exact source mutual parent edge.
    bool diagnostic_town_island_routes=false;
    bool diagnostic_town_player_visibility=false;
    bool diagnostic_town_battle_after_quest=false;
    bool diagnostic_town_return_after_battle=false;
    bool diagnostic_town_door_after_battle=false;
    std::filesystem::path diagnostic_town_indoor_navigation;
    std::filesystem::path diagnostic_town_indoor_scenes;
    std::filesystem::path diagnostic_kunlun_indoor_scenes;
    std::filesystem::path diagnostic_kunlun_parent_navigation;
    std::filesystem::path diagnostic_town_island_navigation;
    std::filesystem::path character_birthplace_navigation;
    std::uint16_t character_birthplace_x{},character_birthplace_y{};
    bool diagnostic_town_source_consensus=false;
    int diagnostic_town_center_x=0,diagnostic_town_center_y=0;
    std::uint16_t diagnostic_town_x=0,diagnostic_town_y=0;
    std::uint16_t character_port{};
    std::filesystem::path database, script_root, bootstrap, log_file;
    std::filesystem::path chinese_dictionary_root;
    bool owned_blacklist_enabled=false; // CUSTOM-0096 explicit source opt-in only
    bool owned_party_directory_enabled=false; // CUSTOM-0097 transient discovery opt-in
    bool owned_client_options_enabled=false; // CUSTOM-0100 opaque preference WORD; no gameplay authority
    bool owned_battle_pose_enabled=false; // CUSTOM-0103 actual diagnostic battle symbol source only
    void validate_owned_whole_bag_moves() const;
    static Config load(const std::filesystem::path& path);
};
}
