#include "db/GuildOfficerSqliteMigrations.h"
#include "db/ServerSqliteMigrations.h"
#include "db/SqliteOwnedGuildMembershipRepository.h"
#include "db/SqliteSupport.h"
#include <memory>
namespace god2 {
namespace {
void require(bool ok,const char* message) {if(!ok)throw DatabaseError(message);}
bool same(const Migration& a,const Migration& b) {
    return a.version==b.version && a.name==b.name && a.sql==b.sql;
}
using Connection=std::unique_ptr<sqlite3,decltype(&sqlite3_close_v2)>;
Connection open(const std::filesystem::path& path) {
    const auto text=path.u8string();sqlite3* raw=nullptr;
    const auto result=sqlite3_open_v2(reinterpret_cast<const char*>(text.c_str()),&raw,
        SQLITE_OPEN_READONLY|SQLITE_OPEN_FULLMUTEX,nullptr);
    Connection owned(raw,sqlite3_close_v2);
    if(result!=SQLITE_OK)throw DatabaseError(raw?sqlite3_errmsg(raw):"Cannot inspect officer migration storage");
    sqlite_detail::check(raw,sqlite3_busy_timeout(raw,5000));return owned;
}
std::string schema51_ddl() {
    // Scratch only: SQLite canonicalizes CREATE SQL independently of whitespace
    // delimiters. Never execute schema statements against the inspected save.
    sqlite3* raw=nullptr;const auto result=sqlite3_open(":memory:",&raw);
    Connection owned(raw,sqlite3_close_v2);
    if(result!=SQLITE_OK)throw DatabaseError("Cannot canonicalize pinned officer DDL");
    sqlite_detail::execute(raw,SqliteOwnedGuildMembershipRepository::officer_schema());
    sqlite_detail::Statement q(raw,"SELECT sql FROM sqlite_master WHERE type='table' AND name='owned_guild_officers_0082'");
    require(q.row(),"Pinned officer DDL missing");auto ddl=q.text(0);
    require(!q.row(),"Pinned officer DDL ambiguous");return ddl;
}
struct Installed {bool table{},history51{};std::size_t count{};};
Installed inspect(sqlite3* raw,const std::vector<Migration>& expected) {
    Installed result;
    std::string actual;
    {
        sqlite_detail::Statement q(raw,"SELECT type,sql FROM sqlite_master WHERE name='owned_guild_officers_0082'");
        if(q.row()) {
            require(q.text(0)=="table","Officer object is not a table");actual=q.text(1);result.table=true;
            require(!q.row(),"Ambiguous officer storage object");
        }
    }
    bool history=false;
    {
        sqlite_detail::Statement q(raw,"SELECT type FROM sqlite_master WHERE name='schema_migrations'");
        if(q.row()) {require(q.text(0)=="table" && !q.row(),"Invalid officer migration history object");history=true;}
    }
    if(history) {
        sqlite_detail::Statement q(raw,"SELECT version,name,sql_text FROM schema_migrations ORDER BY version");
        while(q.row()) {
            require(result.count<expected.size(),"Unknown future officer migration");
            const auto& migration=expected[result.count++];
            require(q.integer(0)==migration.version && q.text(1)==migration.name && q.text(2)==migration.sql,
                "Officer immutable migration prefix mismatch");
            result.history51=migration.version==51;
        }
    }
    require(result.table==result.history51,"Orphan officer table or migration51 history");
    if(result.history51) {
        require(result.count==51,"Officer installed prefix is incomplete");
        static const auto ddl=schema51_ddl();
        require(actual==ddl,"Officer physical schema51 DDL differs; unknown schema extensions unsupported");
        // Exact51 includes all persistent attached metadata, not just the
        // CREATE TABLE text. WITHOUT ROWID's composite PRIMARY KEY creates no
        // sqlite_master autoindex object. Unknown indexes/triggers fail closed;
        // legacy49/50 opaque objects remain outside this new51 check.
        sqlite_detail::Statement objects(raw,
            "SELECT type,name,tbl_name,sql FROM sqlite_master WHERE tbl_name='owned_guild_officers_0082' ORDER BY type,name");
        require(objects.row() && objects.text(0)=="table" &&
            objects.text(1)=="owned_guild_officers_0082" &&
            objects.text(2)=="owned_guild_officers_0082" && objects.text(3)==ddl && !objects.row(),
            "Officer physical schema51 attached metadata differs; unknown schema extensions unsupported");
    }
    return result;
}
}
std::vector<Migration> owned_guild_officer_migrations() {
    auto migrations=owned_guild_announcement_migrations();
    require(migrations.size()==50 && migrations.back().version==50,"Officer requires exact immutable announcement50 prefix");
    migrations.push_back({51,"owned_guild_officers_candidate",SqliteOwnedGuildMembershipRepository::officer_schema()});
    return migrations;
}
void require_exact_guild_officer_migrations(sqlite3* raw,const std::vector<Migration>& migrations) {
    require(raw!=nullptr,"Officer accessor requires initialized SQLite");const auto expected=owned_guild_officer_migrations();
    require(migrations.size()==expected.size(),"Officer accessor requires exact51 migration vector");
    for(std::size_t i=0;i<expected.size();++i)require(same(migrations[i],expected[i]),"Officer accessor migration vector mismatch");
    const auto installed=inspect(raw,expected);
    require(installed.history51,"Officer accessor requires already installed exact51");
}
std::vector<Migration> configured_guild_officer_sqlite_migrations(
    const std::filesystem::path& path,bool announcements_enabled,bool officers_enabled) {
    require(!officers_enabled || announcements_enabled,"Enabled officers require announcement50 gameplay prerequisite");
    // Retain frozen selector's path/NUL/read-only50 checks byte-for-byte.
    auto legacy=configured_sqlite_migrations(path,announcements_enabled);
    const auto officer=owned_guild_officer_migrations();
    if(!std::filesystem::exists(path))return officers_enabled?officer:legacy;
    auto connection=open(path);
    sqlite_detail::execute(connection.get(),"BEGIN");
    const auto installed=inspect(connection.get(),officer);
    if(installed.history51 || officers_enabled)return officer;
    return legacy;
}
}
