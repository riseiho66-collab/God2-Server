#include "db/Database.h"
#include "db/SqliteDatabase.h"
#include "db/SqliteMigrationManager.h"
#include "db/SqliteSupport.h"
#include "db/SqliteOwnedGuildAnnouncementRepository.h"
#include <algorithm>
#include <array>
#include <bit>
#include <chrono>
#include <filesystem>
#include <iostream>
#include <map>
#include <memory>
#include <random>
#include <source_location>
#include <vector>
namespace {
using namespace god2;
unsigned checks=0;
void check(bool ok,const std::source_location at=std::source_location::current()) {
    ++checks;if(!ok)throw std::runtime_error("Announcement activation line "+std::to_string(at.line()));
}
template<class F> void rejects(F action) {bool bad=false;try{action();}catch(const DatabaseError&){bad=true;}check(bad);}
struct Memory {
    sqlite3* raw=nullptr;
    Memory(){check(sqlite3_open(":memory:",&raw)==SQLITE_OK);sqlite_detail::execute(raw,"PRAGMA foreign_keys=ON");}
    ~Memory(){sqlite3_close_v2(raw);}
};
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

std::vector<std::array<std::string,4>> history(sqlite3* db,unsigned maximum=50) {
    sqlite_detail::Statement q(db,"SELECT version,name,sql_text,applied_at FROM schema_migrations WHERE version<=? ORDER BY version");
    q.bind(1,maximum);std::vector<std::array<std::string,4>> rows;
    while(q.row())rows.push_back({std::to_string(q.integer(0)),q.text(1),q.text(2),q.text(3)});return rows;
}
std::vector<std::array<std::string,4>> schema(sqlite3* db,bool without_announcement=false) {
    sqlite_detail::Statement q(db,without_announcement?
        "SELECT type,name,tbl_name,COALESCE(sql,'') FROM sqlite_master WHERE name<>'owned_guild_announcements_0078' ORDER BY type,name":
        "SELECT type,name,tbl_name,COALESCE(sql,'') FROM sqlite_master ORDER BY type,name");
    std::vector<std::array<std::string,4>> rows;
    while(q.row())rows.push_back({q.text(0),q.text(1),q.text(2),q.text(3)});return rows;
}
void seed_saved(sqlite3* db) {
    // TEST_ONLY saved49 fixture; never against formal/player databases.
    sqlite_detail::execute(db,"ALTER TABLE accounts ADD COLUMN opaque_saved BLOB;"
        "INSERT INTO accounts(id,username,password_hash,opaque_saved) VALUES(1,'PreservedCase','opaque-password-hash',X'000102FF');"
        "CREATE TABLE unknown_saved(id,bytes BLOB,label TEXT);"
        "INSERT INTO unknown_saved VALUES(NULL,X'','');INSERT INTO unknown_saved VALUES(1.25,X'000102FF',NULL);"
        "INSERT INTO unknown_saved SELECT * FROM unknown_saved;CREATE INDEX unknown_index ON unknown_saved(label);"
        "CREATE TRIGGER unknown_saved_trigger AFTER UPDATE ON unknown_saved BEGIN SELECT 1;END;"
        "PRAGMA user_version=178;PRAGMA application_id=1278;");
    std::array<std::uint8_t,40> profile{};profile[0]='S';
    sqlite_detail::Statement character(db,"INSERT INTO recovered_characters(id,account_id,slot,profile,name_bytes,name_codepage,streamer_privilege) VALUES(1,1,0,?,X'53',0,2)");
    character.bind_blob(1,profile);character.done();
    constexpr auto source="149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763";
    sqlite_detail::Statement guild(db,"INSERT INTO owned_guilds VALUES(1,'SavedGuild',1,'CUSTOM_DESIGNED','CUSTOM-0075',?)");guild.bind(1,source);guild.done();
    sqlite_detail::Statement member(db,"INSERT INTO owned_guild_members VALUES(1,1,1,'CUSTOM_DESIGNED','CUSTOM-0075',?)");member.bind(1,source);member.done();
    sqlite_detail::Statement gov(db,"INSERT INTO owned_guild_governance_0078 VALUES(1,1,1,1,50000,20,'CUSTOM_DESIGNED','CUSTOM-0078',?)");gov.bind(1,source);gov.done();
}
void migration_preservation() {
    const auto all=owned_guild_announcement_migrations();check(all.size()==50);
    for(unsigned i=0;i<all.size();++i)check(all[i].version==static_cast<int>(i+1));
    check(all[48].name=="owned_player_guild_membership_candidate" && all[48].sql==SqliteOwnedGuildMembershipRepository::schema());
    check(all[49].name=="owned_guild_announcements_candidate" && all[49].sql==SqliteOwnedGuildAnnouncementRepository::schema());
    auto previous=all;previous.resize(49);Memory m;SqliteMigrationManager(m.raw,previous).migrate();seed_saved(m.raw);
    const auto before=snapshot(m.raw);const auto schema_before=schema(m.raw);const auto history_before=history(m.raw);
    SqliteMigrationManager(m.raw,all).migrate();auto after=snapshot(m.raw);
    check(after.erase("owned_guild_announcements_0078")==1);check(after.erase("owned_guild_announcements_0078:schema")==1);
    check(after==before && schema(m.raw,true)==schema_before && history(m.raw,49)==history_before);
    check(scalar(m.raw,"SELECT count(*) FROM owned_guild_announcements_0078")==0);
    check(scalar(m.raw,"SELECT max(version) FROM schema_migrations")==50);
    check(scalar(m.raw,"PRAGMA user_version")==178 && scalar(m.raw,"PRAGMA application_id")==1278);
    auto absent=SqliteOwnedGuildAnnouncementRepository(m.raw).load(1);check(absent.guild_id==1 && !absent.value);
    const auto once=snapshot(m.raw);const auto fullschema=schema(m.raw);const auto history_once=history(m.raw);
    SqliteMigrationManager(m.raw,all).migrate();check(snapshot(m.raw)==once && schema(m.raw)==fullschema && history(m.raw)==history_once);
    auto altered=all;altered[49].sql+=' ';rejects([&]{SqliteMigrationManager(m.raw,altered).migrate();});
    check(snapshot(m.raw)==once && history(m.raw)==history_once);
    altered=all;altered[48].name+="tampered";rejects([&]{SqliteMigrationManager(m.raw,altered).migrate();});
    check(snapshot(m.raw)==once && history(m.raw)==history_once);
    rejects([&]{SqliteMigrationManager(m.raw,previous).migrate();});check(snapshot(m.raw)==once);
}
void rollback50() {
    auto all=owned_guild_announcement_migrations(),previous=all;previous.resize(49);Memory m;
    SqliteMigrationManager(m.raw,previous).migrate();seed_saved(m.raw);
    sqlite_detail::execute(m.raw,"CREATE TRIGGER reject50 BEFORE INSERT ON schema_migrations WHEN NEW.version=50 BEGIN SELECT RAISE(ABORT,'TEST_ONLY_REJECT50');END;");
    const auto before=snapshot(m.raw);const auto schema_before=schema(m.raw);const auto history_before=history(m.raw);
    rejects([&]{SqliteMigrationManager(m.raw,all).migrate();});
    check(snapshot(m.raw)==before && schema(m.raw)==schema_before && history(m.raw)==history_before && sqlite3_get_autocommit(m.raw));
    check(scalar(m.raw,"SELECT max(version) FROM schema_migrations")==49);
    check(scalar(m.raw,"SELECT count(*) FROM sqlite_master WHERE name='owned_guild_announcements_0078'")==0);
    sqlite_detail::execute(m.raw,"DROP TRIGGER reject50");SqliteMigrationManager(m.raw,all).migrate();check(history(m.raw,49)==history_before);
}
void accessors() {
    auto all=owned_guild_announcement_migrations(),old=all;old.resize(49);
    check(default_sqlite_migrations().size()==49);
    SqliteDatabase default_db(":memory:");default_db.initialize();default_db.migrate();rejects([&]{default_db.guild_announcements();});
    (void)default_db.candidate_guild_membership();
    SqliteDatabase db(":memory:",all);rejects([&]{db.guild_announcements();});db.initialize();rejects([&]{db.guild_announcements();});db.migrate();
    Database& generic=db;check(&generic.guild_announcements()==&db.guild_announcements());
    (void)db.candidate_guild_membership();db.migrate();check(&generic.guild_announcements()==&db.guild_announcements());
    SqliteDatabase legacy(":memory:",old);legacy.initialize();legacy.migrate();(void)legacy.candidate_guild_membership();rejects([&]{legacy.guild_announcements();});
    // This custom schema would fail migration if the getter had installed its table.
    old.push_back({50,"TEST_ONLY_EXPLICIT_CUSTOM50",SqliteOwnedGuildAnnouncementRepository::schema()});
    SqliteDatabase wrong(":memory:",old);wrong.initialize();wrong.migrate();rejects([&]{wrong.guild_announcements();});rejects([&]{wrong.candidate_guild_membership();});
    old=all;old.back().sql+=' ';SqliteDatabase wrongsql(":memory:",old);wrongsql.initialize();wrongsql.migrate();rejects([&]{wrongsql.guild_announcements();});rejects([&]{wrongsql.candidate_guild_membership();});
}
void persisted_reopen() {
    const auto temp=std::filesystem::canonical(std::filesystem::temp_directory_path());
    std::random_device r;const auto dir=temp/("god2-announcement-activation-"+std::to_string(r())+"-"+std::to_string(std::chrono::steady_clock::now().time_since_epoch().count()));
    check(std::filesystem::create_directory(dir));struct Cleanup{std::filesystem::path path;~Cleanup(){std::error_code e;std::filesystem::remove_all(path,e);}} cleanup{dir};
    const auto path=dir/"exclusive-test49.db";auto all=owned_guild_announcement_migrations(),old=all;old.resize(49);
    {SqliteDatabase prior(path,old);prior.initialize();prior.migrate();rejects([&]{prior.guild_announcements();});}
    sqlite3* raw=nullptr;check(sqlite3_open(path.string().c_str(),&raw)==SQLITE_OK);
    {std::unique_ptr<sqlite3,decltype(&sqlite3_close_v2)> handle(raw,sqlite3_close_v2);
        check(scalar(raw,"SELECT max(version) FROM schema_migrations")==49);
        check(scalar(raw,"SELECT count(*) FROM sqlite_master WHERE name='owned_guild_announcements_0078'")==0);seed_saved(raw);}
    {SqliteDatabase upgraded(path,all);upgraded.initialize();upgraded.migrate();auto missing=upgraded.guild_announcements().load(1);check(!missing.value);(void)upgraded.candidate_guild_membership();}
    {SqliteDatabase reopened(path,all);reopened.initialize();reopened.migrate();check(!reopened.guild_announcements().load(1).value);}
}
}
int main(){try{migration_preservation();rollback50();accessors();persisted_reopen();std::cout<<"CUSTOM0078 announcement explicit50 activation: "<<checks<<" checks PASS; isolated only\n";return 0;}
catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
