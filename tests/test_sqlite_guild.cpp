#include "db/SqliteGuildRepository.h"
#include "db/SqliteSupport.h"
#include "text/LegacyChineseCodec.h"
#include <chrono>
#include <filesystem>
#include <iostream>
#include <limits>
#include <string>

using namespace god2;
namespace {
unsigned checks=0;
void check(bool value) {++checks;if(!value)throw std::runtime_error("Owned guild storage check failed");}
template<class F> void rejects(F operation) {
    bool failed=false;try {operation();}catch(const DatabaseError&) {failed=true;}check(failed);
}
std::string protected_rows(sqlite3* db) {
    sqlite_detail::Statement query(db,
        "SELECT 'A',id,username||':'||password_hash FROM accounts UNION ALL "
        "SELECT 'C',id,account_id||':'||hex(profile)||':'||hex(name_bytes) FROM recovered_characters UNION ALL "
        "SELECT 'S',character_id,hp||':'||mp||':'||xp||':'||map_id||':'||revision FROM saved_fixture ORDER BY 1,2");
    std::string result;
    while(query.row())result+=query.text(0)+std::to_string(query.integer(1))+query.text(2)+"\n";
    return result;
}
std::int64_t scalar(sqlite3* db,const char* sql) {
    sqlite_detail::Statement query(db,sql);check(query.row());return query.integer(0);
}
}
int main() {
    sqlite3* db=nullptr;
    if(sqlite3_open(":memory:",&db)!=SQLITE_OK)return 2;
    int result=0;
    try {
        sqlite_detail::execute(db,R"SQL(
PRAGMA foreign_keys=ON;
CREATE TABLE accounts(id INTEGER PRIMARY KEY,username TEXT,password_hash TEXT);
CREATE TABLE recovered_characters(id INTEGER PRIMARY KEY,account_id INTEGER REFERENCES accounts(id),profile BLOB,name_bytes BLOB);
CREATE TABLE saved_fixture(character_id INTEGER PRIMARY KEY REFERENCES recovered_characters(id),hp INTEGER,mp INTEGER,xp INTEGER,map_id INTEGER,revision INTEGER);
INSERT INTO accounts VALUES(1,'Owner','hash-a'),(2,'Other','hash-b');
INSERT INTO recovered_characters VALUES(1,1,X'010203',X'41'),(2,1,X'040506',X'42'),(3,2,X'070809',X'43');
INSERT INTO saved_fixture VALUES(1,234,56,789,101,7),(2,345,67,890,102,8),(3,456,78,901,103,9);
)SQL");
        const auto protected_before=protected_rows(db);
        sqlite_detail::execute(db,SqliteGuildRepository::schema());
        SqliteGuildRepository repository(db);
        rejects([]{SqliteGuildRepository invalid(nullptr);});
        check(!repository.load(1,1) && !repository.load(1,2) && !repository.load(2,3));
        for(const auto& owner:{std::pair{0u,1u},std::pair{1u,0u},std::pair{2u,1u},std::pair{1u,3u},std::pair{1u,99u}})
            rejects([&]{repository.load(owner.first,owner.second);});
        const auto guild=repository.admin_create("Guild");
        check(guild>0);
        const auto lower=repository.admin_create("guild");
        check(lower!=guild); // Exact binary spelling; no forced lowercasing.
        rejects([&]{repository.admin_create("Guild");});
        for(const auto& name:{std::string{},std::string(16,'A'),std::string("A\0B",3),std::string("100%"),
                             std::string("\xff",1),std::string("\xf0\x9f\x90\x82",4),
                             std::string("\xe4\xb8\x93",3)})
            rejects([&]{repository.admin_create(name);});
        const std::string chinese="\xe4\xbb\x99\xe7\x95\x8c"; // 仙界, lossless CP950/936.
        for(bool simplified:{false,true})check(LegacyChineseCodec::decode(LegacyChineseCodec::encode(chinese,simplified),simplified)==chinese);
        const auto chinese_guild=repository.admin_create(chinese);
        check(chinese_guild!=guild && chinese_guild!=lower);
        const auto max_name=repository.admin_create("ABCDEFGHIJKLMNO");
        check(max_name>0);
        const auto initial=repository.admin_assign(1,1,guild,std::nullopt);
        check(initial.guild_id==guild && initial.name_utf8=="Guild" && initial.membership_revision>0 &&
              initial.membership_revision==initial.guild_revision);
        check(repository.load(1,1)==std::optional(initial));
        check(repository.admin_assign(1,1,guild,initial.membership_revision)==initial);
        rejects([&]{repository.admin_assign(1,1,guild,std::nullopt);});
        for(const auto revision:{0ULL,initial.membership_revision+1,std::numeric_limits<std::uint64_t>::max()})
            rejects([&]{repository.admin_assign(1,1,guild,revision);});
        for(const auto& owner:{std::pair{2u,1u},std::pair{1u,3u},std::pair{1u,99u},std::pair{0u,1u}}) {
            rejects([&]{repository.admin_assign(owner.first,owner.second,guild,std::nullopt);});
            rejects([&]{repository.admin_remove(owner.first,owner.second,initial.membership_revision);});
        }
        rejects([&]{repository.admin_assign(1,2,0,std::nullopt);});
        rejects([&]{repository.admin_assign(1,2,99999,std::nullopt);});
        check(!repository.load(1,2));
        const auto sibling=repository.admin_assign(1,2,guild,std::nullopt);
        const auto before_transfer=*repository.load(1,1);
        check(before_transfer.membership_revision==initial.membership_revision &&
              before_transfer.guild_revision==sibling.guild_revision && sibling.membership_revision>initial.membership_revision);
        const auto foreign=repository.admin_assign(2,3,lower,std::nullopt);
        check(foreign.guild_id==lower);
        // Moving one member advances both affected guild generations, never
        // changes another member's ownership or personal CAS generation.
        const auto transferred=repository.admin_assign(1,1,chinese_guild,initial.membership_revision);
        check(transferred.name_utf8==chinese && transferred.membership_revision>sibling.membership_revision);
        const auto sibling_after=*repository.load(1,2);
        check(sibling_after.guild_id==guild && sibling_after.membership_revision==sibling.membership_revision &&
              sibling_after.guild_revision==transferred.guild_revision);
        check(repository.load(2,3)==std::optional(foreign));
        rejects([&]{repository.admin_remove(1,1,initial.membership_revision);});
        rejects([&]{repository.admin_remove(1,1,0);});
        repository.admin_remove(1,1,transferred.membership_revision);
        check(!repository.load(1,1));
        rejects([&]{repository.admin_remove(1,1,transferred.membership_revision);});
        const auto rejoined=repository.admin_assign(1,1,lower,std::nullopt);
        check(rejoined.membership_revision>transferred.membership_revision);
        rejects([&]{repository.admin_assign(1,1,guild,initial.membership_revision);});
        rejects([&]{repository.admin_remove(1,1,initial.membership_revision);});
        // The clock survives an empty guild and protects stale remove/rejoin
        // operations even when the replacement joins a different guild.
        check(scalar(db,"SELECT count(*) FROM owned_guilds")==4);
        rejects([&]{sqlite_detail::execute(db,"DELETE FROM owned_guilds WHERE id="+std::to_string(chinese_guild));});
        const auto max_before=scalar(db,"SELECT max(revision) FROM owned_guilds");
        const auto state_before=*repository.load(1,1);
        sqlite_detail::execute(db,"CREATE TRIGGER reject_member_update BEFORE UPDATE ON owned_guild_members BEGIN SELECT RAISE(ABORT,'injected failure'); END");
        rejects([&]{repository.admin_assign(1,1,guild,state_before.membership_revision);});
        check(repository.load(1,1)==std::optional(state_before));
        check(scalar(db,"SELECT max(revision) FROM owned_guilds")==max_before);
        sqlite_detail::execute(db,"DROP TRIGGER reject_member_update");
        sqlite_detail::execute(db,"CREATE TRIGGER reject_member_delete BEFORE DELETE ON owned_guild_members BEGIN SELECT RAISE(ABORT,'injected failure'); END");
        rejects([&]{repository.admin_remove(1,1,state_before.membership_revision);});
        check(repository.load(1,1)==std::optional(state_before));
        check(scalar(db,"SELECT max(revision) FROM owned_guilds")==max_before);
        sqlite_detail::execute(db,"DROP TRIGGER reject_member_delete");
        // Readback failure after a trigger rewrites otherwise valid data rolls
        // back both guild generations and the entire member reassignment.
        sqlite_detail::execute(db,"CREATE TRIGGER change_guild_name AFTER UPDATE ON owned_guilds BEGIN UPDATE owned_guilds SET name_utf8='Unexpected' WHERE id=NEW.id; END");
        rejects([&]{repository.admin_assign(1,1,guild,state_before.membership_revision);});
        check(repository.load(1,1)==std::optional(state_before));
        check(scalar(db,"SELECT max(revision) FROM owned_guilds")==max_before);
        sqlite_detail::execute(db,"DROP TRIGGER change_guild_name");
        // Schema rejects foreign/dangling identities and unlabelled storage.
        rejects([&]{sqlite_detail::execute(db,"UPDATE owned_guild_members SET guild_id=99999 WHERE character_id=1");});
        rejects([&]{sqlite_detail::execute(db,"UPDATE owned_guild_members SET revision=0 WHERE character_id=1");});
        rejects([&]{sqlite_detail::execute(db,"UPDATE owned_guild_members SET origin='NATIVE_VERIFIED' WHERE character_id=1");});
        rejects([&]{sqlite_detail::execute(db,"UPDATE owned_guilds SET design_id='CUSTOM-0000' WHERE id=1");});
        sqlite_detail::execute(db,"UPDATE owned_guilds SET name_utf8='1234567890123456' WHERE id="+std::to_string(lower));
        rejects([&]{repository.load(1,1);});
        sqlite_detail::execute(db,"UPDATE owned_guilds SET name_utf8='guild' WHERE id="+std::to_string(lower));
        check(repository.load(1,1)==std::optional(state_before));
        check(protected_rows(db)==protected_before);
        // Reopen a real isolated SQLite file: membership and CAS generations
        // are durable, including read-only reopening. No production DB used.
        const auto path=std::filesystem::temp_directory_path()/
            ("god2-owned-guild-"+std::to_string(std::chrono::steady_clock::now().time_since_epoch().count())+".db");
        struct Cleanup {std::filesystem::path path;~Cleanup(){std::error_code error;std::filesystem::remove(path,error);}} cleanup{path};
        sqlite3* disk=nullptr;check(sqlite3_open(path.string().c_str(),&disk)==SQLITE_OK);
        auto* backup=sqlite3_backup_init(disk,"main",db,"main");check(backup!=nullptr);
        check(sqlite3_backup_step(backup,-1)==SQLITE_DONE);check(sqlite3_backup_finish(backup)==SQLITE_OK);
        check(sqlite3_close(disk)==SQLITE_OK);disk=nullptr;
        check(sqlite3_open_v2(path.string().c_str(),&disk,SQLITE_OPEN_READONLY,nullptr)==SQLITE_OK);
        {
            SqliteGuildRepository reopened(disk);
            check(reopened.load(1,1)==std::optional(state_before));
            rejects([&]{reopened.admin_remove(1,1,state_before.membership_revision);});
            check(protected_rows(disk)==protected_before);
        }
        check(sqlite3_close(disk)==SQLITE_OK);
        // Global revision exhaustion fails without partial membership/guild
        // changes. Idempotent same-guild retry remains harmless at the cap.
        sqlite_detail::execute(db,"UPDATE owned_guilds SET revision=9223372036854775807 WHERE id="+std::to_string(max_name));
        rejects([&]{repository.admin_create("Exhausted");});
        rejects([&]{repository.admin_assign(1,1,guild,state_before.membership_revision);});
        rejects([&]{repository.admin_remove(1,1,state_before.membership_revision);});
        check(repository.admin_assign(1,1,lower,state_before.membership_revision)==state_before);
        check(protected_rows(db)==protected_before);
        check(scalar(db,"SELECT count(*) FROM pragma_foreign_key_check")==0);
        std::cout<<"PASS "<<checks<<" owned guild ownership/CAS/encoding/rollback/reopen/save-preservation checks\n";
    }catch(const std::exception& error) {std::cerr<<error.what()<<'\n';result=1;}
    sqlite3_close(db);return result;
}
