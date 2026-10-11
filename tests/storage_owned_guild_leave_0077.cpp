#include "db/SqliteOwnedGuildLeaveRepository.h"
#include "db/SqliteSupport.h"
#include <chrono>
#include <filesystem>
#include <iostream>
#include <limits>
#include <string>
#include <utility>

using namespace god2;
namespace {
unsigned checks=0;
void check(bool value) {++checks;if(!value)throw std::runtime_error("Owned self-leave storage check failed");}
template<class F> void rejects(F operation) {
    bool rejected=false;try {operation();}catch(const DatabaseError&) {rejected=true;}check(rejected);
}
std::int64_t scalar(sqlite3* db,const char* sql) {
    sqlite_detail::Statement query(db,sql);check(query.row());return query.integer(0);
}
std::string rows(sqlite3* db,const char* sql) {
    sqlite_detail::Statement query(db,sql);std::string result;
    while(query.row()) result+=query.text(0)+"\n";
    return result;
}
std::string protected_rows(sqlite3* db) {
    return rows(db,
        "SELECT 'A:'||id||':'||hex(username)||':'||hex(password_hash) FROM accounts "
        "UNION ALL SELECT 'C:'||id||':'||account_id||':'||hex(profile)||':'||hex(name_bytes) FROM recovered_characters "
        "UNION ALL SELECT 'S:'||character_id||':'||hp||':'||mp||':'||xp||':'||map_id||':'||revision FROM saved_fixture ORDER BY 1");
}
std::string guild_rows(sqlite3* db) {
    return rows(db,"SELECT id||':'||hex(name_utf8)||':'||revision||':'||origin||':'||design_id||':'||source_sha256 FROM owned_guilds ORDER BY id");
}
std::string member_rows(sqlite3* db,const char* filter="") {
    const auto sql=std::string("SELECT character_id||':'||guild_id||':'||revision||':'||origin||':'||design_id||':'||source_sha256 FROM owned_guild_members ")+filter+" ORDER BY character_id";
    return rows(db,sql.c_str());
}
std::string all_rows(sqlite3* db) {return protected_rows(db)+guild_rows(db)+member_rows(db);}
struct Connection {
    sqlite3* db=nullptr;
    explicit Connection(const std::string& path=":memory:") {
        if(sqlite3_open(path.c_str(),&db)!=SQLITE_OK) {
            if(db)sqlite3_close(db);db=nullptr;throw std::runtime_error("Cannot open isolated test database");
        }
        sqlite_detail::execute(db,"PRAGMA foreign_keys=ON");
    }
    ~Connection(){if(db)sqlite3_close(db);}
    Connection(const Connection&)=delete;
};
struct Fixture {
    Connection connection;
    SqliteGuildRepository admin{connection.db};
    SqliteOwnedGuildLeaveRepository leave{connection.db};
    std::uint64_t first=0,second=0;
    explicit Fixture(const std::string& path=":memory:") :connection(path) {
        sqlite_detail::execute(connection.db,R"SQL(
CREATE TABLE accounts(id INTEGER PRIMARY KEY,username TEXT,password_hash TEXT);
CREATE TABLE recovered_characters(id INTEGER PRIMARY KEY,account_id INTEGER NOT NULL REFERENCES accounts(id),profile BLOB,name_bytes BLOB);
CREATE TABLE saved_fixture(character_id INTEGER PRIMARY KEY REFERENCES recovered_characters(id),hp INTEGER,mp INTEGER,xp INTEGER,map_id INTEGER,revision INTEGER);
INSERT INTO accounts VALUES(1,'Owner','hash-a'),(2,'Other','hash-b'),(3,'Third','hash-c');
INSERT INTO recovered_characters VALUES(1,1,X'010203',X'41'),(2,1,X'040506',X'42'),(3,2,X'070809',X'43'),(4,2,X'101112',X'44'),(5,3,X'131415',X'45');
INSERT INTO saved_fixture VALUES(1,234,56,789,101,7),(2,345,67,890,102,8),(3,456,78,901,103,9),(4,567,89,123,104,10),(5,678,90,234,105,11);
)SQL");
        sqlite_detail::execute(connection.db,SqliteGuildRepository::schema());
        first=admin.admin_create("Guild");second=admin.admin_create("OtherGuild");
        admin.admin_assign(1,1,first,std::nullopt);admin.admin_assign(1,2,first,std::nullopt);
        admin.admin_assign(2,3,first,std::nullopt);admin.admin_assign(2,4,second,std::nullopt);
    }
    sqlite3* db() const{return connection.db;}
    StoredGuildMembership self(){return *admin.load(1,1);}
    template<class F> void unchanged_failure(F operation) {
        const auto before=all_rows(db());rejects(operation);check(all_rows(db())==before);
        check(sqlite3_get_autocommit(db())==1);
    }
};
}
int main() {
    try {
        rejects([]{SqliteOwnedGuildLeaveRepository invalid(nullptr);});
        Fixture f;
        const auto initial=f.self();
        for(const auto owner:{std::pair{0ULL,1ULL},std::pair{1ULL,0ULL},std::pair{2ULL,1ULL},
                              std::pair{1ULL,3ULL},std::pair{1ULL,99ULL},std::pair{99ULL,1ULL}})
            f.unchanged_failure([&]{f.leave.leave(owner.first,owner.second,initial);});
        f.unchanged_failure([&]{f.leave.leave(3,5,initial);}); // Owned but no membership.
        for(unsigned field=0;field<3;++field) {
            for(const auto invalid:{0ULL,std::numeric_limits<std::uint64_t>::max()}) {
                auto expected=initial;
                if(field==0)expected.guild_id=invalid;
                if(field==1)expected.guild_revision=invalid;
                if(field==2)expected.membership_revision=invalid;
                f.unchanged_failure([&]{f.leave.leave(1,1,expected);});
            }
        }
        auto changed=initial;changed.name_utf8="guild";
        f.unchanged_failure([&]{f.leave.leave(1,1,changed);}); // Exact case, no aliases.
        changed=initial;changed.guild_revision++;
        f.unchanged_failure([&]{f.leave.leave(1,1,changed);});
        changed=initial;changed.membership_revision++;
        f.unchanged_failure([&]{f.leave.leave(1,1,changed);});

        // Full equality rejects a guild generation change even when this
        // member's personal revision and ownership remain exactly the same.
        f.admin.admin_assign(3,5,f.first,std::nullopt);
        check(f.self().membership_revision==initial.membership_revision);
        f.unchanged_failure([&]{f.leave.leave(1,1,initial);});
        auto before=f.self();
        f.admin.admin_assign(1,1,f.second,before.membership_revision);
        f.unchanged_failure([&]{f.leave.leave(1,1,before);}); // Transfer.
        before=f.self();f.admin.admin_remove(1,1,before.membership_revision);
        f.unchanged_failure([&]{f.leave.leave(1,1,before);}); // Removed, not idempotent success.
        f.admin.admin_assign(1,1,f.second,std::nullopt);
        check(f.self().membership_revision>before.membership_revision);
        f.unchanged_failure([&]{f.leave.leave(1,1,before);}); // Remove/rejoin ABA.

        before=f.self();
        sqlite_detail::execute(f.db(),"UPDATE owned_guilds SET name_utf8='Renamed' WHERE id="+std::to_string(f.second));
        f.unchanged_failure([&]{f.leave.leave(1,1,before);}); // Same generations, changed name.
        sqlite_detail::execute(f.db(),"UPDATE owned_guilds SET name_utf8='OtherGuild' WHERE id="+std::to_string(f.second));
        check(f.self()==before);

        // Fault-injected schemas are isolated; no formal database is accessed.
        sqlite_detail::execute(f.db(),"PRAGMA ignore_check_constraints=ON");
        sqlite_detail::execute(f.db(),"UPDATE owned_guild_members SET source_sha256='invalid' WHERE character_id=1");
        f.unchanged_failure([&]{f.leave.leave(1,1,before);});
        sqlite_detail::execute(f.db(),"UPDATE owned_guild_members SET source_sha256='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763' WHERE character_id=1");
        sqlite_detail::execute(f.db(),"UPDATE owned_guilds SET revision=0 WHERE id="+std::to_string(f.second));
        f.unchanged_failure([&]{f.leave.leave(1,1,before);});
        sqlite_detail::execute(f.db(),"UPDATE owned_guilds SET revision="+std::to_string(before.guild_revision)+" WHERE id="+std::to_string(f.second));
        sqlite_detail::execute(f.db(),"PRAGMA ignore_check_constraints=OFF");
        check(f.self()==before);

        for(const auto trigger:{
            "CREATE TRIGGER fail_leave BEFORE DELETE ON owned_guild_members BEGIN SELECT RAISE(ABORT,'injected delete failure'); END",
            "CREATE TRIGGER fail_leave BEFORE UPDATE ON owned_guilds BEGIN SELECT RAISE(ABORT,'injected generation failure'); END",
            "CREATE TRIGGER fail_leave AFTER UPDATE ON owned_guilds BEGIN UPDATE owned_guilds SET name_utf8='Wrong' WHERE id=NEW.id; END",
            "CREATE TRIGGER fail_leave AFTER DELETE ON owned_guild_members BEGIN INSERT INTO owned_guild_members VALUES(OLD.character_id,OLD.guild_id,OLD.revision,OLD.origin,OLD.design_id,OLD.source_sha256); END",
            "CREATE TRIGGER fail_leave AFTER DELETE ON owned_guild_members BEGIN UPDATE owned_guilds SET revision=revision+1 WHERE id=OLD.guild_id; END"}) {
            sqlite_detail::execute(f.db(),trigger);
            f.unchanged_failure([&]{f.leave.leave(1,1,before);});
            sqlite_detail::execute(f.db(),"DROP TRIGGER fail_leave");
        }

        const auto protected_before=protected_rows(f.db());
        const auto unaffected_members=member_rows(f.db(),"WHERE character_id<>1");
        const auto other_guild=rows(f.db(),("SELECT id||':'||hex(name_utf8)||':'||revision||':'||origin||':'||design_id||':'||source_sha256 FROM owned_guilds WHERE id<>"+std::to_string(before.guild_id)+" ORDER BY id").c_str());
        const auto clock=scalar(f.db(),"SELECT max(revision) FROM owned_guilds");
        f.leave.leave(1,1,before);
        check(!f.admin.load(1,1));check(protected_rows(f.db())==protected_before);
        check(member_rows(f.db())==unaffected_members);
        check(rows(f.db(),("SELECT id||':'||hex(name_utf8)||':'||revision||':'||origin||':'||design_id||':'||source_sha256 FROM owned_guilds WHERE id<>"+std::to_string(before.guild_id)+" ORDER BY id").c_str())==other_guild);
        check(scalar(f.db(),("SELECT revision FROM owned_guilds WHERE id="+std::to_string(before.guild_id)).c_str())==clock+1);
        check(scalar(f.db(),"SELECT count(*) FROM owned_guilds")==2);
        f.unchanged_failure([&]{f.leave.leave(1,1,before);});

        // Last-member leave retains the guild and global generation clock.
        Fixture last;
        auto stale=last.self();
        for(const auto owner:{std::pair{1u,1u},std::pair{1u,2u},std::pair{2u,3u}}) {
            const auto snapshot=*last.admin.load(owner.first,owner.second);
            last.leave.leave(owner.first,owner.second,snapshot);
        }
        const auto retained_clock=scalar(last.db(),"SELECT max(revision) FROM owned_guilds");
        check(scalar(last.db(),("SELECT count(*) FROM owned_guild_members WHERE guild_id="+std::to_string(last.first)).c_str())==0);
        check(scalar(last.db(),"SELECT count(*) FROM owned_guilds")==2);
        const auto rejoined=last.admin.admin_assign(1,1,last.first,std::nullopt);
        check(rejoined.membership_revision>static_cast<std::uint64_t>(retained_clock));
        last.unchanged_failure([&]{last.leave.leave(1,1,stale);});

        // Two independent connections to the same file: a second writer
        // invalidates a captured full snapshot, including unchanged member rev.
        const auto path=std::filesystem::temp_directory_path()/
            ("god2-owned-self-leave-0077-"+std::to_string(std::chrono::steady_clock::now().time_since_epoch().count())+".db");
        struct Cleanup {std::filesystem::path path;~Cleanup(){std::error_code e;std::filesystem::remove(path,e);}} cleanup{path};
        {
            Fixture disk(path.string());Connection second(path.string());
            SqliteGuildRepository other_admin(second.db);
            const auto captured=disk.self();
            other_admin.admin_assign(3,5,disk.first,std::nullopt);
            check(disk.self().membership_revision==captured.membership_revision);
            disk.unchanged_failure([&]{disk.leave.leave(1,1,captured);});
            const auto fresh=disk.self();
            const auto protected_disk=protected_rows(disk.db());
            disk.leave.leave(1,1,fresh);
            check(!other_admin.load(1,1));check(protected_rows(second.db)==protected_disk);
            const auto rejoin=other_admin.admin_assign(1,1,disk.first,std::nullopt);
            check(rejoin.membership_revision>fresh.membership_revision);
            disk.unchanged_failure([&]{disk.leave.leave(1,1,fresh);});
            other_admin.admin_assign(1,1,disk.second,rejoin.membership_revision);
            disk.unchanged_failure([&]{disk.leave.leave(1,1,rejoin);});
        }

        // Exhaustion occurs in any retained guild, not merely the one leaving.
        Fixture exhausted;
        const auto expected=exhausted.self();
        sqlite_detail::execute(exhausted.db(),"UPDATE owned_guilds SET revision=9223372036854775807 WHERE id="+std::to_string(exhausted.second));
        exhausted.unchanged_failure([&]{exhausted.leave.leave(1,1,expected);});
        check(exhausted.self()==expected);
        check(scalar(f.db(),"SELECT count(*) FROM pragma_foreign_key_check")==0);
        check(scalar(last.db(),"SELECT count(*) FROM pragma_foreign_key_check")==0);
        std::cout<<"PASS "<<checks<<" owned self-leave ownership/full-snapshot/CAS/rollback/durability/preservation checks\n";
        return 0;
    }catch(const std::exception& error) {std::cerr<<error.what()<<'\n';return 1;}
}
