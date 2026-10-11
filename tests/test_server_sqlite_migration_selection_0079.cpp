#include "core/Config.h"
#include "db/ServerSqliteMigrations.h"
#include "db/SqliteDatabase.h"
#include "db/SqliteMigrationManager.h"
#include "db/SqliteOwnedGuildAnnouncementRepository.h"
#include "db/SqliteSupport.h"
#include <algorithm>
#include <array>
#include <bit>
#include <chrono>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <map>
#include <memory>
#include <nlohmann/json.hpp>
#include <random>
#include <source_location>
#include <stdexcept>
#include <utility>
#include <vector>

namespace {
using namespace god2;
unsigned checks=0;
void check(bool value,const std::source_location at=std::source_location::current()) {
    ++checks;
    if(!value)throw std::runtime_error("SQLite startup selection line "+std::to_string(at.line()));
}
struct Workspace {
    std::filesystem::path root;
    Workspace() {
        const auto temp=std::filesystem::canonical(std::filesystem::temp_directory_path());
        std::random_device random;
        root=temp/("god2-announcement-startup-"+std::to_string(random())+"-"+
            std::to_string(std::chrono::steady_clock::now().time_since_epoch().count()));
        check(std::filesystem::create_directory(root));
    }
    ~Workspace() {
        // root is the exclusive child verified above; no formal/player path is used.
        std::error_code error;std::filesystem::remove_all(root,error);
    }
};
struct Connection {
    sqlite3* raw=nullptr;
    explicit Connection(const std::filesystem::path& path) {
        check(sqlite3_open(path.string().c_str(),&raw)==SQLITE_OK);
        sqlite_detail::execute(raw,"PRAGMA foreign_keys=ON");
    }
    ~Connection(){sqlite3_close_v2(raw);}
};
using Rows=std::vector<std::vector<std::uint8_t>>;
using Snapshot=std::map<std::string,Rows>;
void append(std::vector<std::uint8_t>& row,std::uint64_t number) {
    for(unsigned i=0;i<8;++i)row.push_back(static_cast<std::uint8_t>(number>>(8*i)));
}
std::string quote(const std::string& name) {
    std::string result="\"";
    for(const auto c:name){result+=c;if(c=='\"')result+=c;}
    return result+'\"';
}
// All original SQLite types, duplicate rows, full schemas, history and metadata.
// Selector/storage maintenance cannot silently coerce or drop unknown save data.
Snapshot snapshot(sqlite3* db) {
    Snapshot result;
    sqlite_detail::Statement schema(db,"SELECT type,name,tbl_name,COALESCE(sql,'') FROM sqlite_master ORDER BY type,name");
    while(schema.row()) {
        std::vector<std::uint8_t> row;
        for(int i=0;i<4;++i) {
            const auto text=schema.text(i);append(row,text.size());row.insert(row.end(),text.begin(),text.end());
        }
        result[":schema"].push_back(std::move(row));
    }
    sqlite_detail::Statement tables(db,"SELECT name FROM sqlite_master WHERE type='table' ORDER BY name");
    while(tables.row()) {
        const auto name=tables.text(0);sqlite3_stmt* query=nullptr;
        check(sqlite3_prepare_v2(db,("SELECT * FROM "+quote(name)).c_str(),-1,&query,nullptr)==SQLITE_OK);
        std::unique_ptr<sqlite3_stmt,decltype(&sqlite3_finalize)> handle(query,sqlite3_finalize);
        int step=SQLITE_OK;auto& rows=result[name];
        while((step=sqlite3_step(query))==SQLITE_ROW) {
            std::vector<std::uint8_t> row;
            for(int i=0;i<sqlite3_column_count(query);++i) {
                const auto type=sqlite3_column_type(query,i);row.push_back(static_cast<std::uint8_t>(type));
                if(type==SQLITE_INTEGER)append(row,std::bit_cast<std::uint64_t>(sqlite3_column_int64(query,i)));
                else if(type==SQLITE_FLOAT)append(row,std::bit_cast<std::uint64_t>(sqlite3_column_double(query,i)));
                else if(type==SQLITE_TEXT || type==SQLITE_BLOB) {
                    const auto size=sqlite3_column_bytes(query,i);append(row,static_cast<std::uint64_t>(size));
                    const auto* bytes=type==SQLITE_TEXT?sqlite3_column_text(query,i):
                        static_cast<const unsigned char*>(sqlite3_column_blob(query,i));
                    if(size)row.insert(row.end(),bytes,bytes+size);
                }
            }
            rows.push_back(std::move(row));
        }
        check(step==SQLITE_DONE);std::sort(rows.begin(),rows.end());
    }
    for(const auto* name:{"user_version","application_id"}) {
        sqlite_detail::Statement q(db,(std::string("PRAGMA ")+name).c_str());check(q.row());
        std::vector<std::uint8_t> row;append(row,std::bit_cast<std::uint64_t>(q.integer(0)));
        result[std::string(":")+name]={row};
    }
    return result;
}
std::vector<char> file_bytes(const std::filesystem::path& path) {
    std::ifstream file(path,std::ios::binary);check(bool(file));
    return {std::istreambuf_iterator<char>(file),std::istreambuf_iterator<char>()};
}
void exact(const std::vector<Migration>& actual,const std::vector<Migration>& expected) {
    check(actual.size()==expected.size());
    for(std::size_t i=0;i<expected.size();++i) {
        check(actual[i].version==expected[i].version);
        check(actual[i].name==expected[i].name);
        check(actual[i].sql==expected[i].sql);
    }
}
std::int64_t scalar(sqlite3* raw,const char* sql) {
    sqlite_detail::Statement q(raw,sql);check(q.row());const auto value=q.integer(0);check(!q.row());return value;
}
void initialize(const std::filesystem::path& path,const std::vector<Migration>& migrations) {
    SqliteDatabase db(path,migrations);db.initialize();db.migrate();
}
void seed_unknown(sqlite3* raw) {
    // TEST_ONLY, inside the exclusive temporary database; never a formal save.
    sqlite_detail::execute(raw,"CREATE TABLE unknown_save(number,opaque,label);"
        "INSERT INTO unknown_save VALUES(NULL,X'','');"
        "INSERT INTO unknown_save VALUES(1.25,X'000102FF',NULL);"
        "INSERT INTO unknown_save VALUES(-9223372036854775808,'mixed-text',X'FF00');"
        "INSERT INTO unknown_save SELECT * FROM unknown_save;"
        "CREATE INDEX unknown_save_index ON unknown_save(label);"
        "CREATE TRIGGER unknown_save_trigger AFTER UPDATE ON unknown_save BEGIN SELECT 1;END;"
        "PRAGMA user_version=179;PRAGMA application_id=1279;");
}
void seed_announcement(sqlite3* raw) {
    constexpr auto source="149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763";
    sqlite_detail::execute(raw,"INSERT INTO accounts(id,username,password_hash) VALUES(1,'OnlyTest','opaque');");
    std::array<std::uint8_t,40> profile{};profile[0]='S';
    sqlite_detail::Statement character(raw,"INSERT INTO recovered_characters(id,account_id,slot,profile,name_bytes,name_codepage,streamer_privilege) VALUES(1,1,0,?,X'53',0,2)");
    character.bind_blob(1,profile);character.done();
    sqlite_detail::Statement guild(raw,"INSERT INTO owned_guilds VALUES(1,'SavedGuild',1,'CUSTOM_DESIGNED','CUSTOM-0075',?)");guild.bind(1,source);guild.done();
    sqlite_detail::Statement member(raw,"INSERT INTO owned_guild_members VALUES(1,1,1,'CUSTOM_DESIGNED','CUSTOM-0075',?)");member.bind(1,source);member.done();
    sqlite_detail::Statement governance(raw,"INSERT INTO owned_guild_governance_0078 VALUES(1,1,1,1,50000,20,'CUSTOM_DESIGNED','CUSTOM-0078',?)");governance.bind(1,source);governance.done();
    sqlite_detail::Statement announcement(raw,"INSERT INTO owned_guild_announcements_0078 VALUES(1,'Saved announcement 100%',7,'CUSTOM_DESIGNED','CUSTOM-0078',?)");
    announcement.bind(1,source);announcement.done();
    // Opaque extension column is valid future saved data, not reason to reject50.
    sqlite_detail::execute(raw,"ALTER TABLE owned_guild_announcements_0078 ADD COLUMN opaque_extra BLOB;"
        "UPDATE owned_guild_announcements_0078 SET opaque_extra=X'0002FF';");
}
void initial_selection(Workspace& workspace) {
    const auto old=default_sqlite_migrations(),all=owned_guild_announcement_migrations();
    check(old.size()==49 && all.size()==50);
    const auto missing=workspace.root/"missing-parent"/"no-create.db";
    exact(configured_sqlite_migrations(missing,false),old);check(!std::filesystem::exists(missing));
    check(!std::filesystem::exists(missing.parent_path()));
    exact(configured_sqlite_migrations(missing,true),all);check(!std::filesystem::exists(missing));
    check(!std::filesystem::exists(missing.parent_path()));
    const auto empty=workspace.root/"empty.db";
    {Connection raw(empty);check(scalar(raw.raw,"SELECT count(*) FROM sqlite_master")==0);}
    const auto empty_bytes=file_bytes(empty);
    exact(configured_sqlite_migrations(empty,false),old);check(file_bytes(empty)==empty_bytes);
    exact(configured_sqlite_migrations(empty,true),all);check(file_bytes(empty)==empty_bytes);
    initialize(empty,configured_sqlite_migrations(empty,false));
    {Connection raw(empty);check(scalar(raw.raw,"SELECT max(version) FROM schema_migrations")==49);
        check(scalar(raw.raw,"SELECT count(*) FROM sqlite_master WHERE name='owned_guild_announcements_0078'")==0);}
    const auto prehistory=workspace.root/"no-history.db";
    {Connection raw(prehistory);seed_unknown(raw.raw);}
    const auto bytes=file_bytes(prehistory);exact(configured_sqlite_migrations(prehistory,false),old);
    check(file_bytes(prehistory)==bytes);
    initialize(prehistory,configured_sqlite_migrations(prehistory,false));
    {Connection raw(prehistory);check(scalar(raw.raw,"SELECT max(version) FROM schema_migrations")==49);
        check(scalar(raw.raw,"SELECT count(*) FROM unknown_save")==6);
        check(scalar(raw.raw,"SELECT count(*) FROM sqlite_master WHERE name='owned_guild_announcements_0078'")==0);}
}
void reopen_with_feature_disabled(Workspace& workspace) {
    const auto path=workspace.root/"saved50.db";
    initialize(path,configured_sqlite_migrations(path,false));
    {Connection raw(path);seed_unknown(raw.raw);}
    Snapshot before49;{Connection raw(path);before49=snapshot(raw.raw);}
    const auto bytes49=file_bytes(path);
    exact(configured_sqlite_migrations(path,false),default_sqlite_migrations());check(file_bytes(path)==bytes49);
    initialize(path,configured_sqlite_migrations(path,true));
    {Connection raw(path);check(scalar(raw.raw,"SELECT max(version) FROM schema_migrations")==50);
        check(snapshot(raw.raw).at("unknown_save")==before49.at("unknown_save"));seed_announcement(raw.raw);}
    Snapshot before50;{Connection raw(path);before50=snapshot(raw.raw);}
    const auto bytes50=file_bytes(path);
    for(unsigned reopen=0;reopen<2;++reopen) {
        const auto migrations=configured_sqlite_migrations(path,false);
        exact(migrations,owned_guild_announcement_migrations());check(file_bytes(path)==bytes50);
        {SqliteDatabase db(path,migrations);db.initialize();db.migrate();
            const auto loaded=db.guild_announcements().load(1);
            check(loaded.guild_id==1 && loaded.value.has_value());
            check(loaded.value->text_utf8=="Saved announcement 100%" && loaded.value->revision==7);
            (void)db.candidate_guild_membership();}
        {Connection raw(path);check(snapshot(raw.raw)==before50);}
    }
    // Persisted storage maintenance must not turn the runtime feature on.
    const auto config_path=workspace.root/"config.json";
    const nlohmann::json config={
        {"server",{{"name","ONLY_TEST"},{"host","127.0.0.1"},{"port",0},{"worker_threads",1},{"max_sessions",1}}},
        {"protocol",{{"mode","placeholder"},{"packet_header","uint16_length_uint16_opcode"},{"encryption","none"},{"compression","none"},{"packet_dump",false}}},
        {"database",{{"type","sqlite"},{"path",path.string()}}},
        {"lua",{{"script_root","unused"},{"bootstrap","unused"},{"hot_reload",false}}},
        {"logging",{{"file","unused.log"},{"level","info"}}},
        {"development",{{"mock_login",false}}},
        {"world",{{"owned_guild_announcements",{{"enabled",false}}}}}};
    {std::ofstream output(config_path);output<<config.dump();check(bool(output));}
    const auto loaded=Config::load(config_path);check(!loaded.owned_guild_announcements_enabled);
    exact(configured_sqlite_migrations(loaded.database,loaded.owned_guild_announcements_enabled),owned_guild_announcement_migrations());
    check(!loaded.owned_guild_announcements_enabled);
    {Connection raw(path);check(snapshot(raw.raw)==before50);}
}
void unsupported(Workspace& workspace) {
    const auto old=default_sqlite_migrations(),all=owned_guild_announcement_migrations();
    const std::vector<std::pair<unsigned,std::string>> cases={
        {50,"UPDATE schema_migrations SET name='foreign50' WHERE version=50"},
        {50,"UPDATE schema_migrations SET sql_text=sql_text||' ' WHERE version=50"},
        {50,"UPDATE schema_migrations SET sql_text=CAST(sql_text AS BLOB) WHERE version=50"},
        {50,"UPDATE schema_migrations SET name='foreign49' WHERE version=49"},
        {50,"UPDATE schema_migrations SET sql_text=sql_text||' ' WHERE version=1"},
        {50,"DELETE FROM schema_migrations WHERE version=1"},
        {50,"DELETE FROM schema_migrations WHERE version=25"},
        {50,"DELETE FROM schema_migrations WHERE version=49"},
        {50,"INSERT INTO schema_migrations(version,name,sql_text) VALUES(51,'foreign51','SELECT 1')"},
        {50,"DROP TABLE owned_guild_announcements_0078"},
        {50,"DROP TABLE owned_guild_announcements_0078;CREATE TABLE owned_guild_announcements_0078(guild_id INTEGER PRIMARY KEY,text_utf8 TEXT,revision INTEGER,origin TEXT,design_id TEXT,source_sha256 TEXT)"},
        {49,"UPDATE schema_migrations SET name='foreign49' WHERE version=49"},
        {49,"DELETE FROM schema_migrations WHERE version=23"},
        {49,SqliteOwnedGuildAnnouncementRepository::schema()},
        {0,SqliteOwnedGuildAnnouncementRepository::schema()}
    };
    unsigned number=0;
    for(const auto& [version,mutate]:cases) {
        const auto path=workspace.root/("bad-history-"+std::to_string(++number)+".db");
        if(version)initialize(path,version==50?all:old);
        {Connection raw(path);seed_unknown(raw.raw);sqlite_detail::execute(raw.raw,mutate);}
        Snapshot before;{Connection raw(path);before=snapshot(raw.raw);}
        const auto bytes=file_bytes(path);
        for(const bool feature:{false,true}) {
            bool rejected=false;
            try {
                const auto selected=configured_sqlite_migrations(path,feature);
                // Readonly selection and transactional migration are both acceptable
                // rejection boundaries. No unsupported DB may enter server startup.
                check(file_bytes(path)==bytes);
                Connection raw(path);SqliteMigrationManager(raw.raw,selected).migrate();
            }catch(const DatabaseError&){rejected=true;}
            check(rejected);check(file_bytes(path)==bytes);
            {Connection raw(path);check(snapshot(raw.raw)==before);}
        }
    }
}
}
int main() {
    try {
        Workspace workspace;initial_selection(workspace);reopen_with_feature_disabled(workspace);unsupported(workspace);
        std::cout<<"CUSTOM0078 SQLite startup migration selection: "<<checks<<" checks PASS; isolated saved49/50 only\n";
        return 0;
    }catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}
}
