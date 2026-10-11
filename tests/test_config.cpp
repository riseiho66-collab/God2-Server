#include "core/Config.h"
#include <nlohmann/json.hpp>
#include <chrono>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <limits>
#include <random>
#include <stdexcept>
#include <string>
#include <system_error>
#include <vector>

namespace {
namespace fs = std::filesystem;
using Json = nlohmann::json;

class ConfigFixture {
public:
    ConfigFixture() {
        const auto temp = fs::canonical(fs::temp_directory_path());
        std::random_device random;
        for (unsigned attempt = 0; attempt < 100; ++attempt) {
            const auto name = "god2-config-test-" + std::to_string(random()) + "-"
                + std::to_string(std::chrono::steady_clock::now().time_since_epoch().count());
            const auto candidate = temp / name;
            // Only take ownership of a directory this invocation created.
            if (fs::create_directory(candidate)) {
                root_ = candidate;
                return;
            }
        }
        throw std::runtime_error("test_config: cannot create temporary fixture");
    }
    ~ConfigFixture() {
        std::error_code ignored;
        fs::remove_all(root_, ignored);
    }
    ConfigFixture(const ConfigFixture&) = delete;
    ConfigFixture& operator=(const ConfigFixture&) = delete;
    const fs::path& root() const { return root_; }
    fs::path write(const Json& config) const {
        fs::create_directories(root_ / "config");
        const auto path = root_ / "config" / "server.json";
        std::ofstream out(path, std::ios::binary | std::ios::trunc);
        if (!out) throw std::runtime_error("test_config: cannot open fixture");
        out << config.dump(2);
        out.close();
        if (!out) throw std::runtime_error("test_config: cannot write fixture");
        return path;
    }
private:
    fs::path root_;
};

Json valid_config() {
    return {
        {"server", {{"name", "Config test"}, {"host", "127.0.0.1"},
            {"port", 7000}, {"worker_threads", 4}, {"max_sessions", 1000}}},
        {"protocol", {{"name", "GOD2"}, {"mode", "placeholder"},
            {"packet_header", "uint16_length_uint16_opcode"}, {"encryption", "none"},
            {"compression", "none"}, {"packet_dump", true}}},
        {"database", {{"type", "sqlite"}, {"path", "data/../data/test.db"}}},
        {"lua", {{"script_root", "scripts/./"}, {"bootstrap", "scripts/../scripts/bootstrap.lua"},
            {"hot_reload", false}}},
        {"logging", {{"level", "debug"}, {"file", "logs/../logs/test.log"}}},
        {"development", {{"mock_login", true}}}
    };
}
}

void test_config() {
    ConfigFixture fixture;
    std::vector<std::string> failures;
    auto check = [&](bool condition, const std::string& label) {
        if (!condition) failures.push_back(label);
    };
    auto rejects = [&](const Json& input, const std::string& label) {
        // Fixture I/O failures must not count as config rejection.
        const auto path = fixture.write(input);
        try {
            (void)god2::Config::load(path);
        } catch (const std::exception&) {
            return;
        }
        failures.push_back("accepted invalid " + label);
    };
    const auto valid = valid_config();
    const auto loaded = god2::Config::load(fixture.write(valid));
    check(loaded.name == "Config test" && loaded.host == "127.0.0.1", "server strings");
    check(loaded.port == 7000 && loaded.worker_threads == 4 && loaded.max_sessions == 1000, "server limits");
    check(loaded.packet_dump && !loaded.hot_reload && loaded.mock_login, "boolean settings");
    check(!loaded.recovered_account_auth && !loaded.local_account_registration,"account authentication opt-in defaults");
    check(!loaded.recovered_character_creation,"character persistence opt-in default");
    check(!loaded.recovered_dual_connection,"dual connection opt-in default");
    check(!loaded.fixture_battle,"custom battle opt-in default");
    auto battle_config=valid;
    battle_config["development"]["fixture_battle"]=true;
    rejects(battle_config,"custom battle sharing default database");
    battle_config["database"]["path"]="isolated/fixture-combat.sqlite";
    check(god2::Config::load(fixture.write(battle_config)).fixture_battle,"explicit isolated battle config");
    auto invalid_battle=battle_config;
    invalid_battle["server"]["host"]="0.0.0.0";
    rejects(invalid_battle,"custom battle non-loopback bind");
    invalid_battle=battle_config;invalid_battle["development"]["mock_login"]=false;
    rejects(invalid_battle,"custom battle without mock auth");
    invalid_battle=battle_config;
    invalid_battle["protocol"]["mode"]="god2_recovered";
    invalid_battle["protocol"]["packet_header"]="uint16_length_seed_checksum";
    invalid_battle["protocol"]["encryption"]="seed_fixture";
    rejects(invalid_battle,"custom battle in original-client transport");
    check(!loaded.recovered_world_entry,"world entry candidate opt-in default");
    check(!loaded.recovered_movement,"movement opt-in default");
    check(loaded.log_level == "debug", "log level");
    // Config paths are relative to the project root above config/, not the process cwd.
    check(loaded.database == fixture.root() / "data" / "test.db", "relative database path");
    check(loaded.script_root.lexically_normal() == (fixture.root() / "scripts" / "").lexically_normal(), "relative script root");
    check(loaded.bootstrap == fixture.root() / "scripts" / "bootstrap.lua", "relative bootstrap path");
    check(loaded.log_file == fixture.root() / "logs" / "test.log", "relative log path");

    auto absolute = valid;
    const auto absolute_file = fixture.root() / "absolute" / "value";
    absolute["database"]["path"] = absolute_file.generic_string();
    absolute["lua"]["script_root"] = absolute_file.generic_string();
    absolute["lua"]["bootstrap"] = absolute_file.generic_string();
    absolute["logging"]["file"] = absolute_file.generic_string();
    const auto resolved = god2::Config::load(fixture.write(absolute));
    check(resolved.database == absolute_file && resolved.script_root == absolute_file
        && resolved.bootstrap == absolute_file && resolved.log_file == absolute_file, "absolute paths preserved");

    for (const auto* field : {"mode", "packet_header", "encryption", "compression"}) {
        auto bad = valid;
        bad["protocol"][field] = "unsupported";
        rejects(bad, std::string("protocol ") + field);
    }
    for (const auto* backend : {"mysql", "mariadb", "unknown", ""}) {
        auto bad = valid;
        bad["database"]["type"] = backend;
        rejects(bad, std::string("backend ") + backend);
    }
    for (const auto* host : {"0.0.0.0", "::", "192.0.2.1", "2001:db8::1"}) {
        auto bad = valid;
        bad["server"]["host"] = host;
        rejects(bad, std::string("mock bind ") + host);
        bad["development"]["mock_login"] = false;
        check(!god2::Config::load(fixture.write(bad)).mock_login, "nonmock nonloopback bind");
    }
    for (const auto* host : {"127.0.0.1", "127.1.2.3", "::1"}) {
        auto good = valid;
        good["server"]["host"] = host;
        check(god2::Config::load(fixture.write(good)).host == host, "loopback mock bind");
    }
    auto bad_host = valid;
    bad_host["server"]["host"] = "not-an-ip-address";
    rejects(bad_host, "bind address");

    struct Limit { const char* field; int minimum; int maximum; };
    for (const auto limit : {Limit{"port", 0, 65535}, Limit{"worker_threads", 1, 64},
            Limit{"max_sessions", 1, 100000}}) {
        for (const int value : {limit.minimum, limit.maximum}) {
            auto good = valid;
            good["server"][limit.field] = value;
            const auto config = god2::Config::load(fixture.write(good));
            const auto actual = std::string(limit.field) == "port" ? config.port
                : std::string(limit.field) == "worker_threads" ? config.worker_threads : config.max_sessions;
            check(actual == static_cast<std::size_t>(value), std::string("boundary ") + limit.field);
        }
        for (const int value : {limit.minimum - 1, limit.maximum + 1}) {
            auto bad = valid;
            bad["server"][limit.field] = value;
            rejects(bad, std::string(limit.field) + "=" + std::to_string(value));
        }
        // Regressions: validate JSON type and range before any narrowing conversion.
        for (const auto& value : std::vector<Json>{1.0, 1.5, 4294967297ULL, -4294967295LL,
                std::numeric_limits<std::uint64_t>::max(), std::numeric_limits<std::int64_t>::min(),
                "1", true, nullptr}) {
            auto bad = valid;
            bad["server"][limit.field] = value;
            rejects(bad, std::string(limit.field) + "=" + value.dump());
        }
    }
    for (const auto* section : {"server", "protocol", "database", "lua", "logging", "development"}) {
        auto missing = valid;
        missing.erase(section);
        rejects(missing, std::string("missing section ") + section);
    }
    auto recovered=valid;
    recovered["protocol"]["mode"]="god2_recovered";
    recovered["protocol"]["packet_header"]="uint16_length_seed_checksum";
    recovered["protocol"]["encryption"]="seed_fixture";
    check(god2::Config::load(fixture.write(recovered)).protocol_mode==god2::ProtocolMode::God2Recovered,"recovered opt-in");
    recovered["server"]["host"]="0.0.0.0";
    recovered["development"]["mock_login"]=false;
    rejects(recovered,"recovered remote bind refused without mock login");
    auto candidate=recovered;
    candidate["server"]["host"]="127.0.0.1";
    candidate["protocol"]["mode"]="god2_legacy_character_list_candidate";
    rejects(candidate,"legacy candidate without unverified opt-in");
    candidate["protocol"]["allow_unverified_legacy"]=false;
    rejects(candidate,"legacy candidate explicit refusal");
    candidate["protocol"]["allow_unverified_legacy"]=true;
    check(god2::Config::load(fixture.write(candidate)).protocol_mode==god2::ProtocolMode::God2LegacyCharacterListCandidate,
        "legacy character-list candidate opt-in");
    auto authenticated=candidate;
    authenticated["development"]["recovered_account_auth"]=true;
    check(god2::Config::load(fixture.write(authenticated)).recovered_account_auth,"recovered authentication enabled");
    authenticated["development"]["recovered_character_creation"]=true;
    check(god2::Config::load(fixture.write(authenticated)).recovered_character_creation,"character persistence enabled");
    authenticated["development"]["local_account_registration"]=true;
    check(god2::Config::load(fixture.write(authenticated)).local_account_registration,"local registration enabled");
    auto dual=authenticated;
    dual["development"]["recovered_dual_connection"]=true;
    rejects(dual,"dual connection without explicit character port");
    dual["server"]["character_port"]=0;
    check(god2::Config::load(fixture.write(dual)).recovered_dual_connection,"dual connection ephemeral endpoint enabled");
    auto world=dual;world["development"]["recovered_world_entry"]=true;
    check(god2::Config::load(fixture.write(world)).recovered_world_entry,"world entry candidate enabled");
    auto movement=world;movement["development"]["recovered_movement"]=true;
    rejects(movement,"movement without navigation asset");
    movement["development"]["recovered_navigation"]="artifacts/world-atlas/indoor-2-15.json";
    const auto movement_config=god2::Config::load(fixture.write(movement));
    check(movement_config.recovered_movement && movement_config.recovered_navigation==
        fixture.root()/"artifacts/world-atlas/indoor-2-15.json","movement navigation root resolution");
    check(!movement_config.diagnostic_remote_actor,"Remote actor probe defaults off");
    check(!movement_config.diagnostic_player_visibility,"Player visibility defaults off");
    auto visibility=movement;
    visibility["development"]["diagnostic_player_visibility"]=true;
    visibility["development"]["diagnostic_remote_actor_language"]=0;
    rejects(visibility,"Player visibility requires dedicated database");
    visibility["database"]["path"]="artifacts/runs/test/player-visibility-diagnostic.db";
    check(god2::Config::load(fixture.write(visibility)).diagnostic_player_visibility,"Player visibility opt-in");
    for(const auto* key:{"recovered_account_auth","recovered_movement","recovered_dual_connection"}) {
        auto bad=visibility;bad["development"][key]=false;
        rejects(bad,"Player visibility missing dependency");
    }
    for(const auto& language:std::vector<Json>{-1,2,1.5,true,"0",nullptr}) {
        auto bad=visibility;bad["development"]["diagnostic_remote_actor_language"]=language;
        rejects(bad,"Player visibility invalid language");
    }
    auto mixed=visibility;mixed["development"]["diagnostic_remote_actor"]=true;
    rejects(mixed,"Player visibility rejects competing actor probe");
    auto visibility_battle=visibility;
    for(const auto* key:{"diagnostic_visibility_battle","diagnostic_battle_transition",
        "diagnostic_battle_participants","diagnostic_battle_player_appearance",
        "diagnostic_battle_animations","diagnostic_battle_terminal"})
        visibility_battle["development"][key]=true;
    check(god2::Config::load(fixture.write(visibility_battle)).diagnostic_visibility_battle,
        "Explicit isolated visibility battle accepted");
    for(const auto* key:{"diagnostic_player_visibility","diagnostic_battle_transition",
        "diagnostic_battle_participants","diagnostic_battle_player_appearance",
        "diagnostic_battle_animations","diagnostic_battle_terminal"}) {
        auto bad=visibility_battle;bad["development"][key]=false;
        rejects(bad,"Visibility battle missing dependency");
    }
    auto durable_visibility=visibility_battle;durable_visibility["development"]["diagnostic_battle_resources"]=true;
    check(god2::Config::load(fixture.write(durable_visibility)).diagnostic_battle_resources,
        "Explicit visibility fixture can use existing resource settlement");
    auto checkpoint_visibility=durable_visibility;checkpoint_visibility["development"]["diagnostic_visibility_checkpoint"]=true;
    check(god2::Config::load(fixture.write(checkpoint_visibility)).diagnostic_visibility_checkpoint,
        "Explicit durable visibility checkpoint accepted");
    auto skill_visibility=checkpoint_visibility;
    for(const auto* key:{"diagnostic_visibility_skill_recovery","diagnostic_battle_skill_seed","diagnostic_battle_skill_settlement"})
        skill_visibility["development"][key]=true;
    skill_visibility["development"]["diagnostic_battle_rounds"]=3;
    check(god2::Config::load(fixture.write(skill_visibility)).diagnostic_visibility_skill_recovery,
        "Explicit checkpointed visibility skill recovery accepted");
    for(const auto* key:{"diagnostic_visibility_checkpoint","diagnostic_battle_resources",
        "diagnostic_battle_skill_seed","diagnostic_battle_skill_settlement"}) {
        auto bad=skill_visibility;bad["development"][key]=false;
        rejects(bad,"Skill recovery requires all persistence and skill dependencies");
    }
    checkpoint_visibility["development"]["diagnostic_battle_resources"]=false;
    rejects(checkpoint_visibility,"Visibility checkpoint cannot run without persistence");
    checkpoint_visibility=movement;checkpoint_visibility["development"]["diagnostic_visibility_checkpoint"]=true;
    rejects(checkpoint_visibility,"Visibility checkpoint cannot run standalone");
    for(const auto* key:{"diagnostic_battle_skill_seed",
        "diagnostic_remote_actor","diagnostic_world_resources","diagnostic_resume_checkpoint"}) {
        auto bad=visibility_battle;bad["development"][key]=true;
        rejects(bad,"Visibility battle rejects unrelated fixture");
    }
    auto bad_rounds=visibility_battle;bad_rounds["development"]["diagnostic_battle_rounds"]=3;
    rejects(bad_rounds,"Visibility battle admits only single round");
    auto remote=movement;
    remote["development"]["diagnostic_remote_actor"]=true;
    remote["development"]["diagnostic_remote_actor_language"]=0;
    rejects(remote,"Remote actor probe requires dedicated database");
    remote["database"]["path"]="artifacts/runs/test/remote-actor-diagnostic.db";
    check(god2::Config::load(fixture.write(remote)).diagnostic_remote_actor,"Remote actor explicit opt-in");
    for(const auto& language:std::vector<Json>{-1,2,256,1.5,true,"0",nullptr}) {
        auto bad=remote;bad["development"]["diagnostic_remote_actor_language"]=language;
        rejects(bad,"Remote actor invalid language");
    }
    for(const auto* dependency:{"recovered_account_auth","recovered_movement"}) {
        auto bad=remote;bad["development"][dependency]=false;
        rejects(bad,"Remote actor missing dependency");
    }
    auto competing=remote;competing["development"]["diagnostic_battle_transition"]=true;
    rejects(competing,"Remote actor rejects competing diagnostic");
    auto town=movement;
    town["development"]["diagnostic_town"]={{"center_x",3},{"center_y",3},{"x",63},{"y",63}};
    rejects(town,"Town diagnostic refuses normal database");
    town["database"]["path"]="artifacts/runs/test/town-diagnostic-accounts.db";
    town["development"]["recovered_navigation"]="artifacts/world-atlas/town-2-4.json";
    const auto town_config=god2::Config::load(fixture.write(town));
    check(!town_config.diagnostic_town_source_consensus,"Town source agreement defaults off");
    check(!town_config.diagnostic_town_spawn_guides,"Town guide spawn defaults off");
    check(!town_config.diagnostic_town_chat_welcome,"Town chat welcome defaults off");
    auto welcome=town;
    welcome["development"]["diagnostic_town"]["chat_welcome"]=true;
    rejects(welcome,"Town welcome requires first world tick route");
    welcome["development"]["diagnostic_town"]["spawn_guides"]=true;
    check(god2::Config::load(fixture.write(welcome)).diagnostic_town_chat_welcome,
          "Explicit isolated common-channel welcome");
    check(!town_config.diagnostic_town_quest_progress,"Town quest progress defaults off");
    check(!town_config.diagnostic_town_map_probe,"Town map probe defaults off");
    check(!town_config.diagnostic_town_scene_probe,"Town scene probe defaults off");
    check(!town_config.diagnostic_town_scene_relocate,"Town relocation defaults off");
    check(!town_config.diagnostic_town_scene_indoor_probe,"Indoor scene probe defaults off");
    check(!town_config.diagnostic_town_scene_return_probe,"Return probe defaults off");
    check(!town_config.diagnostic_town_scene_return_commit,"Durable return defaults off");
    check(!town_config.diagnostic_town_door_routes,"Door routes default off");
    check(!town_config.diagnostic_town_player_visibility,"Town player visibility defaults off");
    check(!town_config.diagnostic_town_battle_after_quest,"Town battle defaults off");
    auto doors=town;
    auto& door_options=doors["development"]["diagnostic_town"];
    door_options["door_routes"]=true;
    rejects(doors,"Door routes require consensus and guide isolation");
    door_options["source_consensus"]=true;door_options["spawn_guides"]=true;
    rejects(doors,"Door routes require indoor navigation");
    door_options["indoor_navigation"]="";
    rejects(doors,"Door routes refuse empty indoor navigation");
    door_options["indoor_navigation"]="artifacts/world-atlas/indoor-2-15.json";
    check(god2::Config::load(fixture.write(doors)).diagnostic_town_door_routes,"Explicit isolated door routes");
    auto all_doors=doors;
    all_doors["development"]["diagnostic_town"]["all_door_routes"]=true;
    rejects(all_doors,"All town doors require indoor scene bundle");
    all_doors["development"]["diagnostic_town"]["indoor_scenes"]="artifacts/world-atlas/town-doors-2.json";
    const auto all_door_config=god2::Config::load(fixture.write(all_doors));
    check(all_door_config.diagnostic_town_all_door_routes &&
          all_door_config.diagnostic_town_indoor_scenes.filename()=="town-doors-2.json","Configured multi-room door bundle");
    all_doors["development"]["diagnostic_town"]["door_routes"]=false;
    rejects(all_doors,"All town doors require door route state machine");
    auto kunlun_doors=doors;
    kunlun_doors["development"]["diagnostic_town"]["kunlun_door_routes"]=true;
    rejects(kunlun_doors,"Kunlun doors require indoor scene bundle");
    kunlun_doors["development"]["diagnostic_town"]["kunlun_indoor_scenes"]="artifacts/world-atlas/kunlun-doors-4.json";
    rejects(kunlun_doors,"Kunlun doors require birthplace navigation");
    kunlun_doors["world"]["new_character_birthplace"]={{"area",4},{"scene",3},{"kind",0},{"x",126},{"y",126},
        {"navigation","artifacts/world-atlas/kunlun-4-3.json"}};
    const auto kunlun_door_config=god2::Config::load(fixture.write(kunlun_doors));
    check(kunlun_door_config.diagnostic_kunlun_door_routes &&
          kunlun_door_config.diagnostic_kunlun_indoor_scenes.filename()=="kunlun-doors-4.json","Configured Kunlun door bundle");
    kunlun_doors["development"]["diagnostic_town"]["door_routes"]=false;
    rejects(kunlun_doors,"Kunlun doors require door route state machine");
    auto parent=doors;
    parent["development"]["diagnostic_town"]["kunlun_parent_routes"]=true;
    rejects(parent,"Kunlun parent requires full source navigation");
    parent["development"]["diagnostic_town"]["kunlun_parent_navigation"]="artifacts/world-atlas/island03-full-navigation-4-0.json";
    rejects(parent,"Kunlun parent requires city birthplace navigation");
    parent["world"]["new_character_birthplace"]={{"area",4},{"scene",3},{"kind",0},{"x",126},{"y",126},
        {"navigation","artifacts/world-atlas/kunlun-4-3.json"}};
    parent["development"]["diagnostic_town"]["player_visibility"]=true;
    parent["development"]["diagnostic_remote_actor_language"]=0;
    check(god2::Config::load(fixture.write(parent)).diagnostic_kunlun_parent_routes,"Kunlun parent multiplayer flag accepted");
    parent["development"]["diagnostic_town"]["door_routes"]=false;
    rejects(parent,"Kunlun parent requires door transfer machinery");
    auto island_town=doors;
    island_town["development"]["diagnostic_town"]["island_navigation"]=
        "artifacts/world-atlas/island01-entry-2-0.json";
    check(god2::Config::load(fixture.write(island_town)).diagnostic_town_island_navigation.filename()==
          "island01-entry-2-0.json","Explicit scene0 navigation path");
    island_town["development"]["diagnostic_town"]["island_routes"]=true;
    check(god2::Config::load(fixture.write(island_town)).diagnostic_town_island_routes,
          "Explicit isolated Island01 route flag");
    island_town["development"]["diagnostic_town"]["player_visibility"]=true;
    island_town["development"]["diagnostic_remote_actor_language"]=0;
    check(god2::Config::load(fixture.write(island_town)).diagnostic_town_player_visibility,
          "Island route composes with authenticated door visibility");
    island_town["development"]["diagnostic_town"]["player_visibility"]=false;
    island_town["development"]["diagnostic_town"]["door_routes"]=false;
    rejects(island_town,"Island route requires door transfer machinery");
    island_town["development"]["diagnostic_town"]["door_routes"]=true;
    island_town["development"]["diagnostic_town"]["source_consensus"]=false;
    rejects(island_town,"Scene0 navigation requires source consensus");
    island_town["development"]["diagnostic_town"]["source_consensus"]=true;
    island_town["development"]["diagnostic_town"]["island_navigation"]="";
    rejects(island_town,"Scene0 navigation rejects empty path");
    auto map_doors=doors;
    auto& map_door_options=map_doors["development"]["diagnostic_town"];
    map_door_options["quest_progress"]=true;
    map_door_options["map_probe"]=true;
    const auto map_door_config=god2::Config::load(fixture.write(map_doors));
    check(map_door_config.diagnostic_town_door_routes && map_door_config.diagnostic_town_map_probe,
          "Map panel can coexist with isolated movement-triggered doors");
    for(const auto* key:{"scene_probe","scene_indoor_transfer","scene_return_probe"}) {
        auto conflict=map_doors;conflict["development"]["diagnostic_town"][key]=true;
        rejects(conflict,"Door route conflicts with manual transfer probe");
    }
    door_options["door_routes"]=1;
    rejects(doors,"Door routes must be boolean");
    check(!town_config.diagnostic_town_scene_indoor_transfer && town_config.diagnostic_town_indoor_navigation.empty(),
          "Durable indoor transfer defaults off");
    auto relocation_town=town;relocation_town["development"]["diagnostic_town"]["scene_relocate"]=true;
    rejects(relocation_town,"Town relocation requires scene probe");
    auto scene_town=town;scene_town["development"]["diagnostic_town"]["scene_probe"]=true;
    rejects(scene_town,"Scene probe requires map probe");
    scene_town["development"]["diagnostic_town"]["map_probe"]=true;
    scene_town["development"]["diagnostic_town"]["quest_progress"]=true;
    scene_town["development"]["diagnostic_town"]["spawn_guides"]=true;
    check(god2::Config::load(fixture.write(scene_town)).diagnostic_town_scene_probe,"Explicit isolated scene probe");
    auto indoor_probe=scene_town;indoor_probe["development"]["diagnostic_town"]["scene_indoor_probe"]=true;
    check(god2::Config::load(fixture.write(indoor_probe)).diagnostic_town_scene_indoor_probe,"Explicit indoor probe");
    auto durable_indoor=indoor_probe;
    auto& durable_options=durable_indoor["development"]["diagnostic_town"];
    durable_options["scene_indoor_transfer"]=true;
    durable_options["source_consensus"]=true;
    rejects(durable_indoor,"Durable indoor transfer requires explicit navigation");
    durable_options["indoor_navigation"]="";
    rejects(durable_indoor,"Durable indoor transfer rejects empty navigation");
    durable_options["indoor_navigation"]="artifacts/world-atlas/indoor-2-15.json";
    const auto durable_config=god2::Config::load(fixture.write(durable_indoor));
    auto town_battle=durable_indoor;
    town_battle["development"]["diagnostic_town"]["battle_after_quest"]=true;
    rejects(town_battle,"Town battle requires battle transition");
    town_battle["development"]["diagnostic_battle_transition"]=true;
    rejects(town_battle,"Town battle requires complete durable skill fixture");
    for(const auto* key:{"diagnostic_battle_participants","diagnostic_battle_player_appearance",
                         "diagnostic_battle_animations","diagnostic_battle_skill_seed",
                         "diagnostic_battle_skill_settlement","diagnostic_battle_terminal",
                         "diagnostic_battle_resources"})
        town_battle["development"][key]=true;
    check(god2::Config::load(fixture.write(town_battle)).diagnostic_town_battle_after_quest,
          "Explicit isolated completed-town indoor battle");
    auto defeated_world_resources=town_battle;
    defeated_world_resources["development"]["diagnostic_world_resources"]=true;
    check(god2::Config::load(fixture.write(defeated_world_resources)).diagnostic_world_resources,
          "Saved world resources can follow isolated town battle");
    defeated_world_resources["database"]["path"]="artifacts/runs/test/accounts.db";
    rejects(defeated_world_resources,"Town world resources reject normal database");
    defeated_world_resources=town_battle;
    defeated_world_resources["development"]["diagnostic_world_resources"]=true;
    defeated_world_resources["development"]["diagnostic_town"]["battle_after_quest"]=false;
    rejects(defeated_world_resources,"Town world resources require qualified battle route");
    auto battle_return=town_battle;
    battle_return["development"]["diagnostic_town"]["return_after_battle"]=true;
    rejects(battle_return,"Post-battle return requires durable map return");
    battle_return["development"]["diagnostic_town"]["scene_return_probe"]=true;
    battle_return["development"]["diagnostic_town"]["scene_return_commit"]=true;
    check(god2::Config::load(fixture.write(battle_return)).diagnostic_town_return_after_battle,
          "Explicit isolated battle followed by durable map return");
    battle_return["development"]["diagnostic_town"]["battle_after_quest"]=false;
    rejects(battle_return,"Post-battle return cannot bypass battle gate");
    auto battle_door=town_battle;
    battle_door["development"]["diagnostic_town"]["door_routes"]=true;
    rejects(battle_door,"Town battle rejects doorway route without explicit composition");
    battle_door["development"]["diagnostic_town"]["door_after_battle"]=true;
    check(god2::Config::load(fixture.write(battle_door)).diagnostic_town_door_after_battle,
          "Explicit isolated battle followed by indoor doorway route");
    auto natural_battle=map_doors;
    natural_battle["development"]["diagnostic_town"]["battle_after_quest"]=true;
    natural_battle["development"]["diagnostic_town"]["door_after_battle"]=true;
    for(const auto* key:{"diagnostic_battle_transition","diagnostic_battle_participants",
                         "diagnostic_battle_player_appearance","diagnostic_battle_animations",
                         "diagnostic_battle_skill_seed","diagnostic_battle_skill_settlement",
                         "diagnostic_battle_terminal","diagnostic_battle_resources"})
        natural_battle["development"][key]=true;
    const auto natural_battle_config=god2::Config::load(fixture.write(natural_battle));
    check(natural_battle_config.diagnostic_town_door_routes &&
          natural_battle_config.diagnostic_town_map_probe &&
          natural_battle_config.diagnostic_town_battle_after_quest &&
          !natural_battle_config.diagnostic_town_scene_probe,
          "Battle can compose with natural doors and the existing map panel");
    auto visible_town=natural_battle;
    visible_town["development"]["diagnostic_town"]["player_visibility"]=true;
    rejects(visible_town,"Town visibility requires explicit actor language template");
    visible_town["development"]["diagnostic_remote_actor_language"]=0;
    check(god2::Config::load(fixture.write(visible_town)).diagnostic_town_player_visibility,
          "Town multiplayer presence composes with current quest door and battle route");
    auto bad_visible_town=visible_town;
    bad_visible_town["development"]["diagnostic_town"]["door_routes"]=false;
    rejects(bad_visible_town,"Town visibility requires the qualified door lifecycle");
    bad_visible_town=visible_town;
    bad_visible_town["development"]["diagnostic_remote_actor_language"]=2;
    rejects(bad_visible_town,"Town visibility rejects unknown actor language");
    natural_battle["development"]["diagnostic_town"]["door_after_battle"]=false;
    rejects(natural_battle,"Natural doorway battle still requires explicit composition");
    battle_door["development"]["diagnostic_town"]["door_routes"]=false;
    rejects(battle_door,"Post-battle door requires doorway route");
    town_battle["development"]["diagnostic_town"]["quest_progress"]=false;
    rejects(town_battle,"Town battle requires completed quest mode");
    town_battle["development"]["diagnostic_town"]["quest_progress"]=true;
    town_battle["development"]["diagnostic_battle_experience"]=250;
    rejects(town_battle,"Town battle cannot invent quest-linked experience");
    town_battle["development"]["diagnostic_battle_experience"]=0;
    town_battle["development"]["diagnostic_town"]["battle_after_quest"]=false;
    rejects(town_battle,"Town battle transition cannot silently bypass quest gate");
    auto return_probe=durable_indoor;
    return_probe["development"]["diagnostic_town"]["scene_return_probe"]=true;
    check(god2::Config::load(fixture.write(return_probe)).diagnostic_town_scene_return_probe,"Explicit isolated return probe");
    auto return_commit=return_probe;
    return_commit["development"]["diagnostic_town"]["scene_return_commit"]=true;
    check(god2::Config::load(fixture.write(return_commit)).diagnostic_town_scene_return_commit,"Explicit durable return");
    return_commit["development"]["diagnostic_town"]["scene_return_probe"]=false;
    rejects(return_commit,"Durable return requires return probe");
    return_commit["development"]["diagnostic_town"]["scene_return_probe"]=true;
    return_commit["development"]["diagnostic_town"]["scene_return_commit"]=1;
    rejects(return_commit,"Durable return requires boolean opt-in");
    return_probe["development"]["diagnostic_town"]["scene_indoor_transfer"]=false;
    rejects(return_probe,"Return probe requires dual-map mode");
    return_probe["development"]["diagnostic_town"]["scene_indoor_transfer"]=true;
    return_probe["development"]["diagnostic_town"]["scene_return_probe"]=1;
    rejects(return_probe,"Return probe requires boolean opt-in");
    check(durable_config.diagnostic_town_scene_indoor_transfer &&
          durable_config.diagnostic_town_indoor_navigation.filename()=="indoor-2-15.json","Explicit durable indoor transfer");
    durable_options["source_consensus"]=false;
    rejects(durable_indoor,"Durable indoor transfer requires source consensus");
    durable_options["source_consensus"]=true;
    durable_options["scene_indoor_probe"]=false;
    rejects(durable_indoor,"Durable indoor transfer requires indoor probe");
    durable_options["scene_indoor_probe"]=true;
    durable_options["scene_relocate"]=true;
    rejects(durable_indoor,"Durable indoor transfer conflicts with town relocation");
    durable_options["scene_relocate"]=false;
    durable_options["scene_indoor_transfer"]="true";
    rejects(durable_indoor,"Durable indoor transfer requires boolean opt-in");
    indoor_probe["development"]["diagnostic_town"]["scene_relocate"]=true;
    rejects(indoor_probe,"Indoor probe cannot persist town relocation");
    indoor_probe["development"]["diagnostic_town"]["scene_relocate"]=false;
    indoor_probe["development"]["diagnostic_town"]["scene_probe"]=false;
    rejects(indoor_probe,"Indoor probe requires scene probe");
    relocation_town=scene_town;relocation_town["development"]["diagnostic_town"]["scene_relocate"]=true;
    check(god2::Config::load(fixture.write(relocation_town)).diagnostic_town_scene_relocate,"Explicit isolated relocation");
    relocation_town["development"]["diagnostic_town"]["scene_relocate"]=1;
    rejects(relocation_town,"Town relocation must be boolean");
    scene_town["development"]["diagnostic_town"]["scene_probe"]=1;
    rejects(scene_town,"Scene probe must be boolean");
    auto map_town=town;map_town["development"]["diagnostic_town"]["map_probe"]=true;
    rejects(map_town,"Map probe requires quest progress");
    map_town["development"]["diagnostic_town"]["quest_progress"]=true;
    map_town["development"]["diagnostic_town"]["spawn_guides"]=true;
    check(god2::Config::load(fixture.write(map_town)).diagnostic_town_map_probe,"Explicit isolated map probe");
    map_town["development"]["diagnostic_town"]["map_probe"]=1;
    rejects(map_town,"Map probe must be boolean");
    auto progress_town=town;progress_town["development"]["diagnostic_town"]["quest_progress"]=true;
    rejects(progress_town,"Town quest progress requires guide spawn");
    progress_town["development"]["diagnostic_town"]["spawn_guides"]=true;
    check(god2::Config::load(fixture.write(progress_town)).diagnostic_town_quest_progress,"Explicit town quest progress");
    progress_town["development"]["diagnostic_town"]["quest_progress"]=1;
    rejects(progress_town,"Town quest progress requires boolean");
    auto guide_town=town;guide_town["development"]["diagnostic_town"]["spawn_guides"]=true;
    check(god2::Config::load(fixture.write(guide_town)).diagnostic_town_spawn_guides,"Explicit isolated town guide spawn");
    guide_town["development"]["diagnostic_town"]["spawn_guides"]=1;
    rejects(guide_town,"Town guide spawn requires boolean");
    auto consensus_town=town;consensus_town["development"]["diagnostic_town"]["source_consensus"]=true;
    check(god2::Config::load(fixture.write(consensus_town)).diagnostic_town_source_consensus,"Explicit isolated source agreement");
    consensus_town["development"]["diagnostic_town"]["source_consensus"]=1;
    rejects(consensus_town,"Source agreement requires boolean");
    check(town_config.diagnostic_town && town_config.diagnostic_town_x==63 &&
          town_config.diagnostic_town_center_x==3,"Town explicit configuration");
    for(const auto& field:{"x","y","center_x","center_y"}) {
        for(const auto& value:std::vector<nlohmann::json>{-1,189,4294967296ULL,1.5,true}) {
            auto bad=town;bad["development"]["diagnostic_town"][field]=value;
            rejects(bad,"Town coordinate rejects narrowing/type errors");
        }
    }
    auto bad_town=town;bad_town["development"]["diagnostic_town"]=false;
    rejects(bad_town,"Town settings require explicit object");
    bad_town=town;bad_town["development"]["diagnostic_battle_transition"]=true;
    rejects(bad_town,"Town refuses indoor battle diagnostic");
    bad_town=town;bad_town["development"]["recovered_movement"]=false;
    rejects(bad_town,"Town requires movement");
    movement["development"]["recovered_world_entry"]=false;
    auto battle_probe=movement;
    battle_probe["development"]["recovered_world_entry"]=true;
    battle_probe["development"]["diagnostic_battle_transition"]=true;
    battle_probe["development"]["diagnostic_battle_participants"]=true;
    rejects(battle_probe,"diagnostic battle cannot use normal database");
    battle_probe["database"]["path"]="artifacts/runs/test/diagnostic-accounts.db";
    check(god2::Config::load(fixture.write(battle_probe)).diagnostic_battle_transition,"isolated transition opt-in");
    check(!god2::Config::load(fixture.write(battle_probe)).diagnostic_battle_after_movement,"Movement encounter defaults off");
    auto movement_encounter=battle_probe;
    movement_encounter["development"]["diagnostic_battle_after_movement"]=true;
    check(god2::Config::load(fixture.write(movement_encounter)).diagnostic_battle_after_movement,"Movement encounter opt-in");
    auto bad_encounter=movement_encounter;bad_encounter["development"]["diagnostic_battle_transition"]=false;
    rejects(bad_encounter,"Movement encounter without transition");
    bad_encounter=movement_encounter;bad_encounter["development"]["diagnostic_battle_participants"]=false;
    rejects(bad_encounter,"Movement encounter without participants");
    bad_encounter=movement_encounter;bad_encounter["database"]["path"]="accounts.db";
    rejects(bad_encounter,"Movement encounter normal database");
    check(!god2::Config::load(fixture.write(battle_probe)).diagnostic_battle_player_appearance,"Player appearance defaults off");
    auto appearance=battle_probe;appearance["development"]["diagnostic_battle_player_appearance"]=true;
    check(!god2::Config::load(fixture.write(appearance)).diagnostic_battle_skill_seed,"Skill seed defaults off");
    auto skill_seed=appearance;skill_seed["development"]["diagnostic_battle_skill_seed"]=true;
    check(god2::Config::load(fixture.write(skill_seed)).diagnostic_battle_skill_seed,"Isolated skill seed opt-in");
    check(!god2::Config::load(fixture.write(skill_seed)).diagnostic_battle_skill_settlement,"Skill settlement defaults off");
    auto settlement=skill_seed;settlement["development"]["diagnostic_battle_skill_settlement"]=true;
    check(god2::Config::load(fixture.write(settlement)).diagnostic_battle_skill_kind==0,
          "Skill family defaults to physical fixture");
    auto spell_family=settlement;
    spell_family["development"]["diagnostic_battle_skill_kind"]=1;
    rejects(spell_family,"Spell family on existing diagnostic database");
    spell_family["database"]["path"]="private-skill-family-config/diagnostic-accounts.db";
    check(god2::Config::load(fixture.write(spell_family)).diagnostic_battle_skill_kind==1,
          "Explicit isolated spell family opt-in");
    for(const auto& value:std::vector<Json>{-1,2,1.5,"1",true}) {
        auto invalid=spell_family;invalid["development"]["diagnostic_battle_skill_kind"]=value;
        rejects(invalid,"Invalid spell family type or range");
    }
    for(const auto* key:{"diagnostic_battle_skill_seed","diagnostic_battle_skill_settlement"}) {
        auto invalid=spell_family;invalid["development"][key]=false;
        rejects(invalid,"Spell family without seed or settlement");
    }
    auto spell_revival=spell_family;spell_revival["development"]["diagnostic_battle_revival"]=true;
    rejects(spell_revival,"Spell family with revival schema");
    check(!god2::Config::load(fixture.write(skill_seed)).diagnostic_battle_revival,"Revival defaults off");
    auto revival=skill_seed;
    revival["development"]["diagnostic_battle_revival"]=true;
    revival["development"]["diagnostic_battle_animations"]=true;
    check(god2::Config::load(fixture.write(revival)).diagnostic_battle_revival,"Isolated revival opt-in");
    auto revival_two=revival;revival_two["development"]["diagnostic_battle_rounds"]=2;
    check(god2::Config::load(fixture.write(revival_two)).diagnostic_battle_rounds==2,"Revival followup opt-in");
    auto revival_durable=revival_two;revival_durable["development"]["diagnostic_battle_resources"]=true;
    check(god2::Config::load(fixture.write(revival_durable)).diagnostic_battle_resources,"Revival isolated persistence opt-in");
    auto revival_resume=revival_durable;revival_resume["development"]["diagnostic_resume_checkpoint"]=true;
    check(god2::Config::load(fixture.write(revival_resume)).diagnostic_battle_rounds==2,"Revival two-round resume opt-in");
    revival_resume["development"]["diagnostic_battle_rounds"]=1;
    check(god2::Config::load(fixture.write(revival_resume)).diagnostic_resume_checkpoint,"Revival snapshot restore opt-in");
    auto revival_terminal=revival_resume;revival_terminal["development"]["diagnostic_battle_terminal"]=true;
    check(god2::Config::load(fixture.write(revival_terminal)).diagnostic_battle_terminal,"Revival restored zero-award terminal opt-in");
    revival_terminal["development"]["diagnostic_battle_experience"]=1;
    rejects(revival_terminal,"Revival terminal excludes unqualified awards");
    for(const auto* key:{"diagnostic_battle_skill_seed","diagnostic_battle_animations","diagnostic_battle_player_appearance","diagnostic_battle_transition"}) {
        auto invalid=revival;invalid["development"][key]=false;
        rejects(invalid,"Revival missing prerequisite");
    }
    for(const auto* key:{"diagnostic_battle_skill_settlement","diagnostic_world_resources",
                         "diagnostic_battle_mp_refusal","diagnostic_battle_terminal","diagnostic_battle_after_movement"}) {
        auto invalid=revival;invalid["development"][key]=true;
        rejects(invalid,"Revival incompatible diagnostic");
    }
    auto invalid_revival=revival;invalid_revival["database"]["path"]="accounts.db";
    rejects(invalid_revival,"Revival refuses normal database");
    check(!god2::Config::load(fixture.write(settlement)).diagnostic_battle_resources,"Resource persistence defaults off");
    auto resources=settlement;resources["development"]["diagnostic_battle_resources"]=true;
    check(!god2::Config::load(fixture.write(settlement)).diagnostic_world_resources,"World resources default off");
    auto world_resources=movement;
    world_resources["development"]["recovered_world_entry"]=true;
    world_resources["development"]["diagnostic_world_resources"]=true;
    rejects(world_resources,"World resource projection cannot use normal database");
    world_resources["database"]["path"]="artifacts/runs/test/diagnostic-accounts.db";
    check(god2::Config::load(fixture.write(world_resources)).diagnostic_world_resources,"World resource isolated opt-in");
    check(!god2::Config::load(fixture.write(world_resources)).diagnostic_battle_transition,"World resources do not require battle");
    check(!god2::Config::load(fixture.write(world_resources)).diagnostic_world_supply,"Supply default off");
    check(!god2::Config::load(fixture.write(world_resources)).diagnostic_quest_dialogue,"Quest dialogue defaults off");
    auto quest_dialogue=world_resources;
    quest_dialogue["development"]["diagnostic_world_resources"]=false;
    quest_dialogue["development"]["diagnostic_quest_dialogue"]=true;
    check(god2::Config::load(fixture.write(quest_dialogue)).diagnostic_quest_dialogue,"Quest dialogue isolated opt-in");
    check(!god2::Config::load(fixture.write(quest_dialogue)).diagnostic_quest_npc,"NPC spawn defaults off");
    auto npc_probe=quest_dialogue;npc_probe["development"]["diagnostic_quest_npc"]=true;
    check(god2::Config::load(fixture.write(npc_probe)).diagnostic_quest_npc,"NPC spawn isolated opt-in");
    auto npc_invalid=npc_probe;npc_invalid["development"]["diagnostic_quest_dialogue"]=false;
    rejects(npc_invalid,"NPC spawn requires isolated dialogue");
    npc_invalid=npc_probe;npc_invalid["database"]["path"]="accounts.db";
    rejects(npc_invalid,"NPC spawn cannot use normal database");
    for(const auto* key:{"recovered_world_entry","recovered_movement"}) {
        auto invalid=quest_dialogue;invalid["development"][key]=false;
        rejects(invalid,"Quest dialogue missing world prerequisites");
    }
    for(const auto* key:{"diagnostic_world_resources","diagnostic_battle_transition"}) {
        auto invalid=quest_dialogue;invalid["development"][key]=true;
        rejects(invalid,"Quest dialogue mixed projection rejected");
    }
    auto quest_normal_db=quest_dialogue;quest_normal_db["database"]["path"]="accounts.db";
    rejects(quest_normal_db,"Quest dialogue refuses production database");
    auto supply=world_resources;supply["development"]["diagnostic_world_supply"]=true;
    check(god2::Config::load(fixture.write(supply)).diagnostic_world_supply,"Supply isolated opt-in");
    auto bad_supply=supply;bad_supply["development"]["diagnostic_world_resources"]=false;
    rejects(bad_supply,"Supply requires resource projection");
    bad_supply=supply;bad_supply["development"]["diagnostic_battle_transition"]=true;
    rejects(bad_supply,"Supply cannot mix unqualified encounter initialization");
    bad_supply=supply;bad_supply["database"]["path"]="accounts.db";
    rejects(bad_supply,"Supply cannot access production database");
    auto post_supply=resources;
    post_supply["development"]["diagnostic_world_resources"]=true;
    post_supply["development"]["diagnostic_world_supply"]=true;
    post_supply["development"]["diagnostic_battle_terminal"]=true;
    post_supply["development"]["diagnostic_battle_rounds"]=3;
    post_supply["development"]["diagnostic_battle_animations"]=true;
    check(god2::Config::load(fixture.write(post_supply)).diagnostic_world_supply,"Single terminal battle supply opt-in");
    for(const auto key:{"diagnostic_battle_resources","diagnostic_battle_terminal"}) {
        auto bad=post_supply;bad["development"][key]=false;
        rejects(bad,"Post-battle supply requires durable terminal settlement");
    }
    auto bad_post_supply=post_supply;bad_post_supply["development"]["diagnostic_battle_rounds"]=1;
    rejects(bad_post_supply,"Post-battle supply excludes unqualified one-round branch");
    auto repeated_supply=post_supply;
    repeated_supply["development"]["diagnostic_battle_after_movement"]=true;
    repeated_supply["development"]["diagnostic_encounter_limit"]=2;
    check(god2::Config::load(fixture.write(repeated_supply)).diagnostic_encounter_limit==2,
          "Two settled movement battles may use saved supply without level seeding");
    for(const auto* key:{"diagnostic_battle_after_movement","diagnostic_battle_resources",
                         "diagnostic_world_resources","diagnostic_world_supply"}) {
        auto bad=repeated_supply;bad["development"][key]=false;
        rejects(bad,"Two-battle supply requires complete isolated lifecycle");
    }
    for(const auto* key:{"diagnostic_level_snapshot","diagnostic_role_progress",
                         "diagnostic_resume_checkpoint"}) {
        auto bad=repeated_supply;bad["development"][key]=true;
        rejects(bad,"Two-battle supply excludes unqualified progress/resume mix");
    }
    auto bad_repeated_supply=repeated_supply;
    bad_repeated_supply["development"]["diagnostic_battle_experience"]=25;
    rejects(bad_repeated_supply,"Two-battle supply does not invent a reward schedule");
    auto bad_world_resources=world_resources;bad_world_resources["development"]["recovered_movement"]=false;
    rejects(bad_world_resources,"World resources require movement isolation");
    bad_world_resources=world_resources;bad_world_resources["server"]["host"]="0.0.0.0";
    rejects(bad_world_resources,"World resources reject public listener");
    bad_world_resources=world_resources;bad_world_resources["development"]["mock_login"]=true;
    rejects(bad_world_resources,"World resources reject mock authentication");
    check(god2::Config::load(fixture.write(resources)).diagnostic_battle_resources,"Isolated resource persistence opt-in");
    resources["development"]["diagnostic_battle_skill_settlement"]=false;
    rejects(resources,"Resource persistence requires skill settlement isolation");
    check(god2::Config::load(fixture.write(settlement)).diagnostic_battle_skill_settlement,"Isolated skill settlement opt-in");
    auto skill_animation=settlement;skill_animation["development"]["diagnostic_battle_animations"]=true;
    check(god2::Config::load(fixture.write(skill_animation)).diagnostic_battle_animations,"Isolated skill animation opt-in");
    auto manual=skill_animation;
    manual["development"]["diagnostic_shunying_manual"]=true;
    manual["development"]["diagnostic_shunying_character_id"]=6;
    manual["database"]["path"]="private-shunying-manual-config-test/diagnostic-accounts.db";
    check(god2::Config::load(fixture.write(manual)).diagnostic_shunying_manual,"Manual full field isolated opt-in");
    check(!god2::Config::load(fixture.write(manual)).diagnostic_thousand_bulls_manual,"Bull trial must default off");
    auto bull_manual=manual;bull_manual["development"]["diagnostic_thousand_bulls_manual"]=true;
    check(god2::Config::load(fixture.write(bull_manual)).diagnostic_thousand_bulls_manual,"Bull trial isolated opt-in");
    check(!god2::Config::load(fixture.write(bull_manual)).diagnostic_recording_fixed_damage,"Recording mode defaults off");
    auto recording=bull_manual;recording["development"]["diagnostic_recording_fixed_damage"]=true;
    check(god2::Config::load(fixture.write(recording)).diagnostic_recording_fixed_damage,"Isolated recording opt-in");
    recording["development"]["diagnostic_thousand_bulls_manual"]=false;
    rejects(recording,"Fixed damage cannot escape isolated bull trial");
    bull_manual["development"]["diagnostic_shunying_manual"]=false;
    rejects(bull_manual,"Bull trial requires existing full isolation");
    auto bad_manual=manual;bad_manual["database"]["path"]="diagnostic-accounts.db";
    rejects(bad_manual,"Manual requires dedicated directory");
    bad_manual=manual;bad_manual["development"]["diagnostic_shunying_character_id"]=0;
    rejects(bad_manual,"Manual requires one explicit test character");
    bad_manual=manual;bad_manual["server"]["host"]="0.0.0.0";
    rejects(bad_manual,"Manual refuses public listener");
    bad_manual["development"]["diagnostic_thousand_bulls_manual"]=true;
    rejects(bad_manual,"Bull trial refuses public listener");
    for(const auto key:{"diagnostic_battle_resources","diagnostic_battle_terminal","diagnostic_battle_revival","diagnostic_battle_mp_refusal"}) {
        bad_manual=manual;bad_manual["development"][key]=true;
        rejects(bad_manual,"Manual excludes production/durable/other fixture lifecycle");
    }
    auto natural_finish=skill_animation;
    natural_finish["development"]["diagnostic_battle_rounds"]=3;
    rejects(natural_finish,"Three rounds require terminal mode");
    natural_finish["development"]["diagnostic_battle_terminal"]=true;
    check(god2::Config::load(fixture.write(natural_finish)).diagnostic_battle_rounds==3,"Three-round skill completion opt-in");
    for(const auto* required:{"diagnostic_battle_skill_settlement","diagnostic_battle_animations"}) {
        auto bad=natural_finish;bad["development"][required]=false;
        rejects(bad,"Three-round finish requires skill and animations");
    }
    natural_finish["development"]["diagnostic_battle_rounds"]=4;
    rejects(natural_finish,"Unqualified fourth round rejected");
    check(!god2::Config::load(fixture.write(skill_animation)).diagnostic_battle_mp_refusal,"MP refusal defaults off");
    auto refusal=skill_animation;refusal["development"]["diagnostic_battle_mp_refusal"]=true;
    check(god2::Config::load(fixture.write(refusal)).diagnostic_battle_mp_refusal,"Isolated MP refusal opt-in");
    for(const auto* required:{"diagnostic_battle_skill_settlement","diagnostic_battle_animations","diagnostic_battle_skill_seed"}) {
        auto bad=refusal;bad["development"][required]=false;
        rejects(bad,"MP refusal requires isolated skill prerequisites");
    }
    auto refusal_terminal=refusal;refusal_terminal["development"]["diagnostic_battle_terminal"]=true;
    rejects(refusal_terminal,"Refusal and lethal test cannot be mixed");
    auto refusal_rounds=refusal;refusal_rounds["development"]["diagnostic_battle_rounds"]=2;
    rejects(refusal_rounds,"Refusal fixture has one round");
    for(const auto* incompatible:{"diagnostic_battle_terminal"}) {
        auto bad=settlement;bad["development"][incompatible]=true;
        rejects(bad,"Skill settlement rejects incompatible effects");
    }
    auto skill_terminal=skill_animation;skill_terminal["development"]["diagnostic_battle_terminal"]=true;
    check(god2::Config::load(fixture.write(skill_terminal)).diagnostic_battle_terminal,"Animated isolated skill terminal opt-in");
    check(god2::Config::load(fixture.write(skill_terminal)).diagnostic_battle_experience==0,"XP defaults to zero");
    auto award=skill_terminal;award["development"]["diagnostic_battle_experience"]=25;
    rejects(award,"XP requires persistence");
    award["development"]["diagnostic_battle_resources"]=true;
    check(god2::Config::load(fixture.write(award)).diagnostic_battle_experience==25,"Isolated persisted award");
    check(!god2::Config::load(fixture.write(award)).diagnostic_role_progress,"Role progress probe defaults off");
    auto progress=award;progress["development"]["diagnostic_role_progress"]=true;
    check(god2::Config::load(fixture.write(progress)).diagnostic_role_progress,"Qualified progress probe");
    progress["development"]["diagnostic_progress_span"]=200;
    check(god2::Config::load(fixture.write(progress)).diagnostic_progress_span==200,"Explicit test interval");
    check(!god2::Config::load(fixture.write(progress)).diagnostic_level_snapshot,"Level snapshot defaults off");
    auto level=progress;level["development"]["diagnostic_level_snapshot"]=true;
    level["development"]["diagnostic_battle_experience"]=250;
    check(god2::Config::load(fixture.write(level)).diagnostic_level_snapshot,"Explicit crossing experiment");
    check(!god2::Config::load(fixture.write(level)).diagnostic_character_growth,"Growth defaults off");
    auto growth=level;growth["development"]["diagnostic_character_growth"]=true;
    check(god2::Config::load(fixture.write(growth)).diagnostic_character_growth,"Owner growth isolated opt-in");
    auto growth_without_snapshot=growth;growth_without_snapshot["development"]["diagnostic_level_snapshot"]=false;
    rejects(growth_without_snapshot,"Growth requires persisted full level snapshot");
    check(!god2::Config::load(fixture.write(level)).diagnostic_resume_checkpoint,"Resume defaults off");
    auto resume=level;resume["development"]["diagnostic_resume_checkpoint"]=true;
    resume["development"]["diagnostic_battle_rounds"]=3;
    check(god2::Config::load(fixture.write(resume)).diagnostic_resume_checkpoint,"Qualified resume policy");
    auto repeated=resume;
    repeated["development"]["diagnostic_resume_checkpoint"]=false;
    repeated["development"]["diagnostic_battle_after_movement"]=true;
    check(god2::Config::load(fixture.write(repeated)).diagnostic_encounter_limit==1,"Encounter limit defaults one");
    repeated["development"]["diagnostic_encounter_limit"]=2;
    check(god2::Config::load(fixture.write(repeated)).diagnostic_encounter_limit==2,"Qualified two-encounter probe");
    for(const auto* flag:{"diagnostic_battle_after_movement","diagnostic_level_snapshot","diagnostic_battle_terminal"}) {
        auto bad=repeated;bad["development"][flag]=false;rejects(bad,"Two encounters require qualified lifecycle");
    }
    for(const auto value:{nlohmann::json(0),nlohmann::json(-1),nlohmann::json(3),nlohmann::json(1.5),nlohmann::json(true),nlohmann::json("2")}) {
        auto bad=repeated;bad["development"]["diagnostic_encounter_limit"]=value;rejects(bad,"Encounter limit invalid type or range");
    }
    auto movement_resume=resume;movement_resume["development"]["diagnostic_battle_after_movement"]=true;
    rejects(movement_resume,"Resume cannot be triggered as a fresh movement encounter");
    for(const auto* flag:{"diagnostic_level_snapshot","diagnostic_battle_animations","diagnostic_battle_skill_settlement"}) {
        auto bad=resume;bad["development"][flag]=false;rejects(bad,"Resume requires qualified policy");
    }
    auto wrong_resume=resume;wrong_resume["development"]["diagnostic_progress_span"]=201;
    rejects(wrong_resume,"Resume cannot change saved test curve");
    wrong_resume=resume;wrong_resume["development"]["diagnostic_battle_experience"]=251;
    rejects(wrong_resume,"Resume cannot change saved test award");
    for(const auto* flag:{"diagnostic_role_progress","diagnostic_battle_player_appearance","diagnostic_battle_resources","diagnostic_battle_terminal"}) {
        auto bad=level;bad["development"][flag]=false;
        rejects(bad,"Level snapshot must preserve diagnostic prerequisites");
    }
    auto no_span=level;no_span["development"]["diagnostic_progress_span"]=0;
    rejects(no_span,"Level snapshot needs explicit curve");
    for(const auto& invalid:nlohmann::json::array({-1,25,24,2147483648LL,1.5,"200",true})) {
        auto bad=progress;bad["development"]["diagnostic_progress_span"]=invalid;
        rejects(bad,"Invalid or already-earned test interval accepted");
    }
    auto no_progress=progress;no_progress["development"]["diagnostic_role_progress"]=false;
    rejects(no_progress,"Test interval requires isolated progress path");
    progress["development"]["diagnostic_battle_experience"]=0;
    rejects(progress,"Progress probe requires explicit award experiment");
    for(const auto& invalid:nlohmann::json::array({-1,2147483648LL,1.5,"25",true})) {
        auto bad=award;bad["development"]["diagnostic_battle_experience"]=invalid;
        rejects(bad,"Invalid test XP accepted");
    }
    award["development"]["diagnostic_battle_terminal"]=false;
    rejects(award,"XP requires terminal mode");
    skill_terminal["development"]["diagnostic_battle_rounds"]=2;
    rejects(skill_terminal,"Skill terminal cannot rearm additional rounds");
    auto no_seed=settlement;no_seed["development"]["diagnostic_battle_skill_seed"]=false;
    rejects(no_seed,"Skill settlement requires seed");
    auto extra_round=settlement;extra_round["development"]["diagnostic_battle_rounds"]=2;
    rejects(extra_round,"Repeated skills require animation completion");
    extra_round["development"]["diagnostic_battle_animations"]=true;
    check(god2::Config::load(fixture.write(extra_round)).diagnostic_battle_rounds==2,"Two animated skill rounds");
    skill_seed["development"]["diagnostic_battle_player_appearance"]=false;
    rejects(skill_seed,"Skill seed requires isolated player appearance");
    check(god2::Config::load(fixture.write(appearance)).diagnostic_battle_player_appearance,"Isolated player appearance opt-in");
    check(!god2::Config::load(fixture.write(appearance)).diagnostic_battle_animations,"Animation defaults off");
    auto animation=appearance;animation["development"]["diagnostic_battle_animations"]=true;
    check(god2::Config::load(fixture.write(animation)).diagnostic_battle_animations,"Isolated animation opt-in");
    animation["development"]["diagnostic_battle_player_appearance"]=false;
    rejects(animation,"Animation requires player appearance");
    appearance["development"]["diagnostic_battle_participants"]=false;
    rejects(appearance,"Player appearance requires participants");
    auto two_rounds=battle_probe;two_rounds["development"]["diagnostic_battle_rounds"]=2;
    auto terminal=battle_probe;terminal["development"]["diagnostic_battle_terminal"]=true;
    check(god2::Config::load(fixture.write(terminal)).diagnostic_battle_terminal,"Isolated terminal diagnostic");
    terminal["development"]["diagnostic_battle_rounds"]=2;
    rejects(terminal,"Terminal cannot rearm diagnostic rounds");
    terminal["development"]["diagnostic_battle_rounds"]=1;
    terminal["development"]["diagnostic_battle_participants"]=false;
    rejects(terminal,"Terminal requires diagnostic participants");
    check(god2::Config::load(fixture.write(two_rounds)).diagnostic_battle_rounds==2,"Bounded two-round diagnostic");
    for(const auto& count:std::vector<Json>{0,3,-1,true,1.5,"2",4294967297ULL}) {
        auto bad=two_rounds;bad["development"]["diagnostic_battle_rounds"]=count;
        rejects(bad,"Invalid diagnostic round count");
    }
    two_rounds["development"]["diagnostic_battle_participants"]=false;
    rejects(two_rounds,"Multiple rounds without diagnostic participants");
    auto orphan=battle_probe;orphan["development"]["diagnostic_battle_transition"]=false;
    rejects(orphan,"participants without diagnostic transition");
    battle_probe["development"]["recovered_movement"]=false;
    rejects(battle_probe,"diagnostic battle requires world-ready movement service");
    rejects(movement,"movement without world entry");
    auto world_clock=world;world_clock["world"]["clock"]={{"enabled",true},{"sync_seconds",60}};
    auto knowledge=movement;knowledge["development"]["diagnostic_knowledge_menu"]=true;
    knowledge["development"]["recovered_world_entry"]=true;
    knowledge["database"]["path"]="isolated/knowledge-menu-diagnostic.db";
    check(god2::Config::load(fixture.write(knowledge)).diagnostic_knowledge_menu,"Knowledge menu isolated opt-in");
    auto bad_knowledge=knowledge;bad_knowledge["database"]["path"]="town-diagnostic-accounts.db";rejects(bad_knowledge,"Knowledge menu cannot use live town DB");
    for(const auto* field:{"recovered_world_entry","recovered_movement"}) {
        bad_knowledge=knowledge;bad_knowledge["development"][field]=false;rejects(bad_knowledge,"Knowledge native dependency required");
    }
    check(god2::Config::load(fixture.write(world_clock)).world_clock_enabled,"Native world clock enabled");
    for(const auto& value:std::vector<Json>{0,4,301,-1,4294967301ULL,5.5,true,"60",nullptr}) {
        auto bad=world_clock;bad["world"]["clock"]["sync_seconds"]=value;rejects(bad,"Invalid world clock interval");
    }
    auto bad_clock=world_clock;bad_clock["world"]["clock"]["enabled"]=1;rejects(bad_clock,"Clock bool required");
    bad_clock=valid_config();bad_clock["world"]["clock"]={{"enabled",true}};rejects(bad_clock,"Clock world entry required");
    auto maps=knowledge;maps["development"]["diagnostic_knowledge_menu"]=false;
    maps["world"]["owned_map_views"]={{"enabled",true}};
    check(god2::Config::load(fixture.write(maps)).owned_map_views_enabled,"Owned map view opt-in");
    auto weapons=maps;weapons["world"]["owned_weapon_transfers"]={{"enabled",true}};
    check(!god2::Config::load(fixture.write(maps)).owned_attribute_allocation_enabled,"Allocation defaults off");
    auto allocation=maps;allocation["world"]["owned_attribute_allocation"]={{"enabled",true}};
    check(god2::Config::load(fixture.write(allocation)).owned_attribute_allocation_enabled,"Owned allocation opt-in");
    auto bad_allocation=allocation;bad_allocation["world"]["owned_attribute_allocation"]["enabled"]=1;
    rejects(bad_allocation,"Allocation bool required");
    for(const auto* field:{"recovered_account_auth","recovered_world_entry","recovered_movement"}) {
        bad_allocation=allocation;bad_allocation["development"][field]=false;
        rejects(bad_allocation,"Allocation authenticated native dependency required");
    }
    check(god2::Config::load(fixture.write(weapons)).owned_weapon_transfers_enabled,"Owned weapon transfer opt-in");
    // CUSTOM-0066: activation must retain authenticated native world ownership.
    check(!god2::Config::load(fixture.write(maps)).owned_armor_transfers_enabled,"Owned armor defaults off");
    auto armor=maps;armor["world"]["owned_armor_transfers"]={{"enabled",true}};
    check(god2::Config::load(fixture.write(armor)).owned_armor_transfers_enabled,"Owned armor transfer opt-in");
    for(const auto& value:std::vector<Json>{1,0,"true",nullptr,Json::array(),Json::object()}) {
        auto bad_armor=armor;bad_armor["world"]["owned_armor_transfers"]["enabled"]=value;
        rejects(bad_armor,"Armor transfer bool required");
    }
    for(const auto* field:{"recovered_world_entry","recovered_movement","recovered_account_auth"}) {
        auto bad_armor=armor;bad_armor["development"][field]=false;
        rejects(bad_armor,"Armor transfer authenticated native dependency required");
    }
    auto bad_armor=armor;bad_armor["development"]["mock_login"]=true;
    rejects(bad_armor,"Armor transfer cannot use mock login");
    auto armor_off=valid;armor_off["world"]["owned_armor_transfers"]={{"enabled",false}};
    check(!god2::Config::load(fixture.write(armor_off)).owned_armor_transfers_enabled,"Explicit armor off keeps legacy config valid");
    check(!god2::Config::load(fixture.write(armor)).owned_armor_bank_enabled,"Armor bank defaults off");
    auto armor_bank=armor;armor_bank["world"]["owned_armor_bank"]={{"enabled",true}};
    check(god2::Config::load(fixture.write(armor_bank)).owned_armor_bank_enabled,"Armor bank opt-in");
    for(const auto& value:std::vector<Json>{1,"true",nullptr,Json::array(),Json::object()}) {
        auto bad=armor_bank;bad["world"]["owned_armor_bank"]["enabled"]=value;rejects(bad,"Armor bank bool required");
    }
    for(const auto* field:{"recovered_world_entry","recovered_movement","recovered_account_auth"}) {
        auto bad=armor_bank;bad["development"][field]=false;rejects(bad,"Armor bank owner dependencies required");
    }
    auto bad_bank=armor_bank;bad_bank["world"]["owned_armor_transfers"]["enabled"]=false;rejects(bad_bank,"Armor bank requires full armor transport");
    bad_bank=armor_bank;bad_bank["development"]["mock_login"]=true;rejects(bad_bank,"Armor bank cannot use mock login");
    auto daily=maps;daily["world"]["owned_daily_quest_views"]={{"enabled",true}};
    check(god2::Config::load(fixture.write(daily)).owned_daily_quest_views_enabled,"Owned daily view opt-in");
    auto bad_daily=daily;bad_daily["world"]["owned_daily_quest_views"]["enabled"]=1;rejects(bad_daily,"Daily view bool required");
    for(const auto* field:{"recovered_world_entry","recovered_movement","recovered_account_auth"}) {
        bad_daily=daily;bad_daily["development"][field]=false;rejects(bad_daily,"Daily view authenticated native dependencies required");
    }
    auto owned_supply=maps;owned_supply["world"]["owned_supply"]={{"enabled",true}};
    check(god2::Config::load(fixture.write(owned_supply)).owned_supply_enabled,"Owned supply native opt-in");
    auto bad_owned_supply=owned_supply;bad_owned_supply["world"]["owned_supply"]["enabled"]=1;rejects(bad_owned_supply,"Owned supply bool required");
    for(const auto* field:{"recovered_world_entry","recovered_movement","recovered_account_auth"}) {
        bad_owned_supply=owned_supply;bad_owned_supply["development"][field]=false;rejects(bad_owned_supply,"Owned supply authenticated native dependency required");
    }
    bad_owned_supply=owned_supply;bad_owned_supply["development"]["diagnostic_world_resources"]=true;bad_owned_supply["development"]["diagnostic_world_supply"]=true;
    rejects(bad_owned_supply,"Owned supply excludes legacy diagnostic supply");
    {
    auto appearance=weapons;appearance["world"]["owned_player_appearance"]={{"enabled",true}};
    check(god2::Config::load(fixture.write(appearance)).owned_player_appearance_enabled,"Owned appearance restoration opt-in");
    auto bad_appearance=appearance;bad_appearance["world"]["owned_player_appearance"]["enabled"]=1;rejects(bad_appearance,"Appearance bool required");
    for(const char* field:{"recovered_account_auth","recovered_world_entry","recovered_movement"}) {
        bad_appearance=appearance;bad_appearance["development"][field]=false;rejects(bad_appearance,"Appearance native authentication dependency required");
    }
    appearance["development"]["diagnostic_owned_weapon_appearance"]=true;
    check(god2::Config::load(fixture.write(appearance)).diagnostic_owned_weapon_appearance,"Isolated diagnostic appearance opt-in");
    for(const char* field:{"diagnostic_remote_actor"}) {
        bad_appearance=appearance;bad_appearance["development"][field]=true;rejects(bad_appearance,"Diagnostic appearance must not publish stale peers");
    }
    bad_appearance=appearance;bad_appearance["world"]["owned_player_appearance"]["enabled"]=false;rejects(bad_appearance,"Diagnostic appearance needs persistence");
    bad_appearance=appearance;bad_appearance["world"]["owned_weapon_transfers"]["enabled"]=false;rejects(bad_appearance,"Diagnostic appearance needs equipment route");
    }
    auto bad_weapons=weapons;bad_weapons["world"]["owned_weapon_transfers"]["enabled"]=1;rejects(bad_weapons,"Weapon transfer bool required");
    for(const auto* field:{"recovered_world_entry","recovered_movement","recovered_account_auth"}) {
        bad_weapons=weapons;bad_weapons["development"][field]=false;rejects(bad_weapons,"Weapon transfer native authentication dependency required");
    }
    auto bad_maps=maps;bad_maps["world"]["owned_map_views"]["enabled"]=1;rejects(bad_maps,"Map view bool required");
    for(const auto* field:{"recovered_world_entry","recovered_movement"}) {
        bad_maps=maps;bad_maps["development"][field]=false;rejects(bad_maps,"Map view native dependency required");
    }
    world["development"]["recovered_dual_connection"]=false;
    rejects(world,"world entry without independent character connection");
    for(const auto& value:std::vector<Json>{-1,65536,4294967297ULL,1.5,true,"2593",nullptr}) {
        auto bad=dual;bad["server"]["character_port"]=value;
        rejects(bad,"invalid character port");
    }
    auto bad_dual=dual;bad_dual["server"]["character_port"]=7000;
    rejects(bad_dual,"duplicate listener endpoint");
    bad_dual=dual;bad_dual["server"]["host"]="::1";
    rejects(bad_dual,"IPv6 cannot be advertised by recovered IPv4 route");
    bad_dual=dual;bad_dual["development"]["recovered_character_creation"]=false;
    rejects(bad_dual,"dual connection without profile ownership service");
    authenticated["development"]["mock_login"]=true;
    rejects(authenticated,"recovered authentication with mock login");
    authenticated["development"]["mock_login"]=false;
    authenticated["protocol"]["mode"]="god2_post_server_select";
    rejects(authenticated,"recovered authentication outside candidate mode");
    authenticated=candidate;
    authenticated["development"]["local_account_registration"]=true;
    rejects(authenticated,"registration without authentication");
    authenticated=candidate;
    authenticated["development"]["recovered_character_creation"]=true;
    rejects(authenticated,"character persistence without authentication");
    for(const auto* host : {"0.0.0.0","192.0.2.1","::"}) {
        candidate["server"]["host"]=host;
        rejects(candidate,"legacy candidate nonloopback bind");
    }
    if (!failures.empty()) {
        std::string message = "test_config failures:";
        for (const auto& failure : failures) message += "\n- " + failure;
        throw std::runtime_error(message);
    }
}
