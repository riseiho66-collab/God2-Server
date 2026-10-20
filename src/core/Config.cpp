#include "core/Config.h"
#include <fstream>
#include <stdexcept>
#include <asio/ip/address.hpp>
#include <nlohmann/json.hpp>
namespace god2 {
void Config::validate_owned_pve_material_sources() const {
    // CUSTOM-0047 changes runtime DA independently of the retained2A and the
    // complete CUSTOM-0161 Fight profiles. No native after-state bridge owns
    // that combination; reject before any DB/Session mutation, not after equip.
    if(owned_pve_rooms_enabled&&diagnostic_owned_weapon_appearance)
        throw std::invalid_argument("Owned PvE cannot combine runtime diagnostic weapon appearance without a complete native material successor");
}
void Config::validate_owned_whole_bag_moves() const {
    if(!owned_whole_bag_moves_enabled)return;
    if(protocol_mode!=ProtocolMode::God2LegacyCharacterListCandidate || !recovered_account_auth ||
       mock_login || !recovered_character_creation || !recovered_dual_connection ||
       !recovered_world_entry || !recovered_movement || recovered_navigation.empty())
        throw std::invalid_argument("Whole bag moves require actual authenticated native TW normal entry and movement");
    // The dedicated same-map joint movement source does not run legacy
    // transfer/probe or visibility publication hooks. Their Tick handoffs and
    // postmove callbacks require a separate complete material/lifecycle owner.
    if(diagnostic_town_map_probe || diagnostic_town_scene_probe || diagnostic_town_scene_relocate ||
       diagnostic_town_scene_indoor_probe || diagnostic_town_scene_indoor_transfer ||
       diagnostic_town_scene_return_probe || diagnostic_town_scene_return_commit ||
       diagnostic_town_door_routes || diagnostic_town_all_door_routes || diagnostic_kunlun_door_routes ||
       diagnostic_kunlun_parent_routes || diagnostic_town_island_routes || diagnostic_player_visibility ||
       diagnostic_town_player_visibility || diagnostic_remote_actor || diagnostic_owned_weapon_appearance)
        throw std::invalid_argument("Whole bag joint movement cannot combine legacy transfer/probe or diagnostic visibility/appearance experiments");
    // Other inventory populations/projections and diagnostic settlements have
    // independent custody policies. Do not combine their scalar/typed banks.
    if(owned_map_views_enabled || owned_supply_enabled || owned_weapon_transfers_enabled ||
       owned_armor_transfers_enabled || owned_beast_panel_enabled || owned_foreign_bank_enabled ||
       owned_mixed_bank_enabled || owned_instance_discard_enabled || owned_instance_trade_enabled ||
       owned_armor_bank_enabled || owned_teleport_gem_enabled || fruit_village_quests_enabled ||
       diagnostic_world_supply || diagnostic_town_quest_progress || diagnostic_quest_dialogue ||
       fixture_battle || diagnostic_battle_transition || diagnostic_battle_after_movement ||
       diagnostic_battle_participants || diagnostic_battle_player_appearance || diagnostic_battle_animations ||
       diagnostic_battle_skill_seed || diagnostic_shunying_manual || diagnostic_thousand_bulls_manual ||
       diagnostic_recording_fixed_damage || diagnostic_battle_skill_kind || diagnostic_battle_revival ||
       diagnostic_battle_skill_settlement || diagnostic_battle_mp_refusal || diagnostic_battle_resources ||
       diagnostic_battle_experience || diagnostic_role_progress || diagnostic_level_snapshot ||
       diagnostic_character_growth || diagnostic_resume_checkpoint || diagnostic_progress_span ||
       diagnostic_battle_terminal || diagnostic_visibility_battle || diagnostic_visibility_skill_recovery ||
       diagnostic_town_battle_after_quest || diagnostic_town_return_after_battle || diagnostic_town_door_after_battle)
        throw std::invalid_argument("Whole bag moves cannot combine scalar/typed inventory populations or diagnostic battle/quest settlements");
}
Config Config::load(const std::filesystem::path& path) {
    std::ifstream stream(path);
    if (!stream) throw std::runtime_error("Cannot open config: " + path.string());
    const auto j = nlohmann::json::parse(stream);
    const auto root = std::filesystem::absolute(path).parent_path().parent_path();
    auto resolve = [&](const std::string& value) { return (root / value).lexically_normal(); };
    Config c;
    const auto& s = j.at("server");
    c.name=s.at("name").get<std::string>(); c.host=s.at("host").get<std::string>();
    auto integer_limit = [&](const char* field, int minimum, int maximum) {
        const auto& value = s.at(field);
        const auto invalid = [&] {
            return std::runtime_error(std::string("Invalid server limit: ") + field);
        };
        if (!value.is_number_integer()) throw invalid();
        // Validate at the JSON integer width before narrowing to the config type.
        if (value.is_number_unsigned()) {
            const auto number = value.get<std::uint64_t>();
            if (number < static_cast<std::uint64_t>(minimum)
                || number > static_cast<std::uint64_t>(maximum)) throw invalid();
            return static_cast<int>(number);
        }
        const auto number = value.get<std::int64_t>();
        if (number < minimum || number > maximum) throw invalid();
        return static_cast<int>(number);
    };
    const auto port=integer_limit("port", 0, 65535);
    const auto workers=integer_limit("worker_threads", 1, 64);
    const auto sessions=integer_limit("max_sessions", 1, 100000);
    c.port=static_cast<std::uint16_t>(port); c.worker_threads=workers; c.max_sessions=sessions;
    const auto& p=j.at("protocol");
    if(p.at("mode")=="god2_recovered" || p.at("mode")=="god2_post_seed" || p.at("mode")=="god2_c2s0002" || p.at("mode")=="god2_login_terminal" || p.at("mode")=="god2_server_list" || p.at("mode")=="god2_post_server_select" || p.at("mode")=="god2_legacy_character_list_candidate") {
        if(p.at("packet_header")!="uint16_length_seed_checksum" || p.at("encryption")!="seed_fixture" || p.at("compression")!="none")
            throw std::runtime_error("Recovered mode supports only the verified zero-seed exchange");
        c.protocol_mode=p.at("mode")=="god2_post_seed"?ProtocolMode::God2PostSeed:ProtocolMode::God2Recovered;
        if(p.at("mode")=="god2_c2s0002") c.protocol_mode=ProtocolMode::God2C2S0002;
        if(p.at("mode")=="god2_login_terminal") c.protocol_mode=ProtocolMode::God2LoginTerminal;
        if(p.at("mode")=="god2_server_list") c.protocol_mode=ProtocolMode::God2ServerList;
        if(p.at("mode")=="god2_post_server_select") c.protocol_mode=ProtocolMode::God2PostServerSelect;
        if(p.at("mode")=="god2_legacy_character_list_candidate") {
            c.protocol_mode=ProtocolMode::God2LegacyCharacterListCandidate;
            if(p.value("allow_unverified_legacy",false)!=true)
                throw std::runtime_error("Legacy character-list candidate requires explicit unverified opt-in");
        }
        if(!asio::ip::make_address(c.host).is_loopback()) throw std::runtime_error("Recovered lab mode requires loopback");
    } else if(p.at("mode")!="placeholder" || p.at("packet_header")!="uint16_length_uint16_opcode" || p.at("encryption")!="none" || p.at("compression")!="none")
        throw std::runtime_error("Only explicit PLACEHOLDER protocol with no crypto/compression is implemented");
    if(j.at("database").at("type")!="sqlite") throw std::runtime_error("Database backend is not implemented");
    c.packet_dump=p.at("packet_dump").get<bool>();
    c.database=resolve(j.at("database").at("path").get<std::string>());
    if(j.at("database").contains("taiwan_skill_profile")) {
        const auto& profile=j.at("database").at("taiwan_skill_profile");
        if(!profile.is_string())throw std::runtime_error("Taiwan skill profile string required");
        const auto value=profile.get<std::string>();
        if(value=="historical448")c.taiwan_skill_profile=NativeTaiwanSkillProfile::Historical448;
        else if(value=="installed453")c.taiwan_skill_profile=NativeTaiwanSkillProfile::Installed453;
        else throw std::runtime_error("Unknown Taiwan skill source profile");
    }
    c.script_root=resolve(j.at("lua").at("script_root").get<std::string>());
    c.bootstrap=resolve(j.at("lua").at("bootstrap").get<std::string>());
    c.hot_reload=j.at("lua").at("hot_reload").get<bool>();
    c.log_file=resolve(j.at("logging").at("file").get<std::string>());
    c.log_level=j.at("logging").at("level").get<std::string>();
    c.chinese_dictionary_root=resolve(j.value("text",nlohmann::json::object())
        .value("dictionary_root",std::string("resources/opencc")));
    c.mock_login=j.at("development").at("mock_login").get<bool>();
    c.fixture_battle=j.at("development").value("fixture_battle",false);
    if(c.fixture_battle && (c.protocol_mode!=ProtocolMode::Fixture || !c.mock_login ||
        !asio::ip::make_address(c.host).is_loopback() || c.database.filename()!="fixture-combat.sqlite"))
        throw std::runtime_error("Custom fixture battle requires loopback, placeholder mode, mock login and a dedicated fixture-combat.sqlite database");
    c.recovered_account_auth=j.at("development").value("recovered_account_auth",false);
    c.local_account_registration=j.at("development").value("local_account_registration",false);
    c.recovered_character_creation=j.at("development").value("recovered_character_creation",false);
    c.recovered_dual_connection=j.at("development").value("recovered_dual_connection",false);
    c.recovered_world_entry=j.at("development").value("recovered_world_entry",false);
    if(c.recovered_world_entry && !c.recovered_dual_connection)
        throw std::runtime_error("Recovered world entry candidate requires dual connection");
    c.recovered_movement=j.at("development").value("recovered_movement",false);
    if(c.recovered_movement) {
        if(!c.recovered_world_entry) throw std::runtime_error("Recovered movement requires world entry");
        const auto navigation=j.at("development").at("recovered_navigation").get<std::string>();
        if(navigation.empty()) throw std::runtime_error("Recovered movement requires navigation data");
        c.recovered_navigation=resolve(navigation);
    }
    if(c.recovered_dual_connection) {
        c.character_port=static_cast<std::uint16_t>(integer_limit("character_port",0,65535));
        if(!c.recovered_character_creation || !asio::ip::make_address(c.host).is_v4())
            throw std::runtime_error("Dual connection requires character persistence and IPv4 loopback");
        if(c.port && c.port==c.character_port)
            throw std::runtime_error("Dual connection requires distinct listener ports");
    }
    c.diagnostic_remote_actor=j.at("development").value("diagnostic_remote_actor",false);
    c.diagnostic_player_visibility=j.at("development").value("diagnostic_player_visibility",false);
    c.diagnostic_visibility_battle=j.at("development").value("diagnostic_visibility_battle",false);
    c.diagnostic_visibility_checkpoint=j.at("development").value("diagnostic_visibility_checkpoint",false);
    c.diagnostic_visibility_skill_recovery=j.at("development").value("diagnostic_visibility_skill_recovery",false);
    if(c.diagnostic_visibility_battle && !c.diagnostic_player_visibility)
        throw std::runtime_error("Visibility battle requires player visibility");
    if(c.diagnostic_player_visibility) {
        if(!c.recovered_movement || !c.recovered_dual_connection || c.mock_login || !c.recovered_account_auth ||
           !asio::ip::make_address(c.host).is_loopback() ||
           c.database.filename()!="player-visibility-diagnostic.db")
            throw std::runtime_error("Player visibility requires isolated authenticated loopback movement database");
        const auto language=j.at("development").at("diagnostic_remote_actor_language");
        if(!language.is_number_integer() || language<0 || language>1)
            throw std::runtime_error("Player visibility requires explicit language bit0..1");
        c.diagnostic_remote_actor_language=language.get<unsigned>();
        for(const auto& [key,value]:j.at("development").items()) {
            // CUSTOM-0027: explicit terminal or checkpointed skill fixture only.
            if(c.diagnostic_visibility_battle &&
               (key=="diagnostic_visibility_battle" || key=="diagnostic_battle_transition" ||
                key=="diagnostic_battle_participants" || key=="diagnostic_battle_player_appearance" ||
                key=="diagnostic_battle_animations" || key=="diagnostic_battle_terminal" ||
                key=="diagnostic_battle_resources" ||
                key=="diagnostic_visibility_checkpoint" ||
                (c.diagnostic_visibility_skill_recovery && (key=="diagnostic_visibility_skill_recovery" ||
                    key=="diagnostic_battle_skill_seed" || key=="diagnostic_battle_skill_settlement" ||
                    (key=="diagnostic_battle_rounds" && value.is_number_integer() && value==3))) ||
                (key=="diagnostic_battle_rounds" && value.is_number_integer() && value==1))) continue;
            if(key.starts_with("diagnostic_") && key!="diagnostic_player_visibility" &&
               key!="diagnostic_remote_actor_language" && value!=false)
                throw std::runtime_error("Player visibility cannot combine other diagnostic modes");
        }
    }
    if(c.diagnostic_remote_actor) {
        if(!c.recovered_movement || c.mock_login || !c.recovered_account_auth ||
           !asio::ip::make_address(c.host).is_loopback() ||
           c.database.filename()!="remote-actor-diagnostic.db")
            throw std::runtime_error("Remote actor diagnostic requires isolated authenticated loopback movement database");
        const auto language=j.at("development").at("diagnostic_remote_actor_language");
        if(!language.is_number_integer() || language<0 || language>1)
            throw std::runtime_error("Remote actor diagnostic requires explicit language bit0..1");
        c.diagnostic_remote_actor_language=language.get<unsigned>();
        for(const auto& [key,value]:j.at("development").items())
            if(key.starts_with("diagnostic_") && key!="diagnostic_remote_actor" &&
               key!="diagnostic_remote_actor_language" && value!=false)
                throw std::runtime_error("Remote actor diagnostic cannot combine other diagnostic modes");
    }
    c.diagnostic_battle_transition=j.at("development").value("diagnostic_battle_transition",false);
    c.native_monster_placements_only=j.at("development").value("native_monster_placements_only",false);
    c.streamer_privileges_enabled=j.at("development").value("streamer_privileges",false);
    c.diagnostic_knowledge_menu=j.at("development").value("diagnostic_knowledge_menu",false);
    c.diagnostic_town=j.at("development").contains("diagnostic_town");
    if(c.diagnostic_town) {
        const auto& town=j.at("development").at("diagnostic_town");
        if(!town.is_object() || !c.recovered_movement || c.mock_login ||
           !asio::ip::make_address(c.host).is_loopback() ||
           (c.database.filename()!="town-diagnostic-accounts.db" &&
            !(c.diagnostic_knowledge_menu && c.database.filename()=="knowledge-menu-diagnostic.db")))
            throw std::runtime_error("Town diagnostic requires isolated loopback movement and town-diagnostic-accounts.db");
        const auto bounded=[&](const char* key,int maximum) {
            const auto& v=town.at(key);
            if(!v.is_number_integer() || v<0 || v>maximum)
                throw std::runtime_error("Invalid town diagnostic coordinate");
            return v.get<int>();
        };
        c.diagnostic_town_center_x=bounded("center_x",8);
        c.diagnostic_town_center_y=bounded("center_y",8);
        c.diagnostic_town_x=static_cast<std::uint16_t>(bounded("x",188));
        c.diagnostic_town_y=static_cast<std::uint16_t>(bounded("y",188));
        c.diagnostic_town_source_consensus=town.value("source_consensus",false);
        if(town.contains("island_navigation")) {
            if(!c.diagnostic_town_source_consensus || !town.at("island_navigation").is_string())
                throw std::runtime_error("Island navigation requires isolated town source consensus");
            const auto navigation=town.at("island_navigation").get<std::string>();
            if(navigation.empty()) throw std::runtime_error("Island navigation path is empty");
            c.diagnostic_town_island_navigation=resolve(navigation);
        }
        c.diagnostic_town_spawn_guides=town.value("spawn_guides",false);
        c.native_npc_placements_only=town.value("native_npc_placements_only",false);
        c.diagnostic_town_chat_welcome=town.value("chat_welcome",false);
        if(c.diagnostic_town_chat_welcome && !c.diagnostic_town_spawn_guides)
            throw std::runtime_error("Town chat welcome requires first world tick route");
        c.diagnostic_town_quest_progress=town.value("quest_progress",false);
        c.diagnostic_town_map_probe=town.value("map_probe",false);
        c.diagnostic_town_scene_probe=town.value("scene_probe",false);
        c.diagnostic_town_scene_relocate=town.value("scene_relocate",false);
        c.diagnostic_town_scene_indoor_probe=town.value("scene_indoor_probe",false);
        c.diagnostic_town_scene_indoor_transfer=town.value("scene_indoor_transfer",false);
        c.diagnostic_town_scene_return_probe=town.value("scene_return_probe",false);
        c.diagnostic_town_scene_return_commit=town.value("scene_return_commit",false);
        c.diagnostic_town_door_routes=town.value("door_routes",false);
        c.diagnostic_town_all_door_routes=town.value("all_door_routes",false);
        const auto indoor_scenes=town.value("indoor_scenes",std::string{});
        if(!indoor_scenes.empty()) c.diagnostic_town_indoor_scenes=resolve(indoor_scenes);
        c.diagnostic_kunlun_door_routes=town.value("kunlun_door_routes",false);
        c.diagnostic_kunlun_parent_routes=town.value("kunlun_parent_routes",false);
        const auto kunlun_parent=town.value("kunlun_parent_navigation",std::string{});
        if(!kunlun_parent.empty())c.diagnostic_kunlun_parent_navigation=resolve(kunlun_parent);
        if(c.diagnostic_kunlun_parent_routes && (!c.diagnostic_town_door_routes ||
           !c.diagnostic_town_source_consensus || c.diagnostic_kunlun_parent_navigation.empty()))
            throw std::runtime_error("Kunlun parent requires door routes, consensus and parent navigation");
        const auto kunlun_scenes=town.value("kunlun_indoor_scenes",std::string{});
        if(!kunlun_scenes.empty()) c.diagnostic_kunlun_indoor_scenes=resolve(kunlun_scenes);
        if(c.diagnostic_kunlun_door_routes && (!c.diagnostic_town_door_routes ||
           !c.diagnostic_town_source_consensus || c.diagnostic_kunlun_indoor_scenes.empty()))
            throw std::runtime_error("Kunlun doors require door routes, consensus and an indoor scene bundle");
        if(c.diagnostic_town_all_door_routes && (!c.diagnostic_town_door_routes ||
           !c.diagnostic_town_source_consensus || c.diagnostic_town_indoor_scenes.empty()))
            throw std::runtime_error("All town doors require door routes, consensus and an indoor scene bundle");
        c.diagnostic_town_island_routes=town.value("island_routes",false);
        c.diagnostic_town_player_visibility=town.value("player_visibility",false);
        if(c.diagnostic_town_island_routes &&
           (!c.diagnostic_town_door_routes || c.diagnostic_town_island_navigation.empty()))
            throw std::runtime_error("Island routes require doors/navigation");
        if(town.contains("diagnostic_cross_map_navigation")) {
            const auto& path=town.at("diagnostic_cross_map_navigation");
            if(!path.is_string() || path.get_ref<const std::string&>().empty() ||
               !c.diagnostic_town_island_routes || !c.diagnostic_town_source_consensus)
                throw std::runtime_error("Cross-map navigation requires Island routes, consensus and a nonempty bundle path");
            c.diagnostic_cross_map_navigation=resolve(path.get<std::string>());
        }
        c.diagnostic_town_battle_after_quest=town.value("battle_after_quest",false);
        c.diagnostic_town_return_after_battle=town.value("return_after_battle",false);
        c.diagnostic_town_door_after_battle=town.value("door_after_battle",false);
        if(c.diagnostic_town_player_visibility) {
            if(!c.recovered_dual_connection || !c.recovered_account_auth || !c.diagnostic_town_door_routes ||
               !c.diagnostic_town_source_consensus || !c.diagnostic_town_spawn_guides ||
               c.diagnostic_player_visibility || c.diagnostic_remote_actor ||
               c.diagnostic_town_scene_probe || c.diagnostic_town_scene_indoor_transfer ||
               c.diagnostic_town_scene_return_probe)
                throw std::runtime_error("Town player visibility requires isolated authenticated door/guide route");
            const auto language=j.at("development").at("diagnostic_remote_actor_language");
            if(!language.is_number_integer() || language<0 || language>1)
                throw std::runtime_error("Town player visibility requires explicit language bit0..1");
            c.diagnostic_remote_actor_language=language.get<unsigned>();
        }
        if(c.diagnostic_town_door_routes) {
            if(!c.diagnostic_town_source_consensus || !c.diagnostic_town_spawn_guides ||
               (c.diagnostic_town_scene_probe && !c.diagnostic_town_door_after_battle) ||
               (c.diagnostic_town_scene_indoor_transfer && !c.diagnostic_town_door_after_battle) ||
               c.diagnostic_town_scene_return_probe)
                throw std::runtime_error("Door routes require isolated consensus/guide mode without competing scene-transfer probes");
            const auto navigation=town.at("indoor_navigation").get<std::string>();
            if(navigation.empty()) throw std::runtime_error("Door routes require indoor navigation");
            c.diagnostic_town_indoor_navigation=resolve(navigation);
        }
        if(c.diagnostic_town_scene_return_commit && !c.diagnostic_town_scene_return_probe)
            throw std::runtime_error("Durable return requires isolated return probe");
        if(c.diagnostic_town_scene_return_probe && !c.diagnostic_town_scene_indoor_transfer)
            throw std::runtime_error("Return probe requires isolated dual-map restore mode");
        if(c.diagnostic_town_scene_indoor_transfer) {
            if(!c.diagnostic_town_scene_indoor_probe || !c.diagnostic_town_source_consensus)
                throw std::runtime_error("Durable indoor transfer requires isolated indoor probe and source consensus");
            const auto navigation=town.at("indoor_navigation").get<std::string>();
            if(navigation.empty()) throw std::runtime_error("Durable indoor transfer requires indoor navigation");
            c.diagnostic_town_indoor_navigation=resolve(navigation);
        }
        if(c.diagnostic_town_scene_indoor_probe && (!c.diagnostic_town_scene_probe || c.diagnostic_town_scene_relocate))
            throw std::runtime_error("Indoor scene probe requires scene probe without relocation");
        if(c.diagnostic_town_scene_relocate && !c.diagnostic_town_scene_probe)
            throw std::runtime_error("Town relocation requires isolated scene probe");
        if(c.diagnostic_town_scene_probe && !c.diagnostic_town_map_probe)
            throw std::runtime_error("Town scene probe requires isolated map probe");
        if(c.diagnostic_town_map_probe && !c.diagnostic_town_quest_progress)
            throw std::runtime_error("Town map probe requires isolated quest progress");
        if(c.diagnostic_town_quest_progress && !c.diagnostic_town_spawn_guides)
            throw std::runtime_error("Town quest progress requires isolated guide spawn");
        if(c.diagnostic_battle_transition && !c.diagnostic_town_battle_after_quest)
            throw std::runtime_error("Town diagnostic cannot reuse indoor battle transitions without explicit quest gate");
        if(c.diagnostic_town_battle_after_quest &&
           (!c.diagnostic_battle_transition ||
            !(c.diagnostic_town_scene_indoor_transfer || c.diagnostic_town_door_routes) ||
            !c.diagnostic_town_quest_progress ||
            (c.diagnostic_town_scene_return_probe && !c.diagnostic_town_return_after_battle) ||
            (c.diagnostic_town_door_routes && !c.diagnostic_town_door_after_battle)))
            throw std::runtime_error("Town battle requires one isolated completed-quest indoor encounter");
        if(c.diagnostic_town_return_after_battle &&
           (!c.diagnostic_town_battle_after_quest || !c.diagnostic_town_scene_return_probe ||
            !c.diagnostic_town_scene_return_commit || c.diagnostic_town_door_routes))
            throw std::runtime_error("Post-battle return requires isolated battle and durable map return");
        if(c.diagnostic_town_door_after_battle &&
           (!c.diagnostic_town_battle_after_quest || !c.diagnostic_town_door_routes ||
            !c.diagnostic_town_map_probe || c.diagnostic_town_return_after_battle ||
            c.diagnostic_town_scene_return_probe))
            throw std::runtime_error("Post-battle door requires isolated battle and indoor doorway route");
    }
    c.diagnostic_battle_after_movement=j.at("development").value("diagnostic_battle_after_movement",false);
    const auto encounter_limit=j.at("development").value("diagnostic_encounter_limit",nlohmann::json(1));
    if(!encounter_limit.is_number_integer() || encounter_limit<1 || encounter_limit>2)
        throw std::runtime_error("Diagnostic encounter limit must be integer1..2");
    c.diagnostic_encounter_limit=encounter_limit.get<unsigned>();
    c.diagnostic_battle_participants=j.at("development").value("diagnostic_battle_participants",false);
    c.diagnostic_battle_player_appearance=j.at("development").value("diagnostic_battle_player_appearance",false);
    c.diagnostic_battle_animations=j.at("development").value("diagnostic_battle_animations",false);
    c.diagnostic_battle_skill_seed=j.at("development").value("diagnostic_battle_skill_seed",false);
    c.diagnostic_shunying_manual=j.at("development").value("diagnostic_shunying_manual",false);
    c.diagnostic_thousand_bulls_manual=j.at("development").value("diagnostic_thousand_bulls_manual",false);
    c.diagnostic_recording_fixed_damage=j.at("development").value("diagnostic_recording_fixed_damage",false);
    c.diagnostic_shunying_character_id=j.at("development").value("diagnostic_shunying_character_id",std::uint64_t{0});
    c.diagnostic_battle_revival=j.at("development").value("diagnostic_battle_revival",false);
    c.diagnostic_battle_skill_settlement=j.at("development").value("diagnostic_battle_skill_settlement",false);
    const auto skill_kind=j.at("development").value("diagnostic_battle_skill_kind",nlohmann::json(0));
    if(!skill_kind.is_number_integer() || skill_kind<0 || skill_kind>1)
        throw std::runtime_error("Diagnostic skill family must be0 or1");
    c.diagnostic_battle_skill_kind=skill_kind.get<unsigned>();
    if(c.diagnostic_battle_skill_kind && (!c.diagnostic_battle_skill_seed ||
        !c.diagnostic_battle_skill_settlement || c.diagnostic_battle_revival ||
        !asio::ip::make_address(c.host).is_loopback() ||
        c.database.parent_path().filename().string().rfind("private-skill-family-",0)!=0))
        throw std::runtime_error("Skill family probe requires named isolated own-server fixture");
    if(c.diagnostic_battle_skill_seed && !c.diagnostic_battle_player_appearance)
        throw std::runtime_error("Skill seed diagnostic requires isolated player appearance");
    if(c.diagnostic_battle_animations && !c.diagnostic_battle_player_appearance)
        throw std::runtime_error("Animation diagnostic requires isolated player appearance");
    if(c.diagnostic_battle_player_appearance && !c.diagnostic_battle_participants)
        throw std::runtime_error("Player appearance diagnostic requires isolated participants");
    const auto rounds=j.at("development").value("diagnostic_battle_rounds",nlohmann::json(1));
    if(!rounds.is_number_integer() || rounds<1 || rounds>3 ||
       (rounds!=1 && !c.diagnostic_battle_participants))
        throw std::runtime_error("Diagnostic round count must be 1..3 and requires participants");
    c.diagnostic_battle_rounds=rounds.get<unsigned>();
    c.diagnostic_battle_terminal=j.at("development").value("diagnostic_battle_terminal",false);
    if(rounds==3 && (!c.diagnostic_battle_terminal || !c.diagnostic_battle_skill_settlement || !c.diagnostic_battle_animations))
        throw std::runtime_error("Three rounds require animated terminal skill diagnostic");
    c.diagnostic_battle_mp_refusal=j.at("development").value("diagnostic_battle_mp_refusal",false);
    c.diagnostic_battle_resources=j.at("development").value("diagnostic_battle_resources",false);
    const auto experience=j.at("development").value("diagnostic_battle_experience",nlohmann::json(0));
    if(!experience.is_number_integer() || experience<0 || experience>2147483647 ||
       (experience!=0 && (!c.diagnostic_battle_resources || !c.diagnostic_battle_terminal)))
        throw std::runtime_error("Diagnostic experience requires persisted terminal battle and signed display range");
    c.diagnostic_battle_experience=experience.get<std::uint64_t>();
    c.diagnostic_role_progress=j.at("development").value("diagnostic_role_progress",false);
    if(c.diagnostic_role_progress && (!c.diagnostic_battle_resources || !c.diagnostic_battle_terminal || experience==0))
        throw std::runtime_error("Role progress probe requires persisted nonzero diagnostic award");
    const auto span=j.at("development").value("diagnostic_progress_span",nlohmann::json(0));
    c.diagnostic_level_snapshot=j.at("development").value("diagnostic_level_snapshot",false);
    c.diagnostic_character_growth=j.at("development").value("diagnostic_character_growth",false);
    if(c.diagnostic_character_growth && !c.diagnostic_level_snapshot)
        throw std::runtime_error("Character growth probe requires isolated persisted level snapshot");
    if(!span.is_number_integer() || span<0 || span>2147483647 ||
       (span!=0 && (!c.diagnostic_role_progress || (!c.diagnostic_level_snapshot && experience>=span))))
        throw std::runtime_error("Diagnostic progress span requires unlevelled role progress experiment");
    if(c.diagnostic_level_snapshot && (!c.diagnostic_role_progress || span==0 || !c.diagnostic_battle_player_appearance))
        throw std::runtime_error("Level snapshot requires explicit isolated player progress experiment");
    c.diagnostic_progress_span=span.get<std::uint32_t>();
    c.diagnostic_resume_checkpoint=j.at("development").value("diagnostic_resume_checkpoint",false);
    if(c.diagnostic_resume_checkpoint && !c.diagnostic_battle_revival && (!c.diagnostic_level_snapshot || c.diagnostic_battle_rounds!=3 ||
        !c.diagnostic_battle_animations || !c.diagnostic_battle_skill_settlement || span!=200 || experience!=250))
        throw std::runtime_error("Checkpoint resume requires the qualified first-exchange diagnostic policy");
    if(c.diagnostic_resume_checkpoint && c.diagnostic_battle_revival &&
       (!c.diagnostic_battle_resources || c.diagnostic_battle_rounds>2))
        throw std::runtime_error("Revival resume requires isolated durable one or two-round projection");
    c.diagnostic_world_resources=j.at("development").value("diagnostic_world_resources",false);
    c.diagnostic_quest_dialogue=j.at("development").value("diagnostic_quest_dialogue",false);
    c.diagnostic_knowledge_menu=j.at("development").value("diagnostic_knowledge_menu",false);
    if(c.diagnostic_knowledge_menu && (!c.recovered_world_entry || !c.recovered_movement || c.mock_login ||
       c.diagnostic_quest_dialogue || !asio::ip::make_address(c.host).is_loopback() ||
       c.database.filename()!="knowledge-menu-diagnostic.db"))
        throw std::runtime_error("Knowledge menu requires isolated native world and no competing dialogue");
    c.diagnostic_quest_npc=j.at("development").value("diagnostic_quest_npc",false);
    if(c.diagnostic_quest_npc && !c.diagnostic_quest_dialogue)
        throw std::runtime_error("NPC diagnostic requires isolated quest dialogue");
    if(c.diagnostic_quest_dialogue && (!c.recovered_world_entry || !c.recovered_movement || c.mock_login ||
       !asio::ip::make_address(c.host).is_loopback() || c.database.filename()!="diagnostic-accounts.db" ||
       c.diagnostic_battle_transition || c.diagnostic_world_resources))
        throw std::runtime_error("Quest dialogue requires standalone isolated loopback world diagnostic");
    const bool isolated_world_resource_database=c.database.filename()=="diagnostic-accounts.db" ||
        (c.database.filename()=="town-diagnostic-accounts.db" && c.diagnostic_town_battle_after_quest);
    if(c.diagnostic_world_resources && (!c.recovered_movement || c.mock_login ||
        !asio::ip::make_address(c.host).is_loopback() || !isolated_world_resource_database))
        throw std::runtime_error("World resources require recovered movement and isolated diagnostic database");
    c.diagnostic_world_supply=j.at("development").value("diagnostic_world_supply",false);
    // CUSTOM-0014/CUSTOM-0016: isolated same-session battle/supply probe.
    // Saved resources, rather than the separate level/EXP fixture, feed fight two.
    const bool two_battle_supply=c.diagnostic_encounter_limit==2 && c.diagnostic_world_supply &&
        c.diagnostic_world_resources && c.diagnostic_battle_after_movement &&
        c.diagnostic_battle_resources && c.diagnostic_battle_terminal &&
        c.diagnostic_battle_rounds==3 && !c.diagnostic_level_snapshot &&
        !c.diagnostic_role_progress && c.diagnostic_progress_span==0 &&
        c.diagnostic_battle_experience==0 && !c.diagnostic_resume_checkpoint;
    if(c.diagnostic_world_supply && (!c.diagnostic_world_resources ||
       (c.diagnostic_battle_transition && (!c.diagnostic_battle_resources || !c.diagnostic_battle_terminal ||
        c.diagnostic_battle_rounds!=3 ||
        (c.diagnostic_encounter_limit!=1 && !two_battle_supply) || c.diagnostic_level_snapshot ||
        c.diagnostic_resume_checkpoint))))
        throw std::runtime_error("World supply requires isolated resources and qualified settled three-round battle");
    if(c.diagnostic_battle_resources && !c.diagnostic_battle_skill_settlement && !c.diagnostic_battle_revival && !c.diagnostic_visibility_battle)
        throw std::runtime_error("Resource persistence diagnostic requires isolated skill settlement");
    if(c.diagnostic_battle_revival && (!c.diagnostic_battle_skill_seed || !c.diagnostic_battle_animations ||
       c.diagnostic_battle_skill_settlement || c.diagnostic_world_resources ||
       c.diagnostic_battle_mp_refusal ||
       (c.diagnostic_battle_terminal && (!c.diagnostic_resume_checkpoint || !c.diagnostic_battle_resources || c.diagnostic_battle_rounds!=1 || c.diagnostic_battle_experience)) ||
       c.diagnostic_battle_rounds>2 ||
       c.diagnostic_encounter_limit!=1 || c.diagnostic_battle_after_movement))
        throw std::runtime_error("Revival requires isolated animated single-action seed without world resources or retaliation policy");
    if(c.diagnostic_battle_mp_refusal && (!c.diagnostic_battle_skill_settlement ||
       !c.diagnostic_battle_animations || c.diagnostic_battle_terminal || c.diagnostic_battle_rounds!=1))
        throw std::runtime_error("MP refusal diagnostic requires animated single skill round without terminal mode");
    if(c.diagnostic_battle_skill_settlement && (!c.diagnostic_battle_skill_seed ||
       ((c.diagnostic_battle_terminal || c.diagnostic_battle_rounds>1) && !c.diagnostic_battle_animations)))
        throw std::runtime_error("Skill settlement requires isolated skill seed and animations for repeated or terminal rounds");
    if(c.diagnostic_battle_terminal && (!c.diagnostic_battle_participants ||
       (c.diagnostic_battle_rounds!=1 && c.diagnostic_battle_rounds!=3)))
        throw std::runtime_error("Terminal diagnostic requires participants and one or three rounds");
    if(c.diagnostic_battle_participants && !c.diagnostic_battle_transition)
        throw std::runtime_error("Diagnostic participants require isolated battle transition");
    if(c.diagnostic_encounter_limit>1 &&
       !((c.diagnostic_battle_after_movement && c.diagnostic_level_snapshot &&
          c.diagnostic_battle_terminal && c.diagnostic_battle_rounds==3 &&
          c.diagnostic_battle_experience==250 && c.diagnostic_progress_span==200 &&
          !c.diagnostic_world_supply) || two_battle_supply))
        throw std::runtime_error("Two encounters require qualified movement/level or supply diagnostic fixture");
    if(c.diagnostic_battle_after_movement && (!c.diagnostic_battle_transition ||
       !c.diagnostic_battle_participants || c.diagnostic_resume_checkpoint))
        throw std::runtime_error("Movement encounter probe requires fresh isolated participant transition");
    if(c.diagnostic_visibility_battle && (!c.diagnostic_battle_transition ||
       !c.diagnostic_battle_participants || !c.diagnostic_battle_player_appearance ||
       !c.diagnostic_battle_animations || !c.diagnostic_battle_terminal ||
       c.diagnostic_battle_rounds!=(c.diagnostic_visibility_skill_recovery ? 3u : 1u)))
        throw std::runtime_error("Visibility battle requires qualified animated terminal player fixture and round count");
    if(c.diagnostic_visibility_skill_recovery && (!c.diagnostic_visibility_checkpoint ||
       !c.diagnostic_battle_skill_seed || !c.diagnostic_battle_skill_settlement || c.diagnostic_battle_rounds!=3))
        throw std::runtime_error("Visibility skill recovery requires checkpointed three-round skill fixture");
    if(c.diagnostic_visibility_checkpoint && (!c.diagnostic_visibility_battle || !c.diagnostic_battle_resources))
        throw std::runtime_error("Visibility checkpoint requires durable isolated visibility battle");
    if(c.diagnostic_battle_transition && (!c.recovered_movement || c.mock_login ||
        !asio::ip::make_address(c.host).is_loopback() ||
        c.database.filename()!=(c.diagnostic_visibility_battle ? "player-visibility-diagnostic.db" :
                                  c.diagnostic_town_battle_after_quest ? "town-diagnostic-accounts.db" : "diagnostic-accounts.db")))
        throw std::runtime_error("Battle transition diagnostic requires recovered movement and isolated diagnostic database");
    if(c.diagnostic_recording_fixed_damage && !c.diagnostic_thousand_bulls_manual)
        throw std::runtime_error("Recording damage requires isolated ThousandBulls manual mode");
    if(c.diagnostic_thousand_bulls_manual && !c.diagnostic_shunying_manual)
        throw std::runtime_error("ThousandBulls manual trial requires existing isolated Shunying fixture");
    if(c.diagnostic_shunying_manual &&
       (!c.diagnostic_shunying_character_id || c.diagnostic_shunying_character_id>0x3fff ||
        !c.diagnostic_battle_transition || !c.diagnostic_battle_participants ||
        !c.diagnostic_battle_player_appearance || !c.diagnostic_battle_animations ||
        !c.diagnostic_battle_skill_seed || !c.diagnostic_battle_skill_settlement ||
        c.diagnostic_battle_skill_kind || c.diagnostic_battle_terminal ||
        c.diagnostic_battle_resources || c.diagnostic_world_resources ||
        c.diagnostic_battle_revival || c.diagnostic_resume_checkpoint ||
        c.diagnostic_level_snapshot || c.diagnostic_role_progress ||
        c.diagnostic_battle_rounds!=1 || c.diagnostic_battle_mp_refusal ||
        c.diagnostic_visibility_battle || c.diagnostic_town_battle_after_quest ||
        c.native_monster_placements_only || c.diagnostic_battle_after_movement ||
        c.diagnostic_encounter_limit!=1 ||
        !asio::ip::make_address(c.host).is_loopback() ||
        c.database.filename()!="diagnostic-accounts.db" ||
        c.database.parent_path().filename().string().rfind("private-shunying-manual-",0)!=0))
        throw std::runtime_error("Shunying manual trial requires named isolated loopback nonpersistent battle");
    if(c.diagnostic_town_battle_after_quest &&
       (!c.diagnostic_battle_participants || !c.diagnostic_battle_player_appearance ||
        !c.diagnostic_battle_animations || !c.diagnostic_battle_skill_seed ||
        !c.diagnostic_battle_skill_settlement || !c.diagnostic_battle_terminal ||
        !c.diagnostic_battle_resources || c.diagnostic_battle_rounds!=1 ||
        c.diagnostic_encounter_limit!=1 || c.diagnostic_battle_experience ||
        c.diagnostic_role_progress || c.diagnostic_resume_checkpoint))
        throw std::runtime_error("Town battle requires isolated one-round durable skill fixture without XP or resume");
    if(c.recovered_account_auth && (c.protocol_mode!=ProtocolMode::God2LegacyCharacterListCandidate || c.mock_login))
        throw std::runtime_error("Recovered account authentication requires non-mock legacy candidate mode");
    if(c.local_account_registration && !c.recovered_account_auth)
        throw std::runtime_error("Local account registration requires recovered account authentication");
    if(c.recovered_character_creation && !c.recovered_account_auth)
        throw std::runtime_error("Recovered character creation requires recovered account authentication");
    if(j.contains("world") && j.at("world").contains("new_character_birthplace")) {
        const auto& birth=j.at("world").at("new_character_birthplace");
        if(!birth.is_object() || !c.diagnostic_town || !c.diagnostic_town_source_consensus ||
           birth.at("area")!=4 || birth.at("scene")!=3 || birth.at("kind")!=0)
            throw std::runtime_error("New birthplace requires qualified Kunlun map4/3 kind0");
        for(const auto* key:{"x","y"})if(!birth.at(key).is_number_integer() || birth.at(key)<0 || birth.at(key)>251)
            throw std::runtime_error("Invalid Kunlun birthplace coordinate");
        c.character_birthplace_x=birth.at("x").get<std::uint16_t>();c.character_birthplace_y=birth.at("y").get<std::uint16_t>();
        const auto navigation=birth.at("navigation").get<std::string>();
        if(navigation.empty())throw std::runtime_error("Kunlun birthplace navigation missing");
        c.character_birthplace_navigation=resolve(navigation);
    }
    if((c.diagnostic_kunlun_door_routes || c.diagnostic_kunlun_parent_routes) && c.character_birthplace_navigation.empty())
        throw std::runtime_error("Kunlun doors require qualified birthplace navigation");
    if(j.contains("world") && j.at("world").contains("clock")) {
        const auto& clock=j.at("world").at("clock");
        if(!clock.is_object() || !clock.at("enabled").is_boolean())throw std::runtime_error("World clock configuration required");
        c.world_clock_enabled=clock.at("enabled").get<bool>();
        if(clock.contains("sync_seconds")) {
            const auto& interval=clock.at("sync_seconds");
            if(!interval.is_number_integer() || interval<5 || interval>300)throw std::runtime_error("World clock interval outside bounds");
            c.world_clock_sync_seconds=interval.get<unsigned>();
        }
        if(c.world_clock_enabled && !c.recovered_world_entry)throw std::runtime_error("World clock requires native world entry");
    }
    // CUSTOM-0078: formal admission is independent of disposable lab environments.
    // Battle/transfer invalidation belongs to Application; preserve existing options.
    if(j.contains("world") && j.at("world").contains("owned_guild_membership")) {
        const auto& guild=j.at("world").at("owned_guild_membership");
        if(!guild.is_object() || !guild.contains("enabled") || !guild.at("enabled").is_boolean())
            throw std::runtime_error("Owned guild membership bool required");
        c.owned_guild_membership_enabled=guild.at("enabled").get<bool>();
        if(guild.contains("entry_resource_bundle")) {
            if(!guild.at("entry_resource_bundle").is_string())
                throw std::runtime_error("Owned guild entry resource bundle string required");
            c.owned_guild_entry_resource_bundle=guild.at("entry_resource_bundle").get<std::string>();
        }
        if(c.owned_guild_membership_enabled && (!c.recovered_account_auth || !c.recovered_world_entry ||
           !c.recovered_dual_connection || !c.recovered_movement || c.mock_login))
            throw std::runtime_error("Owned guild membership requires authenticated native world, dual connection and movement");
        if(c.owned_guild_membership_enabled && c.owned_guild_entry_resource_bundle!="CUSTOM-0078-2996-v1")
            throw std::runtime_error("Owned guild membership requires qualified CUSTOM-0078-2996-v1 resources");
    }
    if(j.contains("world") && j.at("world").contains("owned_guild_announcements")) {
        const auto& notice=j.at("world").at("owned_guild_announcements");
        if(!notice.is_object() || !notice.contains("enabled") || !notice.at("enabled").is_boolean())
            throw std::runtime_error("Owned guild announcement bool required");
        c.owned_guild_announcements_enabled=notice.at("enabled").get<bool>();
        if(c.owned_guild_announcements_enabled && !c.owned_guild_membership_enabled)
            throw std::runtime_error("Owned guild announcements require configured authenticated membership");
    }
    if(j.contains("world") && j.at("world").contains("owned_guild_officers")) {
        const auto& officers=j.at("world").at("owned_guild_officers");
        if(!officers.is_object() || !officers.contains("enabled") || !officers.at("enabled").is_boolean())
            throw std::runtime_error("Owned guild officers bool required");
        c.owned_guild_officers_enabled=officers.at("enabled").get<bool>();
        if(c.owned_guild_officers_enabled && (!c.owned_guild_membership_enabled || !c.owned_guild_announcements_enabled))
            throw std::runtime_error("Owned guild officers require configured authenticated membership and announcements");
    }
    if(j.contains("world") && j.at("world").contains("owned_guild_succession")) {
        const auto& succession=j.at("world").at("owned_guild_succession");
        if(!succession.is_object() || !succession.contains("enabled") || !succession.at("enabled").is_boolean())
            throw std::runtime_error("Owned guild succession bool required");
        c.owned_guild_succession_enabled=succession.at("enabled").get<bool>();
        if(c.owned_guild_succession_enabled && (!c.owned_guild_membership_enabled || !c.owned_guild_announcements_enabled || !c.owned_guild_officers_enabled))
            throw std::runtime_error("CUSTOM0083 succession requires authenticated membership, announcements and officers");
    }
    if(j.contains("world") && j.at("world").contains("owned_guild_relations53")) {
        const auto& value=j.at("world").at("owned_guild_relations53");
        if(!value.is_object()||!value.contains("enabled")||!value.at("enabled").is_boolean())throw std::runtime_error("PRIVATE CUSTOM84 explicit bool required");
        c.owned_guild_relations53_enabled=value.at("enabled").get<bool>();
        if(c.owned_guild_relations53_enabled && !c.owned_guild_succession_enabled)
            throw std::runtime_error("Guild relations53 requires guild succession52");
    }
    if(j.contains("world") && j.at("world").contains("owned_map_views")) {
        const auto& maps=j.at("world").at("owned_map_views");
        if(!maps.is_object() || !maps.at("enabled").is_boolean())throw std::runtime_error("Map view bool required");
        c.owned_map_views_enabled=maps.at("enabled").get<bool>();
        if(c.owned_map_views_enabled && (!c.recovered_world_entry || !c.recovered_movement || c.mock_login))
            throw std::runtime_error("Owned map view requires authenticated native world and movement");
    }
    if(j.contains("world") && j.at("world").contains("owned_attribute_allocation")) {
        const auto& allocation=j.at("world").at("owned_attribute_allocation");
        if(!allocation.is_object() || !allocation.at("enabled").is_boolean())throw std::runtime_error("Owned allocation bool required");
        c.owned_attribute_allocation_enabled=allocation.at("enabled").get<bool>();
        if(c.owned_attribute_allocation_enabled && (!c.recovered_world_entry || !c.recovered_movement || !c.recovered_account_auth || c.mock_login))
            throw std::runtime_error("Owned allocation requires authenticated native world and movement");
    }
    if(j.contains("world") && j.at("world").contains("owned_weapon_transfers")) {
        const auto& weapons=j.at("world").at("owned_weapon_transfers");
        if(!weapons.is_object() || !weapons.at("enabled").is_boolean())throw std::runtime_error("Owned weapon transfer bool required");
        c.owned_weapon_transfers_enabled=weapons.at("enabled").get<bool>();
        if(c.owned_weapon_transfers_enabled && (!c.recovered_world_entry || !c.recovered_movement || !c.recovered_account_auth || c.mock_login))
            throw std::runtime_error("Owned weapon transfers require authenticated native world and movement");
    }
    if(j.contains("world") && j.at("world").contains("owned_armor_transfers")) {
        const auto& armor=j.at("world").at("owned_armor_transfers");
        if(!armor.is_object() || !armor.at("enabled").is_boolean())throw std::runtime_error("Owned armor transfer bool required");
        c.owned_armor_transfers_enabled=armor.at("enabled").get<bool>();
        if(c.owned_armor_transfers_enabled && (!c.recovered_world_entry || !c.recovered_movement || !c.recovered_account_auth || c.mock_login))
            throw std::runtime_error("Owned armor transfers require authenticated native world and movement");
    }
    if(j.contains("world") && j.at("world").contains("owned_armor_bank")) {
        const auto& bank=j.at("world").at("owned_armor_bank");
        if(!bank.is_object() || !bank.at("enabled").is_boolean())throw std::runtime_error("Owned armor bank bool required");
        c.owned_armor_bank_enabled=bank.at("enabled").get<bool>();
        if(c.owned_armor_bank_enabled && (!c.owned_armor_transfers_enabled || !c.recovered_world_entry ||
           !c.recovered_movement || !c.recovered_account_auth || c.mock_login))
            throw std::runtime_error("Owned armor bank requires authenticated native world and owned armor transport");
    }
    if(j.contains("world") && j.at("world").contains("owned_foreign_bank")) {
        const auto& bank=j.at("world").at("owned_foreign_bank");
        if(!bank.is_object() || !bank.at("enabled").is_boolean())throw std::runtime_error("Owned foreign bank bool required");
        c.owned_foreign_bank_enabled=bank.at("enabled").get<bool>();
        if(c.owned_foreign_bank_enabled && (!c.owned_armor_bank_enabled || !c.owned_armor_transfers_enabled ||
           !c.recovered_world_entry || !c.recovered_movement || !c.recovered_account_auth || c.mock_login))
            throw std::runtime_error("Owned foreign bank requires authenticated native world and owned armor bank");
    }
    if(j.contains("world") && j.at("world").contains("owned_mixed_bank")) {
        const auto& bank=j.at("world").at("owned_mixed_bank");
        if(!bank.is_object() || !bank.at("enabled").is_boolean())throw std::runtime_error("Owned mixed bank bool required");
        c.owned_mixed_bank_enabled=bank.at("enabled").get<bool>();
        if(c.owned_mixed_bank_enabled && (!c.owned_foreign_bank_enabled || !c.owned_armor_bank_enabled ||
           !c.owned_armor_transfers_enabled || !c.recovered_world_entry || !c.recovered_movement ||
           !c.recovered_account_auth || c.mock_login))
            throw std::runtime_error("Owned mixed bank requires authenticated native world and owned foreign bank");
    }
    if(j.contains("world") && j.at("world").contains("owned_instance_discard")) {
        const auto& discard=j.at("world").at("owned_instance_discard");
        if(!discard.is_object() || !discard.at("enabled").is_boolean())throw std::runtime_error("Owned instance discard bool required");
        c.owned_instance_discard_enabled=discard.at("enabled").get<bool>();
        if(c.owned_instance_discard_enabled && (!c.owned_armor_transfers_enabled ||
           !c.recovered_world_entry || !c.recovered_movement || !c.recovered_account_auth || c.mock_login))
            throw std::runtime_error("Owned instance discard requires authenticated native world and complete owned bag projection");
    }
    if(j.contains("world") && j.at("world").contains("owned_instance_trade")) {
        const auto& trade=j.at("world").at("owned_instance_trade");
        if(!trade.is_object() || !trade.at("enabled").is_boolean())throw std::runtime_error("Owned instance trade bool required");
        c.owned_instance_trade_enabled=trade.at("enabled").get<bool>();
        if(c.owned_instance_trade_enabled && (!c.owned_armor_transfers_enabled || !c.recovered_world_entry ||
           !c.recovered_movement || !c.recovered_account_auth || c.mock_login))
            throw std::runtime_error("Owned instance trade requires authenticated native world and owned armor transport");
    }
    if(j.contains("world") && j.at("world").contains("owned_teleport_gem")) {
        const auto& gem=j.at("world").at("owned_teleport_gem");
        if(!gem.is_object() || !gem.at("enabled").is_boolean())throw std::runtime_error("Owned teleport gem bool required");
        c.owned_teleport_gem_enabled=gem.at("enabled").get<bool>();
        if(c.owned_teleport_gem_enabled && (!c.recovered_world_entry || !c.recovered_movement ||
           !c.recovered_account_auth || c.mock_login || !c.diagnostic_town_door_routes ||
           !c.diagnostic_town_island_routes || !c.diagnostic_town_source_consensus))
            throw std::runtime_error("Owned teleport gem requires authenticated source-qualified island routes");
    }
    if(j.contains("world") && j.at("world").contains("owned_daily_quest_views")) {
        const auto& daily=j.at("world").at("owned_daily_quest_views");
        if(!daily.is_object() || !daily.at("enabled").is_boolean())throw std::runtime_error("Owned daily view bool required");
        c.owned_daily_quest_views_enabled=daily.at("enabled").get<bool>();
        if(c.owned_daily_quest_views_enabled && (!c.recovered_world_entry || !c.recovered_movement || !c.recovered_account_auth || c.mock_login))
            throw std::runtime_error("Owned daily views require authenticated native world and movement");
    }
    if(j.contains("world") && j.at("world").contains("owned_supply")) {
        const auto& supply=j.at("world").at("owned_supply");
        if(!supply.is_object() || !supply.at("enabled").is_boolean())throw std::runtime_error("Owned supply bool required");
        c.owned_supply_enabled=supply.at("enabled").get<bool>();
        if(c.owned_supply_enabled && (!c.recovered_world_entry || !c.recovered_movement || !c.recovered_account_auth || c.mock_login || c.diagnostic_world_supply))
            throw std::runtime_error("Owned supply requires authenticated native world and movement without diagnostic supply");
    }
    if(j.contains("world") && j.at("world").contains("owned_skillbook_learning")) {
        const auto& learning=j.at("world").at("owned_skillbook_learning");
        if(!learning.is_object() || !learning.at("enabled").is_boolean())
            throw std::runtime_error("Owned skill-book learning bool required");
        c.owned_skillbook_learning_enabled=learning.at("enabled").get<bool>();
        if(c.owned_skillbook_learning_enabled && (!c.recovered_world_entry || !c.recovered_movement ||
           !c.recovered_account_auth || !c.recovered_dual_connection || c.mock_login))
            throw std::runtime_error("Owned skill-book learning requires authenticated native TW world and movement");
    }
    if(j.contains("world") && j.at("world").contains("owned_initial_player")) {
        const auto& player=j.at("world").at("owned_initial_player");
        if(!player.is_object() || !player.at("enabled").is_boolean())
            throw std::runtime_error("Owned initial player bool required");
        c.owned_initial_player_enabled=player.at("enabled").get<bool>();
        if(c.owned_initial_player_enabled && (!c.owned_skillbook_learning_enabled ||
           c.protocol_mode!=ProtocolMode::God2LegacyCharacterListCandidate ||
           !c.recovered_world_entry || !c.recovered_movement || !c.recovered_account_auth ||
           !c.recovered_dual_connection || c.mock_login))
            throw std::runtime_error("Owned initial player requires owned skill-book learning and authenticated native TW dual-connection world and movement");
    }
    if(j.contains("world") && j.at("world").contains("owned_beast_panel")) {
        const auto& beast=j.at("world").at("owned_beast_panel");
        if(!beast.is_object()||!beast.at("enabled").is_boolean())throw std::runtime_error("Owned beast panel bool required");
        c.owned_beast_panel_enabled=beast.at("enabled").get<bool>();
        if(c.owned_beast_panel_enabled&&(!c.recovered_world_entry||!c.recovered_movement||!c.recovered_account_auth||c.mock_login||c.diagnostic_world_supply))
            throw std::runtime_error("Owned beast panel requires authenticated native world and movement");
    }
    if(j.contains("battle") && j.at("battle").contains("owned_pose")) {
        const auto& feature=j.at("battle").at("owned_pose");
        if(!feature.is_object() || !feature.at("enabled").is_boolean())throw std::runtime_error("Owned battle pose bool required");
        c.owned_battle_pose_enabled=feature.at("enabled").get<bool>();
        if(c.owned_battle_pose_enabled && (!c.recovered_dual_connection || !c.recovered_world_entry ||
           !c.recovered_account_auth || c.mock_login || !c.diagnostic_battle_transition ||
           !c.diagnostic_battle_participants || !c.diagnostic_battle_player_appearance))
            throw std::runtime_error("Owned battle pose requires actual authenticated diagnostic player bootstrap");
    }
    if(j.contains("world") && j.at("world").contains("owned_client_options")) {
        const auto& feature=j.at("world").at("owned_client_options");
        if(!feature.is_object() || !feature.at("enabled").is_boolean())throw std::runtime_error("Owned client options bool required");
        c.owned_client_options_enabled=feature.at("enabled").get<bool>();
        if(c.owned_client_options_enabled && (!c.recovered_dual_connection || !c.recovered_world_entry || !c.recovered_account_auth || c.mock_login))
            throw std::runtime_error("Owned client options requires authenticated native dual-connection world entry");
    }
    if(j.contains("world") && j.at("world").contains("owned_party_directory")) {
        const auto& feature=j.at("world").at("owned_party_directory");
        if(!feature.is_object() || !feature.at("enabled").is_boolean())throw std::runtime_error("Owned party directory bool required");
        c.owned_party_directory_enabled=feature.at("enabled").get<bool>();
        if(c.owned_party_directory_enabled && (!c.recovered_dual_connection || !c.recovered_world_entry || !c.recovered_movement || !c.recovered_account_auth || c.mock_login))
            throw std::runtime_error("Owned party directory requires authenticated dual-connection world and movement");
    }
    if(j.contains("world") && j.at("world").contains("owned_blacklist")) {
        const auto& feature=j.at("world").at("owned_blacklist");
        if(!feature.is_object() || !feature.at("enabled").is_boolean())throw std::runtime_error("Owned blacklist bool required");
        c.owned_blacklist_enabled=feature.at("enabled").get<bool>();
        if(c.owned_blacklist_enabled && (!c.recovered_dual_connection || !c.recovered_world_entry || !c.recovered_movement || !c.recovered_account_auth || c.mock_login))
            throw std::runtime_error("Owned blacklist requires authenticated dual-connection world and movement");
    }
    if(j.contains("world") && j.at("world").contains("owned_pk_invitation")) {
        const auto& pk=j.at("world").at("owned_pk_invitation");
        if(!pk.is_object()||!pk.at("enabled").is_boolean())throw std::runtime_error("Owned PK invitation bool required");
        c.owned_pk_invitation_enabled=pk.at("enabled").get<bool>();
        if(c.owned_pk_invitation_enabled&&(!c.recovered_world_entry||!c.recovered_movement||!c.recovered_account_auth||c.mock_login||c.fixture_battle||c.diagnostic_battle_transition||c.diagnostic_battle_after_movement))
            throw std::runtime_error("Owned PK requires authenticated native world independently of diagnostic combat");
    }
    if(j.contains("world") && j.at("world").contains("owned_pve_rooms")) {
        const auto& feature=j.at("world").at("owned_pve_rooms");
        if(!feature.is_object()||!feature.at("enabled").is_boolean())throw std::runtime_error("Owned PvE rooms bool required");
        c.owned_pve_rooms_enabled=feature.at("enabled").get<bool>();
        if(c.owned_pve_rooms_enabled&&(c.protocol_mode!=ProtocolMode::God2LegacyCharacterListCandidate||
           !c.recovered_character_creation||!c.recovered_dual_connection||!c.recovered_world_entry||!c.recovered_movement||!c.recovered_account_auth||
           c.mock_login||c.fixture_battle||c.diagnostic_battle_participants||c.diagnostic_battle_transition||c.diagnostic_battle_after_movement))
            throw std::runtime_error("Owned PvE requires authenticated normal Taiwan world independently of all diagnostic combat");
    }
    if(j.contains("world") && j.at("world").contains("fruit_village_quests")) {
        const auto& fruit=j.at("world").at("fruit_village_quests");
        if(!fruit.is_object() || !fruit.at("enabled").is_boolean())throw std::runtime_error("Fruit quest bool required");
        c.fruit_village_quests_enabled=fruit.at("enabled").get<bool>();
        if(fruit.contains("allow_inferred_placements") && !fruit.at("allow_inferred_placements").is_boolean())throw std::runtime_error("Fruit placement bool required");
        c.fruit_sourcehint_placements=fruit.value("allow_inferred_placements",false);
        c.fruit_navigation=resolve(fruit.value("navigation",std::string("artifacts/world-atlas/fruit-13-12.json")));
        if(c.fruit_village_quests_enabled && (!c.recovered_account_auth || !c.recovered_world_entry || !c.recovered_movement || c.mock_login || !c.diagnostic_town || !c.diagnostic_town_source_consensus))
            throw std::runtime_error("Fruit quests require authenticated world and source consensus navigation");
    }
    if(j.contains("world") && j.at("world").contains("owned_whole_bag_moves")) {
        const auto& moves=j.at("world").at("owned_whole_bag_moves");
        if(!moves.is_object() || !moves.at("enabled").is_boolean())
            throw std::runtime_error("Whole bag moves bool required");
        c.owned_whole_bag_moves_enabled=moves.at("enabled").get<bool>();
    }
    const auto addr=asio::ip::make_address(c.host);
    if(j.contains("world") && j.at("world").contains("owned_player_appearance")) {
        const auto& appearance=j.at("world").at("owned_player_appearance");
        if(!appearance.is_object() || !appearance.at("enabled").is_boolean())throw std::runtime_error("Owned appearance bool required");
        c.owned_player_appearance_enabled=appearance.at("enabled").get<bool>();
        if(c.owned_player_appearance_enabled && (!c.recovered_account_auth || !c.recovered_world_entry || !c.recovered_movement || c.mock_login))
            throw std::runtime_error("Owned appearance requires authenticated world and movement");
    }
    if(j.at("development").contains("diagnostic_owned_weapon_appearance")) {
        const auto& option=j.at("development").at("diagnostic_owned_weapon_appearance");
        if(!option.is_boolean())throw std::runtime_error("Diagnostic appearance bool required");
        c.diagnostic_owned_weapon_appearance=option.get<bool>();
    }
    if(c.diagnostic_owned_weapon_appearance && (!c.owned_player_appearance_enabled || !c.owned_weapon_transfers_enabled || !addr.is_loopback() ||
       c.diagnostic_remote_actor))
        throw std::runtime_error("Diagnostic appearance requires loopback owned appearance and weapons without synthetic remote actor");
    if(c.mock_login && !addr.is_loopback()) throw std::runtime_error("Mock authentication requires a loopback bind address");
    if(j.at("development").contains("world_transfers")) {
        const auto& option=j.at("development").at("world_transfers");
        if(!option.is_object() || (option.contains("enabled") && !option.at("enabled").is_boolean()))
            throw std::runtime_error("World transfers require an object with a boolean enabled field");
        c.world_transfers_enabled=option.value("enabled",false);
        if(c.world_transfers_enabled) {
            if(!c.recovered_movement || !c.recovered_world_entry || !c.recovered_dual_connection ||
               !c.diagnostic_town_door_routes || !c.diagnostic_town_source_consensus ||
               !option.contains("catalog") || !option.at("catalog").is_string() ||
               option.at("catalog").get_ref<const std::string&>().empty())
                throw std::runtime_error("World transfers require authenticated movement, owned scene receipts, consensus and a catalog path");
            c.world_transfer_catalog=resolve(option.at("catalog").get<std::string>());
        }
    }
    c.validate_owned_pve_material_sources();
    c.validate_owned_whole_bag_moves();
    return c;
}
}
