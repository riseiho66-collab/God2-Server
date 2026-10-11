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
    ++checks;if(!value)throw std::runtime_error("Guild kick0080 storage line "+std::to_string(at.line()));
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
    explicit Fixture(const std::string& path=":memory:",bool utf16=false) {
        check(sqlite3_open(path.c_str(),&db)==SQLITE_OK);sqlite_detail::execute(db,"PRAGMA foreign_keys=ON");
        if(utf16)sqlite_detail::execute(db,"PRAGMA encoding='UTF-16be'");
        const auto migrations=owned_guild_announcement_migrations();check(migrations.size()==50);
        SqliteMigrationManager(db,migrations).migrate();check(scalar(db,"SELECT max(version) FROM schema_migrations")==50);
        repo=std::make_unique<Repo>(db);memberships=std::make_unique<SqliteGuildRepository>(db);
        money=std::make_unique<SqliteTradeRepository>(db);money->install_schema();
        for(unsigned i=1;i<=7;++i) {
            sqlite_detail::Statement account(db,"INSERT INTO accounts(id,username,password_hash) VALUES(?,?,'TEST_ONLY_OPAQUE_HASH')");
            account.bind(1,i);account.bind(2,"KickAccount"+std::to_string(i));account.done();
            const auto name="KickPlayer"+std::to_string(i);std::array<std::uint8_t,40> profile{};
            std::copy(name.begin(),name.end(),profile.begin());profile[29]=static_cast<std::uint8_t>(i);
            const std::vector<std::uint8_t> bytes(name.begin(),name.end());
            sqlite_detail::Statement character(db,"INSERT INTO recovered_characters(id,account_id,slot,profile,name_bytes,name_codepage) VALUES(?,?,0,?,?,0)");
            character.bind(1,i);character.bind(2,i);character.bind_blob(3,profile);character.bind_blob(4,bytes);character.done();
            RecoveredRoleLevel::Bytes role{};role[0]=0x22;role[1]=35;role[17]=100;role[21]=50;
            sqlite_detail::Statement r(db,"INSERT INTO character_role_snapshots(character_id,logical,revision,design_id) VALUES(?,?,1,'CUSTOM-0013')");
            r.bind(1,i);r.bind_blob(2,role);r.done();money->provision_wallet(i,i);
            SqliteRecoveredCharacterRepository(db).commit_resources(i,i,{}, {100,100,50,50,0,"CUSTOM-0012"});
        }
        sqlite_detail::execute(db,"UPDATE character_trade_wallets SET amount=100000"); // Explicit disposable funds.
        guild=create(1,"KickGuild");join(2,guild);apply(3,guild);
        foreign=create(4,"ForeignGuild");join(5,foreign);apply(6,foreign);
        SqliteOwnedGuildAnnouncementRepository announcements(db);
        announcements.save(repo->leader(1,1),announcements.load(guild),"Saved primary 100%",proof);
        announcements.save(repo->leader(4,4),announcements.load(foreign),"Saved foreign",proof);
        sqlite_detail::execute(db,
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
    struct Lease {Repo::Leader leader;std::vector<Repo::Application> applications;Repo::Identity target;StoredGuildMembership member;};
    Lease lease() {return {repo->leader(1,1),repo->applications(guild),repo->identity(2,2),*memberships->load(2,2)};}
    Repo::Kicked kick(const Lease& lease,const Repo::Proof& callbacks) {
        return repo->member_kick(lease.leader,lease.applications,lease.target,lease.member,callbacks);
    }
    Repo::Kicked kick(const Lease& lease) {return kick(lease,proof);}
    template<class F> void failed(F action,const std::source_location at=std::source_location::current()) {
        const auto before=snapshot(db);bool rejected=false;
        try{action();}catch(const DatabaseError&){rejected=true;}
        check(rejected,at);check(snapshot(db)==before,at);check(sqlite3_get_autocommit(db)==1,at);
    }
};
void lifecycle(bool utf16) {
    Fixture f(":memory:",utf16);const auto lease=f.lease();
    const Exclusions allowed{{"owned_guilds","id<>"+std::to_string(f.guild)},
                             {"owned_guild_members","character_id<>2"}};
    const auto protected_before=snapshot(f.db,allowed);
    const auto foreign_before=f.repo->guild(f.foreign);
    const auto notice=SqliteOwnedGuildAnnouncementRepository(f.db).load(f.guild);
    unsigned before_calls=0,after_calls=0;
    const auto kicked=f.kick(lease,{[&]{++before_calls;check(sqlite3_get_autocommit(f.db)==0);},
                                   [&]{++after_calls;check(sqlite3_get_autocommit(f.db)==0);}});
    // Target is offline: no target actor, session grant or presence seed exists.
    check(before_calls==1 && after_calls==1 && sqlite3_get_autocommit(f.db)==1);
    check(kicked.guild.id==f.guild && kicked.guild.revision>foreign_before.revision && kicked.guild.revision>lease.member.guild_revision);
    check(kicked.removed==lease.target && kicked.removed_membership==lease.member);
    check(kicked.leader==f.repo->leader(1,1) && kicked.leader.governance==lease.leader.governance);
    check(kicked.leader.roster.size()==1 && kicked.leader.roster.front().character_id==1);
    check(!f.memberships->load(2,2) && f.repo->nonmember(2,2)==lease.target);
    check(f.repo->applications(f.guild)==lease.applications && f.repo->guild(f.foreign)==foreign_before);
    check(SqliteOwnedGuildAnnouncementRepository(f.db).load(f.guild)==notice);
    check(snapshot(f.db,allowed)==protected_before);
    sqlite_detail::Statement retained(f.db,"SELECT hex(opaque_blob),typeof(opaque_float),opaque_float FROM owned_guilds WHERE id=?");
    retained.bind_id(1,f.guild);check(retained.row());check(retained.text(0)=="0002FF" && retained.text(1)=="real");
    f.failed([&]{f.kick(lease);}); // single-use stored membership and old full generation.
    f.join(2,f.guild);const auto fresh=f.lease();check(fresh.member.membership_revision>lease.member.membership_revision);
    f.failed([&]{f.kick(lease);});
    auto mixed=fresh;mixed.target=lease.target;mixed.member=lease.member;f.failed([&]{f.kick(mixed);});
    const auto again=f.kick(fresh);check(again.guild.revision>kicked.guild.revision);
}
void forged_leases() {
    Fixture f;const auto base=f.lease();
    const auto bad_target=[&](auto mutate){auto lease=base;mutate(lease.target);f.failed([&]{f.kick(lease);});};
    bad_target([](auto& x){x.account_id=1;});bad_target([](auto& x){x.character_id=3;});
    bad_target([](auto& x){x.account_id=0;});bad_target([](auto& x){x.character_id=0;});
    bad_target([](auto& x){x.slot=1;});bad_target([](auto& x){x.profile[30]++;});
    bad_target([](auto& x){x.name_bytes[0]='X';});bad_target([](auto& x){x.name_codepage=936;});
    bad_target([](auto& x){x.name_utf8="Different";});bad_target([](auto& x){x.role->revision++;});
    bad_target([](auto& x){x.role->logical[1]++;});bad_target([](auto& x){x.role.reset();});
    bad_target([](auto& x){x.membership_revision=1;});
    const auto bad_membership=[&](auto mutate){auto lease=base;mutate(lease.member);f.failed([&]{f.kick(lease);});};
    bad_membership([](auto& x){x.guild_id=0;});bad_membership([](auto& x){x.guild_revision=0;});
    bad_membership([](auto& x){x.membership_revision=0;});bad_membership([](auto& x){x.guild_id++;});
    bad_membership([](auto& x){x.guild_revision++;});bad_membership([](auto& x){x.membership_revision++;});
    bad_membership([](auto& x){x.name_utf8="Different";});
    const auto bad_founder=[&](auto mutate){auto lease=base;mutate(lease.leader);f.failed([&]{f.kick(lease);});};
    bad_founder([&](auto& x){x.identity=base.target;}); // target actor cannot authorize removal.
    bad_founder([](auto& x){x.identity.profile[30]++;});bad_founder([](auto& x){x.identity.account_id=0;});
    bad_founder([](auto& x){x.identity.role->revision++;});bad_founder([](auto& x){x.identity.role.reset();});
    bad_founder([](auto& x){x.governance.owner_account++;});bad_founder([](auto& x){x.governance.owner_character++;});
    bad_founder([](auto& x){x.governance.capacity--;});bad_founder([](auto& x){x.governance.created_cost++;});
    bad_founder([](auto& x){x.governance.created_revision++;});
    bad_founder([](auto& x){x.membership.guild_revision++;});bad_founder([](auto& x){x.membership.membership_revision++;});
    bad_founder([](auto& x){x.roster.clear();});bad_founder([](auto& x){std::reverse(x.roster.begin(),x.roster.end());});
    bad_founder([](auto& x){x.roster.back().profile[30]++;});
    bad_founder([](auto& x){x.roster.back().membership_revision++;});
    auto pending=base;pending.target=f.repo->identity(3,3);f.failed([&]{f.kick(pending);});
    auto self=base;self.target=f.repo->identity(1,1);self.member=*f.memberships->load(1,1);f.failed([&]{f.kick(self);});
    auto foreign=base;foreign.target=f.repo->identity(5,5);foreign.member=*f.memberships->load(5,5);f.failed([&]{f.kick(foreign);});
    auto foreign_founder=base;foreign_founder.leader=f.repo->leader(4,4);foreign_founder.applications=f.repo->applications(f.foreign);
    f.failed([&]{f.kick(foreign_founder);});
    const auto bad_application=[&](auto mutate){auto lease=base;mutate(lease.applications);f.failed([&]{f.kick(lease);});};
    bad_application([](auto& x){x.clear();});bad_application([](auto& x){x.front().id++;});
    bad_application([](auto& x){x.front().target.id++;});bad_application([](auto& x){x.front().target.name_utf8="Other";});
    bad_application([](auto& x){x.front().target.revision++;});bad_application([](auto& x){x.front().applicant.role->revision++;});
    for(const auto proof:{Repo::Proof{},Repo::Proof{[]{},{}},Repo::Proof{{},[]{}}})
        f.failed([&]{f.kick(base,proof);});
    const auto fail=[]{throw DatabaseError("TEST_ONLY readiness rejects");};
    f.failed([&]{f.kick(base,{fail,[]{}});});f.failed([&]{f.kick(base,{[]{},fail});});
}
void battle_and_projection() {
    for(const unsigned person:{1u,2u}) {
        Fixture f;const auto lease=f.lease();SqliteRecoveredCharacterRepository characters(f.db);
        const auto resources=characters.load_resources(person,person);check(resources.has_value());
        check(characters.reserve_battle(person,person,*resources)>0);
        f.failed([&]{f.kick(lease);});
        // Exact read-only governance snapshot cannot replace nonbattle founder authority.
        auto current=lease;current.leader=f.repo->governance_snapshot(1,1);
        f.failed([&]{f.kick(current);});
    }
    {
        Fixture f;const auto lease=f.lease();SqliteRecoveredCharacterRepository characters(f.db);
        const auto resources=characters.load_resources(5,5);check(resources.has_value());
        check(characters.reserve_battle(5,5,*resources)>0);
        const auto kicked=f.kick(lease);check(kicked.removed.character_id==2); // unrelated guild battle is harmless.
    }
    for(const auto mutation:{
        "UPDATE recovered_characters SET name_codepage=936 WHERE id=2",
        "UPDATE character_role_snapshots SET revision=revision+1 WHERE character_id=2",
        "UPDATE character_role_snapshots SET revision=revision+1 WHERE character_id=1",
        "UPDATE owned_guild_governance_0078 SET capacity=capacity-1 WHERE owner_character=1",
        "UPDATE owned_guild_applications_0078 SET role_revision=role_revision+1 WHERE character_id=3",
        "UPDATE owned_guild_members SET revision=revision+1 WHERE character_id=2",
        "DELETE FROM owned_guild_applications_0078 WHERE character_id=3"
    }) {
        Fixture f;const auto stale=f.lease();sqlite_detail::execute(f.db,mutation);f.failed([&]{f.kick(stale);});
    }
    {
        Fixture f;
        sqlite_detail::execute(f.db,
            "UPDATE owned_guild_applications_0078 SET profile=(SELECT profile FROM recovered_characters WHERE id=2),"
            "name_bytes=(SELECT name_bytes FROM recovered_characters WHERE id=2),name_utf8='KickPlayer2' WHERE character_id=3");
        const auto current=f.lease();f.failed([&]{f.kick(current);}); // exact leases, folded pending/accepted collision.
    }
    {
        Fixture f;
        sqlite_detail::execute(f.db,
            "INSERT INTO owned_guild_applications_0078(guild_id,guild_name,observed_revision,character_id,account_id,slot,profile,name_bytes,name_codepage,name_utf8,role,role_revision,role_design,origin,design_id,source_sha256) "
            "SELECT guild_id,guild_name,observed_revision,2,2,slot,profile,name_bytes,name_codepage,name_utf8,role,role_revision,role_design,origin,design_id,source_sha256 FROM owned_guild_applications_0078 WHERE character_id=3");
        const auto current=f.lease();f.failed([&]{f.kick(current);}); // accepted target cannot also be pending.
    }
    {
        Fixture f;
        sqlite_detail::execute(f.db,"UPDATE owned_guilds SET revision=9223372036854775807 WHERE id=(SELECT guild_id FROM owned_guild_members WHERE character_id=5)");
        const auto current=f.lease();f.failed([&]{f.kick(current);}); // global monotonic generation cannot wrap.
    }
}
void callbacks_and_triggers() {
    Fixture f;const auto lease=f.lease();
    for(const bool before:{true,false})for(const auto mutation:{
        "UPDATE accounts SET password_hash='changed' WHERE id=2",
        "UPDATE recovered_characters SET name_codepage=936 WHERE id=2",
        "UPDATE character_trade_wallets SET amount=amount-1 WHERE character_id=2",
        "UPDATE opaque_item_fixture SET instance=X'010203' WHERE character_id=2",
        "UPDATE owned_guilds SET opaque_blob=X'FFFF' WHERE id=(SELECT guild_id FROM owned_guild_members WHERE character_id=1)",
        "UPDATE owned_guilds SET opaque_float=CAST(opaque_float AS TEXT) WHERE id=(SELECT guild_id FROM owned_guild_members WHERE character_id=1)",
        "UPDATE owned_guild_governance_0078 SET opaque_governance=X'0000'",
        "UPDATE owned_guild_applications_0078 SET opaque_request=X'0101'",
        "UPDATE owned_guild_announcements_0078 SET text_utf8='wrong',opaque_notice=X'0102'",
        "UPDATE owned_guild_members SET opaque_member=X'0103' WHERE character_id=5",
        "UPDATE unknown_save SET number=CAST(number AS TEXT) WHERE number IS NOT NULL",
        "INSERT INTO unknown_save SELECT * FROM unknown_save LIMIT 1",
        "CREATE TABLE unexpected_table(v)",
        "CREATE INDEX unexpected_index ON unknown_save(bytes)",
        "CREATE TRIGGER unexpected_trigger AFTER INSERT ON unknown_save BEGIN SELECT 1;END",
        "INSERT INTO battle_reservations(character_id,resource_revision,design_id) VALUES(2,1,'CUSTOM-0012')",
        "INSERT INTO battle_reservations(character_id,resource_revision,design_id) VALUES(1,1,'CUSTOM-0012')"
    }) {
        unsigned after_calls=0;
        const auto mutate=[&]{sqlite_detail::execute(f.db,mutation);};
        const auto after=[&]{++after_calls;if(!before)mutate();};
        f.failed([&]{f.kick(lease,{[&]{if(before)mutate();},after});});
        if(before)check(after_calls==0);else check(after_calls==1);
    }
    for(const auto event:{"BEFORE","AFTER"})for(const auto effect:{
        "SELECT RAISE(ABORT,'TEST_ONLY fail');",
        "UPDATE accounts SET password_hash='changed' WHERE id=2;",
        "UPDATE character_trade_wallets SET amount=0 WHERE character_id=2;",
        "UPDATE opaque_item_fixture SET instance=X'FF' WHERE character_id=2;",
        "UPDATE owned_guild_governance_0078 SET capacity=capacity-1 WHERE owner_character=1;",
        "UPDATE owned_guild_announcements_0078 SET text_utf8='changed';",
        "DELETE FROM owned_guild_applications_0078 WHERE character_id=3;",
        "UPDATE owned_guilds SET opaque_blob=X'0000';",
        "DELETE FROM owned_guild_members WHERE character_id=5;"
    }) {
        sqlite_detail::execute(f.db,"CREATE TRIGGER fault "+std::string(event)+" DELETE ON owned_guild_members WHEN OLD.character_id=2 BEGIN "+effect+" END");
        unsigned after_calls=0;f.failed([&]{f.kick(lease,{[]{},[&]{++after_calls;}});});check(after_calls==0);
        sqlite_detail::execute(f.db,"DROP TRIGGER fault");
    }
    for(const auto statement:{
        "CREATE TRIGGER fault BEFORE DELETE ON owned_guild_members WHEN OLD.character_id=2 BEGIN SELECT RAISE(IGNORE);END",
        "CREATE TRIGGER fault AFTER UPDATE OF revision ON owned_guilds BEGIN UPDATE owned_guilds SET opaque_blob=X'01' WHERE id=NEW.id;END",
        "CREATE TRIGGER fault AFTER UPDATE OF revision ON owned_guilds BEGIN UPDATE owned_guild_members SET revision=revision+1 WHERE character_id=2;END"
    }) {
        sqlite_detail::execute(f.db,statement);f.failed([&]{f.kick(lease);});sqlite_detail::execute(f.db,"DROP TRIGGER fault");
    }
}
void persistence_and_writer_conflict() {
    const auto temp=std::filesystem::canonical(std::filesystem::temp_directory_path());std::random_device random;
    const auto root=temp/("god2-kick0080-"+std::to_string(random())+"-"+
        std::to_string(std::chrono::steady_clock::now().time_since_epoch().count()));
    check(std::filesystem::create_directory(root));
    struct Cleanup{std::filesystem::path root;~Cleanup(){std::error_code ec;std::filesystem::remove_all(root,ec);}} cleanup{root};
    const auto path=root/"exclusive-test.db";Snapshot committed;
    {
        Fixture f(path.string());const auto lease=f.lease();sqlite3* other=nullptr;
        check(sqlite3_open(path.string().c_str(),&other)==SQLITE_OK);
        std::unique_ptr<sqlite3,decltype(&sqlite3_close_v2)> connection(other,sqlite3_close_v2);
        sqlite_detail::execute(other,"PRAGMA foreign_keys=ON;BEGIN IMMEDIATE");
        f.failed([&]{f.kick(lease);});sqlite_detail::execute(other,"ROLLBACK");
        const auto kicked=f.kick(lease);check(kicked.guild.revision>lease.member.guild_revision);
        bool rejected=false;
        try{Repo(other).member_kick(lease.leader,lease.applications,lease.target,lease.member,f.proof);}catch(const DatabaseError&){rejected=true;}
        check(rejected && !SqliteGuildRepository(other).load(2,2));committed=snapshot(f.db);check(snapshot(other)==committed);
    }
    sqlite3* reopened=nullptr;check(sqlite3_open(path.string().c_str(),&reopened)==SQLITE_OK);
    std::unique_ptr<sqlite3,decltype(&sqlite3_close_v2)> connection(reopened,sqlite3_close_v2);
    check(snapshot(reopened)==committed && !SqliteGuildRepository(reopened).load(2,2));
    check(Repo(reopened).leader(1,1).roster.size()==1);
    check(SqliteOwnedGuildAnnouncementRepository(reopened).load(1).value->text_utf8=="Saved primary 100%");
}
}
int main() {
    try {
        lifecycle(false);lifecycle(true);forged_leases();battle_and_projection();callbacks_and_triggers();persistence_and_writer_conflict();
        std::cout<<"PASS "<<checks<<" CUSTOM0080 founder/member-kick storage checks; current50 isolated, no native UI claim\n";
        return 0;
    }catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}
}
