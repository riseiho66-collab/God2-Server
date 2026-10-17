#include "db/SqliteOwnedGuildMembershipRepository.h"
#include "db/SqliteOwnedGuildAnnouncementRepository.h"
#include "db/SqliteRecoveredCharacterRepository.h"
#include "db/SqliteMigrationManager.h"
#include "db/SqliteSupport.h"
#include <algorithm>
#include <array>
#include <bit>
#include <chrono>
#include <filesystem>
#include <iostream>
#include <limits>
#include <map>
#include <memory>
#include <random>
#include <source_location>

namespace {
using namespace god2;
using Repo=SqliteOwnedGuildMembershipRepository;
using Rows=std::vector<std::vector<std::uint8_t>>;
using Snapshot=std::map<std::string,Rows>;
using Exclusions=std::map<std::string,std::string>;
unsigned checks=0;
void check(bool value,const std::source_location at=std::source_location::current()) {
    ++checks;if(!value)throw std::runtime_error("Guild disband0081 storage line "+std::to_string(at.line()));
}
void number(std::vector<std::uint8_t>& row,std::uint64_t value) {
    for(unsigned i=0;i<8;++i)row.push_back(static_cast<std::uint8_t>(value>>(8*i)));
}
std::string quote(const std::string& name) {
    std::string value="\"";for(const auto c:name){value+=c;if(c=='\"')value+=c;}return value+'\"';
}
// Independent oracle, including types, all bytes, duplicate rows and all schema.
// Never use the implementation's guard as its own expected result.
Snapshot snapshot(sqlite3* db,const Exclusions& exclusions={}) {
    Snapshot result;
    sqlite_detail::Statement schema(db,"SELECT type,name,tbl_name,COALESCE(sql,'') FROM sqlite_master ORDER BY type,name");
    while(schema.row()) {
        std::vector<std::uint8_t> row;
        for(int c=0;c<4;++c){const auto text=schema.text(c);number(row,text.size());row.insert(row.end(),text.begin(),text.end());}
        result[":schema"].push_back(std::move(row));
    }
    sqlite_detail::Statement tables(db,"SELECT name FROM sqlite_master WHERE type='table' ORDER BY name");
    while(tables.row()) {
        const auto name=tables.text(0);const auto exclude=exclusions.find(name);
        const auto sql="SELECT * FROM "+quote(name)+(exclude==exclusions.end()?"":" WHERE "+exclude->second);
        sqlite3_stmt* q=nullptr;check(sqlite3_prepare_v2(db,sql.c_str(),-1,&q,nullptr)==SQLITE_OK);
        std::unique_ptr<sqlite3_stmt,decltype(&sqlite3_finalize)> query(q,sqlite3_finalize);
        auto& rows=result[name];int rc=SQLITE_OK;
        while((rc=sqlite3_step(q))==SQLITE_ROW) {
            std::vector<std::uint8_t> row;
            for(int c=0;c<sqlite3_column_count(q);++c) {
                const auto type=sqlite3_column_type(q,c);row.push_back(static_cast<std::uint8_t>(type));
                if(type==SQLITE_INTEGER)number(row,std::bit_cast<std::uint64_t>(sqlite3_column_int64(q,c)));
                else if(type==SQLITE_FLOAT)number(row,std::bit_cast<std::uint64_t>(sqlite3_column_double(q,c)));
                else if(type==SQLITE_TEXT || type==SQLITE_BLOB) {
                    const auto size=sqlite3_column_bytes(q,c);number(row,static_cast<std::uint64_t>(size));
                    const auto* data=type==SQLITE_TEXT?sqlite3_column_text(q,c):static_cast<const unsigned char*>(sqlite3_column_blob(q,c));
                    if(size)row.insert(row.end(),data,data+size);
                }
            }
            rows.push_back(std::move(row));
        }
        check(rc==SQLITE_DONE);std::sort(rows.begin(),rows.end());
    }
    return result;
}
std::int64_t scalar(sqlite3* db,const char* sql) {
    sqlite_detail::Statement q(db,sql);check(q.row());return q.integer(0);
}
struct Fixture {
    sqlite3* db=nullptr;
    std::unique_ptr<Repo> repo;
    std::unique_ptr<SqliteGuildRepository> memberships;
    std::unique_ptr<SqliteTradeRepository> money;
    std::uint64_t guild{},foreign{};
    const Repo::Proof proof{[]{},[]{}}; // TEST_ONLY world readiness, no gameplay authority minted.
    explicit Fixture(const std::string& path=":memory:",bool utf16=false,bool simplified=false,bool opaque=true) {
        check(sqlite3_open(path.c_str(),&db)==SQLITE_OK);sqlite_detail::execute(db,"PRAGMA foreign_keys=ON");
        if(utf16)sqlite_detail::execute(db,"PRAGMA encoding='UTF-16be'");
        const auto migrations=owned_guild_announcement_migrations();check(migrations.size()==50);
        SqliteMigrationManager(db,migrations).migrate();check(scalar(db,"SELECT max(version) FROM schema_migrations")==50);
        repo=std::make_unique<Repo>(db);memberships=std::make_unique<SqliteGuildRepository>(db);
        money=std::make_unique<SqliteTradeRepository>(db);money->install_schema();
        for(unsigned i=1;i<=7;++i) {
            sqlite_detail::Statement account(db,"INSERT INTO accounts(id,username,password_hash) VALUES(?,?,'TEST_ONLY_OPAQUE_HASH')");
            account.bind(1,i);account.bind(2,"DisAccount"+std::to_string(i));account.done();
            const auto name="DisPlayer"+std::to_string(i);std::array<std::uint8_t,40> profile{};
            std::copy(name.begin(),name.end(),profile.begin());profile[29]=static_cast<std::uint8_t>(i);
            const std::vector<std::uint8_t> bytes(name.begin(),name.end());
            sqlite_detail::Statement character(db,"INSERT INTO recovered_characters(id,account_id,slot,profile,name_bytes,name_codepage) VALUES(?,?,0,?,?,?)");
            character.bind(1,i);character.bind(2,i);character.bind_blob(3,profile);character.bind_blob(4,bytes);character.bind(5,simplified?936:950);character.done();
            RecoveredRoleLevel::Bytes role{};role[0]=0x22;role[1]=35;role[17]=100;role[21]=50;
            sqlite_detail::Statement r(db,"INSERT INTO character_role_snapshots(character_id,logical,revision,design_id) VALUES(?,?,1,'CUSTOM-0013')");
            r.bind(1,i);r.bind_blob(2,role);r.done();money->provision_wallet(i,i);
            SqliteRecoveredCharacterRepository(db).commit_resources(i,i,{}, {100,100,50,50,0,"CUSTOM-0012"});
        }
        sqlite_detail::execute(db,"UPDATE character_trade_wallets SET amount=100000"); // Explicit disposable funds.
        guild=create(1,"DisGuild");join(2,guild);apply(3,guild);
        foreign=create(4,"ForeignGuild");join(5,foreign);apply(6,foreign);
        SqliteOwnedGuildAnnouncementRepository announcements(db);
        announcements.save(repo->leader(1,1),announcements.load(guild),"Saved primary 100%",proof);
        announcements.save(repo->leader(4,4),announcements.load(foreign),"Saved foreign",proof);
        if(opaque)sqlite_detail::execute(db,
            "ALTER TABLE owned_guilds ADD COLUMN opaque_blob BLOB DEFAULT X'0002FF';"
            "ALTER TABLE owned_guilds ADD COLUMN opaque_float DEFAULT 1.25;"
            "ALTER TABLE owned_guild_members ADD COLUMN opaque_member BLOB DEFAULT X'0012';"
            "ALTER TABLE owned_guild_applications_0078 ADD COLUMN opaque_request BLOB DEFAULT X'0013';"
            "ALTER TABLE owned_guild_governance_0078 ADD COLUMN opaque_governance BLOB DEFAULT X'0014';"
            "ALTER TABLE owned_guild_announcements_0078 ADD COLUMN opaque_notice BLOB DEFAULT X'0015';"
            "CREATE TABLE unknown_save(number,bytes BLOB,label TEXT);"
            "INSERT INTO unknown_save VALUES(NULL,X'','');"
            "INSERT INTO unknown_save VALUES(1.25,X'000102FF',NULL);"
            "INSERT INTO unknown_save SELECT * FROM unknown_save;"
            "CREATE TABLE opaque_item_fixture(character_id INTEGER,instance BLOB);"
            "INSERT INTO opaque_item_fixture VALUES(2,X'00FF12'),(5,X'FF0001');"
            "CREATE INDEX unknown_save_index ON unknown_save(label);"
            "CREATE TRIGGER unknown_save_trigger AFTER UPDATE ON unknown_save BEGIN SELECT 1;END;");
    }
    ~Fixture(){money.reset();memberships.reset();repo.reset();if(db)sqlite3_close_v2(db);}
    std::uint64_t create(unsigned person,const std::string& name) {
        return repo->create(repo->nonmember(person,person),*money->load_wallet(person,person),name,{50000,30,20},proof).leader.governance.guild_id;
    }
    Repo::Application apply(unsigned person,std::uint64_t target) {
        return repo->apply(repo->nonmember(person,person),repo->guild(target),proof);
    }
    void join(unsigned person,std::uint64_t target) {
        const auto application=apply(person,target);const auto gov=repo->governance(target);
        repo->approve(repo->leader(gov.owner_account,gov.owner_character),application,proof);
    }
    struct Lease {Repo::Leader leader;std::vector<Repo::Application> applications;};
    Lease lease() {return {repo->leader(1,1),repo->applications(guild)};}
    Repo::Disbanded disband(const Lease& lease,const Repo::Proof& callbacks) {
        return repo->disband(lease.leader,lease.applications,callbacks);
    }
    Repo::Disbanded disband(const Lease& lease) {return disband(lease,proof);}
    template<class F> void failed(F action,const std::source_location at=std::source_location::current()) {
        const auto before=snapshot(db);bool rejected=false;
        try{action();}catch(const DatabaseError&){rejected=true;}
        check(rejected,at);check(snapshot(db)==before,at);check(sqlite3_get_autocommit(db)==1,at);
    }
};

// TEST_ONLY standalone fixtures: no server/client/gameplay grants are started.
// The duplicate independent typed oracle above is sourced from the frozen0080
// test, not the implementation's guard. Extends it with retained-column checks.
Rows retained_guild(sqlite3* db,std::uint64_t id) {
    sqlite3_stmt* raw=nullptr;
    check(sqlite3_prepare_v2(db,"SELECT * FROM owned_guilds WHERE id=?",-1,&raw,nullptr)==SQLITE_OK);
    std::unique_ptr<sqlite3_stmt,decltype(&sqlite3_finalize)> q(raw,sqlite3_finalize);
    check(sqlite3_bind_int64(raw,1,static_cast<sqlite3_int64>(id))==SQLITE_OK);
    Rows result;int rc;
    while((rc=sqlite3_step(raw))==SQLITE_ROW) {
        std::vector<std::uint8_t> row;unsigned skipped=0;
        for(int c=0;c<sqlite3_column_count(raw);++c) {
            if(std::string(sqlite3_column_name(raw,c))=="revision"){++skipped;continue;}
            const auto type=sqlite3_column_type(raw,c);row.push_back(static_cast<std::uint8_t>(type));
            if(type==SQLITE_INTEGER)number(row,std::bit_cast<std::uint64_t>(sqlite3_column_int64(raw,c)));
            else if(type==SQLITE_FLOAT)number(row,std::bit_cast<std::uint64_t>(sqlite3_column_double(raw,c)));
            else if(type==SQLITE_TEXT || type==SQLITE_BLOB) {
                const auto size=sqlite3_column_bytes(raw,c);number(row,static_cast<std::uint64_t>(size));
                const auto* bytes=type==SQLITE_TEXT?sqlite3_column_text(raw,c):static_cast<const unsigned char*>(sqlite3_column_blob(raw,c));
                if(size)row.insert(row.end(),bytes,bytes+size);
            }
        }
        check(skipped==1);result.push_back(std::move(row));
    }
    check(rc==SQLITE_DONE && result.size()==1);return result;
}
void assert_removed(Fixture& f,const Fixture::Lease& lease) {
    for(const auto* table:{"owned_guild_members","owned_guild_governance_0078","owned_guild_applications_0078"}) {
        const auto sql="SELECT COUNT(*) FROM "+quote(table)+" WHERE guild_id=?";
        sqlite_detail::Statement q(f.db,sql.c_str());q.bind_id(1,f.guild);
        check(q.row() && q.integer(0)==0);
    }
    check(!f.repo->player_created(f.guild) && !f.repo->find_by_name(lease.leader.membership.name_utf8));
    for(const auto& member:lease.leader.roster) {
        auto identity=member;identity.membership_revision=0;
        check(!f.memberships->load(member.account_id,member.character_id));
        check(f.repo->nonmember(member.account_id,member.character_id)==identity);
    }
    for(const auto& application:lease.applications)
        check(!f.repo->pending(application.applicant.account_id,application.applicant.character_id));
    // Announcement.load() intentionally requires governance and cannot be used
    // after retirement. Exact raw retained rows are checked by typed oracle.
}
Exclusions allowed(Fixture& f) {
    return {{"owned_guilds","id<>"+std::to_string(f.guild)},
        {"owned_guild_members","guild_id<>"+std::to_string(f.guild)},
        {"owned_guild_governance_0078","guild_id<>"+std::to_string(f.guild)},
        {"owned_guild_applications_0078","guild_id<>"+std::to_string(f.guild)}};
}
void lifecycle(bool simplified,bool utf16) {
    Fixture f(":memory:",utf16,simplified);const auto lease=f.lease();
    const auto before=snapshot(f.db,allowed(f));const auto fields=retained_guild(f.db,f.guild);
    const auto foreign=f.repo->leader(4,4);const auto foreign_apps=f.repo->applications(f.foreign);
    const auto clock=scalar(f.db,"SELECT MAX(revision) FROM owned_guilds");
    const auto sequence=scalar(f.db,"SELECT seq FROM sqlite_sequence WHERE name='owned_guild_applications_0078'");
    unsigned first=0,last=0;
    const auto retired=f.disband(lease,{[&]{++first;check(sqlite3_get_autocommit(f.db)==0);},
        [&]{++last;check(sqlite3_get_autocommit(f.db)==0);}});
    check(first==1 && last==1 && sqlite3_get_autocommit(f.db)==1);
    check(retired.retained==Repo::Guild{f.guild,static_cast<std::uint64_t>(clock+1),lease.leader.membership.name_utf8});
    check(retired.former_leader==lease.leader && retired.former_applications==lease.applications);
    assert_removed(f,lease);check(retained_guild(f.db,f.guild)==fields);
    check(snapshot(f.db,allowed(f))==before);
    check(f.repo->leader(4,4)==foreign && f.repo->applications(f.foreign)==foreign_apps);
    check(scalar(f.db,"SELECT seq FROM sqlite_sequence WHERE name='owned_guild_applications_0078'")==sequence);
    f.failed([&]{f.disband(lease);}); // Replay does not resurrect history or delete foreign rows.
    f.failed([&]{f.repo->apply(f.repo->nonmember(7,7),retired.retained,f.proof);});
    f.failed([&]{sqlite_detail::execute(f.db,"DELETE FROM owned_guilds WHERE id=1");}); // retained trigger.
}
void empty_and_name_reservation() {
    Fixture f(":memory:",false,false,false); // no extension columns: frozen create uses positional gov INSERT.
    f.repo->cancel(f.repo->nonmember(3,3),*f.repo->pending(3,3),f.proof);
    f.memberships->admin_remove(2,2,f.memberships->load(2,2)->membership_revision); // TEST_ONLY fixture arrangement.
    sqlite_detail::execute(f.db,"DELETE FROM owned_guild_announcements_0078 WHERE guild_id=1");
    const auto lease=f.lease();const auto state=snapshot(f.db,allowed(f));
    const auto retired=f.disband(lease);assert_removed(f,lease);check(snapshot(f.db,allowed(f))==state);
    for(const auto* name:{"DisGuild","disguild","DISGUILD","dIsGuIlD"})
        f.failed([&]{f.create(1,name);}); // Native folded comparison includes retired rows.
    const auto fresh=f.create(1,"NewGuild");check(fresh>f.foreign && fresh!=retired.retained.id);
    check(f.repo->guild(fresh).revision>retired.retained.revision);
    check(f.repo->guild(retired.retained.id)==retired.retained);
    check(!f.repo->find_by_name("DisGuild") && f.repo->find_by_name("NewGuild").has_value());
}
void native_capacity50(bool simplified) {
    Fixture f(":memory:",false,simplified);
    // TEST_ONLY capacity arrangement in a disposable DB. This is not a native
    // capacity/economics claim, and no gameplay server receives these fixtures.
    sqlite_detail::execute(f.db,"UPDATE owned_guild_governance_0078 SET capacity=50 WHERE guild_id=1");
    for(unsigned person=8;person<=54;++person) {
        sqlite_detail::Statement account(f.db,"INSERT INTO accounts(id,username,password_hash) VALUES(?,?,'TEST_ONLY_OPAQUE_HASH')");
        account.bind(1,person);account.bind(2,"CapacityAccount"+std::to_string(person));account.done();
        const auto name="Capacity"+std::to_string(person);
        std::array<std::uint8_t,40> profile{};std::copy(name.begin(),name.end(),profile.begin());
        profile[29]=static_cast<std::uint8_t>(1+(person%8));
        const std::vector<std::uint8_t> bytes(name.begin(),name.end());
        sqlite_detail::Statement character(f.db,
            "INSERT INTO recovered_characters(id,account_id,slot,profile,name_bytes,name_codepage) VALUES(?,?,0,?,?,?)");
        character.bind(1,person);character.bind(2,person);character.bind_blob(3,profile);
        character.bind_blob(4,bytes);character.bind(5,simplified?936:950);character.done();
        RecoveredRoleLevel::Bytes role{};role[0]=0x22;role[1]=35;role[17]=100;role[21]=50;
        sqlite_detail::Statement r(f.db,
            "INSERT INTO character_role_snapshots(character_id,logical,revision,design_id) VALUES(?,?,1,'CUSTOM-0013')");
        r.bind(1,person);r.bind_blob(2,role);r.done();
        if(person<=30)f.join(person,f.guild);else f.apply(person,f.guild);
    }
    const auto lease=f.lease();check(lease.leader.roster.size()==25 && lease.applications.size()==25);
    const auto before=snapshot(f.db,allowed(f));const auto fields=retained_guild(f.db,f.guild);
    f.disband(lease);assert_removed(f,lease);
    check(snapshot(f.db,allowed(f))==before && retained_guild(f.db,f.guild)==fields);
}
void forged_and_stale() {
    Fixture f;const auto base=f.lease();
    const auto founder=[&](auto mutate){auto lease=base;mutate(lease.leader);f.failed([&]{f.disband(lease);});};
    founder([](auto& x){x.identity.account_id=0;});founder([](auto& x){x.identity.character_id=2;});
    founder([](auto& x){x.identity.slot=1;});founder([](auto& x){x.identity.profile[30]++;});
    founder([](auto& x){x.identity.role->revision++;});founder([](auto& x){x.identity.role.reset();});
    founder([](auto& x){x.identity.membership_revision=1;});
    founder([](auto& x){x.membership.guild_id++;});founder([](auto& x){x.membership.guild_revision++;});
    founder([](auto& x){x.membership.membership_revision++;});founder([](auto& x){x.membership.name_utf8="Other";});
    founder([](auto& x){x.governance.owner_account++;});founder([](auto& x){x.governance.owner_character++;});
    founder([](auto& x){x.governance.created_revision++;});founder([](auto& x){x.governance.created_cost++;});
    founder([](auto& x){x.governance.capacity--;});founder([](auto& x){x.roster.clear();});
    founder([](auto& x){std::reverse(x.roster.begin(),x.roster.end());});
    founder([](auto& x){x.roster.back().profile[30]++;});founder([](auto& x){x.roster.back().membership_revision++;});
    const auto pending=[&](auto mutate){auto lease=base;mutate(lease.applications);f.failed([&]{f.disband(lease);});};
    pending([](auto& x){x.clear();});pending([](auto& x){x.push_back(x.front());});
    pending([](auto& x){x.front().id++;});pending([](auto& x){x.front().target.id++;});
    pending([](auto& x){x.front().target.revision++;});pending([](auto& x){x.front().applicant.account_id++;});
    pending([](auto& x){x.front().applicant.role->revision++;});pending([](auto& x){x.front().applicant.profile[30]++;});
    auto mixed=base;mixed.leader=f.repo->leader(4,4);f.failed([&]{f.disband(mixed);});
    for(const auto& proof:{Repo::Proof{},Repo::Proof{[]{},{}},Repo::Proof{{},[]{}}})
        f.failed([&]{f.disband(base,proof);});
    const auto reject=[]{throw DatabaseError("TEST_ONLY proof denies world/audience");};
    f.failed([&]{f.disband(base,{reject,[]{}});});f.failed([&]{f.disband(base,{[]{},reject});});
    for(const auto* mutation:{
        "UPDATE character_role_snapshots SET revision=revision+1 WHERE character_id=2",
        "UPDATE recovered_characters SET name_codepage=936 WHERE id=2",
        "UPDATE owned_guild_governance_0078 SET capacity=capacity-1 WHERE guild_id=1",
        "UPDATE owned_guild_applications_0078 SET role_revision=role_revision+1 WHERE character_id=3",
        "DELETE FROM owned_guild_applications_0078 WHERE character_id=3",
        "UPDATE owned_guilds SET revision=revision+1 WHERE id=1"}) {
        Fixture changed;const auto stale=changed.lease();sqlite_detail::execute(changed.db,mutation);
        changed.failed([&]{changed.disband(stale);});
    }
}
void battle_and_historical_pending() {
    for(const unsigned person:{1u,2u,3u}) {
        Fixture f;const auto lease=f.lease();SqliteRecoveredCharacterRepository chars(f.db);
        const auto resources=chars.load_resources(person,person);check(resources.has_value());
        check(chars.reserve_battle(person,person,*resources)>0);
        f.failed([&]{f.disband(lease);}); // pending3 included in explicit all-audience nonbattle policy.
    }
    {
        Fixture f;const auto lease=f.lease();SqliteRecoveredCharacterRepository chars(f.db);
        const auto r=chars.load_resources(5,5);check(r.has_value());check(chars.reserve_battle(5,5,*r)>0);
        f.disband(lease);assert_removed(f,lease); // foreign battle does not block.
    }
    {
        Fixture f;const auto historical=*f.repo->pending(3,3);
        sqlite_detail::execute(f.db,"UPDATE character_role_snapshots SET revision=revision+1 WHERE character_id=3");
        const auto lease=f.lease();check(lease.applications.front()==historical);
        check(f.repo->identity(3,3).role->revision>historical.applicant.role->revision);
        f.disband(lease);assert_removed(f,lease); // snapshot is saved history, not current action authority.
    }
    {
        Fixture f;sqlite_detail::execute(f.db,"UPDATE owned_guilds SET revision=9223372036854775807 WHERE id=2");
        const auto lease=f.lease();f.failed([&]{f.disband(lease);});
    }
    {
        Fixture f;sqlite_detail::execute(f.db,
            "UPDATE owned_guild_applications_0078 SET profile=(SELECT profile FROM recovered_characters WHERE id=2),"
            "name_bytes=(SELECT name_bytes FROM recovered_characters WHERE id=2),name_utf8='DisPlayer2' WHERE character_id=3");
        const auto lease=f.lease();f.failed([&]{f.disband(lease);}); // stored-name accepted/pending collision.
    }
}
void callbacks_and_triggers() {
    for(const bool before:{true,false})for(const auto* mutation:{
        "UPDATE accounts SET password_hash='changed' WHERE id=2",
        "UPDATE recovered_characters SET name_codepage=936 WHERE id=2",
        "UPDATE character_trade_wallets SET amount=amount-1 WHERE character_id=2",
        "UPDATE opaque_item_fixture SET instance=X'010203' WHERE character_id=2",
        "UPDATE owned_guilds SET opaque_blob=X'FFFF' WHERE id=1",
        "UPDATE owned_guilds SET opaque_float=CAST(opaque_float AS TEXT) WHERE id=1",
        "UPDATE owned_guild_governance_0078 SET opaque_governance=X'0000' WHERE guild_id=2",
        "UPDATE owned_guild_applications_0078 SET opaque_request=X'0101' WHERE guild_id=2",
        "UPDATE owned_guild_announcements_0078 SET text_utf8='wrong',opaque_notice=X'0102'",
        "UPDATE owned_guild_members SET opaque_member=X'0103' WHERE character_id=5",
        "UPDATE unknown_save SET number=CAST(number AS TEXT) WHERE number IS NOT NULL",
        "INSERT INTO unknown_save SELECT * FROM unknown_save LIMIT 1",
        "CREATE TABLE unexpected_table(v)","CREATE INDEX unexpected_index ON unknown_save(bytes)",
        "CREATE TRIGGER unexpected_trigger AFTER INSERT ON unknown_save BEGIN SELECT 1;END",
        "UPDATE sqlite_sequence SET seq=seq+1 WHERE name='owned_guild_applications_0078'",
        "INSERT INTO battle_reservations(character_id,resource_revision,design_id) VALUES(3,1,'CUSTOM-0012')"}) {
        Fixture f;const auto lease=f.lease();unsigned last=0;
        const auto mutate=[&]{sqlite_detail::execute(f.db,mutation);};
        f.failed([&]{f.disband(lease,{[&]{if(before)mutate();},[&]{++last;if(!before)mutate();}});});
        check(last==(before?0u:1u));
    }
    // Target rows destined for deletion still cannot be silently mutated by a
    // before-proof callback. This exercises full G0 rather than final allowlist.
    for(const auto* mutation:{
        "UPDATE owned_guild_members SET opaque_member=X'9999' WHERE character_id=2",
        "UPDATE owned_guild_applications_0078 SET opaque_request=X'8888' WHERE guild_id=1",
        "UPDATE owned_guild_governance_0078 SET opaque_governance=X'7777' WHERE guild_id=1"}) {
        Fixture f;const auto lease=f.lease();f.failed([&]{f.disband(lease,{[&]{sqlite_detail::execute(f.db,mutation);},[]{}});});
    }
    for(const auto* table:{"owned_guild_applications_0078","owned_guild_members","owned_guild_governance_0078"})
    for(const auto* event:{"BEFORE","AFTER"})for(const auto* effect:{
        "SELECT RAISE(ABORT,'TEST_ONLY fault');",
        "UPDATE accounts SET password_hash='changed' WHERE id=2;",
        "UPDATE character_trade_wallets SET amount=0 WHERE character_id=2;",
        "UPDATE owned_guild_announcements_0078 SET text_utf8='changed';",
        "UPDATE sqlite_sequence SET seq=seq+1 WHERE name='owned_guild_applications_0078';",
        "UPDATE owned_guilds SET opaque_blob=X'00' WHERE id=1;",
        "DELETE FROM owned_guild_members WHERE character_id=5;"}) {
        Fixture f;const auto lease=f.lease();
        const auto sql="CREATE TRIGGER fault "+std::string(event)+" DELETE ON "+table+" WHEN OLD.guild_id=1 BEGIN "+effect+" END";
        sqlite_detail::execute(f.db,sql);f.failed([&]{f.disband(lease);});
    }
    for(const auto* statement:{
        "CREATE TRIGGER fault BEFORE DELETE ON owned_guild_applications_0078 WHEN OLD.guild_id=1 BEGIN SELECT RAISE(IGNORE);END",
        "CREATE TRIGGER fault BEFORE DELETE ON owned_guild_members WHEN OLD.character_id=2 BEGIN SELECT RAISE(IGNORE);END",
        "CREATE TRIGGER fault BEFORE DELETE ON owned_guild_governance_0078 WHEN OLD.guild_id=1 BEGIN SELECT RAISE(IGNORE);END",
        "CREATE TRIGGER fault AFTER UPDATE OF revision ON owned_guilds WHEN NEW.id=1 BEGIN UPDATE owned_guilds SET opaque_blob=X'01' WHERE id=NEW.id;END",
        "CREATE TRIGGER fault AFTER UPDATE OF revision ON owned_guilds WHEN NEW.id=1 BEGIN UPDATE owned_guild_members SET revision=revision+1 WHERE character_id=2;END",
        "CREATE TRIGGER fault AFTER DELETE ON owned_guild_applications_0078 WHEN OLD.guild_id=1 BEGIN UPDATE owned_guild_members SET revision=revision+1 WHERE character_id=2;END"}) {
        Fixture f;const auto lease=f.lease();sqlite_detail::execute(f.db,statement);f.failed([&]{f.disband(lease);});
    }
}
void persistence_and_writer_conflict() {
    const auto temp=std::filesystem::canonical(std::filesystem::temp_directory_path());std::random_device random;
    const auto root=temp/("god2-disband0081-"+std::to_string(random())+"-"+
        std::to_string(std::chrono::steady_clock::now().time_since_epoch().count()));
    check(std::filesystem::create_directory(root));
    struct Cleanup{std::filesystem::path root;~Cleanup(){std::error_code ec;std::filesystem::remove_all(root,ec);}} cleanup{root};
    const auto path=root/"exclusive-test.db";Snapshot committed;Repo::Guild retained;
    {
        Fixture f(path.string());const auto lease=f.lease();sqlite3* other=nullptr;
        check(sqlite3_open(path.string().c_str(),&other)==SQLITE_OK);
        std::unique_ptr<sqlite3,decltype(&sqlite3_close_v2)> connection(other,sqlite3_close_v2);
        sqlite_detail::execute(other,"PRAGMA foreign_keys=ON;BEGIN IMMEDIATE");
        f.failed([&]{f.disband(lease);});sqlite_detail::execute(other,"ROLLBACK");
        retained=f.disband(lease).retained;assert_removed(f,lease);
        bool rejected=false;
        try{Repo(other).disband(lease.leader,lease.applications,f.proof);}catch(const DatabaseError&){rejected=true;}
        check(rejected && !SqliteGuildRepository(other).load(2,2));
        committed=snapshot(f.db);check(snapshot(other)==committed);
    }
    sqlite3* reopened=nullptr;check(sqlite3_open(path.string().c_str(),&reopened)==SQLITE_OK);
    std::unique_ptr<sqlite3,decltype(&sqlite3_close_v2)> connection(reopened,sqlite3_close_v2);
    check(snapshot(reopened)==committed);check(Repo(reopened).guild(1)==retained);
    check(!SqliteGuildRepository(reopened).load(1,1) && !SqliteGuildRepository(reopened).load(2,2));
    check(!Repo(reopened).player_created(1) && !Repo(reopened).pending(3,3));
    check(Repo(reopened).leader(4,4).roster.size()==2);
    check(scalar(reopened,"SELECT COUNT(*) FROM owned_guild_announcements_0078 WHERE guild_id=1 AND text_utf8='Saved primary 100%'")==1);
}
}
int main() {
    try {
        for(const bool simplified:{false,true})for(const bool utf16:{false,true})lifecycle(simplified,utf16);
        empty_and_name_reservation();native_capacity50(false);native_capacity50(true);
        forged_and_stale();battle_and_historical_pending();
        callbacks_and_triggers();persistence_and_writer_conflict();
        std::cout<<"PASS "<<checks<<" CUSTOM0081 disband storage assertions; schema50 isolated, no native UI claim\n";
        return 0;
    }catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}
}
