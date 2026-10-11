#include "db/SqliteOwnedGuildAnnouncementRepository.h"
#include "db/SqliteRecoveredCharacterRepository.h"
#include "db/SqliteMigrationManager.h"
#include "db/SqliteSupport.h"
#include <algorithm>
#include <chrono>
#include <filesystem>
#include <iostream>
#include <source_location>
#include <vector>

namespace announcement_test {
using Member=god2::SqliteOwnedGuildMembershipRepository;
using Repo=god2::SqliteOwnedGuildAnnouncementRepository;
using god2::sqlite_detail::execute;
unsigned checks=0;
void check(bool value,const std::source_location at=std::source_location::current()) {
    ++checks;if(!value)throw std::runtime_error("Announcement storage check "+std::to_string(checks)+" line "+std::to_string(at.line()));
}
template<class F> void rejects(F action,const std::source_location at=std::source_location::current()) {
    bool rejected=false;try{action();}catch(const god2::DatabaseError&){rejected=true;}check(rejected,at);
}
// Independent typed database oracle: retain type names, bytes, and duplicate
// rows, plus all schema. This does not rely on either repository's private guard.
std::vector<std::string> state(sqlite3* db,const std::string& skip={}) {
    std::vector<std::string> result;
    god2::sqlite_detail::Statement schema(db,"SELECT type,name,tbl_name,COALESCE(sql,'') FROM sqlite_master ORDER BY type,name");
    while(schema.row())for(int c=0;c<4;++c)result.push_back("schema:"+schema.text(c));
    god2::sqlite_detail::Statement tables(db,"SELECT name FROM sqlite_master WHERE type='table' ORDER BY name");
    while(tables.row()) {
        const auto name=tables.text(0);if(name==skip)continue;
        std::string quoted="\"";for(const auto c:name){quoted+=c;if(c=='\"')quoted+=c;}quoted+='\"';
        sqlite3_stmt* q=nullptr;god2::sqlite_detail::check(db,sqlite3_prepare_v2(db,("SELECT * FROM "+quoted).c_str(),-1,&q,nullptr));
        struct Done{sqlite3_stmt* q;~Done(){sqlite3_finalize(q);}} done{q};
        std::vector<std::string> rows;int rc;
        while((rc=sqlite3_step(q))==SQLITE_ROW) {
            std::string row=name+":";
            for(int c=0;c<sqlite3_column_count(q);++c) {
                const auto type=sqlite3_column_type(q,c);row+=std::to_string(type)+":";
                if(type==SQLITE_NULL)continue;
                const auto size=sqlite3_column_bytes(q,c);const auto* data=static_cast<const char*>(sqlite3_column_blob(q,c));
                row+=std::to_string(size)+":";if(size)row.append(data,static_cast<std::size_t>(size));
            }
            rows.push_back(std::move(row));
        }
        if(rc!=SQLITE_DONE)throw std::runtime_error("Independent database oracle failed");
        std::sort(rows.begin(),rows.end());result.insert(result.end(),rows.begin(),rows.end());
    }
    return result;
}
struct Fixture {
    sqlite3* db=nullptr;
    Member::Policy policy{50000,30,20};
    Member::Proof proof{[]{},[]{}}; // TEST_ONLY world readiness, no ports/session permissions.
    Member::Leader leader;
    std::uint64_t guild{};
    explicit Fixture(const std::string& path=":memory:",bool utf16=false) {
        check(sqlite3_open(path.c_str(),&db)==SQLITE_OK);execute(db,"PRAGMA foreign_keys=ON");
        if(utf16)execute(db,"PRAGMA encoding='UTF-16be'");
        auto migrations=god2::default_sqlite_migrations();check(migrations.size()==49);
        
        god2::SqliteMigrationManager(db,migrations).migrate();god2::SqliteTradeRepository(db).install_schema();
        execute(db,Repo::schema()); // Explicit test-only schema proposal, not migration50.
        for(unsigned i=1;i<=4;++i) {
            god2::sqlite_detail::Statement a(db,"INSERT INTO accounts(id,username,password_hash) VALUES(?,?,'TEST_ONLY_NOT_LOGIN')");
            a.bind(1,i);a.bind(2,"AnnAccount"+std::to_string(i));a.done();
            const auto name="AnnPlayer"+std::to_string(i);const std::vector<std::uint8_t> bytes(name.begin(),name.end());
            std::array<std::uint8_t,40> profile{};std::copy(bytes.begin(),bytes.end(),profile.begin());profile[29]=1;
            god2::sqlite_detail::Statement c(db,"INSERT INTO recovered_characters(id,account_id,slot,profile,name_bytes,name_codepage) VALUES(?,?,0,?,?,0)");
            c.bind(1,i);c.bind(2,i);c.bind_blob(3,profile);c.bind_blob(4,bytes);c.done();
            god2::RecoveredRoleLevel::Bytes role{};role[0]=0x22;role[1]=35;role[17]=100;role[21]=50;
            god2::sqlite_detail::Statement r(db,"INSERT INTO character_role_snapshots(character_id,logical,revision,design_id) VALUES(?,?,1,'CUSTOM-0013')");
            r.bind(1,i);r.bind_blob(2,role);r.done();
            god2::sqlite_detail::Statement w(db,"INSERT INTO character_trade_wallets(character_id,amount,revision,design_id) VALUES(?,100000,1,'CUSTOM-0063')");
            w.bind(1,i);w.done();
            god2::SqliteRecoveredCharacterRepository(db).commit_resources(i,i,{}, {100,100,50,50,0,"CUSTOM-0012"});
        }
        Member members(db);god2::SqliteTradeRepository money(db);
        guild=members.create(members.nonmember(1,1),*money.load_wallet(1,1),"AnnGuild",policy,proof).leader.governance.guild_id;
        const auto application=members.apply(members.nonmember(2,2),members.guild(guild),proof);
        members.approve(members.leader(1,1),application,proof);leader=members.leader(1,1);
        members.apply(members.nonmember(3,3),members.guild(guild),proof);
        execute(db,"CREATE TABLE unknown_save(v,blob BLOB,text TEXT);INSERT INTO unknown_save VALUES(NULL,X'00017F','unchanged');"
                   "INSERT INTO unknown_save VALUES(1.25,X'', '');INSERT INTO unknown_save SELECT * FROM unknown_save;");
    }
    ~Fixture(){if(db)sqlite3_close(db);}
    Repo repo(){return Repo(db);}
    template<class F> void failed(F action,const std::source_location at=std::source_location::current()) {
        const auto before=state(db);rejects(action,at);check(state(db)==before,at);check(sqlite3_get_autocommit(db)==1,at);
    }
    Repo::Snapshot save(const Repo::Snapshot& before,const std::string& text) {return repo().save(leader,before,text,proof);}
};
void lifecycle(bool utf16) {
    Fixture f(":memory:",utf16);rejects([]{Repo bad(nullptr);});
    auto absent=f.repo().load(f.guild);check(absent==Repo::Snapshot{f.guild,{}});
    const auto untouched=state(f.db,"owned_guild_announcements_0078");
    auto first=f.save(absent,"  洞府公告 100%  ");check(first.value==Repo::Value{"  洞府公告 100%  ",1});
    check(f.repo().load(f.guild)==first);check(state(f.db,"owned_guild_announcements_0078")==untouched);
    f.failed([&]{f.save(absent,"stale");});
    auto cleared=f.save(first,"");check(cleared.value==Repo::Value{"",2});
    f.failed([&]{f.save(first,"stale after clear");});f.failed([&]{f.save(absent,"absent ABA");});
    auto same=f.save(cleared,"");check(same.value==Repo::Value{"",3});
    auto maximum=f.save(same,std::string(1040,'x'));check(maximum.value->text_utf8.size()==1040);
    f.failed([&]{f.save(maximum,std::string(1041,'x'));});
    std::string chinese;for(unsigned i=0;i<520;++i)chinese+="中";
    auto dual=f.save(maximum,chinese);check(dual.value->text_utf8==chinese);
    f.failed([&]{f.save(dual,chinese+"中");});
    for(const auto text:{std::string("bad\0text",8),std::string("\n"),std::string("\r"),std::string("\t"),std::string(1,'\x7f'),std::string("😀"),std::string("\xff")})
        f.failed([&]{f.save(dual,text);});
    rejects([&]{f.repo().load(0);});rejects([&]{f.repo().load(999);});
    for(const auto proof:{Member::Proof{},Member::Proof{[]{},{}},Member::Proof{{},[]{}}})
        f.failed([&]{f.repo().save(f.leader,dual,"wrong",proof);});
    const auto fail=[]{throw god2::DatabaseError("TEST_ONLY world proof failure");};
    f.failed([&]{f.repo().save(f.leader,dual,"wrong",{fail,[]{}});});
    f.failed([&]{f.repo().save(f.leader,dual,"wrong",{[]{},fail});});
    auto stale=dual;stale.value->revision++;f.failed([&]{f.save(stale,"wrong");});
    stale=dual;stale.value->text_utf8="changed";f.failed([&]{f.save(stale,"wrong");});
    stale=dual;stale.guild_id=999;f.failed([&]{f.save(stale,"wrong");});
    auto forged=f.leader;forged.identity.account_id=2;forged.identity.character_id=2;
    f.failed([&]{f.repo().save(forged,dual,"ordinary member",f.proof);});
    forged=f.leader;forged.identity=Member(f.db).identity(4,4);
    f.failed([&]{f.repo().save(forged,dual,"foreign",f.proof);});
    forged=f.leader;forged.roster.pop_back();f.failed([&]{f.repo().save(forged,dual,"partial roster",f.proof);});
    forged=f.leader;forged.governance.capacity++;f.failed([&]{f.repo().save(forged,dual,"stale governance",f.proof);});
    forged=f.leader;forged.identity.role->revision++;f.failed([&]{f.repo().save(forged,dual,"stale role",f.proof);});
    check(state(f.db,"owned_guild_announcements_0078")==untouched);
}
void authority_and_overflow() {
    Fixture f;auto empty=f.repo().load(f.guild);
    god2::SqliteRecoveredCharacterRepository characters(f.db);const auto resources=characters.load_resources(1,1);check(resources.has_value());
    check(characters.reserve_battle(1,1,*resources)>0);check(characters.owned_pending_battle(1,1));
    const auto snapshot=Member(f.db).governance_snapshot(1,1);check(snapshot==f.leader);
    check(f.repo().load(f.guild)==empty);f.failed([&]{f.repo().save(snapshot,empty,"battle unauthorized",f.proof);});
    // A nonfounder battle is unrelated to the founder's announcement authority.
    Fixture ordinary;const auto r=god2::SqliteRecoveredCharacterRepository(ordinary.db).load_resources(2,2);check(r.has_value());
    check(god2::SqliteRecoveredCharacterRepository(ordinary.db).reserve_battle(2,2,*r)>0);
    auto saved=ordinary.save(ordinary.repo().load(ordinary.guild),"allowed founder");check(saved.value->revision==1);
    execute(ordinary.db,"UPDATE owned_guild_announcements_0078 SET revision=9223372036854775807");
    const auto overflow=ordinary.repo().load(ordinary.guild);ordinary.failed([&]{ordinary.save(overflow,"overflow");});
    execute(ordinary.db,"PRAGMA ignore_check_constraints=ON;UPDATE owned_guild_announcements_0078 SET source_sha256='bad'");
    ordinary.failed([&]{ordinary.repo().load(ordinary.guild);});
    Fixture broken;execute(broken.db,"PRAGMA ignore_check_constraints=ON;UPDATE owned_guild_governance_0078 SET source_sha256='bad'");
    broken.failed([&]{broken.repo().load(broken.guild);});
}
void guards_and_extensions() {
    for(const bool existing:{false,true}) {
        Fixture f;execute(f.db,"ALTER TABLE owned_guild_announcements_0078 ADD COLUMN future_blob BLOB DEFAULT X'00127F';"
                              "ALTER TABLE owned_guild_announcements_0078 ADD COLUMN future_text TEXT DEFAULT 'retained';"
                              "ALTER TABLE owned_guild_announcements_0078 ADD COLUMN future_float DEFAULT 1.25");
        auto before=f.repo().load(f.guild);if(existing)before=f.save(before,"original");
        for(const auto event:{"BEFORE","AFTER"}) {
            const std::string action=existing?"UPDATE":"INSERT";
            const auto trigger="CREATE TRIGGER fault "+std::string(event)+" "+action+" ON owned_guild_announcements_0078 BEGIN ";
            for(const auto effect:{
                "SELECT RAISE(ABORT,'TEST_ONLY rejected');",
                "SELECT RAISE(IGNORE);",
                "UPDATE unknown_save SET blob=X'12';",
                "UPDATE character_trade_wallets SET amount=0 WHERE character_id=2;",
                "UPDATE accounts SET password_hash='bad' WHERE id=4;",
                "UPDATE character_role_snapshots SET revision=revision+1 WHERE character_id=2;",
                "UPDATE owned_guild_governance_0078 SET capacity=capacity-1;",
                "UPDATE owned_guilds SET revision=revision+1;"
            }) {
                // SQLite AFTER RAISE(IGNORE) does not cancel the completed row
                // mutation. It is harmless here; qualify it separately below.
                if(std::string(event)=="AFTER" && std::string(effect)=="SELECT RAISE(IGNORE);")continue;
                execute(f.db,trigger+effect+" END");bool after=false;
                f.failed([&]{f.repo().save(f.leader,before,"write",{[]{},[&]{after=true;}});});check(!after);
                execute(f.db,"DROP TRIGGER fault");
            }
        }
        const auto action=existing?"UPDATE":"INSERT";
        for(const auto effect:{
            "UPDATE owned_guild_announcements_0078 SET text_utf8='rewritten' WHERE guild_id=NEW.guild_id;",
            "UPDATE owned_guild_announcements_0078 SET revision=revision+1 WHERE guild_id=NEW.guild_id;",
            "UPDATE owned_guild_announcements_0078 SET future_blob=X'FFFF' WHERE guild_id=NEW.guild_id;",
            "UPDATE owned_guild_announcements_0078 SET future_text='changed' WHERE guild_id=NEW.guild_id;",
            "UPDATE owned_guild_announcements_0078 SET future_float='1.25' WHERE guild_id=NEW.guild_id;",
            "DELETE FROM owned_guild_announcements_0078 WHERE guild_id=NEW.guild_id;"
        }) {
            execute(f.db,"CREATE TRIGGER fault AFTER "+std::string(action)+" ON owned_guild_announcements_0078 BEGIN "+effect+" END");
            bool after=false;f.failed([&]{f.repo().save(f.leader,before,"write",{[]{},[&]{after=true;}});});check(!after);execute(f.db,"DROP TRIGGER fault");
        }
        for(const bool pre:{false,true})for(const auto mutation:{
            "UPDATE unknown_save SET v=CAST(v AS TEXT) WHERE v IS NOT NULL",
            "INSERT INTO unknown_save SELECT * FROM unknown_save LIMIT 1",
            "CREATE TABLE malicious_schema(extra)",
            "CREATE TRIGGER future_trigger AFTER INSERT ON unknown_save BEGIN SELECT 1; END",
            "CREATE INDEX future_index ON unknown_save(text)",
            "UPDATE recovered_characters SET name_codepage=936 WHERE id=3"
        }) {
            const auto change=[&]{execute(f.db,mutation);};
            f.failed([&]{f.repo().save(f.leader,before,"write",pre?Member::Proof{change,[]{}}:Member::Proof{[]{},change});});
        }
        if(existing)for(const bool pre:{false,true}) {
            const auto change=[&]{execute(f.db,"UPDATE owned_guild_announcements_0078 SET future_blob=X'01'");};
            f.failed([&]{f.repo().save(f.leader,before,"write",pre?Member::Proof{change,[]{}}:Member::Proof{[]{},change});});
        }
        auto after=f.save(before,"preserved extensions");check(after.value->text_utf8=="preserved extensions");
        god2::sqlite_detail::Statement q(f.db,"SELECT hex(future_blob),future_text,typeof(future_float) FROM owned_guild_announcements_0078");
        check(q.row());check(q.text(0)=="00127F" && q.text(1)=="retained" && q.text(2)=="real");
    }
    {
        Fixture ignored;const auto before=ignored.repo().load(ignored.guild);
        execute(ignored.db,"CREATE TRIGGER ignored AFTER INSERT ON owned_guild_announcements_0078 BEGIN SELECT RAISE(IGNORE); END");
        const auto after=ignored.save(before,"safe ignored tail");check(after.value==Repo::Value{"safe ignored tail",1});
    }
    // A trigger tampering with a different guild's announcement is unrelated DML.
    Fixture f;Member members(f.db);god2::SqliteTradeRepository money(f.db);
    const auto foreign=members.create(members.nonmember(4,4),*money.load_wallet(4,4),"ForeignGuild",f.policy,f.proof).leader;
    f.repo().save(foreign,f.repo().load(foreign.governance.guild_id),"foreign",f.proof);
    auto before=f.repo().load(f.guild);
    execute(f.db,"CREATE TRIGGER fault AFTER INSERT ON owned_guild_announcements_0078 BEGIN UPDATE owned_guild_announcements_0078 SET text_utf8='wrong' WHERE guild_id<>NEW.guild_id; END");
    f.failed([&]{f.save(before,"write");});
}
void connection_conflict_and_persistence() {
    const auto path=std::filesystem::temp_directory_path()/("god2-ann78-"+std::to_string(std::chrono::steady_clock::now().time_since_epoch().count())+".db");
    struct Cleanup{std::filesystem::path path;~Cleanup(){std::error_code ec;std::filesystem::remove(path,ec);}} cleanup{path};
    Repo::Snapshot committed;
    {
        Fixture f(path.string());auto first=f.repo().load(f.guild);
        sqlite3* other=nullptr;check(sqlite3_open(path.string().c_str(),&other)==SQLITE_OK);
        struct Done{sqlite3* db;~Done(){sqlite3_close(db);}} done{other};execute(other,"PRAGMA foreign_keys=ON");
        const auto leader=Member(other).leader(1,1);const auto stale=Repo(other).load(f.guild);
        // Real two-connection reserved writer conflict; no network or gameplay load.
        execute(other,"BEGIN IMMEDIATE");f.failed([&]{f.save(first,"busy writer");});execute(other,"ROLLBACK");
        committed=f.save(first,"winner");rejects([&]{Repo(other).save(leader,stale,"stale loser",f.proof);});
        check(Repo(other).load(f.guild)==committed);
    }
    sqlite3* reopened=nullptr;check(sqlite3_open(path.string().c_str(),&reopened)==SQLITE_OK);
    struct Done{sqlite3* db;~Done(){sqlite3_close(db);}} done{reopened};check(Repo(reopened).load(committed.guild_id)==committed);
}
}
int main() {
    try {
        using namespace announcement_test;
        lifecycle(false);lifecycle(true);authority_and_overflow();guards_and_extensions();connection_conflict_and_persistence();
        std::cout<<"PASS "<<checks<<" announcement storage authority/CAS/typed-preservation checks\n";return 0;
    }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
