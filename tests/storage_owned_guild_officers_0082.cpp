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
unsigned checks=0;unsigned negative_cases=0;
void check(bool value,const std::source_location at=std::source_location::current()) {
    ++checks;if(!value)throw std::runtime_error("Guild officer0082 line "+std::to_string(at.line()));
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
    explicit Fixture(const std::string& path=":memory:",bool utf16=false,bool cn=false,bool opaque=true) {
        check(sqlite3_open(path.c_str(),&db)==SQLITE_OK);sqlite_detail::execute(db,"PRAGMA foreign_keys=ON");
        if(utf16)sqlite_detail::execute(db,"PRAGMA encoding='UTF-16be'");
        auto migrations=owned_guild_announcement_migrations();check(migrations.size()==50);migrations.push_back({51,"owned_guild_officers_candidate",Repo::officer_schema()});
        SqliteMigrationManager(db,migrations).migrate();check(scalar(db,"SELECT max(version) FROM schema_migrations")==51);
        repo=std::make_unique<Repo>(db);memberships=std::make_unique<SqliteGuildRepository>(db);
        money=std::make_unique<SqliteTradeRepository>(db);money->install_schema();
        for(unsigned i=1;i<=7;++i) {
            sqlite_detail::Statement account(db,"INSERT INTO accounts(id,username,password_hash) VALUES(?,?,'TEST_ONLY_OPAQUE_HASH')");
            account.bind(1,i);account.bind(2,"DisAccount"+std::to_string(i));account.done();
            const auto name="DisPlayer"+std::to_string(i);std::array<std::uint8_t,40> profile{};
            std::copy(name.begin(),name.end(),profile.begin());profile[29]=static_cast<std::uint8_t>(i);
            const std::vector<std::uint8_t> bytes(name.begin(),name.end());
            sqlite_detail::Statement character(db,"INSERT INTO recovered_characters(id,account_id,slot,profile,name_bytes,name_codepage) VALUES(?,?,0,?,?,?)");
            character.bind(1,i);character.bind(2,i);character.bind_blob(3,profile);character.bind_blob(4,bytes);character.bind(5,cn?936:950);character.done();
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
            "ALTER TABLE owned_guild_officers_0082 ADD COLUMN opaque_rank BLOB DEFAULT X'00F2';"
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
        ++negative_cases;const auto before=snapshot(db);bool rejected=false;
        try{action();}catch(const DatabaseError&){rejected=true;}
        check(rejected,at);check(snapshot(db)==before,at);check(sqlite3_get_autocommit(db)==1,at);
    }
};


unsigned cases=0;
void case_start(const char* name){++cases;std::cout<<"CASE "<<name<<'\n';}
struct RankLease {Repo::Leader founder;std::vector<Repo::Application> apps;Repo::OfficerHistory history;Repo::Identity target;StoredGuildMembership member;};
RankLease rank_lease(Fixture& f,unsigned person=2) {
    return {f.repo->leader(1,1),f.repo->applications(f.guild),f.repo->officer_history(f.guild),
        f.repo->identity(person,person),*f.memberships->load(person,person)};
}
auto change(Fixture& f,const RankLease& l,Repo::OfficerAction action,const Repo::Proof& proof) {
    return f.repo->change_officer(l.founder,l.apps,l.history,l.target,l.member,action,proof);
}
auto change(Fixture& f,Repo::OfficerAction action) {return change(f,rank_lease(f),action,f.proof);}
auto display(Fixture& f,unsigned person=2) {
    const auto leader=f.repo->governance_snapshot(1,1);const auto history=f.repo->officer_history(f.guild);
    const auto member=std::find_if(leader.roster.begin(),leader.roster.end(),[&](const auto& r){return r.character_id==person;});
    check(member!=leader.roster.end());return Repo::officer_display_role(leader,*member,history);
}
auto leave(Fixture& f,const RankLease& l,const Repo::Proof& proof) {
    return f.repo->officer_leave(l.target,l.member,l.founder,l.apps,l.history,proof);
}
Exclusions rank_allowed(Fixture& f) {return {{"owned_guilds","id<>"+std::to_string(f.guild)},
    {"owned_guild_officers_0082","NOT(guild_id="+std::to_string(f.guild)+" AND character_id=2)"}};}
void battle(Fixture& f,unsigned person) {
    sqlite_detail::execute(f.db,"INSERT INTO battle_reservations(character_id,resource_revision,design_id) VALUES("+
        std::to_string(person)+",1,'CUSTOM-0012')");
}
void basic(bool cn,bool utf16) {
    case_start("appoint-demote-reappoint-retain");Fixture f(":memory:",utf16,cn);
    const auto foreign=f.repo->leader(4,4);const auto apps=f.repo->applications(f.foreign);
    const auto preserved=snapshot(f.db,rank_allowed(f));const auto identity=f.repo->identity(2,2);
    const auto before=rank_lease(f);const auto clock=scalar(f.db,"SELECT MAX(revision) FROM owned_guilds");
    const auto result=change(f,before,Repo::OfficerAction::Appoint,f.proof);
    check(result.guild.revision==static_cast<std::uint64_t>(clock+1));check(display(f)==2);check(display(f,1)==3);
    check(result.history.size()==1 && result.history[0].role==2);
    check(f.repo->identity(2,2)==identity);check(f.memberships->load(2,2)->membership_revision==before.member.membership_revision);
    check(snapshot(f.db,rank_allowed(f))==preserved && f.repo->leader(4,4)==foreign && f.repo->applications(f.foreign)==apps);
    f.failed([&]{change(f,before,Repo::OfficerAction::Appoint,f.proof);});
    f.failed([&]{change(f,Repo::OfficerAction::Appoint);});
    const auto appointed=f.repo->officer_history(f.guild);change(f,Repo::OfficerAction::RemoveOffice);check(display(f)==1);
    check(f.repo->officer_history(f.guild)[0].membership_revision==appointed[0].membership_revision);
    f.failed([&]{change(f,Repo::OfficerAction::RemoveOffice);});change(f,Repo::OfficerAction::Appoint);check(display(f)==2);
    check(snapshot(f.db,rank_allowed(f))==preserved);
}
void leave_rejoin(bool cn,bool utf16) {
    case_start("officer-leave-rejoin-no-inheritance");Fixture f(":memory:",utf16,cn);change(f,Repo::OfficerAction::Appoint);
    const auto old=rank_lease(f);const auto history=old.history;
    const Exclusions allowed{{"owned_guilds","id<>1"},{"owned_guild_members","character_id<>2"}};
    const auto before=snapshot(f.db,allowed);unsigned first=0,last=0;
    leave(f,old,{[&]{++first;check(sqlite3_get_autocommit(f.db)==0);},[&]{++last;
        check(!f.memberships->load(2,2));check(f.repo->officer_history(f.guild)==history);}});
    check(first==1 && last==1 && !f.memberships->load(2,2));check(snapshot(f.db,allowed)==before);
    f.failed([&]{leave(f,old,f.proof);});f.join(2,f.guild);check(display(f)==1);
    check(f.memberships->load(2,2)->membership_revision!=old.member.membership_revision && f.repo->officer_history(f.guild)==history);
    change(f,Repo::OfficerAction::Appoint);check(display(f)==2 && f.repo->officer_history(f.guild).size()==2);
}
void legacy_lifecycles() {
    case_start("demote-kick-disband-history");
    {Fixture f;change(f,Repo::OfficerAction::Appoint);change(f,Repo::OfficerAction::RemoveOffice);const auto l=rank_lease(f);
     const auto history=l.history;f.repo->member_kick(l.founder,l.apps,l.target,l.member,f.proof);
     check(!f.memberships->load(2,2) && f.repo->officer_history(f.guild)==history);}
    {Fixture f;change(f,Repo::OfficerAction::Appoint);const auto history=f.repo->officer_history(f.guild);
     const auto saved=snapshot(f.db,{{"owned_guilds","id<>1"},{"owned_guild_members","guild_id<>1"},
         {"owned_guild_governance_0078","guild_id<>1"},{"owned_guild_applications_0078","guild_id<>1"}});
     f.disband(f.lease());check(f.repo->officer_history(f.guild)==history && !f.repo->player_created(f.guild));
     check(snapshot(f.db,{{"owned_guilds","id<>1"},{"owned_guild_members","guild_id<>1"},
         {"owned_guild_governance_0078","guild_id<>1"},{"owned_guild_applications_0078","guild_id<>1"}})==saved);}
    {Fixture f;change(f,Repo::OfficerAction::Appoint);change(f,Repo::OfficerAction::RemoveOffice);auto l=rank_lease(f);
     const auto history=l.history;f.repo->member_leave(l.target,l.member,l.founder,l.apps,f.proof);
     check(f.repo->officer_history(f.guild)==history);}
}
void stale_leases() {
    case_start("stale-founder-target-applications-rank-history");
    for(unsigned variant=0;variant<11;++variant) {
        Fixture f;auto l=rank_lease(f);
        if(variant==0)l.founder.governance.owner_character=2;
        if(variant==1)l.founder.roster.pop_back();
        if(variant==2)l.apps.clear();
        if(variant==3)l.target.profile[29]=8;
        if(variant==4)l.target.account_id=4;
        if(variant==5)l.target.slot=1;
        if(variant==6)l.member.membership_revision++;
        if(variant==7)l.member.guild_id=f.foreign;
        if(variant==8)l.target.role->revision++;
        if(variant==9)l.target.name_utf8="Changed";
        if(variant==10)l.history.push_back({f.guild,2,2,l.member.membership_revision,l.member.guild_revision,0,1});
        f.failed([&]{change(f,l,Repo::OfficerAction::Appoint,f.proof);});
    }
    {Fixture f;auto l=rank_lease(f);l.target=f.repo->identity(1,1);l.member=*f.memberships->load(1,1);
     f.failed([&]{change(f,l,Repo::OfficerAction::Appoint,f.proof);});}
    {Fixture f;auto l=rank_lease(f);l.target=f.repo->identity(3,3);f.failed([&]{change(f,l,Repo::OfficerAction::Appoint,f.proof);});}
    {Fixture f;change(f,Repo::OfficerAction::Appoint);auto l=rank_lease(f);l.history[0].revision++;
     f.failed([&]{change(f,l,Repo::OfficerAction::RemoveOffice,f.proof);});}
}
void callbacks_and_triggers() {
    case_start("proof-before-after-fulltyped-rollback");
    const std::vector<std::string> mutations{
        "UPDATE owned_guilds SET opaque_blob=X'FF' WHERE id=1",
        "UPDATE recovered_characters SET name_codepage=0 WHERE id=2",
        "UPDATE character_resources SET max_hp=max_hp+1 WHERE character_id=2",
        "UPDATE unknown_save SET label='modified'", // fixed below matches fixture column
        "UPDATE owned_guild_announcements_0078 SET text_utf8='modified' WHERE guild_id=1",
        "CREATE TABLE forbidden_proof_table(n)",
        "UPDATE owned_guild_members SET revision=revision+1 WHERE character_id=2"};
    for(bool after:{false,true})for(auto sql:mutations) {
        Fixture f;sql=sql=="UPDATE unknown_save SET label='modified'"?"UPDATE unknown_save SET label='modified'":sql;
        bool executed=false;auto l=rank_lease(f);const auto mutation=[&]{sqlite_detail::execute(f.db,sql);executed=true;};
        const Repo::Proof p=after?Repo::Proof{[]{},mutation}:Repo::Proof{mutation,[]{}};
        f.failed([&]{change(f,l,Repo::OfficerAction::Appoint,p);});check(executed);
    }
    for(const auto sql:{"UPDATE owned_guild_officers_0082 SET role=2 WHERE character_id=2",
                        "UPDATE owned_guild_officers_0082 SET opaque_rank=X'FF' WHERE character_id=2"}) {
        Fixture f;change(f,Repo::OfficerAction::Appoint);auto l=rank_lease(f);
        f.failed([&]{change(f,l,Repo::OfficerAction::RemoveOffice,{[]{},[&]{sqlite_detail::execute(f.db,sql);}});});
    }
    case_start("rank-guild-triggers-rollback");
    for(const auto body:{"UPDATE unknown_save SET label='trigger'","UPDATE owned_guilds SET opaque_blob=X'FF' WHERE id=1",
                         "UPDATE owned_guild_officers_0082 SET opaque_rank=X'FF' WHERE character_id=2"}) {
        Fixture f;sqlite_detail::execute(f.db,std::string("CREATE TRIGGER forbidden_rank_trigger AFTER INSERT ON owned_guild_officers_0082 BEGIN ")+body+"; END");
        const auto l=rank_lease(f);f.failed([&]{change(f,l,Repo::OfficerAction::Appoint,f.proof);});
    }
    case_start("officer-leave-callback-rollback");
    for(bool after:{false,true}) {
        Fixture f;change(f,Repo::OfficerAction::Appoint);auto l=rank_lease(f);
        const auto mutate=[&]{sqlite_detail::execute(f.db,"UPDATE owned_guild_officers_0082 SET role=1 WHERE character_id=2");};
        f.failed([&]{leave(f,l,after?Repo::Proof{[]{},mutate}:Repo::Proof{mutate,[]{}});});
    }
}
void battle_overflow_schema() {
    case_start("persisted-battle-overflow-mandatory-proof");
    for(const auto person:{1u,2u}) {Fixture f;auto l=rank_lease(f);battle(f,person);f.failed([&]{change(f,l,Repo::OfficerAction::Appoint,f.proof);});}
    {Fixture f;change(f,Repo::OfficerAction::Appoint);auto l=rank_lease(f);battle(f,2);f.failed([&]{leave(f,l,f.proof);});}
    {Fixture f;change(f,Repo::OfficerAction::Appoint);auto l=rank_lease(f);battle(f,1);
     l.founder=f.repo->governance_snapshot(1,1);leave(f,l,f.proof);check(!f.memberships->load(2,2));}
    {Fixture f;sqlite_detail::execute(f.db,"UPDATE owned_guilds SET revision=9223372036854775807 WHERE id=1");
     auto l=rank_lease(f);f.failed([&]{change(f,l,Repo::OfficerAction::Appoint,f.proof);});}
    for(unsigned p=0;p<2;++p) {Fixture f;auto l=rank_lease(f);f.failed([&]{change(f,l,Repo::OfficerAction::Appoint,p?Repo::Proof{[]{},{}}:Repo::Proof{{},[]{}});});}
    case_start("schema-missing-history-fail-closed");
    {Fixture f;sqlite_detail::execute(f.db,"DROP TABLE owned_guild_officers_0082");auto leader=f.repo->leader(1,1);
     auto member=*f.memberships->load(2,2);auto target=f.repo->identity(2,2);auto apps=f.repo->applications(f.guild);
     f.failed([&]{f.repo->change_officer(leader,apps,{},target,member,Repo::OfficerAction::Appoint,f.proof);});}
    case_start("first-row-literal-defaults-and-expression-fail-closed");
    {Fixture f;sqlite_detail::execute(f.db,"ALTER TABLE owned_guild_officers_0082 ADD COLUMN opaque_text TEXT DEFAULT 'literal';"
        "ALTER TABLE owned_guild_officers_0082 ADD COLUMN opaque_real REAL DEFAULT 1.25;"
        "ALTER TABLE owned_guild_officers_0082 ADD COLUMN opaque_null BLOB DEFAULT NULL;");
     change(f,Repo::OfficerAction::Appoint);sqlite_detail::Statement q(f.db,
        "SELECT opaque_text,opaque_real,typeof(opaque_null) FROM owned_guild_officers_0082 WHERE character_id=2");
     check(q.row() && q.text(0)=="literal" && q.text(2)=="null");}
    {Fixture f;sqlite_detail::execute(f.db,"ALTER TABLE owned_guild_officers_0082 ADD COLUMN dynamic_default TEXT DEFAULT (lower('ABC'));");
     const auto l=rank_lease(f);f.failed([&]{change(f,l,Repo::OfficerAction::Appoint,f.proof);});}
}
}
int main(){try{for(bool cn:{false,true})for(bool utf16:{false,true}){basic(cn,utf16);leave_rejoin(cn,utf16);}
    legacy_lifecycles();stale_leases();callbacks_and_triggers();battle_overflow_schema();
    std::cout<<"PASS storage_owned_guild_officers_0082 cases="<<cases<<" checks="<<checks<<" negative_cases="<<negative_cases<<'\n';return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
