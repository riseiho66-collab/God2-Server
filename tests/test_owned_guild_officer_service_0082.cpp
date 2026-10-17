#include "handlers/OwnedGuildOfficerService.h"
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
    explicit Fixture(const std::string& path=":memory:",bool utf16=false,bool simplified=false,bool opaque=true) {
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

unsigned service_cases=0;
using Service=OwnedGuildOfficerServiceDraft;using Projection=OwnedGuildOfficerProjectionDraft;using Panel=OwnedGuildLeaderPanelService;
void begin_case(const char* name){++service_cases;std::cout<<"CASE "<<name<<'\n';}
struct WorldFixture:Fixture {
    std::unique_ptr<Panel> panel;std::unique_ptr<Projection> projection;std::unique_ptr<Service> service;
    std::map<std::uint64_t,Panel::Owner> owners;std::set<std::uint32_t> online;
    std::set<std::uint64_t> unready;
    std::function<void()> on_capture,on_world;
    bool deny_sql=false,deny_after_write=false,wrote=false;
    unsigned after_write_calls=0;
    WorldFixture(bool simplified=false):Fixture(":memory:",false,simplified) {
        for(unsigned i=1;i<=7;++i){owners.emplace(i,Panel::Owner{i,i,i,1,4,3,59,60,static_cast<std::uint16_t>(simplified?936:950),1,1});online.insert(i);}
        check(sqlite3_create_function_v2(db,"test_officer_written",0,SQLITE_UTF8,this,
            [](sqlite3_context* c,int,sqlite3_value**){static_cast<WorldFixture*>(sqlite3_user_data(c))->wrote=true;sqlite3_result_int(c,1);},
            nullptr,nullptr,nullptr)==SQLITE_OK);
        sqlite_detail::execute(db,"CREATE TRIGGER officer_write_witness AFTER UPDATE ON owned_guilds WHEN NEW.id=1 BEGIN SELECT test_officer_written(); END");
        panel=std::make_unique<Panel>(*repo,[this](auto session){return resolve(session);},
            [this](auto account,auto character){return memberships->load(account,character);},[this]{return online;});
        projection=std::make_unique<Projection>(*repo,*panel);
        service=std::make_unique<Service>(*repo,*projection,[this](auto session){return resolve(session);},
            [this](const auto& state){return capture(state);},[this](const auto& state,const auto& world){return current_world(state,world);});
    }
    std::optional<Panel::Owner> resolve(std::uint64_t session) {
        const auto at=owners.find(session);if(at==owners.end())return {};return at->second;
    }
    std::optional<Service::WorldLease> capture(const Panel::State& state) {
        if(auto hook=std::exchange(on_capture,{}))hook();Service::WorldLease lease;
        for(const auto& [session,owner]:owners)for(const auto& row:state.rows)
            if(row.identity.character_id==owner.character && row.identity.account_id==owner.account) {
                if(unready.contains(session))return {};lease.connected.push_back(owner);break;
            }
        return lease;
    }
    bool current_world(const Panel::State&,const Service::WorldLease& world) {
        if(auto hook=std::exchange(on_world,{}))hook();
        if(wrote)++after_write_calls;
        if(deny_sql && !sqlite3_get_autocommit(db))return false;
        if(deny_after_write && wrote && !sqlite3_get_autocommit(db))return false;
        for(const auto& owner:world.connected)if(unready.contains(owner.session) || resolve(owner.session)!=std::optional{owner})return false;
        // This callback NEVER reads SQL membership/governance/profile/resources.
        return true;
    }
    Projection::Plan open(unsigned session=1) {
        auto plan=projection->prepare(session,true);check(bool(plan));check(projection->published(*plan));return *plan;
    }
    Service::Plan action(Service::Action kind=Service::Action::Appoint,unsigned session=1,std::uint8_t slot=1) {
        open(session);const auto plan=service->prepare(session,kind,slot);check(bool(plan));return *plan;
    }
    void fail(const Service::Plan& plan) {
        ++negative_cases;const auto before=snapshot(db);check(!service->execute(plan));check(snapshot(db)==before);check(sqlite3_get_autocommit(db)==1);
    }
};
void service_lifecycle(bool simplified) {
    begin_case("native-slot-projection-appoint-demote-selfleave");WorldFixture f(simplified);
    check(!f.service->prepare(1,Service::Action::Appoint,1));
    const auto appoint=f.action();check(f.service->execute(appoint));check(!f.service->execute(appoint));
    const auto founder=f.open();check(f.projection->cached_role(1,1)==std::optional<std::uint8_t>{2});
    const auto self=f.open(2);check(f.projection->cached_role(2,0)==std::optional<std::uint8_t>{2});
    check(f.projection->cached_role(2,1)==std::optional<std::uint8_t>{3});
    const auto has93=[](const auto& data,std::uint8_t slot){
        for(std::size_t i=0;i+2<data.size();++i)if(data[i]==0x93 && data[i+1]==slot && data[i+2]==2)return true;return false;};
    check(has93(founder.logical,1) && has93(self.logical,0));
    check(!f.service->prepare(2,Service::Action::Appoint,1));check(!f.service->prepare(1,Service::Action::Appoint,0));
    check(!f.service->prepare(1,Service::Action::Appoint,2)); // applicant slot
    const auto remove=f.action(Service::Action::RemoveOffice);check(f.service->execute(remove));f.open(2);
    check(f.projection->cached_role(2,0)==std::optional<std::uint8_t>{1});
    check(!f.service->prepare(2,Service::Action::SelfLeave,0));
    check(f.service->execute(f.action()));const auto leave=f.action(Service::Action::SelfLeave,2,0);
    const auto history=f.repo->officer_history(f.guild);f.wrote=false;f.after_write_calls=0;
    check(f.service->execute(leave));check(!f.memberships->load(2,2) && f.repo->officer_history(f.guild)==history);
    check(f.after_write_calls>0);const auto clear=f.panel->prepare_clear(2);check(clear.has_value());
    check(clear->logical.size()>=2 && clear->logical[clear->logical.size()-2]==0x92 && clear->logical.back()==0);
    check(f.panel->cleared(*clear));f.projection->forget_after_clear(2);check(!f.projection->publication(2));
    f.join(2,f.guild);f.open(2);check(f.projection->cached_role(2,0)==std::optional<std::uint8_t>{1});
}
void service_denials() {
    begin_case("all-owner-fields-audience-aba-stale-publication");
    for(unsigned field=0;field<11;++field) {
        WorldFixture f;const auto plan=f.action();auto& owner=f.owners[1];
        if(field==0)owner.session++;if(field==1)owner.account++;if(field==2)owner.character++;
        if(field==3)owner.world_generation++;if(field==4)owner.area++;if(field==5)owner.scene++;
        if(field==6)owner.x++;if(field==7)owner.y++;if(field==8)owner.name_codepage=936;
        if(field==9)owner.battle_generation++;if(field==10)owner.position_revision++;
        f.fail(plan);
    }
    for(unsigned session:{2u,3u}) {WorldFixture f;const auto plan=f.action();f.owners[session].position_revision++;f.fail(plan);}
    {WorldFixture f;auto duplicate=f.owners[2];duplicate.session=20;f.owners.emplace(20,duplicate);
     const auto plan=f.action();check(plan.world.connected.size()==4);f.owners[20].world_generation++;f.fail(plan);}
    {WorldFixture f;const auto old=f.action();const auto fresh=f.action();f.fail(old);check(f.service->current(fresh));check(f.service->execute(fresh));}
    {WorldFixture f;const auto plan=f.action();f.on_capture=[&]{f.open();};f.fail(plan);}
    {WorldFixture f;const auto plan=f.action();f.deny_sql=true;f.fail(plan);check(!f.service->prepare(1,Service::Action::Appoint,1));}
    {WorldFixture f;const auto plan=f.action();f.deny_after_write=true;f.fail(plan);}
    {WorldFixture f;const auto plan=f.action();f.on_world=[&]{if(!sqlite3_get_autocommit(f.db))f.open();};
     // Hook must run inside paired proof, not pre-execute current(); install via
     // count witness below instead. This case only confirms one-shot harmless hook.
     check(f.service->execute(plan));}
}
void cache_behaviors() {
    begin_case("readonly-tick-missing-cache-consumed-history");WorldFixture f;
    const auto prepared=f.projection->prepare(1,false);check(prepared && f.projection->published(*prepared));
    check(!f.service->prepare(1,Service::Action::Appoint,1));const auto plan=f.action();check(f.service->execute(plan));
    const auto tick=f.projection->prepare(1,false);check(tick && f.projection->published(*tick));
    check(!f.service->prepare(1,Service::Action::RemoveOffice,1));
    f.open();check(f.service->prepare(1,Service::Action::RemoveOffice,1).has_value());
    Projection fresh(*f.repo,*f.panel);check(!fresh.prepare(1,false));check(fresh.prepare(1,true).has_value());
    const auto lease=f.action(Service::Action::RemoveOffice);auto history=lease.publication.history;
    sqlite_detail::execute(f.db,"UPDATE owned_guild_officers_0082 SET role=1 WHERE character_id=2");f.fail(lease);
    check(!f.projection->prepare(1,false)); // rank-only unversioned corruption: explicitopen required
}
void consumed_publication_proof() {
    begin_case("sql-callback-new-publication-rolls-back");WorldFixture f;const auto plan=f.action();
    unsigned calls=0;Service hostile(*f.repo,*f.projection,[&](auto id){return f.resolve(id);},
        [&](const auto& p){return f.capture(p);},[&](const auto& p,const auto& world){
            ++calls;if(!sqlite3_get_autocommit(f.db) && f.wrote)f.open();return f.current_world(p,world);});
    const auto before=snapshot(f.db);check(!hostile.execute(plan));check(snapshot(f.db)==before);check(calls>=3);
}
void full50_and_duplicates(bool simplified) {
    begin_case(simplified?"complete50-mixed-accepted-pending-duplicates-simplified":"complete50-mixed-accepted-pending-duplicates-traditional");WorldFixture f(simplified);
    sqlite_detail::execute(f.db,"UPDATE owned_guild_governance_0078 SET capacity=50 WHERE guild_id=1");
    for(unsigned i=8;i<=54;++i) {
        sqlite_detail::Statement a(f.db,"INSERT INTO accounts(id,username,password_hash) VALUES(?,?,'PRIVATE_ONLY')");
        a.bind(1,i);a.bind(2,"OfficerAcct"+std::to_string(i));a.done();
        const auto name="OfficerP"+std::to_string(i);const std::vector<std::uint8_t> bytes(name.begin(),name.end());
        std::array<std::uint8_t,40> profile{};std::copy(bytes.begin(),bytes.end(),profile.begin());profile[29]=1;
        sqlite_detail::Statement c(f.db,"INSERT INTO recovered_characters(id,account_id,slot,profile,name_bytes,name_codepage) VALUES(?,?,0,?,?,?)");
        c.bind(1,i);c.bind(2,i);c.bind_blob(3,profile);c.bind_blob(4,bytes);c.bind(5,simplified?936:950);c.done();
        RecoveredRoleLevel::Bytes role{};role[0]=0x22;role[1]=35;role[17]=100;role[21]=50;
        sqlite_detail::Statement r(f.db,"INSERT INTO character_role_snapshots(character_id,logical,revision,design_id) VALUES(?,?,1,'CUSTOM-0013')");
        r.bind(1,i);r.bind_blob(2,role);r.done();f.money->provision_wallet(i,i);
        SqliteRecoveredCharacterRepository(f.db).commit_resources(i,i,{}, {100,100,50,50,0,"CUSTOM-0012"});
        f.owners.emplace(i,Panel::Owner{i,i,i,1,4,3,59,60,static_cast<std::uint16_t>(simplified?936:950),1,1});f.online.insert(i);
    }
    f.join(7,f.guild);for(unsigned i=8;i<=30;++i)f.join(i,f.guild);
    for(unsigned i=31;i<=53;++i)f.apply(i,f.guild);
    const auto open=f.open();check(open.base.next.rows.size()==50 && open.base.next.leader.roster.size()==26 && open.base.next.applications.size()==24);
    auto dup=f.owners[53];dup.session=100;f.owners.emplace(100,dup);
    const auto action=f.action();check(action.world.connected.size()==51);
    f.unready.insert(100);f.fail(action);f.unready.clear();
    const auto fresh=f.action();check(f.service->execute(fresh));const auto update=f.open();
    check(update.base.next.rows.size()==50 && update.logical[update.logical.size()-3]==0x93 &&
        update.logical[update.logical.size()-2]==1 && update.logical.back()==2);
    const auto self=f.open(2);check(self.base.next.rows.size()==50 && self.logical[self.logical.size()-2]==0);
    // Offline accepted target still requires a complete founder panel and SQL
    // nonbattle lease; it is not a native offline administrative grant.
    f.owners.erase(2);f.online.erase(2);const auto removal=f.action(Service::Action::RemoveOffice);
    check(f.service->execute(removal));f.open();check(f.projection->cached_role(1,1)==std::optional<std::uint8_t>{1});
}
void forged_and_missing_schema() {
    begin_case("forged-composite-plan-and-fresh-missing-schema");
    for(unsigned field=0;field<9;++field) {
        WorldFixture f;const auto valid=f.action();auto forged=valid;
        if(field==0)forged.slot=2;if(field==1)forged.publication.base.serial++;
        if(field==2)forged.publication.projection_generation++;
        if(field==3)forged.target.account_id=4;
        if(field==4)forged.target.profile[29]=8;
        if(field==5)forged.target_membership.membership_revision++;
        if(field==6)forged.action=Service::Action::RemoveOffice;
        if(field==7)forged.world.connected.pop_back();
        if(field==8)forged.publication.history.push_back({f.guild,2,2,forged.target_membership.membership_revision,
            forged.target_membership.guild_revision,0,2});
        f.fail(forged);
    }
    {WorldFixture f;sqlite_detail::execute(f.db,"DROP TABLE owned_guild_officers_0082");
     check(!f.projection->prepare(1,true));check(!f.service->prepare(1,Service::Action::Appoint,1));
     check(f.panel->prepare(1,true).has_value()); // Frozen old reader unchanged.
    }
    {WorldFixture f;const auto plan=f.action();f.unready.insert(3);f.fail(plan);} // connected pending applicant
    {WorldFixture f;const auto plan=f.action();auto retired=f.owners[3];f.owners.erase(3);f.fail(plan);}
}
}
int main(){try{for(bool simplified:{false,true})service_lifecycle(simplified);service_denials();cache_behaviors();consumed_publication_proof();
    for(bool simplified:{false,true})full50_and_duplicates(simplified);
    forged_and_missing_schema();
    std::cout<<"PASS test_owned_guild_officer_service_0082 cases="<<service_cases<<" checks="<<checks<<" negative_cases="<<negative_cases<<'\n';return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
