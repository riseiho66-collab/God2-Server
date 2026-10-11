#include "core/Config.h"
#include "db/Migration.h"
#include "db/SqliteDatabase.h"
#include "db/SqliteMigrationManager.h"
#include "db/SqliteOwnedGuildMembershipRepository.h"
#include "db/SqliteSupport.h"
#include <nlohmann/json.hpp>
#include <algorithm>
#include <array>
#include <bit>
#include <chrono>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <memory>
#include <random>
#include <source_location>
#include <stdexcept>
#include <vector>

namespace {
using Json=nlohmann::json;
using namespace god2;
unsigned checks=0;
void check(bool value,const std::source_location at=std::source_location::current()) {
    ++checks;if(!value)throw std::runtime_error("Formal guild0078 check failed at line "+std::to_string(at.line()));
}
template<class F> void rejects(F operation) {
    bool rejected=false;try{operation();}catch(const std::exception&){rejected=true;}check(rejected);
}
struct Fixture {
    std::filesystem::path root;
    Fixture() {
        const auto temp=std::filesystem::canonical(std::filesystem::temp_directory_path());
        std::random_device random;
        for(unsigned i=0;i<100;++i) {
            auto candidate=temp/("god2-formal-guild-config-"+std::to_string(random())+"-"+
                std::to_string(std::chrono::steady_clock::now().time_since_epoch().count()));
            if(std::filesystem::create_directory(candidate)){root=candidate;return;}
        }
        throw std::runtime_error("Cannot allocate isolated formal guild fixture");
    }
    ~Fixture(){std::error_code error;std::filesystem::remove_all(root,error);}
    Config load(const Json& value) const {
        const auto path=root/"server.json";
        {std::ofstream file(path,std::ios::binary);file<<value.dump();if(!file)throw std::runtime_error("Cannot write private config");}
        return Config::load(path);
    }
};
Json base() {
    return {
        {"server",{{"name","Isolated formal guild config"},{"host","127.0.0.1"},{"port",2592},
            {"character_port",0},{"worker_threads",2},{"max_sessions",8}}},
        {"protocol",{{"name","GOD2"},{"mode","god2_legacy_character_list_candidate"},{"allow_unverified_legacy",true},
            {"packet_header","uint16_length_seed_checksum"},{"encryption","seed_fixture"},{"compression","none"},{"packet_dump",false}}},
        {"database",{{"type","sqlite"},{"path","ordinary-owned-accounts.db"}}},
        {"lua",{{"bootstrap","scripts/bootstrap.lua"},{"script_root","scripts"},{"hot_reload",false}}},
        {"logging",{{"level","debug"},{"file","private.log"}}},
        {"development",{{"mock_login",false},{"recovered_account_auth",true},{"recovered_character_creation",true},
            {"recovered_dual_connection",true},{"recovered_world_entry",true},{"recovered_movement",true},
            {"recovered_navigation","fixture-navigation.json"}}}
    };
}
void configured_admission() {
    Fixture fixture;
    auto value=base();
    const auto initial=fixture.load(value);
    check(!initial.owned_guild_membership_enabled && initial.owned_guild_entry_resource_bundle.empty());
    value["world"]["owned_guild_membership"]={{"enabled",true},{"entry_resource_bundle","CUSTOM-0078-2996-v1"}};
    const auto enabled=fixture.load(value);
    check(enabled.owned_guild_membership_enabled && enabled.owned_guild_entry_resource_bundle=="CUSTOM-0078-2996-v1");
    check(enabled.port==2592 && enabled.database.filename()=="ordinary-owned-accounts.db");
    check(enabled.recovered_account_auth && enabled.recovered_world_entry && enabled.recovered_dual_connection && enabled.recovered_movement);
    // No parser branch reads or authorizes disposable native-record environment options.
    for(const auto* field:{"recovered_account_auth","recovered_world_entry","recovered_dual_connection","recovered_movement"}) {
        auto bad=value;bad["development"][field]=false;rejects([&]{fixture.load(bad);});
    }
    auto mock=value;mock["development"]["mock_login"]=true;rejects([&]{fixture.load(mock);});
    auto missing=value;missing["world"]["owned_guild_membership"].erase("entry_resource_bundle");rejects([&]{fixture.load(missing);});
    for(const auto& bundle:Json::array({"","CUSTOM-0078-2996-v2","custom-0078-2996-v1","CUSTOM-0078-2996-v1 ",nullptr,true,3,Json::array()})) {
        auto bad=value;bad["world"]["owned_guild_membership"]["entry_resource_bundle"]=bundle;rejects([&]{fixture.load(bad);});
    }
    for(const auto& option:Json::array({nullptr,true,3,"enabled",Json::array(),Json::object(),Json{{"enabled",1}},Json{{"enabled","true"}}})) {
        auto bad=value;bad["world"]["owned_guild_membership"]=option;rejects([&]{fixture.load(bad);});
    }
    auto disabled=value;disabled["world"]["owned_guild_membership"]={{"enabled",false}};
    check(!fixture.load(disabled).owned_guild_membership_enabled);
    disabled["world"]["owned_guild_membership"]["entry_resource_bundle"]="UNQUALIFIED_DISABLED_VALUE";
    check(!fixture.load(disabled).owned_guild_membership_enabled);
    disabled["world"]["owned_guild_membership"]["entry_resource_bundle"]=false;
    rejects([&]{fixture.load(disabled);});

    // Reuse a READ-ONLY JSON config as data; Config::load does not open its DB or ports.
    // Copying it into this fixture exercises existing accepted battle parser options.
    std::ifstream formal(std::filesystem::path(GOD2_SOURCE_DIR)/"artifacts/releases/town-chat-welcome-20260924/server-config.json");
    check(bool(formal));auto compatible=Json::parse(formal);
    // Production now enables announcements, which require membership. The
    // isolated admission comparison deliberately disables that dependent flag
    // in BOTH cases; its separate activation tests retain dependency rejection.
    compatible["world"].erase("owned_guild_announcements");
    compatible["world"].erase("owned_guild_membership");
    const auto before=fixture.load(compatible);
    compatible["world"]["owned_guild_membership"]={{"enabled",true},{"entry_resource_bundle","CUSTOM-0078-2996-v1"}};
    const auto after=fixture.load(compatible);
    check(after.owned_guild_membership_enabled);
    check(before.diagnostic_battle_transition==after.diagnostic_battle_transition &&
          before.diagnostic_battle_participants==after.diagnostic_battle_participants &&
          before.diagnostic_battle_animations==after.diagnostic_battle_animations &&
          before.diagnostic_battle_resources==after.diagnostic_battle_resources &&
          before.diagnostic_battle_skill_seed==after.diagnostic_battle_skill_seed &&
          before.diagnostic_battle_skill_settlement==after.diagnostic_battle_skill_settlement &&
          before.diagnostic_battle_terminal==after.diagnostic_battle_terminal &&
          before.diagnostic_town_battle_after_quest==after.diagnostic_town_battle_after_quest &&
          before.diagnostic_town_door_after_battle==after.diagnostic_town_door_after_battle);
    check(before.database==after.database && before.port==after.port && before.character_port==after.character_port &&
          before.recovered_navigation==after.recovered_navigation && before.bootstrap==after.bootstrap &&
          before.streamer_privileges_enabled==after.streamer_privileges_enabled &&
          before.diagnostic_town_chat_welcome==after.diagnostic_town_chat_welcome &&
          before.diagnostic_town_player_visibility==after.diagnostic_town_player_visibility &&
          before.owned_instance_trade_enabled==after.owned_instance_trade_enabled);
}

using Rows=std::vector<std::vector<std::uint8_t>>;
using Snapshot=std::map<std::string,Rows>;
void append(std::vector<std::uint8_t>& row,std::uint64_t value) {
    for(unsigned i=0;i<8;++i)row.push_back(static_cast<std::uint8_t>(value>>(8*i)));
}
Snapshot snapshot(sqlite3* db) {
    Snapshot result;
    sqlite_detail::Statement tables(db,"SELECT name,sql FROM sqlite_master WHERE type='table' AND name<>'schema_migrations' ORDER BY name");
    while(tables.row()) {
        const auto name=tables.text(0),schema=tables.text(1);result[name+":schema"]={{schema.begin(),schema.end()}};
        std::string quoted="\"";for(const auto c:name){quoted+=c;if(c=='\"')quoted+=c;}quoted+='\"';
        sqlite3_stmt* q=nullptr;check(sqlite3_prepare_v2(db,("SELECT * FROM "+quoted).c_str(),-1,&q,nullptr)==SQLITE_OK);
        std::unique_ptr<sqlite3_stmt,decltype(&sqlite3_finalize)> query(q,sqlite3_finalize);
        auto& rows=result[name];int step=SQLITE_OK;
        while((step=sqlite3_step(q))==SQLITE_ROW) {
            std::vector<std::uint8_t> row;
            for(int i=0;i<sqlite3_column_count(q);++i) {
                const auto type=sqlite3_column_type(q,i);row.push_back(static_cast<std::uint8_t>(type));
                if(type==SQLITE_INTEGER)append(row,std::bit_cast<std::uint64_t>(sqlite3_column_int64(q,i)));
                else if(type==SQLITE_FLOAT)append(row,std::bit_cast<std::uint64_t>(sqlite3_column_double(q,i)));
                else if(type==SQLITE_TEXT || type==SQLITE_BLOB) {
                    const auto bytes=sqlite3_column_bytes(q,i);append(row,static_cast<std::uint64_t>(bytes));
                    const auto* data=type==SQLITE_TEXT?sqlite3_column_text(q,i):static_cast<const unsigned char*>(sqlite3_column_blob(q,i));
                    if(bytes)row.insert(row.end(),data,data+bytes);
                }
            }
            rows.push_back(std::move(row));
        }
        check(step==SQLITE_DONE);std::sort(rows.begin(),rows.end());
    }
    return result;
}
std::int64_t scalar(sqlite3* db,const char* sql) {sqlite_detail::Statement q(db,sql);check(q.row());return q.integer(0);}
void migration49_and_accessor() {
    const auto all=default_sqlite_migrations();
    check(all.size()==49);
    for(std::size_t i=0;i<all.size();++i)check(all[i].version==static_cast<int>(i+1));
    check(all[47].name=="owned_guild_chat_membership");
    check(all[48].name=="owned_player_guild_membership_candidate" && all[48].sql==SqliteOwnedGuildMembershipRepository::schema());
    sqlite3* raw=nullptr;check(sqlite3_open(":memory:",&raw)==SQLITE_OK);
    std::unique_ptr<sqlite3,decltype(&sqlite3_close_v2)> db(raw,sqlite3_close_v2);
    sqlite_detail::execute(raw,"PRAGMA foreign_keys=ON");auto old=all;old.resize(48);
    SqliteMigrationManager(raw,old).migrate();
    sqlite_detail::execute(raw,"ALTER TABLE accounts ADD COLUMN unknown_saved BLOB;"
        "INSERT INTO accounts(id,username,password_hash,unknown_saved) VALUES(1,'preserved','exact_hash',X'000102FF');"
        "CREATE TABLE unknown_player_save(id INTEGER PRIMARY KEY,empty BLOB,missing TEXT,r REAL);"
        "INSERT INTO unknown_player_save VALUES(1,X'',NULL,1.25);");
    const auto before=snapshot(raw);
    sqlite_detail::Statement history(raw,"SELECT version,name,sql_text,applied_at FROM schema_migrations ORDER BY version");
    std::vector<std::array<std::string,4>> history_before;
    while(history.row())history_before.push_back({std::to_string(history.integer(0)),history.text(1),history.text(2),history.text(3)});
    SqliteMigrationManager(raw,all).migrate();
    auto after=snapshot(raw);
    check(after.erase("owned_guild_governance_0078")==1 && after.erase("owned_guild_governance_0078:schema")==1);
    check(after.erase("owned_guild_applications_0078")==1 && after.erase("owned_guild_applications_0078:schema")==1);
    check(after==before);
    check(scalar(raw,"SELECT count(*) FROM owned_guild_governance_0078")==0);
    check(scalar(raw,"SELECT count(*) FROM owned_guild_applications_0078")==0);
    check(scalar(raw,"SELECT count(*) FROM schema_migrations")==49);
    sqlite_detail::Statement history_after(raw,"SELECT version,name,sql_text,applied_at FROM schema_migrations WHERE version<=48 ORDER BY version");
    std::vector<std::array<std::string,4>> saved_history;
    while(history_after.row())saved_history.push_back({std::to_string(history_after.integer(0)),history_after.text(1),history_after.text(2),history_after.text(3)});
    check(saved_history==history_before);
    const auto once=snapshot(raw);SqliteMigrationManager(raw,all).migrate();check(snapshot(raw)==once);
    auto tampered=all;tampered.back().sql+=' ';rejects([&]{SqliteMigrationManager(raw,tampered).migrate();});check(snapshot(raw)==once);

    sqlite3* failing_raw=nullptr;check(sqlite3_open(":memory:",&failing_raw)==SQLITE_OK);
    std::unique_ptr<sqlite3,decltype(&sqlite3_close_v2)> failing(failing_raw,sqlite3_close_v2);
    sqlite_detail::execute(failing_raw,"PRAGMA foreign_keys=ON");SqliteMigrationManager(failing_raw,old).migrate();
    sqlite_detail::execute(failing_raw,"INSERT INTO accounts(id,username,password_hash) VALUES(2,'kept','same_hash');"
        "CREATE TRIGGER reject49 BEFORE INSERT ON schema_migrations WHEN NEW.version=49 "
        "BEGIN SELECT RAISE(ABORT,'TEST_ONLY_REJECT49'); END;");
    const auto failure_before=snapshot(failing_raw);
    rejects([&]{SqliteMigrationManager(failing_raw,all).migrate();});
    check(snapshot(failing_raw)==failure_before && scalar(failing_raw,"SELECT max(version) FROM schema_migrations")==48);
    check(scalar(failing_raw,"SELECT count(*) FROM sqlite_master WHERE name IN "
        "('owned_guild_governance_0078','owned_guild_applications_0078','owned_guild_pending_audience_0078')")==0);
    sqlite_detail::execute(failing_raw,"DROP TRIGGER reject49");SqliteMigrationManager(failing_raw,all).migrate();
    check(scalar(failing_raw,"SELECT max(version) FROM schema_migrations")==49);

    Fixture fixture;const auto file=fixture.root/"private-default49.db";
    {SqliteDatabase store(file);store.initialize();store.migrate();(void)store.candidate_guild_membership();store.migrate();}
    {SqliteDatabase store(file);store.initialize();store.migrate();(void)store.candidate_guild_membership();}
    check(std::filesystem::is_regular_file(file));
}
}
int main() {
    try {configured_admission();migration49_and_accessor();
        std::cout<<"CUSTOM0078 formal Config/default49/accessor preservation: "<<checks<<" checks PASS; no server/UI/formal DB writes\n";return 0;
    }catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}
}
